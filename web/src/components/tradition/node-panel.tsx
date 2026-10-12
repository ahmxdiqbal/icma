"use client";

import type { ReactElement } from "react";
import { Ar } from "@/components/arabic";
import type { GraphNode } from "@/lib/bundle-graph";
import { GAP_DESCRIPTIONS, ROLE_TEXT } from "@/lib/labels";
import { lookup } from "@/lib/tradition-index";
import { ChainList } from "./chain-list";
import { useExplorer } from "./explorer-context";
import { NarratorFacts } from "./narrator-facts";
import { NodeMetrics } from "./node-metrics";

interface NodePanelProps {
  node: GraphNode;
  selectedChainId: number | null;
  onClose: () => void;
}

function roleOf(node: GraphNode): string {
  if (node.kind === "prophet") return "The Prophet";
  if (node.kind === "gap") return "Gap in the chain";
  const role = node.emphasis === "none" ? "Transmitter" : ROLE_TEXT[node.emphasis].name;
  if (node.books.length === 0) return role;
  return node.emphasis === "none" ? "Collector" : `${role}, collector`;
}

function RoleNote({ node }: { node: GraphNode }): ReactElement | null {
  const note = node.kind === "gap" && node.gap !== null ? GAP_DESCRIPTIONS[node.gap] : node.emphasis === "none" ? null : ROLE_TEXT[node.emphasis].note;
  return note === null ? null : <p className="text-[14px] leading-snug text-ink-muted">{note}</p>;
}

function Identity({ node }: { node: GraphNode }): ReactElement {
  const { index } = useExplorer();
  const bundleNode = lookup(index.nodes, node.key, "node");
  if (bundleNode.kind !== "narrator") {
    return <h2 className={node.labelLang === "ar" ? "font-arabic text-[26px]" : "text-[22px] font-bold italic"}>{node.label}</h2>;
  }
  const narrator = lookup(index.narrators, bundleNode.narrator_id, "narrator");
  return (
    <div dir="rtl" lang="ar" className="space-y-1 font-arabic">
      <h2 className="text-[26px] font-bold leading-snug">{narrator.display_name_ar}</h2>
      <p className="text-[17px] leading-relaxed text-ink-muted">{narrator.name_ar}</p>
    </div>
  );
}

function Books({ titles }: { titles: readonly string[] }): ReactElement | null {
  if (titles.length === 0) return null;
  return (
    <section>
      <h3 className="mb-1 text-[15px] font-bold">Collector in</h3>
      <ul className="space-y-0.5">
        {titles.map((t) => (
          <li key={t}>
            <Ar className="text-[17px]">{t}</Ar>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function NodePanel({ node, selectedChainId, onClose }: NodePanelProps): ReactElement {
  const { index } = useExplorer();
  const bundleNode = lookup(index.nodes, node.key, "node");
  return (
    <aside
      aria-label="Selected node"
      className="fixed inset-x-0 bottom-0 z-20 max-h-[62dvh] overflow-y-auto border-t border-rule bg-paper-raised shadow-[0_-8px_24px_rgb(0_0_0/0.12)] md:absolute md:inset-y-0 md:left-auto md:right-0 md:max-h-none md:w-[400px] md:border-l md:border-t-0 md:shadow-none"
    >
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-rule bg-paper-raised px-4 py-2.5">
        <span className="text-[14px] font-medium text-ink-muted">{roleOf(node)}</span>
        <button type="button" onClick={onClose} className="rounded px-2 py-0.5 text-[14px] text-ink-muted hover:bg-paper-sunk hover:text-ink">
          Close
        </button>
      </div>
      <div className="space-y-5 px-4 py-4">
        <Identity node={node} />
        <RoleNote node={node} />
        {bundleNode.kind === "narrator" ? <NarratorFacts narrator={lookup(index.narrators, bundleNode.narrator_id, "narrator")} /> : null}
        <Books titles={node.books} />
        <NodeMetrics node={bundleNode} />
        <ChainList chainIds={bundleNode.chain_ids} selectedChainId={selectedChainId} />
      </div>
    </aside>
  );
}
