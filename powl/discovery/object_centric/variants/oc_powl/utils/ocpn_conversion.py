from powl.conversion.utils.pn_reduction import add_arc_from_to
from powl.objects.obj import Transition, SilentTransition, OperatorPOWL, Operator, Sequence, StrictPartialOrder, \
    DecisionGraph
from powl.objects.oc_powl import ObjectCentricPOWL, LeafNode, ComplexModel
from pm4py.objects.petri_net.obj import PetriNet, Marking


def generate_flower_model(activity_labels):
    return OperatorPOWL(operator=Operator.LOOP,
                        children=[SilentTransition(),
                            OperatorPOWL(operator=Operator.XOR, children=
                            [Transition(label=a) for a in activity_labels])])


def clone_workflow_net(
    net: PetriNet,
    im: Marking,
    fm: Marking,
    name_suffix: str = "_copy",
    label_delimiter: str = "<|>"
):
    """
    Create a deep copy of a Petri net and its initial/final markings.
    - Appends `name_suffix` to place/transition names.
    - If a transition label contains `label_delimiter`, keeps only the part before it.
    """
    mapping = {}

    new_net = PetriNet(f"{net.name}{name_suffix}")

    for place in net.places:
        new_place = PetriNet.Place(f"{place.name}{name_suffix}")
        new_net.places.add(new_place)
        mapping[place] = new_place

    for t in net.transitions:
        label = t.label
        if label and label_delimiter in label:
            label = label.split(label_delimiter, 1)[0].strip()
        new_t = PetriNet.Transition(name=f"{t.name}{name_suffix}", label=label)
        new_net.transitions.add(new_t)
        mapping[t] = new_t

    for arc in net.arcs:
        add_arc_from_to(mapping[arc.source], mapping[arc.target], new_net)

    new_im = Marking({mapping[p]: im[p] for p in im})
    new_fm = Marking({mapping[p]: fm[p] for p in fm})

    return new_net, new_im, new_fm


def project_oc_powl(oc_powl: ObjectCentricPOWL, object_type, divergent_partitions):

    if isinstance(oc_powl, LeafNode):
        if oc_powl.activity == "" or object_type not in oc_powl.related:
            return SilentTransition()
        return Transition(label=oc_powl.activity)

    assert isinstance(oc_powl, ComplexModel)
    related_activities = set([a for a in oc_powl.get_activities()
        if object_type in oc_powl.get_type_information()[(a,"rel")] and a != ""])

    if not related_activities:
        return SilentTransition()

    if all(object_type in oc_powl.get_type_information()[(a,"div")] for a in related_activities):
        return OperatorPOWL(operator=Operator.LOOP,
            children=[SilentTransition(),OperatorPOWL(operator=Operator.XOR,
                                                      children= [Transition(label=a) for a in related_activities])])

    else:
        loop = isinstance(oc_powl.flat_model, OperatorPOWL) and oc_powl.flat_model.operator == Operator.LOOP
        parallel = isinstance(oc_powl.flat_model, StrictPartialOrder) and len(oc_powl.flat_model.order.edges) == 0
        if loop:
            return OperatorPOWL(operator=Operator.LOOP,
                               children=[project_oc_powl(sub, object_type, divergent_partitions) for sub in oc_powl.oc_children])
        if parallel:
            return StrictPartialOrder([project_oc_powl(sub, object_type, divergent_partitions) for sub in oc_powl.oc_children])

        diverging = [i for i in range(len(oc_powl.oc_children)) if oc_powl.oc_children[i].get_activities() & related_activities
            and all(object_type in oc_powl.get_type_information()[(a,"div")]
                    for a in oc_powl.oc_children[i].get_activities() & related_activities)]
        non_diverging = [i for i in range(len(oc_powl.oc_children)) if oc_powl.oc_children[i].get_activities()
            & related_activities and i not in diverging]

        if isinstance(oc_powl.flat_model, StrictPartialOrder):
            div_activities = set(
                sum([list(oc_powl.oc_children[i].get_activities() & related_activities) for i in diverging], []))
            div_activities = {a for a in div_activities if a != ""}

            if div_activities:
                div_subtree = generate_flower_model(activity_labels=div_activities)
                if len(non_diverging) > 0:
                    mapping = {
                        oc_powl.flat_model.children[i]: (
                            project_oc_powl(oc_powl.oc_children[i], object_type, divergent_partitions)
                            if i in non_diverging
                            else SilentTransition()
                        )
                        for i in range(len(oc_powl.oc_children))
                    }
                    non_div_subtree = oc_powl.flat_model.map_nodes(mapping)
                    return StrictPartialOrder(nodes=[non_div_subtree, div_subtree])
                else:
                    return div_subtree
            else:
                mapping = {oc_powl.flat_model.children[i]: project_oc_powl(oc_powl.oc_children[i], object_type, divergent_partitions) for i in range(len(oc_powl.oc_children))}
                return oc_powl.flat_model.map_nodes(mapping)

        elif isinstance(oc_powl.flat_model, DecisionGraph):

            mapping_with_ids = {}

            for group in divergent_partitions:
                group_children_ids = [i for i in range(len(oc_powl.oc_children)) if i in diverging and len(oc_powl.oc_children[i].get_activities() & group) > 0]
                if len(group_children_ids) == 0:
                    pass
                elif len(group_children_ids) == 1:
                    child_id = group_children_ids[0]
                    projected_child = project_oc_powl(oc_powl.oc_children[child_id], object_type, divergent_partitions)
                    mapping_with_ids[child_id] = OperatorPOWL(operator=Operator.LOOP, children=[SilentTransition(), projected_child])
                else:
                    projected_children = [project_oc_powl(oc_powl.oc_children[child_id], object_type, divergent_partitions) for child_id in group_children_ids]
                    flower = OperatorPOWL(operator=Operator.LOOP,
                                        children=[SilentTransition(),
                                                  OperatorPOWL(operator=Operator.XOR, children=projected_children)])
                    for child_id in group_children_ids:
                        mapping_with_ids[child_id] = flower

            mapping = {}

            for i in range(len(oc_powl.oc_children)):
                if i in mapping_with_ids:
                    value = mapping_with_ids[i]
                else:
                    value = project_oc_powl(oc_powl.oc_children[i], object_type, divergent_partitions)
                mapping[oc_powl.flat_model.children[i]] = value

            return oc_powl.flat_model.map_nodes(mapping)
        else:
            raise NotImplementedError

