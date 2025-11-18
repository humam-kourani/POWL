from powl.objects.obj import POWL, SilentTransition, Transition


class ObjectCentricPOWL:
    def __init__(self) -> None:
        self.flat_model: POWL | Transition | None = None


class LeafNode(ObjectCentricPOWL):
    def __init__(
        self, transition: Transition, related, divergent, convergent, deficient
    ):
        super().__init__()
        if isinstance(transition, SilentTransition):
            self.activity = ""
        else:
            self.activity = transition.label
        self.flat_model = transition
        self.related = related
        self.divergent = divergent
        self.convergent = convergent
        self.deficient = deficient

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


class ComplexModel(ObjectCentricPOWL):
    def __init__(self, flat_model: POWL, mapping):
        super().__init__()
        self.flat_model = flat_model
        self.mapping = mapping
        self.oc_children = [mapping[child] for child in flat_model.children]

    def get_type_information(self):
        return {
            key: value
            for oc_child in self.oc_children
            for key, value in oc_child.get_type_information().items()
        }

    def get_object_types(self):
        return set(
            sum([list(value) for value in self.get_type_information().values()], [])
        )

    def get_activities(self):
        return set(sum([[key[0]] for key in self.get_type_information().keys()], []))


def load_oc_powl(
    flat_model: POWL, related, divergence, convergence, deficiency
) -> ObjectCentricPOWL:
    if isinstance(flat_model, Transition):
        if isinstance(flat_model, SilentTransition):
            all_types = set(sum([list(v) for v in related.values()], []))
            return LeafNode(
                SilentTransition(), all_types, all_types, all_types, all_types
            )
        else:
            activity = flat_model.label
            return LeafNode(
                flat_model,
                related[activity],
                divergence[activity],
                convergence[activity],
                deficiency[activity],
            )
    else:
        oc_children = [
            load_oc_powl(sub, related, divergence, convergence, deficiency)
            for sub in flat_model.children
        ]
        mapping = {
            flat_model.children[i]: oc_children[i]
            for i in range(len(flat_model.children))
        }
        return ComplexModel(flat_model, mapping)
