# AILA Ingest

AILA Ingest is a **production-ready, full-stack ingestion platform** that orchestrates the entire life cycle for heterogeneous knowledge sources—articles, PDFs, GitHub repositories, YouTube videos, and more. It extracts raw content, standardizes and enriches it, and persists vector embeddings that are ready to plug into retrieval-augmented applications.

This broader mission goes beyond classic ETL by emphasizing automated source acquisition, observability, and downstream-ready vector stores that can feed copilots, analytics, or any AI-fueled workflow.

---

## Table of Contents

- [AILA Ingest](#aila-ingest)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Architecture](#architecture)
  - [Tech Stack](#tech-stack)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Clone \& Bootstrap](#clone--bootstrap)
  - [Configuration](#configuration)
  - [Running the Stack](#running-the-stack)
  - [Project Structure](#project-structure)
  - [License](#license)

---

## Features

- **Multi-source extraction**: Built-in extractors for web articles, PDFs, YouTube, and GitHub repositories. New types can be added via a pluggable dispatcher.
- **Preprocessing pipeline**: Cleaning, chunking, and embedding handlers per source type ensure consistent downstream data.
- **Vector storage**: Embedded chunks are written to Qdrant with collection metadata for efficient semantic search.
- **Airflow DAG**: `etl_dag` orchestrates extract → warehouse query → clean → chunk/embed → vector load, with guard rails for duplicates.
- **Streamlit frontend**: Upload form, file tracking, DAG status stream, and historical dashboard with summaries.
- **Observability**: Structured logging to stdout + `backend/logs/aila.log`; ready for JSON log shipper integrations.
- **12-factor configuration**: Settings loaded via Pydantic from `.env`, keeping secrets out of source control.

---

## Architecture
![alt text](./images/aila-ingest.jpg)

- **Backend API**: FastAPI endpoints triggering Airflow DAGs, exposing run status, logs, and file upload endpoints.
- **Airflow Tasks**: Python-based tasks in `backend/etl/tasks` orchestrate dispatchers and document models.
- **Storage**: MongoEngine models store raw & cleaned documents; Qdrant collections store vectors.
- **Frontend**: Streamlit pages (`Data_Upload`, `Upload_Dashboard`) interact with the API and visualize results.

---

## Tech Stack

| Layer          | Technology                                |
| -------------- | ----------------------------------------- |
| API            | FastAPI                                   |
| Orchestration  | Apache Airflow DAG (taskflow API)         |
| Data           | MongoDB (via MongoEngine), Qdrant         |
| Frontend       | Streamlit                                 |
| Infrastructure | Docker Compose, Grafana + Loki , Promtail |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local tooling/tests)
- Node/npm not required (Streamlit frontend is Python-based)
- Optional: `poetry` for dependency management

### Clone & Bootstrap

```bash
git clone https://github.com/miladbehrooz/aila.git
cd aila
cp .env.example .env   # populate with credentials, API keys, etc.
```

Install dependencies locally (if running without Docker):

```bash
poetry install   # or python -m venv .venv && pip install -r requirements.txt
```

---

## Configuration

- **Backend**: `backend/settings/settings.py` reads values from `.env`. Required keys include Mongo/Qdrant hosts, Airflow credentials, embedding provider details, etc.
- **Frontend**: `frontend/settings/settings.py` uses `.env` for API URL and logging settings.
- **Environment files**: Keep secrets in `.env` (never commit). Example variables:

```
MONGO_DB_HOST=mongo:27017
QDRANT_DATABASE_HOST=qdrant
OPENAI_API_KEY=...
AIRFLOW_API_URL=http://airflow-webserver:8080/api/v1
```

---

## Running the Stack

1. **Start services**:
   ```bash
   docker compose up --build
   ```
   This launches backend API, Airflow scheduler/webserver, MongoDB, Qdrant, and Streamlit frontend.

2. **Access components**:
   - FastAPI docs: `http://localhost:8000/docs`
   - Streamlit UI: `http://localhost:8501`
   - Airflow: `http://localhost:8080` (default `airflow/airflow`)
   - Qdrant Dashboard: `http://localhost:6333/dashboard`

   - Grafana: `http://localhost:3000` (default `admin/admin`, requires Loki stack)
   - Mongo Express or other DB consoles as configured in `docker-compose.yml`

3. **Trigger ETL**:
   - Use Streamlit “Data Upload” page to submit URLs/files.
   - Or POST to `/api/v1/etl/runs` with JSON `{"sources": ["https://..."]}`.

4. **Monitor**:
   - Streamlit dashboard shows recent DAG runs and summaries.
   - API endpoints expose run status, logs, and cancellation.

---

## Project Structure

```
backend/
  api/                # FastAPI app, routes, services, models
  etl/                # Airflow DAG, tasks, preprocessors, extractors
  infrastructure/     # DB connectors, embeddings, utils
  settings/           # Pydantic settings
frontend/
  pages/              # Streamlit pages (Data Upload, Dashboard)
  services/           # API client wrappers
  state/              # Streamlit session helpers
docker-compose.yml    # Defines Mongo, Qdrant, Airflow, backend, frontend
README.md
```

---

## License

Released under the [MIT License](LICENSE).
