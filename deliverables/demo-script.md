# Demonstration and narration script

Suggested live demonstration: 3–4 minutes. The supplied WebM is a shorter, captioned automated walkthrough with no narration.

| Time | Action | Suggested explanation |
| --- | --- | --- |
| 0:00–0:25 | Open the topology lab and identify PC-A, R1, R2, and PC-B. | “NetSim Lite demonstrates graph-based routing and IPv4 subnetting. These device icons are simplified; the app does not send real packets.” |
| 0:25–0:55 | Explain both paths, then click Send packet. | “The route through R1 costs 1 + 1 = 2; through R2 it costs 3 + 2 = 5. Dijkstra selects the minimum total cost. The packet marker and log show logical delivery.” |
| 0:55–1:25 | Click the PC-A–R1 link, uncheck Link enabled, and send again. | “Disabled links are excluded from the active graph. On this new request, the alternate route through R2 is selected with cost 5.” |
| 1:25–1:45 | Disable PC-A–R2 too and calculate again. | “There is no remaining path from the source, so the destination is unreachable. This is a valid simulation result, not a server error.” |
| 1:45–2:25 | Reset to demo, save, add/edit a switch, then load. | “The palette adds devices, the inspector edits properties, and Save/Load preserves one topology in this browser. IP fields are metadata and do not govern graph connectivity.” |
| 2:25–3:00 | Calculate 192.168.1.0/26. | “There are six host bits and 64 total addresses. The network is .0, broadcast is .63, and the ordinary usable range is .1 through .62: 62 hosts.” |
| 3:00–3:25 | Briefly show API docs or the architecture slide. | “React sends JSON through the Vite proxy to FastAPI. Pydantic validates requests, custom heapq-based Dijkstra calculates routes, and ipaddress calculates subnets.” |
| 3:25–3:45 | Summarize tests and limitations. | “Fourteen backend/core tests, nine browser tests, and the production build passed. The model does not emulate Ethernet switching, routing protocols, or actual TCP/IP traffic.” |

## Before presenting

- Run the app and verify “Backend connected.” Start with Reset to demo.
- Set source PC-A and destination PC-B. Ensure all four links are enabled.
- Open the PPT and API docs beforehand; keep the captioned video available as a fallback.
- Speak about what is implemented. Do not call the costs milliseconds or claim automatic live rerouting: a new route request performs recalculation.
- Replace presentation/report identity placeholders and follow your institution’s declaration and attribution requirements.

## Video playback

Open `NetSim_Lite_Demo.webm` in Edge, Chrome, or a WebM-capable player. It contains explanatory captions and no voice track. If the institution requires MP4 or spoken narration, convert it with an approved video editor and record your own explanation using this script. Review the final recording before submission.
