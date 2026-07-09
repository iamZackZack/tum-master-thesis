import yaml


class DcrGraph:
    def __init__(self, activities):
        self.activities = set(activities)
        self.conditions = set()
        self.responses = set()
        self.includes = set()
        self.excludes = set()

    def add_condition(self, source, target):
        self.conditions.add((source, target))

    def add_response(self, source, target):
        self.responses.add((source, target))

    def add_include(self, source, target):
        self.includes.add((source, target))

    def add_exclude(self, source, target):
        self.excludes.add((source, target))

    def create_graph(self):
        return {
            "activities": sorted(self.activities),
            "conditions": sorted_pairs(self.conditions),
            "responses": sorted_pairs(self.responses),
            "includes": sorted_pairs(self.includes),
            "excludes": sorted_pairs(self.excludes),
        }

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.create_graph(), f, sort_keys=False, allow_unicode=True)


def sorted_pairs(relation):
    pairs = []
    for pair in relation:
        pairs.append(list(pair))
    return sorted(pairs)
