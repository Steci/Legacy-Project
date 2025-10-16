#!/usr/bin/env python3

"""
Genealogical Search Engine Demo
Comprehensive demonstration of all search capabilities
Consolidates functionality from both complex and simple demos
"""

import sys
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, Counter
import re
from difflib import SequenceMatcher

# Add the src directory to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Try importing full models first, fall back to simple structures if needed
try:
    from ..src.search_engine.search_engine import SearchEngine, SearchField, SearchType, AdvancedSearchCriteria
    from ..src.search_engine.relationship_search import RelationshipSearchEngine, RelationshipType
    from ..src.search_engine.statistics_engine import StatisticsEngine
    from ..src.search_engine.genealogy_search_api import GenealogySearchAPI
    from ..src.models.person.person import Person
    from ..src.models.family.family import Family
    from ..src.models.date import Date, DMY
    from ..src.models.person.params import Sex, PEventType
    from ..src.models.event import Event
    from ..src.models.place import Place
    
    FULL_MODELS_AVAILABLE = True
    print("Using full genealogical models")
    
except ImportError as e:
    print(f"Full models not available ({e})")
    print("Using simplified demo structures")
    FULL_MODELS_AVAILABLE = False
    
    # Simple data structures for standalone demonstration
    @dataclass
    class SimplePerson:
        key: str
        first_name: str
        surname: str
        sex: str = "unknown"
        birth_year: Optional[int] = None
        death_year: Optional[int] = None
        birth_place: str = ""
        occupation: str = ""
        
        @property
        def full_name(self) -> str:
            return f"{self.first_name} {self.surname}"
    
    @dataclass
    class SimpleFamily:
        key: str
        husband_key: str
        wife_key: str
        marriage_year: Optional[int] = None
        children_keys: List[str] = None
        
        def __post_init__(self):
            if self.children_keys is None:
                self.children_keys = []


def create_sample_data_full():
    """Create sample data using full genealogical models"""
    if not FULL_MODELS_AVAILABLE:
        return None, None
    
    persons = []
    families = []
    
    # Generation 1 (oldest)
    john_smith = Person(
        key="john_smith_1920",
        first_name="John",
        surname="Smith",
        sex=Sex.MALE,
        birth=Event(
            event_type=PEventType.BIRTH,
            date=Date(dmy=DMY(day=15, month=3, year=1920)),
            place=Place(town="London", country="England")
        ),
        death=Event(
            event_type=PEventType.DEATH,
            date=Date(dmy=DMY(day=22, month=8, year=1995)),
            place=Place(town="London", country="England")
        ),
        occupation="Carpenter"
    )
    persons.append(john_smith)
    
    mary_jones = Person(
        key="mary_jones_1925",
        first_name="Mary",
        surname="Jones",
        sex=Sex.FEMALE,
        birth=Event(
            event_type=PEventType.BIRTH,
            date=Date(dmy=DMY(day=8, month=11, year=1925)),
            place=Place(town="Birmingham", country="England")
        ),
        occupation="Teacher"
    )
    persons.append(mary_jones)
    
    # Create their family
    smith_family = Family(
        key="smith_family_1945",
        husband=john_smith,
        wife=mary_jones,
        marriage=Event(
            event_type=PEventType.MARRIAGE,
            date=Date(dmy=DMY(day=12, month=6, year=1945)),
            place=Place(town="London", country="England")
        )
    )
    families.append(smith_family)
    
    # Generation 2 - Children
    robert_smith = Person(
        key="robert_smith_1950",
        first_name="Robert",
        surname="Smith",
        sex=Sex.MALE,
        birth=Event(
            event_type=PEventType.BIRTH,
            date=Date(dmy=DMY(day=3, month=4, year=1950)),
            place=Place(town="London", country="England")
        ),
        occupation="Engineer"
    )
    persons.append(robert_smith)
    
    patricia_brown = Person(
        key="patricia_brown_1955",
        first_name="Patricia",
        surname="Brown",
        sex=Sex.FEMALE,
        birth=Event(
            event_type=PEventType.BIRTH,
            date=Date(dmy=DMY(day=17, month=9, year=1955)),
            place=Place(town="Manchester", country="England")
        ),
        occupation="Nurse"
    )
    persons.append(patricia_brown)
    
    return persons, families


def create_sample_data_simple():
    """Create sample data using simple structures"""
    persons = [
        SimplePerson("john_smith_1920", "John", "Smith", "male", 1920, 1995, "London", "Carpenter"),
        SimplePerson("mary_jones_1925", "Mary", "Jones", "female", 1925, None, "Birmingham", "Teacher"),
        SimplePerson("robert_smith_1950", "Robert", "Smith", "male", 1950, None, "London", "Engineer"),
        SimplePerson("patricia_brown_1955", "Patricia", "Brown", "female", 1955, None, "Manchester", "Nurse"),
        SimplePerson("james_wilson_1960", "James", "Wilson", "male", 1960, None, "Liverpool", "Doctor"),
        SimplePerson("susan_davis_1965", "Susan", "Davis", "female", 1965, None, "York", "Lawyer"),
    ]
    
    families = [
        SimpleFamily("smith_family", "john_smith_1920", "mary_jones_1925", 1945, ["robert_smith_1950"]),
        SimpleFamily("brown_family", "robert_smith_1950", "patricia_brown_1955", 1978, []),
    ]
    
    return persons, families


