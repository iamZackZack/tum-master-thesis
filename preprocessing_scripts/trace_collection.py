from pathlib import Path
import re
import yaml
import xml.etree.ElementTree as ElementTree
from xml.dom import minidom

# Regular Expression was generated with the help of Generative AI
INDEX_REGEX = re.compile(r"^\s*(?P<process_name>[A-Za-z0-9_]+)\s+\((?P<uuid>[0-9a-fA-F-]{36})\)\s+-\s+(?P<instance_num>\d+)\s*$")

PREFIXES = ("concept:", "time:", "lifecycle:", "org:", "cost:", "semantic:")
KEYS = {"concept:name", "time:timestamp", "lifecycle:transition", "concept", "time", "lifecycle", "cpee:lifecycle:transition"}


def find_game_dirs(raw_logs_dir):
    return sorted(p.name for p in raw_logs_dir.iterdir() if p.is_dir())


def collect_process_instances(raw_logs_dir, process_name):
    instances = []
    found = []
    games = find_game_dirs(raw_logs_dir)

    for game in games:
        processes = []
        with open(raw_logs_dir / game / "index.txt") as index_file:
            for line in index_file:
                proc_line = INDEX_REGEX.match(line)
                if proc_line and proc_line.group("process_name") == process_name:
                    processes.append((proc_line.group("uuid"), proc_line.group("instance_num")))

        for uuid, instance_number in processes:
            instances.append((game, uuid, instance_number))

    # print(instances)

    for game, uuid, instance_number in instances:
        path = raw_logs_dir / game / f"{uuid}.xes.yaml"
        if path.exists():
            found.append((game, uuid, instance_number, path))

    return found


def load_events(path):
    with open(path) as f:
        docs = list(yaml.safe_load_all(f))

    events = []
    for doc in docs:
        if doc is None:
            continue
        if isinstance(doc, list):
            events.extend(d for d in doc if isinstance(d, dict))
        elif isinstance(doc, dict):
            if "event" in doc and isinstance(doc["event"], dict):
                events.append(doc["event"])
            elif "events" in doc and isinstance(doc["events"], list):
                events.extend(d for d in doc["events"] if isinstance(d, dict))
            else:
                events.append(doc)
    return events


def build_event(parent, activity):
    event = ElementTree.SubElement(parent, "event")

    if "concept:name" in activity:
        name = activity["concept:name"]
    elif isinstance(activity.get("concept"), dict) and "name" in activity.get("concept"):
        name = activity.get("concept")["name"]
    else:
        name = "UNKNOWN_EVENT"

    ElementTree.SubElement(event, "string", {
        "key": str("concept:name"),
        "value": "" if name is None else str(name),
    })

    if "lifecycle:transition" in activity:
        lifecycle = activity["lifecycle:transition"]
    elif "cpee:lifecycle:transition" in activity:
        lifecycle = activity["cpee:lifecycle:transition"]
    elif isinstance(activity.get("lifecycle"), dict) and "transition" in activity.get("lifecycle"):
        lifecycle = activity.get("lifecycle")["transition"]
    else:
        lifecycle = None

    if lifecycle is not None:
        ElementTree.SubElement(event, "string", {
            "key": "lifecycle:transition",
            "value": str(lifecycle),
        })

    if "time:timestamp" in activity:
        timestamp = activity["time:timestamp"]
    elif isinstance(activity.get("time"), dict) and "timestamp" in activity.get("time"):
        timestamp = activity.get("time")["timestamp"]
    else:
        timestamp = None

    if timestamp is not None:
        ElementTree.SubElement(event, "date", {
            "key": "time:timestamp",
            "value": str(timestamp)})

    for key, value in activity.items():
        key = str(key)
        if key in KEYS:
            continue

        for prefix in PREFIXES:
            if key.startswith(prefix):
                key = "cpee:" + key.replace(":", "_")
                break

        if key in KEYS:
            continue
        add_attr(event, key, value)

    """
    for element in event:
        print(element.get("key"), element.get("value"))
    """

    return event


def add_attr(parent, key, value):
    key = str(key)
    if value is None:
        ElementTree.SubElement(parent, "string", {
            "key": str(key),
            "value": "",
        })
    elif isinstance(value, bool):
        ElementTree.SubElement(parent, "boolean", {
            "key": key,
            "value": "true" if value else "false"
        })
    elif isinstance(value, int):
        ElementTree.SubElement(parent, "int", {
            "key": key,
            "value": str(value)
        })
    elif isinstance(value, float):
        ElementTree.SubElement(parent, "float", {
            "key": key,
            "value": str(value)
        })
    elif isinstance(value, (dict, list)):
        ElementTree.SubElement(parent, "string", {
            "key": str(key),
            "value": yaml.safe_dump(value, sort_keys=False).strip()
        })
    else:
        ElementTree.SubElement(parent, "string", {
            "key": str(key),
            "value": value,
        })


def build_trace(parent, game, process_name, uuid, inst, activities):
    trace = ElementTree.SubElement(parent, "trace")

    ElementTree.SubElement(trace, "string", {
        "key": "concept:name",
        "value": f"{game}_{process_name}_{inst}",
    })

    ElementTree.SubElement(trace, "string", {
        "key": "trace:id",
        "value": uuid,
    })

    ElementTree.SubElement(trace, "string", {
        "key": "game:id",
        "value": game,
    })

    ElementTree.SubElement(trace, "string", {
        "key": "cpee:instance",
        "value": inst,
    })

    for activity in activities:
        build_event(trace, activity)

    return trace


# The XES log specifications were determined by log file examination with the help of Generative AI.
def build_log(process_name, instances):
    log = ElementTree.Element("log", {"xes.version": "1.0", "xes.features": ""})
    for name, prefix, uri in (
        ("Concept",   "concept",   "http://www.xes-standard.org/concept.xesext"),
        ("Time",      "time",      "http://www.xes-standard.org/time.xesext"),
        ("Lifecycle", "lifecycle", "http://www.xes-standard.org/lifecycle.xesext"),
    ):
        ElementTree.SubElement(log, "extension", {"name": name, "prefix": prefix, "uri": uri})

    ElementTree.SubElement(log, "string", {
        "key": str("concept:name"),
        "value": process_name,
    })

    for game, uuid, instance_num, path in instances:
        build_trace(log, game, process_name, uuid, instance_num, load_events(path))

    return log


def filename(log_name):
    rough = ElementTree.tostring(log_name, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ")


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    raw_logs = ROOT / "log_files" / "raw_logs"
    output_dir = ROOT / "log_files" / "trace_logs"
    processes = ["action_attack", "get_input", "action_move", "gridmaster", "manipulate_grid", "player_turn"]

    for process in processes:
        instances = collect_process_instances(raw_logs, process)
        log = build_log(process, instances)

        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{process}.xes"
        out_path.write_text(filename(log), encoding="utf-8")