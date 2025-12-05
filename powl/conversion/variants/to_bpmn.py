from typing import List

import networkx as nx
import pm4py.objects.bpmn.obj as bpmn_obj
from pm4py.objects.process_tree.obj import Operator

from powl.objects.obj import (
    DecisionGraph,
    EndNode,
    OperatorPOWL,
    SilentTransition,
    StartNode,
    StrictPartialOrder,
    Transition,
)


def __handle_transition(powl_content: Transition) -> nx.DiGraph:
    # Add artificial start and end nodes
    subgraph = nx.DiGraph()
    start_node = f"Start_{id(powl_content)}"
    end_node = f"End_{id(powl_content)}"
    subgraph.add_node(start_node, type="start", visited=True)
    subgraph.add_node(end_node, type="end", visited=True)
    subgraph.add_node(id(powl_content), content=powl_content.label, visited=True)
    # Add the edges start -> transition -> end
    subgraph.add_edge(start_node, id(powl_content))
    subgraph.add_edge(id(powl_content), end_node)
    return subgraph


def __handle_silent_transition(powl_content: SilentTransition) -> nx.DiGraph:
    subgraph = nx.DiGraph()
    start_node = f"Start_{id(powl_content)}"
    end_node = f"End_{id(powl_content)}"
    subgraph.add_node(start_node, type="start", visited=True)
    subgraph.add_node(end_node, type="end", visited=True)
    # Add the edges start -> silent transition -> end
    subgraph.add_node(start_node, visited=True)
    subgraph.add_node(end_node, visited=True)
    subgraph.add_edge(start_node, end_node)
    return subgraph


def __handle_operator_powl(powl_content: OperatorPOWL) -> nx.DiGraph:
    """
    Handle the OperatorPOWL content and return a directed graph.

    Parameters
    ----------
    powl_content : OperatorPOWL
        The OperatorPOWL content to handle.

    Returns
    -------
    G : nx.DiGraph
        The directed graph representing the OperatorPOWL.
    """
    G = nx.DiGraph()
    start_event = f"Start_{id(powl_content)}"
    end_event = f"End_{id(powl_content)}"
    G.add_node(start_event, type="start", visited=True)
    G.add_node(end_event, type="end", visited=True)
    operator = powl_content.operator

    if operator == Operator.LOOP and len(powl_content.children) == 2:
        # Add a diverging parallel gateway and a converging parallel gateway
        diverging_gateway = f"ExclusiveGateway_{id(powl_content)}_diverging"
        converging_gateway = f"ExclusiveGateway_{id(powl_content)}_converging"
        G.add_node(
            diverging_gateway,
            type="diverging",
            paired_with=[converging_gateway],
            visited=True,
        )
        G.add_node(
            converging_gateway,
            type="converging",
            paired_with=[diverging_gateway],
            visited=True,
        )
        # Handle the edges now
        do_part = powl_content.children[0]
        redo_part = powl_content.children[1]
        G.add_node(id(do_part), content=do_part, visited=False)
        G.add_node(id(redo_part), content=redo_part, visited=False)
        G.add_edge(start_event, converging_gateway)
        G.add_edge(converging_gateway, id(do_part))
        G.add_edge(id(do_part), diverging_gateway)
        G.add_edge(diverging_gateway, end_event)
        G.add_edge(diverging_gateway, id(redo_part))
        G.add_edge(id(redo_part), converging_gateway)

    elif operator == Operator.XOR:
        # One exclusive choice gateway
        exclusive_gateway_diverging = f"ExclusiveGateway_{id(powl_content)}_diverging"
        exclusive_gateway_converging = f"ExclusiveGateway_{id(powl_content)}_converging"
        G.add_node(
            exclusive_gateway_diverging,
            type="diverging",
            paired_with=[exclusive_gateway_converging],
            visited=True,
        )
        G.add_node(
            exclusive_gateway_converging,
            type="converging",
            paired_with=[exclusive_gateway_diverging],
            visited=True,
        )
        G.add_edge(start_event, exclusive_gateway_diverging)
        G.add_edge(exclusive_gateway_converging, end_event)

        for child in powl_content.children:
            if id(child) not in G.nodes:
                G.add_node(id(child), content=child, visited=False)
            G.add_edge(exclusive_gateway_diverging, id(child))
            G.add_edge(id(child), exclusive_gateway_converging)
    else:
        raise ValueError(f"Unsupported operator: {operator}")
    return G


