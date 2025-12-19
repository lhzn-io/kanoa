"""
kanoa: AI-powered interpretation of data science outputs.
"""

__version__ = "0.4.1"

from .config import options
from .core.interpreter import AnalyticsInterpreter, supported_backends
from .core.types import InterpretationResult, UsageInfo

# Re-export for convenient access
backends = supported_backends
