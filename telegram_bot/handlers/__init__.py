"""
Telegram Bot Handlers Package
Initialization file for all bot handlers
"""

from .commands import *
from .callbacks import *
from .inline import *
from .payments import *

__all__ = [
    'register_commands',
    'register_callbacks',
    'register_inline',
    'register_payments'
]