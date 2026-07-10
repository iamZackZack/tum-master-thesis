from collections import defaultdict

STRONG_WEAK_CONSTRAINTS = {
    "succession": ["response", "precedence"],
    "alternate_response": ["response"],
    "alternate_precedence": ["precedence"],
    "alternate_succession": ["alternate_response", "alternate_precedence", "succession", "response", "precedence"],
    "chain_response": ["response", "alternate_response"],
    "chain_precedence": ["precedence", "alternate_precedence"],
    "chain_succession": ["chain_response", "chain_precedence", "alternate_succession", "succession",
                         "alternate_response", "alternate_precedence", "response", "precedence"]
}

TRANSITIVE_EDGE_OF = {
    "response":   {"response", "alternate_response", "chain_response", "succession", "alternate_succession", "chain_succession"},
    "precedence": {"precedence", "alternate_precedence", "chain_precedence", "succession", "alternate_succession", "chain_succession"},
    "succession": {"succession", "alternate_succession", "chain_succession"}
}

TRANSITIVE_RELATIONS = {"response", "precedence", "succession"}
SYMMETRIC_TEMPLATES = {"coexistence", "exclusive_choice"}


def sort_constraint(constraint):
    return constraint["template"], constraint["a"], constraint["b"]


def reachable(edges, source, target):
    stack = list(edges.get(source, set()))
    seen = set()
    while stack:
        node = stack.pop()
        if node == target:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, set()))
    return False


def remove_constraints_by_hierarchy(constraints):
    current_constraints = set()
    removed = set()

    for constraint in constraints:
        current_constraints.add(sort_constraint(constraint))

    for constraint in constraints:
        template = constraint["template"]
        event_a = constraint["a"]
        event_b = constraint["b"]
        for stronger_template, weaker_templates in STRONG_WEAK_CONSTRAINTS.items():
            if template in weaker_templates and (stronger_template, event_a, event_b) in current_constraints:
                removed.add(sort_constraint(constraint))
                break
    return removed


def remove_constraints_by_transitivity(constraints, relation):
    edges = defaultdict(set)
    for constraint in constraints:
        if constraint["template"] in TRANSITIVE_EDGE_OF[relation]:
            edges[constraint["a"]].add(constraint["b"])

    removed = set()
    rows = []
    for constraint in constraints:
        if constraint["template"] == relation:
            rows.append(constraint)

    for constraint in sorted(rows, key=lambda c: (c["a"], c["b"])):
        a = constraint["a"]
        b = constraint["b"]
        edges[a].discard(b)
        if reachable(edges, a, b):
            removed.add(sort_constraint(constraint))
        else:
            edges[a].add(b)
    return removed


def remove_constraints_by_symmetry(constraints, template):
    removed = set()
    kept_constraints = set()
    for constraint in constraints:
        if constraint["template"] != template:
            continue
        a = constraint["a"]
        b = constraint["b"]
        canonical = tuple(sorted([a, b]))
        if canonical in kept_constraints or (a, b) != canonical:
            removed.add(sort_constraint(constraint))
        else:
            kept_constraints.add(canonical)
    return removed


class ConstraintReducer:
    def __init__(self, templates):
        self.templates = set(templates)

    def reduce(self, constraints):
        kept_constraints = []
        removed_constraints = remove_constraints_by_hierarchy(constraints)
        for constraint in constraints:
            if sort_constraint(constraint) not in removed_constraints:
                kept_constraints.append(constraint)

        for template in sorted(self.templates):
            if template in TRANSITIVE_RELATIONS:
                removed_constraints = removed_constraints.union(remove_constraints_by_transitivity(kept_constraints, template))
            elif template in SYMMETRIC_TEMPLATES:
                removed_constraints = removed_constraints.union(remove_constraints_by_symmetry(kept_constraints, template))

        final_constraints = []
        for constraint in constraints:
            if sort_constraint(constraint) not in removed_constraints:
                final_constraints.append(constraint)

        return final_constraints
