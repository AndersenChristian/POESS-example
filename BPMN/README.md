# BPMN Order Processing Demo

This folder contains the BPMN-based implementation of the project. It demonstrates how process logic can be modeled and orchestrated using Camunda Zeebe together with a Siddhi event-processing layer and Python-based integration services.

The setup is intentionally lightweight and acts as a foundation for extension into more advanced process-driven systems.

---

## Overview

The BPMN example combines the following components:

- a Python communication service
- a Siddhi runtime for event handling and stream processing
- Camunda Zeebe as the workflow engine
- Elasticsearch and Operate for process monitoring and inspection
- a logging service for operational output

This gives a full example of a process-centric system where workflow execution and event-driven messaging are connected.

---

## Architecture

```text
Customer / Test Event Stream
          |
          v
      Siddhi Runtime
          |
          v
  Python communication service
          |
          v
       Zeebe Broker
          |
      Elasticsearch / Operate
          |
      Logging Service
```

The communication layer forwards workflow-relevant messages to the BPMN engine, while the event stream and logging components help connect runtime activity with external inputs and outputs.

---

## Components

### Communication service
Location: `BPMN/deployer`

This component acts as the main interface between the event-driven layer and the BPMN engine. It handles communication, process control, and service coordination.

### Siddhi runtime
Location: `BPMN/siddhi`

Siddhi is used for stream-based processing and orchestration logic. It can receive incoming events, validate or route them, and connect to the workflow engine.

### Logging service
Location: `BPMN/logging_service`

This service receives operational messages and stores them in files for inspection and debugging.

### Zeebe, Elasticsearch, and Operate
These components are part of the core BPMN infrastructure and are started through Docker Compose.

---

## Prerequisites

Before starting the BPMN stack, make sure that:

- Docker is installed and running
- Docker Compose is available
- the local environment has enough resources to run the containers

---

## Running the BPMN setup

From the BPMN folder, run:

```bash
docker compose up --build
```

This starts the system containers for:

- communication service
- Siddhi runtime
- logging service
- Zeebe broker
- Elasticsearch
- Operate

To stop everything:

```bash
docker compose down
```

---

## Sending sample events

The repository includes a simple event-stream helper under `BPMN/event_streams`.

Example:

```powershell
python .\event_streams\send_stream.py .\event_streams\test_events.jsonl
```

You can also validate the payload without sending it:

```powershell
python .\event_streams\send_stream.py .\event_streams\test_events.jsonl --dry-run
```

For more details, see [event_streams/README.md](event_streams/README.md).

---

## Notes

This BPMN example is meant to serve as a starter project. It is intentionally simple so you can extend the process logic, event models, and integration points for your own implementation.

For the DCR implementation, see [../DCR/README.md](../DCR/README.md).
