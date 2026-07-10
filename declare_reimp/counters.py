from collections import namedtuple

TraceOutcome = namedtuple("TraceOutcome",
                          ["activated", "satisfied", "non_vacuous", "activations", "fulfillments", "violations"])


def find_positions(trace, activity):
    positions = []
    for index in range(len(trace)):
        if trace[index] == activity:
            positions.append(index)

    return positions


def unary_outcome(satisfaction_condition):
    return TraceOutcome(
        activated=True,
        satisfied=satisfaction_condition,
        non_vacuous=satisfaction_condition,
        activations=1,
        fulfillments=1 if satisfaction_condition else 0,
        violations=0 if satisfaction_condition else 1,
    )


def relation_outcome(trigger_positions, fulfillments, violations):
    if len(trigger_positions) > 0:
        activated = True
    else:
        activated = False

    if violations == 0:
        satisfied = True
    else:
        satisfied = False

    if satisfied and activated and fulfillments > 0:
        non_vacuous = True
    else:
        non_vacuous = False

    return TraceOutcome(
        activated=activated,
        satisfied=satisfied,
        non_vacuous=non_vacuous,
        activations=len(trigger_positions),
        fulfillments=fulfillments,
        violations=violations,
    )


def combine_bidirectional(forward, backward):
    if forward.satisfied and backward.satisfied:
        satisfied = True
    else:
        satisfied = False

    return TraceOutcome(
        activated=forward.activated or backward.activated,
        satisfied=satisfied,
        non_vacuous=satisfied and forward.non_vacuous and backward.non_vacuous,
        activations=forward.activations + backward.activations,
        fulfillments=forward.fulfillments + backward.fulfillments,
        violations=forward.violations + backward.violations,
    )
