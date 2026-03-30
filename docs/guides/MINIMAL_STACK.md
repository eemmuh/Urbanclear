# Minimal stack: API + dashboard + Postgres

This is the recommended footprint for **learning** and **local demos**: one database, backend, and React UI — **no** MongoDB, Redis, Kafka, Spark, or monitoring stack required.

## What runs where

| Piece | How you run it |
|--------|----------------|
| **Postgres** | Docker (see below) |
| **API** | `uv run python start_api.py` or `make api` (port **8000**) |
| **Dashboard** | `cd dashboard && npm run dev` (port **3001** in `vite.config.ts`, proxies `/api` to API) |

**MongoDB:** Set `DATABASE__MONGODB__ENABLED=false` in `.env` so the API does not try to connect to Mongo (no 2s wait, no connection warnings). Redis remains optional; cache/rate limits degrade gracefully if Redis is down.

## 1. Start Postgres only

From the repo root:

```bash
docker compose -f docker-compose.minimal.yml up -d
```

Copy env and point the app at Postgres (defaults match compose):

```bash
cp .env.example .env
# Add this line for Postgres-only (recommended):
# DATABASE__MONGODB__ENABLED=false
# POSTGRES_* should match docker-compose.minimal.yml (defaults usually fine)
```

## 2. Install and run the API

```bash
uv sync
uv run python start_api.py
# or: make api
```

- API docs: <http://localhost:8000/api/docs>  
- Health: <http://localhost:8000/health>

## 3. Install and run the dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open <http://localhost:3001> (ensure `ALLOWED_ORIGINS` in `.env` includes this origin for direct API/WebSocket calls).

## 4. Stop Postgres

```bash
docker compose -f docker-compose.minimal.yml down
```

Data is kept in the Docker volume `postgres_minimal_data` until you remove it.

## Makefile shortcuts

```bash
make minimal-up    # start Postgres (minimal compose)
make minimal-down  # stop Postgres
```