def demonstrate_simple_search(persons):
    """Demonstrate simple search functionality without complex dependencies"""
    print("\n" + "="*50)
    print("SIMPLE SEARCH DEMONSTRATIONS")
    print("="*50)
    
    def simple_name_search(persons, search_term, field="first_name"):
        """Simple name search implementation"""
        results = []
        search_term = search_term.lower()
        
        for person in persons:
            if field == "first_name":
                if search_term in person.first_name.lower():
                    results.append(person)
            elif field == "surname":
                if search_term in person.surname.lower():
                    results.append(person)
            elif field == "full_name":
                if search_term in person.full_name.lower():
                    results.append(person)
        
        return results
    
    def simple_fuzzy_search(persons, search_term, field="first_name"):
        """Simple fuzzy search using similarity matching"""
        results = []
        search_term = search_term.lower()
        
        for person in persons:
            target = ""
            if field == "first_name":
                target = person.first_name.lower()
            elif field == "surname":
                target = person.surname.lower()
            
            # Calculate similarity
            similarity = SequenceMatcher(None, search_term, target).ratio()
            if similarity > 0.6:  # 60% similarity threshold
                results.append((person, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results]
    
    def simple_date_range_search(persons, min_year, max_year):
        """Simple birth year range search"""
        results = []
        for person in persons:
            if person.birth_year and min_year <= person.birth_year <= max_year:
                results.append(person)
        return results
    
    # Demonstrate searches
    print("\\n1. Exact name search for 'John':")
    results = simple_name_search(persons, "John")
    for person in results:
        print(f"   - {person.full_name} (born {person.birth_year})")
    
    print("\\n2. Fuzzy search for 'Jon' (should find John):")
    results = simple_fuzzy_search(persons, "Jon")
    for person in results:
        print(f"   - {person.full_name} (fuzzy match)")
    
    print("\\n3. Surname search for 'Smith':")
    results = simple_name_search(persons, "Smith", "surname")
    for person in results:
        print(f"   - {person.full_name} ({person.occupation})")
    
    print("\\n4. Birth year range 1950-1965:")
    results = simple_date_range_search(persons, 1950, 1965)
    for person in results:
        print(f"   - {person.full_name} (born {person.birth_year})")
    
    print("\\n5. Occupation-based grouping:")
    occupations = defaultdict(list)
    for person in persons:
        if person.occupation:
            occupations[person.occupation].append(person)
    
    for occupation, people in occupations.items():
        print(f"   {occupation}: {len(people)} person(s)")
        for person in people:
            print(f"     - {person.full_name}")


def demonstrate_full_search(persons, families):
    """Demonstrate full search engine functionality"""
    if not FULL_MODELS_AVAILABLE:
        return
    
    print("\\n" + "="*50)
    print("FULL SEARCH ENGINE DEMONSTRATIONS")
    print("="*50)
    
    # Initialize the search API
    api = GenealogySearchAPI()
    api.load_data(persons, families)
    
    print("\\n1. Basic name search:")
    results = api.search_persons("John", SearchField.FIRST_NAME, SearchType.EXACT)
    for result in results:
        person = result.person
        print(f"   - {person.full_name} (confidence: {result.confidence:.2f})")
    
    print("\\n2. Fuzzy name search:")
    results = api.search_persons("Jon", SearchField.FIRST_NAME, SearchType.FUZZY)
    for result in results:
        person = result.person
        print(f"   - {person.full_name} (confidence: {result.confidence:.2f})")
    
    print("\\n3. Location-based search:")
    results = api.search_persons("London", SearchField.BIRTH_PLACE, SearchType.EXACT)
    for result in results:
        person = result.person
        birth_place = person.birth.place.town if person.birth and person.birth.place else "Unknown"
        print(f"   - {person.full_name} (born in {birth_place})")
    
    print("\\n4. Advanced search - males born 1920-1960:")
    criteria = AdvancedSearchCriteria(
        sex=Sex.MALE,
        birth_year_min=1920,
        birth_year_max=1960
    )
    results = api.advanced_search(criteria)
    for result in results:
        person = result.person
        birth_year = person.birth.date.dmy.year if person.birth and person.birth.date else "Unknown"
        print(f"   - {person.full_name} (born {birth_year})")
    
    print("\\n5. Statistical analysis:")
    stats = api.generate_statistics()
    print(f"   Total persons: {stats.total_persons}")
    print(f"   Total families: {stats.total_families}")
    print(f"   Most common surnames: {list(stats.surname_frequency.most_common(3))}")
    print(f"   Average birth year: {stats.average_birth_year:.1f}")


def run_demo():
    """Run the complete demonstration"""
    print("GENEALOGICAL SEARCH ENGINE DEMO")
    print("=" * 50)
    
    # Create sample data
    if FULL_MODELS_AVAILABLE:
        print("Creating comprehensive genealogical data...")
        persons, families = create_sample_data_full()
        print(f"   Created {len(persons)} persons and {len(families)} families")
        
        # Run full demonstrations
        demonstrate_full_search(persons, families)
    
    # Always run simple demonstration for comparison
    print("\\nCreating simple demonstration data...")
    simple_persons, simple_families = create_sample_data_simple()
    print(f"   Created {len(simple_persons)} persons and {len(simple_families)} families")
    
    demonstrate_simple_search(simple_persons)
    
    print("\\n" + "="*50)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("="*50)
    
    return True


if __name__ == "__main__":
    try:
        success = run_demo()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)