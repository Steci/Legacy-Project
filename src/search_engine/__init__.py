"""
Genealogical Search Engine Package

This package provides comprehensive search capabilities for genealogical data:
- Person and family search with fuzzy matching
- Relationship discovery and family tree traversal  
- Statistical analysis and data quality assessment
- Unified API for all search functionality
"""

# Import individual modules - this will work when the directory is added to sys.path
from .search_engine import SearchEngine, SearchField, SearchType, AdvancedSearchCriteria, SearchResult
from .relationship_search import RelationshipSearchEngine, RelationshipType, RelationshipPath
from .statistics_engine import StatisticsEngine, StatisticsReport, NameStatistics
from .genealogy_search_api import GenealogySearchAPI, APIResponse

__all__ = [
    'SearchEngine',
    'SearchField', 
    'SearchType',
    'AdvancedSearchCriteria',
    'SearchResult',
    'RelationshipSearchEngine',
    'RelationshipType', 
    'RelationshipPath',
    'StatisticsEngine',
    'StatisticsReport',
    'NameStatistics',
    'GenealogySearchAPI',
    'APIResponse'
]

__version__ = '1.0.0'