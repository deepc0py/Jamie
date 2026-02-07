"""Pytest configuration for Jamie tests."""

import sys
from unittest.mock import MagicMock

# Mock CUA dependencies that aren't available during testing
# These are only needed at runtime when actually running the agent
sys.modules['computer'] = MagicMock()
sys.modules['agent'] = MagicMock()
