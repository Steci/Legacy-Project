"""
GeneWeb Legacy Project - Flask Web Application

This application serves the GeneWeb frontend integrated with the Python backend.
It provides web routes for viewing genealogical data, including:
- Person pages
- Family trees
- Search functionality
- Various genealogy displays

The application uses:
- Flask for web serving
- Jinja2 for template rendering (adapted from GeneWeb templates)
- Static files (CSS, JS, images) from original GeneWeb
"""

from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.person import Person
from models.person.params import Sex
from models.family import Family
from models.event import Event, Place
from models.date import Date, DMY, Calendar

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Configure Flask
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['DEBUG'] = True

# Sample data for demonstration
sample_persons = {}
sample_families = {}


def init_sample_data():
    """Initialize sample genealogy data for demonstration."""
    global sample_persons, sample_families

    # Create a sample person: Charles Darwin
    darwin = Person(
        first_name="Charles",
        surname="Darwin",
        sex=Sex.MALE,
        occupation="Naturalist, Geologist, Biologist",
        public_name="Charles Robert Darwin",
        access="public"
    )
    darwin.birth = Event(
        name="Birth",
        date=Date(
            dmy=DMY(day=12, month=2, year=1809),
            calendar=Calendar.GREGORIAN
        ),
        place=Place(
            town="Shrewsbury",
            county="Shropshire",
            country="England"
        )
    )
    darwin.death = Event(
        name="Death",
        date=Date(
            dmy=DMY(day=19, month=4, year=1882),
            calendar=Calendar.GREGORIAN
        ),
        place=Place(
            town="Downe",
            county="Kent",
            country="England"
        )
    )
    darwin.notes = """
Charles Robert Darwin was an English naturalist, geologist and biologist,
best known for his contributions to evolutionary biology. His proposition
that all species of life have descended from a common ancestor is now
widely accepted and considered a fundamental concept in science.
"""

    sample_persons["darwin"] = darwin

    # Create another sample: Ada Lovelace
    lovelace = Person(
        first_name="Ada",
        surname="Lovelace",
        sex=Sex.FEMALE,
        occupation="Mathematician, Writer",
        public_name="Augusta Ada King, Countess of Lovelace",
        access="public"
    )
    lovelace.birth = Event(
        name="Birth",
        date=Date(
            dmy=DMY(day=10, month=12, year=1815),
            calendar=Calendar.GREGORIAN
        ),
        place=Place(
            town="London",
            country="England"
        )
    )
    lovelace.death = Event(
        name="Death",
        date=Date(
            dmy=DMY(day=27, month=11, year=1852),
            calendar=Calendar.GREGORIAN
        ),
        place=Place(
            town="Marylebone",
            county="London",
            country="England"
        )
    )
    lovelace.notes = """
Ada Lovelace was an English mathematician and writer, chiefly known for
her work on Charles Babbage's proposed mechanical general-purpose computer,
the Analytical Engine. She is often regarded as the first computer programmer.
"""

    sample_persons["lovelace"] = lovelace


# Initialize sample data
init_sample_data()


@app.route('/')
def index():
    """Home page - displays welcome message and navigation."""
    return render_template('home.html',
                         persons=sample_persons,
                         title="GeneWeb Legacy Project")


@app.route('/person/<person_id>')
def person(person_id):
    """Display a person's page with all their information."""
    person_obj = sample_persons.get(person_id)

    if not person_obj:
        return render_template('404.html',
                             error=f"Person '{person_id}' not found"), 404

    # Prepare person context for template
    context = prepare_person_context(person_obj)

    return render_template('person.html', **context)


@app.route('/family/<family_id>')
def family(family_id):
    """Display a family page."""
    family_obj = sample_families.get(family_id)

    if not family_obj:
        return render_template('404.html',
                             error=f"Family '{family_id}' not found"), 404

    return render_template('family.html', family=family_obj)


