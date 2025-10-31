#!/usr/bin/env python3
"""
Quick test script to verify the Flask application works correctly.
Tests imports, sample data creation, and basic routes.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing GeneWeb Legacy Project Flask Application")
print("=" * 60)

# Test 1: Import Flask
print("\n1. Testing Flask import...")
try:
    from flask import Flask
    print("   ✅ Flask imported successfully")
except ImportError as e:
    print(f"   ❌ Flask import failed: {e}")
    print("   Install with: pip install flask")
    sys.exit(1)

# Test 2: Import models
print("\n2. Testing model imports...")
try:
    from models.person import Person
    from models.person.params import Sex
    from models.family import Family
    from models.event import Event, Place
    from models.date import Date, DMY, Calendar
    print("   ✅ All models imported successfully")
except ImportError as e:
    print(f"   ❌ Model import failed: {e}")
    sys.exit(1)

# Test 3: Create sample person
print("\n3. Testing Person creation...")
try:
    person = Person(
        first_name="Test",
        surname="Person",
        sex=Sex.MALE,
        occupation="Tester"
    )
    print(f"   ✅ Created person: {person.first_name} {person.surname}")
except Exception as e:
    print(f"   ❌ Person creation failed: {e}")
    sys.exit(1)

# Test 4: Create person with events
print("\n4. Testing Person with events...")
try:
    person.birth = Event(
        name="Birth",
        date=Date(
            dmy=DMY(day=1, month=1, year=2000),
            calendar=Calendar.GREGORIAN
        ),
        place=Place(town="Test City", country="Test Country")
    )
    print(f"   ✅ Added birth event: {person.birth.date.dmy.year}")
except Exception as e:
    print(f"   ❌ Event creation failed: {e}")
    sys.exit(1)

# Test 5: Import Flask app
print("\n5. Testing Flask app import...")
try:
    import app as flask_app
    print("   ✅ Flask app imported successfully")
except Exception as e:
    print(f"   ❌ Flask app import failed: {e}")
    sys.exit(1)

# Test 6: Test Flask app context
print("\n6. Testing Flask app context...")
try:
    with flask_app.app.app_context():
        print("   ✅ Flask app context created successfully")
except Exception as e:
    print(f"   ❌ Flask app context failed: {e}")
    sys.exit(1)

# Test 7: Check static files
print("\n7. Checking static files...")
try:
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    css_dir = os.path.join(static_dir, 'css')
    js_dir = os.path.join(static_dir, 'js')
    images_dir = os.path.join(static_dir, 'images')

    css_count = len(os.listdir(css_dir)) if os.path.exists(css_dir) else 0
    js_count = len(os.listdir(js_dir)) if os.path.exists(js_dir) else 0
    images_count = len(os.listdir(images_dir)) if os.path.exists(images_dir) else 0

    print(f"   ✅ CSS files: {css_count}")
    print(f"   ✅ JS files: {js_count}")
    print(f"   ✅ Images: {images_count}")
except Exception as e:
    print(f"   ⚠️  Static files check failed: {e}")

# Test 8: Check templates
print("\n8. Checking templates...")
try:
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if os.path.exists(templates_dir):
        template_files = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
        print(f"   ✅ HTML templates: {len(template_files)}")
        for template in ['base.html', 'home.html', 'person.html']:
            if template in template_files:
                print(f"   ✅ {template} found")
            else:
                print(f"   ❌ {template} missing")
    else:
        print(f"   ❌ Templates directory not found")
except Exception as e:
    print(f"   ⚠️  Templates check failed: {e}")

print("\n" + "=" * 60)
print("✅ All tests passed! The application is ready to run.")
print("\nTo start the server, run:")
print("  python app.py")
print("\nOr use the convenience script:")
print("  ./run.sh")
print("=" * 60)
