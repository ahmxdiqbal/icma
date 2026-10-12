from icma.bundle import (
    PROPHET,
    Bundle,
    NodeStats,
    Path,
    branch_groups,
    build_bundle,
    key_figures,
    label_of,
    to_paths,
)
from icma.models import Chain, GapKind, GapLink, NarratorLink


def paths(*rows: str) -> list[Path]:
    """Each row is 'a>b>c' (top-down); chain ids are the row numbers starting at 1."""
    return [Path(i, tuple(row.split(">"))) for i, row in enumerate(rows, start=1)]


def node(bundle: Bundle, key: str) -> NodeStats:
    return next(n for n in bundle.nodes if n.key == key)


# A textbook bundle: companion C -> X -> CL, then two PCLs each fanning to collectors.
CLASSIC = (
    "prophet>C>X>CL>P1>a>col1",
    "prophet>C>X>CL>P1>b>col2",
    "prophet>C>X>CL>P2>c>col3",
    "prophet>C>X>CL>P2>d>col4",
)


def test_classic_bundle_finds_cl_below_single_strand() -> None:
    bundle = build_bundle(paths(*CLASSIC))
    assert bundle.suggested_cl == "CL"
    assert bundle.cl_candidates == ("CL",)
    assert node(bundle, "X").independent_branch_count == 1
    assert node(bundle, "CL").corroborated_branch_count == 2


def test_pcl_fanning_to_collectors_teachers_is_not_a_spider() -> None:
    bundle = build_bundle(paths(*CLASSIC))
    p1 = node(bundle, "P1")
    assert (p1.independent_branch_count, p1.single_strand_branch_count) == (2, 0)
    assert bundle.spiders == ()


def test_direct_attestations_are_not_strands() -> None:
    bundle = build_bundle(paths("prophet>C>P>col1", "prophet>C>P>col2"))
    p = node(bundle, "P")
    assert (p.independent_branch_count, p.single_strand_branch_count) == (2, 0)
    assert bundle.spiders == ()


def test_spider_has_only_single_strands() -> None:
    bundle = build_bundle(
        paths("prophet>C>S>a1>a2>col1", "prophet>C>S>b1>b2>col2", "prophet>C>S>d1>d2>col3")
    )
    assert bundle.spiders == ("S",)
    assert bundle.cl_candidates == ()
    assert bundle.suggested_cl is None


def test_branches_that_reconverge_are_one_line() -> None:
    # The 'Ubada shape: two names above H, everything funnels through H.
    bundle = build_bundle(
        paths(
            "prophet>C>A>H>P1>a>col1",
            "prophet>C>A>H>P1>b>col2",
            "prophet>C>B>H>P2>c>col3",
            "prophet>C>B>H>P2>d>col4",
        )
    )
    assert node(bundle, "C").independent_branch_count == 1
    assert bundle.suggested_cl == "H"


def test_meeting_only_at_the_collector_keeps_lines_independent() -> None:
    bundle = build_bundle(
        paths(
            "prophet>N>a>x>Ahmad",
            "prophet>N>a>y>Ahmad",
            "prophet>N>b>z>Ahmad",
            "prophet>N>b>w>Ahmad",
        )
    )
    assert node(bundle, "N").independent_branch_count == 2
    assert bundle.suggested_cl == "N"


def test_shared_mid_chain_transmitter_joins_lines() -> None:
    bundle = build_bundle(paths("prophet>N>a>Q>x>col1", "prophet>N>b>Q>y>col2"))
    assert node(bundle, "N").independent_branch_count == 1


def test_dive_bypasses_cl_and_reports_where_it_rejoins() -> None:
    bundle = build_bundle(paths(*CLASSIC, "prophet>C>X>P1>e>col5"))
    assert bundle.suggested_cl == "CL"
    assert len(bundle.dives) == 1
    dive = bundle.dives[0]
    assert (dive.chain_id, dive.departs_from, dive.rejoins_at) == (5, "X", "P1")


def test_dive_that_never_rejoins() -> None:
    bundle = build_bundle(paths(*CLASSIC, "prophet>C>other>col9"))
    assert [(d.departs_from, d.rejoins_at) for d in bundle.dives] == [("C", None)]


def test_chains_from_unrelated_authorities_are_not_dives() -> None:
    bundle = build_bundle(paths(*CLASSIC, "prophet>D>y>col9"))
    assert bundle.dives == ()


