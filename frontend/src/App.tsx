import LinkCost from "./LinkCost";
import { api } from "./api";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type NodeProps,
} from "@xyflow/react";
import { parseTopology, type Device, type Wire } from "./topology";
import PacketEdge from "./PacketEdge";
import {
  Network,
  Monitor,
  Router,
  Server,
  Play,
  Save,
  FolderOpen,
  Plus,
  Trash2,
  Activity,
  Calculator,
  Cable,
  RotateCcw,
} from "lucide-react";

type Result = {
  path: string[];
  total_cost: number | null;
  reachable: boolean;
  events?: {
    type: string;
    node?: string;
    source?: string;
    destination?: string;
  }[];
};
const initialNodes: Device[] = [
  {
    id: "PC-A",
    type: "device",
    position: { x: 70, y: 210 },
    data: { label: "PC-A", kind: "pc", ip: "192.168.1.10" },
  },
  {
    id: "R1",
    type: "device",
    position: { x: 320, y: 70 },
    data: { label: "R1", kind: "router", ip: "192.168.1.1" },
  },
  {
    id: "R2",
    type: "device",
    position: { x: 320, y: 350 },
    data: { label: "R2", kind: "router", ip: "192.168.1.2" },
  },
  {
    id: "PC-B",
    type: "device",
    position: { x: 580, y: 210 },
    data: { label: "PC-B", kind: "pc", ip: "192.168.1.20" },
  },
];
const initialEdges: Wire[] = [
  ["PC-A", "R1", 1],
  ["R1", "PC-B", 1],
  ["PC-A", "R2", 3],
  ["R2", "PC-B", 2],
].map(([source, target, cost], i) => ({
  id: `link-${i}`,
  source: String(source),
  target: String(target),
  data: { cost: Number(cost), enabled: true },
}));
const icons = { pc: Monitor, router: Router, switch: Server };
function DeviceNode({ data, selected }: NodeProps<Device>) {
  const Icon = icons[data.kind as keyof typeof icons] || Router;
  return (
    <div
      className={`device ${selected ? "selected" : ""} ${data.packet ? "packet" : ""}`}
    >
      <Handle type="target" position={Position.Left} />
      <div className="device-icon">
        <Icon size={26} />
      </div>
      <strong>{data.label}</strong>
      <small>{data.ip || "No IP assigned"}</small>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { device: DeviceNode };
const edgeTypes = { packet: PacketEdge };
export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Device>(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Wire>(initialEdges);
  const [tab, setTab] = useState("lab"),
    [selection, setSelection] = useState<{ type: string; id: string } | null>(
      null,
    );
  const [source, setSource] = useState("PC-A"),
    [destination, setDestination] = useState("PC-B");
  const [result, setResult] = useState<Result | null>(null),
    [packet, setPacket] = useState<string | null>(null),
    [busy, setBusy] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    "Lab ready. Choose a route and send your first packet.",
  ]);
  const [status, setStatus] = useState("Connecting"),
    [cidr, setCidr] = useState("192.168.1.0/26"),
    [subnet, setSubnet] = useState<Record<string, string | number> | null>(
      null,
    ),
    [subnetError, setSubnetError] = useState("");
  const generation = useRef(0);
  const subnetGeneration = useRef(0);
  const [subnetBusy, setSubnetBusy] = useState(false);
  const log = useCallback(
    (message: string) =>
      setLogs((old) =>
        [`${new Date().toLocaleTimeString()}  ${message}`, ...old].slice(0, 80),
      ),
    [],
  );
  useEffect(() => {
    let active = true;
    const check = () =>
      fetch("/api/health", { signal: AbortSignal.timeout(5000) })
        .then((r) => {
          if (active) setStatus(r.ok ? "Connected" : "Offline");
        })
        .catch(() => {
          if (active) setStatus("Offline");
        });
    check();
    const timer = setInterval(check, 10000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);
  // Selection, measurements, and positions do not change routing.
  const topologyKey = JSON.stringify({
    nodes: nodes.map((n) => ({ id: n.id, ip: n.data.ip })),
    edges: edges.map((e) => ({
      source: e.source,
      target: e.target,
      cost: e.data?.cost,
      enabled: e.data?.enabled,
    })),
  });
  useEffect(() => {
    if (!nodes.some((n) => n.id === source)) setSource("");
    if (!nodes.some((n) => n.id === destination)) setDestination("");
  }, [topologyKey, source, destination]);
  useEffect(() => {
    generation.current++;
    setResult(null);
    setPacket(null);
    setBusy(false);
  }, [topologyKey, source, destination]);
  useEffect(
    () => () => {
      generation.current++;
      subnetGeneration.current++;
    },
    [],
  );
  const selectedNode =
    selection?.type === "node"
      ? nodes.find((n) => n.id === selection.id)
      : undefined;
  const selectedEdge =
    selection?.type === "edge"
      ? edges.find((e) => e.id === selection.id)
      : undefined;
  const name = (id: string) => nodes.find((n) => n.id === id)?.data.label || id;
  const request = () => ({
    nodes: nodes.map((n) => ({ id: n.id, ...n.data })),
    links: edges.map((e) => ({
      source: e.source,
      target: e.target,
      ...e.data,
    })),
    source,
    destination,
  });
  async function run(animate: boolean) {
    if (busy) return;
    const token = ++generation.current;
    setBusy(true);
    setResult(null);
    setPacket(null);
    try {
      const data = await api<Result>(animate ? "simulate" : "route", request());
      if (token !== generation.current) return;
      setResult(data);
      if (!data.reachable) {
        log("Destination unreachable. Restore a link or connect another path.");
        return;
      }
      log(
        `Route: ${data.path.map(name).join(" → ")} · cost ${data.total_cost}`,
      );
      if (animate) {
        for (let i = 0; i < data.path.length; i++) {
          if (token !== generation.current) return;
          setPacket(data.path[i]);
          log(
            `${i === 0 ? "Packet created at" : i === data.path.length - 1 ? "Packet delivered to" : "Packet forwarded by"} ${name(data.path[i])}`,
          );
          if (data.path.length === 1)
            log(`Packet delivered to ${name(data.path[0])}`);
          await new Promise((resolve) => setTimeout(resolve, 800));
        }
        if (token === generation.current) setPacket(null);
      }
    } catch (error) {
      if (token === generation.current) log((error as Error).message);
    } finally {
      if (token === generation.current) setBusy(false);
    }
  }
  function addDevice(kind: string) {
    const id = `${kind.toUpperCase()}-${crypto.randomUUID().slice(0, 5)}`;
    setNodes((ns) => [
      ...ns,
      {
        id,
        type: "device",
        position: {
          x: 150 + Math.random() * 200,
          y: 100 + Math.random() * 250,
        },
        data: { label: id, kind, ip: "" },
      },
    ]);
    setSelection({ type: "node", id });
  }
  function connect(connection: Connection) {
    if (connection.source === connection.target) {
      log("Connect two different devices.");
      return;
    }
    if (
      edges.some(
        (e) =>
          (e.source === connection.source && e.target === connection.target) ||
          (e.source === connection.target && e.target === connection.source),
      )
    ) {
      log("These devices already have a link.");
      return;
    }
    setEdges((es) =>
      addEdge(
        {
          ...connection,
          id: crypto.randomUUID(),
          data: { cost: 1, enabled: true },
        },
        es,
      ),
    );
  }
  function remove() {
    if (selectedNode) {
      setNodes((ns) => ns.filter((n) => n.id !== selectedNode.id));
      setEdges((es) =>
        es.filter(
          (e) => e.source !== selectedNode.id && e.target !== selectedNode.id,
        ),
      );
    }
    if (selectedEdge)
      setEdges((es) => es.filter((e) => e.id !== selectedEdge.id));
    setSelection(null);
  }
  function save() {
    try {
      localStorage.setItem(
        "netsim-topology",
        JSON.stringify({ nodes, edges, source, destination }),
      );
      log("Topology saved in this browser.");
    } catch {
      log("Unable to save: browser storage is unavailable.");
    }
  }
  function load() {
    try {
      const raw = localStorage.getItem("netsim-topology");
      if (!raw) throw new Error("No saved topology found.");
      const data = parseTopology(JSON.parse(raw));
      setNodes(data.nodes);
      setEdges(data.edges);
      setSource(data.source || "");
      setDestination(data.destination || "");
      setSelection(null);
      log("Saved topology loaded.");
    } catch (error) {
      log((error as Error).message);
    }
  }
  function preset() {
    setNodes(
      initialNodes.map((n) => ({
        ...n,
        data: { ...n.data },
        position: { ...n.position },
      })),
    );
    setEdges(initialEdges.map((e) => ({ ...e, data: { ...e.data! } })));
    setSource("PC-A");
    setDestination("PC-B");
    setSelection(null);
    log(
      "Four-device demo loaded. The upper route costs 2; the lower route costs 5.",
    );
  }
  const renderedEdges = edges.map((e) => {
    const active = result?.path.some(
      (n, i, arr) =>
        i < arr.length - 1 &&
        ((n === e.source && arr[i + 1] === e.target) ||
          (n === e.target && arr[i + 1] === e.source)),
    );
    const index = result?.path.indexOf(packet || "") ?? -1;
    const next = result?.path[index + 1];
    const moving =
      busy &&
      index >= 0 &&
      ((e.source === packet && e.target === next) ||
        (e.target === packet && e.source === next));
    return {
      ...e,
      type: "packet",
      data: { ...e.data!, reverse: e.target === packet },
      label: `${e.data?.cost}${e.data?.enabled ? "" : " · OFF"}`,
      animated: moving,
      style: {
        stroke: e.data?.enabled ? (active ? "#20d4b0" : "#71849a") : "#ef7777",
        strokeWidth: active ? 3 : 2,
        strokeDasharray: e.data?.enabled ? undefined : "6 5",
      },
      labelStyle: { fill: "#d9e5f2", fontWeight: 600 },
      labelBgStyle: { fill: "#182333" },
      labelBgPadding: [8, 5] as [number, number],
    };
  });
  return (
    <div className="app">
      <header>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setTab("lab");
          }}
        >
          <span className="brand-icon">
            <Network />
          </span>
          <span>
            NetSim <b>Lite</b>
            <small>YOUR INTERACTIVE NETWORK LAB</small>
          </span>
        </a>
        <nav>
          <button
            className={tab === "lab" ? "active" : ""}
            onClick={() => setTab("lab")}
          >
            <Network size={16} />
            Topology lab
          </button>
          <button
            className={tab === "subnet" ? "active" : ""}
            onClick={() => setTab("subnet")}
          >
            <Calculator size={16} />
            Subnet calculator
          </button>
        </nav>
        <span
          className={`connection ${status === "Connected" ? "online" : ""}`}
        >
          <i />
          {status === "Connected"
            ? "Backend connected"
            : status === "Connecting"
              ? "Connecting…"
              : "Backend offline"}
        </span>
      </header>
      <div className="page-heading">
        <div>
          <div className="eyebrow">COMPUTER NETWORKS / VIRTUAL LAB</div>
          <h1>
            {tab === "lab"
              ? "A small network. Endless possibilities."
              : "Make sense of your address space."}
          </h1>
          <p>
            {tab === "lab"
              ? "Build a topology, trace a packet, and discover how networks find their way."
              : "Explore IPv4 networks, host ranges, and subnet boundaries."}
          </p>
        </div>
        <span className="badge">EDUCATIONAL SIMULATOR</span>
      </div>
      {tab === "lab" ? (
        <>
          <div className="workspace">
            <aside className="palette">
              <div className="panel-title">
                DEVICES <span>{nodes.length}</span>
              </div>
              <p className="hint">Click to add to your canvas</p>
              {(["pc", "router", "switch"] as const).map((kind) => {
                const Icon = icons[kind];
                return (
                  <button
                    className="palette-item"
                    key={kind}
                    onClick={() => addDevice(kind)}
                  >
                    <span>
                      <Icon size={23} />
                    </span>
                    <div>
                      <strong>
                        {kind === "pc"
                          ? "Computer"
                          : kind === "router"
                            ? "Router"
                            : "Switch"}
                      </strong>
                      <small>
                        {kind === "pc"
                          ? "End device"
                          : kind === "router"
                            ? "Route packets"
                            : "Connect devices"}
                      </small>
                    </div>
                    <Plus size={15} />
                  </button>
                );
              })}
              <div className="sidebar-divider" />
              <div className="panel-title">QUICK START</div>
              <button className="preset" onClick={preset}>
                <Network size={19} />
                <strong>Two paths, one destination</strong>
                <small>4 devices · 4 weighted links</small>
                <span>Load demo topology →</span>
              </button>
              <div className="tip">
                <Cable size={20} />
                <strong>Make a connection</strong>
                <p>
                  Drag from a device’s right port to another device’s left port.
                  Links work in both directions.
                </p>
              </div>
              <p className="scope">
                Logical graph simulation.
                <br />
                No real network traffic is sent.
              </p>
            </aside>
            <section className="canvas-section">
              <div className="canvas-toolbar">
                <span>
                  <i className="live-dot" />
                  TOPOLOGY CANVAS
                </span>
                <div>
                  <button onClick={save} title="Save topology">
                    <Save size={15} />
                    Save
                  </button>
                  <button onClick={load} title="Load topology">
                    <FolderOpen size={15} />
                    Load
                  </button>
                  <button onClick={preset} title="Reset to demo">
                    <RotateCcw size={15} />
                  </button>
                </div>
              </div>
              <div className="canvas">
                <ReactFlow
                  nodes={nodes.map((n) => ({
                    ...n,
                    data: { ...n.data, packet: n.id === packet },
                  }))}
                  edges={renderedEdges}
                  nodeTypes={nodeTypes}
                  edgeTypes={edgeTypes}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  onConnect={connect}
                  onNodeClick={(_, n) =>
                    setSelection({ type: "node", id: n.id })
                  }
                  onEdgeClick={(_, e) =>
                    setSelection({ type: "edge", id: e.id })
                  }
                  onPaneClick={() => setSelection(null)}
                  fitView
                  fitViewOptions={{ padding: 0.25 }}
                  minZoom={0.3}
                  colorMode="dark"
                  deleteKeyCode={null}
                >
                  <Background color="#29384b" gap={22} size={1} />
                  <Controls showInteractive={false} />
                  <MiniMap nodeColor="#27bda3" maskColor="rgba(10,17,28,.7)" />
                </ReactFlow>
                <div className="canvas-legend">
                  <span>
                    <i />
                    Active link
                  </span>
                  <span>
                    <i className="route" />
                    Selected route
                  </span>
                  <span>
                    <i className="failed" />
                    Disabled link
                  </span>
                </div>
              </div>
              <div className="canvas-footer">
                <span>
                  {nodes.length} devices <b>·</b>{" "}
                  {edges.filter((e) => e.data?.enabled).length} active links
                </span>
                <span>Drag to move · Scroll to zoom</span>
              </div>
            </section>
            <aside className="inspector">
              <div className="panel-title">
                ROUTE EXPLORER <Activity size={15} />
              </div>
              <label>
                Source device
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                >
                  <option value="">Select source</option>
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.data.label}
                    </option>
                  ))}
                </select>
              </label>
              <div className="route-dots">↓</div>
              <label>
                Destination device
                <select
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                >
                  <option value="">Select destination</option>
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.data.label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="primary"
                disabled={
                  busy ||
                  !nodes.some((n) => n.id === source) ||
                  !nodes.some((n) => n.id === destination)
                }
                onClick={() => run(true)}
              >
                <Play size={16} />
                {busy ? "Sending packet…" : "Send packet"}
              </button>
              <button
                className="secondary"
                disabled={
                  busy ||
                  !nodes.some((n) => n.id === source) ||
                  !nodes.some((n) => n.id === destination)
                }
                onClick={() => run(false)}
              >
                Calculate shortest path
              </button>
              {result && (
                <div
                  className={`route-result ${result.reachable ? "" : "unreachable"}`}
                >
                  <small>
                    {result.reachable ? "SHORTEST PATH" : "DELIVERY FAILED"}
                  </small>
                  <strong>
                    {result.reachable
                      ? result.path.map(name).join(" → ")
                      : "Destination unreachable"}
                  </strong>
                  {result.reachable && (
                    <span>
                      Total cost <b>{result.total_cost}</b> ·{" "}
                      {result.path.length - 1} hops
                    </span>
                  )}
                </div>
              )}
              <div className="sidebar-divider" />
              <div className="panel-title">PROPERTIES</div>
              {selectedNode ? (
                <>
                  <label>
                    Device name
                    <input
                      value={selectedNode.data.label}
                      onChange={(e) =>
                        setNodes((ns) =>
                          ns.map((n) =>
                            n.id === selectedNode.id
                              ? {
                                  ...n,
                                  data: { ...n.data, label: e.target.value },
                                }
                              : n,
                          ),
                        )
                      }
                    />
                  </label>
                  <label>
                    IPv4 address
                    <input
                      placeholder="192.168.1.10"
                      value={selectedNode.data.ip}
                      onChange={(e) =>
                        setNodes((ns) =>
                          ns.map((n) =>
                            n.id === selectedNode.id
                              ? {
                                  ...n,
                                  data: { ...n.data, ip: e.target.value },
                                }
                              : n,
                          ),
                        )
                      }
                    />
                  </label>
                  <button className="danger" onClick={remove}>
                    <Trash2 size={14} />
                    Delete device
                  </button>
                </>
              ) : selectedEdge ? (
                <>
                  <p className="hint">
                    {name(selectedEdge.source)} ↔ {name(selectedEdge.target)}
                  </p>
                  <label>
                    Link cost
                    <LinkCost
                      key={selectedEdge.id}
                      value={selectedEdge.data!.cost}
                      onInvalid={() =>
                        log(
                          "Link cost must be a finite non-negative number. Previous cost restored.",
                        )
                      }
                      onCommit={(value) =>
                        setEdges((es) =>
                          es.map((edge) =>
                            edge.id === selectedEdge.id
                              ? {
                                  ...edge,
                                  data: { ...edge.data!, cost: value },
                                }
                              : edge,
                          ),
                        )
                      }
                    />
                  </label>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={selectedEdge.data!.enabled}
                      onChange={(e) => {
                        setEdges((es) =>
                          es.map((edge) =>
                            edge.id === selectedEdge.id
                              ? {
                                  ...edge,
                                  data: {
                                    ...edge.data!,
                                    enabled: e.target.checked,
                                  },
                                }
                              : edge,
                          ),
                        );
                        log(
                          `Link ${e.target.checked ? "restored" : "disabled"}. Send a packet to recalculate.`,
                        );
                      }}
                    />
                    Link enabled
                  </label>
                  <button className="danger" onClick={remove}>
                    <Trash2 size={14} />
                    Delete link
                  </button>
                </>
              ) : (
                <div className="empty-properties">
                  <Cable size={25} />
                  <p>
                    Select a device or link
                    <br />
                    to edit its properties.
                  </p>
                </div>
              )}
            </aside>
          </div>
          <section className="events">
            <div className="events-title">
              <span>
                <Activity size={16} />
                EVENT LOG <b>{logs.length}</b>
              </span>
              <button onClick={() => setLogs([])}>Clear log</button>
            </div>
            <div className="log-lines" aria-live="polite">
              {logs.map((line, i) => (
                <div key={`${i}-${line}`}>
                  <span>›</span>
                  {line}
                </div>
              ))}
            </div>
          </section>
        </>
      ) : (
        <section className="subnet-page">
          <div className="subnet-form">
            <div className="calculator-icon">
              <Calculator size={30} />
            </div>
            <h2>IPv4 subnet calculator</h2>
            <p>
              Enter an IPv4 address and CIDR prefix. Host addresses are
              normalized to their network.
            </p>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const token = ++subnetGeneration.current;
                setSubnetBusy(true);
                setSubnetError("");
                setSubnet(null);
                try {
                  const data = await api<Record<string, string | number>>(
                    "subnet",
                    { cidr },
                  );
                  if (token === subnetGeneration.current) setSubnet(data);
                } catch (error) {
                  if (token === subnetGeneration.current)
                    setSubnetError((error as Error).message);
                } finally {
                  if (token === subnetGeneration.current) setSubnetBusy(false);
                }
              }}
            >
              <label>
                IPv4 address / prefix
                <input
                  value={cidr}
                  onChange={(e) => {
                    subnetGeneration.current++;
                    setSubnetBusy(false);
                    setSubnet(null);
                    setSubnetError("");
                    setCidr(e.target.value);
                  }}
                  placeholder="192.168.1.0/26"
                  required
                />
              </label>
              <button className="primary" disabled={subnetBusy}>
                Calculate subnet →
              </button>
            </form>
            {subnetError && (
              <p role="alert" className="error">
                {subnetError}
              </p>
            )}
            <small>
              /31 includes both point-to-point addresses; /32 contains one host.
            </small>
          </div>
          <div className="subnet-results">
            <div className="panel-title">NETWORK BREAKDOWN</div>
            {subnet ? (
              <div className="subnet-grid">
                {Object.entries(subnet).map(([key, value]) => (
                  <div key={key}>
                    <small>{key.replaceAll("_", " ")}</small>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <div className="subnet-placeholder">
                <Network size={50} />
                <h3>Your network, decoded.</h3>
                <p>
                  Calculate a subnet to see its mask, broadcast address, and
                  usable host range.
                </p>
              </div>
            )}
          </div>
        </section>
      )}
      <footer>
        <span>
          NetSim Lite <b> / </b> Learn by connecting.
        </span>
        <span>
          Dijkstra routing · IPv4 subnetting · Logical packet simulation
        </span>
      </footer>
    </div>
  );
}
