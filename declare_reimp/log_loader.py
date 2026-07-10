import xml.etree.ElementTree as ElementTree


def load_log(path):
    log = ElementTree.parse(path).getroot()

    traces = []
    for trace in log:
        events = []
        if trace.tag != "trace":
            continue
        for event in trace:
            if event.tag == "event":
                events.append(activity_name(event))
        traces.append(events)
    return traces


def activity_name(event):
    for attribute in event:
        if attribute.get("key") == "concept:name":
            return attribute.get("value").strip()
