"""
Telegram Bot WebApp Package
Web interface for TikTok Views Bot
"""

from .mini_app import app, init_web_app

__all__ = ['app', 'init_web_app']

__version__ = '1.0.0'
__author__ = 'TikTok Views Bot Team'
__description__ = 'Telegram WebApp interface for TikTok Views Bot'

print("🌐 WebApp package initialized")