from flask import Flask, request, jsonify
import json
import requests
from dcr_helper import create_case, execute_event, get_enabled_events
from enum import Enum
from datetime import datetime, timezone

class EventID(str, Enum):
    PlaceOrder = "PlaceOrder"
    ReceiveOrder = "ReceiveOrder"
    CancelOrder = "CancelOrder"
    PayOrder = "PayOrder"
    GetAvailableActions = "GetAvailableActions"

app = Flask(__name__)

SIDDHI_CALLBACK_URL = "http://siddhi:7072/middleman"


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def send_callback_to_siddhi(order_id, case_id, event_name, dcr_result):
    payload = {
        "order_id": order_id,
        "case_id": case_id,
        "event": event_name,
        "timestamp": utc_now_iso(),
        "role": "microservice",
        "payload": json.dumps({
            "enabledEvents": dcr_result.get("enabledEvents", []),
            "status": "error" if dcr_result.get("error") else "success"
        }),
        "error": ""
    }

    if dcr_result.get("error"):
        payload["error"] = dcr_result["message"]

    requests.post(SIDDHI_CALLBACK_URL, json=payload)

def process_event(order_id, case_id, event_name):
    dcr_result = execute_event(case_id, event_name.value)
    # always fetch the current enabled events so every callback tells siddhi what's possible next
    dcr_result["enabledEvents"] = get_enabled_events(case_id)
    send_callback_to_siddhi(order_id, case_id, event_name.value, dcr_result) #required because siddhi doesn't wait for the response from dcr, so we need to send it manually
    return jsonify({"status": "ok"})


@app.route("/place_order", methods=["POST"])
def place_order():
    print("[RAW BODY]", request.data)
    data = request.json
    order_id = data["event"]["order_id"]
    print(f"[PlaceOrder] Received order_id = {order_id}")

    # instantiate a new DCR case
    case_id = create_case()

    return process_event(order_id, case_id, EventID.PlaceOrder)


@app.route("/receive_order", methods=["POST"])
def receive_order():
    data = request.json
    order_id = data.get("order_id")
    case_id = data.get("case_id")
    return process_event(order_id, case_id, EventID.ReceiveOrder)


@app.route("/cancel_order", methods=["POST"])
def cancel_order():
    data = request.json
    order_id = data.get("order_id")
    case_id = data.get("case_id")
    return process_event(order_id, case_id, EventID.CancelOrder)


@app.route("/pay_order", methods=["POST"])
def pay_order():
    data = request.json
    order_id = data.get("order_id")
    case_id = data.get("case_id")
    return process_event(order_id, case_id, EventID.PayOrder)


@app.route("/enabled_events/<case_id>", methods=["GET"])
def enabled_events(case_id):
    events = get_enabled_events(case_id)
    return jsonify({"case_id": case_id, "enabled_events": events})


@app.route("/get_available_actions", methods=["POST"])
def get_available_actions():
    data = request.json
    order_id = data.get("order_id")
    case_id = data.get("case_id")
    events = get_enabled_events(case_id)
    dcr_result = {"error": False, "message": "", "enabledEvents": events}
    send_callback_to_siddhi(order_id, case_id, EventID.GetAvailableActions.value, dcr_result)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
