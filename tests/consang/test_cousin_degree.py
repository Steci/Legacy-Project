from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional

import pytest

from consang.relationship import BranchPath, RelationshipSummary

from consang.cousin_degree import (
    CousinComputationSettings,
    CousinDegree,
    CousinListing,
    CousinMatrixEntry,
    CousinTerminology,
    PersonTemporalData,
    RelationshipKind,
    clear_cousin_degree_cache,
    get_cousin_degree_settings,
    build_cousin_listings,
    build_cousin_matrix,
    build_default_spouse_lookup,
    describe_cousin_degree,
    format_cousin_listing,
    format_cousin_listings,
    infer_all_cousin_degrees,
    infer_cousin_degree,
    load_cousin_settings,
    set_cousin_degree_settings,
)
from models.date import Precision


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "consang" / "cousin_degrees"
GOLDEN_CASES = json.loads((FIXTURE_DIR / "simple_cases.json").read_text(encoding="utf-8"))


def _summary_for(
    *,
    ancestor: str,
    length_a: int,
    length_b: int,
    person_a: str = "Person A",
    person_b: str = "Person B",
    path_a_nodes: tuple[str, ...] | None = None,
    path_b_nodes: tuple[str, ...] | None = None,
) -> RelationshipSummary:
    if path_a_nodes is None:
        path_a_nodes = tuple(f"A{i}" for i in range(length_a - 1))
    if path_b_nodes is None:
        path_b_nodes = tuple(f"B{i}" for i in range(length_b - 1))

    path_a = (ancestor, *path_a_nodes, person_a) if length_a else (ancestor,)
    path_b = (ancestor, *path_b_nodes, person_b) if length_b else (ancestor,)

    branch_a = BranchPath(length=length_a, multiplicity=1, path=path_a)
    branch_b = BranchPath(length=length_b, multiplicity=1, path=path_b)

    return RelationshipSummary(
        person_a=person_a,
        person_b=person_b,
        coefficient=0.0,
        ancestors=(ancestor,),
        paths_to_a={ancestor: (branch_a,)},
        paths_to_b={ancestor: (branch_b,)},
    )


def _summary_from_case(case: Dict[str, Any]) -> RelationshipSummary:
    ancestors = case.get("ancestors", [])
    if not ancestors:
        return RelationshipSummary(
            person_a=case["person_a"],
            person_b=case["person_b"],
            coefficient=0.0,
            ancestors=(),
            paths_to_a={},
            paths_to_b={},
        )

    paths_to_a: Dict[str, tuple[BranchPath, ...]] = {}
    paths_to_b: Dict[str, tuple[BranchPath, ...]] = {}

    for ancestor in ancestors:
        name = ancestor["name"]
        length_a = ancestor["length_a"]
        length_b = ancestor["length_b"]

        path_a = _build_branch_path(name, case["person_a"], length_a)
        path_b = _build_branch_path(name, case["person_b"], length_b)

        paths_to_a[name] = (path_a,)
        paths_to_b[name] = (path_b,)

    ancestor_names = tuple(ancestor["name"] for ancestor in ancestors)

    return RelationshipSummary(
        person_a=case["person_a"],
        person_b=case["person_b"],
        coefficient=0.0,
        ancestors=ancestor_names,
        paths_to_a=paths_to_a,
        paths_to_b=paths_to_b,
    )


def _build_branch_path(ancestor: str, person: str, length: int) -> BranchPath:
    if length <= 0:
        path = (ancestor,)
    else:
        intermediates = tuple(f"{ancestor}->{person}#{index}" for index in range(length - 1))
        path = (ancestor, *intermediates, person)
    return BranchPath(length=length, multiplicity=1, path=path)


def test_unrelated_when_no_ancestors() -> None:
    summary = RelationshipSummary(
        person_a="A",
        person_b="B",
        coefficient=0.0,
        ancestors=(),
        paths_to_a={},
        paths_to_b={},
    )

    all_results = infer_all_cousin_degrees(summary)
    result = infer_cousin_degree(summary)

    assert all_results == []
    assert result.kind is RelationshipKind.UNRELATED
    assert describe_cousin_degree(result) == "unrelated"


def test_self_relationship_detected() -> None:
    summary = _summary_for(ancestor="Same", length_a=0, length_b=0, person_a="P", person_b="P")

    all_results = infer_all_cousin_degrees(summary)
    result = infer_cousin_degree(summary)

    assert len(all_results) == 1
    assert all_results[0].kind is RelationshipKind.SELF
    assert result.kind is RelationshipKind.SELF
    assert describe_cousin_degree(result) == "same person"


