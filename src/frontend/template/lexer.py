"""
Template lexer - tokenizes Geneweb template syntax.

Translates geneweb/lib/templ/lexer.mll
Converts template text into tokens for parsing.

Template syntax:
- %variable; or %variable.field.subfield;
- %if;(condition)...%else;...%end;
- %foreach;collection;...%end;
- %for;i;min;max;...%end;
- %define;name(params)...%end;
- %apply;name%with;arg1%and;arg2%end;
- %let;var;...%in;...%end;
- [*translation key]
- %%(escaped %), %[, %], %/
- %(comment%)
"""

import re
from typing import List, Tuple, Optional, Iterator
from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """Token types in template language"""
    TEXT = auto()             # Plain text
    VARIABLE = auto()         # %var; or %var.field;
    TRANSLATION = auto()      # [*text]
    IF = auto()               # %if;
    ELSE = auto()             # %else;
    ELSEIF = auto()           # %elseif;
    END = auto()              # %end;
    FOREACH = auto()          # %foreach;
    FOR = auto()              # %for;
    DEFINE = auto()           # %define;
    APPLY = auto()            # %apply;
    WITH = auto()             # %with;
    AND = auto()              # %and;
    LET = auto()              # %let;
    IN = auto()               # %in;
    INCLUDE = auto()          # %include;
    WID_HEI = auto()          # %wid_hei;
    EXPR = auto()             # %expr;
    LPAREN = auto()           # (
    RPAREN = auto()           # )
    COMMA = auto()            # ,
    COLON = auto()            # :
    EQUALS = auto()           # =
    SEMICOLON = auto()        # ;
    DOT = auto()              # .
    IDENTIFIER = auto()       # Variable name
    NUMBER = auto()           # Integer literal
    STRING = auto()           # "quoted string"
    OPERATOR = auto()         # +, -, *, /, <, >, etc.
    EOF = auto()              # End of file


