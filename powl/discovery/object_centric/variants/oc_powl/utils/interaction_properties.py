# this file was initially copied from https://github.com/Nik314/DF2-Miner


def get_interaction_patterns(relations):

    convergent_object_types = {a: set() for a in relations["ocel:activity"].unique()}
    divergent_object_types = {a: set() for a in relations["ocel:activity"].unique()}
    deficient_object_types = {a: set() for a in relations["ocel:activity"].unique()}
    related_object_types = {
        a: set(relations["ocel:type"].unique())
        for a in relations["ocel:activity"].unique()
    }

    look_up_dict_activities = relations.set_index("ocel:eid").to_dict()["ocel:activity"]
    look_up_dict_objects = relations.set_index("ocel:oid").to_dict()["ocel:type"]

    identifiers = (
        relations.groupby("ocel:eid")
        .apply(
            lambda frame: tuple(sorted(set(frame["ocel:oid"].values))),
            include_groups=False,
        )
        .to_frame(name="all")
    )
    identifiers["activity"] = [
        look_up_dict_activities[event_id] for event_id in identifiers.index
    ]

    for activity in relations["ocel:activity"].unique():
        sub_relations = relations[relations["ocel:activity"] == activity]
        for object_type in relations["ocel:type"].unique():
            sub_sub_relations = sub_relations[sub_relations["ocel:type"] == object_type]
            if (
                sub_sub_relations["ocel:eid"].nunique()
                != sub_relations["ocel:eid"].nunique()
            ):
                if not sub_sub_relations["ocel:eid"].nunique() > 0:
                    related_object_types[activity].remove(object_type)
                else:
                    if (
                        sub_sub_relations["ocel:eid"].nunique()
                        < sub_relations["ocel:eid"].nunique()
                    ):
                        deficient_object_types[activity].add(object_type)

    for object_type in relations["ocel:type"].unique():
        identifiers[object_type] = identifiers["all"].apply(
            lambda object_set: tuple(
                sorted(
                    list(
                        {
                            object_id
                            for object_id in object_set
                            if look_up_dict_objects[object_id] == object_type
                        }
                    )
                )
            )
        )

    for object_type in relations["ocel:type"].unique():
        sub_identifiers = identifiers[identifiers[object_type] != set()]
        for activity in relations["ocel:activity"].unique():
            sub_sub_identifiers = sub_identifiers[
                sub_identifiers["activity"] == activity
            ]

            matches = sub_sub_identifiers.groupby(object_type).apply(
                lambda frame: frame["all"].nunique(), include_groups=False
            )
            matches = matches[[index for index in matches.index if index]]

            if (
                sub_sub_identifiers[object_type]
                .apply(lambda object_set: len(object_set))
                .max()
                > 1
            ):
                convergent_object_types[activity].add(object_type)
            if matches.max() > 1:
                divergent_object_types[activity].add(object_type)

    return (
        divergent_object_types,
        convergent_object_types,
        related_object_types,
        deficient_object_types,
    )
