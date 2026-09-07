# DCR Order Processing Demo

This project demonstrates an event-driven order-processing workflow built around DCR graphs, Siddhi stream processing, and Python microservices. It is designed to model a simple customer order lifecycle where actions such as place, receive, cancel, and pay are validated by a central event processor and executed through a DCR backend.

The demo consists of three main runtime components:

- A Python microservice that communicates with the DCR graph API
- A Siddhi runtime that routes incoming customer actions and handles callbacks
- A lightweight logging service that records operational errors to a file

Everything is orchestrated with Docker Compose so the full system can run locally in a single setup.

---

## Architecture overview

The project follows a message-routing pattern where Siddhi acts as the orchestration layer between the customer-facing event stream and the DCR microservice.

```text
Customer / Client
      |
      v
Siddhi Runtime (port 7071 / 7073)
  |
  |-- validates order_id / case_id state
  |-- routes to microservice endpoints
  |
  +--> Microservice (port 5001)
          |
          |-- creates DCR cases
          |-- executes events through DCR API
          |-- sends callback to Siddhi
          |
          +--> DCR Graph API

Siddhi also forwards errors to the Logging Service (port 5002)
      |
      v
Logging Service
  |
  +--> writes to /logs/logs.txt
```

---

## Components

### 1. Microservice
Location: `DCR/microservice`

This is the Python Flask application responsible for interacting with the DCR graph service.

Responsibilities:

- Create new DCR cases for each placed order
- Execute DCR events such as `PlaceOrder`, `ReceiveOrder`, `CancelOrder`, and `PayOrder`
- Forward the outcome back to Siddhi via a callback
- Expose HTTP endpoints for the Siddhi runtime to call

Key files:

- `app.py` - Flask API endpoints and request routing
- `dcr_helper.py` - DCR API integration and authentication logic
- `requirements.txt` - Python dependencies
- `.env.template` - template for required DCR credentials

### 2. Siddhi runtime
Location: `DCR/siddhi`

Siddhi handles stream-based validation, order state tracking, and routing logic.

Responsibilities:

- Receive customer actions from an HTTP input stream
- Check if an order exists in the in-memory `OrderCases` table
- Route valid actions to the microservice endpoints
- Receive callback events from the microservice
- Update the state of active orders
- Send logging payloads to the logging service for invalid actions or failures

Key file:

- `app.siddhi` - event streams, tables, routing logic, and logging sinks

### 3. Logging service
Location: `DCR/logging_service`

This is a minimal Flask service that records errors as timestamped log lines.

Responsibilities:

- Receive POST requests from Siddhi
- Write log entries into `/logs/logs.txt`
- Print the same message to stdout for Docker log visibility

---

## Order lifecycle modeled by the system

The demo models a simple order workflow:

1. Customer requests to place an order
2. Siddhi checks whether the order already exists
3. If valid, it calls the microservice `/place_order` endpoint
4. The microservice creates a new DCR case and executes the `PlaceOrder` event
5. The result is posted back to Siddhi through the callback endpoint
6. Siddhi stores the `order_id` and `case_id` mapping in `OrderCases`
7. Later, the customer may receive, cancel, or pay for the order
8. At each step, Siddhi verifies the order exists before routing the action
9. Errors are sent to the logging service for persistence

---

## Project structure

```text
DCR/
├── docker-compose.yml
├── README.md
├── logging_service/
│   ├── app.py
│   ├── Dockerfile
│   └── logs/
├── microservice/
│   ├── .env.template
│   ├── app.py
│   ├── dcr_helper.py
│   ├── dockerfile
│   ├── requirements.txt
│   └── venv/
└── siddhi/
    ├── app.siddhi
    └── dockerfile
```

---

## Prerequisites

Before running the project, make sure the following are available:

- Docker
- Docker Compose
- A valid DCR Graph account and credentials
- Access to the DCR Graphs API

You will need the following environment variables for the microservice:

- `DCR_GRAPH_ID`
- `DCR_USERNAME`
- `DCR_PASSWORD`

The template for these credentials is available at `DCR/microservice/.env.template`.

---

## Configuration

Create a `.env` file in the `microservice` folder based on the template:

```env
DCR_GRAPH_ID=YOUR_GRAPH_ID
DCR_USERNAME=YOUR_USERNAME
DCR_PASSWORD=YOUR_PASSWORD
```

This file is used by the Flask microservice at startup. The code reads these values with `os.getenv(...)` in `dcr_helper.py`.

> Important: never commit real credentials to version control. Keep the actual `.env` file local only.

---

## Running the system

From the project root (`DCR/`), run:

```bash
docker compose up --build
```

This builds and starts:

- `microservice` on port `5001`
- `siddhi-runtime` on port `7070` and `9390`
- `logging-service` on port `5002`

To stop the stack:

```bash
docker compose down
```

---

## Service endpoints and responsibilities

### Microservice endpoints

The Flask API in `microservice/app.py` exposes the following endpoints:

#### POST `/place_order`
Creates a new DCR case and triggers the `PlaceOrder` event.

Request body:

```json
{
  "order_id": "ORD-1001"
}
```

Behavior:

- Creates a DCR case ID
- Calls the DCR backend to execute `PlaceOrder`
- Sends callback information back to Siddhi

#### POST `/receive_order`
Executes the `ReceiveOrder` event for an existing order.

Request body:

```json
{
  "order_id": "ORD-1001",
  "case_id": "12345"
}
```

#### POST `/cancel_order`
Executes the `CancelOrder` event for an existing order.

Request body:

