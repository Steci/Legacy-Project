# statistics_engine.py

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
from datetime import datetime
import statistics

try:
    # Try relative imports first (when imported as a package)
    from ..models.person.person import Person
    from ..models.family.family import Family
    from ..models.date import Date, DMY
    from ..models.person.params import Sex
except ImportError:
    # Fall back to absolute imports (when imported directly)
    from models.person.person import Person
    from models.family.family import Family
    from models.date import Date, DMY
    from models.person.params import Sex

@dataclass
class StatisticsReport:
    total_persons: int
    total_families: int
    living_persons: int
    deceased_persons: int
    males: int
    females: int
    unknown_sex: int
    age_statistics: Dict[str, float]
    birth_year_range: Tuple[Optional[int], Optional[int]]
    death_year_range: Tuple[Optional[int], Optional[int]]
    most_common_first_names: List[Tuple[str, int]]
    most_common_surnames: List[Tuple[str, int]]
    most_common_places: List[Tuple[str, int]]
    most_common_occupations: List[Tuple[str, int]]
    generation_statistics: Dict[str, int]
    family_size_statistics: Dict[str, float]
    longevity_statistics: Dict[str, float]

@dataclass
class NameStatistics:
    name: str
    count: int
    first_occurrence_year: Optional[int]
    last_occurrence_year: Optional[int]
    popularity_by_decade: Dict[int, int]
    associated_places: List[str]

