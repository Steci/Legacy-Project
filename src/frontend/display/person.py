"""
Person page display module.

Translates geneweb/lib/perso.ml (person page rendering).
Bridges models.person.Person with the template engine.

This module:
- Takes Person objects from models/
- Prepares context data for templates
- Renders person pages using template engine
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from models.person import Person
from models.person.params import Sex
from frontend.config import RequestConfig
from frontend.template.interpreter import render_template, TemplateInterpreter
from frontend.template.parser import parse


def prepare_person_context(person: Person, config: RequestConfig) -> Dict[str, Any]:
    """
    Prepare context dictionary for person template rendering.

    Extracts data from Person model and formats it for template variables.

    Args:
        person: Person object to render
        config: Request configuration

    Returns:
        Dictionary of template variables
    """
    context = {}

    # Basic identification
    context['first_name'] = person.first_name or ""
    context['surname'] = person.surname or ""
    context['public_name'] = person.public_name or ""
    context['qualifiers'] = person.qualifiers or []
    context['aliases'] = person.aliases or []
    context['first_names_aliases'] = person.first_names_aliases or []
    context['surnames_aliases'] = person.surnames_aliases or []

    # Gender
    context['sex'] = person.sex.value if person.sex else "unknown"
    context['is_male'] = person.sex == Sex.MALE
    context['is_female'] = person.sex == Sex.FEMALE

    # Image
    context['image'] = person.image or ""
    context['has_image'] = bool(person.image)

    # Occupation and titles
    context['occupation'] = person.occupation or ""
    context['has_occupation'] = bool(person.occupation)

    # Format titles
    titles = []
    if person.titles:
        for title in person.titles:
            title_dict = {
                'name': title.title_type,
                'title': title.title,
                'place': title.place or "",
                'date_start': str(title.date_start) if title.date_start else "",
                'date_end': str(title.date_end) if title.date_end else "",
                'nth': title.nth or 0,
            }
            titles.append(title_dict)
    context['titles'] = titles
    context['has_titles'] = len(titles) > 0

    # Life events
    birth_event = person.get_birth()
    death_event = person.get_death()

    def format_date(event):
        """Format event date as string"""
        if not event or not event.date:
            return ""
        date = event.date
        if date.dmy:
            return f"{date.dmy.year}-{date.dmy.month:02d}-{date.dmy.day:02d}"
        return str(date)

    def format_place(event):
        """Format event place as string"""
        if not event or not event.place:
            return ""
        place = event.place
        parts = []
        if place.town:
            parts.append(place.town)
        if place.county:
            parts.append(place.county)
        if place.region:
            parts.append(place.region)
        if place.country:
            parts.append(place.country)
        return ", ".join(parts) if parts else ""

    context['birth_date'] = format_date(birth_event)
    context['birth_place'] = format_place(birth_event)
    context['has_birth'] = birth_event is not None

    context['death_date'] = format_date(death_event)
    context['death_place'] = format_place(death_event)
    context['has_death'] = death_event is not None
    context['is_dead'] = death_event is not None

    # Baptism and burial
    bapt_event = person.get_baptism()
    burial_event = person.get_burial()

    context['baptism_date'] = format_date(bapt_event)
    context['baptism_place'] = format_place(bapt_event)
    context['has_baptism'] = bapt_event is not None

    context['burial_date'] = format_date(burial_event)
    context['burial_place'] = format_place(burial_event)
    context['has_burial'] = burial_event is not None

    # Access control
    # Check if person has restricted access (not public)
    is_restricted = person.access and person.access.lower() not in ['public', 'none', '']
    context['is_restricted'] = is_restricted
    context['is_public'] = not is_restricted

    # Notes
    context['notes'] = person.notes or ""
    context['has_notes'] = bool(person.notes)

    # Sources
    context['sources'] = person.psources or ""
    context['has_sources'] = bool(person.psources)

    # Related persons
    context['related'] = []
    if person.related:
        for rel in person.related:
            context['related'].append({
                'type': rel.relation_type.value,
                'person': rel.person,
                'sources': rel.sources or "",
            })
    context['has_related'] = len(context['related']) > 0

    # Sosa number (if calculated)
    context['sosa'] = ""
    context['has_sosa'] = False

    # Person index
    context['person_index'] = person.index if hasattr(person, 'index') else 0

    return context


def render_person_page(person: Person, config: RequestConfig, template_source: Optional[str] = None) -> str:
    """
    Render a person page as HTML.

    Args:
        person: Person object to render
        config: Request configuration with language, privacy settings, etc.
        template_source: Optional custom template. If None, uses default template.

    Returns:
        HTML string of rendered person page

    Example:
        >>> from models.person import Person
        >>> from models.person.params import Sex
        >>> from frontend.config import create_empty_config
        >>>
        >>> person = Person(
        ...     first_name="John",
        ...     surname="Smith",
        ...     sex=Sex.MALE,
        ... )
        >>> config = create_empty_config()
        >>> html = render_person_page(person, config)
    """
    # Use default template if none provided
    if template_source is None:
        template_source = DEFAULT_PERSON_TEMPLATE

    # Prepare context
    context = prepare_person_context(person, config)

    # Create interpreter with config
    interp = TemplateInterpreter(config)

    # Set person context variables in environment
    for key, value in context.items():
        interp.env.set(key, value)

    # Parse and interpret template
    ast = parse(template_source)
    html = interp.interpret(ast)

    return html


# Default person template
DEFAULT_PERSON_TEMPLATE = """<!DOCTYPE html>
<html lang="%lang;">
<head>
    <meta charset="UTF-8">
    <title>%first_name; %surname;</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 0 20px;
        }
        .person-header {
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .person-name {
            font-size: 2em;
            font-weight: bold;
        }
        .person-section {
            margin: 20px 0;
        }
        .section-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #444;
        }
        .event-info {
            margin: 5px 0;
        }
        .label {
            font-weight: bold;
            display: inline-block;
            min-width: 100px;
        }
        .image-container {
            float: right;
            margin: 0 0 10px 20px;
        }
        .person-image {
            max-width: 200px;
            border: 1px solid #ccc;
            padding: 5px;
        }
        .note-section {
            background: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #ccc;
            margin: 20px 0;
        }
        .title-item {
            margin: 5px 0;
            padding: 5px;
            background: #f5f5f5;
        }
    </style>