def test_siblings_detected() -> None:
    summary = _summary_for(ancestor="Parent", length_a=1, length_b=1, person_a="Alice", person_b="Bob")

    all_results = infer_all_cousin_degrees(summary)
    result = infer_cousin_degree(summary)

    assert len(all_results) == 1
    assert result.kind is RelationshipKind.SIBLING
    assert describe_cousin_degree(result) == "siblings"


def test_half_siblings_detected_with_extra_paths() -> None:
    summary = RelationshipSummary(
        person_a="Hannah",
        person_b="Ian",
        coefficient=0.0,
        ancestors=("Shared Parent",),
        paths_to_a={
            "Shared Parent": (
                BranchPath(length=1, multiplicity=1, path=("Shared Parent", "Hannah")),
            )
        },
        paths_to_b={
            "Shared Parent": (
                BranchPath(length=1, multiplicity=1, path=("Shared Parent", "Ian")),
                BranchPath(length=2, multiplicity=1, path=("Shared Parent", "Step", "Ian")),
            )
        },
    )

    result = infer_cousin_degree(summary)

    assert result.kind is RelationshipKind.SIBLING
    assert describe_cousin_degree(result) == "siblings"


def test_first_cousins_detected() -> None:
    summary = _summary_for(ancestor="Grandparent", length_a=2, length_b=2)

    result = infer_cousin_degree(summary)

    assert result.kind is RelationshipKind.COUSIN
    assert result.degree == 1
    assert result.removal == 0
    assert describe_cousin_degree(result) == "first cousins"


def test_first_cousins_once_removed_detected() -> None:
    summary = _summary_for(ancestor="Grandparent", length_a=2, length_b=3)

    result = infer_cousin_degree(summary)

    assert result.kind is RelationshipKind.COUSIN
    assert result.degree == 1
    assert result.removal == 1
    assert describe_cousin_degree(result) == "first cousins once removed"


def test_direct_ancestor_detected() -> None:
    summary = _summary_for(ancestor="Parent", length_a=1, length_b=0)

    result = infer_cousin_degree(summary)

    assert result.kind is RelationshipKind.DIRECT_ANCESTOR
    assert result.generations_a == 1
    assert result.generations_b == 0
    assert "ancestor" in describe_cousin_degree(result)


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda entry: entry["name"])
def test_golden_master_cases(case: Dict[str, Any]) -> None:
    summary = _summary_from_case(case)
    result = infer_cousin_degree(summary)

    expected_kind = RelationshipKind[case["expected_kind"]]
    assert result.kind is expected_kind
    assert describe_cousin_degree(result) == case["expected_description"]


def test_prefers_closest_common_ancestor() -> None:
    summary = RelationshipSummary(
        person_a="A",
        person_b="B",
        coefficient=0.0,
        ancestors=("Grandparent", "GreatGrandparent"),
        paths_to_a={
            "Grandparent": (BranchPath(length=2, multiplicity=1, path=("Grandparent", "Parent", "A")),),
            "GreatGrandparent": (BranchPath(length=3, multiplicity=1, path=("GreatGrandparent", "Ancestor", "Parent", "A")),),
        },
        paths_to_b={
            "Grandparent": (BranchPath(length=2, multiplicity=1, path=("Grandparent", "Parent", "B")),),
            "GreatGrandparent": (BranchPath(length=3, multiplicity=1, path=("GreatGrandparent", "Ancestor", "Parent", "B")),),
        },
    )

    all_results = infer_all_cousin_degrees(summary)
    result = infer_cousin_degree(summary)

    assert len(all_results) == 2
    assert all_results[0].ancestor == "Grandparent"
    assert all_results[1].ancestor == "GreatGrandparent"
    assert result.kind is RelationshipKind.COUSIN
    assert result.degree == 1
    assert result.ancestor == "Grandparent"


def test_prefers_shortest_paths_per_common_ancestor() -> None:
    summary = RelationshipSummary(
        person_a="Liam",
        person_b="Mia",
        coefficient=0.0,
        ancestors=("Ancestor",),
        paths_to_a={
            "Ancestor": (
                BranchPath(length=3, multiplicity=1, path=("Ancestor", "X", "Y", "Liam")),
                BranchPath(length=2, multiplicity=1, path=("Ancestor", "Y", "Liam")),
            )
        },
        paths_to_b={
            "Ancestor": (
                BranchPath(length=4, multiplicity=1, path=("Ancestor", "A1", "A2", "A3", "Mia")),
                BranchPath(length=2, multiplicity=1, path=("Ancestor", "A", "Mia")),
            )
        },
    )

    result = infer_cousin_degree(summary)

    assert result.kind is RelationshipKind.COUSIN
    assert result.generations_a == 2
    assert result.generations_b == 2


