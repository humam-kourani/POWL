from powl.objects.obj import Transition, SilentTransition, StrictPartialOrder, OperatorPOWL, FrequentTransition, \
    DecisionGraph, StartNode, EndNode
import networkx as nx
from pm4py.objects.process_tree.obj import Operator
from typing import List

def __handle_transition(powl_content : Transition) -> nx.DiGraph:
    # Add artificial start and end nodes
    subgraph = nx.DiGraph()
    start_node = f"Start_{hash(powl_content)}"
    end_node = f"End_{hash(powl_content)}"
    subgraph.add_node(start_node, type="start", visited=True)
    subgraph.add_node(end_node, type="end", visited=True)
    subgraph.add_node(hash(powl_content), content = powl_content.label, visited=True)
    # Add the edges start -> transition -> end
    subgraph.add_edge(start_node, hash(powl_content))
    subgraph.add_edge(hash(powl_content), end_node)
    return subgraph

def __handle_silent_transition(powl_content : SilentTransition) -> nx.DiGraph:
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
        exclusive_gateway_diverging = f"ExclusiveGateway_{hash(powl_content)}_diverging"
        exclusive_gateway_converging = f"ExclusiveGateway_{hash(powl_content)}_converging"
        subgraph.add_node(exclusive_gateway_diverging, type="diverging", paired_with = exclusive_gateway_diverging, visited=True)
        subgraph.add_node(exclusive_gateway_converging, type="converging", paired_with = exclusive_gateway_converging, visited=True)
        # Add the parallel gateway for the selfloop
        exclusive_gateway_diverging_sl = f"ParallelGateway_{hash(powl_content)}_diverging_sl"
        exclusive_gateway_converging_sl = f"ParallelGateway_{hash(powl_content)}_converging_sl"
        subgraph.add_node(exclusive_gateway_diverging_sl, type="diverging", paired_with = parallel_gateway_converging, visited=True)
        subgraph.add_node(exclusive_gateway_diverging_sl, type="converging", paired_with = parallel_gateway_diverging, visited=True)
        # Now, add the transition
        subgraph.add_node(hash(powl_content), content = powl_content.label, visited=True)
        # Add the edges start -> exclusive_gateway_diverging
        # exclusive_gateway_diverging -> parallel_gateway_diverging
        # parallel_gateway_diverging -> transition
        # transition -> parallel_gateway_converging
        # parallel_gateway_converging -> exclusive_gateway_converging
        # parallel_gateway_converging -> parallel_gateway_diverging
        # exclusive_gateway_diverging -> exclusive_gateway_converging
        # exclusive_gateway_converging -> end
        subgraph.add_edge(start_node, exclusive_gateway_diverging)
        subgraph.add_edge(exclusive_gateway_diverging, exclusive_gateway_converging_sl)
        subgraph.add_edge(exclusive_gateway_converging_sl, hash(powl_content))
        subgraph.add_edge(hash(powl_content), exclusive_gateway_diverging_sl)
        subgraph.add_edge(exclusive_gateway_diverging_sl, exclusive_gateway_converging)
        subgraph.add_edge(exclusive_gateway_diverging_sl, exclusive_gateway_converging_sl)
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
        exclusive_gateway_diverging = f"ExclusiveGateway_{hash(powl_content)}_diverging"
        exclusive_gateway_converging = f"ExclusiveGateway_{hash(powl_content)}_converging"
        subgraph.add_node(exclusive_gateway_diverging, type="diverging", paired_with = exclusive_gateway_converging, visited=True)
        subgraph.add_node(exclusive_gateway_converging, type="converging", paired_with = exclusive_gateway_diverging, visited=True)
        subgraph.add_node(hash(powl_content), content = powl_content.label, visited=True)
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
        parallel_gateway_diverging = f"ParallelGateway_{hash(powl_content)}_diverging"
        parallel_gateway_converging = f"ParallelGateway_{hash(powl_content)}_converging"
        subgraph.add_node(parallel_gateway_diverging, type="parallel_gateway_diverging", paired_with = parallel_gateway_converging, visited=True)
        subgraph.add_node(parallel_gateway_converging, type="parallel_gateway_converging", paired_with = parallel_gateway_diverging, visited=True)
        subgraph.add_node(hash(powl_content), label = powl_content.label, visited=True)
        # Edges
        subgraph.add_edge(start_node, parallel_gateway_diverging)
        subgraph.add_edge(parallel_gateway_converging, hash(powl_content))
        subgraph.add_edge(hash(powl_content), parallel_gateway_diverging)
        subgraph.add_edge(parallel_gateway_diverging, parallel_gateway_converging)
        subgraph.add_edge(parallel_gateway_diverging, end_node)
    return subgraph
