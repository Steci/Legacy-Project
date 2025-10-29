# genealogy_search_api.py

"""
Comprehensive Genealogical Search API
Provides a unified interface to all search capabilities
"""

from typing import List, Dict, Optional, Union, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

# Use only relative imports, as in src/parsers
from search_engine.search_engine import SearchEngine, SearchField, SearchType, AdvancedSearchCriteria, SearchResult
from search_engine.relationship_search import RelationshipSearchEngine, RelationshipType, RelationshipPath
from search_engine.statistics_engine import StatisticsEngine, StatisticsReport, NameStatistics
from models.person.person import Person
from models.family.family import Family

class APIResponse:
    """Standard API response wrapper"""
    
    def __init__(self, success: bool, data: Any = None, message: str = "", error: str = ""):
        self.success = success
        self.data = data
        self.message = message
        self.error = error
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convert response to dictionary"""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'error': self.error,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert response to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)

class GenealogySearchAPI:
    """
    Unified API for all genealogical search and analysis functions
    
    This class provides a clean, consistent interface to:
    - Person search (simple and advanced)
    - Relationship discovery
    - Statistical analysis
    - Data quality checking
    - Export/import functionality
    """
    
    def __init__(self, persons: List[Person], families: List[Family]):
        """Initialize the API with genealogical data"""
        self.persons = persons
        self.families = families
        
        # Initialize search engines
        self.search_engine = SearchEngine(persons, families)
        self.relationship_engine = RelationshipSearchEngine(persons, families)
        self.statistics_engine = StatisticsEngine(persons, families)
        
        # Cache for expensive operations
        self._stats_cache = {}
        self._relationship_cache = {}
    
    # PERSON SEARCH METHODS
    
    def search_persons(self, query: str, field: str = "all", search_type: str = "fuzzy", 
                      max_results: int = 50) -> APIResponse:
        """
        Search for persons using simple criteria
        
        Args:
            query: Search term
            field: Field to search in (all, first_name, surname, full_name, occupation, etc.)
            search_type: Type of search (exact, fuzzy, wildcard, regex, phonetic)
            max_results: Maximum number of results to return
        """
        try:
            # Convert string parameters to enums
            search_field = SearchField(field.lower())
            search_type_enum = SearchType(search_type.lower())
            
            results = self.search_engine.simple_search(
                query, search_field, search_type_enum, max_results
            )
            
            # Convert results to serializable format
            result_data = []
            for result in results:
                result_data.append({
                    'person': result.person.to_dict(),
                    'score': result.score,
                    'matched_fields': result.matched_fields,
                    'match_details': result.match_details
                })
            
            return APIResponse(
                success=True,
                data=result_data,
                message=f"Found {len(results)} persons matching '{query}'"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Search failed: {str(e)}"
            )
    
    def advanced_search_persons(self, criteria: dict) -> APIResponse:
        """
        Advanced person search with multiple criteria
        
        Args:
            criteria: Dictionary containing search criteria
        """
        try:
            # Create AdvancedSearchCriteria from dictionary
            search_criteria = AdvancedSearchCriteria(
                first_name=criteria.get('first_name'),
                surname=criteria.get('surname'),
                public_name=criteria.get('public_name'),
                sex=criteria.get('sex'),
                birth_year_from=criteria.get('birth_year_from'),
                birth_year_to=criteria.get('birth_year_to'),
                death_year_from=criteria.get('death_year_from'),
                death_year_to=criteria.get('death_year_to'),
                birth_place=criteria.get('birth_place'),
                death_place=criteria.get('death_place'),
                spouse_name=criteria.get('spouse_name'),
                parent_name=criteria.get('parent_name'),
                child_name=criteria.get('child_name'),
                occupation=criteria.get('occupation'),
                has_titles=criteria.get('has_titles'),
                notes_contain=criteria.get('notes_contain'),
                sources_contain=criteria.get('sources_contain'),
                alive_in_year=criteria.get('alive_in_year'),
                search_type=SearchType(criteria.get('search_type', 'fuzzy')),
                max_results=criteria.get('max_results', 100),
                min_score=criteria.get('min_score', 0.3)
            )
            
            results = self.search_engine.advanced_search(search_criteria)
            
            # Convert results to serializable format
            result_data = []
            for result in results:
                result_data.append({
                    'person': result.person.to_dict(),
                    'score': result.score,
                    'matched_fields': result.matched_fields,
                    'match_details': result.match_details
                })
            
            return APIResponse(
                success=True,
                data=result_data,
                message=f"Found {len(results)} persons matching advanced criteria"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Advanced search failed: {str(e)}"
            )
    
    def get_suggestions(self, partial_name: str, field: str = "all", max_suggestions: int = 10) -> APIResponse:
        """Get autocomplete suggestions for names"""
        try:
            search_field = SearchField(field.lower())
            suggestions = self.search_engine.get_name_suggestions(
                partial_name, search_field, max_suggestions
            )
            
            return APIResponse(
                success=True,
                data=suggestions,
                message=f"Found {len(suggestions)} suggestions for '{partial_name}'"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Suggestions failed: {str(e)}"
            )
    
    # RELATIONSHIP METHODS
    
    def find_relationship(self, person1_key: str, person2_key: str, max_distance: int = 6) -> APIResponse:
        """Find relationship between two persons"""
        try:
            relationship = self.relationship_engine.find_relationship(
                person1_key, person2_key, max_distance
            )
            
            if relationship:
                data = {
                    'from_person': relationship.from_person.to_dict(),
                    'to_person': relationship.to_person.to_dict(),
                    'relationship_type': relationship.relationship_type.value,
                    'description': relationship.description,
                    'distance': relationship.distance,
                    'path': [person.to_dict() for person in relationship.path]
                }
                
                return APIResponse(
                    success=True,
                    data=data,
                    message=f"Relationship found: {relationship.description}"
                )
            else:
                return APIResponse(
                    success=True,
                    data=None,
                    message="No relationship found within specified distance"
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Relationship search failed: {str(e)}"
            )
    
    def get_all_relatives(self, person_key: str, max_distance: int = 4) -> APIResponse:
        """Get all relatives of a person"""
        try:
            relatives = self.relationship_engine.find_all_relatives(person_key, max_distance)
            
            # Convert to serializable format
            data = {}
            for rel_type, persons in relatives.items():
                data[rel_type.value] = [person.to_dict() for person in persons]
            
            total_relatives = sum(len(persons) for persons in relatives.values())
            
            return APIResponse(
                success=True,
                data=data,
                message=f"Found {total_relatives} relatives across {len(relatives)} relationship types"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Relatives search failed: {str(e)}"
            )
    
    def find_common_ancestors(self, person1_key: str, person2_key: str, max_generations: int = 10) -> APIResponse:
        """Find common ancestors of two persons"""
        try:
            ancestors = self.relationship_engine.find_common_ancestors(
                person1_key, person2_key, max_generations
            )
            
            data = [ancestor.to_dict() for ancestor in ancestors]
            
            return APIResponse(
                success=True,
                data=data,
                message=f"Found {len(ancestors)} common ancestors"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Common ancestors search failed: {str(e)}"
            )
    
    def get_descendants(self, person_key: str, max_generations: int = 10) -> APIResponse:
        """Get all descendants of a person"""
        try:
            descendants = self.relationship_engine.find_descendants(person_key, max_generations)
            
            data = [descendant.to_dict() for descendant in descendants]
            
            return APIResponse(
                success=True,
                data=data,
                message=f"Found {len(descendants)} descendants"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Descendants search failed: {str(e)}"
            )
    
    # STATISTICS METHODS
    
    def get_statistics_report(self, use_cache: bool = True) -> APIResponse:
        """Get comprehensive statistics report"""
        try:
            cache_key = "comprehensive_report"
            
            if use_cache and cache_key in self._stats_cache:
                report = self._stats_cache[cache_key]
            else:
                report = self.statistics_engine.generate_comprehensive_report()
                self._stats_cache[cache_key] = report
            
            # Convert to serializable format
            data = {
                'total_persons': report.total_persons,
                'total_families': report.total_families,
                'living_persons': report.living_persons,
                'deceased_persons': report.deceased_persons,
                'males': report.males,
                'females': report.females,
                'unknown_sex': report.unknown_sex,
                'age_statistics': report.age_statistics,
                'birth_year_range': report.birth_year_range,
                'death_year_range': report.death_year_range,
                'most_common_first_names': report.most_common_first_names,
                'most_common_surnames': report.most_common_surnames,
                'most_common_places': report.most_common_places,
                'most_common_occupations': report.most_common_occupations,
                'generation_statistics': report.generation_statistics,
                'family_size_statistics': report.family_size_statistics,
                'longevity_statistics': report.longevity_statistics
            }
            
            return APIResponse(
                success=True,
                data=data,
                message="Statistics report generated successfully"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Statistics generation failed: {str(e)}"
            )
    
    def analyze_name_popularity(self, name_type: str = "first_name") -> APIResponse:
        """Analyze name popularity over time"""
        try:
            name_stats = self.statistics_engine.analyze_name_popularity(name_type)
            
            # Convert to serializable format
            data = []
            for stat in name_stats:
                data.append({
                    'name': stat.name,
                    'count': stat.count,
                    'first_occurrence_year': stat.first_occurrence_year,
                    'last_occurrence_year': stat.last_occurrence_year,
                    'popularity_by_decade': stat.popularity_by_decade,
                    'associated_places': stat.associated_places
                })
            
            return APIResponse(
                success=True,
                data=data,
                message=f"Analyzed popularity of {len(data)} {name_type.replace('_', ' ')}s"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Name popularity analysis failed: {str(e)}"
            )
    
    def get_data_quality_report(self) -> APIResponse:
        """Get data quality analysis"""
        try:
            completion_stats = self.statistics_engine.calculate_completion_statistics()
            quality_issues = self.statistics_engine.find_data_quality_issues()
            
            data = {
                'completion_statistics': completion_stats,
                'quality_issues': quality_issues,
                'summary': {
                    'total_issues': sum(len(cases) for cases in quality_issues.values()),
                    'issue_types': len(quality_issues),
                    'average_completion': sum(completion_stats.values()) / len(completion_stats) if completion_stats else 0
                }
            }
            
            return APIResponse(
                success=True,
                data=data,
                message="Data quality report generated successfully"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Data quality analysis failed: {str(e)}"
            )
    
    # UTILITY METHODS
    
    def find_duplicates(self, threshold: float = 0.85) -> APIResponse:
        """Find possible duplicate persons"""
        try:
            duplicates = self.search_engine.find_possible_duplicates(threshold)
            
            # Convert to serializable format
            data = []
            for person1, person2, score in duplicates:
                data.append({
                    'person1': person1.to_dict(),
                    'person2': person2.to_dict(),
                    'similarity_score': score
                })
            
            return APIResponse(
                success=True,
                data=data,
                message=f"Found {len(duplicates)} possible duplicate pairs"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Duplicate detection failed: {str(e)}"
            )
    
    def get_person_by_key(self, person_key: str) -> APIResponse:
        """Get a specific person by their key"""
        try:
            person = next((p for p in self.persons if p.key == person_key), None)
            
            if person:
                return APIResponse(
                    success=True,
                    data=person.to_dict(),
                    message=f"Person found: {person.full_name}"
                )
            else:
                return APIResponse(
                    success=False,
                    error=f"Person with key '{person_key}' not found"
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Person lookup failed: {str(e)}"
            )
    
    def get_family_by_key(self, family_key: str) -> APIResponse:
        """Get a specific family by their key"""
        try:
            family = next((f for f in self.families if f.key == family_key), None)
            
            if family:
                return APIResponse(
                    success=True,
                    data=family.to_dict(),
                    message=f"Family found: {family.key}"
                )
            else:
                return APIResponse(
                    success=False,
                    error=f"Family with key '{family_key}' not found"
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Family lookup failed: {str(e)}"
            )
    
    def export_search_results(self, results: List[SearchResult], format: str = "json") -> APIResponse:
        """Export search results in specified format"""
        try:
            if format.lower() == "json":
                data = []
                for result in results:
                    data.append({
                        'person': result.person.to_dict(),
                        'score': result.score,
                        'matched_fields': result.matched_fields,
                        'match_details': result.match_details
                    })
                
                return APIResponse(
                    success=True,
                    data=data,
                    message=f"Exported {len(results)} search results as JSON"
                )
            else:
                return APIResponse(
                    success=False,
                    error=f"Unsupported export format: {format}"
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Export failed: {str(e)}"
            )
    
    def get_api_info(self) -> APIResponse:
        """Get information about the API and loaded data"""
        try:
            data = {
                'api_version': '1.0.0',
                'data_summary': {
                    'total_persons': len(self.persons),
                    'total_families': len(self.families),
                    'search_capabilities': [
                        'Simple person search',
                        'Advanced person search',
                        'Relationship discovery',
                        'Statistical analysis',
                        'Duplicate detection',
                        'Name suggestions'
                    ]
                },
                'available_endpoints': [
                    'search_persons',
                    'advanced_search_persons',
                    'find_relationship',
                    'get_all_relatives',
                    'get_statistics_report',
                    'analyze_name_popularity',
                    'find_duplicates'
                ]
            }
            
            return APIResponse(
                success=True,
                data=data,
                message="API information retrieved successfully"
            )
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"API info retrieval failed: {str(e)}"
            )