"""
Database Package Initialization
"""
from .models import (
    Base, User, Order, Transaction, Analytics, TikTokAccount, Proxy,
    ViewLog, SystemLog, Setting, DailyAnalytics, UserAnalytics,
    OrderAnalytics, PerformanceAnalytics, RevenueAnalytics, GeographicAnalytics,
    PaymentGateway, PaymentMethod, Invoice, CryptoPayment, Subscription,
    SubscriptionInvoice, PaymentWebhook, Refund,
    init_database, get_db
)

__all__ = [
    'Base',
    'User',
    'Order',
    'Transaction',
    'Analytics',
    'TikTokAccount',
    'Proxy',
    'ViewLog',
    'SystemLog',
    'Setting',
    'DailyAnalytics',
    'UserAnalytics',
    'OrderAnalytics',
    'PerformanceAnalytics',
    'RevenueAnalytics',
    'GeographicAnalytics',
    'PaymentGateway',
    'PaymentMethod',
    'Invoice',
    'CryptoPayment',
    'Subscription',
    'SubscriptionInvoice',
    'PaymentWebhook',
    'Refund',
    'init_database',
    'get_db'
]

# Initialize database on import
import os
from pathlib import Path

# Create database directory
db_dir = Path("database")
db_dir.mkdir(exist_ok=True)

# Create sessions and analytics directories
(db_dir / "sessions").mkdir(exist_ok=True)
(db_dir / "analytics").mkdir(exist_ok=True)

print("📦 Database package initialized successfully")