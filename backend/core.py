"""Graph routing and IPv4 calculations for an educational simulator."""
import heapq
import ipaddress
import math


def route(nodes, links, source, destination):
    ids = [node['id'] for node in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError('Device IDs must be unique')
    graph = {key: [] for key in ids}
    pairs = set()
    for node in nodes:
        if node.get('ip'):
            ipaddress.IPv4Address(node['ip'])
    if source not in graph or destination not in graph:
        raise ValueError('Source and destination must exist')
    for link in links:
        a, b, cost = link['source'], link['target'], link.get('cost', 1)
        if a not in graph or b not in graph:
            raise ValueError('Link endpoints must exist')
        if a == b:
            raise ValueError('Links must connect two different devices')
        pair = frozenset((a, b))
        if pair in pairs:
            raise ValueError('Only one link is allowed between two devices')
        pairs.add(pair)
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
            raise ValueError('Link costs must be finite and non-negative')
        if link.get('enabled', True):
            graph[a].append((b, cost))
            graph[b].append((a, cost))
    distances, previous = {source: 0}, {}
    overflow = False
    queue = [(0, source)]
    while queue:
        distance, current = heapq.heappop(queue)
        if distance != distances[current]:
            continue
        if current == destination:
            path = [current]
            while current in previous:
                current = previous[current]
                path.append(current)
            return dict(source=source, destination=destination, path=path[::-1], total_cost=distance, reachable=True)
        for neighbor, cost in graph[current]:
            candidate = distance + cost
            if not math.isfinite(candidate):
                overflow = True
                continue
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = current
                heapq.heappush(queue, (candidate, neighbor))
    if overflow:
        # An overflowing dead end must not hide a finite alternative or make a
        # genuinely disconnected destination look reachable.
        visited, pending = {source}, [source]
        while pending:
            current = pending.pop()
            for neighbor, _ in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        if destination in visited:
            raise ValueError('Total route cost exceeds the supported numeric range; reduce link costs')
    return dict(source=source, destination=destination, path=[], total_cost=None, reachable=False)


def subnet(cidr):
    network = ipaddress.IPv4Network(cidr, strict=False)
    first, last = int(network.network_address), int(network.broadcast_address)
    if network.prefixlen < 31:
        first += 1
        last -= 1
    return dict(network=str(network.network_address), prefix=network.prefixlen,
                mask=str(network.netmask), broadcast=str(network.broadcast_address),
                first_host=str(ipaddress.IPv4Address(first)),
                last_host=str(ipaddress.IPv4Address(last)), usable_hosts=last-first+1)