def __handle_operator_powl(powl_content : OperatorPOWL) -> nx.DiGraph:
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
    start_event = f"Start_{hash(powl_content)}"
    end_event = f"End_{hash(powl_content)}"
    G.add_node(start_event, type="start", visited=True)
    G.add_node(end_event, type="end", visited=True)
    operator = powl_content.operator
    if operator == Operator.LOOP and len(powl_content.children) == 2:
        # Add a diverging parallel gateway and a converging parallel gateway
        diverging_gateway = f"ExclusiveGateway_{hash(powl_content)}_diverging"
        converging_gateway = f"ExclusiveGateway_{hash(powl_content)}_converging"
        G.add_node(diverging_gateway, type="diverging", paired_with=converging_gateway, visited=True)
        G.add_node(converging_gateway, type="converging", paired_with=diverging_gateway, visited=True)
        
        do_part = powl_content.children[0]
        redo_part = powl_content.children[1]
        G.add_node(hash(do_part), content=do_part, visited=False)
        G.add_node(hash(redo_part), content=redo_part, visited=False)
        G.add_edge(start_event, converging_gateway)
        G.add_edge(converging_gateway, hash(do_part))
        G.add_edge(hash(do_part), diverging_gateway)
        G.add_edge(diverging_gateway, end_event)
        G.add_edge(diverging_gateway, hash(redo_part))
        G.add_edge(hash(redo_part), diverging_gateway)
    elif operator == Operator.XOR:
        # One exclusive choice gateway
        exclusive_gateway_diverging = f"ExclusiveGateway_{hash(powl_content)}_diverging"
        exclusive_gateway_converging = f"ExclusiveGateway_{hash(powl_content)}_converging"
        G.add_edge(start_event, exclusive_gateway_diverging)
        G.add_edge(exclusive_gateway_converging, end_event)

        for child in powl_content.children:
            if hash(child) not in G.nodes:
                G.add_node(hash(child), content=child, visited=False)
            G.add_edge(exclusive_gateway_diverging, hash(child))
            G.add_edge(hash(child), exclusive_gateway_converging)
    else:
        raise ValueError(f"Unsupported operator: {operator}")
    return G
    
def __handle_decision_graph(powl_content : DecisionGraph) -> nx.DiGraph:
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
    edges = __obtain_edges(powl_content)
    node_edges = {node: {'incoming': [], 'outgoing': []} for node in powl_content.order.nodes}
    added_edges = set()
    for node in node_edges.keys():
        # Check for end and start
        if type(node) is StartNode:
            G.add_node(hash(node), type="start", visited=True)
        elif type(node) is EndNode:
            G.add_node(hash(node), type="end", visited=True)
        # Now add the edges
        if len(node_edges[node]['outgoing']) > 1:
            # Add one exclusive gateway after it and connect it
            exclusive_gateway_node = f"ExclusiveGateway_{hash(node)}_afternode"
            if exclusive_gateway_node not in G.nodes:
                G.add_node(exclusive_gateway_node, type="exclusive_gateway", visited=True)
            for outgoing in node_edges[node]['outgoing']:
                added_edges.add((node, outgoing))
                if hash(outgoing) not in G.nodes:
                    G.add_node(hash(outgoing), content=outgoing, visited=False)
                G.add_edge(exclusive_gateway_node, hash(outgoing))
            G.add_edge(hash(node), exclusive_gateway_node)
        if len(node_edges[node]['incoming']) > 1:
            # Add one exclusive gateway before it and connect it
            exclusive_gateway_node = f"ExclusiveGateway_{hash(node)}_beforenode"
            if exclusive_gateway_node not in G.nodes:
                G.add_node(exclusive_gateway_node, type="exclusive_gateway", paired_with=hash(node), visited=True)
            for incoming in node_edges[node]['incoming']:
                added_edges.add((incoming, node))
                if hash(incoming) not in G.nodes:
                    G.add_node(hash(incoming), content=incoming, visited=False)
                G.add_edge(hash(incoming), exclusive_gateway_node)
            G.add_edge(exclusive_gateway_node, hash(node))
    remaining_edges = set((src, dst) for src, dst in edges if (src, dst) not in added_edges)
    for src, dst in remaining_edges:
        # Connect them directly
        if hash(src) not in G.nodes:
            G.add_node(hash(src), content=src, visited=False)
        if hash(dst) not in G.nodes:
            G.add_node(hash(dst), content=dst, visited=False)
        node_src_to_connect = hash(src) if f'ExclusiveGateway_{hash(src)}_afternode' not in G.nodes else f'ExclusiveGateway_{hash(src)}_afternode'
        node_dst_to_connect = hash(dst) if f'ExclusiveGateway_{hash(dst)}_beforenode' not in G.nodes else f'ExclusiveGateway_{hash(dst)}_beforenode'
        G.add_edge(node_src_to_connect, node_dst_to_connect)
    return G