def __handle_decision_graph(powl_content: DecisionGraph) -> nx.DiGraph:
    """
    Handle the DecisionGraph content and return a directed graph.

    Parameters
    ----------
    powl_content : DecisionGraph
        The DecisionGraph content to handle.

    Returns
    -------
    G : nx.DiGraph
        The directed graph representing the DecisionGraph.
    """

    G = nx.DiGraph()
    edges = __obtain_edges(powl_content, transitive_reduction=False)
    node_edges = {
        node: {"incoming": [], "outgoing": []} for node in powl_content.order.nodes
    }
    for edge in edges:
        src, dst = edge
        node_edges[src]["outgoing"].append(dst)
        node_edges[dst]["incoming"].append(src)
    for node in node_edges.keys():
        # Check for end and start
        if type(node) is StartNode:
            G.add_node(id(node), type="start", visited=True)
            # Add an exclusive gateway after it
            G.add_node(
                f"ExclusiveGateway_{id(node)}_afternode",
                type="exclusive_gateway",
                visited=True,
            )
            # Connect them
            G.add_edge(id(node), f"ExclusiveGateway_{id(node)}_afternode")
        elif type(node) is EndNode:
            G.add_node(id(node), type="end", visited=True)
            # Add an exclusive gateway before it
            G.add_node(
                f"ExclusiveGateway_{id(node)}_beforenode",
                type="exclusive_gateway",
                visited=True,
            )
            # Connect them
            G.add_edge(f"ExclusiveGateway_{id(node)}_beforenode", id(node))

    G = __add_auxiliary_nodes_before_after(G, node_edges, type="exclusive_gateway")
    for edge in edges:
        src, dst = edge
        src = (
            f"ExclusiveGateway_{id(src)}_afternode"
            if f"ExclusiveGateway_{id(src)}_afternode" in G.nodes
            else id(src)
        )
        dst = (
            f"ExclusiveGateway_{id(dst)}_beforenode"
            if f"ExclusiveGateway_{id(dst)}_beforenode" in G.nodes
            else id(dst)
        )
        G.add_edge(src, dst)
    return G


def __obtain_edges(powl_content, transitive_reduction: bool = True) -> List[tuple]:
    edges = []
    for src in powl_content.order.nodes:
        for dst in powl_content.order.nodes:
            if powl_content.order.is_edge(src, dst):
                edges.append((src, dst))
    G = nx.DiGraph()
    G.add_edges_from(edges)
    if transitive_reduction:
        G = nx.transitive_reduction(G)
    return list(G.edges)


def __add_auxiliary_nodes_before_after(
    G: nx.DiGraph, neighbors: dict, type: str = "exclusive_gateway"
):
    for node in neighbors.keys():
        # add the node
        if id(node) in G.nodes:
            # It is handled ad-hoc
            continue
        G.add_node(id(node), content=node, visited=False)
        # Add one exclusive gateway before it and connect it

        gateway = (
            f"ExclusiveGateway_{id(node)}_beforenode"
            if type == "exclusive_gateway"
            else f"ParallelGateway_{id(node)}_beforenode"
        )
        if gateway not in G.nodes:
            G.add_node(gateway, type=type, paired_with=[id(node)], visited=True)
        G.add_edge(gateway, id(node))

        # Add one exclusive gateway after it and connect it
        gateway = (
            f"ExclusiveGateway_{id(node)}_afternode"
            if type == "exclusive_gateway"
            else f"ParallelGateway_{id(node)}_afternode"
        )
        if gateway not in G.nodes:
            G.add_node(gateway, type=type, visited=True)
        G.add_edge(id(node), gateway)
    return G


