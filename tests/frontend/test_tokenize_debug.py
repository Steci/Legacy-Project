"""Debug tokenization"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from frontend.template.lexer import tokenize

template = "%if;(is_admin)Admin%end;"

print(f"Template: {template}")
print("\n=== Tokens ===")
tokens = tokenize(template)
for i, token in enumerate(tokens):
    print(f"{i}: {token.type.name:15} | value='{token.value}' | loc={token.line}:{token.column}")
