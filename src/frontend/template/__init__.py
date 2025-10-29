"""
Template engine for Legacy Project.

Provides parsing and evaluation of Geneweb template files (.txt).
Translates geneweb/lib/templ/ OCaml module.

Three-stage pipeline:
    1. Lexer (lexer.py) - Tokenizes template source
    2. Parser (parser.py) - Builds AST from tokens
    3. Interpreter (interpreter.py) - Evaluates AST with context

Usage:
    from frontend.template import parse, render_template
    from frontend.config import RequestConfig

    config = RequestConfig(...)
    html = render_template(template_source, config)

Integration:
    - Uses frontend.config.RequestConfig for context
    - Compatible with models.person.Person and models.family.Family data
    - Outputs HTML via frontend.output.Output
"""

from .ast import (
    ASTNode, Location,
    Text, Variable, Translation, WidthHeight,
    If, ForEach, For, Define, Apply, Let,
    Op1, Op2, Integer, Include, Pack,
    make_text, make_variable, make_if, make_op2, make_integer
)
from .lexer import tokenize, Token, TokenType, TemplateLexer
from .parser import parse, TemplateParser, ParseError
from .interpreter import (
    interpret, render_template,
    TemplateInterpreter, InterpretError, Environment
)

__all__ = [
    # AST nodes
    'ASTNode', 'Location',
    'Text', 'Variable', 'Translation', 'WidthHeight',
    'If', 'ForEach', 'For', 'Define', 'Apply', 'Let',
    'Op1', 'Op2', 'Integer', 'Include', 'Pack',
    # AST helpers
    'make_text', 'make_variable', 'make_if', 'make_op2', 'make_integer',
    # Lexer
    'tokenize', 'Token', 'TokenType', 'TemplateLexer',
    # Parser
    'parse', 'TemplateParser', 'ParseError',
    # Interpreter
    'interpret', 'render_template',
    'TemplateInterpreter', 'InterpretError', 'Environment',
]

