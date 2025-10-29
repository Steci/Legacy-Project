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

# Import GeneWeb parser
from parsers.gw import load_geneweb_file, GWDatabase

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Configure Flask
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['DEBUG'] = True

# Data storage for persons and families
sample_persons = {}
sample_families = {}

# Configure which .gw file to load
# You can change this to point to any .gw file in your system
GENEWEB_DB_PATH = os.path.join(
    os.path.dirname(__file__),
    'examples_files',
    'galichet_ref.gw'  # Change to 'example.gw' for a smaller dataset
)


def load_geneweb_database():
    """
    Load GeneWeb database from .gw file and populate sample_persons and sample_families.

    This replaces the old init_sample_data() function that created Darwin and Lovelace.
    """
    global sample_persons, sample_families

    print("=" * 60)
    print("Loading GeneWeb Database")
    print("=" * 60)
    print(f"Loading from: {GENEWEB_DB_PATH}")

    # Check if file exists
    if not os.path.exists(GENEWEB_DB_PATH):
        print(f"ERROR: GeneWeb file not found at {GENEWEB_DB_PATH}")
        print("Falling back to empty database.")
        return

    try:
        # Load the GeneWeb database using the parser
        db: GWDatabase = load_geneweb_file(
            GENEWEB_DB_PATH,
            compute_consanguinity=True,  # Compute relationships
            from_scratch=True,
            debug=False
        )

        # Convert persons from GWDatabase to sample_persons dict
        # The key format from parser is "Surname Firstname.number" or "Surname Firstname"
        sample_persons.clear()
        for person_key, person in db.persons.items():
            # Use the person key as the ID for URL routing
            # Clean up the key to make it URL-friendly
            person_id = person_key.lower().replace(" ", "_").replace(".", "_")
            sample_persons[person_id] = person

        # Merge notes into person objects
        for note_block in db.notes:
            person_key = note_block.person_key
            if person_key in db.persons:
                person = db.persons[person_key]
                person.notes = note_block.text

        # Convert families from GWDatabase to sample_families dict
        sample_families.clear()
        for idx, family in enumerate(db.families):
            family_id = f"family_{idx}"
            sample_families[family_id] = family

        print(f"Successfully loaded {len(sample_persons)} persons")
        print(f"Successfully loaded {len(sample_families)} families")

        # Print first few persons for verification
        if sample_persons:
            print("\nFirst 5 persons loaded:")
            for i, (person_id, person) in enumerate(list(sample_persons.items())[:5]):
                print(f"  - {person_id}: {person.first_name} {person.surname}")

        print("=" * 60)

    except Exception as e:
        print(f"ERROR loading GeneWeb database: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with empty database.")
        print("=" * 60)


# Load GeneWeb data at startup
load_geneweb_database()


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


@app.route('/management')
def management():
    """Management and administration page."""
    return render_template('management.html')


@app.route('/search')
def search():
    """Search for persons or families."""
    query = request.args.get('q', '').strip()

    results = []
    family_results = []

    if query:
        # Search is case-insensitive
        query_lower = query.lower()

        # Search persons
        for person_id, person in sample_persons.items():
            # Check if query matches first name, surname, occupation, or place
            matches = False

            # Check names
            if query_lower in person.first_name.lower():
                matches = True
            if query_lower in person.surname.lower():
                matches = True
            if person.public_name and query_lower in person.public_name.lower():
                matches = True

            # Check occupation
            if person.occupation and query_lower in person.occupation.lower():
                matches = True

            # Check birth place
            if person.birth and person.birth.place:
                place = person.birth.place
                if place.town and query_lower in place.town.lower():
                    matches = True
                if place.county and query_lower in place.county.lower():
                    matches = True
                if place.region and query_lower in place.region.lower():
                    matches = True
                if place.country and query_lower in place.country.lower():
                    matches = True

            # Check death place
            if person.death and person.death.place:
                place = person.death.place
                if place.town and query_lower in place.town.lower():
                    matches = True
                if place.county and query_lower in place.county.lower():
                    matches = True
                if place.region and query_lower in place.region.lower():
                    matches = True
                if place.country and query_lower in place.country.lower():
                    matches = True

            # Check notes
            if person.notes and query_lower in person.notes.lower():
                matches = True

            if matches:
                results.append((person_id, person))

        # Search families
        for family_id, family in sample_families.items():
            matches = False

            # Check husband and wife names
            if family.husband and query_lower in family.husband.lower():
                matches = True
            if family.wife and query_lower in family.wife.lower():
                matches = True

            if matches:
                family_results.append((family_id, family))

    return render_template('search.html',
                         query=query,
                         results=results,
                         family_results=family_results)


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
    print("  - Search:      http://localhost:5000/search")
    print("  - API Persons: http://localhost:5000/api/persons")

    # Show available person URLs
    if sample_persons:
        print("\nExample person pages:")
        for person_id in list(sample_persons.keys())[:5]:  # Show first 5
            print(f"  - http://localhost:5000/person/{person_id}")

    # Show available family URLs
    if sample_families:
        print("\nExample family pages:")
        for family_id in list(sample_families.keys())[:3]:  # Show first 3
            print(f"  - http://localhost:5000/family/{family_id}")

    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()

    app.run(host='0.0.0.0', port=5000, debug=True)
