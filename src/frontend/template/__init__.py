"""
Template engine for Legacy Project.

Provides parsing and evaluation of Geneweb template files (.txt).
Translates geneweb/lib/templ/ OCaml module.
"""

from .ast import *
from .parser import TemplateParser
from .interpreter import TemplateInterpreter

__all__ = [
    'ASTNode', 'Text', 'Variable', 'Translation', 'If', 'ForEach',
    'For', 'Define', 'Apply', 'Let', 'Op1', 'Op2', 'Integer',
    'Include', 'Pack', 'WidthHeight',
    'TemplateParser', 'TemplateInterpreter'
]
