from itertools import combinations


def find_support(activities, traces):
    traces_containing_all = 0

    for trace in traces:
        contains_all = True
        for activity in activities:
            if activity not in trace:
                contains_all = False
                break
        if contains_all:
            traces_containing_all += 1

    return traces_containing_all / len(traces)


class FrequentSetMiner:
    def __init__(self, minimum_support):
        self.minimum_support = minimum_support

    def generate_sets(self, raw_traces):
        traces = []
        for trace in raw_traces:
            traces.append(set(trace))

        frequent_activities = self.find_frequent_activities(traces)
        frequent_pairs = self.find_frequent_pairs(frequent_activities, traces)

        return frequent_activities + frequent_pairs

    def find_frequent_activities(self, traces):
        all_activities = set()
        for trace in traces:
            for activity in trace:
                all_activities.add(activity)
        all_activities = sorted(all_activities)

        frequent = []
        for activity in all_activities:
            support = find_support({activity}, traces)
            if support >= self.minimum_support:
                frequent.append({"items": [activity], "support": round(support, 3)})
        return frequent

    def find_frequent_pairs(self, frequent_activities, traces):
        frequent_single_activities = []
        for frequent_set in frequent_activities:
            frequent_single_activities.append(frequent_set["items"][0])

        frequent = []
        for first, second in combinations(frequent_single_activities, 2):
            support = find_support({first, second}, traces)
            if support >= self.minimum_support:
                pair = sorted([first, second])
                frequent.append({"items": pair, "support": round(support, 3)})
        return frequent
