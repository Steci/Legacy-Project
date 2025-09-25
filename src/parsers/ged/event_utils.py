"""
Event parsing utilities for GEDCOM parser.
Extracted to reduce cyclomatic complexity while preserving OCaml compatibility.
"""
from typing import List, Dict, Optional, Any
from ..common.base_models import BaseEvent
from .models import GedcomRecord


class EventParsingUtils:
    """Utility class for parsing GEDCOM events and extracting common patterns."""
    
    # Standard personal event types from OCaml treat_indi_pevent
    PERSONAL_EVENT_TYPES = [
        "BAPM", "CHR", "CHRA", "BARM", "BASM", "BLES", "CONF", 
        "FCOM", "ORDN", "NATU", "EMIG", "IMMI", "CENS", "PROB", 
        "WILL", "GRAD", "RETI", "EVEN"
    ]
    
    # Witness relationship types
    WITNESS_RELATIONSHIPS = {
        "godfather": "godparent",
        "godmother": "godparent", 
        "godparent": "godparent",
        "witness": "witness",
        "témoin": "witness",
        "parrain": "godparent",
        "marraine": "godparent"
    }
    
    @staticmethod
    def parse_basic_event_data(event_record: GedcomRecord, date_parser) -> Dict[str, Any]:
        """Extract basic event data (date, place, notes, sources)."""
        event_data = {}
        
        # Parse date
        date_record = EventParsingUtils._find_sub_record(event_record, "DATE")
        if date_record:
            event_data['date'] = date_parser(date_record.value)
            
        # Parse place
        place_record = EventParsingUtils._find_sub_record(event_record, "PLAC")
        if place_record:
            event_data['place'] = place_record.value
            
        # Parse type for EVEN events
        type_record = EventParsingUtils._find_sub_record(event_record, "TYPE")
        if type_record:
            event_data['event_type'] = type_record.value
            
        return event_data
    
    @staticmethod
    def extract_witnesses(event_record: GedcomRecord) -> List[Dict[str, str]]:
        """Extract witness information from event record."""
        witnesses = []
        
        if not event_record:
            return witnesses
            
        # Find witness records (ASSO or _ASSO)
        witness_records = EventParsingUtils._find_all_sub_records(event_record, "ASSO")
        witness_records.extend(EventParsingUtils._find_all_sub_records(event_record, "_ASSO"))
        
        for witness_record in witness_records:
            witness_xref = witness_record.value
            if not witness_xref:
                continue
                
            witness_info = {'witness': witness_xref, 'type': 'witness'}
            
            # Determine witness relationship type
            rela_record = EventParsingUtils._find_sub_record(witness_record, "RELA")
            if rela_record:
                rela_value = rela_record.value.lower()
                witness_info['type'] = EventParsingUtils.WITNESS_RELATIONSHIPS.get(rela_value, 'witness')
                
            witnesses.append(witness_info)
            
        return witnesses
    
    @staticmethod
    def categorize_witnesses(witnesses: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """Categorize witnesses into godparents and regular witnesses."""
        categorized = {
            'godparents': [],
            'witnesses': []
        }
        
        for witness in witnesses:
            if witness.get('type') == 'godparent':
                categorized['godparents'].append(witness['witness'])
            else:
                categorized['witnesses'].append(witness)
                
        return categorized
    
    @staticmethod
    def create_event_from_data(event_type: str, event_data: Dict[str, Any], notes_extractor, source_extractor, event_record: GedcomRecord) -> BaseEvent:
        """Create BaseEvent from parsed data."""
        event = BaseEvent(event_type=event_type)
        
        # Set basic data
        event.date = event_data.get('date')
        event.place = event_data.get('place')
        if 'event_type' in event_data:
            event.event_type = event_data['event_type']
            
        # Extract notes and sources
        event.note = notes_extractor(event_record)
        event.source = source_extractor(event_record)
        
        return event
    
    @staticmethod
    def parse_adoption_info(record: GedcomRecord) -> Dict[str, Any]:
        """Parse adoption-related information from record."""
        adoption_info = {}
        
        # Handle ADOP events
        adop_records = EventParsingUtils._find_all_sub_records(record, "ADOP")
        for adop_record in adop_records:
            # Parse adoption family
            famc_record = EventParsingUtils._find_sub_record(adop_record, "FAMC")
            if famc_record:
                family_xref = famc_record.value
                
                # Check adoption type (ADOP_BY_HUSB, ADOP_BY_WIFE, ADOP_BY_BOTH)
                adop_type = "both"  # Default
                for sub_rec in adop_record.sub_records:
                    if sub_rec.tag == "ADOP":
                        if sub_rec.value == "HUSB":
                            adop_type = "husband"
                        elif sub_rec.value == "WIFE":
                            adop_type = "wife"
                            
                adoption_info[family_xref] = adop_type
        
        # Handle FAMC with PEDI information
        famc_records = EventParsingUtils._find_all_sub_records(record, "FAMC")
        for famc_record in famc_records:
            family_xref = famc_record.value
            
            # Check for PEDI (pedigree) information
            pedi_record = EventParsingUtils._find_sub_record(famc_record, "PEDI")
            if pedi_record and pedi_record.value in ["adopted", "foster"]:
                if family_xref not in adoption_info:
                    adoption_info[family_xref] = "both"  # Default both parents
                    
        return adoption_info
    
    @staticmethod
    def _find_sub_record(record: GedcomRecord, tag: str) -> Optional[GedcomRecord]:
        """Find first sub-record with given tag."""
        for sub_record in record.sub_records:
            if sub_record.tag == tag:
                sub_record.used = True
                return sub_record
        return None
    
    @staticmethod
    def _find_all_sub_records(record: GedcomRecord, tag: str) -> List[GedcomRecord]:
        """Find all sub-records with given tag."""
        found = []
        for sub_record in record.sub_records:
            if sub_record.tag == tag:
                sub_record.used = True
                found.append(sub_record)
        return found


class SpecialRelationshipProcessor:
    """Handles processing of special relationships (adoption, godparent, witnesses)."""
    
    def __init__(self):
        self.adoption_map = {}  # family_xref -> {person_xref -> adoption_type}
        self.godparent_relationships = {}  # person_xref -> [godparent_xrefs]
        self.witness_relationships = {}  # person_xref -> [witness_info]
    
    def process_adoption_event(self, adop_record: GedcomRecord, person_xref: str):
        """Process ADOP event following OCaml logic."""
        # Parse adoption family
        famc_record = EventParsingUtils._find_sub_record(adop_record, "FAMC")
        if famc_record:
            family_xref = famc_record.value
            
            # Check adoption type
            adop_type = "both"  # Default
            for sub_rec in adop_record.sub_records:
                if sub_rec.tag == "ADOP":
                    if sub_rec.value == "HUSB":
                        adop_type = "husband"
                    elif sub_rec.value == "WIFE":
                        adop_type = "wife"
                        
            # Store adoption information
            if family_xref not in self.adoption_map:
                self.adoption_map[family_xref] = {}
            self.adoption_map[family_xref][person_xref] = adop_type
    
    def process_famc_adoption(self, famc_record: GedcomRecord, person_xref: str):
        """Process FAMC with PEDI or adoption info."""
        family_xref = famc_record.value
        
        # Check for PEDI (pedigree) information
        pedi_record = EventParsingUtils._find_sub_record(famc_record, "PEDI")
        if pedi_record and pedi_record.value in ["adopted", "foster"]:
            if family_xref not in self.adoption_map:
                self.adoption_map[family_xref] = {}
            self.adoption_map[family_xref][person_xref] = "both"  # Default both parents
    
    def process_event_witnesses(self, event_record: GedcomRecord, event_type: str, person_xref: str):
        """Process witnesses for an event following OCaml witness logic."""
        witnesses = EventParsingUtils.extract_witnesses(event_record)
        categorized = EventParsingUtils.categorize_witnesses(witnesses)
        
        # Store godparent relationships
        if categorized['godparents']:
            if person_xref not in self.godparent_relationships:
                self.godparent_relationships[person_xref] = []
            self.godparent_relationships[person_xref].extend(categorized['godparents'])
        
        # Store witness relationships
        if categorized['witnesses']:
            if person_xref not in self.witness_relationships:
                self.witness_relationships[person_xref] = []
            for witness_info in categorized['witnesses']:
                witness_info['event'] = event_type
                self.witness_relationships[person_xref].append(witness_info)
    
    def finalize_relationships(self, database):
        """Apply stored relationships to database."""
        # Process adoption relationships
        for family_xref, adoptions in self.adoption_map.items():
            for person_xref, adoption_type in adoptions.items():
                if person_xref in database.individuals and adoption_type != "biological":
                    person = database.individuals[person_xref]
                    person.adoption_families.append(family_xref)
                    
        # Process godparent relationships
        for person_xref, godparent_list in self.godparent_relationships.items():
            if person_xref in database.individuals:
                person = database.individuals[person_xref]
                person.godparents.extend(godparent_list)
                
        # Process witness relationships
        for person_xref, witness_list in self.witness_relationships.items():
            if person_xref in database.individuals:
                person = database.individuals[person_xref]
                person.witnesses.extend(witness_list)
