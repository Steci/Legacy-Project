"""Post-import helpers for GeneWeb databases."""

from __future__ import annotations

from collections.abc import Mapping, Iterator
from typing import Dict, List, Optional, Tuple

from consang.adapters import build_nodes_from_domain, compute_for_domain
from consang.exceptions import AncestralLoopError, ConsanguinityComputationError
from models.family.family import Family as DomainFamily

from .exporter import build_relationship_blocks
from .models import GWDatabase, Person, RelationBlock
from consang.relationship import (
    RelationshipSummary,
    RelationshipInfo,
    build_relationship_info,
    summarize_relationship,
)


def refresh_consanguinity(database: GWDatabase, *, from_scratch: bool = True) -> None:
    """Compute consanguinity coefficients for a parsed GeneWeb database.

    This function mirrors the post-import refresh step performed by the
    original GeneWeb pipeline, keeping the parser itself as a pure text loader.
    """

    database.consanguinity_warnings = []
    database.consanguinity_errors = []

    database.relationship_info = None
    database.relationship_key_to_index = {}
    database.relationship_index_to_key = {}
    database.relationship_summaries = {}

    prepared = _prepare_consanguinity_inputs(database, from_scratch=from_scratch)
    if prepared is None:
        return

    persons, families, index_to_key, key_to_index = prepared
    if not families:
        database.relationship_index_to_key = index_to_key
        database.relationship_key_to_index = key_to_index
        return

    try:
        compute_for_domain(persons, families, from_scratch=from_scratch)
    except AncestralLoopError as exc:
        _handle_consanguinity_loop(database, exc, index_to_key)
        return
    except ConsanguinityComputationError as exc:
        database.consanguinity_errors.append(str(exc))
        return

    database.relationship_index_to_key = index_to_key
    database.relationship_key_to_index = key_to_index

    person_nodes, family_nodes = build_nodes_from_domain(
        persons, families, from_scratch=False
    )
    if person_nodes and family_nodes:
        relationship_info = build_relationship_info(person_nodes, family_nodes)
        database.relationship_info = relationship_info

        pair_map: Dict[Tuple[str, str], Tuple[int, int]] = {}
        for family in families:
            father_id = getattr(family, "parent1", None)
            mother_id = getattr(family, "parent2", None)
            if father_id is None or mother_id is None:
                continue
            if father_id <= 0 or mother_id <= 0:
                continue
            if father_id not in person_nodes or mother_id not in person_nodes:
                continue

            key_a = database.relationship_index_to_key.get(father_id)
            key_b = database.relationship_index_to_key.get(mother_id)
            if not key_a or not key_b:
                continue

            pair_key = (key_a, key_b)
            pair_map.setdefault(pair_key, (father_id, mother_id))

        if pair_map:
            summary_cache = RelationshipSummaryCache(
                relationship_info,
                database.relationship_index_to_key,
                pair_map,
            )
            database.relationship_summaries = summary_cache
            _merge_relationship_blocks(database, summary_cache)


def _prepare_consanguinity_inputs(
    database: GWDatabase,
    *,
    from_scratch: bool,
) -> Optional[
    Tuple[
        List[Person],
        List[DomainFamily],
        Dict[int, str],
        Dict[str, int],
    ]
]:
    if not database.persons or not database.families:
        return None

    ordered_persons = sorted(database.persons.items(), key=lambda item: item[0].lower())

    persons_for_compute: List[Person] = []
    key_to_index: Dict[str, int] = {}
    key_lower_to_index: Dict[str, int] = {}
    index_to_key: Dict[int, str] = {}

    for idx, (key, person) in enumerate(ordered_persons, start=1):
        person.key_index = idx
        person.consanguinity_issue = None
        if from_scratch:
            person.consanguinity = 0.0
            person.consanguinity_known = False
        else:
            person.consanguinity_known = bool(getattr(person, "consanguinity_known", False))
        persons_for_compute.append(person)
        key_to_index[key] = idx
        key_lower_to_index[key.lower()] = idx
        index_to_key[idx] = key

    families_for_compute: List[DomainFamily] = []

    for family_idx, family in enumerate(database.families, start=1):
        child_ids: List[int] = []
        for _, child, _ in family.children:
            if child.key_index is None:
                continue
            child_ids.append(child.key_index)

        if not child_ids:
            continue

        father_id = _lookup_person_index(family.husband, key_to_index, key_lower_to_index)
        mother_id = _lookup_person_index(family.wife, key_to_index, key_lower_to_index)

        if father_id == 0 and mother_id == 0:
            mother_id = -family_idx

        try:
            domain_family = DomainFamily(
                parent1=father_id,
                parent2=mother_id,
                children=child_ids,
                relation=family.relation,
            )
        except ValueError:
            continue

        domain_family.key_index = family_idx
        family.key_index = family_idx
        families_for_compute.append(domain_family)

    return persons_for_compute, families_for_compute, index_to_key, key_to_index