```json
{
  "order_id": "ORD-1001",
  "case_id": "12345"
}
```

#### POST `/pay_order`
Executes the `PayOrder` event for an existing order.

Request body:

```json
{
  "order_id": "ORD-1001",
  "case_id": "12345"
}
```

---

### Siddhi input and callback behavior

Siddhi listens for incoming customer actions and calls the microservice endpoints as needed.

#### Customer stream
The `CustomerStream` expects a JSON payload like:

```json
{
  "order_id": "ORD-1001",
  "action": "PlaceOrder"
}
```

Allowed actions:

- `PlaceOrder`
- `ReceiveOrder`
- `CancelOrder`
- `PayOrder`

#### Middleman callback stream
The microservice posts callback information to Siddhi at the `middleman` endpoint.

Example payload:

```json
{
  "order_id": "ORD-1001",
  "case_id": "12345",
  "event": "PlaceOrder"
}
```

If the DCR execution returned an error, Siddhi receives:

```json
{
  "order_id": "ORD-1001",
  "case_id": "12345",
  "event": "CancelOrder",
  "error": "DCR returned 400"
}
```

---

## DCR integration details

The DCR logic lives in `microservice/dcr_helper.py`.

The helper configures Basic Authentication headers with the credentials stored in the environment variables:

```python
DCR_API_BASE = "https://api.dcrgraphs.net/api"
```

It supports two key operations:

- `create_case()`
  - Calls the DCR API to create a new simulation instance
  - Retrieves the newest case ID from the graph simulations list

- `execute_event(case_id, event_id)`
  - Sends a POST request to execute a named event on a DCR case
  - Returns a result object with `error`, `message`, and `enabledEvents`

This is the direct bridge between the order logic and the DCR backend.

---

## Error handling and logging

The logging service exposes this endpoint:

#### POST `/log`

Example payload:

```json
{
  "order_id": "ORD-1001",
  "error": "Can't pay an order that doesn't exist"
}
```

The service appends the entry in the format:

```text
2026-09-07T12:00:00.000000 | order_id=ORD-1001 | error=Can't pay an order that doesn't exist
```

The log file is stored at:

```text
DCR/logging_service/logs/logs.txt
```

The log message is also printed to the Docker console for immediate debugging.

---

## Example workflow

A typical successful flow looks like this:

```text
POST /place_order
  {"order_id": "ORD-1001"}
      |
      v
Siddhi validates request and sends to microservice
      |
      v
Microservice creates new DCR case
      |
      v
Microservice calls DCR API: PlaceOrder
      |
      v
Microservice posts callback to Siddhi
      |
      v
Siddhi saves order_id -> case_id in OrderCases
      |
      v
Later: POST /pay_order with same order_id and case_id
```

Invalid actions are rejected by Siddhi before they reach the microservice. Examples include:

- Trying to place an order that already exists
- Trying to cancel an order that was never created
- Trying to receive or pay for a non-existent order

Those invalid operations produce an error message that is forwarded to the logging service.

---

## Docker Compose setup

The `docker-compose.yml` file defines the services:

```yaml
services:
  microservice:
    build: ./microservice
    container_name: dcr-microservice
    ports:
      - "5001:5001"
    env_file:
      - ./microservice/.env
    depends_on:
      - siddhi

  siddhi:
    build: ./siddhi
    container_name: siddhi-runtime
    ports:
      - "7070:7070"
      - "9390:9390"

logging-service:
  build: ./logging_service
  container_name: logging-service
  ports:
    - "5002:5002"
  volumes:
    - ./logging_service/logs:/logs
```

Notes:

- The microservice depends on Siddhi, so the event pipeline starts in the expected order.
- The logging service mounts a local log folder into the container at `/logs`.
- The Siddhi application is loaded from `DCR/siddhi/app.siddhi` when the container starts.

---

## Common troubleshooting

### 1. DCR API authentication fails
Check that the `.env` file contains valid values for:

- `DCR_GRAPH_ID`
- `DCR_USERNAME`
- `DCR_PASSWORD`

If the credentials are incorrect, DCR requests will fail even though the services are up.

### 2. Microservice starts but events do nothing
Check whether the callback URL in `microservice/app.py` is correct:

```python
SIDDHI_CALLBACK_URL = "http://siddhi:7073/middleman"
```

This must match the Siddhi callback receiver configuration.

### 3. Siddhi does not receive or route events
Verify the Siddhi `@source` configurations for `CustomerStream` and `MiddlemanStream` and check that the container is running normally.

### 4. Logs not appearing
Make sure the `logging_service/logs` directory exists and is mounted correctly in Docker Compose.

### 5. Port conflicts
If any of the following ports are already in use on your machine, stop the conflicting process or adjust the port mappings:

- 5001
- 5002
- 7070
- 9390

---

## Useful development notes

- The microservice uses Flask and `requests` for HTTP communication.
- The DCR helper does not store state locally; it relies on the DCR backend as the source of truth for case execution.
- Siddhi acts as the workflow coordinator and maintains the mapping between customer order IDs and DCR case IDs.
- The logging service is intentionally simple and writes plain text entries, which makes it easy to inspect in the local filesystem.

---

## Summary

This project is a compact demonstration of how a stream-processing workflow can orchestrate business events across multiple components:

- customer actions enter through Siddhi
- valid orders are routed to a Python microservice
- the microservice executes DCR graph events
- state is tracked through callbacks
- failed or invalid operations are logged for monitoring

It is a useful reference for building event-driven, graph-based process flows with a microservice architecture.

