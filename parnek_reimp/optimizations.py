from collections import defaultdict, deque


class TransitiveReduction:
    def transitive_reduce(self, edges):
        adjacency = defaultdict(set)
        for start, end in edges:
            adjacency[start].add(end)

        reduced = set(edges)
        for start, end in list(edges):
            if self._reachable(adjacency, start, end, banned=(start, end)):
                reduced.discard((start, end))
        return reduced

    @staticmethod
    def _reachable(adjacency, source, target, banned):
        queue = deque([source])
        seen = {source}
        while queue:
            start = queue.popleft()
            for end in adjacency[start]:
                if (start, end) == banned:
                    continue
                if end == target:
                    return True
                if end not in seen:
                    seen.add(end)
                    queue.append(end)
        return False


class PredecessorSuccessors:
    def __init__(self, log, activities):
        self.predecessors = {}
        self.successors = {}

        for a in activities:
            self.predecessors[a] = set()
            self.successors[a] = set()

        for trace in log:
            for a in activities:
                if a not in trace:
                    continue

                first = trace.index(a)
                last = len(trace) - 1
                while trace[last] != a:
                    last -= 1

                for activity in trace[:last]:
                    self.predecessors[a].add(activity)
                for activity in trace[first + 1:]:
                    self.successors[a].add(activity)


class PredecessorExclusions:
    def find(self, activities, pred_succ, self_excluding):
        found = set()
        for a in activities:
            for b in pred_succ.predecessors[a]:
                if b in pred_succ.successors[a]:
                    continue
                if b != a and b not in self_excluding:
                    found.add((a, b))
        return found


class MutualExclusions:
    def find(self, activities, pred_succ):
        found = set()
        for a in activities:
            for b in activities:
                if a == b:
                    continue

                if b not in pred_succ.predecessors[a] and b not in pred_succ.successors[a]:
                    found.add((a, b))
                    found.add((b, a))
        return found


class ExclusionOptimization:
    def prune(self, exclusions, pred_succ):
        kept = set(exclusions)
        changed = True
        while changed:
            changed = False

            for a, b in sorted(kept):
                if a == b:
                    continue

                preds = set(pred_succ.predecessors.get(a, set()))
                preds.discard(a)

                # if any predecessor of a already excludes b, then a -> b is redundant
                redundant = False
                for pred in preds:
                    if (pred, b) in kept:
                        redundant = True
                        break

                if redundant:
                    kept.discard((a, b))
                    changed = True
        return kept