def _lookup_person_index(
    reference: Optional[str],
    key_map: Dict[str, int],
    key_lower_map: Dict[str, int],
) -> int:
    if not reference:
        return 0
    if reference in key_map:
        return key_map[reference]
    lowered = reference.lower()
    return key_lower_map.get(lowered, 0)


def _handle_consanguinity_loop(
    database: GWDatabase,
    exc: AncestralLoopError,
    index_to_key: Dict[int, str],
) -> None:
    cycle_keys: List[str] = []
    for pid in getattr(exc, "cycle", []) or []:
        key = index_to_key.get(pid)
        if not key:
            continue
        cycle_keys.append(key)
        person = database.persons.get(key)
        if person is not None:
            person.consanguinity_issue = "ancestral_loop"

    if not cycle_keys and exc.person_id is not None:
        key = index_to_key.get(exc.person_id)
        if key:
            cycle_keys.append(key)
            person = database.persons.get(key)
            if person is not None:
                person.consanguinity_issue = "ancestral_loop"

    if cycle_keys:
        message = "Skipped consanguinity due to ancestral loop: " + " -> ".join(cycle_keys)
    else:
        message = str(exc)
    database.consanguinity_warnings.append(message)


def _merge_relationship_blocks(
    database: GWDatabase,
    summaries: Mapping[Tuple[str, str], RelationshipSummary],
) -> None:
    if not summaries:
        return

    block_lookup: Dict[str, RelationBlock] = {}
    existing_targets: Dict[str, set[str]] = {}

    for block in database.relations:
        block_lookup[block.person_key] = block
        targets: set[str] = set()
        for line in block.lines:
            target = _extract_relation_target(line)
            if target:
                targets.add(target)
        existing_targets[block.person_key] = targets

    for pair_key in summaries:
        if not isinstance(pair_key, tuple) or len(pair_key) != 2:
            continue
        person_a, person_b = pair_key

        targets_a = existing_targets.setdefault(person_a, set())
        targets_b = existing_targets.setdefault(person_b, set())

        needs_a = person_b not in targets_a
        needs_b = person_a not in targets_b
        if not (needs_a or needs_b):
            continue

        summary = summaries[pair_key]
        summary_blocks = build_relationship_blocks({pair_key: summary})

        for person_key, blocks in summary_blocks.items():
            block = block_lookup.get(person_key)
            if block is None:
                block = RelationBlock(person_key=person_key, lines=[])
                database.relations.append(block)
                block_lookup[person_key] = block
                existing_targets[person_key] = set()

            targets = existing_targets.setdefault(person_key, set())

            for block_lines in blocks:
                if not block_lines:
                    continue
                target = _extract_relation_target(block_lines[0])
                if target and target in targets:
                    continue
                if block.lines and block.lines[-1].strip():
                    block.lines.append("")
                block.lines.extend(block_lines)
                if target:
                    targets.add(target)


def _extract_relation_target(line: str) -> Optional[str]:
    candidate = (line or "").strip()
    lower = candidate.lower()
    if not lower.startswith("- rel"):
        return None
    _, _, remainder = candidate.partition(":")
    target = remainder.strip()
    if not target:
        return None
    target = target.split(" coef", 1)[0].strip()
    return target or None


class RelationshipSummaryCache(Mapping[Tuple[str, str], RelationshipSummary]):
    def __init__(
        self,
        relationship_info: "RelationshipInfo",
        index_to_key: Dict[int, str],
        pairs: Dict[Tuple[str, str], Tuple[int, int]],
    ) -> None:
        self._relationship_info = relationship_info
        self._index_to_key = index_to_key
        self._pairs = dict(pairs)
        self._keys: Tuple[Tuple[str, str], ...] = tuple(sorted(self._pairs.keys()))
        self._cache: Dict[Tuple[str, str], RelationshipSummary] = {}

    def __getitem__(self, key: Tuple[str, str]) -> RelationshipSummary:
        if key not in self._pairs:
            raise KeyError(key)
        if key not in self._cache:
            person_a_id, person_b_id = self._pairs[key]
            summary = summarize_relationship(
                self._relationship_info,
                person_a_id,
                person_b_id,
                self._index_to_key,
            )
            self._cache[key] = summary
        return self._cache[key]

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._pairs)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, tuple) and key in self._pairs

