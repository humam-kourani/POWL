from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List as TList, Optional, Union

from pm4py.objects.process_tree.obj import Operator, ProcessTree

from powl.objects.BinaryRelation import BinaryRelation


class POWL(ProcessTree, ABC):
    @abstractmethod
    def simplify_using_frequent_transitions(self) -> "POWL":
        return self

    @abstractmethod
    def simplify(self) -> "POWL":
        return self

    def __str__(self):
        return self.__repr__()

    @abstractmethod
    def reduce_silent_transitions(self, add_empty_paths=True) -> "POWL":
        return self


class Transition(POWL):
    transition_id: int = 0

    def __init__(
        self, label: Optional[str] = None, organization=None, role=None
    ) -> None:
        super().__init__()
        self._label = label
        self._organization = organization
        self._role = role
        self._identifier = Transition.transition_id
        Transition.transition_id = Transition.transition_id + 1

    def __repr__(self) -> str:
        return f"Transition(label={self._label}, id={self._identifier})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Transition):
            return self._label == other._label and self._identifier == other._identifier
        return False

    def __copy__(self):
        return Transition(self._label)

    def __deepcopy__(self, memo):
        return Transition(self._label)

    def equal_content(self, other: object) -> bool:
        if isinstance(other, Transition):
            return self._label == other._label
        return False

    def set_organization(self, organization):
        self._organization = organization

    def set_role(self, role):
        self._role = role

    def __hash__(self) -> int:
        return self._identifier

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Transition):
            if self.label and other.label and self.label < other.label:
                return self.label < other.label
            return self._identifier < other._identifier
        elif isinstance(other, OperatorPOWL):
            return True
        elif isinstance(other, StrictPartialOrder):
            return True
        return NotImplemented

    def simplify_using_frequent_transitions(self) -> "Transition":
        return self

    def simplify(self) -> "Transition":
        return self

    def reduce_silent_transitions(self, add_empty_paths=True) -> "Transition":
        return self


class SilentTransition(Transition):
    def __init__(self) -> None:
        super().__init__(label=None)

    def __copy__(self):
        return SilentTransition()

    def __deepcopy__(self, memo):
        return SilentTransition()


class FrequentTransition(Transition):
    def __init__(
        self, label, min_freq: Union[str, int], max_freq: Union[str, int]
    ) -> None:
        self.skippable = False
        self.selfloop = False
        if min_freq == 0:
            self.skippable = True
        if max_freq == "-":
            self.selfloop = True
        self.activity = label
        if self.skippable or self.selfloop:
            label = str(label) + "\n" + "[" + str(min_freq) + "," + str(max_freq) + "]"

        super().__init__(label=label)

    def simplify(self):
        raise Exception(
            "Not allowed! You cannot call the simplify function on powl models annotated with frequency tags."
        )

    def __repr__(self):
        return f"FrequentTransition(activity={self.activity}, skippable={self.skippable}, selfloop={self.selfloop})"

    def set_skippable(self, skip):
        self.skippable = skip
        self.__update_label()

    def set_selfloop(self, loop):
        self.selfloop = loop
        self.__update_label()

    def __update_label(self):
        if self.skippable:
            min_freq = 0
        else:
            min_freq = 1
        if self.selfloop:
            max_freq = "-"
        else:
            max_freq = 1
        self.label = (
            str(self.activity) + "\n" + "[" + str(min_freq) + "," + str(max_freq) + "]"
        )

    def __copy__(self):
        if self.skippable:
            min_freq = 0
        else:
            min_freq = 1
        if self.selfloop:
            max_freq = "-"
        else:
            max_freq = 1
        ft = FrequentTransition(self.activity, min_freq, max_freq)
        ft._organization = self._organization
        ft._role = self._role
        return ft

    def __deepcopy__(self, memo):
        if self.skippable:
            min_freq = 0
        else:
            min_freq = 1
        if self.selfloop:
            max_freq = "-"
        else:
            max_freq = 1
        ft = FrequentTransition(self.activity, min_freq, max_freq)
        ft._organization = self._organization
        ft._role = self._role
        return ft


