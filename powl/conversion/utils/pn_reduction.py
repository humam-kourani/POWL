from itertools import combinations
from typing import Union

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.utils import petri_utils as pn_util


def id_generator():
    count = 1
    while True:
        yield f"id{count}"
        count += 1


def add_arc_from_to(
    source: Union[PetriNet.Place, PetriNet.Transition],
    target: Union[PetriNet.Transition, PetriNet.Place],
    net: PetriNet,
):
    arc = PetriNet.Arc(source, target)
    net.arcs.add(arc)
    source.out_arcs.add(arc)
    target.in_arcs.add(arc)


def get_pre_places(place):
    preset_transitions = pn_util.pre_set(place)
    preset_places = set()
    for t in preset_transitions:
        if t.label or len(t.in_arcs) != 1 or len(t.out_arcs) != 1:
            return None, None
        else:
            preset_places.add(list(t.in_arcs)[0].source)
    return preset_places, preset_transitions


def get_post_nodes(place):
    postset_transitions = pn_util.post_set(place)
    postset_places = set()
    for t in postset_transitions:
        if t.label or len(t.in_arcs) != 1 or len(t.out_arcs) != 1:
            return None, None
        else:
            postset_places.add(list(t.out_arcs)[0].target)
    return postset_places, postset_transitions


def merge_places_connected_with_silent_transition(net, source, sink):
    all_silent_transitions = [t for t in net.transitions if not t.label]

    reduced = True
    while reduced:
        reduced = False
        for t in all_silent_transitions:
            in_arcs = list(t.in_arcs)
            out_arcs = list(t.out_arcs)

            if len(in_arcs) == len(out_arcs) == 1:
                p1 = in_arcs[0].source
                p2 = out_arcs[0].target

                if p1 != source and p2 != sink:
                    if len(p1.out_arcs) == 1:
                        for arc in list(p1.in_arcs):
                            add_arc_from_to(arc.source, p2, net)
                        pn_util.remove_place(net, p1)
                        pn_util.remove_transition(net, t)
                        reduced = True
                        break
                    elif len(p2.in_arcs) == 1:
                        for arc in list(p2.out_arcs):
                            add_arc_from_to(p1, arc.target, net)
                        pn_util.remove_place(net, p2)
                        pn_util.remove_transition(net, t)
                        reduced = True
                        break
    return net


def merge_places_with_identical_preset_or_postset(net, source, sink):
    all_places = [p for p in net.places if p not in {source, sink}]
    for p1, p2 in combinations(all_places, 2):
        pre1_p, pre1_t = get_pre_places(p1)
        pre2_p, pre2_t = get_pre_places(p2)
        post1_p, post1_t = get_post_nodes(p1)
        post2_p, post2_t = get_post_nodes(p2)

        if pre1_p and pre2_p and pre1_p == pre2_p:
            for t in pn_util.post_set(p2):
                add_arc_from_to(p1, t, net)
            for silent_t in pre2_t:
                pn_util.remove_transition(net, silent_t)
            pn_util.remove_place(net, p2)
            return merge_places_with_identical_preset_or_postset(net, source, sink)

        if post1_p and post2_p and post1_p == post2_p:
            for t in pn_util.pre_set(p2):
                add_arc_from_to(t, p1, net)
            for silent_t in post2_t:
                pn_util.remove_transition(net, silent_t)
            pn_util.remove_place(net, p2)
            return merge_places_with_identical_preset_or_postset(net, source, sink)

    return net
