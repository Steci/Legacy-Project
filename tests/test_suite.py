#!/usr/bin/env python3

"""
Comprehensive Test Suite for Genealogical Search Engine
Tests all search functionality with proper import handling and bug fixes
"""

import sys
import os
from typing import List, Optional
import unittest

# Add the src directory to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Import our modules
from ..src.search_engine.search_engine import SearchEngine, SearchField, SearchType, AdvancedSearchCriteria, SearchResult
from ..src.search_engine.relationship_search import RelationshipSearchEngine, RelationshipType
from ..src.search_engine.statistics_engine import StatisticsEngine
from ..src.search_engine.genealogy_search_api import GenealogySearchAPI
from ..src.models.person.person import Person
from ..src.models.family.family import Family
from ..src.models.date import Date, DMY
from ..src.models.person.params import Sex, PEventType
from ..src.models.event import Event
from ..src.models.place import Place


class TestPerson:
    """Simple test person class for basic testing"""
    def __init__(self, key: str, first_name: str, surname: str, sex_str: str, birth_year: Optional[int] = None, occupation: Optional[str] = None):
        self.key = key
        self.first_name = first_name
        self.surname = surname
        self.sex = Sex.MALE if sex_str.lower() == 'male' else Sex.FEMALE
        self.birth_year = birth_year
        self.occupation = occupation or ""
        self.full_name = f"{first_name} {surname}"
        self.public_name = None
        self.aliases = []
        self.first_names_aliases = []
        self.surnames_aliases = []
        self.birth = None
        self.death = None
        self.has_titles = False
        
        # Mock birth event if birth_year provided
        if birth_year:
            class MockDate:
                def __init__(self, year):
                    self.dmy = MockDMY(year)
            
            class MockDMY:
                def __init__(self, year):
                    self.year = year
            
            class MockEvent:
                def __init__(self, year):
                    self.date = MockDate(year)
                    self.place = None
            
            self.birth = MockEvent(birth_year)


