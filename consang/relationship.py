from typing import Dict, List, Tuple, Optional


class Relationship:
    def __init__(self):
        self.weight1: float = 0.0
        self.weight2: float = 0.0
        self.relationship: float = 0.0
        self.lens1: List[Tuple[int, int, List[int]]] = []
        self.lens2: List[Tuple[int, int, List[int]]] = []
        self.inserted: int = 0
        self.elim_ancestors: bool = False
        self.anc_stat1: str = "MaybeAnc"
        self.anc_stat2: str = "MaybeAnc"


class RelationshipInfo:
    def __init__(self):
        self.tstab: Dict[int, int] = {}
        self.reltab: Dict[int, Relationship] = {}
        self.queue: List[List[int]] = []


def relationship_and_links(
    base: Dict[int, Dict[str, Optional[int]]],
    ri: RelationshipInfo,
    include_branch_lengths: bool,
    ip1: int,
    ip2: int,
) -> Tuple[float, List[int]]:
    if ip1 == ip2:
        return 1.0, []

    def reset(u: int):
        if u not in ri.reltab:
            ri.reltab[u] = Relationship()

    def insert(u: int):
        v = ri.tstab[u]
        reset(u)
        while len(ri.queue) <= v:
            ri.queue.append([])
        ri.queue[v].append(u)

    def propagate_weights(parent: Relationship, child: Relationship):
        child.weight1 += parent.weight1 * 0.5
        child.weight2 += parent.weight2 * 0.5

    def treat_parent(parent_id: int, child: Relationship):
        if parent_id is None:
            return
        reset(parent_id)
        parent = ri.reltab[parent_id]
        propagate_weights(child, parent)

    def calculate_contribution(ancestor: Relationship, person: Dict[str, Optional[int]]):
        consang = consang_of(person)
        return (ancestor.weight1 * ancestor.weight2) - (
            ancestor.relationship * (1.0 + consang)
        )

    def treat_ancestor(ancestor_id: int):
        ancestor = ri.reltab[ancestor_id]
        person = base[ancestor_id]
        contribution = calculate_contribution(ancestor, person)
        nonlocal relationship
        relationship += contribution
        if contribution > 0.0 and ancestor_id not in tops:
            tops.append(ancestor_id)
        treat_parent(person["father"], ancestor)
        treat_parent(person["mother"], ancestor)

    reset(ip1)
    reset(ip2)
    ri.reltab[ip1].weight1 = 1.0
    ri.reltab[ip2].weight2 = 1.0
    insert(ip1)
    insert(ip2)

    relationship = 0.0
    tops = []
    for level in ri.queue:
        for ancestor_id in level:
            treat_ancestor(ancestor_id)

    return relationship * 0.5, tops


def consang_of(person: Dict[str, Optional[int]]) -> float:
    return person.get("consang", 0) / 100.0
