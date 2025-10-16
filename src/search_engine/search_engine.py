# search_engine.py

from typing import List, Optional, Dict, Set, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
from difflib import SequenceMatcher
from collections import defaultdict
import unicodedata
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    # Try relative imports first (when imported as a package)
    from ..models.person.person import Person
    from ..models.family.family import Family
    from ..models.date import Date, DMY
    from ..models.person.params import Sex, PEventType
    from ..models.family.params import RelationKind
except ImportError:
    # Fall back to absolute imports (when imported directly)
    from models.person.person import Person
    from models.family.family import Family
    from models.date import Date, DMY
    from models.person.params import Sex, PEventType
    from models.family.params import RelationKind

class SearchType(Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    PHONETIC = "phonetic"
    WILDCARD = "wildcard"
    REGEX = "regex"

class SearchField(Enum):
    FIRST_NAME = "first_name"
    SURNAME = "surname"
    FULL_NAME = "full_name"
    PUBLIC_NAME = "public_name"
    ALIASES = "aliases"
    OCCUPATION = "occupation"
    PLACE = "place"
    DATE = "date"
    NOTES = "notes"
    SOURCES = "sources"
    ALL = "all"

@dataclass
class SearchResult:
    person: Person
    score: float = 0.0
    matched_fields: List[str] = field(default_factory=list)
    match_details: Dict[str, str] = field(default_factory=dict)

@dataclass
class AdvancedSearchCriteria:
    # Name criteria
    first_name: Optional[str] = None
    surname: Optional[str] = None
    public_name: Optional[str] = None
    
    # Demographic criteria
    sex: Optional[Sex] = None
    birth_year_from: Optional[int] = None
    birth_year_to: Optional[int] = None
    death_year_from: Optional[int] = None
    death_year_to: Optional[int] = None
    
    # Location criteria
    birth_place: Optional[str] = None
    death_place: Optional[str] = None
    
    # Relationship criteria
    spouse_name: Optional[str] = None
    parent_name: Optional[str] = None
    child_name: Optional[str] = None
    
    # Occupation and titles
    occupation: Optional[str] = None
    has_titles: Optional[bool] = None
    
    # Other criteria
    notes_contain: Optional[str] = None
    sources_contain: Optional[str] = None
    alive_in_year: Optional[int] = None
    
    # Search behavior
    search_type: SearchType = SearchType.FUZZY
    max_results: int = 100
    min_score: float = 0.3

class SearchEngine:
    """Advanced search engine for genealogical data with fuzzy matching, phonetic search, and complex queries"""
    
    def __init__(self, persons: List[Person], families: List[Family]):
        self.persons = persons
        self.families = families
        self._build_indexes()
    
    def _build_indexes(self):
        """Build search indexes for fast retrieval"""
        self.name_index = defaultdict(set)
        self.surname_index = defaultdict(set)
        self.first_name_index = defaultdict(set)
        self.occupation_index = defaultdict(set)
        self.place_index = defaultdict(set)
        self.year_index = defaultdict(set)
        
        for i, person in enumerate(self.persons):
            # Index names
            self._index_name(person.first_name, self.first_name_index, i)
            self._index_name(person.surname, self.surname_index, i)
            self._index_name(person.full_name, self.name_index, i)
            
            # Index aliases
            for alias in person.aliases:
                self._index_name(alias, self.name_index, i)
            for alias in person.first_names_aliases:
                self._index_name(alias, self.first_name_index, i)
            for alias in person.surnames_aliases:
                self._index_name(alias, self.surname_index, i)
            
            if person.public_name:
                self._index_name(person.public_name, self.name_index, i)
            
            # Index occupation
            if person.occupation:
                self._index_name(person.occupation, self.occupation_index, i)
            
            # Index places from events
            for event in [person.birth, person.baptism, person.death, person.burial]:
                if event and event.place:
                    place_str = self._extract_place_string(event.place)
                    if place_str:
                        self._index_name(place_str, self.place_index, i)
            
            # Index years from events
            for event in [person.birth, person.baptism, person.death, person.burial]:
                if event and event.date and event.date.dmy and event.date.dmy.year > 0:
                    self.year_index[event.date.dmy.year].add(i)
    
    def _index_name(self, name: str, index: Dict[str, Set[int]], person_idx: int):
        """Add name to search index with normalization"""
        if not name:
            return
        
        # Normalize the name
        normalized = self._normalize_text(name)
        index[normalized].add(person_idx)
        
        # Also index individual words
        words = normalized.split()
        for word in words:
            if len(word) > 1:  # Skip single characters
                index[word].add(person_idx)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent searching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents and diacritics
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_place_string(self, place) -> str:
        """Extract searchable string from place object"""
        parts = []
        if place.town:
            parts.append(place.town)
        if place.county:
            parts.append(place.county)
        if place.region:
            parts.append(place.region)
        if place.country:
            parts.append(place.country)
        if place.other:
            parts.append(place.other)
        return ", ".join(parts)
    
    def simple_search(self, query: str, field: SearchField = SearchField.ALL, 
                     search_type: SearchType = SearchType.FUZZY, max_results: int = 50) -> List[SearchResult]:
        """Simple search interface"""
        results = []
        query_normalized = self._normalize_text(query)
        
        if not query_normalized:
            return results
        
        for i, person in enumerate(self.persons):
            score = 0.0
            matched_fields = []
            match_details = {}
            
            if field == SearchField.ALL or field == SearchField.FIRST_NAME:
                s = self._calculate_match_score(query_normalized, person.first_name, search_type)
                if s > 0:
                    score = max(score, s)
                    matched_fields.append("first_name")
                    match_details["first_name"] = person.first_name
            
            if field == SearchField.ALL or field == SearchField.SURNAME:
                s = self._calculate_match_score(query_normalized, person.surname, search_type)
                if s > 0:
                    score = max(score, s)
                    matched_fields.append("surname")
                    match_details["surname"] = person.surname
            
            if field == SearchField.ALL or field == SearchField.FULL_NAME:
                s = self._calculate_match_score(query_normalized, person.full_name, search_type)
                if s > 0:
                    score = max(score, s)
                    matched_fields.append("full_name")
                    match_details["full_name"] = person.full_name
            
            if field == SearchField.ALL or field == SearchField.PUBLIC_NAME:
                if person.public_name:
                    s = self._calculate_match_score(query_normalized, person.public_name, search_type)
                    if s > 0:
                        score = max(score, s)
                        matched_fields.append("public_name")
                        match_details["public_name"] = person.public_name
            
            if field == SearchField.ALL or field == SearchField.ALIASES:
                for alias in person.aliases + person.first_names_aliases + person.surnames_aliases:
                    s = self._calculate_match_score(query_normalized, alias, search_type)
                    if s > 0:
                        score = max(score, s)
                        matched_fields.append("aliases")
                        match_details["aliases"] = alias
            
            if field == SearchField.ALL or field == SearchField.OCCUPATION:
                if person.occupation:
                    s = self._calculate_match_score(query_normalized, person.occupation, search_type)
                    if s > 0:
                        score = max(score, s)
                        matched_fields.append("occupation")
                        match_details["occupation"] = person.occupation
            
            if score > 0.3:  # Minimum threshold
                results.append(SearchResult(
                    person=person,
                    score=score,
                    matched_fields=matched_fields,
                    match_details=match_details
                ))
        
        # Sort by score (descending) and limit results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]
    
    def advanced_search(self, criteria: AdvancedSearchCriteria) -> List[SearchResult]:
        """Advanced search with multiple criteria - ALL criteria must match"""
        results = []
        
        for i, person in enumerate(self.persons):
            score = 0.0
            matched_fields = []
            match_details = {}
            criteria_count = 0
            all_match = True  # Flag to track if ALL criteria match
            
            # Name criteria
            if criteria.first_name:
                criteria_count += 1
                s = self._calculate_match_score(criteria.first_name, person.first_name, criteria.search_type)
                if s > criteria.min_score:
                    score += s
                    matched_fields.append("first_name")
                    match_details["first_name"] = person.first_name
                else:
                    all_match = False
                    break  # Early exit if criterion fails
            
            if not all_match:
                continue
            
            if criteria.surname:
                criteria_count += 1
                s = self._calculate_match_score(criteria.surname, person.surname, criteria.search_type)
                if s > criteria.min_score:
                    score += s
                    matched_fields.append("surname")
                    match_details["surname"] = person.surname
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
                
            if criteria.public_name and person.public_name:
                criteria_count += 1
                s = self._calculate_match_score(criteria.public_name, person.public_name, criteria.search_type)
                if s > criteria.min_score:
                    score += s
                    matched_fields.append("public_name")
                    match_details["public_name"] = person.public_name
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
            
            # Demographic criteria
            if criteria.sex is not None:
                criteria_count += 1
                if person.sex == criteria.sex:
                    score += 1.0
                    matched_fields.append("sex")
                    match_details["sex"] = person.sex.value
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
            
            # Date criteria
            birth_year = self._extract_year_from_event(person.birth)
            if criteria.birth_year_from is not None or criteria.birth_year_to is not None:
                criteria_count += 1
                if birth_year and self._year_in_range(birth_year, criteria.birth_year_from, criteria.birth_year_to):
                    score += 1.0
                    matched_fields.append("birth_year")
                    match_details["birth_year"] = str(birth_year)
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
            
            death_year = self._extract_year_from_event(person.death)
            if criteria.death_year_from is not None or criteria.death_year_to is not None:
                criteria_count += 1
                if death_year and self._year_in_range(death_year, criteria.death_year_from, criteria.death_year_to):
                    score += 1.0
                    matched_fields.append("death_year")
                    match_details["death_year"] = str(death_year)
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
            
            # Place criteria
            if criteria.birth_place:
                criteria_count += 1
                birth_place = self._extract_place_string(person.birth.place) if person.birth and person.birth.place else ""
                if birth_place:
                    s = self._calculate_match_score(criteria.birth_place, birth_place, criteria.search_type)
                    if s > criteria.min_score:
                        score += s
                        matched_fields.append("birth_place")
                        match_details["birth_place"] = birth_place
                    else:
                        all_match = False
                        break
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
            
            if criteria.death_place:
                criteria_count += 1
                death_place = self._extract_place_string(person.death.place) if person.death and person.death.place else ""
                if death_place:
                    s = self._calculate_match_score(criteria.death_place, death_place, criteria.search_type)
                    if s > criteria.min_score:
                        score += s
                        matched_fields.append("death_place")
                        match_details["death_place"] = death_place
                    else:
                        all_match = False
                        break
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
            
            # Occupation criteria
            if criteria.occupation:
                criteria_count += 1
                if person.occupation:
                    s = self._calculate_match_score(criteria.occupation, person.occupation, criteria.search_type)
                    if s > criteria.min_score:
                        score += s
                        matched_fields.append("occupation")
                        match_details["occupation"] = person.occupation
                    else:
                        all_match = False
                        break
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
            
            # Title criteria
            if criteria.has_titles is not None:
                criteria_count += 1
                has_titles = person.has_titles
                if has_titles == criteria.has_titles:
                    score += 1.0
                    matched_fields.append("has_titles")
                    match_details["has_titles"] = str(has_titles)
                else:
                    all_match = False
                    break
            
            if not all_match:
                continue
            
            # Alive in year criteria
            if criteria.alive_in_year:
                criteria_count += 1
                if self._was_alive_in_year(person, criteria.alive_in_year):
                    score += 1.0
                    matched_fields.append("alive_in_year")
                    match_details["alive_in_year"] = str(criteria.alive_in_year)
                else:
                    all_match = False
                    break
            
            # If all criteria matched, add to results
            if all_match and criteria_count > 0:
                final_score = score / criteria_count  # Average score across criteria
                
                results.append(SearchResult(
                    person=person,
                    score=final_score,
                    matched_fields=matched_fields,
                    match_details=match_details
                ))
        
        # Sort by score (descending) and limit results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:criteria.max_results]
    
    def _calculate_match_score(self, query: str, text: str, search_type: SearchType) -> float:
        """Calculate match score between query and text"""
        if not query or not text:
            return 0.0
        
        query_norm = self._normalize_text(query)
        text_norm = self._normalize_text(text)
        
        if search_type == SearchType.EXACT:
            return 1.0 if query_norm == text_norm else 0.0
        
        elif search_type == SearchType.FUZZY:
            # Use sequence matcher for fuzzy matching
            return SequenceMatcher(None, query_norm, text_norm).ratio()
        
        elif search_type == SearchType.WILDCARD:
            # Convert wildcard to regex
            pattern = query_norm.replace('*', '.*').replace('?', '.')
            return 1.0 if re.fullmatch(pattern, text_norm) else 0.0
        
        elif search_type == SearchType.REGEX:
            try:
                return 1.0 if re.search(query_norm, text_norm) else 0.0
            except re.error:
                return 0.0
        
        elif search_type == SearchType.PHONETIC:
            # Simple phonetic matching using Soundex-like algorithm
            return self._phonetic_similarity(query_norm, text_norm)
        
        return 0.0
    
    def _phonetic_similarity(self, s1: str, s2: str) -> float:
        """Calculate phonetic similarity between two strings"""
        def soundex(s):
            if not s:
                return ""
            
            s = s.upper()
            # Keep first letter
            soundex_str = s[0]
            
            # Mapping of letters to codes
            mapping = {
                'BFPV': '1', 'CGJKQSXZ': '2', 'DT': '3',
                'L': '4', 'MN': '5', 'R': '6'
            }
            
            for char in s[1:]:
                for letters, code in mapping.items():
                    if char in letters:
                        if soundex_str[-1] != code:  # Avoid duplicates
                            soundex_str += code
                        break
            
            # Pad with zeros and truncate to 4 characters
            soundex_str = (soundex_str + '000')[:4]
            return soundex_str
        
        soundex1 = soundex(s1)
        soundex2 = soundex(s2)
        
        if soundex1 == soundex2:
            return 0.8  # High score for phonetic match
        else:
            # Partial credit for similar soundex codes
            return SequenceMatcher(None, soundex1, soundex2).ratio() * 0.5
    
    def _extract_year_from_event(self, event) -> Optional[int]:
        """Extract year from an event"""
        if event and event.date and event.date.dmy and event.date.dmy.year > 0:
            return event.date.dmy.year
        return None
    
    def _year_in_range(self, year: int, year_from: Optional[int], year_to: Optional[int]) -> bool:
        """Check if year is in specified range"""
        if year_from is not None and year < year_from:
            return False
        if year_to is not None and year > year_to:
            return False
        return True
    
    def _was_alive_in_year(self, person: Person, year: int) -> bool:
        """Check if person was alive in specified year"""
        birth_year = self._extract_year_from_event(person.birth)
        death_year = self._extract_year_from_event(person.death)
        
        # Must be born before or in the year
        if birth_year and birth_year > year:
            return False
        
        # Must not have died before the year
        if death_year and death_year < year:
            return False
        
        return True
    
    def find_possible_duplicates(self, threshold: float = 0.85) -> List[Tuple[Person, Person, float]]:
        """Find possible duplicate persons based on name similarity"""
        duplicates = []
        
        for i in range(len(self.persons)):
            for j in range(i + 1, len(self.persons)):
                person1 = self.persons[i]
                person2 = self.persons[j]
                
                # Calculate similarity score
                name_score = SequenceMatcher(None, 
                                           self._normalize_text(person1.full_name),
                                           self._normalize_text(person2.full_name)).ratio()
                
                if name_score > threshold:
                    # Additional checks for birth year similarity
                    birth1 = self._extract_year_from_event(person1.birth)
                    birth2 = self._extract_year_from_event(person2.birth)
                    
                    year_penalty = 0.0
                    if birth1 and birth2 and abs(birth1 - birth2) > 5:
                        year_penalty = 0.2
                    
                    final_score = name_score - year_penalty
                    if final_score > threshold:
                        duplicates.append((person1, person2, final_score))
        
        return sorted(duplicates, key=lambda x: x[2], reverse=True)
    
    def get_name_suggestions(self, partial_name: str, field: SearchField = SearchField.ALL, 
                           max_suggestions: int = 10) -> List[str]:
        """Get name suggestions for autocomplete"""
        suggestions = set()
        partial_norm = self._normalize_text(partial_name)
        
        if not partial_norm:
            return []
        
        # Search in appropriate indexes
        indexes_to_search = []
        if field == SearchField.ALL:
            indexes_to_search = [self.name_index, self.first_name_index, self.surname_index]
        elif field == SearchField.FIRST_NAME:
            indexes_to_search = [self.first_name_index]
        elif field == SearchField.SURNAME:
            indexes_to_search = [self.surname_index]
        elif field == SearchField.FULL_NAME:
            indexes_to_search = [self.name_index]
        
        for index in indexes_to_search:
            for name in index.keys():
                if name.startswith(partial_norm):
                    suggestions.add(name)
                elif partial_norm in name:
                    suggestions.add(name)
        
        # Sort by relevance (starts with query first)
        suggestions_list = list(suggestions)
        suggestions_list.sort(key=lambda x: (not x.startswith(partial_norm), len(x), x))
        
        return suggestions_list[:max_suggestions]