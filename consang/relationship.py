from typing import Dict, List, Tuple, Union

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

def relationship_and_links(base, ri, b: bool, ip1: int, ip2: int) -> Tuple[float, List[int]]:
    if ip1 == ip2:
        return 1.0, []

    reltab = ri['reltab']
    tstab = ri['tstab']
    yes_inserted = new_mark()

    def reset(u):
        if u not in reltab or reltab[u] is None:
            reltab[u] = {
                "weight1": 0.0,
                "weight2": 0.0,
                "relationship": 0.0,
                "lens1": [],
                "lens2": [],
                "inserted": yes_inserted,
                "elim_ancestors": False,
                "anc_stat1": "MaybeAnc",
                "anc_stat2": "MaybeAnc",
            }
        else:
            tu = reltab[u]
            tu["weight1"] = 0.0
            tu["weight2"] = 0.0
            tu["relationship"] = 0.0
            tu["lens1"] = []
            tu["lens2"] = []
            tu["inserted"] = yes_inserted
            tu["elim_ancestors"] = False
            tu["anc_stat1"] = "MaybeAnc"
            tu["anc_stat2"] = "MaybeAnc"

    qi = min(tstab[ip1], tstab[ip2])
    qmax = -1
    queue = ri['queue']

    def insert(u):
        v = tstab[u]
        reset(u)
        while len(queue) <= v:
            queue.append([])
        if qmax < 0:
            for i in range(qi, v):
                queue[i] = []
            qmax = v
            queue[v] = [u]
        else:
            if v > qmax:
                for i in range(qmax + 1, v + 1):
                    queue.append([])
                qmax = v
            queue[v].append(u)

    relationship = 0.0
    nb_anc1 = 1
    nb_anc2 = 1
    tops = []

    def treat_parent(ip_from, u, y):
        if reltab[y]["inserted"] != yes_inserted:
            insert(y)
        ty = reltab[y]
        p1 = u["weight1"] * 0.5
        p2 = u["weight2"] * 0.5
        if u["anc_stat1"] == "IsAnc" and ty["anc_stat1"] != "IsAnc":
            ty["anc_stat1"] = "IsAnc"
            nonlocal nb_anc1
            nb_anc1 += 1
        if u["anc_stat2"] == "IsAnc" and ty["anc_stat2"] != "IsAnc":
            ty["anc_stat2"] = "IsAnc"
            nonlocal nb_anc2
            nb_anc2 += 1
        ty["weight1"] += p1
        ty["weight2"] += p2
        ty["relationship"] += p1 * p2
        if u["elim_ancestors"]:
            ty["elim_ancestors"] = True
        if b and not ty["elim_ancestors"]:
            ty["lens1"] = insert_branch_len(ip_from, ty["lens1"], u["lens1"])
            ty["lens2"] = insert_branch_len(ip_from, ty["lens2"], u["lens2"])

    def treat_ancestor(u):
        nonlocal relationship, nb_anc1, nb_anc2, tops
        tu = reltab[u]
        a = base[u]
        contribution = (tu["weight1"] * tu["weight2"]) - (
            tu["relationship"] * (1.0 + consang_of(a))
        )
        if tu["anc_stat1"] == "IsAnc":
            nb_anc1 -= 1
        if tu["anc_stat2"] == "IsAnc":
            nb_anc2 -= 1
        relationship += contribution
        if b and contribution != 0.0 and not tu["elim_ancestors"]:
            tops.append(u)
            tu["elim_ancestors"] = True
        parents = get_parents(a)
        if parents:
            treat_parent(u, tu, parents["father"])
            treat_parent(u, tu, parents["mother"])

    insert(ip1)
    insert(ip2)
    reltab[ip1]["weight1"] = 1.0
    reltab[ip2]["weight2"] = 1.0
    reltab[ip1]["lens1"] = [(0, 1, [])]
    reltab[ip2]["lens2"] = [(0, 1, [])]
    reltab[ip1]["anc_stat1"] = "IsAnc"
    reltab[ip2]["anc_stat2"] = "IsAnc"

    while qi <= qmax and nb_anc1 > 0 and nb_anc2 > 0:
        for u in queue[qi]:
            treat_ancestor(u)
        qi += 1

    return relationship * 0.5, tops

# Helper functions to be implemented:
def new_mark():
    if not hasattr(new_mark, "current_mark"):
        new_mark.current_mark = 0
    new_mark.current_mark += 1
    return new_mark.current_mark

def insert_branch_len(ip_from, lens, u_lens):
    for (len_u, n_u, ip_list_u) in u_lens:
        found = False
        for i, (len_l, n_l, ip_list_l) in enumerate(lens):
            if len_u + 1 == len_l:
                lens[i] = (
                    len_l,
                    n_l + n_u if n_l >= 0 and n_u >= 0 else -1,
                    ip_list_l + [ip_from] + ip_list_u,
                )
                found = True
                break
        if not found:
            lens.append((len_u + 1, n_u, [ip_from] + ip_list_u))
    return lens

def consang_of(person):
    consang = person.get("consang", -1)
    if consang == -1:
        return 0.0
    return consang / 100.0  # Assuming consang is stored as an integer percentage

def get_parents(person):
    return {
        "father": person.get("father"),
        "mother": person.get("mother"),
    }
