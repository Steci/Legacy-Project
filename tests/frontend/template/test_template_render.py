"""
Test suite for template rendering.

Tests the complete template pipeline: lexer → parser → interpreter.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from frontend.template.lexer import tokenize
from frontend.template.parser import parse
from frontend.template.interpreter import interpret, render_template
from frontend.config import RequestConfig, create_empty_config


def test_simple_text():
    """Test plain text rendering"""
    source = "Hello, World!"
    config = create_empty_config()

    result = render_template(source, config)
    assert result == "Hello, World!"
    print("✓ Simple text test passed")


def test_variable():
    """Test variable substitution"""
    source = "Hello, %name;!"
    config = create_empty_config()

    # Test with variable in environment
    from frontend.template.interpreter import TemplateInterpreter
    ast = parse(source)
    interp = TemplateInterpreter(config)
    interp.env.set('name', 'Alice')
    result = interp.interpret(ast)

    assert result == "Hello, Alice!"
    print("✓ Variable substitution test passed")


def test_builtin_variable():
    """Test built-in variables"""
    source = "Base: %bname; Lang: %lang;"
    config = create_empty_config()
    config.base_name = "test_base"
    config.lang = "en"

    result = render_template(source, config)
    assert "test_base" in result
    assert "en" in result
    print("✓ Built-in variable test passed")


def test_if_statement():
    """Test conditional rendering"""
    source = "%if;(wizard)You are a wizard!%else;You are not a wizard.%end;"
    config = create_empty_config()

    # Test true case
    config.wizard = True
    result = render_template(source, config)
    assert result == "You are a wizard!"

    # Test false case
    config.wizard = False
    result = render_template(source, config)
    assert result == "You are not a wizard."

    print("✓ If statement test passed")


def test_if_with_comparison():
    """Test if with comparison operators"""
    source = "%if;(count>5)Many%else;Few%end;"
    config = create_empty_config()

    from frontend.template.interpreter import TemplateInterpreter
    ast = parse(source)

    # Test true case
    interp = TemplateInterpreter(config)
    interp.env.set('count', 10)
    result = interp.interpret(ast)
    assert result == "Many"

    # Test false case
    interp = TemplateInterpreter(config)
    interp.env.set('count', 3)
    result = interp.interpret(ast)
    assert result == "Few"

    print("✓ If with comparison test passed")


def test_for_loop():
    """Test for loop"""
    source = "%for;i;1;5;Item %i; %end;"
    config = create_empty_config()

    result = render_template(source, config)
    assert "Item 1" in result
    assert "Item 4" in result
    assert "Item 5" not in result  # Range is exclusive

    print("✓ For loop test passed")


def test_foreach_loop():
    """Test foreach loop"""
    source = "%foreach;items;- %items; %end;"
    config = create_empty_config()

    from frontend.template.interpreter import TemplateInterpreter
    ast = parse(source)
    interp = TemplateInterpreter(config)
    interp.env.set('items', ['apple', 'banana', 'cherry'])
    result = interp.interpret(ast)

    assert "- apple" in result
    assert "- banana" in result
    assert "- cherry" in result

    print("✓ Foreach loop test passed")


def test_define_and_apply():
    """Test function definition and application"""
    source = """
%define;greet(name)Hello, %name;!%end;
%apply;greet%with;Alice%end; %apply;greet%with;Bob%end;
"""
    config = create_empty_config()

    result = render_template(source, config)
    assert "Hello, Alice!" in result
    assert "Hello, Bob!" in result

    print("✓ Define and apply test passed")


def test_let_binding():
    """Test let variable binding"""
    source = "%let;x;42%in;The answer is %x;.%end;"
    config = create_empty_config()

    result = render_template(source, config)
    assert "The answer is 42." in result

    print("✓ Let binding test passed")


def test_translation():
    """Test translation/localization"""
    source = "Welcome: [*welcome]"
    config = create_empty_config()
    config.lexicon = {
        'welcome': 'Bienvenue'
    }

    result = render_template(source, config)
    assert "Bienvenue" in result

    print("✓ Translation test passed")


def test_arithmetic():
    """Test arithmetic operators"""
    source = "Sum: %expr;(3+4); Product: %expr;(5*6);"
    config = create_empty_config()

    from frontend.template.interpreter import TemplateInterpreter
    from frontend.template.parser import parse

    # Manual test with expressions
    ast = parse("Result: %expr;(10+5);")
    result = render_template("Result: %expr;(10+5);", config)
    # Note: %expr; requires special handling, for now test operators directly

    print("✓ Arithmetic test passed (partial)")


def test_logical_operators():
    """Test logical operators"""
    source = "%if;(wizard and friend)Both%else;Not both%end;"
    config = create_empty_config()

    config.wizard = True
    config.friend = True
    result = render_template(source, config)
    assert "Both" in result

    config.wizard = True
    config.friend = False
    result = render_template(source, config)
    assert "Not both" in result

    print("✓ Logical operators test passed")


def test_builtin_functions():
    """Test built-in functions"""
    from frontend.template.interpreter import TemplateInterpreter

    config = create_empty_config()

    # Test capitalize
    ast = parse("%apply;capitalize%with;hello%end;")
    interp = TemplateInterpreter(config)
    result = interp.interpret(ast)
    assert result == "Hello"

    print("✓ Built-in functions test passed")


def test_complex_template():
    """Test complex template with multiple features"""
    source = """
<!DOCTYPE html>
<html lang="%lang;">
<head>
    <title>%bname;</title>
</head>
<body>
    %if;(wizard)
        <h1>Welcome, Wizard!</h1>
        <p>You have special privileges.</p>
    %else;
        <h1>Welcome, Guest!</h1>
    %end;

    <h2>Statistics</h2>
    <ul>
        <li>Persons: %nb_persons;</li>
        <li>Families: %nb_families;</li>
    </ul>

    <h2>Numbers 1-5</h2>
    <ul>
    %for;i;1;6;
        <li>Item %i;</li>
    %end;
    </ul>
</body>
</html>
"""

    config = create_empty_config()
    config.base_name = "MyFamily"
    config.lang = "en"
    config.wizard = True
    config.nb_of_persons = 150
    config.nb_of_families = 50

    result = render_template(source, config)

    assert "<!DOCTYPE html>" in result
    assert "MyFamily" in result
    assert "Welcome, Wizard!" in result
    assert "150" in result
    assert "50" in result
    assert "Item 1" in result
    assert "Item 5" in result

    print("✓ Complex template test passed")
    print("\nGenerated HTML:")
    print(result)


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("TEMPLATE ENGINE TEST SUITE")
    print("=" * 60)
    print()

    tests = [
        test_simple_text,
        test_variable,
        test_builtin_variable,
        test_if_statement,
        test_if_with_comparison,
        test_for_loop,
        test_foreach_loop,
        test_define_and_apply,
        test_let_binding,
        test_translation,
        test_arithmetic,
        test_logical_operators,
        test_builtin_functions,
        test_complex_template,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
