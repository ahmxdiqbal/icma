"""Run one ICMA analysis with several OpenRouter models; compare cost, speed, and quality."""

import json
import re
import shutil
import urllib.request
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

from icma.analysis.llm import AnalysisError
from icma.analysis.openrouter import OpenRouterCaller
from icma.analysis.runner import AnalysisResult, analysis_json, analyze
from icma.analysis.variants import ChainText
from icma.arabic import normalize
from icma.bundle import Bundle
from icma.evaluate import Score, ScoringKey, score
from icma.models import Tradition

MODELS_URL = "https://openrouter.ai/api/v1/models"
MAX_OUTPUT_TOKENS = 131_072


@dataclass(frozen=True, slots=True)
class StageStats:
    stage: str
    cost_usd: float
    prompt_tokens: int
    completion_tokens: int
    seconds: float


@dataclass(slots=True)
class ModelReport:
    model: str
    completed: bool = False
    error: str | None = None
    stages: list[StageStats] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    extracted_verbatim: int = 0
    extracted_total: int = 0
    score: Score | None = None

    @property
    def cost_usd(self) -> float:
        return round(sum(s.cost_usd for s in self.stages), 4)

    @property
    def seconds(self) -> float:
        return round(sum(s.seconds for s in self.stages), 1)


def output_limits(models: Sequence[str]) -> dict[str, int]:
    """Each model's max completion tokens on OpenRouter, capped at MAX_OUTPUT_TOKENS."""
    with urllib.request.urlopen(MODELS_URL, timeout=60) as response:
        listing = json.loads(response.read())["data"]
    limits: dict[str, int] = {}
    for entry in listing:
        if entry["id"] in models:
            top = entry.get("top_provider") or {}
            limits[entry["id"]] = min(
                int(top.get("max_completion_tokens") or MAX_OUTPUT_TOKENS), MAX_OUTPUT_TOKENS
            )
    return limits


def slug(model: str) -> str:
    return re.sub(r"[^a-z0-9.-]+", "_", model.lower())


def _int(value: object) -> int:
    return value if isinstance(value, int) else 0


def stage_stats(work_dir: Path, model: str) -> list[StageStats]:
    """Stages this model ran itself; records seeded from another model are skipped."""
    stats: list[StageStats] = []
    for path in sorted(work_dir.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if "stage" not in record or not str(record.get("model", "")).startswith(model):
            continue
        usage = record.get("usage") or {}
        cost = usage.get("cost")
        stats.append(
            StageStats(
                stage=str(record["stage"]),
                cost_usd=float(cost) if isinstance(cost, int | float) else 0.0,
                prompt_tokens=_int(usage.get("prompt_tokens")),
                completion_tokens=_int(usage.get("completion_tokens")),
                seconds=float(record.get("elapsed_seconds") or 0.0),
            )
        )
    return stats


def verbatim_extractions(tradition: Tradition, texts: Sequence[ChainText]) -> tuple[int, int]:
    """How many model-extracted per-route matns occur word for word in their source entry."""
    entries = {h.id: normalize(h.text_ar) for h in tradition.hadiths}
    extracted = [t for t in texts if t.source == "extracted" and t.text_ar]
    verbatim = sum(
        1 for t in extracted if normalize(t.text_ar or "") in entries.get(t.hadith_id, "")
    )
    return verbatim, len(extracted)


SEEDED_STAGES = ("chain_matns", "matn_inventory")


@dataclass(frozen=True, slots=True)
class Job:
    package_id: str
    title: str
    tradition: Tradition
    bundle: Bundle
    key: ScoringKey
    work_root: Path
    # Copy these stage outputs into every model's cache, so models differ only in the synthesis.
    seed_dir: Path | None = None


def seed(work_dir: Path, seed_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    for stage in SEEDED_STAGES:
        for path in seed_dir.glob(f"{stage}-*.json"):
            shutil.copy2(path, work_dir / path.name)


def run_model(job: Job, model: str, max_tokens: int) -> ModelReport:
    report = ModelReport(model)
    work_dir = job.work_root / slug(model)
    if job.seed_dir is not None:
        seed(work_dir, job.seed_dir)
    try:
        caller = OpenRouterCaller(model=model, effort="high", max_tokens=max_tokens)
        result: AnalysisResult = analyze(job.title, job.tradition, job.bundle, caller, work_dir)
    except (AnalysisError, ValueError) as error:
        report.error = str(error)[:400]
    else:
        report.completed = True
        report.warnings = result.warnings
        report.extracted_verbatim, report.extracted_total = verbatim_extractions(
            job.tradition, result.chain_texts
        )
        report.score = score(result.synthesis, job.key)
        payload = analysis_json(job.package_id, result, model)
        (work_dir / "analysis.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    report.stages = stage_stats(work_dir, model) if work_dir.exists() else []
    return report


def compare(job: Job, models: Sequence[str]) -> list[ModelReport]:
    limits = output_limits(models)
    missing = [m for m in models if m not in limits]
    if missing:
        raise ValueError(f"not on OpenRouter: {missing}")
    with ThreadPoolExecutor(max_workers=len(models)) as pool:
        return list(pool.map(lambda m: run_model(job, m, limits[m]), models))


def _score_cells(s: Score | None) -> str:
    if s is None:
        return "| - | - | - | - |"
    convergence = "yes" if s.convergence_verdict_correct else "no"
    return f"| {s.cl_recall:.2f} | {s.cl_precision:.2f} | {s.pcl_recall:.2f} | {convergence} |"


def markdown(reports: Sequence[ModelReport]) -> str:
    head = (
        "| Model | Done | Cost (USD) | Time (s) | Warnings | Verbatim extractions "
        "| CL recall | CL precision | PCL recall | Convergence verdict right |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
    )
    rows = [
        f"| {r.model} | {'yes' if r.completed else 'no'} | {r.cost_usd:.3f} | {r.seconds:.0f} "
        f"| {len(r.warnings)} | {r.extracted_verbatim}/{r.extracted_total} {_score_cells(r.score)}"
        for r in reports
    ]
    errors = [f"- {r.model}: {r.error}" for r in reports if r.error]
    return head + "\n".join(rows) + ("\n\nErrors:\n" + "\n".join(errors) if errors else "") + "\n"


def report_json(reports: Sequence[ModelReport]) -> list[dict[str, object]]:
    return [asdict(r) | {"cost_usd": r.cost_usd, "seconds": r.seconds} for r in reports]
