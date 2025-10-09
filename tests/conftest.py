"""
Pytest configuration for deterministic testing.
"""

import pytest
import random
import numpy as np


@pytest.fixture(autouse=True)
def set_deterministic_seeds():
    """Automatically set deterministic seeds for all tests."""
    random.seed(0)
    np.random.seed(0)
    yield
    # Cleanup after test if needed

