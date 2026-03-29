# Free to build and secure operations

This document explains how to run and ship the project **without paid licenses** for the stack itself, and how to keep deployments **reasonably secure**.

## Free to build (no paid product required)

| Area | Notes |
|------|--------|
| **License** | Project is **MIT**. Dependencies are open-source; check each license if you redistribute a combined product. |
| **Python packages** | Installed from **PyPI** at no charge. Large ML libraries (e.g. TensorFlow, PyTorch) are **free** but heavy on **disk and download time** — not a license fee. |
| **Node / dashboard** | `npm install` uses the public npm registry; no fee for normal open-source deps. |
| **Docker images** | Official-style images (Postgres, Redis, Mongo, Prometheus, etc.) are **free to pull** from public registries; you may pay **your host** (VM, bandwidth), not for the images themselves. |
| **External map/routing APIs** | **Optional**. Geoapify and OpenRouteService offer **free tiers** with limits; the app can use **mock data** when keys are absent (see `.env.example`). OpenStreetMap-related usage is subject to each provider’s terms. |
| **CI** | GitHub Actions and similar providers have **free tiers** for public repos and limited private minutes. |

**Summary:** Building and running this project does not require purchasing a commercial license for the stack described above. Optional third-party APIs may have quotas; hosting costs are separate.

## Reducing build time and size (optional)

The default `pyproject.toml` dependency set is broad (ML, Spark, Kafka clients, etc.). For a **lighter** install you can:

- Use **`uv sync --extra ci`** (or the `ci` optional dependency group) where a minimal set is defined for automation.
- Over time, split rarely used stacks into **optional extras** (e.g. `ml`, `streaming`) so default installs stay smaller — see roadmap in the main README.

Docker builds use **`uv sync --frozen`** (see `Dockerfile`) and the committed **`uv.lock`**, so installs are reproducible. The full dependency tree is still large; you may later introduce a **slim** extra or multi-stage build that only installs what the API imports.

## Security checklist

### Development

- [ ] Use `.env` locally; **never** commit it (it is gitignored).
- [ ] Keep `ALLOW_DEV_AUTH_BYPASS` **false** unless you deliberately need unauthenticated dev access.

### Production

- [ ] `ENVIRONMENT=production`
- [ ] Strong, unique `JWT_SECRET_KEY` (32+ bytes of randomness)
- [ ] Strong database and Redis passwords; restrict services to private networks
- [ ] `ALLOWED_ORIGINS` set to real front-end URLs only
- [ ] `ALLOW_DEV_AUTH_BYPASS=false`
- [ ] HTTPS termination in front of the API
- [ ] Regular dependency and image updates

### Docker Compose

- [ ] Override default passwords via **environment** or a secrets mechanism; do not rely on compose file defaults in real deployments.
- [ ] Do not publish Postgres/Mongo/Redis ports on `0.0.0.0` on the public internet without a firewall.

## Where to read more

- [SECURITY.md](../../SECURITY.md) — vulnerability reporting and deployment summary
- [../../.env.example](../../.env.example) — required and optional variables
- [../security/SECURITY_AUDIT.md](../security/SECURITY_AUDIT.md) — audit notes and fixes applied
