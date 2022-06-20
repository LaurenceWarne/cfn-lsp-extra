"""
Integration tests for completions
"""

import pytest


# See
# https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules
pytestmark = pytest.mark.integration


def test_integration():
    assert 1 == 2


def test_integration():
    assert 1 == 2