def test_cousin_matrix_collects_unique_path_pairs() -> None:
    ancestor = "Ancestor"
    path_a_short = _build_branch_path(ancestor, "A", 2)
    path_a_long = _build_branch_path(ancestor, "A", 3)
    path_b_short = _build_branch_path(ancestor, "B", 2)
    # Duplicate entry to ensure pruning works
    path_b_dup = BranchPath(length=2, multiplicity=1, path=path_b_short.path)

    summary = RelationshipSummary(
        person_a="A",
        person_b="B",
        coefficient=0.0,
        ancestors=(ancestor,),
        paths_to_a={ancestor: (path_a_short, path_a_long)},
        paths_to_b={ancestor: (path_b_short, path_b_dup)},
    )

    matrix = build_cousin_matrix(summary)

    assert 2 in matrix and 3 in matrix
    assert 2 in matrix[2]
    entries_short = matrix[2][2]
    assert len(entries_short) == 1
    entry = entries_short[0]
    assert isinstance(entry, CousinMatrixEntry)
    assert entry.ancestor == ancestor
    assert entry.degree.kind is RelationshipKind.COUSIN

    entries_mixed = matrix[3][2]
    assert len(entries_mixed) == 1
    assert entries_mixed[0].degree.generations_a == 3


def test_cousin_matrix_respects_depth_limits() -> None:
    ancestor = "Ancestor"
    summary = RelationshipSummary(
        person_a="A",
        person_b="B",
        coefficient=0.0,
        ancestors=(ancestor,),
        paths_to_a={ancestor: (_build_branch_path(ancestor, "A", 3),)},
        paths_to_b={ancestor: (_build_branch_path(ancestor, "B", 2),)},
    )

    limited = build_cousin_matrix(summary, max_depth_a=2)
    assert limited == {}

    unlimited = build_cousin_matrix(summary, max_depth_a=3)
    assert 3 in unlimited and 2 in unlimited[3]


def test_cousin_matrix_cache_reuses_results() -> None:
    clear_cousin_degree_cache()
    summary = _summary_for(ancestor="Ancestor", length_a=2, length_b=3)

    first = build_cousin_matrix(summary)
    second = build_cousin_matrix(summary)

    assert first is second

    clear_cousin_degree_cache()

    rebuilt = build_cousin_matrix(summary)
    assert rebuilt is not first
    assert rebuilt == first

    uncached = build_cousin_matrix(summary, use_cache=False)
    assert uncached is not rebuilt
    assert uncached == rebuilt


def test_settings_from_env_supports_geneweb_knobs(tmp_path: Path) -> None:
    env = {
        "max_anc_level": "5",
        "max_desc_level": "4",
        "max_cousins_level": "3",
        "max_cousins": "100",
        "cache_cousins_tool": "yes",
    }

    settings = load_cousin_settings(env, base_path=tmp_path)

    assert settings.max_depth_a == 3
    assert settings.max_depth_b == 3
    assert settings.max_results == 100
    assert settings.cache_enabled is True
    assert settings.cache_directory == tmp_path


def test_module_settings_control_depth_and_disk_cache(tmp_path: Path) -> None:
    summary = _summary_for(ancestor="Ancestor", length_a=3, length_b=3)

    original = get_cousin_degree_settings()
    limited_settings = CousinComputationSettings(
        max_depth_a=1,
        max_depth_b=1,
        max_results=None,
        cache_enabled=False,
        cache_directory=None,
        cache_prefix=original.cache_prefix,
        cache_version=original.cache_version,
    )
    disk_settings = CousinComputationSettings(
        max_depth_a=4,
        max_depth_b=4,
        max_results=None,
        cache_directory=tmp_path,
        cache_enabled=True,
        cache_prefix=original.cache_prefix,
        cache_version=original.cache_version,
    )

    try:
        set_cousin_degree_settings(limited_settings)
        clear_cousin_degree_cache()
        assert build_cousin_matrix(summary) == {}

        set_cousin_degree_settings(disk_settings)
        clear_cousin_degree_cache(include_disk=True, settings=disk_settings)
        matrix = build_cousin_matrix(summary)
        assert matrix

        cache_files = list(tmp_path.glob(f"{disk_settings.cache_prefix}-*.pkl"))
        assert cache_files

        cached_again = build_cousin_matrix(summary)
        assert cached_again is matrix
    finally:
        set_cousin_degree_settings(original)
        clear_cousin_degree_cache(include_disk=True, settings=disk_settings)


