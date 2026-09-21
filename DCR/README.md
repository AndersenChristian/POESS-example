# DCR Order Processing Demo

This folder contains the DCR-based implementation of the project. It shows how a process can be modeled with DCR Graph constraints, coordinated through Siddhi, and connected to Python services.

The goal is to provide a small but functional workflow example for order handling, where events such as placing, receiving, canceling, and paying an order are validated and executed through a process-aware backend.

---

## Overview

The DCR example is built from three main runtime components:

- a Python microservice that interacts with the DCR backend
- a Siddhi runtime that routes incoming events and validates process state
- a logging service that stores operational errors and warnings

Everything is orchestrated with Docker Compose and can be started locally as a single stack.

---

## Architecture

```text
Customer / Event Source
          |
          v
      Siddhi Runtime
          |
          +----> Microservice
          |            |
          |            v
          |         DCR Graph API
          |
          +----> Logging Service
```

Siddhi acts as the central orchestration layer. It receives incoming customer actions, checks whether the order is valid in the current process state, sends the request to the microservice, and records failures to the logging service.

---

## Components

### Microservice
Location: `microservice`

This Flask service is responsible for interacting with the DCR Graph API and executing workflow events.

Responsibilities:

- create a new DCR case for an order
- trigger events such as `PlaceOrder`, `ReceiveOrder`, `CancelOrder`, and `PayOrder`
- return callback results to Siddhi
- expose HTTP endpoints for event execution

Key files:

- `app.py` – REST endpoints and request handling
- `dcr_helper.py` – DCR API integration and credential handling
- `requirements.txt` – Python dependencies
- `.env.template` – template for the required environment variables

### Siddhi runtime
Location: `siddhi`

Siddhi manages event processing, order validation, routing, and state tracking.

Responsibilities:

- receive incoming customer actions
- validate the order state before forwarding a request
- call the correct microservice endpoint
- receive callback responses and update state
- send failures to the logging service

### Logging service
Location: `logging_service`

This lightweight service logs operational issues and writes them to a file for later inspection.

---

## Example order flow

A typical DCR workflow looks like this:

1. A customer sends a request to place an order
2. Siddhi validates that the order is not already active
3. Siddhi calls the DCR microservice
4. The microservice creates a DCR case and executes the relevant event
5. The result is returned to Siddhi through a callback
6. Later, the same order can be received, canceled, or paid for
7. Invalid actions are rejected and logged

---

## Supported actions

The process supports the following order actions:

- `PlaceOrder`
- `ReceiveOrder`
- `CancelOrder`
- `PayOrder`

These actions are routed through the DCR logic and validated before execution.

---

## Prerequisites

Before running the DCR setup, make sure that:

- Docker and Docker Compose are installed
- a valid DCR Graph account is available
- the required credentials are configured locally

You need the following environment variables in the microservice:

- `DCR_GRAPH_ID`
- `DCR_USERNAME`
- `DCR_PASSWORD`

A template is available in `microservice/.env.template`.

---

## Configuration

Create a `.env` file in the `microservice` folder based on the template:

```env
DCR_GRAPH_ID=YOUR_GRAPH_ID
DCR_USERNAME=YOUR_USERNAME
DCR_PASSWORD=YOUR_PASSWORD
```

> Do not commit real credentials to version control. Keep the actual `.env` file local only.

---

## Running the DCR stack

From the `DCR` folder, run:

```bash
docker compose up --build
```

This starts the main services for the project:

- microservice
- Siddhi runtime
- logging service

To stop the stack:

```bash
docker compose down
```

---

## Project structure

```text
DCR/
├── docker-compose.yml
├── README.md
├── rebuild.sh
├── logging_service/
│   ├── app.py
│   ├── dockerfile
│   ├── logs/
│   └── XES/
├── microservice/
│   ├── .env.template
│   ├── app.py
│   ├── dcr_helper.py
│   ├── dockerfile
│   └── requirements.txt
└── siddhi/
    ├── OrderFoodAppDEMO.siddhi
    └── dockerfile
```

---

## Example runtime behavior

The system expects requests in the following shape:

```json
{
  "order_id": "ORD-1001",
  "action": "PlaceOrder"
}
```

The microservice endpoints then perform the DCR operations for the corresponding order. If a request is invalid, Siddhi rejects it before it reaches the backend and forwards the error to the logging service.

---

## Logging and debugging

The logging service records entries in a file and prints them to the Docker console. This makes it easier to trace invalid requests and process errors during development.

Typical log messages include:

- order does not exist
- invalid transition in the DCR process
- execution failed for a given order action

---

## Notes

This DCR implementation is intentionally minimal, but it is designed to be extended. It acts as a strong foundation for more advanced event-driven systems that require strict process constraints, state validation, and service orchestration.

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

