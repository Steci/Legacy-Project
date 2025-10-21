# person/person.py

from typing import List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..event import Event
from ..date import Date
from .params import Sex, Title, Relation, PEventType

@dataclass
class Person:
    first_name: str
    surname: str
    public_name: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    first_names_aliases: List[str] = field(default_factory=list)
    surnames_aliases: List[str] = field(default_factory=list)

    sex: Sex = Sex.NEUTER
    titles: List[Title] = field(default_factory=list)
    qualifiers: List[str] = field(default_factory=list)
    occupation: Optional[str] = None

    occ: int = 0
    image: Optional[str] = None

    parents: List[Relation] = field(default_factory=list) # Parents' unique identifiers
    related: List[int] = field(default_factory=list)
    families: List[int] = field(default_factory=list) # List of unique identifiers of families

    birth: Optional[Event] = None
    baptism: Optional[Event] = None
    death: Optional[Event] = None
    burial: Optional[Event] = None
    events: List[Event] = field(default_factory=list)

    notes: Optional[str] = None
    psources: Optional[str] = None
    access: Optional[str] = None  # e.g., "public", "private"
    key_index: Optional[int] = None  # Unique identifier for the person
    consanguinity: float = 0.0

    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Validate basic constraints
        if not self.first_name.strip():
            raise ValueError("First name cannot be empty")
        if not self.surname.strip():
            raise ValueError("Surname cannot be empty")
        if self.occ < 0:
            raise ValueError("Occurrence number cannot be negative")
        if self.key_index is not None and self.key_index < 0:
            raise ValueError("Key index cannot be negative")

    # Properties for most common getters (Pythonic way)
    @property
    def full_name(self) -> str:
        """Get full name (first name + surname)"""
        return f"{self.first_name} {self.surname}".strip()
    
    @property
    def display_name(self) -> str:
        """Get display name (public name if available, otherwise full name)"""
        return self.public_name if self.public_name else self.full_name
    
    @property
    def is_alive(self) -> bool:
        """Check if person is alive (no death event)"""
        return self.death is None
    
    @property
    def is_deceased(self) -> bool:
        """Check if person is deceased (has death event)"""
        return self.death is not None

    # Getter methods
    def get_first_name(self) -> str:
        return self.first_name
    
    def get_surname(self) -> str:
        return self.surname
    
    def get_public_name(self) -> Optional[str]:
        return self.public_name
    
    def get_aliases(self) -> List[str]:
        return self.aliases
    
    def get_first_names_aliases(self) -> List[str]:
        return self.first_names_aliases
    
    def get_surnames_aliases(self) -> List[str]:
        return self.surnames_aliases
    
    def get_sex(self) -> Sex:
        return self.sex
    
    def get_titles(self) -> List[Title]:
        return self.titles
    
    def get_qualifiers(self) -> List[str]:
        return self.qualifiers
    
    def get_occupation(self) -> Optional[str]:
        return self.occupation
    
    def get_occ(self) -> int:
        """Get occurrence number (for disambiguating people with same name)"""
        return self.occ
    
    def get_image(self) -> Optional[str]:
        return self.image
    
    def get_parents(self) -> List[Relation]:
        """Get relations with parents (including non-native parents)"""
        return self.parents
    
    def get_related(self) -> List[int]:
        """Get list of related person IDs"""
        return self.related
    
    def get_families(self) -> List[int]:
        """Get list of family IDs where this person is a parent"""
        return self.families
    
    def get_birth(self) -> Optional[Event]:
        return self.birth
    
    def get_baptism(self) -> Optional[Event]:
        return self.baptism
    
    def get_death(self) -> Optional[Event]:
        return self.death
    
    def get_burial(self) -> Optional[Event]:
        return self.burial
    
    def get_events(self) -> List[Event]:
        """Get all personal events"""
        return self.events
    
    def get_notes(self) -> Optional[str]:
        return self.notes
    
    def get_psources(self) -> Optional[str]:
        """Get personal sources"""
        return self.psources
    
    def get_access(self) -> Optional[str]:
        """Get access level (public, private, etc.)"""
        return self.access
    
    def get_key_index(self) -> int:
        """Get unique identifier for this person"""
        return self.key_index


    def add_family(self, index: int):
        if index not in self.families:
            self.families.append(index)

    def add_event(self, event: Event):
        self.events.append(event)

    def add_relation(self, relation: Relation):
        self.parents.append(relation)

    # Setter methods for updating person data
    def set_first_name(self, first_name: str):
        """Update first name"""
        self.first_name = first_name
    
    def set_surname(self, surname: str):
        """Update surname"""
        self.surname = surname
    
    def set_public_name(self, public_name: Optional[str]):
        """Update public name"""
        self.public_name = public_name
    
    def set_sex(self, sex: Sex):
        """Update sex"""
        self.sex = sex
    
    def set_occupation(self, occupation: Optional[str]):
        """Update occupation"""
        self.occupation = occupation
    
    def set_occ(self, occ: int):
        """Update occurrence number"""
        self.occ = occ
    
    def set_image(self, image: Optional[str]):
        """Update image path"""
        self.image = image
    
    def set_birth(self, birth: Optional[Event]):
        """Update birth event"""
        self.birth = birth
    
    def set_baptism(self, baptism: Optional[Event]):
        """Update baptism event"""
        self.baptism = baptism
    
    def set_death(self, death: Optional[Event]):
        """Update death event"""
        self.death = death
    
    def set_burial(self, burial: Optional[Event]):
        """Update burial event"""
        self.burial = burial
    
    def set_notes(self, notes: Optional[str]):
        """Update notes"""
        self.notes = notes
    
    def set_psources(self, psources: Optional[str]):
        """Update personal sources"""
        self.psources = psources
    
    def set_access(self, access: Optional[str]):
        """Update access level"""
        self.access = access

    # List manipulation methods
    def add_alias(self, alias: str):
        """Add an alias"""
        if alias not in self.aliases:
            self.aliases.append(alias)
    
    def remove_alias(self, alias: str):
        """Remove an alias"""
        if alias in self.aliases:
            self.aliases.remove(alias)
    
    def add_first_name_alias(self, alias: str):
        """Add a first name alias"""
        if alias not in self.first_names_aliases:
            self.first_names_aliases.append(alias)
    
    def remove_first_name_alias(self, alias: str):
        """Remove a first name alias"""
        if alias in self.first_names_aliases:
            self.first_names_aliases.remove(alias)
    
    def add_surname_alias(self, alias: str):
        """Add a surname alias"""
        if alias not in self.surnames_aliases:
            self.surnames_aliases.append(alias)
    
    def remove_surname_alias(self, alias: str):
        """Remove a surname alias"""
        if alias in self.surnames_aliases:
            self.surnames_aliases.remove(alias)
    
    def add_title(self, title: Title):
        """Add a title"""
        if title not in self.titles:
            self.titles.append(title)
    
    def remove_title(self, title: Title):
        """Remove a title"""
        if title in self.titles:
            self.titles.remove(title)
    
    def add_qualifier(self, qualifier: str):
        """Add a qualifier"""
        if qualifier not in self.qualifiers:
            self.qualifiers.append(qualifier)
    
    def remove_qualifier(self, qualifier: str):
        """Remove a qualifier"""
        if qualifier in self.qualifiers:
            self.qualifiers.remove(qualifier)
    
    def remove_family(self, index: int):
        """Remove a family ID"""
        if index in self.families:
            self.families.remove(index)
    
    def add_related(self, person_id: int):
        """Add a related person ID"""
        if person_id not in self.related:
            self.related.append(person_id)
    
    def remove_related(self, person_id: int):
        """Remove a related person ID"""
        if person_id in self.related:
            self.related.remove(person_id)
    
    def remove_event(self, event: Event):
        """Remove an event"""
        if event in self.events:
            self.events.remove(event)
    
    def remove_relation(self, relation: Relation):
        """Remove a parent relation"""
        if relation in self.parents:
            self.parents.remove(relation)

    # Utility and validation methods
    def is_empty_name(self) -> bool:
        """Check if person has empty name (like '? ?')"""
        return not self.first_name.strip() or not self.surname.strip() or \
               self.first_name.strip() == '?' or self.surname.strip() == '?'
    
    def is_hidden(self) -> bool:
        """Check if person is hidden (surname is empty)"""
        return not self.surname.strip()
    
    def has_children(self) -> bool:
        """Check if person has any families (and potentially children)"""
        return len(self.families) > 0
    
    def has_titles(self) -> bool:
        """Check if person has any titles"""
        return len(self.titles) > 0
    
    def has_events(self) -> bool:
        """Check if person has any personal events"""
        return len(self.events) > 0
    
    # Note: is_alive and is_deceased methods removed - use properties instead
    
    def get_full_name(self) -> str:
        """Get full name (first name + surname) - DEPRECATED: use .full_name property"""
        return self.full_name
    
    def get_display_name(self) -> str:
        """Get display name (public name if available, otherwise full name) - DEPRECATED: use .display_name property"""
        return self.display_name
    
    def get_name_with_occ(self) -> str:
        """Get name with occurrence number if > 0"""
        full_name = self.get_full_name()
        if self.occ > 0:
            return f"{full_name} ({self.occ})"
        return full_name

    # Search and comparison methods
    def matches_name(self, first_name: str, surname: str, occ: int = 0) -> bool:
        """Check if person matches given name criteria"""
        return (self.first_name.lower() == first_name.lower() and 
                self.surname.lower() == surname.lower() and 
                self.occ == occ)
    
    def has_name_variant(self, name: str) -> bool:
        """Check if name appears in any name field or alias"""
        name_lower = name.lower()
        return (name_lower in self.first_name.lower() or 
                name_lower in self.surname.lower() or
                (self.public_name and name_lower in self.public_name.lower()) or
                any(name_lower in alias.lower() for alias in self.aliases) or
                any(name_lower in alias.lower() for alias in self.first_names_aliases) or
                any(name_lower in alias.lower() for alias in self.surnames_aliases))

    # Event creation helper methods
    def create_birth_event(self, date: Optional[Date] = None, place: Optional[str] = None, 
                          note: Optional[str] = None, source: Optional[str] = None) -> Event:
        """Create a birth event"""
        from ..event import Place
        place_obj = Place(other=place) if place else None
        event = Event(name=PEventType.BIRTH.value, date=date, place=place_obj, 
                     note=note, source=source)
        self.birth = event
        return event
    
    def create_baptism_event(self, date: Optional[Date] = None, place: Optional[str] = None,
                           note: Optional[str] = None, source: Optional[str] = None) -> Event:
        """Create a baptism event"""
        from ..event import Place
        place_obj = Place(other=place) if place else None
        event = Event(name=PEventType.BAPTISM.value, date=date, place=place_obj,
                     note=note, source=source)
        self.baptism = event
        return event
    
    def create_death_event(self, date: Optional[Date] = None, place: Optional[str] = None,
                          note: Optional[str] = None, source: Optional[str] = None) -> Event:
        """Create a death event"""
        from ..event import Place
        place_obj = Place(other=place) if place else None
        event = Event(name=PEventType.DEATH.value, date=date, place=place_obj,
                     note=note, source=source)
        self.death = event
        return event
    
    def create_burial_event(self, date: Optional[Date] = None, place: Optional[str] = None,
                           note: Optional[str] = None, source: Optional[str] = None) -> Event:
        """Create a burial event"""
        from ..event import Place
        place_obj = Place(other=place) if place else None
        event = Event(name=PEventType.BURIAL.value, date=date, place=place_obj,
                     note=note, source=source)
        self.burial = event
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
    
    def get_birth_date(self) -> Optional[Date]:
        """Get birth date from birth event"""
        return self._extract_date_from_event(self.birth)
    
    def get_baptism_date(self) -> Optional[Date]:
        """Get baptism date from baptism event"""
        return self._extract_date_from_event(self.baptism)
    
    def get_death_date(self) -> Optional[Date]:
        """Get death date from death event"""
        return self._extract_date_from_event(self.death)
    
    def get_burial_date(self) -> Optional[Date]:
        """Get burial date from burial event"""
        return self._extract_date_from_event(self.burial)
    
    def get_birth_place(self) -> Optional[str]:
        """Get birth place from birth event"""
        if self.birth and self.birth.place:
            return self.birth.place.other or f"{self.birth.place.town}, {self.birth.place.country}".strip(', ')
        return None
    
    def get_death_place(self) -> Optional[str]:
        """Get death place from death event"""
        if self.death and self.death.place:
            return self.death.place.other or f"{self.death.place.town}, {self.death.place.country}".strip(', ')
        return None
    
    def get_age_at_death(self) -> Optional[int]:
        """Calculate age at death if both birth and death dates are available"""
        birth_date = self.get_birth_date()
        death_date = self.get_death_date()
        
        if not birth_date or not death_date or not birth_date.dmy or not death_date.dmy:
            return None
        
        if birth_date.dmy.year == 0 or death_date.dmy.year == 0:
            return None
        
        age = death_date.dmy.year - birth_date.dmy.year
        
        # Adjust for month/day if available
        if (birth_date.dmy.month > 0 and death_date.dmy.month > 0 and
            birth_date.dmy.day > 0 and death_date.dmy.day > 0):
            if (death_date.dmy.month < birth_date.dmy.month or 
                (death_date.dmy.month == birth_date.dmy.month and death_date.dmy.day < birth_date.dmy.day)):
                age -= 1
        
        return age if age >= 0 else None

    # Event search methods
    def find_events_by_type(self, event_type: PEventType) -> List[Event]:
        """Find all events of a specific type"""
        return [event for event in self.events if event.name == event_type.value]
    
    def has_event_type(self, event_type: PEventType) -> bool:
        """Check if person has an event of specific type"""
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

    # Data validation methods
    def validate(self) -> List[str]:
        """Validate person data and return list of validation errors"""
        errors = []
        
        if not self.first_name.strip():
            errors.append("First name cannot be empty")
        
        if not self.surname.strip():
            errors.append("Surname cannot be empty")
        
        if self.occ < 0:
            errors.append("Occurrence number cannot be negative")
        
        if self.key_index is not None and self.key_index < 0:
            errors.append("Key index cannot be negative")
        
        # Validate birth/death chronology
        if self.birth and self.death:
            birth_date = self._extract_date_from_event(self.birth)
            death_date = self._extract_date_from_event(self.death)
            if birth_date and death_date and self._compare_dates(birth_date, death_date) > 0:
                errors.append("Birth date cannot be after death date")
        
        # Validate baptism after birth
        if self.birth and self.baptism:
            birth_date = self._extract_date_from_event(self.birth)
            baptism_date = self._extract_date_from_event(self.baptism)
            if birth_date and baptism_date and self._compare_dates(birth_date, baptism_date) > 0:
                errors.append("Baptism date cannot be before birth date")
        
        # Validate burial after death
        if self.death and self.burial:
            death_date = self._extract_date_from_event(self.death)
            burial_date = self._extract_date_from_event(self.burial)
            if death_date and burial_date and self._compare_dates(death_date, burial_date) > 0:
                errors.append("Burial date cannot be before death date")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if person data is valid"""
        return len(self.validate()) == 0

    # Conversion methods
    def to_dict(self) -> dict:
        """Convert person to dictionary representation"""
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
        
        def relation_to_dict(relation: Relation) -> dict:
            return {
                'type': relation.r_type.value if relation.r_type else None,
                'father': relation.r_fath,
                'mother': relation.r_moth,
                'sources': relation.r_sources
            }
        
        def title_to_dict(title: Title) -> dict:
            return {
                'name': title.name
                # Add other title fields as they become available
            }
        
        return {
            'first_name': self.first_name,
            'surname': self.surname,
            'public_name': self.public_name,
            'aliases': self.aliases,
            'first_names_aliases': self.first_names_aliases,
            'surnames_aliases': self.surnames_aliases,
            'sex': self.sex.value if hasattr(self.sex, 'value') else str(self.sex),
            'titles': [title_to_dict(title) for title in self.titles],
            'qualifiers': self.qualifiers,
            'occupation': self.occupation,
            'occ': self.occ,
            'image': self.image,
            'parents': [relation_to_dict(rel) for rel in self.parents],
            'related': self.related,
            'families': self.families,
            'birth': event_to_dict(self.birth),
            'baptism': event_to_dict(self.baptism),
            'death': event_to_dict(self.death),
            'burial': event_to_dict(self.burial),
            'events': [event_to_dict(event) for event in self.events],
            'notes': self.notes,
            'psources': self.psources,
            'access': self.access,
            'key_index': self.key_index,
            # Additional computed fields
            'full_name': self.full_name,
            'display_name': self.display_name,
            'is_alive': self.is_alive,
            'age_at_death': self.get_age_at_death(),
            'birth_date': event_to_dict(self.birth)['date'] if self.birth else None,
            'death_date': event_to_dict(self.death)['date'] if self.death else None
        }
    
    def __str__(self) -> str:
        """String representation of person"""
        return self.display_name
    
    def __repr__(self) -> str:
        """Detailed string representation of person"""
        return f"Person(first_name='{self.first_name}', surname='{self.surname}', occ={self.occ}, key_index={self.key_index})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on key_index if available, otherwise name and occ"""
        if not isinstance(other, Person):
            return False
        if self.key_index is not None and other.key_index is not None:
            return self.key_index == other.key_index
        return (self.first_name == other.first_name and 
                self.surname == other.surname and 
                self.occ == other.occ)
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries"""
        if self.key_index is not None:
            return hash(self.key_index)
        return hash((self.first_name, self.surname, self.occ))

    # JSON Export Methods (Enhanced beyond original Geneweb)
    def to_json(self, indent: Optional[int] = None, ensure_ascii: bool = False) -> str:
        """Export person to JSON string
        
        Args:
            indent: JSON indentation for pretty printing (None for compact)
            ensure_ascii: If True, non-ASCII characters are escaped
            
        Returns:
            JSON string representation of the person
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii, default=str)
    
    def to_json_file(self, filepath: str, indent: int = 2, ensure_ascii: bool = False) -> None:
        """Export person to JSON file
        
        Args:
            filepath: Path to output JSON file
            indent: JSON indentation for pretty printing
            ensure_ascii: If True, non-ASCII characters are escaped
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=ensure_ascii, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Person':
        """Create Person from JSON string
        
        Args:
            json_str: JSON string representation
            
        Returns:
            Person instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_json_file(cls, filepath: str) -> 'Person':
        """Create Person from JSON file
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Person instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Person':
        """Create Person from dictionary (inverse of to_dict)
        
        Args:
            data: Dictionary representation of person
            
        Returns:
            Person instance
        """
        # Helper to reconstruct Event from dict
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
        
        # Helper to reconstruct Relation from dict
        def dict_to_relation(rel_data: dict) -> Relation:
            from params import RelationType
            return Relation(
                r_type=RelationType(rel_data['type']) if rel_data.get('type') else RelationType.ADOPTION,
                r_fath=rel_data.get('father'),
                r_moth=rel_data.get('mother'),
                r_sources=rel_data.get('sources', '')
            )
        
        # Helper to reconstruct Title from dict
        def dict_to_title(title_data: dict) -> Title:
            return Title(name=title_data['name'])
        
        # Reconstruct the Person
        return cls(
            first_name=data['first_name'],
            surname=data['surname'],
            public_name=data.get('public_name'),
            aliases=data.get('aliases', []),
            first_names_aliases=data.get('first_names_aliases', []),
            surnames_aliases=data.get('surnames_aliases', []),
            sex=Sex(data['sex']) if data.get('sex') else Sex.NEUTER,
            titles=[dict_to_title(t) for t in data.get('titles', [])],
            qualifiers=data.get('qualifiers', []),
            occupation=data.get('occupation'),
            occ=data.get('occ', 0),
            image=data.get('image'),
            parents=[dict_to_relation(r) for r in data.get('parents', [])],
            related=data.get('related', []),
            families=data.get('families', []),
            birth=dict_to_event(data.get('birth')),
            baptism=dict_to_event(data.get('baptism')),
            death=dict_to_event(data.get('death')),
            burial=dict_to_event(data.get('burial')),
            events=[dict_to_event(e) for e in data.get('events', []) if e],
            notes=data.get('notes'),
            psources=data.get('psources'),
            access=data.get('access'),
            key_index=data.get('key_index')
        )