def test_cousin_listings_include_descendants_spouses_and_temporal_ranges() -> None:
    ancestor = "Ancestor"
    path_a = BranchPath(length=2, multiplicity=1, path=(ancestor, "ParentA", "ChildA"))
    path_b = BranchPath(length=2, multiplicity=1, path=(ancestor, "ParentB", "ChildB"))

    summary = RelationshipSummary(
        person_a="ChildA",
        person_b="ChildB",
        coefficient=0.0,
        ancestors=(ancestor,),
        paths_to_a={ancestor: (path_a,)},
        paths_to_b={ancestor: (path_b,)},
    )

    def fake_spouses(person: str) -> list[str]:
        return {"ChildA": ["PartnerA"], "ChildB": ["PartnerB", "PartnerB"]}.get(person, [])

    def fake_temporal(person: str) -> Optional[PersonTemporalData]:
        data = {
            "Ancestor": PersonTemporalData(
                birth_year=1820,
                birth_precision=Precision.SURE,
                death_year=1890,
                death_precision=Precision.SURE,
                is_alive=False,
            ),
            "ParentA": PersonTemporalData(
                birth_year=1850,
                birth_precision=Precision.SURE,
                death_year=1920,
                death_precision=Precision.SURE,
                is_alive=False,
            ),
            "ParentB": PersonTemporalData(
                birth_year=1855,
                birth_precision=Precision.SURE,
                death_year=1915,
                death_precision=Precision.SURE,
                is_alive=False,
            ),
            "ChildA": PersonTemporalData(
                birth_year=1880,
                birth_precision=Precision.SURE,
                death_year=1950,
                death_precision=Precision.SURE,
                is_alive=False,
            ),
            "ChildB": PersonTemporalData(
                birth_year=1885,
                birth_precision=Precision.SURE,
                death_year=1960,
                death_precision=Precision.SURE,
                is_alive=False,
            ),
        }
        return data.get(person)

    listings = build_cousin_listings(
        summary,
        spouse_lookup=fake_spouses,
        temporal_lookup=fake_temporal,
    )

    assert len(listings) == 1
    listing = listings[0]
    assert isinstance(listing, CousinListing)
    assert listing.descendants_a == ("ParentA", "ChildA")
    assert listing.descendants_b == ("ParentB", "ChildB")
    assert listing.spouses_a == ("PartnerA",)
    assert listing.spouses_b == ("PartnerB",)
    assert listing.birth_year_range == (1820, 1885)
    assert listing.death_year_range == (1890, 1960)


def test_temporal_aggregation_handles_fuzzy_and_living_data() -> None:
    ancestor = "Ancestor"
    path_a = BranchPath(length=2, multiplicity=1, path=(ancestor, "ParentA", "ChildA"))
    path_b = BranchPath(length=2, multiplicity=1, path=(ancestor, "ParentB", "ChildB"))

    summary = RelationshipSummary(
        person_a="ChildA",
        person_b="ChildB",
        coefficient=0.0,
        ancestors=(ancestor,),
        paths_to_a={ancestor: (path_a,)},
        paths_to_b={ancestor: (path_b,)},
    )

    current_year = datetime.now(timezone.utc).year

    def temporal_lookup(person: str) -> Optional[PersonTemporalData]:
        mapping = {
            "Ancestor": PersonTemporalData(
                birth_year=1820,
                birth_precision=Precision.SURE,
                death_year=None,
                death_precision=None,
                is_alive=True,
            ),
            "ParentA": PersonTemporalData(
                birth_year=1850,
                birth_precision=Precision.SURE,
                death_year=1930,
                death_precision=Precision.SURE,
                is_alive=False,
            ),
            "ParentB": PersonTemporalData(
                birth_year=1855,
                birth_precision=Precision.SURE,
                death_year=1935,
                death_precision=Precision.BEFORE,
                is_alive=False,
            ),
            "ChildA": PersonTemporalData(
                birth_year=1980,
                birth_precision=Precision.SURE,
                death_year=None,
                death_precision=None,
                is_alive=True,
            ),
            "ChildB": PersonTemporalData(
                birth_year=1985,
                birth_precision=Precision.ABOUT,
                death_year=None,
                death_precision=None,
                is_alive=True,
            ),
        }
        return mapping.get(person)

    listings = build_cousin_listings(summary, temporal_lookup=temporal_lookup)
    assert listings
    listing = listings[0]

    assert listing.birth_year_range == (1820, 1980)
    assert listing.death_year_range == (1930, current_year)


