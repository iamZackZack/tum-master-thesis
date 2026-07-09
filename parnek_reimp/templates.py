class Template:
    def check_constraint(self, log, graph):
        return


class AtMostOne(Template):
    def check_constraint(self, log, graph):
        for activity_a in log.activities:
            never_repeats = all(trace.count(activity_a) <= 1 for trace in log)
            if never_repeats:
                graph.add_exclude(activity_a, activity_a)


class Response(Template):
    def check_constraint(self, log, graph):
        for activity_a in log.activities:
            for activity_b in log.activities:
                if activity_a != activity_b and follows(log, activity_a, activity_b):
                    graph.add_response(activity_a, activity_b)


class Precedence(Template):
    def check_constraint(self, log, graph):
        for activity_a in log.activities:
            for activity_b in log.activities:
                if activity_a != activity_b and precedes(log, activity_a, activity_b):
                    graph.add_condition(activity_a, activity_b)


class ChainPrecedence(Template):
    def check_constraint(self, log, graph):
        for activity_a in log.activities:
            for activity_b in log.activities:
                if activity_a != activity_b and directly_precedes(log, activity_a, activity_b):
                    graph.add_include(activity_a, activity_b)
                    graph.add_exclude(activity_b, activity_b)


def follows(log, event_a, event_b):
    for trace in log:
        for event in range(len(trace)):
            if trace[event] == event_a:
                found_b = False
                for next_event in range(event + 1, len(trace)):
                    if trace[next_event] == event_b:
                        found_b = True
                        break
                if not found_b:
                    return False
    return True


def precedes(log, event_a, event_b):
    for trace in log:
        for event in range(len(trace)):
            if trace[event] == event_b:
                found_a = False
                for prev_event in range(event):
                    if trace[prev_event] == event_a:
                        found_a = True
                        break
                if not found_a:
                    return False
    return True


def directly_precedes(log, event_a, event_b):
    for trace in log:
        for event in range(len(trace)):
            if trace[event] == event_b:
                if event == 0:
                    return False
                if trace[event-1] != event_a:
                    return False
    return True