class StrictPartialOrder(POWL):
    def __init__(self, nodes: TList[POWL]) -> None:
        super().__init__()
        self.operator = None
        self._set_order(nodes)
        self.additional_information = None

    def __repr__(self):
        return f"StrictPartialOrder({self.order.nodes})"

    def _set_order(self, nodes: TList[POWL]) -> None:
        self.order = BinaryRelation(nodes)

    def get_order(self) -> BinaryRelation:
        return self.order

    def _set_children(self, children: TList[POWL]) -> None:
        self.order.nodes = children

    def get_children(self) -> TList[POWL]:
        return self.order.nodes

    def __lt__(self, other: object) -> bool:
        if isinstance(other, StrictPartialOrder):
            return self.__repr__() < other.__repr__()
        elif isinstance(other, OperatorPOWL):
            return False
        elif isinstance(other, Transition):
            return False
        return NotImplemented

    partial_order = property(get_order, _set_order)
    children = property(get_children, _set_children)

    def equal_content(self, other: object) -> bool:
        if not isinstance(other, StrictPartialOrder):
            return False

        ordered_nodes_1 = sorted(list(self.order.nodes))
        ordered_nodes_2 = sorted(list(other.order.nodes))
        if len(ordered_nodes_1) != len(ordered_nodes_2):
            return False
        for i in range(len(ordered_nodes_1)):
            source_1 = ordered_nodes_1[i]
            source_2 = ordered_nodes_2[i]
            if not source_1.equal_content(source_2):
                return False
            for j in range(len(ordered_nodes_1)):
                target_1 = ordered_nodes_1[j]
                target_2 = ordered_nodes_2[j]
                if self.order.is_edge(source_1, target_1) and not other.order.is_edge(
                    source_2, target_2
                ):
                    return False
                if not self.order.is_edge(source_1, target_1) and other.order.is_edge(
                    source_2, target_2
                ):
                    return False
        return True

    def simplify_using_frequent_transitions(self) -> "StrictPartialOrder":
        new_nodes = {
            node: node.simplify_using_frequent_transitions() for node in self.children
        }
        res = StrictPartialOrder(list(new_nodes.values()))
        for node_1 in self.children:
            for node_2 in self.children:
                if self.partial_order.is_edge(node_1, node_2):
                    res.partial_order.add_edge(new_nodes[node_1], new_nodes[node_2])

        return res

    def reduce_silent_transitions(self, add_empty_paths=True) -> "StrictPartialOrder":
        new_nodes_map = {
            node: node.reduce_silent_transitions(add_empty_paths)
            for node in self.children
            if not isinstance(node, SilentTransition)
        }
        return self.map_nodes(new_nodes_map)

    def simplify(self) -> "StrictPartialOrder":
        simplified_nodes = {}
        sub_nodes = {}
        start_nodes = {}
        end_nodes = {}

        def connected(node):
            for node2 in self.children:
                if self.partial_order.is_edge(
                    node, node2
                ) or self.partial_order.is_edge(node2, node):
                    return True
            return False

        for node_1 in self.children:
            simplified_node = node_1.simplify()
            if isinstance(simplified_node, StrictPartialOrder):

                if not connected(node_1):
                    sub_nodes[node_1] = simplified_node
                else:
                    s_nodes = simplified_node.order.get_start_nodes()
                    e_nodes = simplified_node.order.get_end_nodes()
                    if len(s_nodes) == 1 and len(e_nodes) == 1:
                        sub_nodes[node_1] = simplified_node
                        start_nodes[node_1] = list(s_nodes)[0]
                        end_nodes[node_1] = list(e_nodes)[0]
                    else:
                        simplified_nodes[node_1] = simplified_node
            else:
                simplified_nodes[node_1] = simplified_node

        new_nodes = list(simplified_nodes.values())
        for po, simplified_po in sub_nodes.items():
            new_nodes = new_nodes + list(simplified_po.children)
        res = StrictPartialOrder(new_nodes)
        for node_1 in self.children:
            for node_2 in self.children:
                if self.partial_order.is_edge(node_1, node_2):
                    if (
                        node_1 in simplified_nodes.keys()
                        and node_2 in simplified_nodes.keys()
                    ):
                        res.partial_order.add_edge(
                            simplified_nodes[node_1], simplified_nodes[node_2]
                        )
                    elif node_1 in simplified_nodes.keys():
                        res.partial_order.add_edge(
                            simplified_nodes[node_1], start_nodes[node_2]
                        )
                    elif node_2 in simplified_nodes.keys():
                        res.partial_order.add_edge(
                            end_nodes[node_1], simplified_nodes[node_2]
                        )
                    else:
                        res.partial_order.add_edge(
                            end_nodes[node_1], start_nodes[node_2]
                        )
        for po, simplified_po in sub_nodes.items():
            for node_1 in simplified_po.children:
                for node_2 in simplified_po.children:
                    if simplified_po.partial_order.is_edge(node_1, node_2):
                        res.partial_order.add_edge(node_1, node_2)
        return res

    def add_edge(self, source, target):
        return self.order.add_edge(source, target)

    def map_nodes(self, mapping):
        res = StrictPartialOrder(list(mapping.values()))
        for node_1, new_node_1 in mapping.items():
            for node_2, new_node_2 in mapping.items():
                if self.partial_order.is_edge(node_1, node_2):
                    res.partial_order.add_edge(new_node_1, new_node_2)
        return res


