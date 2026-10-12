/**
 * Zod mirror of the tradition package contract (schema v1), written by
 * pipeline/src/icma/export.py. Objects are strict: any field the pipeline adds or
 * drops fails the parse, so contract drift surfaces at load time instead of in the UI.
 */
import { z } from "zod";
import { findReferenceProblems } from "./references";

const id = z.number().int().nonnegative();
const count = z.number().int().nonnegative();

export const GAP_KINDS = ["irsal", "inqita", "taliq", "mubham"] as const;
export const gapKindSchema = z.enum(GAP_KINDS);
export type GapKind = z.infer<typeof gapKindSchema>;

const GAP = GAP_KINDS.join("|");
const prophetKey = z.literal("prophet");
const narratorKey = z.string().regex(/^n:\d+$/);
const gapNodeKey = z.string().regex(new RegExp(`^g:(${GAP}):\\d+:\\d+$`));
const nodeKey = z.union([prophetKey, narratorKey, gapNodeKey]);
/** Upper-path labels group gaps by kind only (`g:<gap>`), dropping per-chain identity. */
const pathLabel = z.union([prophetKey, narratorKey, z.string().regex(new RegExp(`^g:(${GAP})$`))]);

const bookSchema = z.strictObject({
  id,
  title_ar: z.string(),
  author_ar: z.string(),
  author_death_ah: z.number().int().nullable(),
  category_ar: z.string(),
  edition: z.strictObject({
    publisher_ar: z.string().nullable(),
    city_ar: z.string().nullable(),
    printing_ar: z.string().nullable(),
  }),
});

const narratorSchema = z.strictObject({
  id,
  name_ar: z.string(),
  display_name_ar: z.string(),
  tabaqa: z.number().int(),
  grade_code: z.number().int(),
  grade_ar: z.string().nullable(),
  death_ah: z.number().int().nullable(),
  death_ah_raw: z.string().nullable(),
  residence_ar: z.string().nullable(),
  has_tadlis: z.boolean(),
  has_ikhtilat: z.boolean(),
  in_bukhari: z.boolean(),
  in_muslim: z.boolean(),
  is_stub: z.boolean(),
});

const mentionSchema = z.strictObject({
  start: z.number().int(),
  end: z.number().int(),
  narrator_id: id.nullable(),
});

const hadithSchema = z.strictObject({
  id,
  book_id: id,
  number_in_book: z.number().int(),
  page: z.number().int(),
  type: z.enum(["qudsi", "marfu", "mawquf", "maqtu"]),
  grade_ar: z.string(),
  text_ar: z.string(),
  matn_span: z.tuple([z.number().int(), z.number().int()]).nullable(),
  mentions: z.array(mentionSchema),
  translation_en: z.string().nullable(),
  translation_source: z.string().nullable(),
});

const linkSchema = z.discriminatedUnion("kind", [
  z.strictObject({ kind: z.literal("narrator"), narrator_id: id }),
  z.strictObject({ kind: z.literal("gap"), gap: gapKindSchema }),
]);

const chainSchema = z.strictObject({
  id,
  hadith_id: id,
  grade_ar: z.string(),
  in_bundle: z.boolean(),
  links: z.array(linkSchema),
});

const nodeStats = {
  chain_ids: z.array(id),
  min_depth: count,
  student_keys: z.array(nodeKey),
  collector_keys: z.array(nodeKey),
  independent_branch_count: count,
  corroborated_branch_count: count,
  single_strand_branch_count: count,
};

const bundleNodeSchema = z.discriminatedUnion("kind", [
  z.strictObject({ key: prophetKey, kind: z.literal("prophet"), ...nodeStats }),
  z.strictObject({ key: narratorKey, kind: z.literal("narrator"), narrator_id: id, ...nodeStats }),
  z.strictObject({ key: gapNodeKey, kind: z.literal("gap"), gap: gapKindSchema, ...nodeStats }),
]);

const bundleSchema = z.strictObject({
  root: prophetKey,
  nodes: z.array(bundleNodeSchema),
  edges: z.array(
    z.strictObject({ source: nodeKey, target: nodeKey, chain_ids: z.array(id).min(1) }),
  ),
  cl_candidates: z.array(narratorKey),
  suggested_cl: narratorKey.nullable(),
  spiders: z.array(narratorKey),
  dives: z.array(
    z.strictObject({ chain_id: id, departs_from: nodeKey, rejoins_at: nodeKey.nullable() }),
  ),
  upper_paths: z.array(z.strictObject({ labels: z.array(pathLabel), chain_ids: z.array(id) })),
  warnings: z.array(
    z.strictObject({
      code: z.enum(["repeated_narrator", "too_short", "reversed_edge"]),
      message: z.string(),
      chain_ids: z.array(id),
    }),
  ),
});

const correctionSchema = z.strictObject({
  chain_id: id,
  op: z.enum(["replace", "set_links", "exclude"]),
  from_narrator_id: id.nullable(),
  to_narrator_id: id.nullable(),
  links: z.array(linkSchema).nullable(),
  reason: z.string(),
  evidence: z.string(),
  author: z.string(),
  date: z.string(),
});

const sourceSchema = z.strictObject({
  dataset: z.string(),
  url: z.url(),
  license: z.string(),
  attribution: z.string(),
  selection: z.strictObject({ group_id: z.number().int(), anchor_narrator_ids: z.array(id) }),
});

export const rawPackageSchema = z.strictObject({
  schema_version: z.literal(1),
  id: z.string().regex(/^[a-z0-9-]+$/),
  title_en: z.string(),
  generated_at: z.iso.datetime({ offset: true }),
  source: sourceSchema,
  corrections_applied: z.array(correctionSchema),
  books: z.array(bookSchema),
  narrators: z.array(narratorSchema),
  hadiths: z.array(hadithSchema),
  chains: z.array(chainSchema),
  bundle: bundleSchema,
});

export const traditionPackageSchema = rawPackageSchema.superRefine((pkg, ctx) => {
  for (const message of findReferenceProblems(pkg)) {
    ctx.addIssue({ code: "custom", message });
  }
});

export type TraditionPackage = z.infer<typeof rawPackageSchema>;
export type Book = TraditionPackage["books"][number];
export type Narrator = TraditionPackage["narrators"][number];
export type Hadith = TraditionPackage["hadiths"][number];
export type Mention = Hadith["mentions"][number];
export type Chain = TraditionPackage["chains"][number];
export type ChainLink = Chain["links"][number];
export type Bundle = TraditionPackage["bundle"];
export type BundleNode = Bundle["nodes"][number];
export type BundleEdge = Bundle["edges"][number];
export type Dive = Bundle["dives"][number];
export type UpperPath = Bundle["upper_paths"][number];
export type BundleWarning = Bundle["warnings"][number];
export type Correction = TraditionPackage["corrections_applied"][number];
export type Source = TraditionPackage["source"];
