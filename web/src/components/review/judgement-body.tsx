import type { ReactElement, ReactNode } from "react";
import { Ar, MixedText } from "@/components/arabic";
import { OUTPUT_SCHEMAS, type JudgementKind, type OutputOf } from "@/lib/review/schemas";

export type NameOf = (key: string) => { text: string; lang: "ar" | "en" };

function Name({ nodeKey, nameOf }: { nodeKey: string; nameOf: NameOf }): ReactElement {
  const name = nameOf(nodeKey);
  return name.lang === "ar" ? <Ar className="text-[1.15em]">{name.text}</Ar> : <span className="italic">{name.text}</span>;
}

function Tag({ children }: { children: ReactNode }): ReactElement {
  return <span className="rounded bg-paper-sunk px-1.5 py-0.5 text-[13px] font-medium uppercase tracking-wide text-ink-muted">{children}</span>;
}

function Prose({ text }: { text: string }): ReactElement | null {
  return text.trim() === "" ? null : (
    <p className="mt-2 max-w-[75ch] whitespace-pre-line text-[16px] leading-relaxed">
      <MixedText text={text} />
    </p>
  );
}

function Head({ children }: { children: ReactNode }): ReactElement {
  return <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">{children}</div>;
}

type Renderers = { [K in JudgementKind]: (o: OutputOf<K>, nameOf: NameOf) => ReactElement };

const RENDER: Renderers = {
  convergence_point: (o, n) => (
    <>
      <Head>
        <Name nodeKey={o.node_key} nameOf={n} />
        <Tag>{o.verdict}</Tag>
      </Head>
      <Prose text={o.reasoning} />
    </>
  ),
  common_link: (o, n) => (
    <>
      <Head>
        <Name nodeKey={o.node_key} nameOf={n} />
        <Tag>{o.verdict}</Tag>
        {o.cluster_labels.length > 0 ? <span className="text-[15px] text-ink-muted">clusters: {o.cluster_labels.join(", ")}</span> : null}
      </Head>
      <Prose text={o.reasoning} />
    </>
  ),
  partial_common_link: (o, n) => RENDER.convergence_point(o, n),
  dive: (o) => (
    <>
      <Head>
        <span className="font-bold">Chain {o.chain_id}</span>
        <Tag>{o.interpretation.replaceAll("_", " ")}</Tag>
      </Head>
      <Prose text={o.reasoning} />
    </>
  ),
  matn_cluster: (o, n) => (
    <>
      <Head>
        <span className="font-bold">{o.label}</span>
        <span className="text-[15px] text-ink-muted">variants {o.variant_ids.join(", ")}</span>
      </Head>
      <Prose text={o.defining_features} />
      {o.branch_node_keys.length > 0 ? (
        <p className="mt-2 flex flex-wrap items-baseline gap-x-3 text-[15px] text-ink-muted">
          Carried by
          {o.branch_node_keys.map((k) => (
            <Name key={k} nodeKey={k} nameOf={n} />
          ))}
        </p>
      ) : null}
    </>
  ),
  correlation: (o) => (
    <>
      <Tag>{o.finding.replaceAll("_", " ")}</Tag>
      <Prose text={o.reasoning} />
    </>
  ),
  reconstruction: (o, n) => (
    <>
      <Head>
        <Name nodeKey={o.node_key} nameOf={n} />
      </Head>
      <Ar as="p" className="mt-2 text-[21px] leading-loose">
        {o.text_ar}
      </Ar>
      <p className="mt-1 max-w-[75ch] text-[16px] italic">{o.translation_en}</p>
      {o.uncertain_elements.length > 0 ? <p className="mt-2 text-[15px] text-ink-muted">Uncertain: {o.uncertain_elements.join("; ")}</p> : null}
    </>
  ),
  dating: (o, n) => (
    <>
      <Head>
        <Name nodeKey={o.earliest_reliable_node_key} nameOf={n} />
        <span className="tabular-nums">
          {o.date_range_ah} AH · {o.date_range_ce} CE
        </span>
      </Head>
      <Prose text={o.reasoning} />
    </>
  ),
  upper_isnad: (o) => <Prose text={o.assessment} />,
  chain_matn: (o) => (
    <>
      <Head>
        <span className="font-bold">Chain {o.chain_id}</span>
        <Tag>{o.source}</Tag>
      </Head>
      {o.text_ar === null ? <p className="mt-2 text-ink-muted">No wording recovered.</p> : <Ar as="p" className="mt-2 text-[20px] leading-loose">{o.text_ar}</Ar>}
    </>
  ),
  matn_element: (o) => (
    <>
      <Head>
        <span className="font-bold">
          {o.id}. {o.label_en}
        </span>
      </Head>
      <Prose text={o.description_en} />
      <Ar as="p" className="mt-1 text-[19px]">
        {o.exemplar_ar}
      </Ar>
    </>
  ),
  variant_reading: (o) => (
    <>
      <Head>
        <span className="font-bold">{o.variant_id}</span>
        <span className="text-[15px] text-ink-muted">{o.elements.map((e) => `${e.element_id}:${e.wording_class}`).join("  ")}</span>
      </Head>
      <p className="mt-2 max-w-[75ch] text-[16px] italic">{o.translation_en}</p>
      <Prose text={o.notes_en} />
    </>
  ),
};

function render<K extends JudgementKind>(kind: K, output: unknown, nameOf: NameOf): ReactElement {
  const parsed = OUTPUT_SCHEMAS[kind].safeParse(output);
  if (!parsed.success) return <pre className="overflow-x-auto text-[13px]">{JSON.stringify(output, null, 2)}</pre>;
  return RENDER[kind](parsed.data as OutputOf<K>, nameOf);
}

/** A model judgement (or a reviewer's revision of it) rendered for reading. */
export function JudgementBody({ kind, output, nameOf }: { kind: JudgementKind; output: unknown; nameOf: NameOf }): ReactElement {
  return <div>{render(kind, output, nameOf)}</div>;
}
