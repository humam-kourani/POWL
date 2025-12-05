from pm4py.objects.bpmn.exporter.variants.etree import get_xml_string

import powl.conversion.variants.to_bpmn as pminer_bpmn_transformer
import powl.visualization.bpmn.resource_utils.layouter as utils


def apply(activity_to_pool_lane: dict[str, tuple[str, str]], powl) -> str:
    original_pools = set(
        [p for _, (p, _) in activity_to_pool_lane.items() if p is not None]
    )
    activity_to_pool_lane_copy = activity_to_pool_lane.copy()
    if len(original_pools) == 0:
        # Modify it to have a default pool
        activity_to_pool_lane = {
            activity: ("ProcessPool", lane)
            for activity, (_, lane) in activity_to_pool_lane.items()
        }
    for activity, (pool, lane) in activity_to_pool_lane_copy.items():
        if pool is None and lane is None:
            activity_to_pool_lane[activity] = ("ProcessPool", "DefaultLane")
        elif pool is None:
            activity_to_pool_lane[activity] = ("ProcessPool", lane)
        elif lane is None:
            activity_to_pool_lane[activity] = (pool, "DefaultLane")

    pools = utils.__pools_to_tasks(activity_to_pool_lane)
    _, G, _ = pminer_bpmn_transformer.apply(powl)
    coloring = {}
    if len(pools) > 1:
        coloring = utils.color_graph(G, pools)
        G, coloring = utils.__add_intermediate_events_to_graph(G, coloring)
    else:
        pool_name = list(pools.keys())[0] if pools else "DefaultPool"
        coloring = {node: pool_name for node in G.nodes()}
    bpmn, elements_mapping = pminer_bpmn_transformer.__transform_to_bpmn(G)

    # to string
    bpmn = str(get_xml_string(bpmn))
    bpmn = utils.apply_layouting(bpmn)
    bpmn = utils.parse_xml(bpmn)

    # Hardfix coloring keys, don't ask why and how
    # if it includes _, keep it as it is, else add Task_ at the beginning
    coloring = {str(k): v for k, v in coloring.items()}
    coloring = {
        elements_mapping.get(k, k): v
        for k, v in coloring.items()
        if k in elements_mapping
    }
    task_name_to_id = utils.task_name_to_id(bpmn)
    ordered_lanes_and_pools = utils.order_lanes_and_pools(
        activity_to_pool_lane, task_name_to_id, bpmn
    )

    model_dims = utils.get_model_dimensions(bpmn)
    pools = utils.construct_pools(
        activity_to_pool_lane, model_dims, ordered_lanes_and_pools
    )
    lanes = [pool.get_lanes() for pool in pools]
    lanes = [lane for sublist in lanes for lane in sublist]  # Flatten
    task_name_to_id = {k: v for k, v in task_name_to_id.items() if k != ""}
    bpmn, aligned_elements = utils.__align_tasks(lanes, bpmn, task_name_to_id)
    bpmn = utils.__align_elements(bpmn, coloring, aligned_elements, lanes)
    # bpmn = utils.__postprocess_pools(pools, bpmn)
    bpmn = utils.postprocess_diagram(bpmn, pools=pools)
    shapes = utils.__create_shapes(aligned_elements, bpmn)

    # Handle the sequence flows
    bpmn, msg_flows = utils.__handle_sequence_flows(bpmn, shapes)
    bpmn = utils.build_pools_with_collaboration(bpmn, pools, msg_flows)
    return bpmn
