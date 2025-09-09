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