@app.route('/search')
def search():
    """Search for persons or families."""
    query = request.args.get('q', '')
    return render_template('search.html', query=query)


@app.route('/api/persons')
def api_persons():
    """API endpoint to get list of persons as JSON."""
    persons_data = []
    for pid, person in sample_persons.items():
        persons_data.append({
            'id': pid,
            'first_name': person.first_name,
            'surname': person.surname,
            'sex': person.sex.name if person.sex else None,
            'occupation': person.occupation
        })
    return jsonify(persons_data)


@app.route('/api/person/<person_id>')
def api_person(person_id):
    """API endpoint to get a single person's data as JSON."""
    person = sample_persons.get(person_id)
    if not person:
        return jsonify({'error': 'Person not found'}), 404

    person_data = {
        'id': person_id,
        'first_name': person.first_name,
        'surname': person.surname,
        'sex': person.sex.name if person.sex else None,
        'occupation': person.occupation,
        'public_name': person.public_name,
        'notes': person.notes
    }

    if person.birth:
        person_data['birth'] = {
            'date': format_date(person.birth.date) if person.birth.date else None,
            'place': format_place(person.birth.place) if person.birth.place else None
        }

    if person.death:
        person_data['death'] = {
            'date': format_date(person.death.date) if person.death.date else None,
            'place': format_place(person.death.place) if person.death.place else None
        }

    return jsonify(person_data)


@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, images)."""
    return send_from_directory('static', filename)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html', error=str(error)), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return render_template('500.html', error=str(error)), 500


# Utility functions

def prepare_person_context(person):
    """
    Prepare person data for template rendering.
    Converts Person object to dict suitable for template.
    """
    context = {
        'person': person,
        'first_name': person.first_name,
        'surname': person.surname,
        'sex': person.sex.name if person.sex else 'Unknown',
        'occupation': person.occupation or '',
        'public_name': person.public_name or f"{person.first_name} {person.surname}",
        'notes': person.notes or '',
        'access': person.access or 'public',
    }

    # Add birth information
    if person.birth:
        context['birth_date'] = format_date(person.birth.date) if person.birth.date else ''
        context['birth_place'] = format_place(person.birth.place) if person.birth.place else ''
    else:
        context['birth_date'] = ''
        context['birth_place'] = ''

    # Add death information
    if person.death:
        context['death_date'] = format_date(person.death.date) if person.death.date else ''
        context['death_place'] = format_place(person.death.place) if person.death.place else ''
    else:
        context['death_date'] = ''
        context['death_place'] = ''

    # Add other events
    context['events'] = person.events if person.events else []

    return context


def format_date(date_obj):
    """Format a Date object as a string."""
    if not date_obj or not date_obj.dmy:
        return ''

    dmy = date_obj.dmy
    parts = []

    if dmy.day:
        parts.append(str(dmy.day))
    if dmy.month:
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']
        parts.append(months[dmy.month])
    if dmy.year:
        parts.append(str(dmy.year))

    return ' '.join(parts)


def format_place(place_obj):
    """Format a Place object as a string."""
    if not place_obj:
        return ''

    parts = []
    if place_obj.town:
        parts.append(place_obj.town)
    if place_obj.county:
        parts.append(place_obj.county)
    if place_obj.region:
        parts.append(place_obj.region)
    if place_obj.country:
        parts.append(place_obj.country)

    return ', '.join(parts)


if __name__ == '__main__':
    print("=" * 60)
    print("GeneWeb Legacy Project - Web Server")
    print("=" * 60)
    print("\nStarting Flask application...")
    print("\nAvailable routes:")
    print("  - Home:        http://localhost:5000/")
    print("  - Person:      http://localhost:5000/person/darwin")
    print("  - Person:      http://localhost:5000/person/lovelace")
    print("  - Search:      http://localhost:5000/search")
    print("  - API Persons: http://localhost:5000/api/persons")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()

    app.run(host='0.0.0.0', port=5000, debug=True)
