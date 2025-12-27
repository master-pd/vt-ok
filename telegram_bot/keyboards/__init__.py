"""
Keyboard Package for Telegram Bot
"""

from .main_menu import MainKeyboard
from .admin_panel import AdminKeyboard
from .inline_kb import PaymentKeyboard

__all__ = ['MainKeyboard', 'AdminKeyboard', 'PaymentKeyboard']