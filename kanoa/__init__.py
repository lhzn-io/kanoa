"""
kanoa: AI-powered interpretation of data science outputs.
"""

__version__ = "0.1.0"

from .config import options
from .core.interpreter import AnalyticsInterpreter
from .core.types import InterpretationResult, UsageInfo
