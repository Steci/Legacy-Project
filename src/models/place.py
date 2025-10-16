# place.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class Place:
    """Represents a geographical place with hierarchical components"""
    
    town: Optional[str] = None
    county: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    other: Optional[str] = None
    
    def __str__(self) -> str:
        """Return formatted place string"""
        parts = []
        if self.town:
            parts.append(self.town)
        if self.county:
            parts.append(self.county)
        if self.region:
            parts.append(self.region)
        if self.country:
            parts.append(self.country)
        if self.other:
            parts.append(self.other)
        return ", ".join(parts)
    
    @property
    def is_empty(self) -> bool:
        """Check if place has any information"""
        return not any([self.town, self.county, self.region, self.country, self.other])
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'town': self.town,
            'county': self.county,
            'region': self.region,  
            'country': self.country,
            'other': self.other
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Place':
        """Create Place from dictionary"""
        if not data:
            return cls()
        
        return cls(
            town=data.get('town'),
            county=data.get('county'),
            region=data.get('region'),
            country=data.get('country'),
            other=data.get('other')
        )