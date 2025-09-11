#import pytest
from consang.relationship import consang_of

def test_consang_of_with_consang_key():
    person = {"consang": 25}
    assert consang_of(person) == 0.25