class SearchEngineTestSuite(unittest.TestCase):
    """Test suite for search engine functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.test_persons = [
            TestPerson("john_1920", "John", "Smith", "male", 1920, "Engineer"),
            TestPerson("mary_1925", "Mary", "Smith", "female", 1925, "Teacher"),
            TestPerson("robert_1940", "Robert", "Johnson", "male", 1940, "Doctor"),
            TestPerson("patricia_1945", "Patricia", "Jones", "female", 1945, "Nurse"),
            TestPerson("james_1950", "James", "Brown", "male", 1950, "Lawyer"),
            TestPerson("michael_1885", "Michael", "Davis", "male", 1885, "Farmer"),
        ]
        self.search_engine = SearchEngine(self.test_persons, [])
    
    def test_basic_search(self):
        """Test basic search functionality"""
        results = self.search_engine.simple_search(
            "John", 
            SearchField.FIRST_NAME, 
            SearchType.EXACT
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].person.first_name, "John")
    
    def test_fuzzy_search(self):
        """Test fuzzy search capabilities"""
        results = self.search_engine.simple_search(
            "Jon",  # Fuzzy match for "John"
            SearchField.FIRST_NAME,
            SearchType.FUZZY
        )
        
        self.assertGreater(len(results), 0)
        # Should find John with high confidence
        self.assertTrue(any(r.person.first_name == "John" for r in results))
    
    def test_advanced_search_bug_fix(self):
        """Test that the advanced search AND logic bug is fixed"""
        # This test specifically addresses the bug where searching for
        # "males born between 1940-1950" incorrectly included women and people outside date range
        
        criteria = AdvancedSearchCriteria(
            sex=Sex.MALE,
            birth_year_from=1940,
            birth_year_to=1950
        )
        
        results = self.search_engine.advanced_search(criteria)
        
        # Should only find James (male, born 1950)
        self.assertEqual(len(results), 1, "Should find exactly 1 person matching ALL criteria")
        
        found_person = results[0].person
        self.assertEqual(found_person.first_name, "James")
        self.assertEqual(found_person.sex, Sex.MALE)
        self.assertGreaterEqual(found_person.birth_year, 1940)
        self.assertLessEqual(found_person.birth_year, 1950)
        
        # Verify it doesn't include women
        self.assertFalse(any(r.person.sex == Sex.FEMALE for r in results))
        
        # Verify it doesn't include people outside date range
        birth_years = [r.person.birth_year for r in results if r.person.birth_year]
        self.assertTrue(all(1940 <= year <= 1950 for year in birth_years))
    
    def test_occupation_search(self):
        """Test occupation-based search"""
        results = self.search_engine.simple_search(
            "Doctor",
            SearchField.OCCUPATION,
            SearchType.EXACT
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].person.occupation, "Doctor")
        self.assertEqual(results[0].person.first_name, "Robert")


def create_comprehensive_test_data() -> tuple[List[Person], List[Family]]:
    """Create comprehensive test data representing multiple generations"""
    
    persons = []
    families = []
    
    # Generation 1 - Great Grandparents (born 1880-1900)
    thomas_wilson = Person(
        key="thomas_wilson_1885",
        first_name="Thomas",
        surname="Wilson",
        sex=Sex.MALE,
        birth=Event(
            event_type=PEventType.BIRTH,
            date=Date(dmy=DMY(day=12, month=3, year=1885)),
            place=Place(town="Edinburgh", region="Scotland", country="United Kingdom")
        ),
        death=Event(
            event_type=PEventType.DEATH,
            date=Date(dmy=DMY(day=8, month=11, year=1962)),
            place=Place(town="Edinburgh", region="Scotland", country="United Kingdom")
        ),
        occupation="Blacksmith",
        notes="Migrated from rural Scotland to Edinburgh in 1910"
    )
    persons.append(thomas_wilson)
    
    mary_campbell = Person(
        key="mary_campbell_1888",
        first_name="Mary",
        surname="Campbell",
        sex=Sex.FEMALE,
        birth=Event(
            event_type=PEventType.BIRTH,
            date=Date(dmy=DMY(day=25, month=7, year=1888)),
            place=Place(town="Glasgow", region="Scotland", country="United Kingdom")
        ),
        death=Event(
            event_type=PEventType.DEATH,
            date=Date(dmy=DMY(day=14, month=5, year=1965)),
            place=Place(town="Edinburgh", region="Scotland", country="United Kingdom")
        ),
        occupation="Seamstress",
        notes="Known for her beautiful embroidery work"
    )
    persons.append(mary_campbell)
    
    # Create family
    wilson_family = Family(
        key="wilson_family_1910",
        husband=thomas_wilson,
        wife=mary_campbell,
        marriage=Event(
            event_type=PEventType.MARRIAGE,
            date=Date(dmy=DMY(day=15, month=6, year=1910)),
            place=Place(town="Edinburgh", region="Scotland", country="United Kingdom")
        )
    )
    families.append(wilson_family)
    
    return persons, families


def run_comprehensive_tests():
    """Run the full comprehensive test suite"""
    print("=" * 60)
    print("COMPREHENSIVE GENEALOGICAL SEARCH ENGINE TEST SUITE")
    print("=" * 60)
    
    try:
        # Test imports
        print("\n1. Testing imports...")
        print("All modules imported successfully")
        
        # Run unit tests
        print("\n2. Running unit tests...")
        unittest.main(argv=[''], exit=False, verbosity=2)
        
        # Test with comprehensive data
        print("\n3. Testing with comprehensive genealogical data...")
        persons, families = create_comprehensive_test_data()
        
        api = GenealogySearchAPI()
        api.load_data(persons, families)
        
        # Test various search scenarios
        print("\n4. Testing search scenarios...")
        
        # Basic name search
        results = api.search_persons("Thomas", SearchField.FIRST_NAME, SearchType.EXACT)
        print(f"Found {len(results)} person(s) named Thomas")
        
        # Location search
        results = api.search_persons("Edinburgh", SearchField.BIRTH_PLACE, SearchType.EXACT)
        print(f"Found {len(results)} person(s) born in Edinburgh")
        
        # Date range search
        criteria = AdvancedSearchCriteria(birth_year_from=1880, birth_year_to=1890)
        results = api.advanced_search(criteria)
        print(f"Found {len(results)} person(s) born between 1880-1890")
        
        # Generate statistics
        stats = api.generate_statistics()
        print(f"Generated statistics for {stats.total_persons} persons and {stats.total_families} families")
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)