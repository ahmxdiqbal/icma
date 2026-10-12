/** SVG path through a polyline with rounded corners, so routed edges read as drawn lines. */
import type { Point } from "./layout";

function fmt(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

function toward(from: Point, to: Point, distance: number): Point {
  const length = Math.hypot(to.x - from.x, to.y - from.y);
  if (length === 0) return from;
  const t = Math.min(1, distance / length);
  return { x: from.x + (to.x - from.x) * t, y: from.y + (to.y - from.y) * t };
}

function halfSegment(a: Point, b: Point): number {
  return Math.hypot(b.x - a.x, b.y - a.y) / 2;
}

/** Each interior corner becomes a quadratic curve of at most `radius`. */
export function roundedPolylinePath(points: readonly Point[], radius: number): string {
  const [first, ...rest] = points;
  if (first === undefined) return "";
  const parts = [`M${fmt(first.x)},${fmt(first.y)}`];
  let previous = first;
  rest.forEach((corner, i) => {
    const next = rest[i + 1];
    if (next === undefined) {
      parts.push(`L${fmt(corner.x)},${fmt(corner.y)}`);
      return;
    }
    const r = Math.min(radius, halfSegment(previous, corner), halfSegment(corner, next));
    const enter = toward(corner, previous, r);
    const exit = toward(corner, next, r);
    parts.push(`L${fmt(enter.x)},${fmt(enter.y)}`, `Q${fmt(corner.x)},${fmt(corner.y)} ${fmt(exit.x)},${fmt(exit.y)}`);
    previous = corner;
  });
  return parts.join(" ");
}
