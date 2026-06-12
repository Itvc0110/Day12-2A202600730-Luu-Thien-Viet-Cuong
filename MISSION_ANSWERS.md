# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded secrets in source code.
2. Fixed port and config values instead of environment variables.
3. Debug mode enabled all the time.
4. No health or readiness endpoint.
5. No graceful shutdown handling.

### Exercise 1.2: Basic version
- Run the basic app with its `requirements.txt`.
- Start the server.
- Send a POST request to `/ask` with JSON body `{"question": "Hello"}`.

### Exercise 1.3: Comparison table

| Feature | Basic | Advanced | Why it matters |
|---|---|---|---|
| Config | Hardcoded | Environment variables | Easier to move between environments and avoid secret leaks |
| Health check | Missing | Present | Platforms can monitor and restart unhealthy instances |
| Logging | print() | Structured logs | Easier to search and parse in production |
| Shutdown | Abrupt | Graceful | Avoids dropped requests and data loss |

### Discussion answers
1. A public hardcoded API key can be copied and abused immediately, causing data exposure and cost spikes.
2. Stateless design lets multiple instances share no local memory state, so traffic can be load balanced safely.
3. Dev/prod parity means keeping dependencies, config style, startup commands, and observability as similar as possible across environments.

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11-slim`.
2. Working directory: `/app`.
3. Copy `requirements.txt` first so Docker can cache dependency layers.
4. `CMD` is the default command and can be overridden; `ENTRYPOINT` is more fixed.

### Exercise 2.2: Build and run
- Build the image with `docker build`.
- Run it with `docker run -p 8000:8000 ...`.
- Test `/ask` with a JSON POST request.

### Exercise 2.3: Multi-stage build
- Stage 1 installs build dependencies.
- Stage 2 only copies runtime artifacts.
- Result: smaller, cleaner, safer image.

### Exercise 2.4: Docker Compose stack
- Compose starts the agent and Redis together.
- The agent talks to Redis over the compose network.
- Nginx, if present, acts as a reverse proxy / load balancer.

### Discussion answers
1. `COPY requirements.txt` first keeps the dependency layer reusable when code changes.
2. `.dockerignore` should exclude `venv/`, `.env`, `__pycache__/`, logs, and git metadata to keep builds small and safe.
3. Use a volume mount like `-v` in Docker run or a named volume in Compose.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway
- Connect the repo.
- Set env vars.
- Deploy with `railway up`.
- Test the public URL.

### Exercise 3.2: Render
- Push to GitHub.
- Create a Blueprint service.
- Let Render read `render.yaml`.

### Exercise 3.3: Cloud Run
- Use build and service YAML files.
- Cloud Build handles the CI/CD pipeline.

### Discussion answers
1. Serverless is not always ideal for AI agents because of cold starts and execution limits.
2. Cold start is the delay while the platform spins up an idle instance.
3. Move to Cloud Run when you need more production control, scaling, and reliability.

## Part 4: API Security

### Exercise 4.1: API Key authentication
- The key is checked in the auth dependency before the agent logic runs.
- Missing key should return `401`.
- Invalid key should return `401` or `403`, depending on policy.
- Rotate keys by changing the environment variable and redeploying.

### Exercise 4.2: JWT authentication
- The user logs in.
- The app issues a signed token.
- The client includes `Authorization: Bearer <token>` on protected requests.

### Exercise 4.3: Rate limiting
- Use a sliding-window style limiter.
- The lab limit is `20 req/min` in the production sample.
- Admin bypass can be implemented by using a separate bucket or higher limit.

### Exercise 4.4: Cost guard
- Track spending per user per day or month.
- Reject requests when spending exceeds the budget.
- Store totals in Redis for stateless behavior.

### Discussion answers
1. API Key is simplest for internal tools; JWT is better for user identity and claims; OAuth2 is best when you need delegated third-party access.
2. A reasonable starting point for a small AI agent is 10-20 requests/minute per user.
3. Revoke or rotate the key, deploy the new secret, and invalidate the old one immediately.

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks
- `/health` is liveness: is the process alive?
- `/ready` is readiness: can it take traffic now?

### Exercise 5.2: Graceful shutdown
- Catch `SIGTERM`.
- Stop accepting new work.
- Finish in-flight requests.
- Exit cleanly.

### Exercise 5.3: Stateless design
- Do not keep session state only in memory.
- Use Redis or a database for shared state.

### Exercise 5.4: Load balancing
- Run multiple agent instances behind Nginx.
- Traffic is spread across instances.
- If one instance dies, others continue serving traffic.

### Exercise 5.5: Test stateless design
- Create state on one instance.
- Kill that instance.
- Confirm another instance can still serve the same user flow.

### Discussion answers
1. Health checks let the platform restart broken containers; readiness checks stop traffic before startup or during shutdown.
2. Graceful shutdown prevents dropped requests and reduces data corruption risk.
3. Stateless apps scale horizontally because any instance can serve any request.
4. Load balancing spreads traffic and improves availability.

## Part 6: Final Project

### Completed package
- The final lab is implemented in `06-lab-complete/`.
- It includes Docker, Compose, config, API key auth, rate limiting, cost guard, health, readiness, logging, and graceful shutdown.

### Production readiness
- `python check_production_ready.py` passes with `20/20` checks in the local code check.

### Notes
- Public deployment URL can be added later in `DEPLOYMENT.md` after actual cloud deployment.
