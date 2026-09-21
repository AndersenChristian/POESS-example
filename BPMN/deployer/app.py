import asyncio
import json
import os
import threading
from datetime import datetime, timezone

import grpc
import requests
from flask import Flask, jsonify, request
from pyzeebe import Job, ZeebeClient, ZeebeWorker

ZEEBE_ADDRESS = os.getenv("ZEEBE_ADDRESS", "zeebe:26500")
BPMN_FILE = os.getenv("BPMN_FILE", "/bpmn/food_order.bpmn")
SIDDHI_CALLBACK_URL = os.getenv("SIDDHI_CALLBACK_URL", "http://siddhi:7072/middleman")
CUSTOMER_PROCESS_ID = "Process_06p6nly"

app = Flask(__name__)
client = None
worker = None
event_loop = None
process_keys = {}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_order_id(data):
    return data.get("order_id") or data.get("event", {}).get("order_id")


def callback(order_id, case_id, event, payload=None, error=""):
    body = {
        "order_id": order_id,
        "case_id": str(case_id),
        "event": event,
        "timestamp": now_iso(),
        "role": "camunda",
        "payload": json.dumps(payload or {}),
        "error": error,
    }
    response = requests.post(SIDDHI_CALLBACK_URL, json=body, timeout=30)
    response.raise_for_status()


def get_case_id(order_id, supplied_case_id=None):
    return supplied_case_id or process_keys.get(order_id, "UNKNOWN_CASE")


def run_async(coroutine):
    if event_loop is None:
        raise RuntimeError("Communication adapter is not ready")
    future = asyncio.run_coroutine_threadsafe(coroutine, event_loop)
    return future.result(timeout=30)


async def publish_message(name, order_id, variables):
    await client.publish_message(name, str(order_id), variables)


@app.post("/place_order")
def place_order():
    data = request.get_json(force=True)
    order_id = get_order_id(data)
    if not order_id:
        return jsonify({"error": "order_id is required"}), 400

    process_key = run_async(client.run_process(
        CUSTOMER_PROCESS_ID,
        variables={"orderId": order_id},
    ))
    process_keys[order_id] = process_key
    callback(order_id, process_key, "PlaceOrder", {"processInstanceKey": process_key})
    return jsonify({"status": "accepted", "case_id": str(process_key)})


@app.post("/cancel_order")
def cancel_order():
    data = request.get_json(force=True)
    order_id = get_order_id(data)
    if not order_id:
        return jsonify({"error": "order_id is required"}), 400
    case_id = get_case_id(order_id, data.get("case_id"))
    run_async(publish_message("OrderCancelled", order_id, {"orderId": order_id, "caseId": case_id}))
    return jsonify({"status": "accepted"})


@app.post("/receive_order")
def receive_order():
    data = request.get_json(force=True)
    order_id = get_order_id(data)
    if not order_id:
        return jsonify({"error": "order_id is required"}), 400
    case_id = get_case_id(order_id, data.get("case_id"))
    run_async(publish_message("FoodReceived", order_id, {"orderId": order_id, "caseId": case_id}))
    return jsonify({"status": "accepted"})


@app.post("/pay_order")
def pay_order():
    data = request.get_json(force=True)
    order_id = get_order_id(data)
    if not order_id:
        return jsonify({"error": "order_id is required"}), 400
    return jsonify({"status": "accepted"})


async def place_order_task(orderId, job: Job):
    variables = {"orderId": orderId, "caseId": job.process_instance_key}
    order_id = orderId
    await publish_message("OrderCreated", order_id, variables)
    return variables


async def make_order_task(orderId, caseId=None, job: Job = None):
    return {"orderId": orderId, "caseId": caseId} if caseId else {"orderId": orderId}


async def cancel_order_task(orderId, caseId, job: Job):
    variables = {"orderId": orderId, "caseId": caseId}
    callback(orderId, caseId, "CancelOrder", variables)
    return variables


async def send_food_task(orderId, caseId=None, job: Job = None):
    variables = {"orderId": orderId, "caseId": caseId} if caseId else {"orderId": orderId}
    await publish_message("FoodReceived", orderId, variables)
    callback(orderId, caseId, "ReceiveOrder", variables)
    return variables


async def request_payment_task(orderId, caseId=None, job: Job = None):
    variables = {"orderId": orderId, "caseId": caseId} if caseId else {"orderId": orderId}
    callback(orderId, caseId, "PayOrder", variables)
    return variables


async def deploy_and_work():
    global client, worker
    channel = grpc.aio.insecure_channel(ZEEBE_ADDRESS)
    client = ZeebeClient(grpc_channel=channel)
    worker = ZeebeWorker(grpc_channel=channel)
    worker.task(task_type="place-order", variables_to_fetch=["orderId"])(place_order_task)
    worker.task(task_type="make-order", variables_to_fetch=["orderId", "caseId"])(make_order_task)
    worker.task(task_type="cancel-order", variables_to_fetch=["orderId", "caseId"])(cancel_order_task)
    worker.task(task_type="send-food", variables_to_fetch=["orderId", "caseId"])(send_food_task)
    worker.task(task_type="request-payment", variables_to_fetch=["orderId", "caseId"])(request_payment_task)
    for attempt in range(1, 31):
        try:
            deployment = await client.deploy_process(BPMN_FILE)
            print(f"[Camunda] BPMN deployed: {deployment}", flush=True)
            break
        except Exception as error:
            cause = getattr(error, "__cause__", None)
            print(
                f"[Camunda] deployment attempt {attempt} failed: "
                f"{error!r}; cause={cause!r}",
                flush=True,
            )
            if attempt == 30:
                raise
            await asyncio.sleep(2)
    await worker.work()


def serve_http():
    app.run(host="0.0.0.0", port=5001, threaded=True)


async def main():
    global event_loop
    event_loop = asyncio.get_running_loop()
    threading.Thread(target=serve_http, daemon=True).start()
    await deploy_and_work()


if __name__ == "__main__":
    asyncio.run(main())
