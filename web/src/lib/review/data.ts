import "server-only";
import type { Reviewer } from "@/lib/auth/access";
import { db } from "@/lib/db";
import { isJudgementKind, type Decision, type JudgementKind } from "./schemas";
import type { ValidReview } from "./validate";

export interface AnalysisSummary {
  id: number;
  packageId: string;
  promptVersion: string;
  importedAt: string;
  total: number;
  reviewed: number;
}

export interface ReviewRecord {
  id: number;
  reviewer: string;
  decision: Decision;
  revisedOutput: unknown;
  note: string;
  createdAt: string;
}

export interface JudgementRow {
  id: number;
  kind: JudgementKind;
  itemKey: string;
  modelOutput: unknown;
  /** Newest first; the first entry is the current review. */
  history: ReviewRecord[];
}

export interface AnalysisDetail {
  summary: AnalysisSummary;
  payload: unknown;
  judgements: JudgementRow[];
}

const SUMMARY_SELECT = `
  SELECT a.id::int AS id, a.package_id, a.prompt_version, a.imported_at::text AS imported_at,
         count(j.id)::int AS total, count(cr.judgement_id)::int AS reviewed
  FROM analyses a
  LEFT JOIN judgements j ON j.analysis_id = a.id
  LEFT JOIN current_reviews cr ON cr.judgement_id = j.id`;

interface SummaryRow {
  id: number;
  package_id: string;
  prompt_version: string;
  imported_at: string;
  total: number;
  reviewed: number;
}

function toSummary(row: SummaryRow): AnalysisSummary {
  return {
    id: row.id,
    packageId: row.package_id,
    promptVersion: row.prompt_version,
    importedAt: row.imported_at,
    total: row.total,
    reviewed: row.reviewed,
  };
}

export async function listAnalyses(): Promise<AnalysisSummary[]> {
  const { rows } = await db().query<SummaryRow>(`${SUMMARY_SELECT} GROUP BY a.id ORDER BY a.imported_at DESC, a.id DESC`);
  return rows.map(toSummary);
}

interface JudgementQueryRow {
  id: number;
  kind: string;
  item_key: string;
  model_output: unknown;
  history: Array<{ id: number; reviewer: string; decision: Decision; revised_output: unknown; note: string; created_at: string }>;
}

const JUDGEMENTS_SELECT = `
  SELECT j.id::int AS id, j.kind, j.item_key, j.model_output,
         coalesce(json_agg(json_build_object(
           'id', r.id, 'reviewer', r.reviewer, 'decision', r.decision,
           'revised_output', r.revised_output, 'note', r.note, 'created_at', r.created_at)
           ORDER BY r.created_at DESC, r.id DESC) FILTER (WHERE r.id IS NOT NULL), '[]') AS history
  FROM judgements j
  LEFT JOIN reviews r ON r.judgement_id = j.id
  WHERE j.analysis_id = $1
  GROUP BY j.id
  ORDER BY j.position`;

function toJudgement(row: JudgementQueryRow): JudgementRow {
  if (!isJudgementKind(row.kind)) throw new Error(`unknown judgement kind ${row.kind}`);
  return {
    id: row.id,
    kind: row.kind,
    itemKey: row.item_key,
    modelOutput: row.model_output,
    history: row.history.map((h) => ({
      id: Number(h.id),
      reviewer: h.reviewer,
      decision: h.decision,
      revisedOutput: h.revised_output,
      note: h.note,
      createdAt: h.created_at,
    })),
  };
}

export async function getAnalysis(id: number): Promise<AnalysisDetail | null> {
  const summary = await db().query<SummaryRow>(`${SUMMARY_SELECT} WHERE a.id = $1 GROUP BY a.id`, [id]);
  const row = summary.rows[0];
  if (row === undefined) return null;
  const [payload, judgements] = await Promise.all([
    db().query<{ payload: unknown }>("SELECT payload FROM analyses WHERE id = $1", [id]),
    db().query<JudgementQueryRow>(JUDGEMENTS_SELECT, [id]),
  ]);
  return { summary: toSummary(row), payload: payload.rows[0]?.payload, judgements: judgements.rows.map(toJudgement) };
}

export interface JudgementRef {
  analysisId: number;
  kind: JudgementKind;
  itemKey: string;
}

export async function getJudgementRef(id: number): Promise<JudgementRef | null> {
  const { rows } = await db().query<{ analysis_id: number; kind: string; item_key: string }>(
    "SELECT analysis_id::int AS analysis_id, kind, item_key FROM judgements WHERE id = $1",
    [id],
  );
  const row = rows[0];
  if (row === undefined || !isJudgementKind(row.kind)) return null;
  return { analysisId: row.analysis_id, kind: row.kind, itemKey: row.item_key };
}

/** Appends a review; earlier reviews of the same judgement are kept as history. */
export async function insertReview(review: ValidReview, reviewer: Reviewer): Promise<void> {
  await db().query(
    "INSERT INTO reviews (judgement_id, reviewer, decision, revised_output, note) VALUES ($1, $2, $3, $4, $5)",
    [
      review.judgementId,
      reviewer.email,
      review.decision,
      review.revisedOutput === null ? null : JSON.stringify(review.revisedOutput),
      review.note,
    ],
  );
}