def __obtain_edges(powl_content):
    edges = []
    for src in powl_content.order.nodes:
        for dst in powl_content.order.nodes:
            if powl_content.order.is_edge(src, dst):
                edges.append((src, dst))
    G = nx.DiGraph()
    G.add_edges_from(edges)
    G_reduced = nx.transitive_reduction(G)
    return list(G_reduced.edges) 

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
    diverging_gateway = f"ParallelGateway_{hash(powl_content)}_diverging"
    converging_gateway = f"ParallelGateway_{hash(powl_content)}_converging"
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
        G.add_edge(hash(end), converging_gateway)
    added_edges = set()
    for node in node_edges.keys():
        if hash(node) not in G.nodes:
            G.add_node(hash(node), content = node, visited = False)
        # Check if it has multiple outgoing edges
        # If so, then we need to add a parallel gateway after it
        if len(node_edges[node]['outgoing']) > 1:
            # Add one parallel gateway after it and connect it
            parallel_gateway_node = f"ParallelGateway_{hash(node)}_afternode"
            G.add_node(parallel_gateway_node, type="parallel_gateway", visited=True)
            G.add_edge(hash(node), parallel_gateway_node)
            # connect all of the outgoing edges to the parallel gateway
            for outgoing in node_edges[node]['outgoing']:
                added_edges.add((node, outgoing))
                if hash(outgoing) not in G.nodes:
                    G.add_node(hash(outgoing), content = outgoing, visited = False)
                G.add_edge(parallel_gateway_node, hash(outgoing))
        if len(node_edges[node]['incoming']) > 1:
            # Add one parallel gateway before it and connect it
            parallel_gateway_node = f"ParallelGateway_{hash(node)}_beforenode"
            G.add_node(parallel_gateway_node, type="parallel_gateway", paired_with = hash(node), visited=True)
            G.add_edge(parallel_gateway_node, hash(node))
            # connect all of the incoming edges to the parallel gateway
            for incoming in node_edges[node]['incoming']:
                added_edges.add((incoming, node))
                if hash(incoming) not in G.nodes:
                    G.add_node(hash(incoming), content = incoming, visited = False)
                G.add_edge(hash(incoming), parallel_gateway_node)
    remaining_edges = set((src, dst) for src, dst in edges if (src, dst) not in added_edges)
    for src, dst in remaining_edges:
        # Connect them directly
        if hash(src) not in G.nodes:
            G.add_node(hash(src), content=src, visited=False)
        if hash(dst) not in G.nodes:
            G.add_node(hash(dst), content=dst, visited=False)
        G.add_edge(hash(src), hash(dst))
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

    if isinstance(powl_content, SilentTransition):
        G = __handle_silent_transition(powl_content)
        print(f"Handled silent transition: {powl_content}")

    elif isinstance(powl_content, FrequentTransition):
        G = __handle_frequent_transition(powl_content)
        print(f"Handled frequent transition: {powl_content}")

    elif isinstance(powl_content, Transition):
        # That's a base case
        G = __handle_transition(powl_content)
        print(f"Handled transition: {powl_content}")

    elif isinstance(powl_content, OperatorPOWL):
        G = __handle_operator_powl(powl_content)
        print(f"Handled operator POWL: {powl_content}")
    elif isinstance(powl_content, StrictPartialOrder):
        G = __handle_StrictPartialOrder(powl_content)
        print(f"Handled strict partial order: {powl_content}")
    elif isinstance(powl_content, DecisionGraph):
        G = __handle_decision_graph(powl_content)
        print(f"Handled decision graph: {powl_content}")
    else:
        raise ValueError(f"Unsupported POWL content type: {type(powl_content)}")
    return G
    
