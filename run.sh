#!/bin/bash

# Script to run the GeneWeb Legacy Project web server

echo "============================================================"
echo "GeneWeb Legacy Project - Setup and Run"
echo "============================================================"
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install Python 3 and pip."
    exit 1
fi

echo "📦 Installing dependencies..."
pip3 install -q flask jinja2 2>&1 | grep -v "already satisfied" || echo "✅ Flask and Jinja2 installed"

echo ""
echo "🚀 Starting Flask web server..."
echo ""

# Run the Flask application
python3 app.py
