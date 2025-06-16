from powl.conversion.utils.pn_reduction import merge_places_connected_with_silent_transition, \
    merge_places_with_identical_preset_or_postset
from powl.objects.obj import Transition, SilentTransition, StrictPartialOrder, OperatorPOWL, FrequentTransition, \
    DecisionGraph
import networkx as nx
    
def __handle_transition(powl_content):
    # Add artificial start and end nodes
    subgraph = nx.DiGraph()
    start_node = f"Start_{hash(powl_content)}"
    end_node = f"End_{hash(powl_content)}"
    subgraph.add_node(start_node, type="start", visited=True)
    subgraph.add_node(end_node, type="end", visited=True)
    subgraph.add_node(hash(powl_content), label = powl_content.label, visited=True)
    # Add the edges start -> transition -> end
    subgraph.add_edge(start_node, hash(powl_content))
    subgraph.add_edge(hash(powl_content), end_node)
    return subgraph

def __handle_silent_transition(powl_content):
    # That's a silent transition
    subgraph = nx.DiGraph()
    start_node = f"Start_{hash(powl_content)}"
    end_node = f"End_{hash(powl_content)}"
    subgraph.add_node(start_node, type="start", visited=True)
    subgraph.add_node(end_node, type="end", visited=True)
    # Add the edges start -> silent transition -> end
    subgraph.add_node(start_node, visited=True)
    subgraph.add_node(end_node, visited=True)
    subgraph.add_edge(start_node, end_node)
    return subgraph

def __handle_frequent_transition(powl_content : FrequentTransition):
    subgraph = nx.DiGraph()
    if powl_content.skippable and powl_content.selfloop:
        # start and end event as always
        start_node = f"Start_{hash(powl_content)}"
        end_node = f"End_{hash(powl_content)}"
        subgraph.add_node(start_node, type="start", visited=True)
        subgraph.add_node(end_node, type="end", visited=True)
        # We have to add two pairs of gateways
        # First the exclusive gateway for the skip
        exclusive_gateway_diverging = f"ExclusiveGateway_{hash(powl_content)}"
        exclusive_gateway_converging = f"ExclusiveGateway_{hash(powl_content)}"
        subgraph.add_node(exclusive_gateway_diverging, type="diverging", paired_with = exclusive_gateway_diverging, visited=True)
        subgraph.add_node(exclusive_gateway_converging, type="converging", paired_with = exclusive_gateway_converging, visited=True)
        # Add the parallel gateway for the selfloop
        parallel_gateway_diverging = f"ParallelGateway_{hash(powl_content)}"
        parallel_gateway_converging = f"ParallelGateway_{hash(powl_content)}"
        subgraph.add_node(parallel_gateway_diverging, type="diverging", paired_with = parallel_gateway_converging, visited=True)
        subgraph.add_node(parallel_gateway_converging, type="converging", paired_with = parallel_gateway_diverging, visited=True)
        # Now, add the transition
        subgraph.add_node(hash(powl_content), label = powl_content.label, visited=True)
        # Add the edges start -> exclusive_gateway_diverging
        # exclusive_gateway_diverging -> parallel_gateway_diverging
        # parallel_gateway_diverging -> transition
        # transition -> parallel_gateway_converging
        # parallel_gateway_converging -> exclusive_gateway_converging
        # parallel_gateway_converging -> parallel_gateway_diverging
        # exclusive_gateway_diverging -> exclusive_gateway_converging
        # exclusive_gateway_converging -> end
        subgraph.add_edge(start_node, exclusive_gateway_diverging)
        subgraph.add_edge(exclusive_gateway_diverging, parallel_gateway_diverging)
        subgraph.add_edge(parallel_gateway_diverging, hash(powl_content))
        subgraph.add_edge(hash(powl_content), parallel_gateway_converging)
        subgraph.add_edge(parallel_gateway_converging, exclusive_gateway_converging)
        subgraph.add_edge(parallel_gateway_converging, parallel_gateway_diverging)
        subgraph.add_edge(exclusive_gateway_diverging, exclusive_gateway_converging)
        subgraph.add_edge(exclusive_gateway_converging, end_node)
    elif powl_content.skippable:
        # This one is easy
        # start_event -> exclusive_gateway_diverging
        # exclusive_gateway_diverging -> exclusive_gateway_converging
        # exclusive_gateway_diverging -> transition
        # transition -> exclusive_gateway_converging
        # exclusive_gateway_converging -> end_event
        start_node = f"Start_{hash(powl_content)}"
        end_node = f"End_{hash(powl_content)}"
        subgraph.add_node(start_node, type="start", visited=True)
        subgraph.add_node(end_node, type="end", visited=True)
        exclusive_gateway_diverging = f"ExclusiveGateway_{hash(powl_content)}"
        exclusive_gateway_converging = f"ExclusiveGateway_{hash(powl_content)}"
        subgraph.add_node(exclusive_gateway_diverging, type="diverging", paired_with = exclusive_gateway_converging, visited=True)
        subgraph.add_node(exclusive_gateway_converging, type="converging", paired_with = exclusive_gateway_diverging, visited=True)
        subgraph.add_node(hash(powl_content), label = powl_content.label, visited=True)
        subgraph.add_edge(start_node, exclusive_gateway_diverging)
        subgraph.add_edge(exclusive_gateway_diverging, hash(powl_content))
        subgraph.add_edge(hash(powl_content), exclusive_gateway_converging)
        subgraph.add_edge(exclusive_gateway_converging, end_node)
        subgraph.add_edge(exclusive_gateway_diverging, exclusive_gateway_converging)
    else:
        # This is for selfloop and transitions that can happen between [n, m] times
        # Same as previous one but with a parallel gateway
        # start_event -> parallel_gateway_diverging
        # parallel_gateway_diverging -> transition
        # transition -> parallel_gateway_converging
        # parallel_gateway_converging -> parallel_gateway_diverging
        # parallel_gateway_converging -> end_event
        start_node = f"Start_{hash(powl_content)}"
        end_node = f"End_{hash(powl_content)}"
        subgraph.add_node(start_node, type="start", visited=True)
        subgraph.add_node(end_node, type="end", visited=True)
        parallel_gateway_diverging = f"ParallelGateway_{hash(powl_content)}"
        parallel_gateway_converging = f"ParallelGateway_{hash(powl_content)}"
        subgraph.add_node(parallel_gateway_diverging, type="parallel_gateway_diverging", paired_with = parallel_gateway_converging, visited=True)
        subgraph.add_node(parallel_gateway_converging, type="parallel_gateway_converging", paired_with = parallel_gateway_diverging, visited=True)
        subgraph.add_node(hash(powl_content), label = powl_content.label, visited=True)
        # Edges
        subgraph.add_edge(start_node, parallel_gateway_diverging)
        subgraph.add_edge(parallel_gateway_diverging, hash(powl_content))
        subgraph.add_edge(hash(powl_content), parallel_gateway_converging)
        subgraph.add_edge(parallel_gateway_converging, parallel_gateway_diverging)
        subgraph.add_edge(parallel_gateway_converging, end_node)
    return subgraph
