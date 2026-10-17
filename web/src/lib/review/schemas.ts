/**
 * Shapes of each judgement kind's model output, mirroring pipeline/src/icma/analysis/schemas.py and
 * pipeline/src/icma/db.py. A revision must match the same shape as the output it replaces.
 */
import { z } from "zod";

export const JUDGEMENT_KINDS = [
  "convergence_point",
  "common_link",
  "partial_common_link",
  "dive",
  "matn_cluster",
  "correlation",
  "reconstruction",
  "dating",
  "upper_isnad",
  "chain_matn",
  "matn_element",
  "variant_reading",
] as const;

export type JudgementKind = (typeof JUDGEMENT_KINDS)[number];

export const DECISIONS = ["accept", "reject", "revise"] as const;
export type Decision = (typeof DECISIONS)[number];

const verdict = z.enum(["supported", "doubtful", "rejected", "undecidable"]);

const nodeJudgement = z.strictObject({ node_key: z.string(), verdict, reasoning: z.string() });

export const OUTPUT_SCHEMAS = {
  convergence_point: nodeJudgement,
  common_link: z.strictObject({ ...nodeJudgement.shape, cluster_labels: z.array(z.string()) }),
  partial_common_link: nodeJudgement,
  dive: z.strictObject({
    chain_id: z.number().int(),
    interpretation: z.enum(["later_borrowing", "independent_transmission", "transmission_error", "undecidable"]),
    reasoning: z.string(),
  }),
  matn_cluster: z.strictObject({
    label: z.string(),
    defining_features: z.string(),
    variant_ids: z.array(z.string()),
    branch_node_keys: z.array(z.string()),
  }),
  correlation: z.strictObject({ finding: z.enum(["strong", "partial", "none", "insufficient_data"]), reasoning: z.string() }),
  reconstruction: z.strictObject({
    node_key: z.string(),
    text_ar: z.string(),
    translation_en: z.string(),
    uncertain_elements: z.array(z.string()),
  }),
  dating: z.strictObject({
    earliest_reliable_node_key: z.string(),
    date_range_ah: z.string(),
    date_range_ce: z.string(),
    reasoning: z.string(),
  }),
  upper_isnad: z.strictObject({ assessment: z.string() }),
  chain_matn: z.strictObject({
    chain_id: z.number().int(),
    hadith_id: z.number().int(),
    text_ar: z.string().nullable(),
    source: z.enum(["span", "extracted", "inherited", "missing"]),
  }),
  matn_element: z.strictObject({ id: z.string(), label_en: z.string(), description_en: z.string(), exemplar_ar: z.string() }),
  variant_reading: z.strictObject({
    variant_id: z.string(),
    elements: z.array(z.strictObject({ element_id: z.string(), wording_ar: z.string(), wording_class: z.string() })),
    translation_en: z.string(),
    notes_en: z.string(),
  }),
} satisfies Record<JudgementKind, z.ZodType>;

export type OutputOf<K extends JudgementKind> = z.infer<(typeof OUTPUT_SCHEMAS)[K]>;

/** The field that identifies the judged item; a revision may not change it. */
export const IDENTITY_FIELD: Record<JudgementKind, string | null> = {
  convergence_point: "node_key",
  common_link: "node_key",
  partial_common_link: "node_key",
  dive: "chain_id",
  matn_cluster: "label",
  correlation: null,
  reconstruction: "node_key",
  dating: null,
  upper_isnad: null,
  chain_matn: "chain_id",
  matn_element: "id",
  variant_reading: "variant_id",
};

export function isJudgementKind(value: string): value is JudgementKind {
  return (JUDGEMENT_KINDS as readonly string[]).includes(value);
}
