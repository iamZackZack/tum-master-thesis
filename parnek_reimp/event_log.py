import xml.etree.ElementTree as ElementTree


class EventLog:
    def __init__(self, traces):
        self.traces = traces

        activities = set()
        for trace in traces:
            for name in trace:
                activities.add(name)

        self.activities = sorted(activities)

    def __iter__(self):
        return iter(self.traces)

    def average_length(self):
        return sum(len(t) for t in self.traces) / len(self.traces)


def read_xes(path):
    traces = []
    trace = None
    activity = None
    inside_event = False

    stream = ElementTree.iterparse(path, events=("start", "end"))
    _, root = next(stream)

    for event, elem in stream:
        if event == "start":
            if elem.tag == "trace":
                trace = []
            elif elem.tag == "event":
                activity = None
                inside_event = True
            continue

        if elem.tag == "string" and inside_event and elem.get("key") == "concept:name":
            activity = elem.get("value")
        elif elem.tag == "event":
            trace.append(activity.strip())
            inside_event = False
        elif elem.tag == "trace":
            traces.append(trace)
            root.clear()

    return EventLog(traces)
