# this file was initially copied from https://github.com/Nik314/DF2-Miner


class LeafNode:
    def __init__(self, activity, related, divergent, convergent, deficient):
        self.activity = activity
        self.related = related
        self.divergent = divergent
        self.convergent = convergent
        self.deficient = deficient

    def __str__(self, depth=0):
        indent = ""
        for i in range(0, depth):
            indent += "\t"

        result = indent + self.activity + "\n"
        result += indent + "\t Related Types: " + str(self.related) + "\n"
        result += indent + "\t Divergent Types: " + str(self.divergent) + "\n"
        result += indent + "\t Convergent Types: " + str(self.convergent) + "\n"
        result += indent + "\t Deficient Types: " + str(self.deficient) + "\n"
        return result

    def get_as_dict(self):
        return {
            "activity": self.activity,
            "related": self.related,
            "divergent": self.divergent,
            "convergent": self.convergent,
            "deficient": self.deficient,
        }

    def get_type_information(self):
        return {
            (self.activity, "rel"): self.related,
            (self.activity, "div"): self.divergent,
            (self.activity, "con"): self.convergent,
            (self.activity, "def"): self.deficient,
        }

    def get_object_types(self):
        return set(
            sum([list(value) for value in self.get_type_information().values()], [])
        )

    def get_activities(self):
        return {self.activity}

    def get_unique_relations(self):
        return set()


class OperatorNode:
    def __init__(self, operator, subtrees):
        self.operator = operator
        self.subtrees = subtrees

    def __str__(self, depth=0):
        indent = ""
        for i in range(0, depth):
            indent += "\t"
        result = indent + str(self.operator) + "\n"
        for tree in self.subtrees:
            result += tree.__str__(depth + 1)
        return result

    def get_as_dict(self):
        return {
            "operator": str(self.operator),
            "subtrees": [subtree.get_as_dict() for subtree in self.subtrees],
        }

    def get_type_information(self):
        return {
            key: value
            for subtree in self.subtrees
            for key, value in subtree.get_type_information().items()
        }

    def get_object_types(self):
        return set(
            sum([list(value) for value in self.get_type_information().values()], [])
        )

    def get_activities(self):
        return set(sum([[key[0]] for key in self.get_type_information().keys()], []))

    def get_unique_relations(self):
        if len(self.subtrees) == 1:
            return self.subtrees[0].get_unique_relations() | {self.operator}
        else:
            return set(
                sum([list(sub.get_unique_relations()) for sub in self.subtrees], [])
            )


def load_from_pt(process_tree, related, divergence, convergence, deficiency):

    if process_tree.children:
        return OperatorNode(
            process_tree.operator,
            [
                load_from_pt(sub, related, divergence, convergence, deficiency)
                for sub in process_tree.children
            ],
        )
    elif process_tree.label:
        activity = process_tree.label
        return LeafNode(
            activity,
            related[activity],
            divergence[activity],
            convergence[activity],
            deficiency[activity],
        )
    else:
        all_types = set(sum([list(v) for v in related.values()], []))
        return LeafNode("", all_types, all_types, all_types, all_types)
