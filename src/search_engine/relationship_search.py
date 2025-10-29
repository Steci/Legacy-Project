# relationship_search.py

from typing import List, Optional, Dict, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from collections import deque, defaultdict

# Use only relative imports, as in src/parsers
from models.person.person import Person
from models.family.family import Family
from models.family.params import RelationKind

class RelationshipType(Enum):
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    SPOUSE = "spouse"
    GRANDPARENT = "grandparent"
    GRANDCHILD = "grandchild"
    UNCLE_AUNT = "uncle_aunt"
    NEPHEW_NIECE = "nephew_niece"
    COUSIN = "cousin"
    ANCESTOR = "ancestor"
    DESCENDANT = "descendant"

@dataclass
class RelationshipPath:
    from_person: Person
    to_person: Person
    relationship_type: RelationshipType
    path: List[Person]
    description: str
    distance: int

class RelationshipSearchEngine:
    """Search engine for finding relationships between persons"""
    
    def __init__(self, persons: List[Person], families: List[Family]):
        self.persons = persons
        self.families = families
        self._build_relationship_graph()
    
    def _build_relationship_graph(self):
        """Build graph of relationships for efficient traversal"""
        self.person_to_idx = {person.key_index: i for i, person in enumerate(self.persons)}
        self.children_graph = defaultdict(set)  # parent -> children
        self.parents_graph = defaultdict(set)   # child -> parents
        self.spouse_graph = defaultdict(set)    # person -> spouses

        for family in self.families:
            # Add parent-child relationships
            if family.parent1:
                parent1_idx = self.person_to_idx.get(family.parent1)
                if parent1_idx is not None:
                    for child_key in family.children:
                        child_idx = self.person_to_idx.get(child_key)
                        if child_idx is not None:
                            self.children_graph[parent1_idx].add(child_idx)
                            self.parents_graph[child_idx].add(parent1_idx)

            if family.parent2:
                parent2_idx = self.person_to_idx.get(family.parent2)
                if parent2_idx is not None:
                    for child_key in family.children:
                        child_idx = self.person_to_idx.get(child_key)
                        if child_idx is not None:
                            self.children_graph[parent2_idx].add(child_idx)
                            self.parents_graph[child_idx].add(parent2_idx)

            # Add spouse relationships
            if family.parent1 and family.parent2:
                parent1_idx = self.person_to_idx.get(family.parent1)
                parent2_idx = self.person_to_idx.get(family.parent2)
                if parent1_idx is not None and parent2_idx is not None:
                    self.spouse_graph[parent1_idx].add(parent2_idx)
                    self.spouse_graph[parent2_idx].add(parent1_idx)
    
    def find_relationship(self, person1_key_index: int, person2_key_index: int, max_distance: int = 6) -> Optional[RelationshipPath]:
        """Find the closest relationship between two persons"""
        person1_idx = self.person_to_idx.get(person1_key_index)
        person2_idx = self.person_to_idx.get(person2_key_index)
        
        if person1_idx is None or person2_idx is None:
            return None
        
        if person1_idx == person2_idx:
            return RelationshipPath(
                from_person=self.persons[person1_idx],
                to_person=self.persons[person2_idx],
                relationship_type=RelationshipType.PARENT,  # Self
                path=[self.persons[person1_idx]],
                description="Same person",
                distance=0
            )
        
        # BFS to find shortest path
        queue = deque([(person1_idx, [person1_idx])])
        visited = {person1_idx}
        
        while queue:
            current_idx, path = queue.popleft()
            
            if len(path) > max_distance + 1:
                continue
            
            # Check all connected persons
            connected = set()
            connected.update(self.children_graph[current_idx])
            connected.update(self.parents_graph[current_idx])
            connected.update(self.spouse_graph[current_idx])
            
            for next_idx in connected:
                if next_idx == person2_idx:
                    # Found target
                    full_path = path + [next_idx]
                    relationship = self._analyze_relationship_path(full_path)
                    return RelationshipPath(
                        from_person=self.persons[person1_idx],
                        to_person=self.persons[person2_idx],
                        relationship_type=relationship[0],
                        path=[self.persons[i] for i in full_path],
                        description=relationship[1],
                        distance=len(full_path) - 1
                    )
                
                if next_idx not in visited:
                    visited.add(next_idx)
                    queue.append((next_idx, path + [next_idx]))
        
        return None
    
    def _analyze_relationship_path(self, path: List[int]) -> Tuple[RelationshipType, str]:
        """Analyze a relationship path to determine the relationship type"""
        if len(path) < 2:
            return RelationshipType.PARENT, "Same person"
        
        if len(path) == 2:
            # Direct relationship
            person1_idx, person2_idx = path
            
            # Check if parent-child
            if person2_idx in self.children_graph[person1_idx]:
                return RelationshipType.CHILD, "Child"
            elif person1_idx in self.children_graph[person2_idx]:
                return RelationshipType.PARENT, "Parent"
            elif person2_idx in self.spouse_graph[person1_idx]:
                return RelationshipType.SPOUSE, "Spouse"
            else:
                # Must be siblings
                return RelationshipType.SIBLING, "Sibling"
        
        elif len(path) == 3:
            # Two-step relationship
            person1_idx, middle_idx, person2_idx = path
            
            # Grandparent/grandchild
            if middle_idx in self.children_graph[person1_idx] and person2_idx in self.children_graph[middle_idx]:
                return RelationshipType.GRANDCHILD, "Grandchild"
            elif middle_idx in self.parents_graph[person1_idx] and person2_idx in self.parents_graph[middle_idx]:
                return RelationshipType.GRANDPARENT, "Grandparent"
            
            # Uncle/Aunt - Nephew/Niece
            elif (middle_idx in self.parents_graph[person1_idx] and 
                  person2_idx in self.children_graph[middle_idx] and
                  person2_idx != person1_idx):
                return RelationshipType.UNCLE_AUNT, "Uncle/Aunt"
            elif (middle_idx in self.children_graph[person1_idx] and
                  person2_idx in self.parents_graph[middle_idx] and
                  person2_idx != person1_idx):
                return RelationshipType.NEPHEW_NIECE, "Nephew/Niece"
            
            # Sibling-in-law (spouse's sibling)
            elif (middle_idx in self.spouse_graph[person1_idx] and
                  self._are_siblings(middle_idx, person2_idx)):
                return RelationshipType.SIBLING, "Sibling-in-law"
        
        elif len(path) == 4:
            # Cousin relationship
            person1_idx, p1_parent, p2_parent, person2_idx = path
            
            if (p1_parent in self.parents_graph[person1_idx] and
                p2_parent in self.parents_graph[person2_idx] and
                self._are_siblings(p1_parent, p2_parent)):
                return RelationshipType.COUSIN, "First cousin"
        
        # General ancestor/descendant for longer paths
        if self._is_ancestor_path(path):
            generations = len(path) - 1
            if generations == 2:
                return RelationshipType.GRANDPARENT, "Grandparent"
            elif generations == 3:
                return RelationshipType.ANCESTOR, "Great-grandparent"
            else:
                return RelationshipType.ANCESTOR, f"{generations-2}x great-grandparent"
        elif self._is_descendant_path(path):
            generations = len(path) - 1
            if generations == 2:
                return RelationshipType.GRANDCHILD, "Grandchild"
            elif generations == 3:
                return RelationshipType.DESCENDANT, "Great-grandchild"
            else:
                return RelationshipType.DESCENDANT, f"{generations-2}x great-grandchild"
        
        return RelationshipType.ANCESTOR, f"Distant relative ({len(path)-1} degrees)"
    
    def _are_siblings(self, person1_idx: int, person2_idx: int) -> bool:
        """Check if two persons are siblings"""
        parents1 = self.parents_graph[person1_idx]
        parents2 = self.parents_graph[person2_idx]
        return len(parents1.intersection(parents2)) > 0
    
    def _is_ancestor_path(self, path: List[int]) -> bool:
        """Check if path represents ancestor relationship (going up generations)"""
        for i in range(len(path) - 1):
            if path[i+1] not in self.parents_graph[path[i]]:
                return False
        return True
    
    def _is_descendant_path(self, path: List[int]) -> bool:
        """Check if path represents descendant relationship (going down generations)"""
        for i in range(len(path) - 1):
            if path[i+1] not in self.children_graph[path[i]]:
                return False
        return True
    
    def find_all_relatives(self, person_key_index: int, max_distance: int = 4) -> Dict[RelationshipType, List[Person]]:
        """Find all relatives of a person within specified distance"""
        person_idx = self.person_to_idx.get(person_key_index)
        if person_idx is None:
            return {}
        
        relatives = defaultdict(list)
        visited = set()
        queue = deque([(person_idx, 0, [])])
        
        while queue:
            current_idx, distance, path = queue.popleft()
            
            if distance > max_distance:
                continue
            
            if current_idx in visited:
                continue
            visited.add(current_idx)
            
            if distance > 0:  # Don't include the person themselves
                current_path = path + [current_idx]
                relationship = self._analyze_relationship_path([person_idx] + current_path)
                relatives[relationship[0]].append(self.persons[current_idx])
            
            # Add connected persons to queue
            connected = set()
            connected.update(self.children_graph[current_idx])
            connected.update(self.parents_graph[current_idx])
            connected.update(self.spouse_graph[current_idx])
            
            for next_idx in connected:
                if next_idx not in visited:
                    queue.append((next_idx, distance + 1, path + [current_idx] if distance > 0 else []))
        
        return dict(relatives)
    
    def find_common_ancestors(self, person1_key_index: int, person2_key_index: int, max_generations: int = 10) -> List[Person]:
        """Find common ancestors of two persons"""
        person1_idx = self.person_to_idx.get(person1_key_index)
        person2_idx = self.person_to_idx.get(person2_key_index)
        
        if person1_idx is None or person2_idx is None:
            return []
        
        # Get all ancestors for person1
        ancestors1 = self._get_all_ancestors(person1_idx, max_generations)
        # Get all ancestors for person2
        ancestors2 = self._get_all_ancestors(person2_idx, max_generations)
        
        # Find intersection
        common = ancestors1.intersection(ancestors2)
        return [self.persons[idx] for idx in common]
    
    def _get_all_ancestors(self, person_idx: int, max_generations: int) -> Set[int]:
        """Get all ancestors of a person up to max_generations"""
        ancestors = set()
        current_generation = {person_idx}
        
        for generation in range(max_generations):
            next_generation = set()
            for person in current_generation:
                parents = self.parents_graph[person]
                next_generation.update(parents)
                ancestors.update(parents)
            
            if not next_generation:
                break
            current_generation = next_generation
        
        return ancestors
    
    def find_descendants(self, person_key_index: int, max_generations: int = 10) -> List[Person]:
        """Find all descendants of a person"""
        person_idx = self.person_to_idx.get(person_key_index)
        if person_idx is None:
            return []
        
        descendants = set()
        current_generation = {person_idx}
        
        for generation in range(max_generations):
            next_generation = set()
            for person in current_generation:
                children = self.children_graph[person]
                next_generation.update(children)
                descendants.update(children)
            
            if not next_generation:
                break
            current_generation = next_generation
        
        return [self.persons[idx] for idx in descendants]
    
    def find_living_relatives(self, person_key_index: int, max_distance: int = 3) -> List[Tuple[Person, RelationshipType, str]]:
        """Find living relatives of a person"""
        relatives = self.find_all_relatives(person_key_index, max_distance)
        living_relatives = []
        
        for rel_type, persons in relatives.items():
            for person in persons:
                if not person.death:  # Assume no death record means still living
                    living_relatives.append((person, rel_type, rel_type.value))
        
        return living_relatives