# Production deployment

NetSim Lite can run as **one service**: FastAPI serves `/api/*`, API documentation, and the built React frontend on the same origin. Production does not use Vite's development server or a hard-coded localhost API URL.

## Vercel deployment

Live production URL: **https://netsim-lite.vercel.app**. The Vercel project is connected to `WhiteGod0227/NetSim-Lite` for Git deployments.

Import `WhiteGod0227/NetSim-Lite` into Vercel with the **repository root** as Root Directory. The root `vercel.json` selects FastAPI; its build command installs and builds the frontend. `app.py` exports the combined ASGI application. Python 3.12 and the pinned root requirements are supplied. Do not set the Root Directory to `frontend`, because that would omit the Python backend.

From an authenticated CLI at the project root, run `vercel --prod`. No database, API keys, or separate backend URL are required. The platform supplies the Python runtime; do not use the Dockerfile or a persistent Uvicorn start command for Vercel. Verify `/api/health`, packet delivery, rerouting, and subnet calculation after deployment. Local saved topologies remain specific to each browser and origin.

Reference: [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi).

## Docker deployment

From the project root, with Docker installed:

```sh
docker compose up --build -d
```

Open http://localhost:8080. Check status and logs:

```sh
docker compose ps
docker compose logs --tail=100 netsim
```

Stop with `docker compose down`. To change the host port, copy `.env.example` to `.env` and change `NETSIM_PUBLIC_PORT`. This setting is for Compose only. The container's internal port remains 8000.

The multi-stage Dockerfile builds the frontend with `npm ci`, installs pinned production Python dependencies, and runs the application as a non-root user. Node.js, tests, report-generation packages, and local environment files are not needed in the final image. The health check requests `/api/health`.

## Render deployment

1. Put the deployment source in a Git repository accessible to your Render account.
2. In Render, create a Blueprint from that repository and select the supplied root `render.yaml`.
3. Review the service plan/settings in Render and deploy. The Dockerfile builds both parts; no separate frontend service, database, or API URL setting is required.
4. When deployment finishes, open the assigned HTTPS URL and verify `/api/health`, then send a packet and calculate a subnet.

The blueprint uses the Docker runtime, `/api/health`, and PORT=10000. No Render service has been created. The deployed service uses Vercel as described above.

## Native production process

Requirements: Python 3.10+ and Node.js 20.19+ or 22.12+ for the build. The Dockerfile uses Python 3.12 and Node.js 22. After building, the running server only needs Python.

Windows PowerShell, from the project root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements-production.txt
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
$env:PORT='8080'
.venv\Scripts\python -m backend.production
```

Linux:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-production.txt
npm --prefix frontend ci
npm --prefix frontend run build
PORT=8080 .venv/bin/python -m backend.production
```

The production process fails immediately if the frontend build is missing or PORT is invalid. It does not enable auto-reload. Run it under your host's process manager or Docker for restarts. For a custom domain on your own server, terminate HTTPS at your reverse proxy and forward all paths to this service.

| Variable | Default | Purpose |
| --- | --- | --- |
| PORT | 8000 | Listening port; must be 1–65535 |
| HOST | 0.0.0.0 | Bind address; use 127.0.0.1 for local-only testing |
| NETSIM_STATIC_DIR | frontend/dist relative to project root | Absolute path override for the compiled frontend |

Native startup reads environment variables from the shell/host; it does not automatically load `.env`. Production uses one origin and needs no CORS configuration. The two-server development setup remains available through `start.ps1`.

## Verification and release

With dev dependencies installed:

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
npm.cmd --prefix frontend run build
# Against a running native production server:
$env:NETSIM_TEST_URL='http://127.0.0.1:8080'
Set-Location frontend
npx.cmd playwright test
```

The test URL setting skips launching Vite, so the browser scenarios exercise the compiled frontend and production API together. Browser tests currently use Microsoft Edge; see README.md for Chromium setup.

Prepared release: `NetSim_Lite_Deploy.zip`, containing deployment source/configuration and tests. The frontend is built by Docker or the native build commands, rather than shipping local node_modules or a virtual environment.

Verification limits: the native production server, production assets/API, and browser flows have been checked locally. Docker is not installed in this workspace, so the Docker image itself has not been built or run here. The Vercel production deployment is live at https://netsim-lite.vercel.app.

## Persistence and operation

No credentials or database are required. Save/Load remains browser localStorage; saves from localhost do not automatically move to a new domain. Restarting the server does not delete a browser's saves. TLS, traffic limits, and capacity settings belong to the hosting/reverse-proxy configuration when making the service public. The service remains an educational logical simulator.

References: [FastAPI static files](https://fastapi.tiangolo.com/tutorial/static-files/), [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/), and [Render Blueprint specification](https://render.com/docs/blueprint-spec).
