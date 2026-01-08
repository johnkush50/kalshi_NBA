"""
Trading Strategies Module.

Contains all trading strategy implementations.
"""

from backend.strategies.base import BaseStrategy
from backend.strategies.sharp_line import SharpLineStrategy

__all__ = [
    "BaseStrategy",
    "SharpLineStrategy",
]
