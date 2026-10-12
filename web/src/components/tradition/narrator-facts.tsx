import type { ReactElement, ReactNode } from "react";
import { Ar } from "@/components/arabic";
import type { Narrator } from "@/lib/schema";

function deathText(n: Narrator): ReactNode {
  if (n.death_ah !== null) return `${n.death_ah} AH`;
  if (n.death_ah_raw !== null) return `Reported as ${n.death_ah_raw} AH`;
  return <span className="text-ink-faint">Not recorded</span>;
}

function caveats(n: Narrator): string[] {
  return [
    ...(n.has_tadlis ? ["Tadlis reported (may conceal his informant)"] : []),
    ...(n.has_ikhtilat ? ["Ikhtilat reported (memory confused late in life)"] : []),
  ];
}

function sahihayn(n: Narrator): string {
  const books = [...(n.in_bukhari ? ["al-Bukhari"] : []), ...(n.in_muslim ? ["Muslim"] : [])];
  return books.length === 0 ? "Neither" : books.join(" and ");
}

function Fact({ term, children }: { term: string; children: ReactNode }): ReactElement {
  return (
    <div className="grid grid-cols-[7.5rem_1fr] gap-x-3 py-1.5">
      <dt className="text-ink-muted">{term}</dt>
      <dd className="min-w-0">{children}</dd>
    </div>
  );
}

export function NarratorFacts({ narrator }: { narrator: Narrator }): ReactElement {
  const flags = caveats(narrator);
  return (
    <dl className="divide-y divide-rule text-[15px]">
      <Fact term="Died">{deathText(narrator)}</Fact>
      <Fact term="Grade">{narrator.grade_ar === null ? "Not graded" : <Ar className="text-[17px]">{narrator.grade_ar}</Ar>}</Fact>
      <Fact term="Tabaqa">{narrator.tabaqa}</Fact>
      <Fact term="Residence">
        {narrator.residence_ar === null ? <span className="text-ink-faint">Not recorded</span> : <Ar className="text-[16px]">{narrator.residence_ar}</Ar>}
      </Fact>
      <Fact term="Caveats">
        {flags.length === 0 ? (
          <span className="text-ink-faint">None recorded</span>
        ) : (
          <ul className="space-y-0.5 text-ochre">
            {flags.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        )}
      </Fact>
      <Fact term="In the Sahihs of">{sahihayn(narrator)}</Fact>
    </dl>
  );
}
