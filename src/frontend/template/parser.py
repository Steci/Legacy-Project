"""
Template parser - builds AST from tokens.

Translates geneweb/lib/templ/parser.ml and lexer.mll parsing logic.
Constructs Abstract Syntax Tree from token stream.
"""

from typing import List, Optional, Tuple, Union
from .lexer import Token, TokenType, tokenize
from .ast import *


class ParseError(Exception):
    """Parse error with location"""

    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"{message} at {token.line}:{token.column}")


class TemplateParser:
    """
    Parser for Geneweb template language.
    Builds AST from token stream.
    """

    def __init__(self, tokens: List[Token], filename: str = "<template>"):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    def current_token(self) -> Token:
        """Get current token without consuming"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def peek_token(self, offset: int = 1) -> Token:
        """Peek ahead at token"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # EOF

    def advance(self) -> Token:
        """Consume and return current token"""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """Expect specific token type and consume it"""
        token = self.current_token()
        if token.type != token_type:
            raise ParseError(f"Expected {token_type.name}, got {token.type.name}", token)
        return self.advance()

    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of given types"""
        return self.current_token().type in token_types

    def location(self) -> Location:
        """Get current location"""
        token = self.current_token()
        return Location(self.filename, token.line, token.column)

    def parse(self) -> List[ASTNode]:
        """
        Parse entire template.
        Returns list of AST nodes.
        """
        return self.parse_nodes(stop_at=[TokenType.EOF])

    def parse_nodes(self, stop_at: List[TokenType]) -> List[ASTNode]:
        """
        Parse sequence of nodes until stop token.
        Returns list of AST nodes.
        """
        nodes = []

        while not self.match(*stop_at):
            if self.match(TokenType.EOF):
                break

            node = self.parse_node()
            if node:
                nodes.append(node)

        return nodes

    def parse_node(self) -> Optional[ASTNode]:
        """Parse single node"""
        token = self.current_token()
        loc = self.location()

        if token.type == TokenType.TEXT:
            self.advance()
            node = Text(token.value)
            node.loc = loc
            return node

        elif token.type == TokenType.VARIABLE:
            self.advance()
            # Split variable path: var.field.subfield
            parts = token.value.split('.')
            node = Variable(parts[0], parts[1:] if len(parts) > 1 else [])
            node.loc = loc
            return node

        elif token.type == TokenType.TRANSLATION:
            self.advance()
            # Parse format: "cap|key|choice"
            parts = token.value.split('|')
            capitalize = parts[0] == '*'
            key = parts[1] if len(parts) > 1 else ''
            choice = parts[2] if len(parts) > 2 else ''
            node = Translation(capitalize, key, choice)
            node.loc = loc
            return node

        elif token.type == TokenType.IF:
            return self.parse_if()

        elif token.type == TokenType.FOREACH:
            return self.parse_foreach()

        elif token.type == TokenType.FOR:
            return self.parse_for()

        elif token.type == TokenType.DEFINE:
            return self.parse_define()

        elif token.type == TokenType.APPLY:
            return self.parse_apply()

        elif token.type == TokenType.LET:
            return self.parse_let()

        elif token.type == TokenType.INCLUDE:
            return self.parse_include()

        elif token.type == TokenType.WID_HEI:
            return self.parse_wid_hei()

        else:
            raise ParseError(f"Unexpected token: {token.type.name}", token)

    def parse_if(self) -> If:
        """Parse if statement: %if;(expr)...%else;...%end;"""
        loc = self.location()
        self.advance()  # Skip IF

        # Parse condition expression
        condition = self.parse_expression()

        # Parse then branch
        then_branch = self.parse_nodes([TokenType.ELSE, TokenType.ELSEIF, TokenType.END])

        # Parse else/elseif branches
        else_branch = []
        while self.match(TokenType.ELSEIF):
            # Convert elseif to nested if
            self.advance()
            elif_condition = self.parse_expression()
            elif_then = self.parse_nodes([TokenType.ELSE, TokenType.ELSEIF, TokenType.END])

            elif_loc = self.location()
            elif_node = If(elif_condition, elif_then, [])
            elif_node.loc = elif_loc
            else_branch = [elif_node]
            break

        if self.match(TokenType.ELSE):
            self.advance()
            else_branch = self.parse_nodes([TokenType.END])

        self.expect(TokenType.END)

        node = If(condition, then_branch, else_branch)
        node.loc = loc
        return node

    def parse_foreach(self) -> ForEach:
        """Parse foreach: %foreach;collection;...%end;"""
        loc = self.location()
        self.advance()  # Skip FOREACH

        # Parse iterator variable - could be TEXT or VARIABLE after %foreach;
        token = self.current_token()
        if token.type == TokenType.VARIABLE:
            var_token = self.advance()
            parts = var_token.value.split('.')
        elif token.type == TokenType.TEXT:
            text = self.advance().value.strip()
            var_name = text.split(';')[0] if ';' in text else text
            parts = var_name.split('.')
        else:
            raise ParseError("Expected iterator variable after %foreach;", token)

        iterator = parts[0] if parts else "item"
        fields = parts[1:] if len(parts) > 1 else []

        # Parse optional loop parameters (not commonly used)
        loop_params = []

        # Parse body
        body = self.parse_nodes([TokenType.END])
        self.expect(TokenType.END)

        node = ForEach(iterator, fields, loop_params, body)
        node.loc = loc
        return node

    def parse_for(self) -> For:
        """Parse for loop: %for;i;min;max;...%end;"""
        loc = self.location()
        self.advance()  # Skip FOR

        # Parse iterator variable - could be TEXT or VARIABLE after %for;
        token = self.current_token()
        if token.type == TokenType.VARIABLE:
            iterator = self.advance().value
        elif token.type == TokenType.TEXT:
            # Text immediately after %for; is the iterator name
            text = self.advance().value.strip()
            iterator = text.split(';')[0] if ';' in text else text
        else:
            raise ParseError("Expected iterator variable after %for;", token)

        # Parse min expression
        start = self.parse_expression()

        # Parse max expression
        end = self.parse_expression()

        # Parse body
        body = self.parse_nodes([TokenType.END])
        self.expect(TokenType.END)

        node = For(iterator, start, end, body)
        node.loc = loc
        return node

    def parse_define(self) -> Define:
        """Parse function definition: %define;name(params)...%end;"""
        loc = self.location()
        self.advance()  # Skip DEFINE

        # Parse function name
        name_token = self.expect(TokenType.VARIABLE)
        name = name_token.value

        # Parse parameters
        params = self.parse_params()

        # Parse body
        body = self.parse_nodes([TokenType.END])
        self.expect(TokenType.END)

        # Parse continuation (code after define)
        continuation = []

        node = Define(name, params, body, continuation)
        node.loc = loc
        return node

    def parse_params(self) -> List[Tuple[str, Optional[ASTNode]]]:
        """Parse function parameters: (param1, param2=default, ...)"""
        params = []

        # Parameters might be inline or omitted
        if not self.match(TokenType.LPAREN):
            return params

        self.advance()  # Skip LPAREN

        while not self.match(TokenType.RPAREN):
            # Parse parameter name
            if not self.match(TokenType.VARIABLE):
                break

            param_name = self.advance().value

            # Check for default value
            default = None
            if self.match(TokenType.EQUALS):
                self.advance()
                default = self.parse_expression()

            params.append((param_name, default))

            # Check for comma separator
            if self.match(TokenType.COMMA):
                self.advance()

        if self.match(TokenType.RPAREN):
            self.advance()

        return params

    def parse_apply(self) -> Apply:
        """Parse function application: %apply;name%with;arg1%and;arg2%end;"""
        loc = self.location()
        self.advance()  # Skip APPLY

        # Parse function name - could be TEXT or VARIABLE
        token = self.current_token()
        if token.type == TokenType.VARIABLE:
            name = self.advance().value
        elif token.type == TokenType.TEXT:
            text = self.advance().value.strip()
            name = text.split('%')[0].strip() if '%' in text else text
        else:
            raise ParseError("Expected function name after %apply;", token)

        # Check for %with; or immediate arguments
        args = []

        if self.match(TokenType.WITH):
            self.advance()
            # Parse arguments separated by %and;
            while True:
                arg_nodes = self.parse_nodes([TokenType.AND, TokenType.END])
                args.append((None, arg_nodes))

                if self.match(TokenType.AND):
                    self.advance()
                else:
                    break

            self.expect(TokenType.END)

        node = Apply(name, args)
        node.loc = loc
        return node

    def parse_let(self) -> Let:
        """Parse let binding: %let;var;value%in;body%end;"""
        loc = self.location()
        self.advance()  # Skip LET

        # Parse variable name - could be TEXT or VARIABLE
        token = self.current_token()
        if token.type == TokenType.VARIABLE:
            var_name = self.advance().value
        elif token.type == TokenType.TEXT:
            text = self.advance().value.strip()
            var_name = text.split(';')[0] if ';' in text else text
        else:
            raise ParseError("Expected variable name after %let;", token)

        # Parse value
        value = self.parse_nodes([TokenType.IN])
        self.expect(TokenType.IN)

        # Parse body
        body = self.parse_nodes([TokenType.END])
        self.expect(TokenType.END)

        node = Let(var_name, value, body)
        node.loc = loc
        return node

    def parse_include(self) -> Include:
        """Parse include: %include;filename"""
        loc = self.location()
        self.advance()  # Skip INCLUDE

        # Parse filename
        token = self.current_token()
        if token.type == TokenType.VARIABLE:
            filename = self.advance().value
        elif token.type == TokenType.TEXT:
            filename = self.advance().value
        else:
            raise ParseError("Expected filename after %include;", token)

        node = Include(filename, is_file=True)
        node.loc = loc
        return node

    def parse_wid_hei(self) -> WidthHeight:
        """Parse width/height: %wid_hei;filename"""
        loc = self.location()
        self.advance()  # Skip WID_HEI

        # Parse filename
        token = self.current_token()
        if token.type == TokenType.VARIABLE:
            filename = self.advance().value
        elif token.type == TokenType.TEXT:
            filename = self.advance().value
        else:
            filename = ""

        node = WidthHeight(filename)
        node.loc = loc
        return node

    def parse_expression(self) -> ASTNode:
        """Parse expression (for conditions, etc.)"""
        # Handle parenthesized expressions
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_or_expr()
            if self.match(TokenType.RPAREN):
                self.advance()
            return expr

        return self.parse_or_expr()

    def parse_or_expr(self) -> ASTNode:
        """Parse OR expression"""
        left = self.parse_and_expr()

        while self.match(TokenType.VARIABLE) and self.current_token().value == 'or':
            loc = self.location()
            self.advance()
            right = self.parse_and_expr()
            node = Op2('or', left, right)
            node.loc = loc
            left = node

        return left

    def parse_and_expr(self) -> ASTNode:
        """Parse AND expression"""
        left = self.parse_comparison_expr()

        while self.match(TokenType.VARIABLE) and self.current_token().value == 'and':
            loc = self.location()
            self.advance()
            right = self.parse_comparison_expr()
            node = Op2('and', left, right)
            node.loc = loc
            left = node

        return left

    def parse_comparison_expr(self) -> ASTNode:
        """Parse comparison expression"""
        left = self.parse_additive_expr()

        # Check for comparison operators
        token = self.current_token()
        if token.type == TokenType.OPERATOR or (
            token.type == TokenType.VARIABLE and token.value in ['in', 'is_substr']
        ):
            loc = self.location()
            op = self.advance().value
            right = self.parse_additive_expr()
            node = Op2(op, left, right)
            node.loc = loc
            return node

        return left

    def parse_additive_expr(self) -> ASTNode:
        """Parse addition/subtraction expression"""
        left = self.parse_multiplicative_expr()

        while self.match(TokenType.OPERATOR):
            token = self.current_token()
            if token.value not in ['+', '-']:
                break
            loc = self.location()
            op = self.advance().value
            right = self.parse_multiplicative_expr()
            node = Op2(op, left, right)
            node.loc = loc
            left = node

        return left

    def parse_multiplicative_expr(self) -> ASTNode:
        """Parse multiplication/division expression"""
        left = self.parse_unary_expr()

        while self.match(TokenType.OPERATOR):
            token = self.current_token()
            if token.value not in ['*', '/', '|', '%', '^', '/.']:
                break
            loc = self.location()
            op = self.advance().value
            right = self.parse_unary_expr()
            node = Op2(op, left, right)
            node.loc = loc
            left = node

        return left

    def parse_unary_expr(self) -> ASTNode:
        """Parse unary expression"""
        if self.match(TokenType.VARIABLE) and self.current_token().value == 'not':
            loc = self.location()
            self.advance()
            operand = self.parse_unary_expr()
            node = Op1('not', operand)
            node.loc = loc
            return node

        return self.parse_primary_expr()

    def parse_primary_expr(self) -> ASTNode:
        """Parse primary expression"""
        loc = self.location()
        token = self.current_token()

        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        elif token.type == TokenType.NUMBER:
            self.advance()
            node = Integer(token.value)
            node.loc = loc
            return node

        elif token.type == TokenType.STRING:
            self.advance()
            node = Text(token.value)
            node.loc = loc
            return node

        elif token.type == TokenType.VARIABLE:
            self.advance()
            parts = token.value.split('.')
            node = Variable(parts[0], parts[1:] if len(parts) > 1 else [])
            node.loc = loc
            return node

        elif token.type == TokenType.TRANSLATION:
            self.advance()
            parts = token.value.split('|')
            capitalize = parts[0] == '*'
            key = parts[1] if len(parts) > 1 else ''
            choice = parts[2] if len(parts) > 2 else ''
            node = Translation(capitalize, key, choice)
            node.loc = loc
            return node

        elif token.type == TokenType.TEXT:
            self.advance()
            node = Text(token.value)
            node.loc = loc
            return node

        else:
            raise ParseError(f"Unexpected token in expression: {token.type.name}", token)


def parse(source: str, filename: str = "<template>") -> List[ASTNode]:
    """
    Convenience function to parse template source.

    Args:
        source: Template source code
        filename: Source filename for error messages

    Returns:
        List of AST nodes
    """
    tokens = tokenize(source, filename)
    parser = TemplateParser(tokens, filename)
    return parser.parse()