class Sequence(StrictPartialOrder):
    def __init__(self, nodes: TList[POWL]) -> None:
        super().__init__(nodes)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                self.partial_order.add_edge(nodes[i], nodes[j])

    def simplify_using_frequent_transitions(self) -> "StrictPartialOrder":
        new_children = []
        for node in self.children:
            s_node = node.simplify_using_frequent_transitions()
            if isinstance(s_node, Sequence):
                new_children = new_children + s_node.children
            else:
                new_children = new_children + [s_node]
        res = Sequence(new_children)
        return res

    def reduce_silent_transitions(self, add_empty_paths=True) -> "Sequence":
        new_nodes = [
            node.reduce_silent_transitions(add_empty_paths)
            for node in self.children
            if not isinstance(node, SilentTransition)
        ]
        return Sequence(new_nodes)


class OperatorPOWL(POWL):
    operator_id: int = 0
    def __init__(self, operator: Operator, children: TList[POWL]) -> None:
        super().__init__()
        self.operator = operator
        self.children = children
        self._identifier = OperatorPOWL.operator_id
        OperatorPOWL.operator_id = OperatorPOWL.operator_id + 1

    def __repr__(self):
        return f"{self.operator}({self.children})"

    def __lt__(self, other: object) -> bool:
        if isinstance(other, OperatorPOWL):
            return self.__repr__() < other.__repr__()
        elif isinstance(other, Transition):
            return False
        elif isinstance(other, StrictPartialOrder):
            return True
        return NotImplemented

    def equal_content(self, other: object) -> bool:
        if not isinstance(other, OperatorPOWL):
            return False

        if self.operator != other.operator:
            return False

        ordered_nodes_1 = sorted(list(self.children))
        ordered_nodes_2 = sorted(list(other.children))
        if len(ordered_nodes_1) != len(ordered_nodes_2):
            return False
        for i in range(len(ordered_nodes_1)):
            node_1 = ordered_nodes_1[i]
            node_2 = ordered_nodes_2[i]
            if not node_1.equal_content(node_2):
                return False
        return True

    def reduce_silent_transitions(self, add_empty_paths=True) -> POWL:

        new_children = [
            node.reduce_silent_transitions(add_empty_paths) for node in self.children
        ]

        if self.operator == Operator.XOR:
            new_children_no_silent = [
                c for c in new_children if not isinstance(c, SilentTransition)
            ]
            if len(new_children_no_silent) < len(new_children) - 1:
                new_children = new_children_no_silent + [SilentTransition()]
                if len(new_children) == 1:
                    return new_children[0]

        return OperatorPOWL(operator=self.operator, children=new_children)

    def simplify_using_frequent_transitions(self) -> POWL:
        if self.operator is Operator.XOR and len(self.children) == 2:
            child_0 = self.children[0].simplify_using_frequent_transitions()
            child_1 = self.children[1].simplify_using_frequent_transitions()

            if isinstance(child_0, SilentTransition) and isinstance(
                child_1, SilentTransition
            ):
                return child_0

            if isinstance(child_0, SilentTransition):
                if isinstance(child_1, FrequentTransition):
                    child_1.set_skippable(True)
                    return child_1
                elif isinstance(child_1, Transition):
                    return FrequentTransition(
                        label=child_1.label, min_freq=0, max_freq=1
                    )
            if isinstance(child_1, SilentTransition):
                if isinstance(child_0, FrequentTransition):
                    child_0.set_skippable(True)
                    return child_0
                elif isinstance(child_0, Transition):
                    return FrequentTransition(
                        label=child_0.label, min_freq=0, max_freq=1
                    )

        if self.operator is Operator.LOOP and len(self.children) == 2:
            child_0 = self.children[0]
            child_1 = self.children[1]
            if isinstance(child_0, Transition) and isinstance(
                child_1, SilentTransition
            ):
                return FrequentTransition(label=child_0.label, min_freq=1, max_freq="-")
            elif isinstance(child_1, Transition) and isinstance(
                child_0, SilentTransition
            ):
                return FrequentTransition(label=child_1.label, min_freq=0, max_freq="-")

        return OperatorPOWL(
            self.operator,
            [child.simplify_using_frequent_transitions() for child in self.children],
        )

    def simplify(self) -> "OperatorPOWL":
        if self.operator is Operator.XOR and len(self.children) == 2:
            child_0 = self.children[0]
            child_1 = self.children[1]

            def merge_with_children(child0, child1):
                if (
                    isinstance(child0, SilentTransition)
                    and isinstance(child1, OperatorPOWL)
                    and child1.operator is Operator.LOOP
                ):
                    if isinstance(child1.children[0], SilentTransition):
                        return OperatorPOWL(
                            Operator.LOOP, [n.simplify() for n in child1.children]
                        )
                    elif isinstance(child1.children[1], SilentTransition):
                        return OperatorPOWL(
                            Operator.LOOP,
                            list(reversed([n.simplify() for n in child1.children])),
                        )

                return None

            res = merge_with_children(child_0, child_1)
            if res is not None:
                return res

            res = merge_with_children(child_1, child_0)
            if res is not None:
                return res

        return OperatorPOWL(
            self.operator, [child.simplify() for child in self.children]
        )


