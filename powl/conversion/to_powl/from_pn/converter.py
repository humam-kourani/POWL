from pm4py import PetriNet

from powl.objects.BinaryRelation import BinaryRelation
from powl.objects.obj import POWL, StrictPartialOrder, DecisionGraph, OperatorPOWL, Operator, SilentTransition

from powl.conversion.to_powl.from_pn.utils.cut_detection import (
    mine_base_case,
    mine_choice_graph,
    mine_partial_order,
    mine_self_loop, mine_skip,
)

from powl.conversion.to_powl.from_pn.utils.preprocessing import (
    preprocess,
    validate_workflow_net, make_self_loop_explicit,
)
from powl.conversion.to_powl.from_pn.utils.subnet_creation import (
    apply_projection, clone_subnet,
)
from powl.conversion.to_powl.from_pn.utils.weak_reachability import (
    get_simplified_reachability_graph,
)


def convert_workflow_net_to_powl(net: PetriNet) -> POWL:
    """
    Convert a Petri net to a POWL model.

    Parameters:
    - net: PetriNet

    Returns:
    - POWL model
    """
    start_place, end_place = validate_workflow_net(net)
    net = preprocess(net)
    res = __translate_petri_to_powl(net, start_place, end_place)
    res = res.reduce_silent_transitions(add_empty_paths=True)
    return res.simplify()


def __translate_petri_to_powl(
    net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place
) -> POWL:

    net, start_place, end_place = make_self_loop_explicit(net, start_place, end_place)

    base_case = mine_base_case(net)
    if base_case:
        return base_case

    # self_loop = mine_self_loop(net, start_place, end_place)
    # if self_loop:
    #     return __translate_self_loop(
    #         net, self_loop[0], self_loop[1], self_loop[2], self_loop[3]
    #     )
    #
    # skip = mine_skip(net, start_place, end_place)
    # if skip:
    #     return __translate_xor(
    #         net, skip[0], skip[1], skip[2]
    #     )

    reachability_map = get_simplified_reachability_graph(net)

    partition = mine_partial_order(net, end_place, reachability_map)
    if len(partition) > 1:
        return __translate_partial_order(net, partition, start_place, end_place)

    partition = mine_choice_graph(net)
    if len(partition) > 1:
        return __translate_choice_graph(net, partition, start_place, end_place)


    raise Exception(
        f"Failed to detected a POWL structure over the following transitions: {net.transitions}"
    )


def __validate_partial_order(po: StrictPartialOrder):
    po.order.add_transitive_edges()
    if po.order.is_irreflexive():
        return po
    else:
        raise Exception("Conversion failed!")


def __translate_to_binary_relation(
    net, transition_groups, i_place: PetriNet.Place, f_place: PetriNet.Place, enforce_unique_connection_points
):

    groups = [tuple(g) for g in transition_groups]
    transition_to_group_map = {transition: g for g in groups for transition in g}

    group_start_places = {g: set() for g in groups}
    group_end_places = {g: set() for g in groups}
    temp_po = BinaryRelation(groups)
    start_groups = set()
    end_groups = set()

    for p in net.places:
        sources = {arc.source for arc in p.in_arcs}
        targets = {arc.target for arc in p.out_arcs}

        # if p is start place and (p -> t), then p should be a start place in the subnet that contains t
        if p == i_place:
            for t in targets:
                group = transition_to_group_map[t]
                group_start_places[group].add(p)
                start_groups.add(group)
        # if p is end place and (t -> p), then p should be end place in the subnet that contains t
        if p == f_place:
            for t in sources:
                group = transition_to_group_map[t]
                group_end_places[group].add(p)
                end_groups.add(group)

        # if (t1 -> p -> t2) and t1 and t2 are in different subsets, then add an edge in the partial order
        # and set p as end place in g1 and as start place in g2
        for t1 in sources:
            group_1 = transition_to_group_map[t1]
            for t2 in targets:
                group_2 = transition_to_group_map[t2]
                if group_1 != group_2:
                    temp_po.add_edge(group_1, group_2)
                    group_end_places[group_1].add(p)
                    group_start_places[group_2].add(p)

    group_to_powl_map = {}
    children = []
    for group in groups:

        subnet, subnet_start_place, subnet_end_place = apply_projection(
            net, set(group), group_start_places[group], group_end_places[group], enforce_unique_connection_points
        )
        child = __translate_petri_to_powl(subnet, subnet_start_place, subnet_end_place)

        group_to_powl_map[group] = child
        children.append(child)

    rel = BinaryRelation(children)
    for source in temp_po.nodes:
        new_source = group_to_powl_map[source]
        for target in temp_po.nodes:
            if temp_po.is_edge(source, target):
                new_target = group_to_powl_map[target]
                rel.add_edge(new_source, new_target)
    return rel, [group_to_powl_map[g] for g in start_groups], [group_to_powl_map[g] for g in end_groups]


def __translate_partial_order(
    net, transition_groups, i_place: PetriNet.Place, f_place: PetriNet.Place
):

    rel, _, _ = __translate_to_binary_relation(net,
                                               transition_groups,
                                               i_place,
                                               f_place,
                                               enforce_unique_connection_points=False)
    po = StrictPartialOrder(rel.nodes)
    po.order = rel
    po = __validate_partial_order(po)
    return po


def __translate_choice_graph(
    net, transition_groups, i_place: PetriNet.Place, f_place: PetriNet.Place
):

    rel, start_nodes, end_nodes = __translate_to_binary_relation(net,
                                                                 transition_groups,
                                                                 i_place,
                                                                 f_place,
                                                                 enforce_unique_connection_points=True)
    cg = DecisionGraph(rel, start_nodes=start_nodes, end_nodes=end_nodes, empty_path=False)
    cg.validate_connectivity()
    return cg


def __create_sub_powl_model(
    net,
    branch: set[PetriNet.Transition],
    start_place: PetriNet.Place,
    end_place: PetriNet.Place,
):
    subnet, subnet_start_place, subnet_end_place = clone_subnet(
        net, branch, start_place, end_place
    )
    powl = __translate_petri_to_powl(subnet, subnet_start_place, subnet_end_place)
    return powl


def __translate_self_loop(
    net: PetriNet,
    do_nodes,
    redo_nodes,
    start_place: PetriNet.Place,
    end_place: PetriNet.Place,
) -> OperatorPOWL:
    do_powl = __create_sub_powl_model(net, do_nodes, start_place, end_place)
    redo_powl = __create_sub_powl_model(net, redo_nodes, end_place, start_place)
    loop_operator = OperatorPOWL(operator=Operator.LOOP, children=[do_powl, redo_powl])
    return loop_operator


def __translate_xor(
    net: PetriNet,
    children,
    start_place: PetriNet.Place,
    end_place: PetriNet.Place,
) -> OperatorPOWL:
    submodel = __create_sub_powl_model(net, children, start_place, end_place)
    xor_operator = OperatorPOWL(operator=Operator.XOR, children=[submodel, SilentTransition()])
    return xor_operator