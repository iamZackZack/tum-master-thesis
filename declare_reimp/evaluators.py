from templates import TEMPLATES, UNARY_TEMPLATES


def traces_with_activity(traces, activity):
    num_of_traces_with_act = 0
    for trace in traces:
        if activity in trace:
            num_of_traces_with_act += 1
    return num_of_traces_with_act / len(traces)


def traces_with_either_activity(traces, a, b):
    num_of_traces_with_act = 0
    for trace in traces:
        if (a in trace) or (b in trace):
            num_of_traces_with_act += 1
    return num_of_traces_with_act / len(traces)


def safe_divide(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


def measure_interest_factor(constraint_support, antecedent_support, consequent_support):
    if antecedent_support is None or consequent_support is None:
        return None
    denominator = antecedent_support * consequent_support
    if denominator == 0:
        return None
    return constraint_support / denominator


def measure_cpir(constraint_support, antecedent_support, consequent_support):
    if antecedent_support is None or consequent_support is None:
        return None
    denominator = antecedent_support * (1.0 - consequent_support)
    if denominator == 0:
        return None
    return (constraint_support - antecedent_support * consequent_support) / denominator


def antecedent_and_consequent_support(traces, template, a, b):
    if template in UNARY_TEMPLATES:
        return traces_with_activity(traces, a), None

    if b is None or template == "exclusive_choice":
        return None, None

    if template == "coexistence":
        both = traces_with_either_activity(traces, a, b)
        return both, both

    precedence_like = {"precedence", "chain_precedence", "alternate_precedence"}
    if template in precedence_like:
        return traces_with_activity(traces, b), traces_with_activity(traces, a)

    return traces_with_activity(traces, a), traces_with_activity(traces, b)


class ConstraintEvaluator:
    def __init__(self, traces):
        self.traces = traces
        self.total_traces = len(traces)

    def evaluate_candidates(self, candidates):
        results = []
        for candidate in candidates:
            result = self.evaluate_one(candidate)
            results.append(result)
        return results

    def evaluate_one(self, candidate):
        template = candidate["template"]
        a = candidate["a"]
        b = candidate["b"]
        counts = self.count_over_traces(template, a, b)
        return self.build_result(template, a, b, counts)

    def count_over_traces(self, template, a, b):
        check_trace = TEMPLATES[template]
        is_unary = template in UNARY_TEMPLATES

        activated_traces = 0
        satisfied_traces = 0
        violated_traces = 0
        non_vacuous_satisfied_traces = 0
        vacuous_satisfied_traces = 0
        activations = 0
        fulfillments = 0
        violations = 0

        for trace in self.traces:
            outcome = check_trace(trace, a) if is_unary else check_trace(trace, a, b)

            if outcome.activated:
                activated_traces += 1
            if outcome.satisfied:
                satisfied_traces += 1
            if outcome.activated and not outcome.satisfied:
                violated_traces += 1
            if outcome.non_vacuous:
                non_vacuous_satisfied_traces += 1
            if outcome.satisfied and not outcome.non_vacuous:
                vacuous_satisfied_traces += 1

            activations += outcome.activations
            fulfillments += outcome.fulfillments
            violations += outcome.violations

        return {
            "activated_traces": activated_traces,
            "satisfied_traces": satisfied_traces,
            "violated_traces": violated_traces,
            "non_vacuous_satisfied_traces": non_vacuous_satisfied_traces,
            "vacuous_satisfied_traces": vacuous_satisfied_traces,
            "activations": activations,
            "fulfillments": fulfillments,
            "violations": violations,
        }

    def build_result(self, template, a, b, counts):
        total = self.total_traces

        satisfied_traces = counts["satisfied_traces"]
        non_vacuous_satisfied_traces = counts["non_vacuous_satisfied_traces"]
        activated_traces = counts["activated_traces"]
        vacuous_satisfied_traces = counts["vacuous_satisfied_traces"]
        violated_traces = counts["violated_traces"]

        if total:
            support = satisfied_traces / total
            non_vacuous_support = non_vacuous_satisfied_traces / total
            non_activation_rate = (total - activated_traces) / total
            violation_rate = violated_traces / total
        else:
            support = 0
            non_vacuous_support = 0
            non_activation_rate = 0
            violation_rate = 0

        support_antecedent, support_consequent = antecedent_and_consequent_support(self.traces, template, a, b)

        if support_antecedent is not None:
            confidence = safe_divide(non_vacuous_support, support_antecedent)
        else:
            confidence = safe_divide(non_vacuous_support, 0)

        interest = measure_interest_factor(non_vacuous_support, support_antecedent, support_consequent)
        cpir_value = measure_cpir(non_vacuous_support, support_antecedent, support_consequent)
        vacuity_rate = safe_divide(vacuous_satisfied_traces, satisfied_traces)

        return {
            "template": template,
            "a": a,
            "b": b,
            "support": round(support, 6),
            "non_vacuous_support": round(non_vacuous_support, 6),
            "non_activation_rate": round(non_activation_rate, 6),
            "confidence": round(confidence, 6) if confidence is not None else None,
            "interest_factor": round(interest, 6) if interest is not None else None,
            "cpir": round(cpir_value, 6) if cpir_value is not None else None,
            "vacuity_rate": round(vacuity_rate, 6) if vacuity_rate is not None else None,
            "violation_rate": round(violation_rate, 6),
            "support_antecedent": round(support_antecedent, 6) if support_antecedent is not None else None,
            "support_consequent": round(support_consequent, 6) if support_consequent is not None else None,
            "activations": counts["activations"],
            "fulfillments": counts["fulfillments"],
            "violations": counts["violations"],
            "activated_traces": activated_traces,
            "satisfied_traces": satisfied_traces,
            "violated_traces": violated_traces,
            "non_vacuous_satisfied_traces": non_vacuous_satisfied_traces,
            "vacuous_satisfied_traces": vacuous_satisfied_traces,
            "total_traces": total,
        }
