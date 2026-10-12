import type { ReactElement } from "react";
import { labelOfKey } from "@/lib/labels";
import type { TraditionIndex } from "@/lib/tradition-index";
import { Ar } from "./arabic";

/** A node key (or grouped path label) as text: Arabic names, English gap labels. */
export function KeyLabel({ nodeKey, index }: { nodeKey: string; index: TraditionIndex }): ReactElement {
  const label = labelOfKey(nodeKey, index);
  return label.lang === "ar" ? <Ar>{label.text}</Ar> : <span className="italic">{label.text}</span>;
}

interface KeySequenceProps {
  keys: readonly string[];
  index: TraditionIndex;
  /** Render the final key muted, e.g. the convergence point that ends an upper path. */
  muteLast?: boolean;
}

/** Keys in transmission order, teacher to student, joined by arrows. */
export function KeySequence({ keys, index, muteLast = false }: KeySequenceProps): ReactElement {
  return (
    <>
      {keys.map((key, i) => (
        <span key={`${key}-${i}`} className={`inline-flex items-baseline gap-2 ${muteLast && i === keys.length - 1 ? "text-ink-muted" : ""}`}>
          {i > 0 ? <span aria-hidden className="text-ink-faint">&rarr;</span> : null}
          <KeyLabel nodeKey={key} index={index} />
        </span>
      ))}
    </>
  );
}