class DecisionGraph(POWL):
    """
    A DecisionGraph is a POWL model defined over a set of nodes (each node is a POWL model)
    together with a binary relation (order) over these nodes, augmented with two artificial
    nodes: a start node and an end node.

    In the decision graph, each node represents a group (or branch) of activities (or submodels)
    and the binary relation encodes the allowed ordering between these nodes.
    """

    def __init__(
        self, order: BinaryRelation, start_nodes, end_nodes, empty_path=False
    ) -> None:
        super().__init__()
        self.operator = None
        self.children = [n for n in order.nodes]
        self.start_nodes = start_nodes
        self.end_nodes = end_nodes
        # if not all(isinstance(node, POWL) for node in nodes):
        #     raise Exception("The nodes of the decision graph must be POWL models!")
        if not start_nodes or not set(start_nodes).issubset(order.nodes):
            raise Exception(
                "Start nodes must be a non-empty subset of the nodes of the relation!"
            )
        if not end_nodes or not set(end_nodes).issubset(order.nodes):
            raise Exception(
                "End nodes must be a non-empty subset of the nodes of the relation!"
            )
        self.start = StartNode()
        self.end = EndNode()
        order.add_node(self.start)
        order.add_node(self.end)
        for node in start_nodes:
            order.add_edge(self.start, node)
        for node in end_nodes:
            order.add_edge(node, self.end)
        if empty_path:
            order.add_edge(self.start, self.end)

        self.order = order

    def __repr__(self):
        return f"DecisionGraph({self.children})"

    def simplify(self) -> POWL:
        if len(self.children) == 1:
            child_0 = self.children[0]
            skippable = self.order.is_edge(self.start, self.end)
            repeatable = self.order.is_edge(child_0, child_0)

            if skippable:
                if repeatable:
                    return OperatorPOWL(
                        Operator.LOOP, [SilentTransition(), child_0]
                    ).simplify()
                else:
                    if isinstance(child_0, DecisionGraph):
                        child_0.empty_path = True
                        child_0.order.add_edge(child_0.start, child_0.end)
                        return child_0.simplify()
                    else:
                        return OperatorPOWL(
                            Operator.XOR, [SilentTransition(), child_0]
                        ).simplify()

            elif repeatable:
                return OperatorPOWL(
                    Operator.LOOP, [child_0, SilentTransition()]
                ).simplify()

            else:
                return child_0.simplify()

        else:
            new_dg = self

            seq = new_dg.__group_start_seq()
            if seq:
                return seq.simplify()

            seq = new_dg.__group_end_seq()
            if seq:
                return seq.simplify()

            res = new_dg.__group_pure_seq()
            if len(res.children) < len(new_dg.children):
                return res.simplify()

            new_children_map = {}
            for child in new_dg.children:
                s_child = child.simplify()
                new_children_map[child] = s_child
            return new_dg.__apply_mapping(new_children_map)

    def simplify_using_frequent_transitions(self) -> POWL:
        if len(self.children) == 1:
            child_0 = self.children[0]

            if isinstance(child_0, Transition):
                skippable = self.order.is_edge(self.start, self.end)
                repeatable = self.order.is_edge(child_0, child_0)

                min_freq = 0 if skippable else 1
                max_freq = "-" if repeatable else 1

                if skippable or repeatable:
                    return FrequentTransition(
                        label=child_0.label, min_freq=min_freq, max_freq=max_freq
                    )
                else:
                    return child_0

        new_children_map = {}
        edges_to_remove = set()
        for child in self.children:
            s_child = child.simplify_using_frequent_transitions()
            if isinstance(s_child, Transition):
                preset = self.order.get_preset(child)
                postset = self.order.get_postset(child)
                if all(
                    self.order.is_edge(pre, post) for pre in preset for post in postset
                ):
                    for pre in preset:
                        for post in postset:
                            edges_to_remove.add((pre, post))
                    if child in self.start_nodes:
                        self.start_nodes = [
                            x for x in self.start_nodes if x not in postset
                        ]
                    if child in self.end_nodes:
                        self.end_nodes = [x for x in self.end_nodes if x not in preset]
                    if isinstance(s_child, FrequentTransition):
                        s_child.set_skippable(True)
                    else:
                        s_child = FrequentTransition(
                            label=child.label, min_freq=0, max_freq=1
                        )
            new_children_map[child] = s_child
        new_dg = self.__apply_mapping(new_children_map, edges_to_remove)

        old_size = len(new_dg.children) + 1
        while len(new_dg.children) < old_size:
            old_size = len(new_dg.children)
            new_dg = new_dg.__group_pure_seq()

        seq1 = new_dg.__group_start_seq()
        start_nodes = []
        if seq1:
            start_nodes = seq1.children[:-1]
            new_dg = seq1.children[-1]

        seq2 = new_dg.__group_end_seq()
        end_nodes = []
        if seq2:
            end_nodes = seq2.children[1:]
            new_dg = seq2.children[0]

        new_node = new_dg
        if len(new_dg.children) == 1:
            child_0 = new_dg.children[0]
            if new_dg.order.is_edge(new_dg.start, new_dg.end):
                if (
                    isinstance(child_0, OperatorPOWL)
                    and child_0.operator is Operator.LOOP
                ):
                    if isinstance(child_0.children[0], SilentTransition):
                        new_node = OperatorPOWL(Operator.LOOP, child_0.children)
                    elif isinstance(child_0.children[1], SilentTransition):
                        new_node = OperatorPOWL(
                            Operator.LOOP, list(reversed(child_0.children))
                        )
                elif isinstance(child_0, DecisionGraph):
                    child_0.empty_path = True
                    child_0.order.add_edge(child_0.start, child_0.end)
                    new_node = child_0
            else:
                new_node = child_0

        if len(start_nodes) > 0 or len(end_nodes) > 0:
            if isinstance(new_node, Sequence):
                return Sequence(start_nodes + new_node.children + end_nodes)
            else:
                return Sequence(start_nodes + [new_node] + end_nodes)
        else:
            return new_node

    def __apply_mapping(self, mapping, edges_to_remove=None) -> "DecisionGraph":
        if edges_to_remove is None:
            edges_to_remove = set()
        res = BinaryRelation(list(set(mapping.values())))
        for src in self.children:
            for tgt in self.children:
                if self.order.is_edge(src, tgt) and (src, tgt) not in edges_to_remove:
                    new_src = mapping[src]
                    new_tgt = mapping[tgt]
                    if new_src != new_tgt:
                        res.add_edge(new_src, new_tgt)
        new_start_nodes = list({mapping[child] for child in self.start_nodes})
        new_end_nodes = list({mapping[child] for child in self.end_nodes})
        empty_path = (
            self.order.is_edge(self.start, self.end)
            and not (self.start, self.end) in edges_to_remove
        )
        return DecisionGraph(res, new_start_nodes, new_end_nodes, empty_path)

    def __create_mapping(self, old_children, new_child):
        mapping = {}
        for key in self.children:
            if key in old_children:
                mapping[key] = new_child
            else:
                mapping[key] = key
        return mapping

    # def __group_pure_xor(self):
    #     new_dg = deepcopy(self)
    #     visited = set()
    #     for child in list(self.children):
    #         if child not in visited:
    #             visited.add(child)
    #             post1 = new_dg.order.get_postset(child)
    #             pre1 = new_dg.order.get_preset(child)
    #             if len(pre1) > 1 or len(post1) > 1:
    #                 candidates_for_xor = [child2 for child2 in new_dg.children if
    #                                       pre1 == new_dg.order.get_preset(child2) and post1 == new_dg.order.get_postset(
    #                                           child2)]
    #                 if len(candidates_for_xor) > 1:
    #                     visited.update(candidates_for_xor)
    #
    #                     new_rel = BinaryRelation(candidates_for_xor)
    #                     empty_path = False
    #                     edges_to_remove = None
    #                     if all(new_dg.order.is_edge(pre, post) for pre in pre1 for post in post1):
    #                         empty_path = True
    #                         edges_to_remove = [(pre, post) for pre in pre1 for post in post1]
    #                     dg_child = DecisionGraph(new_rel, candidates_for_xor, candidates_for_xor, empty_path)
    #                     mapping = new_dg.__create_mapping(candidates_for_xor, dg_child)
    #                     new_dg = new_dg.__apply_mapping(mapping, edges_to_remove)
    #     return new_dg

    def __group_pure_seq(self):
        for child in list(self.children):
            for child2 in self.children:
                post1 = self.order.get_postset(child)
                pre2 = self.order.get_preset(child2)
                if pre2 == {child} and post1 == {child2}:
                    seq = Sequence([child, child2])
                    mapping = self.__create_mapping({child, child2}, seq)
                    new_dg = self.__apply_mapping(mapping)
                    return new_dg.__group_pure_seq()
        return self

    def __group_start_seq(self):
        start_list = []
        current_dg = self
        while (
            len(current_dg.children) > 1
            and len(current_dg.start_nodes) == 1
            and not current_dg.order.is_edge(current_dg.start, current_dg.end)
            and current_dg.order.get_preset(current_dg.start_nodes[0])
            == {current_dg.start}
        ):
            start = current_dg.start_nodes[0]
            start_list.append(start)
            postset = current_dg.order.get_postset(start)
            new_start_nodes = list(postset - {current_dg.end})
            new_children = [n for n in current_dg.children if n != start]
            new_end_nodes = [n for n in current_dg.end_nodes if n != start]
            new_order = BinaryRelation(new_children)
            for c1 in new_children:
                for c2 in new_children:
                    if current_dg.order.is_edge(c1, c2):
                        new_order.add_edge(c1, c2)
            empty_path = current_dg.end in postset
            current_dg = DecisionGraph(
                new_order, new_start_nodes, new_end_nodes, empty_path
            )
        if len(start_list) > 0:
            seq = Sequence(start_list + [current_dg])
            return seq
        return None

    def __group_end_seq(self):
        end_list = []
        current_dg = self
        while (
            len(current_dg.children) > 1
            and len(current_dg.end_nodes) == 1
            and not current_dg.order.is_edge(current_dg.start, current_dg.end)
            and current_dg.order.get_postset(current_dg.end_nodes[0])
            == {current_dg.end}
        ):
            end = current_dg.end_nodes[0]
            end_list = [end] + end_list
            pretset = current_dg.order.get_preset(end)
            new_end_nodes = list(pretset - {current_dg.start})
            new_children = [n for n in current_dg.children if n != end]
            new_start_nodes = [n for n in current_dg.start_nodes if n != end]
            new_order = BinaryRelation(new_children)
            for c1 in new_children:
                for c2 in new_children:
                    if current_dg.order.is_edge(c1, c2):
                        new_order.add_edge(c1, c2)
            empty_path = current_dg.start in pretset
            current_dg = DecisionGraph(
                new_order, new_start_nodes, new_end_nodes, empty_path
            )
        if len(end_list) > 0:
            seq = Sequence([current_dg] + end_list)
            return seq
        return None

    def reduce_silent_transitions(self, add_empty_paths=True) -> "POWL":
        graph_copy = deepcopy(self)

        mapping = {
            node: node.reduce_silent_transitions(add_empty_paths)
            for node in graph_copy.children
        }
        order_nodes = [n for n in graph_copy.order.nodes]

        for node, new_node in mapping.items():
            if isinstance(new_node, SilentTransition):
                order_nodes.remove(node)
                for n1 in order_nodes:
                    for n2 in order_nodes:
                        if graph_copy.order.is_edge(
                            n1, node
                        ) and graph_copy.order.is_edge(node, n2):
                            graph_copy.order.add_edge(n1, n2)

        mapping = {key: value for key, value in mapping.items() if key in order_nodes}

        if len(mapping.keys()) == 0:
            return SilentTransition()
        else:
            new_start = [
                value
                for key, value in mapping.items()
                if graph_copy.order.is_edge(graph_copy.start, key)
            ]
            new_end = [
                value
                for key, value in mapping.items()
                if graph_copy.order.is_edge(key, graph_copy.end)
            ]
            skip = graph_copy.order.is_edge(graph_copy.start, graph_copy.end)
            new_order = BinaryRelation(list(mapping.values()))
            for node_1 in mapping.keys():
                for node_2 in mapping.keys():
                    if graph_copy.order.is_edge(node_1, node_2):
                        new_order.add_edge(mapping[node_1], mapping[node_2])
            if skip and not add_empty_paths:
                old_skip = self.order.is_edge(self.start, self.end)
                if not old_skip:
                    graph_copy.order.remove_edge(graph_copy.start, graph_copy.end)
                    skip = False
            return DecisionGraph(new_order, new_start, new_end, skip)

    def map_nodes(self, mapping):
        assert all(child in mapping.keys() for child in self.children)
        new_children = list(mapping.values())
        new_order = BinaryRelation(new_children)
        for node_1, new_node_1 in mapping.items():
            for node_2, new_node_2 in mapping.items():
                if self.order.is_edge(node_1, node_2):
                    new_order.add_edge(new_node_1, new_node_2)
        new_start = [mapping[n] for n in self.start_nodes]
        new_end = [mapping[n] for n in self.end_nodes]
        empty_path = self.order.is_edge(self.start, self.end)
        return DecisionGraph(new_order, new_start, new_end, empty_path)


class StartNode:
    def __init__(self) -> None:
        super().__init__()

    def __repr__(self) -> str:
        return "⊕start"


class EndNode:
    def __init__(self) -> None:
        super().__init__()

    def __repr__(self) -> str:
        return "⊕end"