def test_upper_paths_group_gaps_by_kind() -> None:
    bundle = build_bundle(
        paths(
            *CLASSIC,
            "prophet>C>g:inqita:5:1>CL>P1>a>col1",
            "prophet>C>g:inqita:6:1>CL>P2>c>col3",
        )
    )
    assert [(u.labels, u.chain_ids) for u in bundle.upper_paths] == [
        ((PROPHET, "C", "X"), (1, 2, 3, 4)),
        ((PROPHET, "C", "g:inqita"), (5, 6)),
    ]


def test_reversed_edges_are_warned() -> None:
    bundle = build_bundle(paths("prophet>A>B>col1", "prophet>B>A>col2"))
    assert [w.code for w in bundle.warnings] == ["reversed_edge"]
    assert bundle.warnings[0].chain_ids == (1, 2)


def test_edges_carry_their_chain_ids() -> None:
    bundle = build_bundle(paths(*CLASSIC))
    edge = next(e for e in bundle.edges if (e.source, e.target) == ("CL", "P1"))
    assert edge.chain_ids == (1, 2)


def test_to_paths_prefixes_prophet_and_keeps_gaps_unique() -> None:
    chains = [
        Chain(1, 10, "", (NarratorLink(7), GapLink(GapKind.MUBHAM), NarratorLink(9))),
        Chain(2, 11, "", (NarratorLink(7), GapLink(GapKind.MUBHAM), NarratorLink(9))),
        Chain(3, 12, "", (NarratorLink(7), NarratorLink(9))),
    ]
    result, warnings = to_paths(chains, prophetic_chain_ids={1, 2})
    assert warnings == []
    assert result[0].keys == (PROPHET, "n:7", "g:mubham:1:1", "n:9")
    assert result[1].keys[2] == "g:mubham:2:1"
    assert result[2].keys == ("n:7", "n:9")
    assert label_of(result[0].keys[2]) == "g:mubham"


def test_to_paths_excludes_repeated_narrators_and_short_chains() -> None:
    chains = [
        Chain(1, 10, "", (NarratorLink(7), NarratorLink(8), NarratorLink(7))),
        Chain(2, 11, "", (NarratorLink(7),)),
    ]
    result, warnings = to_paths(chains, prophetic_chain_ids=set())
    assert result == []
    assert [(w.code, w.chain_ids) for w in warnings] == [
        ("repeated_narrator", (1,)),
        ("too_short", (2,)),
    ]


def test_unnamed_links_never_merge_lines() -> None:
    bundle = build_bundle(paths("prophet>N>g:mubham:1:2>x>col1", "prophet>N>g:mubham:2:2>y>col2"))
    assert node(bundle, "N").independent_branch_count == 2


def test_empty_bundle() -> None:
    bundle = build_bundle([])
    assert (bundle.nodes, bundle.suggested_cl, bundle.dives) == ((), None, ())


def test_branch_groups_list_independent_lines_largest_first() -> None:
    groups = branch_groups(paths(*CLASSIC, "prophet>C>X>CL>Q>r>s>col9"), "CL")
    assert [(g.student_keys, g.chain_ids, g.kind) for g in groups] == [
        (("P1",), (1, 2), "corroborated"),
        (("P2",), (3, 4), "corroborated"),
        (("Q",), (5,), "single_strand"),
    ]


def test_branch_groups_merge_students_that_reconverge() -> None:
    groups = branch_groups(paths("prophet>C>A>H>x>c1", "prophet>C>B>H>y>c2", "prophet>C>D>c3"), "C")
    assert [(g.student_keys, g.kind) for g in groups] == [
        (("A", "B"), "corroborated"),
        (("D",), "direct"),
    ]


def test_branch_groups_of_unknown_node_is_empty() -> None:
    assert branch_groups(paths(*CLASSIC), "nobody") == []


def test_key_figures_include_direct_attestations_that_strict_rule_misses() -> None:
    bundle = build_bundle(paths(*CLASSIC, "prophet>C>X>Q>col5", "prophet>C>X>Q>col6"))
    figures = [s.key for s in key_figures(bundle.nodes)]
    assert "Q" in figures
    assert "Q" not in bundle.cl_candidates
    # X now fans out to two disjoint lines (via CL and via Q), so it is a key figure as well.
    assert figures[:2] == ["X", "CL"]
