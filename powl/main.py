import pandas as pd
import pm4py
from pm4py.algo.discovery.inductive.variants.imf import IMFParameters
from powl.algo.discovery.inductive.utils.filtering import FILTERING_THRESHOLD
from powl.algo.discovery.inductive.variants.dynamic_clustering_frequency.dynamic_clustering_frequency_partial_order_cut import \
    ORDER_FREQUENCY_RATIO
from powl.algo.discovery.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant
from powl.objects.obj import POWL
from pm4py.util.pandas_utils import check_is_pandas_dataframe, check_pandas_dataframe_columns
from pm4py.utils import get_properties
from powl.conversion.converter import apply as powl_converter
from powl.visualization.powl.visualizer import POWLVisualizationVariants
from pm4py.objects.bpmn.layout import layouter
from powl.conversion.variants.to_bpmn import apply as bpmn_converter



def import_event_log(path: str) -> pd.DataFrame:
    import rustxes
    if path.endswith(".xes") or path.endswith(".xes.gz"):
        [xes, log_attrs] = rustxes.import_xes(path)
        df = xes.to_pandas()
    elif path.endswith(".csv"):
        df = pd.read_csv(path, keep_default_na=False, parse_dates=['time:timestamp'])
        df = pm4py.format_dataframe(df)
    else:
        raise Exception("Unsupported file type!")
    return df



def discover(log: pd.DataFrame, variant=POWLDiscoveryVariant.DECISION_GRAPH_MAX,
                  filtering_weight_factor: float = None, order_graph_filtering_threshold: float = None,
                  dfg_frequency_filtering_threshold: float = None,
                  activity_key: str = "concept:name", timestamp_key: str = "time:timestamp",
                  case_id_key: str = "case:concept:name",
                  lifecycle_key: str = "lifecycle:transition",
                  keep_only_completion_events: bool = True,
                  ) -> POWL:
    """
    Discovers a POWL model from an event log.

    Reference paper:
    Kourani, Humam, and Sebastiaan J. van Zelst. "POWL: partially ordered workflow language." International Conference on Business Process Management. Cham: Springer Nature Switzerland, 2023.

    :param keep_only_completion_events:
    :param lifecycle_key:
    :param log: event log / Pandas dataframe
    :param variant: variant of the algorithm
    :param filtering_weight_factor: accepts values 0 <= x < 1
    :param order_graph_filtering_threshold: accepts values 0.5 < x <= 1
    :param dfg_frequency_filtering_threshold: accepts values 0 <= x < 1
    :param activity_key: attribute to be used for the activity
    :param timestamp_key: attribute to be used for the timestamp
    :param case_id_key: attribute to be used as case identifier
    :rtype: ``POWL``
    """
    if check_is_pandas_dataframe(log):
        check_pandas_dataframe_columns(
            log, activity_key=activity_key, timestamp_key=timestamp_key, case_id_key=case_id_key)

    properties = get_properties(log, activity_key=activity_key, timestamp_key=timestamp_key)

    if keep_only_completion_events and lifecycle_key in log.columns:
        filtered_log = log[log["lifecycle:transition"].isin(["complete", "COMPLETE", "Complete"])]
        if len(filtered_log) > 0:
            log = filtered_log

    from powl.algo.discovery.inductive.utils.filtering import FILTERING_TYPE, FilteringType

    num_filters = 0
    if order_graph_filtering_threshold is not None:
        if not variant is POWLDiscoveryVariant.DYNAMIC_CLUSTERING:
            raise Exception("The order graph filtering threshold can only be used for the variant DYNAMIC_CLUSTERING!")
        properties[ORDER_FREQUENCY_RATIO] = order_graph_filtering_threshold
        properties[FILTERING_TYPE] = FilteringType.DYNAMIC
        num_filters += 1
    if dfg_frequency_filtering_threshold is not None:
        properties[IMFParameters.NOISE_THRESHOLD] = dfg_frequency_filtering_threshold
        properties[FILTERING_TYPE] = FilteringType.DFG_FREQUENCY
        num_filters += 1
    if filtering_weight_factor is not None:
        properties[FILTERING_THRESHOLD] = filtering_weight_factor
        properties[FILTERING_TYPE] = FilteringType.DECREASING_FACTOR
        num_filters += 1

    if num_filters > 1:
        raise Exception("The algorithm can only be used with one filtering threshold at a time!")

    from powl.algo.discovery import algorithm as powl_discovery
    return powl_discovery.apply(log, variant=variant, parameters=properties)


def view(powl: POWL, use_frequency_tags=True):
    from powl.visualization.powl import visualizer as powl_visualizer
    gviz = powl_visualizer.apply(powl, variant=POWLVisualizationVariants.BASIC, frequency_tags=use_frequency_tags)
    powl_visualizer.view(gviz)


def view_net(powl: POWL, use_frequency_tags=True):
    from powl.visualization.powl import visualizer as powl_visualizer
    gviz = powl_visualizer.apply(powl, variant=POWLVisualizationVariants.NET, frequency_tags=use_frequency_tags)
    powl_visualizer.view(gviz)


def save_visualization(powl: POWL, file_path: str, use_frequency_tags=True):
    file_path = str(file_path)
    from powl.visualization.powl import visualizer as powl_visualizer
    gviz = powl_visualizer.apply(powl, variant=POWLVisualizationVariants.BASIC, frequency_tags=use_frequency_tags)
    return powl_visualizer.save(gviz, file_path)


def save_visualization_net(powl: POWL, file_path: str, use_frequency_tags=True):
    file_path = str(file_path)
    from powl.visualization.powl import visualizer as powl_visualizer
    gviz = powl_visualizer.apply(powl, variant=POWLVisualizationVariants.NET, frequency_tags=use_frequency_tags)
    return powl_visualizer.save(gviz, file_path)


def convert_to_petri_net(powl: POWL):
    return powl_converter(powl)


def convert_to_bpmn(powl: POWL):
    bpmn, _, _ = bpmn_converter(powl)
    bpmn = layouter.apply(bpmn)
    return bpmn
