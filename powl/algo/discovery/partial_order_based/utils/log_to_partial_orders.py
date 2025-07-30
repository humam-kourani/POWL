import warnings
from collections import deque, defaultdict
from typing import List, Dict, Tuple, Any, Set
import pandas as pd

from powl.algo.discovery.partial_order_based.utils.constants import VARIANT_FREQUENCY_KEY
from powl.algo.discovery.partial_order_based.utils.simplified_objects import ActivityInstance, Graph


def generate_interval_df_fifo(
    df: pd.DataFrame,
    case_id_col: str, activity_col: str, ordering_col: str, lifecycle_col: str or None,
    start_transitions: Set[str], complete_transitions: Set[str]
) -> pd.DataFrame:
    work_df = df[[case_id_col, activity_col, ordering_col] + ([lifecycle_col] if lifecycle_col else [])].copy()

    if lifecycle_col:
        work_df[lifecycle_col] = work_df[lifecycle_col].str.lower()
    work_df = work_df.sort_values([case_id_col, ordering_col])
    interval_list = []
    for case_id, trace_df in work_df.groupby(case_id_col, sort=False):
        activities_start: Dict[str, deque] = {}
        activities_ids: Dict[str, int] = {}
        for index, event in trace_df.iterrows():
            activity_key = str(event[activity_col])
            timestamp = event[ordering_col]
            if lifecycle_col:
                transition = event[lifecycle_col]
                if transition in start_transitions:
                    if activity_key not in activities_start:
                        activities_start[activity_key] = deque()
                    activities_start[activity_key].append({'timestamp': timestamp, 'event_index': index})
                elif transition in complete_transitions:
                    start_timestamp = timestamp
                    if activity_key in activities_start and activities_start[activity_key]:
                        start_timestamp = activities_start[activity_key].popleft()['timestamp']
                    if activity_key not in activities_ids:
                        activities_ids[activity_key] = 1
                    else:
                        activities_ids[activity_key] = activities_ids[activity_key] + 1
                    activity_instance = ActivityInstance(activity_key, activities_ids[activity_key])
                    interval_record = { case_id_col: case_id, 'activity': activity_instance, 'start_timestamp': start_timestamp, 'end_timestamp': timestamp}
                    interval_list.append(interval_record)
            else:
                if activity_key not in activities_ids:
                    activities_ids[activity_key] = 1
                else:
                    activities_ids[activity_key] = activities_ids[activity_key] + 1
                activity_instance = ActivityInstance(activity_key, activities_ids[activity_key])
                interval_record = {case_id_col: case_id, 'activity': activity_instance,
                                   'start_timestamp': timestamp, 'end_timestamp': timestamp}
                interval_list.append(interval_record)
    if not interval_list:
        return pd.DataFrame()
    interval_df = pd.DataFrame(interval_list)
    interval_df['start_timestamp'] = pd.to_datetime(interval_df['start_timestamp'], utc=True)
    interval_df['end_timestamp'] = pd.to_datetime(interval_df['end_timestamp'], utc=True)
    interval_df = interval_df.sort_values([case_id_col, 'start_timestamp', 'end_timestamp']).reset_index(drop=True)
    interval_df['event_instance_id'] = interval_df.index
    print(f"Successfully created {len(interval_df)} activity intervals using FIFO logic.")
    return interval_df


def apply(
    df: pd.DataFrame,
    case_id_col: str,
    activity_col: str,
    ordering_col: str,
    lifecycle_col: str or None,
    start_transitions: Set[str],
    complete_transitions: Set[str],
) -> List[Any]:

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input 'log' must be a Pandas DataFrame.")

    for col in [activity_col, ordering_col, case_id_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in the event table!")

    if lifecycle_col:
        if lifecycle_col in df.columns:
            complete_log = df[df['lifecycle:transition'].isin(complete_transitions)]
            if len(complete_log) == 0:
                lifecycle_col = None
                warnings.warn(message=f'The event log does not contain any completion events! All events will be considered during discovery!', category=UserWarning)
        else:
            lifecycle_col = None
            warnings.warn(f'The event log does not contain any attribute with the lifecycle key "{lifecycle_col}"! All events will be considered during discovery!', category=UserWarning)

    interval_df = generate_interval_df_fifo(
        df, case_id_col, activity_col, ordering_col, lifecycle_col,
        start_transitions, complete_transitions
    )

    if interval_df.empty:
        raise Exception("Interval DataFrame is empty, no variants to generate.")

    # calculate potential direct succession edges
    merged_df = pd.merge(
        interval_df[[case_id_col, 'activity', 'start_timestamp', 'end_timestamp', 'event_instance_id']],
        interval_df[[case_id_col, 'activity', 'start_timestamp', 'end_timestamp', 'event_instance_id']],
        on=case_id_col,
        suffixes=('_1', '_2')
    )
    merged_df = merged_df[merged_df['event_instance_id_1'] != merged_df['event_instance_id_2']]
    is_directly_followed = merged_df['start_timestamp_2'] > merged_df['end_timestamp_1']
    direct_follows_edges_df = merged_df.loc[is_directly_followed, [case_id_col, 'activity_1', 'activity_2']].copy()

    # Group edges by case for quick lookup later
    edges_by_case = direct_follows_edges_df.groupby(case_id_col)[['activity_1', 'activity_2']].apply(
        lambda g: tuple(sorted(zip(g['activity_1'], g['activity_2'])))
    ).to_dict()  # Convert to dictionary {case_id: tuple_of_edges}

    variants_data = defaultdict(lambda: {VARIANT_FREQUENCY_KEY: 0})

    grouped_intervals = interval_df.groupby(case_id_col)
    total_cases = len(grouped_intervals)
    processed_cases = 0

    for case_id, trace_df in grouped_intervals:
        trace_activities_multiset = frozenset(trace_df['activity'].tolist())

        trace_edges = frozenset(edges_by_case.get(case_id, tuple()))

        variant_key = (trace_activities_multiset, trace_edges)

        variants_data[variant_key][VARIANT_FREQUENCY_KEY] += 1
        if 'structure' not in variants_data[variant_key]:
            variants_data[variant_key]['structure'] = {'activities': trace_activities_multiset, 'edges': trace_edges}

        processed_cases += 1
        if processed_cases % 1000 == 0:
            print(f"Processed {processed_cases}/{total_cases} cases for grouping...")

    print(f"Found {len(variants_data)} unique variants.")

    output_list = []
    for variant_key, data in variants_data.items():
        add_info = {
            VARIANT_FREQUENCY_KEY: data[VARIANT_FREQUENCY_KEY],
        }
        order = Graph(variant_key[0], variant_key[1], add_info)
        output_list.append(order)

    output_list.sort(
        key=lambda x: x.additional_information[VARIANT_FREQUENCY_KEY],
        reverse=True)

    return output_list