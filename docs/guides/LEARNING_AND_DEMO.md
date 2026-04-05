# Learning and demo installs

The repository supports a **small default install** so you can run the API and dashboard without downloading TensorFlow, PyTorch, Spark, Kafka clients, Jupyter, etc.

## Default (fast)

```bash
uv sync
uv run python start_api.py
```

This matches **`pyproject.toml`** `[project] dependencies` — the FastAPI stack, databases clients, Prometheus, Socket.IO, and a minimal numeric stack (`numpy`, `scikit-learn`, …) for unpickling simple models under `models/simple_trained/` if present.

## Full historical stack (optional)

For notebooks, GeoPandas, TensorFlow/Torch, Spark/Kafka **Python** libraries, Streamlit, etc.:

```bash
uv sync --extra full
```

Use this for notebooks, heavy ML experiments, or scripts that import Spark/Kafka client libraries. Optional Kafka/Spark **services** still come from `docker-compose.yml` when you run the full stack.

## Development tools

```bash
uv sync --extra dev
```

`pytest`, `ruff`, etc. are **not** in the default install — use `--extra dev` (or `--extra ci`) before `make test` / `uv run pytest`.

## CI parity

```bash
uv sync --frozen --extra ci
```

## Docker

The `Dockerfile` uses `uv sync --frozen --no-dev`, which installs the **default** (demo) dependency set — smaller images and faster builds than the full stack.

## API + dashboard + Postgres

For **only** Postgres in Docker and the API + React dashboard on the host, see **[MINIMAL_STACK.md](MINIMAL_STACK.md)** and `docker-compose.minimal.yml`.
