"""
Template interpreter - evaluates AST to generate output.

Translates geneweb/lib/templ.ml
Executes template AST with given configuration context.
"""

from typing import Dict, List, Any, Optional, Callable, Union
from .ast import *
from .parser import parse
from ..config import RequestConfig
from ..output import Output
import html
import re


class InterpretError(Exception):
    """Interpretation error with location"""

    def __init__(self, message: str, location: Optional[Location] = None):
        self.location = location
        if location:
            super().__init__(f"{message} at {location}")
        else:
            super().__init__(message)


class Environment:
    """
    Variable environment for template evaluation.
    Supports nested scopes.
    """

    def __init__(self, parent: Optional['Environment'] = None):
        self.vars: Dict[str, Any] = {}
        self.parent = parent

    def set(self, name: str, value: Any) -> None:
        """Set variable in current scope"""
        self.vars[name] = value

    def get(self, name: str) -> Optional[Any]:
        """Get variable from current or parent scope"""
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def child(self) -> 'Environment':
        """Create child environment"""
        return Environment(self)


class TemplateInterpreter:
    """
    Interpreter for Geneweb template language.
    Evaluates AST with configuration context to generate HTML output.
    """

    def __init__(self, config: RequestConfig):
        self.config = config
        self.env = Environment()
        self.functions: Dict[str, Tuple[List[Tuple[str, Optional[ASTNode]]], List[ASTNode]]] = {}
        self.output_buffer: List[str] = []

        # Register built-in functions
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in functions"""
        # Built-in functions are handled specially in eval_apply
        pass

    def interpret(self, ast: List[ASTNode]) -> str:
        """
        Interpret AST and return generated output.

        Args:
            ast: List of AST nodes to evaluate

        Returns:
            Generated HTML/text output
        """
        self.output_buffer = []
        for node in ast:
            self.eval_node(node)
        return ''.join(self.output_buffer)

    def write(self, text: str) -> None:
        """Write text to output buffer"""
        self.output_buffer.append(text)

    def eval_node(self, node: ASTNode) -> None:
        """
        Evaluate AST node and write output.
        For statements (if, for, etc.), executes side effects.
        """
        if isinstance(node, Text):
            self.write(node.content)

        elif isinstance(node, Variable):
            value = self.eval_variable(node.name, node.fields)
            self.write(self.stringify(value))

        elif isinstance(node, Translation):
            text = self.eval_translation(node.capitalize, node.key, node.choice)
            self.write(text)

        elif isinstance(node, WidthHeight):
            # TODO: Get image dimensions
            # For now, just output empty (would need image file access)
            pass

        elif isinstance(node, If):
            self.eval_if(node)

        elif isinstance(node, ForEach):
            self.eval_foreach(node)

        elif isinstance(node, For):
            self.eval_for(node)

        elif isinstance(node, Define):
            self.eval_define(node)

        elif isinstance(node, Apply):
            result = self.eval_apply(node.name, node.args)
            self.write(self.stringify(result))

        elif isinstance(node, Let):
            self.eval_let(node)

        elif isinstance(node, Include):
            self.eval_include(node)

        elif isinstance(node, Pack):
            for child in node.nodes:
                self.eval_node(child)

        else:
            raise InterpretError(f"Unknown node type: {type(node).__name__}", node.loc)

    def eval_expr(self, node: ASTNode) -> Any:
        """
        Evaluate AST node as expression (returns value).
        For expressions, returns the computed value.
        """
        if isinstance(node, Text):
            return node.content

        elif isinstance(node, Integer):
            return int(node.value)

        elif isinstance(node, Variable):
            return self.eval_variable(node.name, node.fields)

        elif isinstance(node, Translation):
            return self.eval_translation(node.capitalize, node.key, node.choice)

        elif isinstance(node, Op1):
            return self.eval_op1(node.operator, node.operand)

        elif isinstance(node, Op2):
            return self.eval_op2(node.operator, node.left, node.right)

        elif isinstance(node, Apply):
            return self.eval_apply(node.name, node.args)

        elif isinstance(node, If):
            # If as expression: return result of taken branch
            condition = self.eval_expr(node.condition)
            branch = node.then_branch if self.is_truthy(condition) else node.else_branch
            results = [self.eval_expr(n) for n in branch]
            return ''.join(self.stringify(r) for r in results)

        else:
            raise InterpretError(f"Cannot evaluate {type(node).__name__} as expression", node.loc)

    def eval_variable(self, name: str, fields: List[str]) -> Any:
        """
        Evaluate variable reference.
        Handles local variables, config fields, and built-in variables.
        """
        # Check local environment first
        value = self.env.get(name)
        if value is not None:
            # Navigate through fields
            for field in fields:
                if isinstance(value, dict):
                    value = value.get(field, f"%{name}.{'.'.join(fields)}?")
                elif hasattr(value, field):
                    value = getattr(value, field)
                else:
                    return f"%{name}.{'.'.join(fields)}?"
            return value

        # Check built-in variables
        full_path = [name] + fields
        builtin = self.eval_builtin_variable(full_path)
        if builtin is not None:
            return builtin

        # Variable not found
        return f"%{'.'.join(full_path)}?"

    def eval_builtin_variable(self, path: List[str]) -> Optional[Any]:
        """
        Evaluate built-in variables from config.

        Translates geneweb/lib/templ.ml eval_variable and eval_simple_variable.
        """
        if not path:
            return None

        key = '.'.join(path)

        # Common built-in variables
        builtins = {
            'lang': self.config.lang,
            'base.name': self.config.base_name,
            'bname': self.config.base_name,
            'prefix': self.config.prefix,
            'charset': self.config.charset,
            'nl': '\n',
            'nn': '',
            'sp': ' ',
            'wizard': self.config.wizard,
            'friend': self.config.friend,
            'manitou': self.config.manitou,
            'cgi': self.config.cgi,
            'debug': self.config.debug,
            'true': True,
            'false': False,
        }

        if key in builtins:
            return builtins[key]

        # Environment variables
        if len(path) >= 2:
            if path[0] == 'e' or path[0] == 'evar':
                # Environment variable: %e.varname; or %evar.varname;
                var_name = path[1]
                value = self.config.get_env(var_name)
                if len(path) > 2:
                    # Sub-fields not commonly used
                    pass
                return value

            elif path[0] == 'b' or path[0] == 'bvar':
                # Base environment variable: %b.varname; or %bvar.varname;
                var_name = path[1]
                return self.config.get_base_env(var_name)

        # Date/time variables
        if path[0] == 'today':
            today = self.config.today
            if len(path) == 1:
                return f"{today.year}-{today.month:02d}-{today.day:02d}"
            elif path[1] == 'day':
                return str(today.day)
            elif path[1] == 'month':
                return str(today.month)
            elif path[1] == 'year':
                return str(today.year)

        if path[0] == 'time':
            h, m, s = self.config.time
            if len(path) == 1:
                return f"{h:02d}:{m:02d}:{s:02d}"
            elif path[1] == 'hours':
                return f"{h:02d}"
            elif path[1] == 'minutes':
                return f"{m:02d}"
            elif path[1] == 'seconds':
                return f"{s:02d}"

        # Database info
        if path[0] == 'nb_persons' or path[0] == 'nb_of_persons':
            return str(self.config.nb_of_persons)
        if path[0] == 'nb_families' or path[0] == 'nb_of_families':
            return str(self.config.nb_of_families)

        return None

    def eval_translation(self, capitalize: bool, key: str, choice: str) -> str:
        """
        Evaluate translation/localization.

        Args:
            capitalize: Whether to capitalize first letter
            key: Translation key
            choice: Plural/gender choice (0, 1, 2, n, s, w, f, c, e, t)

        Returns:
            Translated text
        """
        # Check lexicon dictionary
        translated = self.config.lexicon.get(key, key)

        # Handle choice/plural forms
        if choice and '/' in translated:
            # Split on / and select appropriate form
            forms = translated.split('/')
            if choice.isdigit():
                idx = int(choice)
                if idx < len(forms):
                    translated = forms[idx]
            elif choice == 'n':  # plural
                translated = forms[-1] if len(forms) > 1 else forms[0]

        # Capitalize if requested
        if capitalize and translated:
            translated = translated[0].upper() + translated[1:] if len(translated) > 1 else translated.upper()

        return translated

    def eval_if(self, node: If) -> None:
        """Evaluate if statement"""
        condition = self.eval_expr(node.condition)
        branch = node.then_branch if self.is_truthy(condition) else node.else_branch

        for child in branch:
            self.eval_node(child)

    def eval_foreach(self, node: ForEach) -> None:
        """
        Evaluate foreach loop.
        Iterates over collection.
        """
        # Get collection
        collection = self.eval_variable(node.iterator, node.iterator_fields)

        if not collection:
            return

        # Ensure collection is iterable
        if isinstance(collection, str):
            collection = [collection]
        elif not hasattr(collection, '__iter__'):
            collection = [collection]

        # Iterate over collection
        for item in collection:
            # Create child environment
            child_env = self.env.child()
            child_env.set(node.iterator, item)

            # Temporarily use child environment
            old_env = self.env
            self.env = child_env

            # Execute body
            for child in node.body:
                self.eval_node(child)

            # Restore environment
            self.env = old_env

    def eval_for(self, node: For) -> None:
        """Evaluate for loop"""
        start_val = self.eval_expr(node.start)
        end_val = self.eval_expr(node.end)

        try:
            start = int(self.stringify(start_val))
            end = int(self.stringify(end_val))
        except (ValueError, TypeError):
            raise InterpretError(f"For loop bounds must be integers", node.loc)

        for i in range(start, end):
            # Create child environment
            child_env = self.env.child()
            child_env.set(node.iterator, i)

            # Temporarily use child environment
            old_env = self.env
            self.env = child_env

            # Execute body
            for child in node.body:
                self.eval_node(child)

            # Restore environment
            self.env = old_env

    def eval_define(self, node: Define) -> None:
        """
        Define function.
        Stores function definition in environment.
        """
        self.functions[node.name] = (node.params, node.body)

        # Execute continuation (code after define)
        for child in node.continuation:
            self.eval_node(child)

    def eval_apply(self, name: str, args: List[Tuple[Optional[str], List[ASTNode]]]) -> Any:
        """
        Apply function.
        Calls user-defined or built-in function.
        """
        # Check for built-in functions
        builtin_result = self.eval_builtin_function(name, args)
        if builtin_result is not None:
            return builtin_result

        # Check for user-defined function
        if name in self.functions:
            params, body = self.functions[name]

            # Create child environment
            child_env = self.env.child()

            # Bind arguments to parameters
            arg_values = []
            for arg_name, arg_nodes in args:
                # Evaluate argument
                if len(arg_nodes) == 1:
                    value = self.eval_expr(arg_nodes[0])
                else:
                    value = ''.join(self.stringify(self.eval_expr(n)) for n in arg_nodes)
                arg_values.append((arg_name, value))

            # Match arguments to parameters
            for i, (param_name, default) in enumerate(params):
                # Find matching argument
                value = None
                for arg_name, arg_value in arg_values:
                    if arg_name == param_name or (arg_name is None and i < len(arg_values)):
                        value = arg_value
                        break

                if value is None and default is not None:
                    value = self.eval_expr(default)

                if value is not None:
                    child_env.set(param_name, value)

            # Execute function body
            old_env = self.env
            self.env = child_env

            results = []
            for child in body:
                # Capture output
                old_buffer = self.output_buffer
                self.output_buffer = []
                self.eval_node(child)
                results.append(''.join(self.output_buffer))
                self.output_buffer = old_buffer

            self.env = old_env
            return ''.join(results)

        # Function not found
        return f"%apply;{name}?"

    def eval_builtin_function(self, name: str, args: List[Tuple[Optional[str], List[ASTNode]]]) -> Optional[Any]:
        """
        Evaluate built-in functions.

        Translates geneweb/lib/templ.ml eval_apply built-in functions.
        """
        # Get argument values
        arg_values = []
        for _, arg_nodes in args:
            if len(arg_nodes) == 1:
                value = self.stringify(self.eval_expr(arg_nodes[0]))
            else:
                value = ''.join(self.stringify(self.eval_expr(n)) for n in arg_nodes)
            arg_values.append(value)

        # String functions
        if name == 'capitalize' and len(arg_values) == 1:
            text = arg_values[0]
            return text[0].upper() + text[1:] if text else text

        elif name == 'capitalize_words' and len(arg_values) == 1:
            return ' '.join(word.capitalize() for word in arg_values[0].split())

        elif name == 'url_encode' or name == 'uri_encode':
            if len(arg_values) == 1:
                from urllib.parse import quote
                return quote(arg_values[0])

        elif name == 'interp' and len(arg_values) == 1:
            # Interpret template string
            ast = parse(arg_values[0])
            return self.interpret(ast)

        elif name == 'nth' and len(arg_values) == 2:
            # Split string and get nth field
            parts = arg_values[0].split('/')
            try:
                idx = int(arg_values[1])
                return parts[idx] if 0 <= idx < len(parts) else ''
            except (ValueError, IndexError):
                return ''

        # Math functions
        elif name == '1000sep' and len(arg_values) == 1:
            try:
                num = int(arg_values[0])
                return f"{num:,}"
            except ValueError:
                return arg_values[0]

        return None

    def eval_let(self, node: Let) -> None:
        """Evaluate let binding"""
        # Evaluate value
        if len(node.value) == 1:
            value = self.eval_expr(node.value[0])
        else:
            # Concatenate multiple nodes
            parts = []
            for child in node.value:
                old_buffer = self.output_buffer
                self.output_buffer = []
                self.eval_node(child)
                parts.append(''.join(self.output_buffer))
                self.output_buffer = old_buffer
            value = ''.join(parts)

        # Bind variable
        self.env.set(node.var_name, value)

        # Evaluate body
        for child in node.body:
            self.eval_node(child)

    def eval_include(self, node: Include) -> None:
        """
        Evaluate include statement.

        Note: In production, this would load and parse template files.
        For now, we just output a placeholder.
        """
        if node.is_file:
            # Would load file and parse/interpret it
            # For now, just output comment
            self.write(f"<!-- include: {node.source} -->")
        else:
            # Raw include - interpret directly
            if isinstance(node.source, str):
                ast = parse(node.source)
                for child in ast:
                    self.eval_node(child)

    def eval_op1(self, operator: str, operand: ASTNode) -> Any:
        """Evaluate unary operation"""
        value = self.eval_expr(operand)

        if operator == 'not':
            return not self.is_truthy(value)

        raise InterpretError(f"Unknown unary operator: {operator}", operand.loc)

    def eval_op2(self, operator: str, left: ASTNode, right: ASTNode) -> Any:
        """Evaluate binary operation"""
        left_val = self.eval_expr(left)
        right_val = self.eval_expr(right)

        # Logical operators
        if operator == 'and':
            return self.is_truthy(left_val) and self.is_truthy(right_val)
        elif operator == 'or':
            return self.is_truthy(left_val) or self.is_truthy(right_val)

        # String operators
        elif operator == 'in' or operator == 'is_substr':
            left_str = self.stringify(left_val)
            right_str = self.stringify(right_val)
            return left_str in right_str

        # Comparison operators
        elif operator == '=':
            return left_val == right_val
        elif operator == '!=':
            return left_val != right_val
        elif operator == '<':
            return self.to_number(left_val) < self.to_number(right_val)
        elif operator == '>':
            return self.to_number(left_val) > self.to_number(right_val)
        elif operator == '<=':
            return self.to_number(left_val) <= self.to_number(right_val)
        elif operator == '>=':
            return self.to_number(left_val) >= self.to_number(right_val)

        # Arithmetic operators
        elif operator == '+':
            return self.to_number(left_val) + self.to_number(right_val)
        elif operator == '-':
            return self.to_number(left_val) - self.to_number(right_val)
        elif operator == '*':
            return self.to_number(left_val) * self.to_number(right_val)
        elif operator == '/' or operator == '|':
            right_num = self.to_number(right_val)
            if right_num == 0:
                raise InterpretError("Division by zero", right.loc)
            return self.to_number(left_val) // right_num
        elif operator == '/.':
            right_num = self.to_number(right_val)
            if right_num == 0:
                raise InterpretError("Division by zero", right.loc)
            return self.to_number(left_val) / right_num
        elif operator == '%':
            right_num = self.to_number(right_val)
            if right_num == 0:
                raise InterpretError("Modulo by zero", right.loc)
            return self.to_number(left_val) % right_num
        elif operator == '^':
            return self.to_number(left_val) ** self.to_number(right_val)

        raise InterpretError(f"Unknown binary operator: {operator}", left.loc)

    def is_truthy(self, value: Any) -> bool:
        """Check if value is truthy"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value != '' and value != '0'
        if value is None:
            return False
        return True

    def to_number(self, value: Any) -> Union[int, float]:
        """Convert value to number"""
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                return 0
        return 0

    def stringify(self, value: Any) -> str:
        """Convert value to string"""
        if isinstance(value, bool):
            return '1' if value else '0'
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return value
        if value is None:
            return ''
        return str(value)


def interpret(ast: List[ASTNode], config: RequestConfig) -> str:
    """
    Convenience function to interpret template AST.

    Args:
        ast: Template AST
        config: Request configuration

    Returns:
        Generated HTML/text output
    """
    interpreter = TemplateInterpreter(config)
    return interpreter.interpret(ast)


def render_template(source: str, config: RequestConfig, filename: str = "<template>") -> str:
    """
    Convenience function to parse and render template.

    Args:
        source: Template source code
        config: Request configuration
        filename: Source filename for error messages

    Returns:
        Generated HTML/text output
    """
    ast = parse(source, filename)
    return interpret(ast, config)
