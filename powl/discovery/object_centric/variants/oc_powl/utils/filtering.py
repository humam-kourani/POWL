# this file was initially copied from https://github.com/Nik314/DF2-Miner


def keep_most_frequent_activities(relations, coverage=1.0):

    if coverage >= 1.0:
        return relations

    counts = (
        relations.groupby("ocel:activity")
        .apply(lambda frame: frame["ocel:eid"].nunique())
        .to_dict()
    )
    shares = {key: value / (sum(counts.values())) for key, value in counts.items()}
    shares_sorted = list(reversed(sorted(shares.items(), key=lambda x: x[1])))
    cut_off = min(
        [
            i
            for i in range(len(shares_sorted))
            if sum([entry[1] for entry in shares_sorted[:i]]) >= coverage
        ]
    )
    activities = [shares_sorted[i][0] for i in range(cut_off)]
    return relations[relations["ocel:activity"].isin(activities)]
