"""Command line entry point: python -m icma.cli {export,analyze} ..."""

import argparse
import json
import os
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
    db_help = "Postgres URL; defaults to $DATABASE_URL_UNPOOLED, then $DATABASE_URL"
    migrate = sub.add_parser("migrate", help="apply database migrations")
    migrate.add_argument("--database-url", help=db_help)
    publish = sub.add_parser("publish", help="store an analysis and its judgements for review")
    publish.add_argument("--analysis", type=Path, required=True, help="analysis JSON from analyze")
    publish.add_argument("--database-url", help=db_help)
    reviewer = sub.add_parser("reviewer", help="grant, change, revoke, or list app access")
    reviewer.add_argument("action", choices=["add", "remove", "list", "passcode"])
    reviewer.add_argument("--email")
    reviewer.add_argument("--role", choices=["admin", "reviewer"], default="reviewer")
    reviewer.add_argument("--database-url", help=db_help)
    compare = sub.add_parser("compare-models", help="run the analysis with several models")
    _add_selection(compare)
    compare.add_argument("--models", required=True, help="comma-separated OpenRouter model ids")
    compare.add_argument("--key", type=Path, required=True, help="scoring key JSON")
    compare.add_argument("--work-dir", type=Path, required=True)
    compare.add_argument("--out", type=Path, required=True, help="markdown report to write")
    compare.add_argument(
        "--seed-from", type=Path, help="reuse this run's extraction and inventory for every model"
    )
    score = sub.add_parser("score", help="score an analysis against a gold scoring key")
    score.add_argument("--analysis", type=Path, required=True, help="analysis JSON from analyze")
    score.add_argument("--key", type=Path, required=True, help="scoring key JSON")
    wording = sub.add_parser("score-wording", help="score the wording rules against gold labels")
    wording.add_argument("--db", type=Path, required=True, help="path to hadith-kg.db")
    wording.add_argument("gold", type=Path, nargs="+", help="gold files (eval/gold/chain-wording)")
    wording.add_argument("--show", action="store_true", help="print every disagreement")
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
    from icma.analysis.llm import AnthropicCaller, StructuredCaller
    from icma.analysis.openrouter import OpenRouterCaller
    from icma.analysis.runner import analysis_json
    from icma.analysis.runner import analyze as run_analysis

    tradition, _ = load_corrected(args.db, args.group, args.anchors, args.corrections)
    bundle = bundle_of(tradition)
    caller: StructuredCaller
    if args.provider == "openrouter":
        caller = OpenRouterCaller(
            effort=args.effort, **({"model": args.model} if args.model else {})
        )
    else:
        caller = AnthropicCaller(
            effort=args.effort, **({"model": args.model} if args.model else {})
        )
    result = run_analysis(args.title, tradition, bundle, caller, args.work_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = analysis_json(args.id, result, caller.model)
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


def _database_url(explicit: str | None) -> str:
    url = explicit or os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("no database URL: pass --database-url or set DATABASE_URL_UNPOOLED")
    return url


def migrate(args: argparse.Namespace) -> None:
    import psycopg

    from icma.db import migrate as run_migrations

    with psycopg.connect(_database_url(args.database_url)) as conn:
        ran = run_migrations(conn)
    print(f"applied {len(ran)} migration(s): {', '.join(ran) or 'none pending'}")


def publish(args: argparse.Namespace) -> None:
    import psycopg

    from icma.db import publish as publish_analysis

    payload = json.loads(args.analysis.read_text(encoding="utf-8"))
    with psycopg.connect(_database_url(args.database_url)) as conn:
        analysis_id, created = publish_analysis(conn, payload)
    print(f"analysis {analysis_id} {'published' if created else 'already published'}")


def reviewer(args: argparse.Namespace) -> None:
    import getpass

    import psycopg

    from icma.db import issue_passcode, list_reviewers, remove_reviewer, set_reviewer

    if args.action != "list" and not args.email:
        raise SystemExit("--email is required")
    with psycopg.connect(_database_url(args.database_url)) as conn:
        if args.action in ("add", "passcode"):
            if args.action == "add":
                set_reviewer(conn, args.email, args.role, f"cli:{getpass.getuser()}")
            print(f"passcode for {args.email.strip().lower()}: {issue_passcode(conn, args.email)}")
        elif args.action == "remove" and not remove_reviewer(conn, args.email):
            raise SystemExit(f"{args.email} was not a reviewer")
        for email, role in list_reviewers(conn):
            print(f"{role:9} {email}")


def compare_models(args: argparse.Namespace) -> None:
    from icma.compare import Job, compare, markdown, report_json
    from icma.evaluate import load_key

    tradition, _ = load_corrected(args.db, args.group, args.anchors, args.corrections)
    key = load_key(json.loads(args.key.read_text(encoding="utf-8")))
    job = Job(
        args.id, args.title, tradition, bundle_of(tradition), key, args.work_dir, args.seed_from
    )
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    reports = compare(job, models)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown(reports), encoding="utf-8")
    raw = args.out.with_suffix(".json")
    raw.write_text(json.dumps(report_json(reports), ensure_ascii=False, indent=1), encoding="utf-8")
    print(markdown(reports))


def score_wording(args: argparse.Namespace) -> None:
    from icma.wording_eval import load_gold, load_selection, score

    chains = correct = entries = entries_correct = 0
    for path in args.gold:
        gold = load_gold(path)
        result = score(gold, load_selection(gold, args.db, path.resolve().parents[3]))
        chains, correct = chains + result.chains, correct + result.correct
        entries, entries_correct = (
            entries + result.entries,
            entries_correct + result.entries_correct,
        )
        print(
            f"{path.stem}: {result.correct}/{result.chains} chains, "
            f"{result.entries_correct}/{result.entries} entries fully right"
        )
        for error in result.errors if args.show else []:
            print(
                f"  hadith {error.hadith_id} chain {error.chain_id}: " + "; ".join(error.problems)
            )
    print(f"total: {correct}/{chains} chains, {entries_correct}/{entries} entries fully right")


def main() -> None:
    args = _parser().parse_args()
    if args.command == "export":
        export(args)
    elif args.command == "analyze":
        analyze(args)
    elif args.command == "score":
        score(args)
    elif args.command == "migrate":
        migrate(args)
    elif args.command == "publish":
        publish(args)
    elif args.command == "reviewer":
        reviewer(args)
    elif args.command == "compare-models":
        compare_models(args)
    elif args.command == "score-wording":
        score_wording(args)


if __name__ == "__main__":
    main()
