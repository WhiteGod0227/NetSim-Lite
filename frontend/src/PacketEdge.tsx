import { BaseEdge, getBezierPath, type EdgeProps } from "@xyflow/react";

export default function PacketEdge(props: EdgeProps) {
  const [path, labelX, labelY] = getBezierPath(props);
  const reverse = Boolean(props.data?.reverse);
  return (
    <>
      <BaseEdge
        id={props.id}
        path={path}
        label={props.label}
        labelX={labelX}
        labelY={labelY}
        labelStyle={props.labelStyle}
        labelBgStyle={props.labelBgStyle}
        labelBgPadding={props.labelBgPadding}
        style={props.style}
      />
      {props.animated && (
        <circle
          r="5"
          fill="#92ffdc"
          style={{
            filter: "drop-shadow(0 0 6px #36ffbd)",
            pointerEvents: "none",
          }}
        >
          <animateMotion
            key={`${props.id}-${reverse}`}
            dur="0.8s"
            repeatCount="indefinite"
            path={path}
            keyPoints={reverse ? "1;0" : "0;1"}
            keyTimes="0;1"
            calcMode="linear"
          />
        </circle>
      )}
    </>
  );
}