def __compose_model(G : nx.DiGraph, submodel : nx.DiGraph, current_node : nx.Graph) -> nx.DiGraph:
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
    G.remove_node(hash(current_node))
    start_nodes = list(submodel.successors(start_event))
    end_nodes = list(submodel.predecessors(end_event))
    if start_event is None or end_event is None:
        raise ValueError(f"Submodel for {current_node} does not have start or end event.")
    print(f"Submodel had {len(submodel.nodes)} nodes and {len(submodel.edges)} edges.")
    submodel.remove_node(start_event)
    submodel.remove_node(end_event)
    print(f"Submodel now has {len(submodel.nodes)} nodes and {len(submodel.edges)} edges.")

    # Now, merge the two graphs
    if len(submodel.nodes) == 0:
        # Just connect predecessors and successors
        if len(predecessors) == 1 and len(successors) == 1:
            # We have one-to-one connection, so we can just connect them
            G.add_edge(predecessors[0], successors[0])
            return G
        elif len(predecessors) >= 1 or len(successors) >= 1:
            # Add a gateway in between
            exclusive_gateway = f"ExclusiveGateway_{hash(current_node)}_additional"
            G.add_node(exclusive_gateway, type="exclusive_gateway", visited=True)
            for predecessor in predecessors:
                G.add_edge(predecessor, exclusive_gateway)
            for successor in successors:
                G.add_edge(exclusive_gateway, successor)
        return G
        

    G = nx.compose(G, submodel)
    if len(predecessors) == 1 and len(start_nodes) == 1:
        # We have one-to-one connection, so we can just connect them
        G.add_edge(predecessors[0], start_nodes[0])
        G.add_edge(end_nodes[0], successors[0])
    elif len(predecessors) >= 1 or len(start_nodes) >= 1:
        # We have many-to-many connection, or many-to-one, or one-to-many
        # We have to add a parallel gateway in between
        exclusive_gateway_diverging = f"ExclusiveGateway_{hash(current_node)}_pre_additional"
        # Now, we connect all predecessors to this gateway
        G.add_node(exclusive_gateway_diverging, type="exclusive_gateway", visited=True)
        for predecessor in predecessors:
            G.add_edge(predecessor, exclusive_gateway_diverging)
        for start_node in start_nodes:
            G.add_edge(exclusive_gateway_diverging, start_node)
    else:
        raise ValueError(f"Unexpected case for node {current_node}: {predecessors} -> {successors}")
    if len(successors) == 1 and len(end_nodes) == 1:
        # We have one-to-one connection, so we can just connect them
        G.add_edge(end_nodes[0], successors[0])
    elif len(successors) >= 1 or len(end_nodes) >= 1:
        # We have many-to-many connection, or many-to-one, or one-to-many
        # We have to add a parallel gateway in between
        exclusive_gateway_converging = f"ExclusiveGateway_{hash(current_node)}_post_additional"
        # Now, we connect all successors to this gateway
        G.add_node(exclusive_gateway_converging, type="exclusive_gateway", visited=True)
        for successor in successors:
            G.add_edge(exclusive_gateway_converging, successor)
        for end_node in end_nodes:
            G.add_edge(end_node, exclusive_gateway_converging)
    else:
        raise ValueError(f"Unexpected case for node {current_node}: {predecessors} -> {successors}")
    return G
        

def expand_model(powl, G : nx.DiGraph):
    """
    Recursively expand the POWL model into a directed graph.

    Parameters
    ----------
    powl : POWL
        The POWL model to expand.
    G : nx.DiGraph
        The directed graph to populate.
    """
    print(f'Expanding model for {powl} of type {type(powl)}')
    # Identify the node that has the powl we are currently considering
    if isinstance(powl, StartNode) or isinstance(powl, EndNode):
        # Remove them from the graph
        node = next((n for n in G.nodes if G.nodes[n].get('content') is powl), None)
        if node is not None:
            G.remove_node(node)
        # And ignore them as they don't add much value
        return G
    node = next((n for n in G.nodes if G.nodes[n].get('content') is powl), None)
    if node is None:
        print(f'The content {powl} is not in the graph.')
        return G
    submodel = __generate_submodel(powl)
    if submodel is None:
        print(f'Submodel for {powl} is empty.')
        return G
    G = __compose_model(G, submodel, node)
    nodes_to_handle = [node for node in submodel.nodes if submodel.nodes[node].get('content') is not None and submodel.nodes[node]['visited'] is False]
    print('=' * 20)
    for node in nodes_to_handle:
        print(f'Child of powl {powl}: {node}')
        content = submodel.nodes[node]['content']
        G = expand_model(content, G)
    return G
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
    G.add_node(start_event, type="startEvent", visited=True)
    G.add_node(end_event, type="endEvent", visited=True)
    G.add_node(hash(powl), content = powl, visited = False)
    G.add_edge(start_event, hash(powl))
    G.add_edge(hash(powl), end_event)
    resulting_graph = (expand_model(powl, G))
    # Export the graph 
    import pickle
    with open('test.gpickle', 'wb') as f:
        pickle.dump(resulting_graph, f, pickle.HIGHEST_PROTOCOL)

    return resulting_graph