def __handle_StrictPartialOrder(powl_content: StrictPartialOrder) -> nx.DiGraph:
    """
    Handle the StrictPartialOrder content and return a directed graph.

    Parameters
    ----------
    powl_content : StrictPartialOrder
        The StrictPartialOrder content to handle.

    Returns
    -------
    G : nx.DiGraph
        The directed graph representing the StrictPartialOrder.
    """
    edges = __obtain_edges(powl_content)
    G = nx.DiGraph()
    start_event = f"Start_{id(powl_content)}"
    end_event = f"End_{id(powl_content)}"
    G.add_node(start_event, type="start", visited=True)
    G.add_node(end_event, type="end", visited=True)

    # Construct a dictionary with incoming and outgoing edges for each node
    node_edges = {
        node: {"incoming": [], "outgoing": []} for node in powl_content.order.nodes
    }
    for src, dst in edges:
        node_edges[src]["outgoing"].append(dst)
        node_edges[dst]["incoming"].append(src)

    # Preprocess the graph
    G = __add_auxiliary_nodes_before_after(G, node_edges, type="parallel_gateway")
    start_powl = [node for node, edges in node_edges.items() if not edges["incoming"]]
    end_edges = [node for node, edges in node_edges.items() if not edges["outgoing"]]

    # It always has a diverging and converging gateway
    diverging_gateway = f"ParallelGateway_{id(powl_content)}_diverging"
    converging_gateway = f"ParallelGateway_{id(powl_content)}_converging"
    G.add_node(
        diverging_gateway,
        type="diverging",
        paired_with=[converging_gateway],
        visited=True,
    )
    G.add_node(
        converging_gateway,
        type="converging",
        paired_with=[diverging_gateway],
        visited=True,
    )

    # Connect the start and end events to the gateways
    G.add_edge(start_event, diverging_gateway)
    G.add_edge(converging_gateway, end_event)

    # Now, we connect all of the start edges to the diverging gateway
    for start in start_powl:
        gateway_before_node = f"ParallelGateway_{id(start)}_beforenode"
        G.add_edge(diverging_gateway, gateway_before_node)

    # We connect the end events to the converging gateway
    for end in end_edges:
        gateway_after_node = f"ParallelGateway_{id(end)}_afternode"
        G.add_edge(gateway_after_node, converging_gateway)

    for edge in edges:
        src, dst = edge
        after_src = f"ParallelGateway_{id(src)}_afternode"
        before_dst = f"ParallelGateway_{id(dst)}_beforenode"
        G.add_edge(after_src, before_dst)
    return G


def __generate_submodel(powl_content) -> nx.DiGraph:
    """
    Obtain a submodel from the POWL content.

    Parameters
    ----------
    powl_content : POWL
        The POWL content to extract the submodel from.

    Returns
    -------
    G : nx.DiGraph
        The directed graph representing the submodel.
    """
    G = nx.DiGraph()
    handler_map = {
        SilentTransition: __handle_silent_transition,
        Transition: __handle_transition,
        OperatorPOWL: __handle_operator_powl,
        StrictPartialOrder: __handle_StrictPartialOrder,
        DecisionGraph: __handle_decision_graph,
    }

    if type(powl_content) in handler_map:
        try:
            handler = handler_map[type(powl_content)]
        except Exception as e:
            raise ValueError(
                f"Error handling POWL content of type {type(powl_content)}: {e}"
            )
        G = handler(powl_content)
    else:
        raise ValueError(f"Unsupported POWL content type: {type(powl_content)}")
    return G


def __compose_model(
    G: nx.DiGraph, submodel: nx.DiGraph, current_node: nx.Graph
) -> nx.DiGraph:
    """
    Compose two directed graphs into one.

    Parameters
    ----------
    G1 : nx.DiGraph
        The first directed graph.
    G2 : nx.DiGraph
        The second directed graph.
    current_node : nx.Graph
        The current POWL node that is being processed.

    Returns
    -------
    G : nx.DiGraph
        The composed directed graph.
    """
    predecessors = list(G.predecessors(current_node))
    successors = list(G.successors(current_node))

    start_event_nodes = [n for n, deg in submodel.in_degree() if deg == 0]
    end_event_nodes = [n for n, deg in submodel.out_degree() if deg == 0]
    start_event = start_event_nodes[0]
    end_event = end_event_nodes[0]

    # Remove the current node from the original graph
    G.remove_node(current_node)
    start_nodes = list(submodel.successors(start_event))
    end_nodes = list(submodel.predecessors(end_event))
    if start_event is None or end_event is None:
        raise ValueError(
            f"Submodel for {current_node} does not have start or end event."
        )
    submodel.remove_node(start_event)
    submodel.remove_node(end_event)

    # Now, merge the two graphs
    if len(submodel.nodes) == 0:
        # Just connect predecessors and successors
        if len(predecessors) == 1 and len(successors) == 1:
            # We have one-to-one connection, so we can just connect them
            G.add_edge(predecessors[0], successors[0])
            return G
        else:
            raise ValueError(
                f"Unexpected case for node {current_node}: {predecessors} -> {successors}"
            )

    G = nx.compose(G, submodel)
    if len(predecessors) == 1 and len(start_nodes) == 1:
        # We have one-to-one connection, so we can just connect them
        G.add_edge(predecessors[0], start_nodes[0])
        G.add_edge(end_nodes[0], successors[0])
    elif len(predecessors) >= 1 or len(start_nodes) >= 1:
        # We have many-to-many connection, or many-to-one, or one-to-many
        # We have to add a parallel gateway in between
        exclusive_gateway_diverging = (
            f"ExclusiveGateway_{id(current_node)}_pre_additional"
        )
        # Now, we connect all predecessors to this gateway
        G.add_node(exclusive_gateway_diverging, type="exclusive_gateway", visited=True)
        for predecessor in predecessors:
            G.add_edge(predecessor, exclusive_gateway_diverging)
        for start_node in start_nodes:
            G.add_edge(exclusive_gateway_diverging, start_node)
    else:
        raise ValueError(
            f"Unexpected case for node {current_node}: {predecessors} -> {successors}"
        )
    if len(successors) == 1 and len(end_nodes) == 1:
        # We have one-to-one connection, so we can just connect them
        G.add_edge(end_nodes[0], successors[0])
    elif len(successors) >= 1 or len(end_nodes) >= 1:
        # We have many-to-many connection, or many-to-one, or one-to-many
        # We have to add a parallel gateway in between
        exclusive_gateway_converging = (
            f"ExclusiveGateway_{id(current_node)}_post_additional"
        )
        # Now, we connect all successors to this gateway
        G.add_node(exclusive_gateway_converging, type="exclusive_gateway", visited=True)
        for successor in successors:
            G.add_edge(exclusive_gateway_converging, successor)
        for end_node in end_nodes:
            G.add_edge(end_node, exclusive_gateway_converging)
    else:
        raise ValueError(
            f"Unexpected case for node {current_node}: {predecessors} -> {successors}"
        )
    return G


