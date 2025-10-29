"""
Frontend generation system for Legacy Project.

This module provides HTML generation capabilities for the Geneweb genealogy system,
including:
- Template parsing and evaluation (template/)
- HTTP output handling (output.py)
- Display modules for various page types (display/)
- Request configuration (config.py)

Architecture:
    Template (.txt) → Lexer → Parser → AST → Interpreter → HTML Output

Integration:
    - Uses models/ for Person, Family, Event, Date data structures
    - Uses sosa/ for Sosa number calculations
    - Uses consang/ for consanguinity analysis

Translated from Geneweb's OCaml frontend system.
"""

from .config import RequestConfig, AuthScheme, AuthInfo, DateDMY, create_empty_config
from .output import (
    Output,
    OutputHandler,
    StandardOutputHandler,
    BufferedOutputHandler,
    HttpStatus
)

__version__ = "0.1.0"

__all__ = [
    # Config
    'RequestConfig',
    'AuthScheme',
    'AuthInfo',
    'DateDMY',
    'create_empty_config',
    # Output
    'Output',
    'OutputHandler',
    'StandardOutputHandler',
    'BufferedOutputHandler',
    'HttpStatus',
]
