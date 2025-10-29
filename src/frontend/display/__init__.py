"""
Display modules for rendering genealogy pages.

This package contains modules that bridge between the data models
(Person, Family, Event, etc.) and the template engine.

Each display module:
- Takes model objects from models/
- Prepares data for template rendering
- Calls template engine to generate HTML

Modules:
    - person.py: Person page rendering
    - family.py: Family page rendering (TODO)
    - descendant.py: Descendant tree rendering (TODO)
    - ancestor.py: Ancestor tree rendering (TODO)

Usage:
    from frontend.display.person import render_person_page
    from frontend.config import RequestConfig
    from models.person import Person

    config = RequestConfig(...)
    person = Person(...)
    html = render_person_page(person, config)
"""

from .person import render_person_page, prepare_person_context

__all__ = [
    'render_person_page',
    'prepare_person_context',
]
