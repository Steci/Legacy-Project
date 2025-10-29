"""
Abstract Syntax Tree for template language.

Translates geneweb/lib/templ/ast.ml
Defines the structure of parsed templates.
"""

from dataclasses import dataclass
from typing import List, Optional, Union, Tuple
from abc import ABC, abstractmethod


@dataclass
class Location:
    """Source location for error reporting"""
    filename: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.filename}:{self.line}:{self.column}"


class ASTNode(ABC):
    """Base class for all AST nodes"""

    def __init__(self, loc: Optional[Location] = None):
        self.loc = loc or Location("", 0, 0)

    @abstractmethod
    def __eq__(self, other) -> bool:
        """Check equality of AST nodes"""
        pass

    @abstractmethod
    def __repr__(self) -> str:
        """String representation for debugging"""
        pass


@dataclass
class Text(ASTNode):
    """Plain text content - Atext"""
    content: str

    def __eq__(self, other) -> bool:
        return isinstance(other, Text) and self.content == other.content

    def __repr__(self) -> str:
        return f"Text({self.content!r})"


@dataclass
class Variable(ASTNode):
    """Variable reference - Avar"""
    name: str
    fields: List[str]

    def __eq__(self, other) -> bool:
        return (isinstance(other, Variable) and
                self.name == other.name and
                self.fields == other.fields)

    def __repr__(self) -> str:
        fields_str = "." + ".".join(self.fields) if self.fields else ""
        return f"Variable({self.name}{fields_str})"


@dataclass
class Translation(ASTNode):
    """Translation/localization - Atransl"""
    capitalize: bool
    key: str
    choice: str  # For plural/gender choices (0, 1, 2, n, s, w, f, c, e, t)

    def __eq__(self, other) -> bool:
        return (isinstance(other, Translation) and
                self.capitalize == other.capitalize and
                self.key == other.key and
                self.choice == other.choice)

    def __repr__(self) -> str:
        cap = "^" if self.capitalize else ""
        choice = self.choice if self.choice else ""
        return f"Translation({cap}[*{self.key}]{choice})"


@dataclass
class WidthHeight(ASTNode):
    """Image width/height attribute - Awid_hei"""
    filename: str

    def __eq__(self, other) -> bool:
        return isinstance(other, WidthHeight) and self.filename == other.filename

    def __repr__(self) -> str:
        return f"WidthHeight({self.filename})"


@dataclass
class If(ASTNode):
    """Conditional - Aif"""
    condition: ASTNode
    then_branch: List[ASTNode]
    else_branch: List[ASTNode]

    def __eq__(self, other) -> bool:
        return (isinstance(other, If) and
                self.condition == other.condition and
                self.then_branch == other.then_branch and
                self.else_branch == other.else_branch)

    def __repr__(self) -> str:
        return f"If({self.condition}, then={len(self.then_branch)}, else={len(self.else_branch)})"


@dataclass
class ForEach(ASTNode):
    """Iteration over collection - Aforeach"""
    iterator: str
    iterator_fields: List[str]
    loop_params: List[List[ASTNode]]  # Parameters for each iteration
    body: List[ASTNode]

    def __eq__(self, other) -> bool:
        return (isinstance(other, ForEach) and
                self.iterator == other.iterator and
                self.iterator_fields == other.iterator_fields and
                self.loop_params == other.loop_params and
                self.body == other.body)

    def __repr__(self) -> str:
        iter_str = f"{self.iterator}." + ".".join(self.iterator_fields) if self.iterator_fields else self.iterator
        return f"ForEach({iter_str}, body={len(self.body)})"


@dataclass
class For(ASTNode):
    """Range loop - Afor"""
    iterator: str
    start: ASTNode
    end: ASTNode
    body: List[ASTNode]

    def __eq__(self, other) -> bool:
        return (isinstance(other, For) and
                self.iterator == other.iterator and
                self.start == other.start and
                self.end == other.end and
                self.body == other.body)

    def __repr__(self) -> str:
        return f"For({self.iterator}, {self.start} to {self.end}, body={len(self.body)})"


@dataclass
class Define(ASTNode):
    """Function definition - Adefine"""
    name: str
    params: List[Tuple[str, Optional[ASTNode]]]  # (param_name, default_value)
    body: List[ASTNode]
    continuation: List[ASTNode]  # Code after the definition

    def __eq__(self, other) -> bool:
        return (isinstance(other, Define) and
                self.name == other.name and
                self.params == other.params and
                self.body == other.body and
                self.continuation == other.continuation)

    def __repr__(self) -> str:
        params_str = ", ".join(f"{name}" for name, _ in self.params)
        return f"Define({self.name}({params_str}), body={len(self.body)})"


