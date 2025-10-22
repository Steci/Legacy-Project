"""Post-import helpers for GeneWeb databases."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from consang.adapters import compute_for_domain
from consang.exceptions import AncestralLoopError, ConsanguinityComputationError
from models.family.family import Family as DomainFamily

from .models import GWDatabase, Person


def refresh_consanguinity(database: GWDatabase, *, from_scratch: bool = True) -> None:
    """Compute consanguinity coefficients for a parsed GeneWeb database.

    This function mirrors the post-import refresh step performed by the
    original GeneWeb pipeline, keeping the parser itself as a pure text loader.
    """

    database.consanguinity_warnings = []
    database.consanguinity_errors = []

    prepared = _prepare_consanguinity_inputs(database, from_scratch=from_scratch)
    if prepared is None:
        return

    persons, families, index_to_key = prepared
    if not families:
        return

    try:
        compute_for_domain(persons, families, from_scratch=from_scratch)
    except AncestralLoopError as exc:
        _handle_consanguinity_loop(database, exc, index_to_key)
    except ConsanguinityComputationError as exc:
        database.consanguinity_errors.append(str(exc))


def _prepare_consanguinity_inputs(
    database: GWDatabase,
    *,
    from_scratch: bool,
) -> Optional[Tuple[List[Person], List[DomainFamily], Dict[int, str]]]:
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

    return persons_for_compute, families_for_compute, index_to_key


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