</head>
<body>
    <div class="person-header">
        %if;(has_image)
        <div class="image-container">
            <img src="%image;" alt="%first_name; %surname;" class="person-image">
        </div>
        %end;

        <div class="person-name">
            %first_name; %surname;
        </div>

        %if;(public_name)
        <div style="font-size: 1.2em; color: #666;">
            [also known as: %public_name;]
        </div>
        %end;

        %if;(is_male)
        <div style="color: #4444ff;">♂ Male</div>
        %end;

        %if;(is_female)
        <div style="color: #ff4444;">♀ Female</div>
        %end;
    </div>

    <div class="person-section">
        <div class="section-title">Life Events</div>

        %if;(has_birth)
        <div class="event-info">
            <span class="label">Born:</span>
            %birth_date;
            %if;(birth_place)
                in %birth_place;
            %end;
        </div>
        %end;

        %if;(has_baptism)
        <div class="event-info">
            <span class="label">Baptized:</span>
            %baptism_date;
            %if;(baptism_place)
                in %baptism_place;
            %end;
        </div>
        %end;

        %if;(has_death)
        <div class="event-info">
            <span class="label">Died:</span>
            %death_date;
            %if;(death_place)
                in %death_place;
            %end;
        </div>
        %end;

        %if;(has_burial)
        <div class="event-info">
            <span class="label">Buried:</span>
            %burial_date;
            %if;(burial_place)
                in %burial_place;
            %end;
        </div>
        %end;
    </div>

    %if;(has_occupation)
    <div class="person-section">
        <div class="section-title">Occupation</div>
        <div>%occupation;</div>
    </div>
    %end;

    %if;(has_titles)
    <div class="person-section">
        <div class="section-title">Titles</div>
        %foreach;titles;
        <div class="title-item">
            <strong>%title.name;</strong>
            %if;(title.title) - %title.title;%end;
            %if;(title.place) (%title.place;)%end;
            %if;(title.date_start)
                [%title.date_start;
                %if;(title.date_end) - %title.date_end;%end;]
            %end;
        </div>
        %end;
    </div>
    %end;

    %if;(has_notes)
    <div class="person-section">
        <div class="section-title">Notes</div>
        <div class="note-section">
            %notes;
        </div>
    </div>
    %end;

    %if;(has_sources)
    <div class="person-section">
        <div class="section-title">Sources</div>
        <div>%sources;</div>
    </div>
    %end;

    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; color: #888; font-size: 0.9em;">
        Generated by Legacy Project Template Engine
    </div>
</body>
</html>
"""