def __obtain_edges(powl_content):
    edges = []
    for src in powl_content.order.nodes:
        for dst in powl_content.order.nodes:
            if powl_content.order.is_edge(src, dst):
                edges.append((src, dst))
    return edges
 

def __handle_StrictPartialOrder(powl_content : StrictPartialOrder) -> nx.DiGraph:
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
    start_event = f"Start_{hash(powl_content)}"
    end_event = f"End_{hash(powl_content)}"
    G.add_node(start_event, type="start", visited=True)
    G.add_node(end_event, type="end", visited=True)
    # Construct a dictionary with incoming and outgoing edges for each node
    node_edges = {node: {'incoming': [], 'outgoing': []} for node in powl_content.order.nodes}
    for src, dst in edges:
        node_edges[src]['outgoing'].append(dst)
        node_edges[dst]['incoming'].append(src)
    start_powl = [node for node, edges in node_edges.items() if not edges['incoming']]
    end_edges = [node for node, edges in node_edges.items() if not edges['outgoing']]
    # It always has a diverging and converging gateway
    diverging_gateway = f"ParallelGateway_{hash(powl_content)}"
    converging_gateway = f"ParallelGateway_{hash(powl_content)}"
    G.add_node(diverging_gateway, type="diverging", paired_with=converging_gateway, visited=True)
    G.add_node(converging_gateway, type="converging", paired_with=diverging_gateway, visited=True)
    # Connect the start and end events to the gateways
    G.add_edge(start_event, diverging_gateway)
    G.add_edge(converging_gateway, end_event)
    # Now, we connect all of the start edges to the diverging gateway
    for start in start_powl:
        G.add_node(hash(start), content = start, visited = False)
        G.add_edge(diverging_gateway, hash(start))
    # We connect the end events to the converging gateway
    for end in end_edges:
        G.add_node(hash(end), content = end, visited = False)
        G.add_edge(end, converging_gateway)
    for node in node_edges.keys():
        G.add_node(hash(node), content = node, visited = False)
        # Check if it has multiple outgoing edges
        # If so, then we need to add a parallel gateway after it
        if len(node_edges[node]['outgoing']) > 1:
            pass
    



    
    
    









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
    if type(powl_content) == Transition:
        # That's a base case
        G = __handle_transition(powl_content, G)

    elif type(powl_content) == SilentTransition:
        G = __handle_silent_transition(powl_content)
    elif type(powl_content) == FrequentTransition:
        pass
    

def expand_recursively(powl, G : nx.DiGraph):
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
    node = [n for n in G.nodes if G.nodes[n].get('content') == powl][0]
    parents = list(G.predecessors(node))
    children = list(G.successors(node))
    print(f'Current node: {node}, Parents: {parents}, Children: {children}')
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
    """
    G = nx.DiGraph()
    # Create the start and end event
    start_event = "StartEvent"
    end_event = "EndEvent"
    G.add_node(start_event, type="start", visited=True)
    G.add_node(end_event, type="end", visited=True)
    G.add_node(hash(powl), content = powl, visited = False)
    G.add_edge(start_event, hash(powl))
    G.add_edge(hash(powl), end_event)
    G = expand_recursively(powl, G, prev_id=1)

    

