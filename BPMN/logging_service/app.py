from flask import Flask, request, jsonify
from datetime import datetime, timezone
from pathlib import Path
import json
import xml.etree.ElementTree as ET

app = Flask(__name__)

LOG_DIR = Path("/logs")
XES_DIR = Path("/XES")
LOG_DIR.mkdir(parents=True, exist_ok=True)
XES_DIR.mkdir(parents=True, exist_ok=True)

RUN_ID = datetime.now(timezone.utc).strftime("%y%m%d_%H%M%S")
EVENT_STORE = LOG_DIR / f"{RUN_ID}_events.json"
XES_FILE = XES_DIR / f"{RUN_ID}_process_log.xes"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_event_payload(data):
    payload = data.get("event") if isinstance(data, dict) and "event" in data and isinstance(data["event"], dict) else data

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            payload = {}

    event_name = payload.get("event") or payload.get("activity") or payload.get("name") or "unknown"
    timestamp = payload.get("timestamp") or utc_now_iso()
    case_id = payload.get("case_id") or payload.get("case") or payload.get("trace_id") or "UNKNOWN_CASE"
    order_id = payload.get("order_id")
    role = payload.get("role") or payload.get("user") or payload.get("actor") or "system"
    error = payload.get("error")
    payload_data = payload.get("payload") or {}

    if isinstance(payload_data, str):
        try:
            payload_data = json.loads(payload_data)
        except (TypeError, ValueError):
            payload_data = {"raw": payload_data}

    return {
        "case_id": str(case_id),
        "order_id": str(order_id) if order_id is not None else "",
        "event": str(event_name),
        "timestamp": str(timestamp),
        "role": str(role),
        "error": str(error) if error is not None else "",
        "payload": payload_data,
    }


def write_json_store(events):
    with open(EVENT_STORE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)


def build_xes(events):
    root = ET.Element(
        "log",
        {
            "xes.version": "2.0",
            "xes.features": "nested-attributes",
            "openxes.version": "1.0RC7",
        },
    )

    ET.SubElement(
        root,
        "extension",
        {
            "name": "concept",
            "prefix": "concept",
            "uri": "http://www.xes-standard.org/concept.xesext",
        },
    )
    ET.SubElement(
        root,
        "extension",
        {
            "name": "time",
            "prefix": "time",
            "uri": "http://www.xes-standard.org/time.xesext",
        },
    )
    ET.SubElement(
        root,
        "extension",
        {
            "name": "org",
            "prefix": "org",
            "uri": "http://www.xes-standard.org/org.xesext",
        },
    )

    global_trace = ET.SubElement(root, "global", {"scope": "trace"})
    ET.SubElement(global_trace, "string", {"key": "concept:name", "value": "name"})

    global_event = ET.SubElement(root, "global", {"scope": "event"})
    ET.SubElement(global_event, "string", {"key": "concept:name", "value": "name"})
    ET.SubElement(global_event, "date", {"key": "time:timestamp", "value": "2024-01-01T00:00:00.000+00:00"})
    ET.SubElement(global_event, "string", {"key": "org:resource", "value": "resource"})

    ET.SubElement(root, "classifier", {"name": "Event Name", "keys": "concept:name"})

    grouped = {}
    for event in events:
        case_id = event.get("case_id", "UNKNOWN_CASE")
        grouped.setdefault(case_id, []).append(event)

    for case_id, case_events in grouped.items():
        trace = ET.SubElement(root, "trace")
        ET.SubElement(trace, "string", {"key": "concept:name", "value": str(case_id)})

        for event in case_events:
            event_el = ET.SubElement(trace, "event")
            ET.SubElement(event_el, "string", {"key": "concept:name", "value": str(event.get("event", "unknown"))})
            ET.SubElement(event_el, "date", {"key": "time:timestamp", "value": str(event.get("timestamp", utc_now_iso()))})
            ET.SubElement(event_el, "string", {"key": "org:resource", "value": str(event.get("role", "system"))})

            if event.get("order_id"):
                ET.SubElement(event_el, "string", {"key": "order_id", "value": str(event["order_id"])})
            if event.get("case_id"):
                ET.SubElement(event_el, "string", {"key": "case_id", "value": str(event["case_id"])})
            if event.get("error"):
                ET.SubElement(event_el, "string", {"key": "error", "value": str(event["error"])})

            payload = event.get("payload") or {}
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (TypeError, ValueError):
                    payload = {"raw": payload}

            if isinstance(payload, dict):
                for key, value in payload.items():
                    if value is None:
                        continue
                    ET.SubElement(event_el, "string", {"key": f"payload:{key}", "value": str(value)})
            elif payload is not None:
                ET.SubElement(event_el, "string", {"key": "payload:raw", "value": str(payload)})

    ET.indent(root)
    tree = ET.ElementTree(root)
    tree.write(XES_FILE, encoding="utf-8", xml_declaration=True)


@app.route("/log", methods=["POST"])
def log_event():
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"status": "invalid", "message": "No JSON payload received"}), 400

    event = normalize_event_payload(data)

    try:
        if EVENT_STORE.exists():
            with open(EVENT_STORE, "r", encoding="utf-8") as f:
                events = json.load(f)
        else:
            events = []
    except (json.JSONDecodeError, OSError):
        events = []

    events.append(event)
    write_json_store(events)
    build_xes(events)

    print(f"[XES] Logged event={event['event']} case_id={event['case_id']} ts={event['timestamp']}", flush=True)
    return jsonify({"status": "logged", "xes_file": str(XES_FILE)}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)
