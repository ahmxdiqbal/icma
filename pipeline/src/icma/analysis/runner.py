"""Run the ICMA stages for one tradition, caching each model call on disk by its exact input.

Stages: chain_matns (model, multi-chain entries only) -> variants (code) -> matn_inventory (model)
-> correlation (code) -> icma_synthesis (model). A rerun with unchanged inputs makes no API calls.
"""

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from icma.analysis import prompts
from icma.analysis.correlation import NodeCorrelation, correlate
from icma.analysis.llm import StructuredCaller
from icma.analysis.schemas import ChainMatn, ChainMatnSet, IcmaAnalysis, MatnInventory
from icma.analysis.variants import (
    ChainText,
    Variant,
    chain_texts,
    extraction_warnings,
    group_variants,
)
from icma.analysis.variants import multi_chain_hadith_ids as multi_ids
from icma.bundle import Bundle, branch_groups, key_figures
from icma.models import Tradition

ANALYSIS_SCHEMA_VERSION = 1
EXTRACTION_WORKERS = 8


@dataclass(frozen=True, slots=True)
class Stage:
    name: str
    system: str
    user: str


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_stage[M: BaseModel](
    stage: Stage, schema: type[M], caller: StructuredCaller, out_dir: Path
) -> M:
    """Return the cached output for this exact input, or call the model and cache it."""
    input_sha = _sha256(f"{prompts.PROMPT_VERSION}\0{stage.system}\0{stage.user}")
    path = out_dir / f"{stage.name}-{input_sha[:16]}.json"
    if path.exists():
        return schema.model_validate(json.loads(path.read_text(encoding="utf-8"))["output"])
    started = time.monotonic()
    result = caller.call(system=stage.system, user=stage.user, schema=schema)
    elapsed = round(time.monotonic() - started, 1)
    record = {
        "stage": stage.name,
        "prompt_version": prompts.PROMPT_VERSION,
        "system_sha256": _sha256(stage.system),
        "input_sha256": input_sha,
        "model": result.model,
        "message_id": result.message_id,
        "stop_reason": result.stop_reason,
        "usage": result.usage,
        "elapsed_seconds": elapsed,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "system": stage.system,
        "user": stage.user,
        "output": result.parsed.model_dump(mode="json"),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return result.parsed


# ---------------------------------------------------------------- validation of model output


def check_chain_matns(
    found: list[ChainMatn], expected: set[int]
) -> tuple[list[ChainMatn], list[str]]:
    """Keep only expected chain ids; report unknown, duplicate and missing ones."""
    warnings: list[str] = []
    kept: dict[int, ChainMatn] = {}
    for m in found:
        if m.chain_id not in expected:
            warnings.append(f"chain_matns: unknown chain id {m.chain_id} dropped")
        elif m.chain_id in kept:
            warnings.append(f"chain_matns: duplicate chain id {m.chain_id}; first kept")
        else:
            kept[m.chain_id] = m
    warnings += [f"chain_matns: no extraction for chain {c}" for c in sorted(expected - set(kept))]
    return list(kept.values()), warnings


def check_inventory(inventory: MatnInventory, variants: list[Variant]) -> list[str]:
    expected = {v.id for v in variants}
    returned = {r.variant_id for r in inventory.variants}
    element_ids = {e.id for e in inventory.elements}
    used = {r.element_id for v in inventory.variants for r in v.elements}
    return (
        [f"matn_inventory: missing variant {v}" for v in sorted(expected - returned)]
        + [f"matn_inventory: unknown variant {v}" for v in sorted(returned - expected)]
        + [f"matn_inventory: undefined element {e}" for e in sorted(used - element_ids)]
    )


def check_synthesis(analysis: IcmaAnalysis, bundle: Bundle, variants: list[Variant]) -> list[str]:
    keys = {s.key for s in bundle.nodes}
    chains = {p.chain_id for p in bundle.paths}
    variant_ids = {v.id for v in variants}
    cited_keys = [
        analysis.convergence_point.node_key,
        analysis.dating.earliest_reliable_node_key,
        *(c.node_key for c in analysis.common_links),
        *(r.node_key for r in analysis.reconstructions),
        *(j.node_key for j in analysis.partial_common_links),
        *(k for c in analysis.matn_clusters for k in c.branch_node_keys),
    ]
    cited_variants = [v for c in analysis.matn_clusters for v in c.variant_ids]
    return (
        [f"icma_synthesis: unknown node key {k}" for k in cited_keys if k not in keys]
        + [
            f"icma_synthesis: unknown chain {d.chain_id}"
            for d in analysis.dives
            if d.chain_id not in chains
        ]
        + [f"icma_synthesis: unknown variant {v}" for v in cited_variants if v not in variant_ids]
    )


# ---------------------------------------------------------------- orchestration


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    chain_texts: list[ChainText]
    variants: list[Variant]
    inventory: MatnInventory
    correlations: list[NodeCorrelation]
    synthesis: IcmaAnalysis
    warnings: list[str]


def _extract_chain_matns(
    tradition: Tradition, caller: StructuredCaller, out_dir: Path
) -> tuple[list[ChainMatn], list[str]]:
    multi = multi_ids(tradition)
    if not multi:
        return [], []

    def extract(hadith_id: int) -> list[ChainMatn]:
        user = prompts.chain_matn_input(tradition, {hadith_id})
        stage = Stage("chain_matns", prompts.CHAIN_MATN_SYSTEM, user)
        return run_stage(stage, ChainMatnSet, caller, out_dir).chains

    # One small request per entry: long multi-entry requests made several models skip routes.
    with ThreadPoolExecutor(max_workers=EXTRACTION_WORKERS) as pool:
        found = [m for batch in pool.map(extract, sorted(multi)) for m in batch]
    expected = {c.id for c in tradition.chains if c.hadith_id in multi}
    kept, warnings = check_chain_matns(found, expected)
    return kept, warnings + extraction_warnings(tradition, kept)


def analyze(
    title: str, tradition: Tradition, bundle: Bundle, caller: StructuredCaller, out_dir: Path
) -> AnalysisResult:
    extracted, warnings = _extract_chain_matns(tradition, caller, out_dir)
    texts = chain_texts(tradition, extracted)
    variants = group_variants(texts)
    inventory_stage = Stage(
        "matn_inventory", prompts.INVENTORY_SYSTEM, prompts.inventory_input(variants)
    )
    inventory = run_stage(inventory_stage, MatnInventory, caller, out_dir)
    warnings += check_inventory(inventory, variants)
    correlations = [
        correlate(s.key, branch_groups(bundle.paths, s.key), variants, inventory)
        for s in key_figures(bundle.nodes)
    ]
    synthesis_user = prompts.synthesis_input(
        title, tradition, bundle, variants, inventory, correlations
    )
    synthesis_stage = Stage("icma_synthesis", prompts.SYNTHESIS_SYSTEM, synthesis_user)
    synthesis = run_stage(synthesis_stage, IcmaAnalysis, caller, out_dir)
    warnings += check_synthesis(synthesis, bundle, variants)
    return AnalysisResult(texts, variants, inventory, correlations, synthesis, warnings)


def analysis_json(package_id: str, result: AnalysisResult, model: str) -> dict[str, object]:
    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "package_id": package_id,
        "model": model,
        "prompt_version": prompts.PROMPT_VERSION,
        "status": "unreviewed",
        "chain_texts": [asdict(t) for t in result.chain_texts],
        "variants": [asdict(v) for v in result.variants],
        "inventory": result.inventory.model_dump(mode="json"),
        "correlations": [asdict(c) for c in result.correlations],
        "synthesis": result.synthesis.model_dump(mode="json"),
        "warnings": result.warnings,
    }
