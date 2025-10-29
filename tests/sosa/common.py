from __future__ import annotations

from consang.models import FamilyNode, PersonNode


def build_simple_tree():
    persons = {
        1: PersonNode(person_id=1, parent_family_id=1),
        2: PersonNode(person_id=2, parent_family_id=2),
        3: PersonNode(person_id=3, parent_family_id=3),
        4: PersonNode(person_id=4, parent_family_id=None),
        5: PersonNode(person_id=5, parent_family_id=None),
        6: PersonNode(person_id=6, parent_family_id=None),
        7: PersonNode(person_id=7, parent_family_id=None),
    }
    families = {
        1: FamilyNode(family_id=1, father_id=2, mother_id=3, children=(1,)),
        2: FamilyNode(family_id=2, father_id=4, mother_id=5, children=(2,)),
        3: FamilyNode(family_id=3, father_id=6, mother_id=7, children=(3,)),
    }
    return persons, families
