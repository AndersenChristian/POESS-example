"""Send an ordered event stream to the Siddhi customer input endpoint."""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SUPPORTED_ACTIONS = {
    "PlaceOrder",
    "ReceiveOrder",
    "CancelOrder",
    "PayOrder",
}


def load_events(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("A .json stream file must contain an array of events")
        events = parsed
    else:
        events = [json.loads(line) for line in text.splitlines() if line.strip()]

    if not events:
        raise ValueError("The stream file does not contain any events")

    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise ValueError(f"Event {index} must be a JSON object")
        if not isinstance(event.get("order_id"), str) or not event["order_id"]:
            raise ValueError(f"Event {index} must have a non-empty string order_id")
        if event.get("action") not in SUPPORTED_ACTIONS:
            actions = ", ".join(sorted(SUPPORTED_ACTIONS))
            raise ValueError(f"Event {index} has an unsupported action; use: {actions}")

    return events


def send_event(url, event, timeout):
    body = json.dumps(event).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
        return response.status, response_body


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send an ordered JSON/JSONL event stream to Siddhi."
    )
    parser.add_argument("file", type=Path, help="JSON array or JSONL event stream file")
    parser.add_argument(
        "--url",
        default=os.getenv("SIDDHI_URL", "http://localhost:7071/customer"),
        help="Siddhi customer endpoint (default: %(default)s)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to wait between events (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print events without sending them",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.delay < 0 or args.timeout <= 0:
        raise ValueError("--delay must be non-negative and --timeout must be positive")
    if not args.file.is_file():
        raise FileNotFoundError(f"Stream file not found: {args.file}")

    events = load_events(args.file)
    total = len(events)
    print(f"Loaded {total} event(s) from {args.file}")

    for index, event in enumerate(events, start=1):
        if args.dry_run:
            print(f"[{index}/{total}] {event['action']} {event['order_id']}")
        else:
            try:
                status, response = send_event(args.url, event, args.timeout)
            except (HTTPError, URLError, TimeoutError) as error:
                print(f"[{index}/{total}] failed: {error}", file=sys.stderr)
                return 1
            print(
                f"[{index}/{total}] {event['action']} {event['order_id']} "
                f"-> HTTP {status} {response}"
            )

        if index < total and args.delay:
            time.sleep(args.delay)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
