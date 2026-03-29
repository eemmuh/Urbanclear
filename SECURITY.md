# Security policy

## Supported versions

Security fixes are applied on the default branch (`main` / primary development branch). Use the latest commit for deployments when possible.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security-sensitive reports.

- Email or open a **private** security advisory on the repository (if enabled), describing:
  - Affected component (e.g. `src/api/...`, Docker setup)
  - Steps to reproduce
  - Impact assessment if known

We will acknowledge receipt and coordinate a fix and disclosure timeline.

## Secure deployment (summary)

1. **Secrets**: Copy `.env.example` to `.env`. Never commit `.env`. Use long random values for database passwords and `JWT_SECRET_KEY` (e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
2. **Production**: Set `ENVIRONMENT=production`, `ALLOW_DEV_AUTH_BYPASS=false`, and a real `JWT_SECRET_KEY`.
3. **CORS**: Set `ALLOWED_ORIGINS` to your real front-end origins (comma-separated), not `*`.
4. **Network**: Put the API behind HTTPS (reverse proxy or load balancer). Do not expose database ports to the public internet.
5. **Dependencies**: Run `pip-audit` / `uv pip audit` or `safety check` regularly; keep images and base OS packages updated.

More detail: [docs/guides/FREE_BUILD_AND_SECURITY.md](docs/guides/FREE_BUILD_AND_SECURITY.md) and [docs/security/SECURITY_AUDIT.md](docs/security/SECURITY_AUDIT.md).

## Docker image

The `Dockerfile` runs the app as a non-root user (`app`). Rebuild images when security patches are released for the base image (`python:*-slim`).
