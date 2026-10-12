"use client";

import { useCallback, useEffect, useMemo, useReducer, type ReactElement } from "react";
import { chainNodeKeys, collectorKeyOf } from "@/lib/chain-path";
import { highlightFor } from "@/lib/highlight";
import { buildIndex, lookup, type TraditionIndex } from "@/lib/tradition-index";
import { orderedVariants } from "@/lib/variants";
import type { TraditionView } from "@/lib/view";
import { BundleGraphView } from "./bundle-graph-view";
import { ExplorerContext, type ExplorerActions } from "./explorer-context";
import { explorerReducer, initialExplorerState, type ExplorerAction, type Tab } from "./explorer-state";
import { GraphLegend } from "./graph-legend";
import { NodePanel } from "./node-panel";
import { SummaryStrip } from "./summary-strip";
import { VariantList } from "./variant-list";

function chainAction(chainId: number, focus: boolean, index: TraditionIndex): ExplorerAction {
  const chain = lookup(index.chains, chainId, "chain");
  return {
    type: "selectChain",
    chainId,
    pathKeys: chainNodeKeys(chain, index.propheticChainIds.has(chainId)),
    fallbackNodeKey: collectorKeyOf(chain),
    focus,
  };
}

function useEscapeToClear(clear: () => void): void {
  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") clear();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [clear]);
}

function TabButton({ tab, current, label, onSelect }: { tab: Tab; current: Tab; label: string; onSelect: (t: Tab) => void }): ReactElement {
  const active = tab === current;
  return (
    <button
      type="button"
      role="tab"
      id={`tab-${tab}`}
      aria-selected={active}
      aria-controls={`panel-${tab}`}
      onClick={() => onSelect(tab)}
      className={`-mb-px border-b-2 px-1 pb-2 text-[17px] ${active ? "border-ink font-bold text-ink" : "border-transparent text-ink-muted hover:text-ink"}`}
    >
      {label}
    </button>
  );
}

export function TraditionExplorer({ view }: { view: TraditionView }): ReactElement {
  const { pkg, graph, layout } = view;
  const index = useMemo(() => buildIndex(pkg), [pkg]);
  const variants = useMemo(() => orderedVariants(pkg, index), [pkg, index]);
  const graphNodes = useMemo(() => new Map(graph.nodes.map((n) => [n.key, n])), [graph]);
  const [state, dispatch] = useReducer(explorerReducer, initialExplorerState);
  const highlight = useMemo(() => highlightFor(state.nodeKey, state.chainId, index), [state.nodeKey, state.chainId, index]);
  const clear = useCallback((): void => dispatch({ type: "clear" }), []);
  const actions = useMemo<ExplorerActions>(
    () => ({
      selectNode: (key, focus = false) => dispatch({ type: "selectNode", key, focus }),
      selectChain: (chainId, focus = false) => dispatch(chainAction(chainId, focus, index)),
      clear,
    }),
    [index, clear],
  );
  useEscapeToClear(clear);
  const selected = state.nodeKey === null ? null : (graphNodes.get(state.nodeKey) ?? null);
  const setTab = (tab: Tab): void => dispatch({ type: "tab", tab });

  return (
    <ExplorerContext value={{ actions, index }}>
      <SummaryStrip pkg={pkg} />
      <div role="tablist" aria-label="Views" className="mt-6 flex gap-6 border-b border-rule">
        <TabButton tab="bundle" current={state.tab} label="Bundle graph" onSelect={setTab} />
        <TabButton tab="texts" current={state.tab} label={`Texts (${pkg.hadiths.length})`} onSelect={setTab} />
      </div>
      <section id="panel-bundle" role="tabpanel" aria-labelledby="tab-bundle" hidden={state.tab !== "bundle"} className="pt-3">
        <GraphLegend />
        <p className="mt-1.5 text-[14px] text-ink-faint">Scroll or pinch to zoom, drag to pan. Select a transmitter to see the chains through it.</p>
        <div className="relative mt-3 h-[72dvh] min-h-[420px] overflow-hidden rounded-md border border-rule" data-testid="bundle-graph">
          <BundleGraphView graph={graph} layout={layout} selectedKey={state.nodeKey} highlight={highlight} focus={state.focus} onPaneClick={clear} />
          {selected === null ? null : <NodePanel key={selected.key} node={selected} selectedChainId={state.chainId} onClose={clear} />}
        </div>
      </section>
      <section id="panel-texts" role="tabpanel" aria-labelledby="tab-texts" hidden={state.tab !== "texts"} className="pt-6">
        <VariantList variants={variants} />
      </section>
    </ExplorerContext>
  );
}
