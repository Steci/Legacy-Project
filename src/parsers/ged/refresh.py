"""Post-conversion helpers for GEDCOM databases."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from consang import compute_for_domain
from consang.exceptions import AncestralLoopError, ConsanguinityComputationError

from models.person.person import Person

from parsers.common.consanguinity_paths import (
    build_relationship_graph,
    populate_relationship_paths,
)

if TYPE_CHECKING:
    from models.family.family import Family as DomainFamily
from .conversion import GedcomParsedDatabase


def refresh_consanguinity(database: GedcomParsedDatabase) -> None:
    """Compute consanguinity coefficients for a converted GEDCOM database."""

    database.consanguinity_warnings = []
    database.consanguinity_errors = []

    if not database.individuals or not database.families:
        return

    persons = list(database.individuals.values())
    families = list(database.families.values())

    index_to_person: Dict[int, Person] = {}
    for person in persons:
        person.consanguinity = 0.0
        person.consanguinity_issue = None
        person.consanguinity_path = None
        if person.key_index is not None:
            index_to_person[person.key_index] = person

    child_parent_map = _build_child_parent_index_map(families)

    try:
        compute_for_domain(persons, families, from_scratch=True)
    except AncestralLoopError as exc:
        _handle_consanguinity_loop(database, exc, index_to_person)
    except ConsanguinityComputationError as exc:
        database.consanguinity_errors.append(str(exc))
    else:
        graph = build_relationship_graph(families)

        def _label_for_person_id(person_id: int) -> Optional[str]:
            person = index_to_person.get(person_id)
            if person is None:
                return None
            return _person_display_key(person)

        populate_relationship_paths(
            graph=graph,
            child_parent_map=child_parent_map,
            person_lookup=index_to_person,
            label_for_person_id=_label_for_person_id,
        )


def _handle_consanguinity_loop(
    database: GedcomParsedDatabase,
    exc: AncestralLoopError,
    index_to_person: Dict[int, Person],
) -> None:
    cycle_keys: List[str] = []
    for person_id in getattr(exc, "cycle", []) or []:
        person = index_to_person.get(person_id)
        if person is None:
            continue
        cycle_keys.append(_person_display_key(person))
        person.consanguinity_issue = "ancestral_loop"

    if not cycle_keys and exc.person_id is not None:
        person = index_to_person.get(exc.person_id)
        if person is not None:
            cycle_keys.append(_person_display_key(person))
            person.consanguinity_issue = "ancestral_loop"

    if cycle_keys:
        database.consanguinity_warnings.append(
            "Skipped consanguinity due to ancestral loop: " + " -> ".join(cycle_keys)
        )
    else:
        database.consanguinity_warnings.append(str(exc))


def _person_display_key(person: Person) -> str:
    key = getattr(person, "xref_id", None)
    if key:
        return str(key)
    surname = getattr(person, "surname", "?") or "?"
    first = getattr(person, "first_name", "0") or "0"
    return f"{surname} {first}".strip()


def _build_child_parent_index_map(
    families: List["DomainFamily"],
) -> Dict[int, Tuple[int, int]]:
    child_parent: Dict[int, Tuple[int, int]] = {}

    for family in families:
        father_id = getattr(family, "parent1", 0) or 0
        mother_id = getattr(family, "parent2", 0) or 0
        for child_id in getattr(family, "children", []):
            if not isinstance(child_id, int):
                continue
            child_parent[child_id] = (father_id, mother_id)

    return child_parent
