"""Debug eval_expr for conditionals"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from frontend.template.interpreter import TemplateInterpreter
from frontend.template.parser import parse
from frontend.template.ast import Variable, If
from frontend.config import create_empty_config

# Setup
config = create_empty_config()
interp = TemplateInterpreter(config)
interp.env.set('is_admin', True)

# Parse the condition
template = "%if;(is_admin)Admin%end;"
ast = parse(template)

print("=== AST ===")
print(f"AST: {ast}")
print(f"Type: {type(ast)}")
if ast:
    print(f"First node: {ast[0]}")
    print(f"First node type: {type(ast[0])}")
    if isinstance(ast[0], If):
        print(f"Condition: {ast[0].condition}")
        print(f"Condition type: {type(ast[0].condition)}")
        print(f"Then branch: {ast[0].then_branch}")
        print(f"Else branch: {ast[0].else_branch}")

# Evaluate the condition
print("\n=== Evaluation ===")
if_node = ast[0]
print(f"Evaluating condition: {if_node.condition}")

# Check if condition is a Variable
if isinstance(if_node.condition, Variable):
    print(f"Condition is Variable with name: {if_node.condition.name}")
    print(f"Fields: {if_node.condition.fields}")

    # Manually evaluate
    value = interp.eval_variable(if_node.condition.name, if_node.condition.fields)
    print(f"Variable value: {value}")
    print(f"Variable type: {type(value)}")
    print(f"is_truthy(value): {interp.is_truthy(value)}")

# Evaluate using eval_expr
expr_result = interp.eval_expr(if_node.condition)
print(f"\neval_expr result: {expr_result}")
print(f"eval_expr result type: {type(expr_result)}")
print(f"is_truthy(expr_result): {interp.is_truthy(expr_result)}")

# Full interpretation
print("\n=== Full Interpretation ===")
result = interp.interpret(ast)
print(f"Final result: '{result}'")
