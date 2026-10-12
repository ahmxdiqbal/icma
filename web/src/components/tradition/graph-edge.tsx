"use client";

import type { Edge, EdgeProps } from "@xyflow/react";
import { memo, type ReactElement } from "react";
import { roundedPolylinePath } from "@/lib/edge-path";
import type { Point } from "@/lib/layout";

export type BundleEdgeData = { points: Point[]; width: number; diveOnly: boolean };
export type BundleFlowEdge = Edge<BundleEdgeData, "bundle">;

const CORNER_RADIUS = 14;

/** Draws ELK's routed polyline; React Flow's handle coordinates are not used. */
function BundleEdgeViewImpl({ data }: EdgeProps<BundleFlowEdge>): ReactElement | null {
  if (data === undefined) return null;
  return (
    <path
      d={roundedPolylinePath(data.points, CORNER_RADIUS)}
      className={data.diveOnly ? "bundle-edge is-dive" : "bundle-edge"}
      style={{ strokeWidth: data.width }}
    />
  );
}

export const BundleEdgeView = memo(BundleEdgeViewImpl);
