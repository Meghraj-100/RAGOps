# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please send an e-mail to the repository maintainers. Do not open public GitHub issues for security vulnerabilities.

Please include:
- A description of the issue and potential impact
- Detailed steps to reproduce
- Suggested fix or remediation if known

All security vulnerabilities will be reviewed promptly.

## Security Baseline & Policies

### 1. Secret Management & Rotation
- Never commit active API keys, JWT signing keys, or database passwords to git.
- If a secret is exposed in development or committed history, consider it compromised immediately:
  - **Groq API Keys**: Revoke immediately in Groq Console (`https://console.groq.com/keys`) and issue a replacement.
  - **Database Passwords**: Update the database role password with `ALTER USER ... WITH PASSWORD '...'` and update production environment variables.
  - **API Keys**: Update `API_KEY` across services and clients.

### 2. Environment Segregation
- In `production` (`ENVIRONMENT=production`):
  - `API_KEY` must be configured with a high-entropy secret (at least 16 characters).
  - Default database credentials (`ragpass`) are rejected at startup (fail-closed).
  - `GROQ_API_KEY` must be configured.
- Protected endpoints require an API key passed via `X-API-Key` header or `Authorization: Bearer <key>`.
- The `/api/v1/health` endpoint remains accessible without credentials for container liveness and readiness probes.

### 3. Defensive Controls Implemented
- **Constant-time Key Comparison**: All API keys are compared using `secrets.compare_digest` to prevent timing attacks.
- **Path Traversal Protection**: Dataset and file loaders enforce strict regex allowlists (`^[a-zA-Z0-9_-]+$`) and path resolution within allowed directories.
- **Infinite Loop / CPU Exhaustion Protection**: Text chunking strictly enforces `0 <= overlap < chunk_size` and `chunk_size > 0`.
- **Defensive HTTP Headers**: Responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **Least-Privilege Containers**: Docker images run as non-root unprivileged users.
