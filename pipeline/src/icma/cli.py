"""Command line entry point: python -m icma.cli {export,analyze} ..."""

import argparse
import json
from dataclasses import replace
from pathlib import Path

from icma.bundle import Bundle, build_bundle, to_paths
from icma.corrections import Correction, apply_corrections, load_corrections
from icma.export import PackageMeta, package_json
from icma.models import HadithType, NarratorLink, Tradition
from icma.sources.hadith_kg import HadithKgReader

PROPHETIC = {HadithType.MARFU, HadithType.QUDSI}


def _int_list(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split(",") if part.strip())


def _add_selection(command: argparse.ArgumentParser) -> None:
    command.add_argument("--db", type=Path, required=True, help="path to hadith-kg.db")
    command.add_argument("--group", type=int, required=True, help="hadith-kg meaning group id")
    command.add_argument(
        "--anchors", type=_int_list, required=True, help="narrator ids, comma list"
    )
    command.add_argument("--corrections", type=Path, help="corrections JSON for this source")
    command.add_argument("--id", required=True, help="package slug")
    command.add_argument("--title", required=True, help="English title")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="icma")
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export", help="export one tradition as a JSON package")
    _add_selection(export)
    export.add_argument("--out", type=Path, required=True)
    analyze = sub.add_parser("analyze", help="run the model ICMA stages for one tradition")
    _add_selection(analyze)
    analyze.add_argument("--work-dir", type=Path, required=True, help="cache of stage outputs")
    analyze.add_argument("--out", type=Path, required=True, help="analysis JSON to write")
    analyze.add_argument(
        "--effort", choices=["low", "medium", "high", "xhigh", "max"], default="high"
    )
    score = sub.add_parser("score", help="score an analysis against a gold scoring key")
    score.add_argument("--analysis", type=Path, required=True, help="analysis JSON from analyze")
    score.add_argument("--key", type=Path, required=True, help="scoring key JSON")
    return parser


def load_corrected(
    db: Path, group: int, anchors: tuple[int, ...], corrections_path: Path | None
) -> tuple[Tradition, list[Correction]]:
    """Load a tradition, apply corrections, and fetch any narrators the corrections introduce."""
    reader = HadithKgReader(db)
    try:
        tradition = reader.load_tradition(group, anchors)
        corrections = load_corrections(corrections_path) if corrections_path else []
        chains, applied = apply_corrections(tradition.chains, corrections)
        linked = {k.narrator_id for c in chains for k in c.links if isinstance(k, NarratorLink)}
        missing = sorted(linked - {n.id for n in tradition.narrators})
        narrators = sorted(
            [*tradition.narrators, *reader.load_narrators(missing)], key=lambda n: n.id
        )
    finally:
        reader.close()
    return replace(tradition, chains=tuple(chains), narrators=tuple(narrators)), applied


def bundle_of(tradition: Tradition) -> Bundle:
    prophetic_hadiths = {h.id for h in tradition.hadiths if h.type in PROPHETIC}
    prophetic_chains = {c.id for c in tradition.chains if c.hadith_id in prophetic_hadiths}
    paths, warnings = to_paths(tradition.chains, prophetic_chains)
    return build_bundle(paths, warnings)


def export(args: argparse.Namespace) -> None:
    tradition, applied = load_corrected(args.db, args.group, args.anchors, args.corrections)
    bundle = bundle_of(tradition)
    meta = PackageMeta(args.id, args.title, args.group, args.anchors)
    package = package_json(meta, tradition, bundle, applied)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(package, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"wrote {args.out}: {len(tradition.hadiths)} hadith, {len(tradition.chains)} chains "
        f"({len(bundle.paths)} in bundle), {len(tradition.narrators)} narrators, "
        f"{len(applied)} corrections; suggested CL {bundle.suggested_cl}"
    )


def analyze(args: argparse.Namespace) -> None:
    # Imported here so `export` works without the model SDK configured.
    from icma.analysis.llm import AnthropicCaller
    from icma.analysis.runner import analysis_json
    from icma.analysis.runner import analyze as run_analysis

    tradition, _ = load_corrected(args.db, args.group, args.anchors, args.corrections)
    bundle = bundle_of(tradition)
    caller = AnthropicCaller(effort=args.effort)
    result = run_analysis(args.title, tradition, bundle, caller, args.work_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = analysis_json(args.id, result)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {args.out}: {len(result.variants)} variants, {len(result.warnings)} warnings")
    for warning in result.warnings:
        print(f"  warning: {warning}")


def score(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from icma.analysis.schemas import IcmaAnalysis
    from icma.evaluate import load_key
    from icma.evaluate import score as score_analysis

    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    synthesis = IcmaAnalysis.model_validate(analysis["synthesis"])
    key = load_key(json.loads(args.key.read_text(encoding="utf-8")))
    print(json.dumps(asdict(score_analysis(synthesis, key)), indent=1))


def main() -> None:
    args = _parser().parse_args()
    if args.command == "export":
        export(args)
    elif args.command == "analyze":
        analyze(args)
    elif args.command == "score":
        score(args)


if __name__ == "__main__":
    main()
