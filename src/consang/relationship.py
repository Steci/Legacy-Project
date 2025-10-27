"""Relationship computation helpers matching GeneWeb's consang engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from .graph import topological_order
from .models import FamilyNode, PersonNode


class AncestorStatus(Enum):
	"""Track whether a node is known to be an ancestor of the target person."""

	MAYBE = auto()
	IS = auto()


@dataclass
class BranchRecord:
	"""Carry branch length and multiplicity information for relationship output."""

	length: int
	count: int
	nodes: List[int] = field(default_factory=list)


@dataclass
class RelationshipState:
	"""Mirror GeneWeb's per-node bookkeeping during relationship computation."""

	weight1: float = 0.0
	weight2: float = 0.0
	relationship: float = 0.0
	lens1: List[BranchRecord] = field(default_factory=list)
	lens2: List[BranchRecord] = field(default_factory=list)
	inserted_mark: int = 0
	eliminate: bool = False
	anc_stat1: AncestorStatus = AncestorStatus.MAYBE
	anc_stat2: AncestorStatus = AncestorStatus.MAYBE


@dataclass
class RelationshipResult:
	"""Aggregate relationship coefficient and ancestor linking information."""

	coefficient: float
	top_ancestors: List[int]
	info: "RelationshipInfo"


@dataclass(frozen=True)
class BranchPath:
	"""Human-friendly path description used for downstream reporting."""

	length: int
	multiplicity: int
	path: Tuple[str, ...]


@dataclass(frozen=True)
class RelationshipSummary:
	"""Serializable summary of a relationship result."""

	person_a: str
	person_b: str
	coefficient: float
	ancestors: Tuple[str, ...]
	paths_to_a: Dict[str, Tuple[BranchPath, ...]]
	paths_to_b: Dict[str, Tuple[BranchPath, ...]]


class RelationshipInfo:
	"""State container that mirrors GeneWeb's `Consang.relationship_info`."""

	def __init__(
		self,
		persons: Dict[int, PersonNode],
		families: Dict[int, FamilyNode],
		rank: Dict[int, int],
	) -> None:
		self._persons = persons
		self._families = families
		self.rank = rank
		self.states: Dict[int, RelationshipState] = {
			pid: RelationshipState() for pid in persons.keys()
		}
		max_rank = max(rank.values(), default=-1)
		self.queue: List[List[int]] = [[] for _ in range(max_rank + 1)]
		self._mark = 0

	def _next_mark(self) -> int:
		self._mark += 1
		return self._mark

	def _ensure_queue_size(self, level: int) -> None:
		if level >= len(self.queue):
			self.queue.extend([] for _ in range(level + 1 - len(self.queue)))

	def relationship_and_links(
		self, person_a: int, person_b: int, *, include_branches: bool = False
	) -> RelationshipResult:
		if person_a == person_b:
			return RelationshipResult(1.0, [], self)

		if person_a not in self.rank or person_b not in self.rank:
			raise KeyError("Both individuals must exist in the relationship info")

		mark = self._next_mark()
		qi = min(self.rank[person_a], self.rank[person_b])
		qmax = -1

		def reset_state(pid: int) -> None:
			state = self.states[pid]
			state.weight1 = 0.0
			state.weight2 = 0.0
			state.relationship = 0.0
			state.lens1 = []
			state.lens2 = []
			state.inserted_mark = mark
			state.eliminate = False
			state.anc_stat1 = AncestorStatus.MAYBE
			state.anc_stat2 = AncestorStatus.MAYBE

		def insert(pid: int) -> None:
			nonlocal qmax
			rank = self.rank.get(pid)
			if rank is None:
				return
			self._ensure_queue_size(rank)
			reset_state(pid)
			if qmax < 0:
				for level in range(qi, rank):
					if level < len(self.queue):
						self.queue[level] = []
				qmax = rank
				self.queue[rank] = [pid]
			else:
				if rank > qmax:
					for level in range(qmax + 1, rank + 1):
						if level < len(self.queue):
							self.queue[level] = []
					qmax = rank
				self.queue[rank] = [pid] + self.queue[rank]

		def combine_counts(left: int, right: int) -> int:
			if left < 0 or right < 0:
				return -1
			value = left + right
			return value if value >= 0 else -1

		def insert_branch(parent_id: int, lens: List[BranchRecord], branch: BranchRecord) -> List[BranchRecord]:
			new_length = branch.length + 1
			new_count = branch.count
			if not lens:
				return [BranchRecord(new_length, new_count, [parent_id])]
			head, *tail = lens
			if head.length == new_length:
				combined = combine_counts(new_count, head.count)
				nodes = [parent_id] + head.nodes
				return [BranchRecord(new_length, combined, nodes)] + tail
			return [head] + insert_branch(parent_id, tail, branch)

		def extend_branches(parent_id: int, target: List[BranchRecord], branches: List[BranchRecord]) -> List[BranchRecord]:
			result = target
			for branch in branches:
				result = insert_branch(parent_id, result, branch)
			return result

		relationship = 0.0
		nb_anc1 = 1
		nb_anc2 = 1
		tops: List[int] = []

		def treat_parent(src_id: int, src_state: RelationshipState, parent_id: Optional[int]) -> None:
			nonlocal nb_anc1, nb_anc2
			if parent_id is None or parent_id not in self.states:
				return
			parent_state = self.states[parent_id]
			if parent_state.inserted_mark != mark:
				insert(parent_id)
				parent_state = self.states[parent_id]

			p1 = 0.5 * src_state.weight1
			p2 = 0.5 * src_state.weight2

			if src_state.anc_stat1 is AncestorStatus.IS and parent_state.anc_stat1 is not AncestorStatus.IS:
				parent_state.anc_stat1 = AncestorStatus.IS
				nb_anc1 += 1
			if src_state.anc_stat2 is AncestorStatus.IS and parent_state.anc_stat2 is not AncestorStatus.IS:
				parent_state.anc_stat2 = AncestorStatus.IS
				nb_anc2 += 1

			parent_state.weight1 += p1
			parent_state.weight2 += p2
			parent_state.relationship += p1 * p2

			if src_state.eliminate:
				parent_state.eliminate = True

			if include_branches and not parent_state.eliminate:
				parent_state.lens1 = extend_branches(src_id, parent_state.lens1, src_state.lens1)
				parent_state.lens2 = extend_branches(src_id, parent_state.lens2, src_state.lens2)

		def treat_ancestor(pid: int) -> None:
			nonlocal relationship, nb_anc1, nb_anc2
			state = self.states[pid]
			node = self._persons.get(pid)
			consang = node.consanguinity if node is not None else 0.0
			contribution = (state.weight1 * state.weight2) - (
				state.relationship * (1.0 + consang)
			)
			if state.anc_stat1 is AncestorStatus.IS:
				nb_anc1 -= 1
			if state.anc_stat2 is AncestorStatus.IS:
				nb_anc2 -= 1
			relationship += contribution

			if include_branches and contribution != 0.0 and not state.eliminate:
				tops.append(pid)
				state.eliminate = True

			if node is None or node.parent_family_id is None:
				return
			family = self._families.get(node.parent_family_id)
			if family is None:
				return
			treat_parent(pid, state, family.father_id)
			treat_parent(pid, state, family.mother_id)

		insert(person_a)
		insert(person_b)

		state_a = self.states[person_a]
		state_b = self.states[person_b]
		state_a.weight1 = 1.0
		state_a.lens1 = [BranchRecord(0, 1, [])]
		state_a.anc_stat1 = AncestorStatus.IS
		state_b.weight2 = 1.0
		state_b.lens2 = [BranchRecord(0, 1, [])]
		state_b.anc_stat2 = AncestorStatus.IS

		while qi <= qmax and nb_anc1 > 0 and nb_anc2 > 0:
			current_level = list(self.queue[qi]) if qi < len(self.queue) else []
			if qi < len(self.queue):
				self.queue[qi] = []
			for node_id in current_level:
				treat_ancestor(node_id)
			qi += 1

		coefficient = 0.5 * relationship
		return RelationshipResult(coefficient, tops, self)


