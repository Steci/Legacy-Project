"""
Name parsing utilities for GEDCOM parser.
Extracted to reduce cyclomatic complexity while preserving OCaml compatibility.
"""
import re
from typing import Optional
from ..common.base_models import BaseName


class NameParsingUtils:
    """Utility class for parsing GEDCOM names and handling name formatting."""
    
    # Name pattern for GEDCOM format: "Given names /Surname/"
    NAME_PATTERN = re.compile(r'^([^/]*?)/?([^/]*?)/?([^/]*)$')
    
    @staticmethod
    def parse_gedcom_name(name_value: str) -> BaseName:
        """
        Parse GEDCOM name format 'First /Surname/' using base model.
        
        Preserves OCaml compatibility for name parsing logic.
        """
        if not name_value:
            return BaseName()
            
        name_value = name_value.strip()
        name = BaseName()
        
        # Handle name format: "Given names /Surname/"
        match = NameParsingUtils.NAME_PATTERN.match(name_value)
        
        if match:
            given = match.group(1).strip() if match.group(1) else ""
            surname = match.group(2).strip() if match.group(2) else ""
            suffix = match.group(3).strip() if match.group(3) else ""
            
            # If no slash pattern, treat as all given names
            if '/' not in name_value:
                given = name_value.strip()
                surname = ""
        else:
            given = name_value.strip()
            surname = ""
        
        # Apply OCaml-compatible name processing
        name.first_name = NameParsingUtils._process_first_name(given)
        name.surname = NameParsingUtils._process_surname(surname)
        
        # Handle suffix if present
        if suffix:
            name.suffix = suffix
            
        return name
    
    @staticmethod
    def _process_first_name(given: str) -> str:
        """Process first name following OCaml logic."""
        if not given:
            return "x"  # OCaml default for empty first names
            
        # Clean and standardize
        given = given.strip()
        if not given:
            return "x"
            
        return given
    
    @staticmethod
    def _process_surname(surname: str) -> str:
        """Process surname following OCaml logic."""
        if not surname:
            return ""
            
        surname = surname.strip()
        return surname
    
    @staticmethod
    def capitalize_name(name: str) -> str:
        """Capitalize name (simplified version matching OCaml)."""
        if not name:
            return name
            
        return " ".join(word.capitalize() for word in name.split())
    
    @staticmethod
    def extract_name_components(full_name: str) -> dict:
        """Extract name components for complex name processing."""
        components = {
            'given': '',
            'surname': '',
            'suffix': '',
            'title': '',
            'nickname': ''
        }
        
        if not full_name:
            return components
            
        # Handle titles (Mr., Mrs., Dr., etc.)
        title_patterns = [r'^(Mr\.?|Mrs\.?|Dr\.?|Prof\.?)\s+', r'^(Sir|Lady|Lord|Dame)\s+']
        for pattern in title_patterns:
            match = re.match(pattern, full_name, re.IGNORECASE)
            if match:
                components['title'] = match.group(1)
                full_name = full_name[match.end():].strip()
                break
        
        # Handle nicknames in quotes or parentheses
        nickname_match = re.search(r'["\']([^"\']+)["\']|\\(([^)]+)\\)', full_name)
        if nickname_match:
            components['nickname'] = nickname_match.group(1) or nickname_match.group(2)
            full_name = re.sub(r'["\']([^"\']+)["\']|\\(([^)]+)\\)', '', full_name).strip()
        
        # Parse the main name using GEDCOM format
        base_name = NameParsingUtils.parse_gedcom_name(full_name)
        components['given'] = base_name.first_name
        components['surname'] = base_name.surname
        components['suffix'] = base_name.suffix
        
        return components
    
    @staticmethod
    def format_name_for_display(name: BaseName, format_style: str = "default") -> str:
        """Format name for display in various styles."""
        if not name:
            return ""
            
        if format_style == "surname_first":
            if name.surname and name.first_name != "x":
                return f"{name.surname}, {name.first_name}"
            elif name.surname:
                return name.surname
            elif name.first_name != "x":
                return name.first_name
            else:
                return ""
        
        elif format_style == "formal":
            parts = []
            if name.first_name and name.first_name != "x":
                parts.append(name.first_name)
            if name.surname:
                parts.append(name.surname)
            if name.suffix:
                parts.append(name.suffix)
            return " ".join(parts)
        
        else:  # default format
            if name.first_name == "x" and name.surname:
                return name.surname
            elif name.first_name != "x" and name.surname:
                return f"{name.first_name} {name.surname}"
            elif name.first_name != "x":
                return name.first_name
            elif name.surname:
                return name.surname
            else:
                return ""
    
    @staticmethod
    def validate_name(name: BaseName) -> bool:
        """Validate that name has at least some content."""
        if not name:
            return False
            
        return bool(
            (name.first_name and name.first_name != "x") or 
            name.surname or 
            name.suffix
        )
    
    @staticmethod
    def normalize_name_for_search(name: BaseName) -> str:
        """Normalize name for searching/comparison."""
        if not name:
            return ""
            
        parts = []
        if name.first_name and name.first_name != "x":
            parts.append(name.first_name.lower().strip())
        if name.surname:
            parts.append(name.surname.lower().strip())
            
        return " ".join(parts)