def expand_model(powl, G: nx.DiGraph):
    """
    Recursively expand the POWL model into a directed graph.

    Parameters
    ----------
    powl : POWL
        The POWL model to expand.
    G : nx.DiGraph
        The directed graph to populate.
    """
    # Identify the node that has the powl we are currently considering
    if isinstance(powl, StartNode) or isinstance(powl, EndNode):
        # Remove them from the graph
        node = next((n for n in G.nodes if G.nodes[n].get("content") is powl), None)
        if node is not None:
            G.remove_node(node)
        # And ignore them as they don't add much value
        return G
    node = next((n for n in G.nodes if G.nodes[n].get("content") is powl), None)
    if node is None:
        return G
    submodel = __generate_submodel(powl)
    if submodel is None:
        return G
    G = __compose_model(G, submodel, node)
    nodes_to_handle = [
        node
        for node in submodel.nodes
        if submodel.nodes[node].get("content") is not None
        and submodel.nodes[node]["visited"] is False
    ]
    for node in nodes_to_handle:
        content = submodel.nodes[node]["content"]
        G = expand_model(content, G)
    return G


def __update_paired_with_relation(G: nx.DiGraph, gateway_to_remove, successor):
    """
    Update the paired_with relation for gateways in the graph.

    Parameters
    ----------
    G : nx.DiGraph
        The directed graph.
    gateway_to_remove : str
        The gateway to remove.
    successor : str
        The successor node to connect to the paired gateway.
    """
    current_gateway = G.nodes[gateway_to_remove]
    if "paired_with" in current_gateway:
        paired_with = current_gateway["paired_with"]
        if isinstance(paired_with, list):
            for paired_gateway in paired_with:
                # find the paired gateway in the graph and update its list
                if "Gateway" not in str(paired_gateway):
                    # We only want to update gateways, not tasks
                    continue
                paired_node = G.nodes.get(paired_gateway, None)
                if paired_node is not None:
                    if "paired_with" in paired_node:
                        # If the paired gateway has a list, append the successor
                        if isinstance(paired_node["paired_with"], list):
                            paired_node["paired_with"].append(successor)
                        else:
                            # If it is not a list, convert it to a list
                            paired_node["paired_with"] = [
                                paired_node["paired_with"],
                                successor,
                            ]
                    else:
                        # If it does not have a paired_with attribute, create it
                        paired_node["paired_with"] = [successor]
                    # Remove current gateway from the paired_with list
                    if paired_gateway in paired_node["paired_with"]:
                        paired_node["paired_with"].remove(paired_gateway)
                    # Add it to the successor's paired_with list
                    if "paired_with" in G.nodes[successor]:
                        if isinstance(G.nodes[successor]["paired_with"], list):
                            G.nodes[successor]["paired_with"].append(paired_gateway)
                        else:
                            G.nodes[successor]["paired_with"] = [
                                G.nodes[successor]["paired_with"],
                                paired_gateway,
                            ]
                    else:
                        G.nodes[successor]["paired_with"] = [paired_gateway]
    return G


