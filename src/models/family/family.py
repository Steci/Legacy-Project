# family/family.py

from typing import List, Optional, Union
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import json

from ..event import Event, Witness
from ..date import Date

class RelationKind(Enum):
    MARRIED = "married"
    NOT_MARRIED = "not_married"
    PACS = "pacs"
    ENGAGED = "engaged"
    SEPARATED = "separated"
    DIVORCED = "divorced"
    UNKNOWN = "unknown"

@dataclass
class Family:
    parent1: int = 0
    parent2: int = 0
    children: List[int] = field(default_factory=list) # List of unique identifiers of children
    relation: RelationKind = RelationKind.UNKNOWN

    marriage: Optional['Event'] = None
    divorce: Optional['Event'] = None
    events: List['Event'] = field(default_factory=list)

    notes: Optional[str] = None
    origin_file: Optional[str] = None
    sources: Optional[str] = None
    key_index: Optional[int] = None  # Unique identifier for the family

    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Validate basic constraints
        if self.parent1 == 0 and self.parent2 == 0:
            raise ValueError("Family must have at least one parent")
        if self.parent1 == self.parent2 and self.parent1 != 0:
            raise ValueError("Parents cannot be the same person")
        if self.key_index is not None and self.key_index < 0:
            raise ValueError("Key index cannot be negative")
        # Check for duplicate children
        if len(self.children) != len(set(self.children)):
            raise ValueError("Duplicate children found")

    # Properties for most common getters (Pythonic way)
    @property
    def children_count(self) -> int:
        """Get number of children"""
        return len(self.children)
    
    @property
    def has_children(self) -> bool:
        """Check if family has any children"""
        return len(self.children) > 0

    def add_child(self, index: int):
        if index not in self.children:
            self.children.append(index)

    def add_event(self, event: Event):
        self.events.append(event)

    # Getter methods (following Geneweb Driver pattern)
    def get_parent1(self) -> int:
        """Get first parent ID"""
        return self.parent1
    
    def get_parent2(self) -> int:
        """Get second parent ID"""
        return self.parent2
    
    def get_children(self) -> List[int]:
        """Get list of children IDs"""
        return self.children.copy()
    
    def get_relation(self) -> RelationKind:
        """Get relation kind between couple"""
        return self.relation
    
    def get_marriage(self) -> Optional[Event]:
        """Get marriage event"""
        return self.marriage
    
    def get_divorce(self) -> Optional[Event]:
        """Get divorce event"""
        return self.divorce
    
    def get_events(self) -> List[Event]:
        """Get all family events"""
        return self.events.copy()
    
    def get_notes(self) -> Optional[str]:
        """Get family notes/comments"""
        return self.notes
    
    def get_origin_file(self) -> Optional[str]:
        """Get origin file (e.g., .gw or .ged filename)"""
        return self.origin_file
    
    def get_sources(self) -> Optional[str]:
        """Get family sources"""
        return self.sources
    
    def get_key_index(self) -> Optional[int]:
        """Get unique family identifier"""
        return self.key_index
    
    def get_parent_array(self) -> List[int]:
        """Get array of parent IDs [parent1, parent2]"""
        return [self.parent1, self.parent2]
    
    def get_witnesses(self) -> List[Witness]:
        """Get witnesses from marriage event"""
        if self.marriage and self.marriage.witnesses:
            return self.marriage.witnesses.copy()
        return []

    # Setter methods
    def set_parent1(self, parent_id: int):
        """Set first parent ID"""
        self.parent1 = parent_id
    
    def set_parent2(self, parent_id: int):
        """Set second parent ID"""
        self.parent2 = parent_id
    
    # Note: Removed set_father/set_mother methods to maintain inclusive naming
    # Use set_parent1/set_parent2 instead
    
    def set_relation(self, relation: RelationKind):
        """Set relation kind between couple"""
        self.relation = relation
    
    def set_marriage(self, marriage: Optional[Event]):
        """Set marriage event"""
        self.marriage = marriage
    
    def set_divorce(self, divorce: Optional[Event]):
        """Set divorce event"""
        self.divorce = divorce
    
    def set_notes(self, notes: Optional[str]):
        """Set family notes/comments"""
        self.notes = notes
    
    def set_origin_file(self, origin_file: Optional[str]):
        """Set origin file"""
        self.origin_file = origin_file
    
    def set_sources(self, sources: Optional[str]):
        """Set family sources"""
        self.sources = sources
    
    def set_key_index(self, key_index: Optional[int]):
        """Set unique family identifier"""
        self.key_index = key_index

    # List manipulation methods
    def remove_child(self, index: int):
        """Remove a child ID"""
        if index in self.children:
            self.children.remove(index)
    
    def remove_event(self, event: Event):
        """Remove a family event"""
        if event in self.events:
            self.events.remove(event)
    
    def clear_children(self):
        """Remove all children"""
        self.children.clear()
    
    def clear_events(self):
        """Remove all events"""
        self.events.clear()

    # Event creation helper methods
    def create_marriage_event(self, date: Optional[Date] = None, place: Optional[str] = None,
                             note: Optional[str] = None, source: Optional[str] = None,
                             witnesses: Optional[List[Witness]] = None) -> Event:
        """Create a marriage event"""
        from ..event import Place
        place_obj = Place(other=place) if place else None
        event = Event(name="Marriage", date=date, place=place_obj,
                     note=note, source=source, witnesses=witnesses or [])
        self.marriage = event
        return event
    
    def create_divorce_event(self, date: Optional[Date] = None, place: Optional[str] = None,
                            note: Optional[str] = None, source: Optional[str] = None) -> Event:
        """Create a divorce event"""
        from ..event import Place
        place_obj = Place(other=place) if place else None
        event = Event(name="Divorce", date=date, place=place_obj,
                     note=note, source=source)
        self.divorce = event
        return event

    # Date helper methods
    def _extract_date_from_event(self, event: Event) -> Optional[Date]:
        """Extract date from an event"""
        return event.date if event else None
    
    def _compare_dates(self, date1: Date, date2: Date) -> int:
        """Compare two dates. Returns -1 if date1 < date2, 0 if equal, 1 if date1 > date2"""
        if not date1 or not date2 or not date1.dmy or not date2.dmy:
            return 0  # Cannot compare incomplete dates
        
        # Compare years first
        if date1.dmy.year != date2.dmy.year:
            return 1 if date1.dmy.year > date2.dmy.year else -1
        
        # Compare months
        if date1.dmy.month != date2.dmy.month:
            return 1 if date1.dmy.month > date2.dmy.month else -1
        
        # Compare days
        if date1.dmy.day != date2.dmy.day:
            return 1 if date1.dmy.day > date2.dmy.day else -1
        
        return 0  # Dates are equal
    
    def get_marriage_date(self) -> Optional[Date]:
        """Get marriage date from marriage event"""
        return self._extract_date_from_event(self.marriage)
    
    def get_divorce_date(self) -> Optional[Date]:
        """Get divorce date from divorce event"""
        return self._extract_date_from_event(self.divorce)
    
    def get_marriage_place(self) -> Optional[str]:
        """Get marriage place from marriage event"""
        if self.marriage and self.marriage.place:
            return self.marriage.place.other or f"{self.marriage.place.town}, {self.marriage.place.country}".strip(', ')
        return None
    
    def get_divorce_place(self) -> Optional[str]:
        """Get divorce place from divorce event"""
        if self.divorce and self.divorce.place:
            return self.divorce.place.other or f"{self.divorce.place.town}, {self.divorce.place.country}".strip(', ')
        return None

    # Relationship status methods
    def is_married(self) -> bool:
        """Check if couple is married"""
        return self.relation == RelationKind.MARRIED
    
    def is_divorced(self) -> bool:
        """Check if couple is divorced"""
        return self.relation == RelationKind.DIVORCED or self.divorce is not None
    
    def is_separated(self) -> bool:
        """Check if couple is separated"""
        return self.relation == RelationKind.SEPARATED
    
    def is_engaged(self) -> bool:
        """Check if couple is engaged"""
        return self.relation == RelationKind.ENGAGED
    
    def has_marriage_event(self) -> bool:
        """Check if family has a marriage event"""
        return self.marriage is not None
    
    def has_divorce_event(self) -> bool:
        """Check if family has a divorce event"""
        return self.divorce is not None
    
    def has_children(self) -> bool:
        """Check if family has any children"""
        return len(self.children) > 0
    
    def get_children_count(self) -> int:
        """Get number of children - DEPRECATED: use .children_count property"""
        return self.children_count
    
    def has_witnesses(self) -> bool:
        """Check if marriage has witnesses"""
        return len(self.get_witnesses()) > 0

    # Utility methods
    def spouse(self, person_id: int) -> Optional[int]:
        """Get spouse ID for given person ID"""
        if person_id == self.parent1:
            return self.parent2
        elif person_id == self.parent2:
            return self.parent1
        return None
    
    def is_parent(self, person_id: int) -> bool:
        """Check if person is a parent in this family"""
        return person_id == self.parent1 or person_id == self.parent2
    
    def is_child(self, person_id: int) -> bool:
        """Check if person is a child in this family"""
        return person_id in self.children
    
    def get_child_position(self, child_id: int) -> Optional[int]:
        """Get position of child in children list (0-based)"""
        try:
            return self.children.index(child_id)
        except ValueError:
            return None
    
    def reorder_children(self, new_order: List[int]):
        """Reorder children according to new order list"""
        if set(new_order) == set(self.children):
            self.children = new_order
        else:
            raise ValueError("New order must contain exactly the same children IDs")
    
    def move_child_to_position(self, child_id: int, new_position: int):
        """Move child to specific position in children list"""
        if child_id in self.children:
            self.children.remove(child_id)
            self.children.insert(new_position, child_id)

    # Search and query methods
    def find_events_by_type(self, event_type: str) -> List[Event]:
        """Find all events of a specific type"""
        return [event for event in self.events if event.name.lower() == event_type.lower()]
    
    def has_event_type(self, event_type: str) -> bool:
        """Check if family has an event of specific type"""
        return len(self.find_events_by_type(event_type)) > 0
    
    def get_latest_event(self) -> Optional[Event]:
        """Get the most recent event (by date)"""
        if not self.events:
            return None
        
        latest_event = None
        latest_date = None
        
        for event in self.events:
            if event.date and event.date.dmy:
                if latest_date is None or self._compare_dates(event.date, latest_date) > 0:
                    latest_date = event.date
                    latest_event = event
        
        return latest_event

    # Validation methods
    def validate(self) -> List[str]:
        """Validate family data and return list of validation errors"""
        errors = []
        
        if self.parent1 == 0 and self.parent2 == 0:
            errors.append("Family must have at least one parent")
        
        if self.parent1 == self.parent2 and self.parent1 != 0:
            errors.append("Parents cannot be the same person")
        
        if self.key_index is not None and self.key_index < 0:
            errors.append("Key index cannot be negative")
        
        # Validate marriage/divorce chronology
        if self.marriage and self.divorce:
            marriage_date = self.get_marriage_date()
            divorce_date = self.get_divorce_date()
            if marriage_date and divorce_date and self._compare_dates(marriage_date, divorce_date) > 0:
                errors.append("Marriage date cannot be after divorce date")
        
        # Check for duplicate children
        if len(self.children) != len(set(self.children)):
            errors.append("Duplicate children found")
        
        # Validate relation consistency
        if self.relation == RelationKind.DIVORCED and not self.has_divorce_event():
            errors.append("Family marked as divorced but has no divorce event")
        
        if self.relation == RelationKind.MARRIED and not self.has_marriage_event():
            # This might be a warning rather than error, as some marriages might not have recorded events
            pass
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if family data is valid"""
        return len(self.validate()) == 0

    # Conversion methods
    def to_dict(self) -> dict:
        """Convert family to dictionary representation"""
        def event_to_dict(event: Optional[Event]) -> Optional[dict]:
            if not event:
                return None
            return {
                'name': event.name,
                'date': {
                    'dmy': {
                        'day': event.date.dmy.day,
                        'month': event.date.dmy.month,
                        'year': event.date.dmy.year,
                        'prec': event.date.dmy.prec.value if event.date.dmy.prec else None,
                        'delta': event.date.dmy.delta
                    } if event.date and event.date.dmy else None,
                    'calendar': event.date.calendar.value if event.date and event.date.calendar else None,
                    'text': event.date.text if event.date else None
                } if event.date else None,
                'place': {
                    'country': event.place.country,
                    'region': event.place.region,
                    'district': event.place.district,
                    'county': event.place.county,
                    'township': event.place.township,
                    'canton': event.place.canton,
                    'town': event.place.town,
                    'other': event.place.other
                } if event.place else None,
                'reason': event.reason,
                'note': event.note,
                'source': event.source,
                'witnesses': [
                    {
                        'key_index': w.key_index,
                        'type': w.type.value if w.type else None
                    } for w in event.witnesses
                ]
            }
        
        return {
            'parent1': self.parent1,
            'parent2': self.parent2,
            'children': self.children,
            'children_count': self.children_count,
            'relation': self.relation.value if self.relation else None,
            'marriage': event_to_dict(self.marriage),
            'divorce': event_to_dict(self.divorce),
            'events': [event_to_dict(event) for event in self.events],
            'notes': self.notes,
            'origin_file': self.origin_file,
            'sources': self.sources,
            'key_index': self.key_index,
            # Additional computed fields
            'is_married': self.is_married(),
            'is_divorced': self.is_divorced(),
            'is_separated': self.is_separated(),
            'has_children': self.has_children,
            'has_marriage_event': self.has_marriage_event(),
            'has_divorce_event': self.has_divorce_event(),
            'marriage_date': event_to_dict(self.marriage)['date'] if self.marriage else None,
            'divorce_date': event_to_dict(self.divorce)['date'] if self.divorce else None,
            'marriage_place': self.get_marriage_place(),
            'divorce_place': self.get_divorce_place(),
            'witnesses': [
                {
                    'key_index': w.key_index,
                    'type': w.type.value if w.type else None
                } for w in self.get_witnesses()
            ]
        }
    
    def __str__(self) -> str:
        """String representation of family"""
        parent_info = f"Parents: {self.parent1}, {self.parent2}"
        children_info = f"Children: {len(self.children)}"
        relation_info = f"Relation: {self.relation.value}"
        return f"Family({parent_info}, {children_info}, {relation_info})"
    
    def __repr__(self) -> str:
        """Detailed string representation of family"""
        return (f"Family(parent1={self.parent1}, parent2={self.parent2}, "
                f"children={self.children}, relation={self.relation}, "
                f"key_index={self.key_index})")
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on key_index if available, otherwise parents and children"""
        if not isinstance(other, Family):
            return False
        if self.key_index is not None and other.key_index is not None:
            return self.key_index == other.key_index
        return (self.parent1 == other.parent1 and 
                self.parent2 == other.parent2 and 
                set(self.children) == set(other.children))
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries"""
        if self.key_index is not None:
            return hash(self.key_index)
        return hash((self.parent1, self.parent2, tuple(sorted(self.children))))

    # JSON Export Methods (Enhanced beyond original Geneweb)
    def to_json(self, indent: Optional[int] = None, ensure_ascii: bool = False) -> str:
        """Export family to JSON string
        
        Args:
            indent: JSON indentation for pretty printing (None for compact)
            ensure_ascii: If True, non-ASCII characters are escaped
            
        Returns:
            JSON string representation of the family
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii, default=str)
    
    def to_json_file(self, filepath: str, indent: int = 2, ensure_ascii: bool = False) -> None:
        """Export family to JSON file
        
        Args:
            filepath: Path to output JSON file
            indent: JSON indentation for pretty printing
            ensure_ascii: If True, non-ASCII characters are escaped
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=ensure_ascii, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Family':
        """Create Family from JSON string
        
        Args:
            json_str: JSON string representation
            
        Returns:
            Family instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_json_file(cls, filepath: str) -> 'Family':
        """Create Family from JSON file
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Family instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Family':
        """Create Family from dictionary (inverse of to_dict)
        
        Args:
            data: Dictionary representation of family
            
        Returns:
            Family instance
        """
        # Helper to reconstruct Event from dict (same as in Person class)
        def dict_to_event(event_data: Optional[dict]) -> Optional[Event]:
            if not event_data:
                return None
            
            # Reconstruct date
            date_obj = None
            if event_data.get('date'):
                date_data = event_data['date']
                if date_data.get('dmy'):
                    from ..date import DMY, Precision, Calendar
                    dmy_data = date_data['dmy']
                    dmy = DMY(
                        day=dmy_data.get('day', 0),
                        month=dmy_data.get('month', 0),
                        year=dmy_data.get('year', 0),
                        prec=Precision(dmy_data['prec']) if dmy_data.get('prec') else None,
                        delta=dmy_data.get('delta')
                    )
                    date_obj = Date(
                        dmy=dmy,
                        calendar=Calendar(date_data['calendar']) if date_data.get('calendar') else None,
                        text=date_data.get('text')
                    )
            
            # Reconstruct place
            place_obj = None
            if event_data.get('place'):
                from ..event import Place
                place_data = event_data['place']
                place_obj = Place(
                    country=place_data.get('country', ''),
                    region=place_data.get('region', ''),
                    district=place_data.get('district', ''),
                    county=place_data.get('county', ''),
                    township=place_data.get('township', ''),
                    canton=place_data.get('canton', ''),
                    town=place_data.get('town', ''),
                    other=place_data.get('other', '')
                )
            
            # Reconstruct witnesses
            witnesses = []
            if event_data.get('witnesses'):
                from ..event import Witness, WitnessType
                for w_data in event_data['witnesses']:
                    witness = Witness(
                        key_index=w_data.get('key_index', 0),
                        type=WitnessType(w_data['type']) if w_data.get('type') else WitnessType.OTHER
                    )
                    witnesses.append(witness)
            
            return Event(
                name=event_data['name'],
                date=date_obj,
                place=place_obj,
                reason=event_data.get('reason'),
                note=event_data.get('note'),
                source=event_data.get('source'),
                witnesses=witnesses
            )
        
        # Reconstruct the Family
        return cls(
            parent1=data.get('parent1', 0),
            parent2=data.get('parent2', 0),
            children=data.get('children', []),
            relation=RelationKind(data['relation']) if data.get('relation') else RelationKind.UNKNOWN,
            marriage=dict_to_event(data.get('marriage')),
            divorce=dict_to_event(data.get('divorce')),
            events=[dict_to_event(e) for e in data.get('events', []) if e],
            notes=data.get('notes'),
            origin_file=data.get('origin_file'),
            sources=data.get('sources'),
            key_index=data.get('key_index')
        )
