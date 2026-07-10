from counters import TraceOutcome, find_positions, unary_outcome, relation_outcome, combine_bidirectional

UNARY_TEMPLATES = {"existence", "absence", "init"}


def existence(trace, event_a):
    return unary_outcome(event_a in trace)


def absence(trace, event_a):
    return unary_outcome(event_a not in trace)


def init(trace, event_a):
    return unary_outcome(trace[0] == event_a)


def response(trace, event_a, event_b):
    a_positions = find_positions(trace, event_a)
    b_positions = find_positions(trace, event_b)

    fulfillments = 0
    violations = 0
    for i in a_positions:
        found = False
        for j in b_positions:
            if j > i:
                found = True
                break

        if found:
            fulfillments += 1
        else:
            violations += 1

    return relation_outcome(a_positions, fulfillments, violations)


def precedence(trace, event_a, event_b):
    a_positions = find_positions(trace, event_a)
    b_positions = find_positions(trace, event_b)

    fulfillments = 0
    violations = 0
    for j in b_positions:
        found = False
        for i in a_positions:
            if i < j:
                found = True
                break

        if found:
            fulfillments += 1
        else:
            violations += 1
    return relation_outcome(b_positions, fulfillments, violations)


def succession(trace, event_a, event_b):
    return combine_bidirectional(response(trace, event_a, event_b), precedence(trace, event_a, event_b))


def chain_response(trace, event_a, event_b):
    a_positions = find_positions(trace, event_a)

    fulfillments = 0
    violations = 0
    for i in a_positions:
        if i + 1 < len(trace) and trace[i + 1] == event_b:
            fulfillments += 1
        else:
            violations += 1
    return relation_outcome(a_positions, fulfillments, violations)


def chain_precedence(trace, event_a, event_b):
    b_positions = find_positions(trace, event_b)

    fulfillments = 0
    violations = 0
    for j in b_positions:
        if j > 0 and trace[j - 1] == event_a:
            fulfillments += 1
        else:
            violations += 1
    return relation_outcome(b_positions, fulfillments, violations)


def chain_succession(trace, a, event_b):
    return combine_bidirectional(chain_response(trace, a, event_b), chain_precedence(trace, a, event_b))


def alternate_response(trace, event_a, event_b):
    a_positions = find_positions(trace, event_a)

    fulfillments = 0
    violations = 0
    for i in a_positions:
        found_b = False
        for j in range(i + 1, len(trace)):
            if trace[j] == event_b:
                found_b = True
                break
            if trace[j] == event_a:
                break
        if found_b:
            fulfillments += 1
        else:
            violations += 1
    return relation_outcome(a_positions, fulfillments, violations)


def alternate_precedence(trace, event_a, event_b):
    b_positions = find_positions(trace, event_b)

    fulfillments = 0
    violations = 0
    for i in b_positions:
        found_a = False
        for j in range(i - 1, -1, -1):
            if trace[j] == event_a:
                found_a = True
                break
            if trace[j] == event_b:
                break
        if found_a:
            fulfillments += 1
        else:
            violations += 1
    return relation_outcome(b_positions, fulfillments, violations)


def alternate_succession(trace, event_a, event_b):
    return combine_bidirectional(alternate_response(trace, event_a, event_b), alternate_precedence(trace, event_a, event_b))


def responded_existence(trace, event_a, event_b):
    a_positions = find_positions(trace, event_a)

    if len(a_positions) == 0:
        return TraceOutcome(False, True, False, 0, 0, 0)

    satisfaction_condition = (event_b in trace)
    activations = len(a_positions)
    return TraceOutcome(
        activated=True,
        satisfied=satisfaction_condition,
        non_vacuous=satisfaction_condition,
        activations=activations,
        fulfillments=activations if satisfaction_condition else 0,
        violations=0 if satisfaction_condition else activations,
    )


def coexistence(trace, event_a, event_b):
    return combine_bidirectional(responded_existence(trace, event_a, event_b), responded_existence(trace, event_b, event_a))


def exclusive_choice(trace, event_a, event_b):
    return unary_outcome((event_a in trace) != (event_b in trace))


TEMPLATES = {
    "existence": existence,
    "absence": absence,
    "init": init,
    "responded_existence": responded_existence,
    "coexistence": coexistence,
    "exclusive_choice": exclusive_choice,
    "response": response,
    "precedence": precedence,
    "succession": succession,
    "alternate_response": alternate_response,
    "alternate_precedence": alternate_precedence,
    "alternate_succession": alternate_succession,
    "chain_response": chain_response,
    "chain_precedence": chain_precedence,
    "chain_succession": chain_succession,
}
