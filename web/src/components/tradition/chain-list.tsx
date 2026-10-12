"use client";

import type { ReactElement } from "react";
import { Ar } from "@/components/arabic";
import { KeyLabel } from "@/components/key-label";
import { chainNodeKeys } from "@/lib/chain-path";
import type { Chain } from "@/lib/schema";
import { bookOfChain, lookup, type TraditionIndex } from "@/lib/tradition-index";
import { useExplorer } from "./explorer-context";

function chainsByCollectorDeath(chainIds: readonly number[], index: TraditionIndex): Chain[] {
  const chains = chainIds.map((id) => lookup(index.chains, id, "chain"));
  const death = (c: Chain): number => bookOfChain(index, c).author_death_ah ?? Number.MAX_SAFE_INTEGER;
  return chains.sort((a, b) => death(a) - death(b) || a.id - b.id);
}

function ChainPath({ chain }: { chain: Chain }): ReactElement {
  const { actions, index } = useExplorer();
  const keys = chainNodeKeys(chain, index.propheticChainIds.has(chain.id));
  return (
    <ol className="mt-2 space-y-0.5 border-l-2 border-lapis pl-3 text-[15px]">
      {keys.map((key) => (
        <li key={key}>
          <button type="button" onClick={() => actions.selectNode(key, true)} className="text-left hover:text-lapis hover:underline">
            <KeyLabel nodeKey={key} index={index} />
          </button>
        </li>
      ))}
    </ol>
  );
}

function ChainItem({ chain, selected }: { chain: Chain; selected: boolean }): ReactElement {
  const { actions, index } = useExplorer();
  const book = bookOfChain(index, chain);
  const hadith = lookup(index.hadiths, chain.hadith_id, "hadith");
  return (
    <li className={`rounded-md px-2.5 py-2 ${selected ? "bg-lapis-soft" : "hover:bg-paper-sunk"}`}>
      <button type="button" aria-pressed={selected} onClick={() => actions.selectChain(chain.id)} className="block w-full text-left">
        <span className="flex flex-row-reverse flex-wrap items-baseline justify-between gap-x-3">
          <Ar className="text-[16px] font-bold">{book.title_ar}</Ar>
          <span className="text-[13px] text-ink-muted tabular-nums">No. {hadith.number_in_book}, chain {chain.id}</span>
        </span>
        {chain.grade_ar === "" ? null : <Ar as="span" className="mt-0.5 block text-[14px] text-ink-muted">{chain.grade_ar}</Ar>}
      </button>
      {selected ? <ChainPath chain={chain} /> : null}
    </li>
  );
}

export function ChainList({ chainIds, selectedChainId }: { chainIds: readonly number[]; selectedChainId: number | null }): ReactElement {
  const { index } = useExplorer();
  const chains = chainsByCollectorDeath(chainIds, index);
  return (
    <section aria-labelledby="chains-heading">
      <h3 id="chains-heading" className="mb-1 text-[15px] font-bold">
        Chains through this node ({chains.length})
      </h3>
      <p className="mb-2 text-[13.5px] text-ink-muted">Ordered by the collector&rsquo;s death. Select one to trace it in the graph.</p>
      <ul className="space-y-1">
        {chains.map((chain) => (
          <ChainItem key={chain.id} chain={chain} selected={chain.id === selectedChainId} />
        ))}
      </ul>
    </section>
  );
}
