from copy import copy

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.utils import petri_utils as pn_util

from powl.conversion.to_powl.from_pn.utils.subnet_creation import pn_transition_to_powl, add_arc_from_to, clone_place
from powl.conversion.to_powl.from_pn.utils.weak_reachability import (
    get_reachable_without_looping,
)


def mine_base_case(net: PetriNet):
    if len(net.transitions) == 1 and len(net.places) == 2 == len(net.arcs):
        activity = list(net.transitions)[0]
        powl_transition = pn_transition_to_powl(activity)
        return powl_transition
    return None


def mine_self_loop(
    net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place
):

    if len(start_place.out_arcs) == 1 and len(end_place.in_arcs) == 1:
        t = pn_util.pre_set(end_place)
        if t in pn_util.post_set(start_place) and isinstance(t, PetriNet.Transition) and not t.label:
            return {t}, copy(net.transitions), start_place, end_place

    if len(start_place.in_arcs) == 1 and len(end_place.out_arcs) == 1:
        t = pn_util.pre_set(start_place)
        if t in pn_util.post_set(end_place) and isinstance(t, PetriNet.Transition) and not t.label:
            return copy(net.transitions), {t}, start_place, end_place

    return None


def mine_skip(
    net: PetriNet, start_place: PetriNet.Place, end_place: PetriNet.Place
):

    if len(start_place.in_arcs) == 0 and len(end_place.out_arcs) == 0:
        silent_connectors = [
            t for t in pn_util.pre_set(end_place) if isinstance(t, PetriNet.Transition)
                                                     and not t.label and len(t.out_arcs) == 1
                                                     and len(t.in_arcs) == 1
                                                     and t in pn_util.post_set(start_place)
        ]
        if len(silent_connectors) > 0:
            other_children = {t for t in net.transitions if t not in silent_connectors}
            if len(other_children) > 0:
                return other_children, start_place, end_place

    return None


def mine_partial_order(net, end_place, reachability_map):
    partition = [{t} for t in net.transitions]

    for place in net.places:
        out_size = len(place.out_arcs)
        if out_size > 1 or (place == end_place and out_size > 0):
            xor_branches = []
            for start_transition in pn_util.post_set(place):
                new_branch = {
                    node
                    for node in reachability_map[start_transition]
                    if isinstance(node, PetriNet.Transition)
                }
                xor_branches.append(new_branch)
            union_of_branches = set().union(*xor_branches)
            if place == end_place:
                not_in_every_branch = union_of_branches
            else:
                intersection_of_branches = set.intersection(*xor_branches)
                not_in_every_branch = union_of_branches - intersection_of_branches
            if len(not_in_every_branch) > 1:
                partition = __combine_parts(not_in_every_branch, partition)

    return partition


def mine_choice_graph(net):
    partition = [{t} for t in net.transitions]

    split_transitions = [transition for transition in net.transitions if  len(transition.out_arcs) > 1]
    join_transitions = [transition for transition in net.transitions if len(transition.in_arcs) > 1]

    for split in split_transitions:
        split_branches = []
        for start_place in pn_util.post_set(split):
            new_branch = {
                node
                for node in get_reachable_without_looping(start_place, split)
                if isinstance(node, PetriNet.Transition)
            }
            split_branches.append(new_branch)
        union_of_branches = set().union(*split_branches)
        intersection_of_branches = set.intersection(*split_branches)
        not_in_every_branch = union_of_branches - intersection_of_branches
        if len(not_in_every_branch) > 1:
            not_in_every_branch.add(split)
            partition = __combine_parts(not_in_every_branch, partition)
        else:
            raise Exception("This should not happen!")

    for join in join_transitions:
        pre_transitions = {join}
        for pre_place in pn_util.pre_set(join):
            pre_transitions = pre_transitions | pn_util.pre_set(pre_place)
        partition = __combine_parts(pre_transitions, partition)

    return partition


def __combine_parts(
    transitions_to_group_together: set[PetriNet.Transition],
    partition: list[set[PetriNet.Transition]],
):
    new_partition = []
    new_combined_group = set()

    for part in partition:

        if part & transitions_to_group_together:
            new_combined_group.update(part)
        else:
            new_partition.append(part)

    if new_combined_group:
        new_partition.append(new_combined_group)

    return new_partition