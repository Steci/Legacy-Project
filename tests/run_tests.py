#!/usr/bin/env python3
"""
Test runner for the reorganized genealogical search engine

This script properly sets up the Python path to allow the tests to import
from the ..src package using relative imports.
"""

import sys
import os

# Add the current directory to Python path so 'src' can be imported
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all imports work correctly"""
    print("Testing reorganized search engine structure...")
    
    try:
        # Test imports from the reorganized packages
        from ..src.search_engine import SearchEngine, AdvancedSearchCriteria, SearchField, SearchType
        from ..src.models.person.params import Sex
        from ..src.models import Person, Family, Date
        
        print("✅ All imports successful!")
        
        # Create a simple test
        search_engine = SearchEngine()
        print(f"✅ SearchEngine created: {type(search_engine)}")
        
        # Test basic functionality
        criteria = AdvancedSearchCriteria()
        print(f"✅ AdvancedSearchCriteria created: {type(criteria)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_simple_search_test():
    """Run a simple search test to verify everything works"""
    print("\n" + "="*50)
    print("Running simple search test...")
    
    try:
        from ..src.search_engine import SearchEngine, AdvancedSearchCriteria, SearchField, SearchType
        from ..src.models import Person, Sex
        
        # Create test data
        people = [
            Person(
                key="1",
                first_name="John",
                surname="Smith", 
                sex=Sex.MALE,
                birth_year=1985
            ),
            Person(
                key="2", 
                first_name="Jane",
                surname="Smith",
                sex=Sex.FEMALE,
                birth_year=1987
            )
        ]
        
        # Create search engine
        search_engine = SearchEngine()
        
        # Test simple search
        results = search_engine.search_people(people, "John")
        print(f"✅ Found {len(results)} results for 'John'")
        
        # Test advanced search
        criteria = AdvancedSearchCriteria()
        criteria.add_criterion(SearchField.SEX, "Male")
        
        advanced_results = search_engine.advanced_search(people, criteria)
        print(f"✅ Found {len(advanced_results)} male people")
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Genealogical Search Engine - Test Suite")
    print("="*50)
    
    # Test imports first
    if test_imports():
        # If imports work, run functional tests
        run_simple_search_test()
    else:
        print("Import tests failed, skipping functional tests")
        sys.exit(1)