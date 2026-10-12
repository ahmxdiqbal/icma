"use client";

import { useMemo, type ReactElement } from "react";
import type { Hadith } from "@/lib/schema";
import { segmentHadithText, type SegmentKind, type TextRun, type TextSegment } from "@/lib/text-segments";
import { useExplorer } from "./explorer-context";

const SEGMENT_CLASS: Record<SegmentKind, string> = {
  isnad: "text-ink-muted text-[19px]",
  matn: "text-ink text-[21px] border-s-2 border-ink-faint ps-4 my-2",
  trailing: "text-ink-muted text-[19px]",
  unsplit: "text-ink text-[20px]",
};

function Mention({ run }: { run: TextRun }): ReactElement {
  const { actions, index } = useExplorer();
  const narratorId = run.mention?.narratorId ?? null;
  const key = narratorId === null ? null : `n:${narratorId}`;
  if (key === null || !index.nodes.has(key)) {
    const why = narratorId === null ? "Transmitter not identified" : "Transmitter not in the bundle";
    return (
      <span title={why} className="underline decoration-ink-faint decoration-dotted underline-offset-[7px]">
        {run.text}
      </span>
    );
  }
  return (
    <button
      type="button"
      onClick={() => actions.selectNode(key, true)}
      className="cursor-pointer underline decoration-lapis/50 decoration-1 underline-offset-[7px] hover:text-lapis hover:decoration-lapis"
    >
      {run.text}
    </button>
  );
}

function Segment({ segment }: { segment: TextSegment }): ReactElement {
  return (
    <p data-segment={segment.kind} className={SEGMENT_CLASS[segment.kind]}>
      {segment.runs.map((run) => (run.mention === null ? <span key={run.start}>{run.text}</span> : <Mention key={run.start} run={run} />))}
    </p>
  );
}

export function VariantText({ hadith }: { hadith: Hadith }): ReactElement {
  const segments = useMemo(() => segmentHadithText(hadith.text_ar, hadith.matn_span, hadith.mentions), [hadith]);
  return (
    <div dir="rtl" lang="ar" className="font-arabic leading-[2.1]">
      {segments.map((segment) => (
        <Segment key={segment.start} segment={segment} />
      ))}
    </div>
  );
}
