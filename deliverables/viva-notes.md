# Viva preparation

1. **What does the project simulate?** An undirected weighted graph, minimum-cost routing, logical packet hops, link failures, and IPv4 subnet calculations. It does not implement a real network stack.
2. **Why use Dijkstra?** Link costs are non-negative and the task is a single-source minimum-cost route. A priority queue efficiently selects the next tentative distance.
3. **Why reject negative weights?** A negative edge could improve a node after its distance was selected as minimum, invalidating Dijkstra’s reasoning.
4. **Are zero-cost links valid?** Yes. Relaxation uses a strict improvement condition, which also avoids cycling through equal-distance zero-cost loops.
5. **Is the chosen route always the fewest hops?** No. It minimizes the sum of link costs; fewer hops and smaller cost are different objectives.
6. **Is link cost latency?** No. It is an abstract teaching weight. The approximately 800 ms animation interval is a visual pacing choice.
7. **What happens on a link failure?** The link stays visible as disabled. The next route request excludes it from adjacency and recalculates the path. There is no distributed routing protocol.
8. **How is an unreachable destination represented?** An empty path, null total_cost, and reachable false. A simulation includes an unreachable event.
9. **What happens if source equals destination?** A one-node path, zero cost, and creation/delivery events without forwarding hops.
10. **What if two paths have equal cost?** Either minimum-cost path is valid. The implementation does not perform equal-cost multipath load balancing.
11. **What is the algorithm’s complexity?** For this simple graph, the heap-based implementation has the usual O((V + E) log V) time bound. Adjacency, heap, and tracking require O(V + E) storage.
12. **What does CIDR /26 mean?** Twenty-six of the 32 IPv4 bits form the network prefix. Six host bits give 64 total addresses, ordinarily 62 usable.
13. **Why are /31 and /32 special?** Python ipaddress treats both /31 point-to-point addresses as usable and represents a /32 as a single host. The normal subtract-two rule is not applied to those cases.
14. **Why normalize host bits?** An input such as 192.168.1.15/26 belongs to network 192.168.1.0/26. strict=False allows the calculator to return the containing network.
15. **How does the frontend communicate with the backend?** Fetch sends JSON POST requests to /api endpoints. Vite proxies them to FastAPI on port 8000; responses drive route display and animation.
16. **Why no database?** The first version needs one local topology save. Browser localStorage is adequate, but it does not sync across browsers or users.
17. **What does Pydantic validate?** Request structure, device kinds, nonblank identifiers, finite non-negative numeric costs, and strict booleans. Graph logic additionally checks unique IDs, endpoints, duplicate/self-links, and IPv4 metadata.
18. **How do asynchronous races get handled?** Route-relevant changes invalidate the active generation; stale results are ignored. Subnet input changes similarly invalidate previous requests. POST requests have a timeout.
19. **Do routers and switches behave realistically?** No. They are visual categories with identical graph routing behavior; there is no MAC table, per-interface routing, or address-based connectivity.
20. **Which bugs were fixed?** Examples include routes disappearing on selection, stale deleted endpoints, decimal cost entry, malformed saved data, old subnet responses overwriting new input, and numeric overflow. See BUGFIXES.md.
21. **Why custom Dijkstra instead of NetworkX?** It keeps the core algorithm small and explainable. The guide proposed NetworkX, but the delivered code uses heapq.
22. **What do the tests prove?** They verify their specific scenarios. Passing tests and a successful build do not prove absence of every possible defect.
23. **What can be improved?** Multiple named saves, JSON import/export, more topology presets, richer interface semantics, guided exercises, and a separately scoped deployment.
24. **What should you disclose?** Follow institutional rules for tools and AI assistance. Explain the code and your contribution accurately; do not claim independent authorship or external approval that did not occur.
