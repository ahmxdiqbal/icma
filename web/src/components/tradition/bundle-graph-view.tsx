"use client";

import {
  Background,
  BackgroundVariant,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type EdgeTypes,
  type FitViewOptions,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useEffect, useMemo, type ReactElement } from "react";
import { openingKeys, type BundleGraph } from "@/lib/bundle-graph";
import type { Highlight } from "@/lib/highlight";
import type { GraphLayout } from "@/lib/layout";
import type { FocusRequest } from "./explorer-state";
import { toFlowEdges, toFlowNodes } from "./flow-elements";
import { BundleEdgeView } from "./graph-edge";
import { BundleNodeView } from "./graph-node";

const NODE_TYPES: NodeTypes = { bundle: BundleNodeView };
const EDGE_TYPES: EdgeTypes = { bundle: BundleEdgeView };

interface BundleGraphViewProps {
  graph: BundleGraph;
  layout: GraphLayout;
  selectedKey: string | null;
  highlight: Highlight | null;
  focus: FocusRequest | null;
  onPaneClick: () => void;
}

/** Pans to the requested nodes once the container has been laid out (it may just have been shown). */
function FocusOnRequest({ request }: { request: FocusRequest | null }): null {
  const { fitView } = useReactFlow();
  useEffect(() => {
    if (request === null) return;
    let frame = requestAnimationFrame(() => {
      frame = requestAnimationFrame(() => {
        void fitView({ nodes: request.keys.map((id) => ({ id })), duration: 450, padding: 0.35, maxZoom: 1.1 });
      });
    });
    return () => cancelAnimationFrame(frame);
  }, [request, fitView]);
  return null;
}

/** The opening view frames the trunk of the bundle, where chains converge, at a readable zoom. */
function openingView(graph: BundleGraph): FitViewOptions {
  return { nodes: openingKeys(graph).map((id) => ({ id })), padding: 0.2, maxZoom: 1, minZoom: 0.35 };
}

export function BundleGraphView(props: BundleGraphViewProps): ReactElement {
  const { graph, layout, selectedKey, highlight, focus, onPaneClick } = props;
  const nodes = useMemo(() => toFlowNodes(graph, layout, selectedKey, highlight), [graph, layout, selectedKey, highlight]);
  const edges = useMemo(() => toFlowEdges(graph, layout, highlight), [graph, layout, highlight]);
  const opening = useMemo(() => openingView(graph), [graph]);
  return (
    <ReactFlowProvider>
      <ReactFlow
        className="bundle-flow"
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        onPaneClick={onPaneClick}
        nodesDraggable={false}
        nodesConnectable={false}
        nodesFocusable={false}
        edgesFocusable={false}
        elementsSelectable={false}
        fitView
        fitViewOptions={opening}
        minZoom={0.04}
        maxZoom={2}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1.2} />
        <Controls showInteractive={false} position="top-left" />
        <FocusOnRequest request={focus} />
      </ReactFlow>
    </ReactFlowProvider>
  );
}
