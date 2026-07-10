class ConstraintPruner:
    def __init__(self, minimum_support, alpha):
        self.minimum_support = minimum_support
        self.alpha = alpha

    def prune_constraints(self, constraints):
        valid_constraints = []
        for constraint in constraints:
            if self.constraint_meets_thresholds(constraint):
                valid_constraints.append(constraint)
        return valid_constraints

    def constraint_meets_thresholds(self, constraint):
        support = constraint["support"]
        non_vacuous_support = constraint["non_vacuous_support"]
        if support < self.minimum_support:
            return False
        if non_vacuous_support < self.minimum_support - self.alpha:
            return False
        return True