@dataclass
class Token:
    """A lexical token"""
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class TemplateLexer:
    """
    Lexer for Geneweb template language.
    Converts template source into stream of tokens.
    """

    def __init__(self, source: str, filename: str = "<template>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def current_char(self) -> Optional[str]:
        """Get current character without consuming"""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Peek ahead at character"""
        pos = self.pos + offset
        if pos < len(self.source):
            return self.source[pos]
        return None

    def advance(self) -> Optional[str]:
        """Consume and return current character"""
        if self.pos >= len(self.source):
            return None
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def skip_whitespace(self) -> None:
        """Skip whitespace characters"""
        while self.current_char() in ' \t\r\n':
            self.advance()

    def read_while(self, predicate) -> str:
        """Read characters while predicate is true"""
        result = []
        while self.current_char() and predicate(self.current_char()):
            result.append(self.advance())
        return ''.join(result)

    def read_identifier(self) -> str:
        """Read identifier: [a-zA-Z0-9_]+"""
        return self.read_while(lambda c: c.isalnum() or c == '_')

    def read_number(self) -> str:
        """Read number: [0-9]+"""
        return self.read_while(lambda c: c.isdigit())

    def read_string(self) -> str:
        """Read quoted string"""
        self.advance()  # Skip opening quote
        result = []
        while self.current_char() and self.current_char() != '"':
            result.append(self.advance())
        self.advance()  # Skip closing quote
        return ''.join(result)

    def make_token(self, token_type: TokenType, value: str) -> Token:
        """Create token at current position"""
        return Token(token_type, value, self.line, self.column)

    def read_variable(self) -> Token:
        """
        Read variable after %.
        Returns either VARIABLE token or keyword token.
        """
        start_line, start_col = self.line, self.column

        # Check for special escapes: %%, %[, %], %/
        char = self.current_char()
        if char in '%[]/':
            self.advance()
            return Token(TokenType.TEXT, char, start_line, start_col)

        # Check for comment: %(
        if char == '(':
            self.advance()
            self.read_comment()
            # Comments produce no token, return special marker
            return Token(TokenType.TEXT, '', start_line, start_col)

        # Read identifier
        if not (char and (char.isalpha() or char == '_')):
            return Token(TokenType.TEXT, '%', start_line, start_col)

        ident = self.read_identifier()

        # Read dotted fields: .field1.field2
        fields = [ident]
        while self.current_char() == '.':
            self.advance()  # Skip dot
            field = self.read_identifier() or self.read_number()
            if field:
                fields.append(field)

        # Check for semicolon terminator
        if self.current_char() == ';':
            self.advance()

        # Check if it's a keyword
        keyword = fields[0] if len(fields) == 1 else None
        keyword_map = {
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'elseif': TokenType.ELSEIF,
            'end': TokenType.END,
            'foreach': TokenType.FOREACH,
            'for': TokenType.FOR,
            'define': TokenType.DEFINE,
            'apply': TokenType.APPLY,
            'with': TokenType.WITH,
            'and': TokenType.AND,
            'let': TokenType.LET,
            'in': TokenType.IN,
            'include': TokenType.INCLUDE,
            'wid_hei': TokenType.WID_HEI,
            'expr': TokenType.EXPR,
            'sq': TokenType.TEXT,  # Special: strip whitespace
            'nn': TokenType.TEXT,  # Special: strip newline
        }

        if keyword and keyword in keyword_map:
            token_type = keyword_map[keyword]
            # Handle special whitespace-stripping variables
            if keyword == 'sq':
                # Skip following whitespace
                while self.current_char() in ' \t\r\n':
                    self.advance()
                return Token(TokenType.TEXT, '', start_line, start_col)
            elif keyword == 'nn':
                # Skip surrounding whitespace and newline
                while self.current_char() in ' \t\r':
                    self.advance()
                if self.current_char() == '\n':
                    self.advance()
                while self.current_char() in ' \t\r':
                    self.advance()
                return Token(TokenType.TEXT, '', start_line, start_col)
            return Token(token_type, keyword, start_line, start_col)

        # It's a regular variable reference
        value = '.'.join(fields)
        return Token(TokenType.VARIABLE, value, start_line, start_col)

    def read_comment(self) -> None:
        """Read comment block: %(comment%)"""
        depth = 1
        while depth > 0 and self.current_char():
            if self.current_char() == '%':
                self.advance()
                if self.current_char() == '(':
                    self.advance()
                    depth += 1
                elif self.current_char() == ')':
                    self.advance()
                    depth -= 1
                    # Skip whitespace after comment
                    if depth == 0:
                        while self.current_char() in ' \t\r\n':
                            self.advance()
            else:
                self.advance()

    def read_translation(self) -> Token:
        """
        Read translation block: [*text] or [text]
        Returns TRANSLATION token.
        """
        start_line, start_col = self.line, self.column
        self.advance()  # Skip opening [

        # Check for capitalization marker
        capitalize = False
        if self.current_char() == '*':
            capitalize = True
            self.advance()

        # Read translation key (nested brackets allowed)
        depth = 0
        chars = []
        while self.current_char():
            if self.current_char() == '[':
                depth += 1
                chars.append(self.advance())
            elif self.current_char() == ']':
                if depth == 0:
                    break
                depth -= 1
                chars.append(self.advance())
            else:
                chars.append(self.advance())

        text = ''.join(chars)
        self.advance()  # Skip closing ]

        # Read optional index/choice marker (0-9, a-z)
        choice = ''
        if self.current_char() and (self.current_char().isdigit() or self.current_char().islower()):
            choice = self.advance()

        # Format: "cap|key|choice"
        value = f"{'*' if capitalize else ''}|{text}|{choice}"
        return Token(TokenType.TRANSLATION, value, start_line, start_col)

    def read_text(self) -> Token:
        """Read plain text until special character"""
        start_line, start_col = self.line, self.column
        chars = []

        while self.current_char():
            char = self.current_char()
            # Stop at template markers
            if char in '%[':
                break
            # Normalize newlines
            if char == '\n':
                # Check if previous newlines exist, collapse them
                chars.append(self.advance())
                # Skip redundant whitespace after newline
                while self.current_char() and self.current_char() in ' \t\r\n':
                    if self.current_char() == '\n':
                        break
                    self.advance()
            else:
                chars.append(self.advance())

        text = ''.join(chars)
        return Token(TokenType.TEXT, text, start_line, start_col)

    def tokenize(self) -> List[Token]:
        """
        Tokenize entire template source.
        Returns list of tokens.
        """
        tokens = []

        while self.pos < len(self.source):
            char = self.current_char()

            if char == '%':
                self.advance()  # Consume %
                token = self.read_variable()
                if token.value or token.type != TokenType.TEXT:  # Skip empty text from comments
                    tokens.append(token)

            elif char == '[':
                token = self.read_translation()
                tokens.append(token)

            else:
                token = self.read_text()
                if token.value:  # Only add non-empty text
                    tokens.append(token)

        # Add EOF token
        tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return tokens


def tokenize(source: str, filename: str = "<template>") -> List[Token]:
    """
    Convenience function to tokenize template source.

    Args:
        source: Template source code
        filename: Source filename for error messages

    Returns:
        List of tokens
    """
    lexer = TemplateLexer(source, filename)
    return lexer.tokenize()
