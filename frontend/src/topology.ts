import type { Node, Edge } from "@xyflow/react";

export type Device = Node<
  { label: string; ip: string; kind: string; packet?: boolean },
  "device"
>;
export type Wire = Edge<{ cost: number; enabled: boolean }>;
type Topology = {
  nodes: Device[];
  edges: Wire[];
  source: string;
  destination: string;
};
function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
const nonempty = (value: unknown): value is string =>
  typeof value === "string" && value.trim().length > 0;

export function parseTopology(value: unknown): Topology {
  const invalid = () => new Error("Saved topology is invalid.");
  if (
    !record(value) ||
    !Array.isArray(value.nodes) ||
    !Array.isArray(value.edges)
  )
    throw invalid();
  const nodes: Device[] = value.nodes.map((n: unknown) => {
    if (
      !record(n) ||
      !nonempty(n.id) ||
      n.id !== n.id.trim() ||
      !record(n.position) ||
      !Number.isFinite(n.position.x) ||
      !Number.isFinite(n.position.y) ||
      !record(n.data) ||
      typeof n.data.label !== "string" ||
      typeof n.data.ip !== "string" ||
      !["pc", "router", "switch"].includes(String(n.data.kind))
    )
      throw invalid();
    return {
      id: n.id,
      type: "device",
      position: { x: n.position.x as number, y: n.position.y as number },
      data: { label: n.data.label, ip: n.data.ip, kind: n.data.kind as string },
    };
  });
  const ids = new Set(nodes.map((n) => n.id));
  if (ids.size !== nodes.length) throw invalid();
  const pairs = new Set<string>(),
    edgeIds = new Set<string>();
  const edges: Wire[] = value.edges.map((e: unknown) => {
    if (
      !record(e) ||
      !nonempty(e.id) ||
      edgeIds.has(e.id) ||
      typeof e.source !== "string" ||
      typeof e.target !== "string" ||
      !ids.has(e.source) ||
      !ids.has(e.target) ||
      e.source === e.target ||
      !record(e.data) ||
      typeof e.data.cost !== "number" ||
      !Number.isFinite(e.data.cost) ||
      e.data.cost < 0 ||
      typeof e.data.enabled !== "boolean"
    )
      throw invalid();
    const pair = JSON.stringify([e.source, e.target].sort());
    if (pairs.has(pair)) throw invalid();
    pairs.add(pair);
    edgeIds.add(e.id);
    return {
      id: e.id,
      source: e.source,
      target: e.target,
      data: { cost: e.data.cost, enabled: e.data.enabled },
    };
  });
  const endpoint = (id: unknown) =>
    typeof id === "string" && ids.has(id) ? id : "";
  return {
    nodes,
    edges,
    source: endpoint(value.source),
    destination: endpoint(value.destination),
  };
}
