# Bug audit

Fixed and regression-tested:

- Selecting or moving canvas items erased the route and cancelled packet animations. Only routing-relevant edits now invalidate simulation state.
- Deleting a source/destination left a stale dropdown value and enabled route calculation. Invalid endpoints now clear and both route buttons disable.
- Starting a failed route request left the previous successful route visible. Each request clears old results.
- Controlled numeric input prevented typing fractional costs reliably and silently converted an empty input to zero. Cost edits now use a draft, commit on blur/Enter, and restore invalid values with a log message.
- Corrupted saved topology could introduce duplicate edge IDs, duplicate links, missing booleans/IP fields, invalid render types, or self-links. Loading validates the structure and reconstructs approved fields before replacing the canvas.
- Older subnet responses could overwrite changed input; errors/results also remained visible after edits. Generation checks discard stale responses and edits clear results.
- Network failures exposed raw fetch/JSON exceptions and hung requests stayed pending indefinitely. API requests now time out and provide actionable messages.
- Same-device transmissions recorded creation without delivery. They now log both events.
- The API accepted boolean/string costs, string booleans, blank IDs, unsupported device kinds, parallel links, and self-links. Request/graph validation now rejects these cases.
- Valid non-negative weights could overflow the total cost and report a reachable destination as disconnected. Overflow is handled explicitly without hiding finite alternative routes.
- CORS allowed localhost but omitted the 127.0.0.1 frontend origin. Both local origins are supported.
- The launcher could silently switch frontend ports or report success before backend startup, and Windows Python child processes could survive cleanup. It now checks ports, waits for backend health, uses a strict frontend port, and cleans up the child interpreter.

Validation: 14 backend/core tests, 9 browser tests, and the production build pass. Browser scenarios cover connections, reverse routes, deletion, fractional/zero costs, malformed storage, stale subnet requests, error handling, and original demo flows.

This is a bounded audit of the prototype, not a guarantee that every possible bug has been eliminated.
