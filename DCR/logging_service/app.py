from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

LOG_FILE = "/logs/logs.txt"

@app.route("/log", methods=["POST"])
def log_error():
    data = request.json["event"]
    order_id = data.get("order_id")
    error = data.get("error")

    timestamp = datetime.datetime.utcnow().isoformat()

    log_entry = f"{timestamp} | order_id={order_id} | error={error}\n"

    # Append to file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

    # Print to console (Docker logs)
    print(log_entry, flush=True)

    return jsonify({"status": "logged"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
