import powl.conversion.variants.to_bpmn as pminer_bpmn_transformer
import powl.visualization.bpmn.resource_utils.layouter as utils
from pm4py.objects.bpmn.exporter.variants.etree import get_xml_string

def apply(pool_data: dict, lane_data: dict, powl) -> str:

    pools = utils.__pools_to_tasks(pool_data, lane_data)
    _, G, _ = pminer_bpmn_transformer.apply(powl)
    coloring = utils.color_graph(G, pools)
    G, coloring = utils.__add_intermediate_events_to_graph(G, coloring)
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
        pool_data, lane_data, task_name_to_id, bpmn
    )
    model_dims = utils.get_model_dimensions(bpmn)
    pools = utils.construct_pools(
        ordered_lanes_and_pools, lane_data, model_dims[0], model_dims[1]
    )
    lanes = [pool.get_lanes() for pool in pools]
    lanes = [lane for sublist in lanes for lane in sublist]  # Flatten
    task_name_to_id = {k: v for k, v in task_name_to_id.items() if k != ""}
    bpmn, aligned_elements = utils.__align_tasks(lanes, bpmn, task_name_to_id)
    bpmn = utils.__align_elements(bpmn, coloring, aligned_elements, lanes)
    shapes = utils.__create_shapes(aligned_elements, bpmn)
    # Handle the sequence flows
    bpmn, msg_flows = utils.__handle_sequence_flows(bpmn, shapes)
    bpmn = utils.build_pools_with_collaboration(bpmn, pools, msg_flows)
    return bpmn