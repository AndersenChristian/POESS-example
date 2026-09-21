# POESS Example

This repository contains two minimal reference implementations for process-oriented and event-driven software systems:

- a BPMN-based setup built with Camunda Zeebe, Siddhi, and Python
- a DCR-based setup built with DCR Graph, Siddhi, and Python

The goal is to give students a lightweight starting point for exploring workflow automation, event processing, and integration patterns in a hands-on way.

> The BPMN and DCR projects are separate implementations. They are designed to be copied, modified, and extended independently.

---

## Repository structure

```text
POESS-example/
├── BPMN/
│   ├── bpmn/
│   ├── deployer/
│   ├── event_streams/
│   ├── logging_service/
│   ├── siddhi/
│   ├── docker-compose.yml
│   └── README.md
├── DCR/
│   ├── logging_service/
│   ├── microservice/
│   ├── siddhi/
│   ├── docker-compose.yml
│   ├── README.md
│   └── rebuild.sh
├── DevTools/
│   └── docker-compose.yml
├── README.md
└── .gitignore
```

---

## BPMN project

The BPMN implementation focuses on process orchestration using Camunda Zeebe together with a Siddhi-based event layer and Python service components.

Key characteristics:

- order processing modeled as a BPMN workflow
- Zeebe as the workflow engine
- Siddhi handling event routing and processing
- Python deployment services for communication and integration
- logging and process tracking for debugging and inspection

For the BPMN-specific setup and commands, see [BPMN/README.md](BPMN/README.md).

---

## DCR project

The DCR implementation represents an event-driven workflow using DCR Graph semantics and stream processing. It is built around the idea of validating and routing order-related actions through a central event processor.

Key characteristics:

- DCR-based constraints and event handling
- Siddhi runtime for event orchestration
- Python microservice for interaction with the DCR backend
- logging service for recording operational issues

For the DCR-specific setup and commands, see [DCR/README.md](DCR/README.md).

---

## Prerequisites

To run either stack locally, you need:

- Docker Engine or Docker Desktop
- Docker Compose
- VS Code (recommended for development)
- A working local environment capable of building and running containers

For Siddhi development, we recommend using the local editor setup included in the DevTools folder. This provides a lightweight local environment for editing and testing Siddhi files in a way that fits the project setup.

The `DevTools/docker-compose.yml` configuration is the preferred option for this repository.

If you prefer to work with Siddhi directly in VS Code, the WSO2 Siddhi extension is also available here:

- https://marketplace.visualstudio.com/items?itemName=WSO2.streaming-integrator

But notice, that from our experience the DevTools we provice gives much clearer error messages.

---

## Running the examples

From the project root, navigate into the implementation you want to run:

```bash
cd BPMN
docker compose up --build
```

or:

```bash
cd DCR
docker compose up --build
```

To stop the services:

```bash
docker compose down
```

---

## Development notes

- The BPMN and DCR folders are intentionally separate and can be used independently.
- The repository is intended as a foundation for student projects and course examples.
- The design is intentionally minimal so it can be extended with more complex workflows, services, and event patterns.

---

## Useful links

- [BPMN/README.md](BPMN/README.md)
- [DCR/README.md](DCR/README.md)
- [BPMN/event_streams/README.md](BPMN/event_streams/README.md)