def build_relationship_info(
	persons: Dict[int, PersonNode], families: Dict[int, FamilyNode]
) -> RelationshipInfo:
	"""Factory mirroring GeneWeb's `make_relationship_info`."""

	order = topological_order(persons, families)
	reversed_order = list(reversed(order))
	rank = {pid: idx for idx, pid in enumerate(reversed_order)}
	return RelationshipInfo(persons, families, rank)


def summarize_relationship(
	info: RelationshipInfo,
	person_a_id: int,
	person_b_id: int,
	index_to_key: Dict[int, str],
) -> RelationshipSummary:
	"""Return a serialisable summary for the two individuals."""

	person_a_key = index_to_key.get(person_a_id, str(person_a_id))
	person_b_key = index_to_key.get(person_b_id, str(person_b_id))

	result = info.relationship_and_links(
		person_a_id, person_b_id, include_branches=True
	)

	ancestors: Tuple[str, ...] = tuple(
		index_to_key.get(ancestor_id, str(ancestor_id))
		for ancestor_id in result.top_ancestors
	)

	paths_to_a: Dict[str, Tuple[BranchPath, ...]] = {}
	paths_to_b: Dict[str, Tuple[BranchPath, ...]] = {}

	for ancestor_id in result.top_ancestors:
		ancestor_key = index_to_key.get(ancestor_id, str(ancestor_id))
		state = result.info.states[ancestor_id]

		paths_to_a[ancestor_key] = tuple(
			BranchPath(
				length=branch.length,
				multiplicity=branch.count,
				path=tuple(
					index_to_key.get(pid, str(pid))
					for pid in [ancestor_id, *branch.nodes, person_a_id]
				),
			)
			for branch in state.lens1
		)

		paths_to_b[ancestor_key] = tuple(
			BranchPath(
				length=branch.length,
				multiplicity=branch.count,
				path=tuple(
					index_to_key.get(pid, str(pid))
					for pid in [ancestor_id, *branch.nodes, person_b_id]
				),
			)
			for branch in state.lens2
		)

	return RelationshipSummary(
		person_a=person_a_key,
		person_b=person_b_key,
		coefficient=result.coefficient,
		ancestors=ancestors,
		paths_to_a=paths_to_a,
		paths_to_b=paths_to_b,
	)

