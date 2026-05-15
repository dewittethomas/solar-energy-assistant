# Solar Energy Assistant

Solar Energy Assistant is a FastAPI backend for solar dataset uploads, model training, predictions, recommendations, and user metadata.

## Directory Structure

```text
core/             Application settings
ingestion/        File reading, column mapping, canonicalization, and time resolution
models/           Request models and domain-style value objects
repositories/     Database, parquet, cache, weather, and model persistence
responses/        API response schemas
routers/          FastAPI route definitions
services/         Business logic orchestration
model_artifacts/  Generated ONNX models
storage/uploads/  Uploaded and processed datasets
```

## Run Locally

```bash
uv sync
uv run uvicorn main:app --reload
```

## Run With Docker

```bash
docker compose up --build
```
