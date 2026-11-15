# NetSim Lite

React/TypeScript + React Flow frontend and FastAPI backend for an educational network simulator.

## Setup

Requires Python 3.10+ and Node.js 20.19+ or 22.12+. From the project root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements-dev.txt
npm.cmd --prefix frontend install
```

## Run

```powershell
.\start.ps1
```

Open http://127.0.0.1:5173. Ctrl+C stops the launcher. If PowerShell policy prevents running scripts, start these in two terminals from the project root:

```powershell
.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

```powershell
npm.cmd --prefix frontend run dev
```

Both servers are required. Keep ports 8000 and 5173 free. Vite proxies /api to FastAPI. API docs: http://127.0.0.1:8000/docs.

## Demo

1. Send a packet from PC-A to PC-B. The upper route through R1 costs 2. Watch each hop and the event log.
2. Select an upper link and uncheck Link enabled. Send again: R2 becomes the route, costing 5.
3. Disable the PC-A to R2 link too. Calculate again to see an unreachable destination.
4. Reset to demo restores the original topology.
5. Add devices with the palette; drag to position. Connect right ports to left ports. Links are bidirectional.
6. Select devices to edit names/IPs; select links to edit non-negative costs, enable/disable, or delete them. Deleting a device removes its links.
7. Save/Load stores one topology in localStorage for this browser and origin.
8. Open Subnet calculator: 192.168.1.0/26 gives mask 255.255.255.192, broadcast 192.168.1.63, and usable hosts 192.168.1.1 through 192.168.1.62.

Routing-relevant edits cancel animations and clear stale routes; selecting or moving devices preserves the route. Recalculate after changing links. Assigned IPv4 addresses are validated on route requests. Zero costs and source equal to destination are supported.

## Checks

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
npm.cmd --prefix frontend run build
cd frontend
npx.cmd playwright test
```

Browser tests need the backend running and Microsoft Edge installed. Playwright starts Vite automatically. For bundled Chromium, remove channel: 'msedge' from playwright.config.ts and run npx.cmd playwright install chromium.

The production frontend builds into frontend/dist; serving that output requires /api forwarding to FastAPI.

## Production deployment

See [DEPLOYMENT.md](DEPLOYMENT.md). The production entry point serves the compiled frontend and API together: `python -m backend.production`. A multi-stage Dockerfile, Compose configuration, pinned production dependencies, and Render blueprint are included. Build/run with `docker compose up --build -d` and open http://localhost:8080. The cloud deployment has not been performed.

## API

- GET /api/health
- POST /api/route: nodes (id, optional label/ip/kind), links (source, target, cost, enabled), source, destination.
- POST /api/simulate: same input; returns path, cost, reachability and packet events.
- POST /api/subnet: {"cidr":"192.168.1.0/26"}.

## Scope

Core prototype features are implemented: topology editing, routing, packet animation, failed links, subnetting, and local save/load. This is a graph simulation; it does not send real traffic or emulate Ethernet or TCP/IP stacks. Costs are abstract weights, not measured latency. IP addresses are metadata and do not control connectivity. /31 and /32 follow Python ipaddress host conventions.

Submission materials are in deliverables/: an editable DOCX report, PDF, 14-slide PPTX with notes, captioned WebM demo, screenshots, viva notes, walkthrough, verification logs, and clean source ZIP. See deliverables/README.md. Replace identity placeholders and review the required institutional format before submission.
