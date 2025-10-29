"""Simple test to debug conditional rendering"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from frontend.template.interpreter import TemplateInterpreter
from frontend.template.parser import parse
from frontend.config import create_empty_config

# Test 1: Simple variable
print("=== Test 1: Simple Variable ===")
template1 = "%name;"
config = create_empty_config()
interp = TemplateInterpreter(config)
interp.env.set('name', 'Alice')
ast = parse(template1)
result = interp.interpret(ast)
print(f"Template: {template1}")
print(f"Result: '{result}'")
print(f"Expected: 'Alice'")
print(f"Pass: {result == 'Alice'}")
print()

# Test 2: Simple conditional with True
print("=== Test 2: Conditional with True ===")
template2 = "%if;(is_admin)Admin%end;"
interp2 = TemplateInterpreter(config)
interp2.env.set('is_admin', True)
ast2 = parse(template2)
result2 = interp2.interpret(ast2)
print(f"Template: {template2}")
print(f"is_admin = {interp2.env.get('is_admin')}")
print(f"Result: '{result2}'")
print(f"Expected: 'Admin'")
print(f"Pass: {result2 == 'Admin'}")
print()

# Test 3: Simple conditional with False
print("=== Test 3: Conditional with False ===")
template3 = "%if;(is_admin)Admin%end;"
interp3 = TemplateInterpreter(config)
interp3.env.set('is_admin', False)
ast3 = parse(template3)
result3 = interp3.interpret(ast3)
print(f"Template: {template3}")
print(f"is_admin = {interp3.env.get('is_admin')}")
print(f"Result: '{result3}'")
print(f"Expected: ''")
print(f"Pass: {result3 == ''}")
print()

# Test 4: Variable and conditional together
print("=== Test 4: Variable + Conditional ===")
template4 = "<p>%name;</p>%if;(is_admin)<p>Admin</p>%end;"
interp4 = TemplateInterpreter(config)
interp4.env.set('name', 'Bob')
interp4.env.set('is_admin', True)
ast4 = parse(template4)
result4 = interp4.interpret(ast4)
print(f"Template: {template4}")
print(f"name = {interp4.env.get('name')}")
print(f"is_admin = {interp4.env.get('is_admin')}")
print(f"Result: '{result4}'")
print(f"Expected: '<p>Bob</p><p>Admin</p>'")
print(f"Pass: {result4 == '<p>Bob</p><p>Admin</p>'}")
