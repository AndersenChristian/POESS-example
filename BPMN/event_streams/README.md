# Event streams

`send_stream.py` sends events to Siddhi in the order they appear in a JSONL or JSON file.

Each event must contain an `order_id` and one of:

- `PlaceOrder`
- `ReceiveOrder`
- `CancelOrder`
- `PayOrder`

From the repository root, with the BPMN stack running:

```powershell
python .\BPMN\event_streams\send_stream.py .\BPMN\event_streams\test_events.jsonl
```

Use `--delay 0` to send without pauses, or `--dry-run` to validate and print the stream without sending it:

```powershell
python .\BPMN\event_streams\send_stream.py .\BPMN\event_streams\test_events.jsonl --dry-run
```

The default endpoint is `http://localhost:7071/customer`. Override it with `--url` or the `SIDDHI_URL` environment variable.

A `.json` file may contain the same events as one JSON array instead of one JSON object per line.