def handle_deficiency(oc_powl: ObjectCentricPOWL):

    if isinstance(oc_powl, LeafNode):
        if oc_powl.activity == "":
            return oc_powl,[]
        else:
            from itertools import combinations, chain
            stable_types = oc_powl.related - oc_powl.deficient
            variable_types = oc_powl.related & oc_powl.deficient
            if variable_types:
                ot_sets =  [stable_types | {c for c in comb} for comb in chain.from_iterable(combinations(variable_types,n)
                                        for n in range(len(variable_types)+1))]

                mapping = {}
                for ots in ot_sets:
                    transition = Transition(oc_powl.activity + "<|>" + str(sorted(list(ots))))
                    mapping[transition] = LeafNode(transition=transition, related=ots, convergent=oc_powl.convergent & ots,
                            deficient= set(), divergent= oc_powl.divergent & ots)
                flat_model = OperatorPOWL(operator=Operator.XOR, children=list(mapping.keys()))
                return ComplexModel(flat_model=flat_model, mapping=mapping), [oc_powl.activity]
            else:
                return oc_powl,[]


    assert isinstance(oc_powl, ComplexModel)
    sub_results = [handle_deficiency(sub) for sub in oc_powl.oc_children]
    flat_children = [child[0].flat_model for child in sub_results]
    flat_to_oc_mapping = {flat_children[i]: sub_results[i][0] for i in range(len(sub_results))}
    old_flat_to_new_flat_mapping = {oc_powl.flat_model.children[i]: flat_children[i] for i in range(len(oc_powl.flat_model.children))}

    flat_model = oc_powl.flat_model

    if isinstance(flat_model, Sequence):
        new_flat_model = Sequence(flat_children)
    elif isinstance(flat_model, StrictPartialOrder) or isinstance(flat_model, DecisionGraph):
        new_flat_model = flat_model.map_nodes(old_flat_to_new_flat_mapping)
    elif isinstance(flat_model, OperatorPOWL):
        new_flat_model = OperatorPOWL(operator=flat_model.operator, children=flat_children)
    else:
        raise NotImplementedError

    return ComplexModel(new_flat_model, flat_to_oc_mapping), sum([sub[1] for sub in sub_results], [])


def convert_ocpowl_to_ocpn(oc_powl: ObjectCentricPOWL, divergent_partitions):

    assert isinstance(oc_powl, ObjectCentricPOWL)
    nets = {}
    nets_duplicates = {}

    convergent_activities = {}
    activities = set()
    oc_powl, special_activities = handle_deficiency(oc_powl)

    for ot in oc_powl.get_object_types():
        powl_model = project_oc_powl(oc_powl,ot,divergent_partitions[ot])
        powl_model = powl_model.reduce_silent_transitions()
        powl_model = powl_model.simplify()
        from powl.conversion.converter import apply as to_pn
        net, im, fm = to_pn(powl_model)
        nets[ot] = net,im,fm
        nets_duplicates[ot] = clone_workflow_net(net, im, fm, label_delimiter="<|>")
        activities.update({a for a in oc_powl.get_activities() if ot in oc_powl.get_type_information()[(a,"rel")]})
        convergent_activities[ot] = {a: ot in oc_powl.get_type_information()[(a,"con")] for a in oc_powl.get_activities()}


    ocpn = {"activities": activities,
            "object_types": nets.keys(),
            "petri_nets": nets,
            "petri_nets_with_duplicates": nets_duplicates,
            "double_arcs_on_activity": convergent_activities,
            "tbr_results" : {}}

    return ocpn

