from trace_collection import collect_process_instances, load_events, filename
from pathlib import Path
import xml.etree.ElementTree as ElementTree
import yaml

LIFECYCLE_POINTERS = {"complete", "completed", "done", "activity/done"}


def build_log(process_name, instances):
    log = ElementTree.Element("log", {"xes.version": "1.0", "xes.features": ""})
    for name, prefix, uri in (
            ("Concept", "concept", "http://www.xes-standard.org/concept.xesext"),
            ("Time", "time", "http://www.xes-standard.org/time.xesext"),
            ("Lifecycle", "lifecycle", "http://www.xes-standard.org/lifecycle.xesext")
    ):
        ElementTree.SubElement(log, "extension", {"name": name, "prefix": prefix, "uri": uri})

    ElementTree.SubElement(log, "string", {
        "key": str("concept:name"),
        "value": process_name,
    })

    for game, uuid, instance_num, path in instances:
        reduced_events = reduce_events(load_events(path))
        # print(reduced_events)
        build_trace(log, game, process_name, uuid, instance_num, reduced_events)
    return log



def build_trace(parent, game, process, uuid, instance_num, cleaned):
    trace = ElementTree.SubElement(parent, "trace")

    ElementTree.SubElement(trace, "string", {
        "key": "concept:name",
        "value": f"{game}_{process}_{instance_num}"
    })

    ElementTree.SubElement(trace, "string", {
        "key": "trace:id",
        "value": uuid
    })

    ElementTree.SubElement(trace, "string", {
        "key": "game:id",
        "value": game
    })

    ElementTree.SubElement(trace, "string", {
        "key": "cpee:instance",
        "value": instance_num
    })

    """
    for element in trace:
        print(element.get("key"), element.get("value"))
    """

    for clean_event in cleaned:
        rebuild_event(trace, clean_event)


def reduce_events(raw_events):
    cleaned = []
    previous_entry = None
    for activity in raw_events:
        # print(activity)

        if "concept:name" in activity:
            name = activity["concept:name"]
        elif isinstance(activity.get("concept"), dict) and "name" in activity.get("concept"):
            name = activity.get("concept")["name"]
        else:
            name = None

        if name is not None and any(lifecycle in LIFECYCLE_POINTERS for lifecycle in lifecycle_values(activity)):
            if "concept:name" in activity:
                name = activity["concept:name"]
            elif isinstance(activity.get("concept"), dict) and "name" in activity.get("concept"):
                name = activity.get("concept")["name"]
            else:
                name = None

            if "time:timestamp" in activity:
                timestamp = activity["time:timestamp"]
            elif isinstance(activity.get("time"), dict) and "timestamp" in activity.get("time"):
                timestamp = activity.get("time")["timestamp"]
            else:
                timestamp = None

            clean_event = {
                "concept:name": name,
                "time:timestamp": timestamp,
                "cpee:activity": activity.get("cpee:activity"),
                "cpee:activity_uuid": activity.get("cpee:activity_uuid"),
                "data": None,
            }

            if previous_entry is not None and "dataelements/change" in lifecycle_values(previous_entry):
                data = previous_entry.get("data")
                # print(data)
                if data is not None:
                    clean_event["data"] = yaml.safe_dump(data, sort_keys=False).strip()
            cleaned.append(clean_event)
        previous_entry = activity

    # print(cleaned)
    return cleaned


def rebuild_event(parent, cleaned):
    event = ElementTree.SubElement(parent, "event")

    ElementTree.SubElement(event, "string", {
        "key": "concept:name",
        "value": cleaned["concept:name"]
    })

    ElementTree.SubElement(event, "string", {
        "key": "lifecycle:transition",
        "value": "complete"
    })

    if cleaned["time:timestamp"] is not None:
        ElementTree.SubElement(event, "date", {
            "key": "time:timestamp",
            "value": cleaned["time:timestamp"]
        })

    if cleaned["cpee:activity"] is not None:
        ElementTree.SubElement(event, "string", {
            "key": "cpee:activity",
            "value": "" if cleaned["cpee:activity"] is None else cleaned["cpee:activity"]
        })

    if cleaned["cpee:activity_uuid"] is not None:
        ElementTree.SubElement(event, "string", {
            "key": "cpee:activity_uuid",
            "value": "" if cleaned["cpee:activity_uuid"] is None else cleaned["cpee:activity_uuid"]
        })

    if cleaned["data"] is not None:
        ElementTree.SubElement(event, "string", {
            "key": "data",
            "value": cleaned["data"]
        })


# Derived from the previous step analysis of log file with Generative AI
def lifecycle_values(activity):
    vals = []
    if "lifecycle:transition" in activity:
        vals.append(activity["lifecycle:transition"])
    if "cpee:lifecycle:transition" in activity:
        vals.append(activity["cpee:lifecycle:transition"])
    lifecycle = activity.get("lifecycle")
    if isinstance(lifecycle, dict) and lifecycle.get("transition") is not None:
        vals.append(lifecycle["transition"])
    return [str(value).strip().lower() for value in vals if value is not None]


if __name__ == "__main__":
    processes = ["get_input"]
    # processes = ["action_attack", "get_input", "action_move", "gridmaster", "manipulate_grid", "player_turn"]
    ROOT = Path(__file__).resolve().parent.parent
    raw_logs = ROOT / "log_files" / "raw_logs"

    for process in processes:
        instances = collect_process_instances(raw_logs, process)
        # print(instances)
        log = build_log(process, instances)
        out_path = ROOT / "log_files" / "reduced_logs" / f"{process}.xes"
        out_path.write_text(filename(log), encoding="utf-8")