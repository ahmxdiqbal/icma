"use client";

import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { memo, type ReactElement } from "react";
import { Ar } from "@/components/arabic";
import type { GraphNode } from "@/lib/bundle-graph";
import { formatDeath } from "@/lib/labels";
import { useExplorer } from "./explorer-context";

export type BundleNodeData = { node: GraphNode; isSelected: boolean };
export type BundleFlowNode = Node<BundleNodeData, "bundle">;

const BASE = "flex h-full w-full cursor-pointer flex-col items-center justify-center gap-0.5 rounded-md px-2 text-center";

const BORDER: Record<GraphNode["emphasis"], string> = {
  convergence: "border-2 border-lapis bg-lapis-soft",
  candidate: "border-[1.5px] border-lapis bg-paper-raised",
  spider: "border-[1.5px] border-ochre bg-ochre-soft",
  none: "border border-rule bg-paper-raised hover:border-ink-faint",
};

export function nodeFrameClass(node: GraphNode, isSelected: boolean): string {
  const frame =
    node.kind === "prophet"
      ? "border-2 border-ink bg-paper-raised"
      : node.kind === "gap"
        ? "border border-dashed border-ink-faint bg-paper-sunk"
        : BORDER[node.emphasis];
  const collector = node.books.length > 0 ? "border-b-[4px] border-b-ink rounded-b-sm" : "";
  const selected = isSelected ? "ring-[3px] ring-lapis ring-offset-2 ring-offset-paper-sunk" : "";
  return `${BASE} ${frame} ${collector} ${selected}`;
}

function Death({ deathAh }: { deathAh: number | null }): ReactElement | null {
  const text = formatDeath(deathAh);
  return text === null ? null : <span className="text-[11.5px] leading-none text-ink-muted tabular-nums">{text}</span>;
}

function CollectorFace({ node }: { node: GraphNode }): ReactElement {
  const [title, ...more] = node.books;
  return (
    <>
      <Ar className="line-clamp-2 text-[14px] font-bold leading-[1.3]">{title}</Ar>
      <span className="flex max-w-full items-baseline gap-1.5">
        <Ar className="truncate text-[13px] leading-tight text-ink-muted">{node.label}</Ar>
        {more.length > 0 ? <span className="text-[11px] text-ink-muted">+{more.length}</span> : null}
      </span>
      <Death deathAh={node.deathAh} />
    </>
  );
}

function NodeFace({ node }: { node: GraphNode }): ReactElement {
  if (node.books.length > 0) return <CollectorFace node={node} />;
  if (node.labelLang === "en") return <span className="text-[13px] italic text-ink-muted">{node.label}</span>;
  return (
    <>
      <Ar className="line-clamp-2 text-[15px] leading-[1.3]">{node.label}</Ar>
      <Death deathAh={node.deathAh} />
    </>
  );
}

function BundleNodeViewImpl({ data }: NodeProps<BundleFlowNode>): ReactElement {
  const { actions } = useExplorer();
  const { node, isSelected } = data;
  return (
    <>
      <Handle type="target" position={Position.Top} className="bundle-handle" isConnectable={false} />
      <button
        type="button"
        data-node-key={node.key}
        aria-pressed={isSelected}
        title={[node.label, ...node.books].join(" / ")}
        onClick={() => actions.selectNode(node.key)}
        className={nodeFrameClass(node, isSelected)}
      >
        <NodeFace node={node} />
      </button>
      <Handle type="source" position={Position.Bottom} className="bundle-handle" isConnectable={false} />
    </>
  );
}

export const BundleNodeView = memo(BundleNodeViewImpl);