def __postprocess_graph(G: nx.DiGraph) -> nx.DiGraph:
    G_copy = G.copy()
    while True:
        gateways = [
            node
            for node, _ in G_copy.nodes(data=True)
            if "Parallel" in str(node) or "Exclusive" in str(node)
        ]
        # Get their predecessors and successors
        for gateway in gateways:
            if gateway not in G_copy.nodes:
                continue
            predecessors = list(G_copy.predecessors(gateway))
            successors = list(G_copy.successors(gateway))
            if len(predecessors) == 1 and len(successors) == 1:
                # We can merge them
                G_copy = __update_paired_with_relation(G_copy, gateway, successors[0])
                G_copy.add_edge(predecessors[0], successors[0])
                G_copy.remove_node(gateway)
        # Check if G and G_copy are the same
        if nx.is_isomorphic(G, G_copy):
            break
        G = G_copy.copy()
    return G_copy


def __print_powl(powl):
    print(powl)


def apply(powl):
    """
    Convert a POWL model to a BPMN model.

    Parameters
    ----------
    powl : POWL
        The POWL model to convert.

    Returns
    -------
    bpmn : BPMN
        The converted BPMN model.
    resulting_graph : nx.DiGraph
        The resulting directed graph representing the POWL model.
    original_element_id_to_id : dict
        A mapping from original element IDs to their ides.
    """
    G = nx.DiGraph()
    # Create the start and end event
    start_event = "StartEvent"
    end_event = "EndEvent"
    G.add_node(start_event, type="startEvent", visited=True)
    G.add_node(end_event, type="endEvent", visited=True)
    G.add_node(id(powl), content=powl, visited=False)
    G.add_edge(start_event, id(powl))
    G.add_edge(id(powl), end_event)
    resulting_graph = expand_model(powl, G)
    resulting_graph = __postprocess_graph(resulting_graph)
    try:
        bpmn, original_element_id_to_id = __transform_to_bpmn(resulting_graph)
    except Exception as e:
        raise ValueError(f"Error transforming graph to BPMN: {e}")
    return bpmn, resulting_graph, original_element_id_to_id


def __transform_to_bpmn(G):
    """
    Transform the graph G into a BPMN file.
    """
    # create the root
    node_dict = {node: {"incoming": [], "outgoing": []} for node in G.nodes()}
    node_object_mapping = {}
    original_element_id_to_id = {}
    for u, v, _ in G.edges(data=True):
        node_dict[u]["outgoing"].append(v)
        node_dict[v]["incoming"].append(u)
    bpmn = bpmn_obj.BPMN()

    for node, attrs in G.nodes(data=True):
        object = None
        ided_id = str(id(str(node)))
        if "Start" in str(node):
            ided_id = f"StartEvent_{ided_id}"
            object = bpmn.StartEvent(id=ided_id)

        elif "End" in str(node):
            ided_id = f"EndEvent_{ided_id}"
            object = bpmn.EndEvent(id=ided_id)

        elif "Parallel" in str(node):
            ided_id = f"ParallelGateway_{ided_id}"
            object = bpmn.ParallelGateway(id=ided_id)

        elif "Exclusive" in str(node):
            ided_id = f"ExclusiveGateway_{ided_id}"
            object = bpmn.ExclusiveGateway(id=ided_id)

        elif "Intermediate" in str(node):

            if "Catch" in str(node):
                ided_id = f"IntermediateCatchEvent_{ided_id}"
                object = bpmn.IntermediateCatchEvent(
                    id=ided_id, name=str(attrs.get("content", ""))
                )

            elif "Throw" in str(node):
                ided_id = f"IntermediateThrowEvent_{ided_id}"
                object = bpmn.IntermediateThrowEvent(
                    id=ided_id, name=str(attrs.get("content", ""))
                )
        else:
            # tasks
            ided_id = f"Task_{ided_id}"
            object = bpmn.Task(id=ided_id, name=str(attrs.get("content", "")))
        original_element_id_to_id[str(node)] = ided_id

        node_object_mapping[node] = object
        for incoming in node_dict[node]["incoming"]:
            if incoming not in node_object_mapping:
                # will be handled later
                continue
            seq_flow = bpmn.SequenceFlow(
                source=node_object_mapping[incoming], target=object
            )
            bpmn.add_flow(seq_flow)
            object.add_in_arc(seq_flow)

        for outgoing in node_dict[node]["outgoing"]:
            if outgoing not in node_object_mapping:
                # will be handled later
                continue
            seq_flow = bpmn.SequenceFlow(
                source=object, target=node_object_mapping[outgoing]
            )
            bpmn.add_flow(seq_flow)
            object.add_out_arc(seq_flow)
        bpmn.add_node(object)

    return bpmn, original_element_id_to_id
