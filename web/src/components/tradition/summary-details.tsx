"use client";

import type { ReactElement } from "react";
import { Ar, MixedText } from "@/components/arabic";
import { KeyLabel, KeySequence } from "@/components/key-label";
import { chainNodeKeys } from "@/lib/chain-path";
import { plural } from "@/lib/format";
import { formatDeath } from "@/lib/labels";
import type { Correction, Dive, TraditionPackage, UpperPath } from "@/lib/schema";
import { bookOfChain, lookup, narratorIdOfKey, type TraditionIndex } from "@/lib/tradition-index";
import { useExplorer } from "./explorer-context";

const UNREVIEWED = "(unreviewed)";

function deathOfKey(key: string, index: TraditionIndex): string | null {
  const id = narratorIdOfKey(key);
  return id === null ? null : formatDeath(lookup(index.narrators, id, "narrator").death_ah);
}

export function CandidateList({ pkg }: { pkg: TraditionPackage }): ReactElement {
  const { actions, index } = useExplorer();
  return (
    <ul className="flex flex-wrap gap-2">
      {pkg.bundle.cl_candidates.map((key) => (
        <li key={key}>
          <button type="button" onClick={() => actions.selectNode(key, true)} className="rounded border border-lapis/60 px-2.5 py-1 hover:bg-lapis-soft">
            <KeyLabel nodeKey={key} index={index} />
            <span className="ms-2 text-[13px] text-ink-muted tabular-nums">
              {[deathOfKey(key, index), plural(lookup(index.nodes, key, "node").chain_ids.length, "chain")].filter((s) => s !== null).join(", ")}
              {key === pkg.bundle.suggested_cl ? ", convergence point" : ""}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function DiveItem({ dive }: { dive: Dive }): ReactElement {
  const { actions, index } = useExplorer();
  const book = bookOfChain(index, lookup(index.chains, dive.chain_id, "chain"));
  return (
    <li>
      <button type="button" onClick={() => actions.selectChain(dive.chain_id, true)} className="text-left hover:text-lapis">
        <span className="tabular-nums">Chain {dive.chain_id}</span> in <Ar className="text-[16px]">{book.title_ar}</Ar> leaves at{" "}
        <KeyLabel nodeKey={dive.departs_from} index={index} />
        {dive.rejoins_at === null ? (
          " and does not rejoin below the convergence point"
        ) : (
          <>
            {" "}and rejoins at <KeyLabel nodeKey={dive.rejoins_at} index={index} />
          </>
        )}
      </button>
    </li>
  );
}

export function DiveList({ dives }: { dives: readonly Dive[] }): ReactElement {
  if (dives.length === 0) return <p className="text-ink-muted">No chain bypasses the convergence point.</p>;
  return (
    <ul className="space-y-1.5">
      {dives.map((d) => (
        <DiveItem key={d.chain_id} dive={d} />
      ))}
    </ul>
  );
}

function PathRow({ path, convergenceKey }: { path: UpperPath; convergenceKey: string }): ReactElement {
  const { index } = useExplorer();
  return (
    <li className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
      <KeySequence keys={[...path.labels, convergenceKey]} index={index} muteLast />
      <span className="text-[13.5px] text-ink-muted tabular-nums">({plural(path.chain_ids.length, "chain")})</span>
    </li>
  );
}

export function UpperPathList({ pkg }: { pkg: TraditionPackage }): ReactElement {
  const cl = pkg.bundle.suggested_cl;
  if (cl === null || pkg.bundle.upper_paths.length === 0) return <p className="text-ink-muted">No paths above a convergence point.</p>;
  return (
    <ul className="space-y-1.5">
      {pkg.bundle.upper_paths.map((p) => (
        <PathRow key={p.labels.join(">")} path={p} convergenceKey={cl} />
      ))}
    </ul>
  );
}

export function WarningList({ pkg }: { pkg: TraditionPackage }): ReactElement {
  if (pkg.bundle.warnings.length === 0) return <p className="text-ink-muted">The pipeline reported no warnings for this bundle.</p>;
  return (
    <ul className="space-y-1.5">
      {pkg.bundle.warnings.map((w, i) => (
        <li key={`${w.code}-${i}`}>
          <span className="font-medium">{w.code.replaceAll("_", " ")}</span>: {w.message}{" "}
          <span className="text-ink-muted tabular-nums">(chains {w.chain_ids.join(", ")})</span>
        </li>
      ))}
    </ul>
  );
}

function AuthorLine({ correction }: { correction: Correction }): ReactElement {
  const unreviewed = correction.author.endsWith(UNREVIEWED);
  const author = unreviewed ? correction.author.slice(0, -UNREVIEWED.length).trim() : correction.author;
  return (
    <p className="text-[14px] text-ink-muted">
      {unreviewed ? (
        <span className="me-2 rounded bg-ochre-soft px-1.5 py-0.5 font-bold text-ochre">Unreviewed: proposed by a model</span>
      ) : null}
      By {author}, {correction.date}
    </p>
  );
}

function OpLine({ correction }: { correction: Correction }): ReactElement {
  const { index } = useExplorer();
  const { chain_id: chainId, from_narrator_id: from, to_narrator_id: to } = correction;
  if (correction.op === "replace" && from !== null && to !== null) {
    return (
      <p className="font-medium">
        Chain {chainId}: replaced <KeyLabel nodeKey={`n:${from}`} index={index} /> with{" "}
        <KeyLabel nodeKey={`n:${to}`} index={index} />
      </p>
    );
  }
  const chain = index.chains.get(chainId);
  if (correction.op === "set_links" && chain !== undefined) {
    // The package does not carry the correction's links, but chains[] already holds the result.
    return (
      <p className="flex flex-wrap items-baseline gap-x-2 font-medium">
        <span>Chain {chainId}: links set to</span>
        <KeySequence keys={chainNodeKeys(chain, index.propheticChainIds.has(chainId))} index={index} />
      </p>
    );
  }
  const verb = correction.op === "exclude" ? "excluded from the bundle" : "links set";
  return <p className="font-medium">Chain {chainId}: {verb}</p>;
}

export function CorrectionList({ corrections }: { corrections: readonly Correction[] }): ReactElement {
  if (corrections.length === 0) return <p className="text-ink-muted">No manual corrections were applied.</p>;
  return (
    <ul className="space-y-4">
      {corrections.map((c, i) => (
        <li key={`${c.chain_id}-${i}`} className="max-w-[80ch] space-y-1.5">
          <OpLine correction={c} />
          <AuthorLine correction={c} />
          <p><span className="text-ink-muted">Reason: </span><MixedText text={c.reason} /></p>
          <p><span className="text-ink-muted">Evidence: </span><MixedText text={c.evidence} /></p>
        </li>
      ))}
    </ul>
  );
}