def test_format_cousin_listing_uses_paths_and_spouses() -> None:
    ancestor = "Ancestor"
    degree = CousinDegree(
        kind=RelationshipKind.COUSIN,
        degree=1,
        removal=0,
        generations_a=2,
        generations_b=2,
        ancestor=ancestor,
    )
    path_a = BranchPath(length=2, multiplicity=1, path=(ancestor, "ParentA", "ChildA"))
    path_b = BranchPath(length=2, multiplicity=1, path=(ancestor, "ParentB", "ChildB"))
    listing = CousinListing(
        ancestor=ancestor,
        degree=degree,
        path_to_a=path_a,
        path_to_b=path_b,
        descendants_a=("ParentA", "ChildA"),
        descendants_b=("ParentB", "ChildB"),
        spouses_a=("PartnerA",),
        spouses_b=(),
        birth_year_range=None,
        death_year_range=None,
    )

    formatted = format_cousin_listing(listing)
    assert "Ancestor" in formatted
    assert "ParentA" in formatted and "ChildA" in formatted
    assert "spouses: PartnerA" in formatted
    assert "spouses: none" in formatted

    formatted_many = format_cousin_listings([listing])
    assert formatted_many == [formatted]


def test_format_cousin_listing_includes_temporal_segments() -> None:
    listing = CousinListing(
        ancestor="Ancestor",
        degree=CousinDegree(kind=RelationshipKind.COUSIN, degree=2, removal=0),
        path_to_a=BranchPath(length=2, multiplicity=1, path=("Ancestor", "ParentA", "ChildA")),
        path_to_b=BranchPath(length=2, multiplicity=1, path=("Ancestor", "ParentB", "ChildB")),
        descendants_a=("ParentA", "ChildA"),
        descendants_b=("ParentB", "ChildB"),
        spouses_a=(),
        spouses_b=(),
        birth_year_range=(1850, 1880),
        death_year_range=(1900, 1950),
    )

    formatted = format_cousin_listing(listing)
    assert "birth years: 1850-1880" in formatted
    assert "death years: 1900-1950" in formatted


def test_build_default_spouse_lookup_derives_partners() -> None:
    persons = {
        "Alice": SimpleNamespace(key_index=1),
        "Bob": SimpleNamespace(key_index=2),
        "Charlie": SimpleNamespace(key_index=3),
    }

    families = [
        SimpleNamespace(husband="Alice", wife="Bob", parent1=None, parent2=None),
        SimpleNamespace(husband=None, wife=None, parent1=3, parent2=2),
    ]

    database = SimpleNamespace(
        persons=persons,
        families=families,
        relationship_index_to_key={1: "Alice", 2: "Bob", 3: "Charlie"},
    )

    lookup = build_default_spouse_lookup(database)
    assert lookup is not None
    assert lookup("Alice") == ("Bob",)
    assert set(lookup("Bob")) == {"Alice", "Charlie"}
    assert lookup("Charlie") == ("Bob",)


@pytest.mark.parametrize(
    "degree, expected",
    [
        (1, "first cousins"),
        (2, "second cousins"),
        (3, "third cousins"),
    ],
)
def test_formatter_handles_degrees(degree: int, expected: str) -> None:
    result = CousinDegree(
        kind=RelationshipKind.COUSIN,
        degree=degree,
        removal=0,
        generations_a=degree + 1,
        generations_b=degree + 1,
        ancestor="Ancestor",
    )

    assert describe_cousin_degree(result) == expected


def test_formatter_handles_removal_text() -> None:
    result = CousinDegree(
        kind=RelationshipKind.COUSIN,
        degree=2,
        removal=2,
        generations_a=4,
        generations_b=2,
        ancestor="Ancestor",
    )

    assert describe_cousin_degree(result) == "second cousins twice removed"


def test_formatter_supports_custom_terminology() -> None:
    terminology = CousinTerminology(
        self_label="même personne",
        siblings_label="frères et sœurs",
        unrelated_label="sans lien",
        ancestor_descendant_label="ancêtre/descendant",
        ancestor_descendant_generations="ancêtre/descendant ({distance} générations)",
        cousin_generic_label="cousins",
        cousin_phrase_template="{ordinal} cousins",
        removal_joiner=" ",
        ordinal_fn=lambda degree: {1: "premiers", 2: "seconds"}.get(degree, f"{degree}e") ,
        removal_fn=lambda removal: {1: "une fois retirés"}.get(removal, f"{removal} fois retirés"),
    )

    result = CousinDegree(
        kind=RelationshipKind.COUSIN,
        degree=1,
        removal=1,
        generations_a=2,
        generations_b=2,
        ancestor="Ancestor",
    )

    description = describe_cousin_degree(result, terminology=terminology)
    assert "premiers" in description
    assert "une fois retirés" in description