@dataclass
class Apply(ASTNode):
    """Function application - Aapply"""
    name: str
    args: List[Tuple[Optional[str], List[ASTNode]]]  # (arg_name, arg_value_nodes)

    def __eq__(self, other) -> bool:
        return (isinstance(other, Apply) and
                self.name == other.name and
                self.args == other.args)

    def __repr__(self) -> str:
        args_str = ", ".join(
            f"{name}={len(nodes)}" if name else f"pos={len(nodes)}"
            for name, nodes in self.args
        )
        return f"Apply({self.name}({args_str}))"


@dataclass
class Let(ASTNode):
    """Variable binding - Alet"""
    var_name: str
    value: List[ASTNode]
    body: List[ASTNode]

    def __eq__(self, other) -> bool:
        return (isinstance(other, Let) and
                self.var_name == other.var_name and
                self.value == other.value and
                self.body == other.body)

    def __repr__(self) -> str:
        return f"Let({self.var_name} = ..., body={len(self.body)})"


@dataclass
class Op1(ASTNode):
    """Unary operation - Aop1"""
    operator: str  # "not", etc.
    operand: ASTNode

    def __eq__(self, other) -> bool:
        return (isinstance(other, Op1) and
                self.operator == other.operator and
                self.operand == other.operand)

    def __repr__(self) -> str:
        return f"Op1({self.operator} {self.operand})"


@dataclass
class Op2(ASTNode):
    """Binary operation - Aop2"""
    operator: str  # "and", "or", "=", "<", ">", "!=", "<=", ">=", "+", "-", "*", "/", etc.
    left: ASTNode
    right: ASTNode

    def __eq__(self, other) -> bool:
        return (isinstance(other, Op2) and
                self.operator == other.operator and
                self.left == other.left and
                self.right == other.right)

    def __repr__(self) -> str:
        return f"Op2({self.left} {self.operator} {self.right})"


@dataclass
class Integer(ASTNode):
    """Integer literal - Aint"""
    value: str  # Keep as string to preserve representation

    def __eq__(self, other) -> bool:
        return isinstance(other, Integer) and self.value == other.value

    def __repr__(self) -> str:
        return f"Integer({self.value})"

    @property
    def int_value(self) -> int:
        """Get integer value"""
        return int(self.value)


@dataclass
class Include(ASTNode):
    """Include another template - Ainclude"""
    source: Union[str, List[ASTNode]]  # File path or raw content
    is_file: bool  # True for file, False for raw

    def __eq__(self, other) -> bool:
        return (isinstance(other, Include) and
                self.source == other.source and
                self.is_file == other.is_file)

    def __repr__(self) -> str:
        src_type = "file" if self.is_file else "raw"
        return f"Include({src_type}: {self.source})"


@dataclass
class Pack(ASTNode):
    """Packed sequence of nodes - Apack"""
    nodes: List[ASTNode]

    def __eq__(self, other) -> bool:
        return isinstance(other, Pack) and self.nodes == other.nodes

    def __repr__(self) -> str:
        return f"Pack({len(self.nodes)} nodes)"


def make_text(content: str, loc: Optional[Location] = None) -> Text:
    """Create a Text node"""
    node = Text(content)
    if loc:
        node.loc = loc
    return node


def make_variable(name: str, fields: List[str], loc: Optional[Location] = None) -> Variable:
    """Create a Variable node"""
    node = Variable(name, fields)
    if loc:
        node.loc = loc
    return node


def make_if(condition: ASTNode, then_branch: List[ASTNode],
            else_branch: List[ASTNode], loc: Optional[Location] = None) -> If:
    """Create an If node"""
    node = If(condition, then_branch, else_branch)
    if loc:
        node.loc = loc
    return node


def make_op2(operator: str, left: ASTNode, right: ASTNode,
             loc: Optional[Location] = None) -> Op2:
    """Create an Op2 node"""
    node = Op2(operator, left, right)
    if loc:
        node.loc = loc
    return node


def make_integer(value: str, loc: Optional[Location] = None) -> Integer:
    """Create an Integer node"""
    node = Integer(value)
    if loc:
        node.loc = loc
    return node
