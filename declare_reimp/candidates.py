from itertools import permutations


class CandidateGenerator:
    def __init__(self, templates):
        unary_templates = {"existence", "absence", "init"}
        binary_templates = {"responded_existence", "coexistence", "exclusive_choice", "response", "precedence",
                            "succession", "alternate_response", "alternate_precedence", "alternate_succession",
                            "chain_response", "chain_precedence", "chain_succession"}

        chosen_unary = set()
        for template in templates:
            if template in unary_templates:
                chosen_unary.add(template)

        self.chosen_unary_templates = sorted(chosen_unary)

        chosen_binary = set()
        for template in templates:
            if template in binary_templates:
                chosen_binary.add(template)

        self.chosen_binary_templates = sorted(chosen_binary)

    def generate_candidates(self, frequent_sets, activities):
        return self.generate_unary_candidates(activities) + self.generate_binary_candidates(frequent_sets)

    def generate_unary_candidates(self, activities):
        candidates = []
        for activity in sorted(activities):
            for template in self.chosen_unary_templates:
                candidates.append({"template": template, "a": activity, "b": None})
        return candidates

    def generate_binary_candidates(self, frequent_sets):
        candidates = []
        for frequent_set in frequent_sets:
            activities = frequent_set["items"]
            for a, b in permutations(activities, 2):
                for template in self.chosen_binary_templates:
                    candidates.append({"template": template, "a": a, "b": b})
        return candidates
