# Project Server

A FastAPI-based server for project management.

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Run the server:
```bash
uvicorn src.project_server.main:app --reload --port 8001
```

## Endpoints

- `GET /` - Welcome message
- `GET /hello` - Hello World endpoint
- `GET /health` - Health check

## Development

The server will be available at `http://localhost:8001` with automatic API documentation at `http://localhost:8001/docs`.
