from pathlib import Path
import xml.etree.ElementTree as ElementTree
from trace_collection import filename
import yaml

# Event identification logic derived with the help of Generative AI


def transform_file(input_path):
    file = ElementTree.parse(input_path).getroot()
    for event in file.iter():
        if event.tag == "event":
            split_data(event)
    return file


def transform_array_to_set(data_string):
    try:
        full_data = yaml.safe_load(data_string)
        # print(full_data)
    except Exception:
        return {}
    if not isinstance(full_data, list):
        return {}
    attributes = {}
    for item in full_data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name is None:
            continue
        if "value" in item:
            value = item["value"]
        elif "data" in item:
            value = item["data"]
        else:
            continue
        if value is None:
            continue
        attributes[str(name)] = value
    # print(attributes)
    return attributes


def split_data(event):
    for data_elements in list(event):
        # print(data_elements)
        if data_elements.tag == "string" and data_elements.attrib.get("key") == "data":
            attributes = transform_array_to_set(data_elements.attrib.get("value"))

            if not attributes:
                continue

            for key, value in attributes.items():
                if isinstance(value, bool):
                    tag = "boolean"
                    value = "true" if value else "false"
                elif isinstance(value, int):
                    tag = "int"
                    value = str(value)
                elif isinstance(value, float):
                    tag = "float"
                    value = str(value)
                else:
                    tag = "string"
                    value = str(value)

                ElementTree.SubElement(event, tag, {
                    "key": str(key),
                    "value": value
                })

            event.remove(data_elements)

            # for e in event:
            #    print(e.get("key"), e.get("value"))


if __name__ == "__main__":
    # processes = ["get_input"]
    processes = ["action_attack", "get_input", "action_move", "gridmaster", "manipulate_grid", "player_turn"]
    for process in processes:
        ROOT = Path(__file__).resolve().parent.parent
        input_dir = ROOT / "log_files" / "reduced_logs"
        output_dir = ROOT / "log_files" / "transformed_logs"

        root = transform_file(input_dir / f"{process}.xes")
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{process}.xes"
        out_path.write_text(filename(root), encoding="utf-8")
        print(process, ": DONE!")