class StatisticsEngine:
    """Engine for generating genealogical statistics and analysis"""
    
    def __init__(self, persons: List[Person], families: List[Family]):
        self.persons = persons
        self.families = families
    
    def generate_comprehensive_report(self) -> StatisticsReport:
        """Generate a comprehensive statistics report"""
        
        # Basic counts
        total_persons = len(self.persons)
        total_families = len(self.families)
        
        # Sex distribution
        sex_counts = Counter(person.sex for person in self.persons)
        males = sex_counts.get(Sex.MALE, 0)
        females = sex_counts.get(Sex.FEMALE, 0)
        unknown_sex = total_persons - males - females
        
        # Living/deceased status
        deceased_persons = sum(1 for person in self.persons if person.death is not None)
        living_persons = total_persons - deceased_persons
        
        # Age statistics
        ages = self._calculate_ages()
        age_statistics = self._calculate_age_statistics(ages)
        
        # Year ranges
        birth_years = [self._extract_year_from_event(person.birth) for person in self.persons 
                      if person.birth and self._extract_year_from_event(person.birth)]
        death_years = [self._extract_year_from_event(person.death) for person in self.persons 
                      if person.death and self._extract_year_from_event(person.death)]
        
        birth_year_range = (min(birth_years) if birth_years else None, 
                           max(birth_years) if birth_years else None)
        death_year_range = (min(death_years) if death_years else None,
                           max(death_years) if death_years else None)
        
        # Name statistics
        first_names = [person.first_name for person in self.persons if person.first_name]
        surnames = [person.surname for person in self.persons if person.surname]
        most_common_first_names = Counter(first_names).most_common(10)
        most_common_surnames = Counter(surnames).most_common(10)
        
        # Place statistics
        places = []
        for person in self.persons:
            for event in [person.birth, person.baptism, person.death, person.burial]:
                if event and event.place:
                    place_str = self._extract_place_string(event.place)
                    if place_str:
                        places.append(place_str)
        most_common_places = Counter(places).most_common(10)
        
        # Occupation statistics
        occupations = [person.occupation for person in self.persons if person.occupation]
        most_common_occupations = Counter(occupations).most_common(10)
        
        # Generation statistics
        generation_statistics = self._calculate_generation_statistics()
        
        # Family size statistics
        family_size_statistics = self._calculate_family_size_statistics()
        
        # Longevity statistics
        longevity_statistics = self._calculate_longevity_statistics()
        
        return StatisticsReport(
            total_persons=total_persons,
            total_families=total_families,
            living_persons=living_persons,
            deceased_persons=deceased_persons,
            males=males,
            females=females,
            unknown_sex=unknown_sex,
            age_statistics=age_statistics,
            birth_year_range=birth_year_range,
            death_year_range=death_year_range,
            most_common_first_names=most_common_first_names,
            most_common_surnames=most_common_surnames,
            most_common_places=most_common_places,
            most_common_occupations=most_common_occupations,
            generation_statistics=generation_statistics,
            family_size_statistics=family_size_statistics,
            longevity_statistics=longevity_statistics
        )
    
    def _extract_year_from_event(self, event) -> Optional[int]:
        """Extract year from an event"""
        if event and event.date and event.date.dmy and event.date.dmy.year > 0:
            return event.date.dmy.year
        return None
    
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
        return ", ".join(parts)
    
    def _calculate_ages(self) -> List[int]:
        """Calculate ages for all deceased persons"""
        ages = []
        for person in self.persons:
            birth_year = self._extract_year_from_event(person.birth)
            death_year = self._extract_year_from_event(person.death)
            
            if birth_year and death_year and death_year > birth_year:
                age = death_year - birth_year
                if 0 <= age <= 150:  # Reasonable age range
                    ages.append(age)
        
        return ages
    
    def _calculate_age_statistics(self, ages: List[int]) -> Dict[str, float]:
        """Calculate age statistics"""
        if not ages:
            return {}
        
        return {
            'mean': statistics.mean(ages),
            'median': statistics.median(ages),
            'mode': statistics.mode(ages) if ages else 0,
            'min': min(ages),
            'max': max(ages),
            'std_dev': statistics.stdev(ages) if len(ages) > 1 else 0
        }
    
    def _calculate_generation_statistics(self) -> Dict[str, int]:
        """Calculate statistics about generations"""
        # Build parent-child relationships
        children_count = defaultdict(int)
        has_parents = set()
        
        for family in self.families:
            num_children = len(family.children_keys)
            if family.parent1_key:
                children_count[family.parent1_key] += num_children
            if family.parent2_key:
                children_count[family.parent2_key] += num_children
            
            for child_key in family.children_keys:
                has_parents.add(child_key)
        
        # Calculate statistics
        root_ancestors = len([p for p in self.persons if p.key not in has_parents])
        childless_persons = len([p for p in self.persons if children_count[p.key] == 0])
        persons_with_children = len([p for p in self.persons if children_count[p.key] > 0])
        
        return {
            'root_ancestors': root_ancestors,
            'childless_persons': childless_persons,
            'persons_with_children': persons_with_children,
            'orphans': len(self.persons) - len(has_parents)
        }
    
    def _calculate_family_size_statistics(self) -> Dict[str, float]:
        """Calculate family size statistics"""
        family_sizes = [len(family.children_keys) for family in self.families]
        
        if not family_sizes:
            return {}
        
        return {
            'mean_children': statistics.mean(family_sizes),
            'median_children': statistics.median(family_sizes),
            'max_children': max(family_sizes),
            'families_with_no_children': sum(1 for size in family_sizes if size == 0),
            'large_families': sum(1 for size in family_sizes if size >= 5)
        }
    
    def _calculate_longevity_statistics(self) -> Dict[str, float]:
        """Calculate longevity statistics by various factors"""
        ages_by_sex = defaultdict(list)
        ages_by_century = defaultdict(list)
        
        for person in self.persons:
            birth_year = self._extract_year_from_event(person.birth)
            death_year = self._extract_year_from_event(person.death)
            
            if birth_year and death_year and death_year > birth_year:
                age = death_year - birth_year
                if 0 <= age <= 150:
                    ages_by_sex[person.sex].append(age)
                    
                    # Group by birth century
                    century = (birth_year // 100) * 100
                    ages_by_century[century].append(age)
        
        statistics_dict = {}
        
        # Sex-based longevity
        for sex, ages in ages_by_sex.items():
            if ages:
                statistics_dict[f'mean_age_{sex.value}'] = statistics.mean(ages)
        
        # Century-based longevity
        for century, ages in ages_by_century.items():
            if ages and len(ages) >= 5:  # Only include centuries with enough data
                statistics_dict[f'mean_age_{century}s'] = statistics.mean(ages)
        
        return statistics_dict
    
    def analyze_name_popularity(self, name_type: str = "first_name") -> List[NameStatistics]:
        """Analyze name popularity over time"""
        name_data = defaultdict(lambda: {
            'count': 0,
            'years': [],
            'places': []
        })
        
        for person in self.persons:
            name = getattr(person, name_type, None)
            if not name:
                continue
            
            birth_year = self._extract_year_from_event(person.birth)
            if birth_year:
                name_data[name]['years'].append(birth_year)
            
            name_data[name]['count'] += 1
            
            # Collect places
            for event in [person.birth, person.baptism]:
                if event and event.place:
                    place_str = self._extract_place_string(event.place)
                    if place_str:
                        name_data[name]['places'].append(place_str)
        
        # Create NameStatistics objects
        name_stats = []
        for name, data in name_data.items():
            years = data['years']
            popularity_by_decade = defaultdict(int)
            
            for year in years:
                decade = (year // 10) * 10
                popularity_by_decade[decade] += 1
            
            name_stats.append(NameStatistics(
                name=name,
                count=data['count'],
                first_occurrence_year=min(years) if years else None,
                last_occurrence_year=max(years) if years else None,
                popularity_by_decade=dict(popularity_by_decade),
                associated_places=list(set(data['places']))
            ))
        
        # Sort by popularity
        name_stats.sort(key=lambda x: x.count, reverse=True)
        return name_stats
    
    def find_migration_patterns(self) -> Dict[str, List[Tuple[str, str, int]]]:
        """Find migration patterns between places"""
        migrations = defaultdict(list)
        
        for person in self.persons:
            birth_place = None
            death_place = None
            
            if person.birth and person.birth.place:
                birth_place = self._extract_place_string(person.birth.place)
            
            if person.death and person.death.place:
                death_place = self._extract_place_string(person.death.place)
            
            if birth_place and death_place and birth_place != death_place:
                birth_year = self._extract_year_from_event(person.birth)
                if birth_year:
                    migrations[birth_place].append((death_place, person.full_name, birth_year))
        
        # Aggregate migrations
        migration_patterns = {}
        for from_place, moves in migrations.items():
            to_places = defaultdict(int)
            for to_place, _, _ in moves:
                to_places[to_place] += 1
            
            migration_patterns[from_place] = [(place, count, 0) for place, count in to_places.most_common()]
        
        return migration_patterns
    
    def calculate_completion_statistics(self) -> Dict[str, float]:
        """Calculate data completion statistics"""
        total = len(self.persons)
        if total == 0:
            return {}
        
        stats = {}
        
        # Basic fields completion
        stats['has_birth_date'] = sum(1 for p in self.persons if p.birth and p.birth.date) / total * 100
        stats['has_death_date'] = sum(1 for p in self.persons if p.death and p.death.date) / total * 100
        stats['has_birth_place'] = sum(1 for p in self.persons if p.birth and p.birth.place) / total * 100
        stats['has_death_place'] = sum(1 for p in self.persons if p.death and p.death.place) / total * 100
        stats['has_occupation'] = sum(1 for p in self.persons if p.occupation) / total * 100
        stats['has_notes'] = sum(1 for p in self.persons if p.notes) / total * 100
        stats['has_sources'] = sum(1 for p in self.persons if p.sources) / total * 100
        
        # Family relationship completion
        persons_with_families = sum(1 for p in self.persons 
                                  if any(f for f in self.families 
                                        if p.key in f.children_keys or p.key == f.parent1_key or p.key == f.parent2_key))
        stats['has_family_connections'] = persons_with_families / total * 100
        
        return stats
    
    def find_data_quality_issues(self) -> Dict[str, List[str]]:
        """Find potential data quality issues"""
        issues = defaultdict(list)
        
        for person in self.persons:
            # Check for impossible dates
            birth_year = self._extract_year_from_event(person.birth)
            death_year = self._extract_year_from_event(person.death)
            
            if birth_year and death_year:
                age = death_year - birth_year
                if age < 0:
                    issues['death_before_birth'].append(f"{person.full_name} (Birth: {birth_year}, Death: {death_year})")
                elif age > 120:
                    issues['unusually_long_life'].append(f"{person.full_name} (Age: {age})")
            
            # Check for missing critical data
            if not person.first_name and not person.surname:
                issues['missing_names'].append(person.key)
            
            if not person.birth and not person.death:
                issues['no_vital_dates'].append(f"{person.full_name}")
            
            # Check for very early or late dates
            if birth_year and (birth_year < 1000 or birth_year > datetime.now().year):
                issues['suspicious_birth_year'].append(f"{person.full_name} (Birth: {birth_year})")
        
        return dict(issues)