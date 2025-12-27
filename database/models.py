from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, Text, ForeignKey, Date, Time, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language = Column(String(10), default='en')
    balance = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    views_bought = Column(Integer, default=0)
    role = Column(String(50), default='user')
    status = Column(String(50), default='active')
    registered_at = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    video_url = Column(String(500), nullable=False)
    video_id = Column(String(100))
    view_count = Column(Integer, nullable=False)
    view_count_sent = Column(Integer, default=0)
    view_count_delivered = Column(Integer, default=0)
    status = Column(String(50), default='pending')
    price = Column(Float, nullable=False)
    payment_method = Column(String(50))
    payment_status = Column(String(50), default='pending')
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders")
    view_logs = relationship("ViewLog", back_populates="order", cascade="all, delete-orphan")
    order_analytics = relationship("OrderAnalytics", back_populates="order", uselist=False, cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    description = Column(String(500))
    status = Column(String(50), default='pending')
    payment_method = Column(String(50))
    payment_details = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    invoice = relationship("Invoice", back_populates="transaction", uselist=False)
    crypto_payment = relationship("CryptoPayment", back_populates="transaction", uselist=False)

class Analytics(Base):
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    metric = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    data = Column(JSON)
    category = Column(String(100))
    subcategory = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        (sa.UniqueConstraint('date', 'metric', 'category', name='uq_analytics_date_metric_category')),
    )

class TikTokAccount(Base):
    __tablename__ = 'tiktok_accounts'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(255))
    email = Column(String(255))
    password = Column(String(500))
    session_id = Column(String(500))
    cookies = Column(JSON)
    device_id = Column(String(255))
    user_agent = Column(String(500))
    proxy = Column(String(500))
    use_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    banned = Column(Boolean, default=False)
    cooldown_until = Column(DateTime)
    last_used = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    view_logs = relationship("ViewLog", back_populates="account")

class Proxy(Base):
    __tablename__ = 'proxies'
    
    id = Column(Integer, primary_key=True)
    proxy_string = Column(String(500), unique=True, nullable=False)
    type = Column(String(50), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255))
    password = Column(String(255))
    country = Column(String(100))
    city = Column(String(100))
    speed = Column(Float)
    latency = Column(Float)
    success_rate = Column(Float, default=0)
    use_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    banned = Column(Boolean, default=False)
    last_used = Column(DateTime)
    last_checked = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    view_logs = relationship("ViewLog", back_populates="proxy")

class ViewLog(Base):
    __tablename__ = 'view_logs'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('tiktok_accounts.id', ondelete='SET NULL'))
    proxy_id = Column(Integer, ForeignKey('proxies.id', ondelete='SET NULL'))
    method = Column(String(100), nullable=False)
    video_url = Column(String(500), nullable=False)
    views_sent = Column(Integer, nullable=False)
    views_delivered = Column(Integer, nullable=False)
    success_rate = Column(Float, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)
    error_message = Column(String(1000))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="view_logs")
    account = relationship("TikTokAccount", back_populates="view_logs")
    proxy = relationship("Proxy", back_populates="view_logs")

class SystemLog(Base):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(50), nullable=False)
    module = Column(String(100), nullable=False)
    message = Column(String(2000), nullable=False)
    data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

class Setting(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(String(500))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class DailyAnalytics(Base):
    __tablename__ = 'daily_analytics'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    total_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    completed_orders = Column(Integer, default=0)
    pending_orders = Column(Integer, default=0)
    failed_orders = Column(Integer, default=0)
    total_views_ordered = Column(Integer, default=0)
    total_views_delivered = Column(Integer, default=0)
    total_revenue = Column(Float, default=0)
    average_order_value = Column(Float, default=0)
    conversion_rate = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserAnalytics(Base):
    __tablename__ = 'user_analytics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    orders_count = Column(Integer, default=0)
    views_ordered = Column(Integer, default=0)
    views_delivered = Column(Integer, default=0)
    total_spent = Column(Float, default=0)
    sessions_count = Column(Integer, default=0)
    last_session_duration = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        (sa.UniqueConstraint('user_id', 'date', name='uq_user_analytics_user_date')),
    )

class OrderAnalytics(Base):
    __tablename__ = 'order_analytics'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), unique=True, nullable=False)
    views_sent_per_hour = Column(JSON)
    delivery_timeline = Column(JSON)
    success_rates = Column(JSON)
    methods_used = Column(JSON)
    peak_delivery_time = Column(DateTime)
    average_delivery_speed = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_analytics")

class PerformanceAnalytics(Base):
    __tablename__ = 'performance_analytics'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    hour = Column(Integer, nullable=False)
    method = Column(String(100), nullable=False)
    views_attempted = Column(Integer, default=0)
    views_successful = Column(Integer, default=0)
    success_rate = Column(Float, default=0)
    average_speed = Column(Float, default=0)
    accounts_used = Column(Integer, default=0)
    proxies_used = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        (sa.UniqueConstraint('date', 'hour', 'method', name='uq_performance_date_hour_method')),
    )

class RevenueAnalytics(Base):
    __tablename__ = 'revenue_analytics'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    payment_method = Column(String(50), nullable=False)
    transactions_count = Column(Integer, default=0)
    total_amount = Column(Float, default=0)
    average_amount = Column(Float, default=0)
    success_rate = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        (sa.UniqueConstraint('date', 'payment_method', name='uq_revenue_date_payment_method')),
    )

class GeographicAnalytics(Base):
    __tablename__ = 'geographic_analytics'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    country = Column(String(100), nullable=False)
    users_count = Column(Integer, default=0)
    orders_count = Column(Integer, default=0)
    views_ordered = Column(Integer, default=0)
    revenue = Column(Float, default=0)
    success_rate = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        (sa.UniqueConstraint('date', 'country', name='uq_geographic_date_country')),
    )

class PaymentGateway(Base):
    __tablename__ = 'payment_gateways'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(50), default='active')
    config = Column(JSON, nullable=False)
    test_mode = Column(Boolean, default=False)
    success_rate = Column(Float, default=0)
    total_transactions = Column(Integer, default=0)
    total_amount = Column(Float, default=0)
    last_used = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    payment_methods = relationship("PaymentMethod", back_populates="gateway", cascade="all, delete-orphan")

class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    
    id = Column(Integer, primary_key=True)
    gateway_id = Column(Integer, ForeignKey('payment_gateways.id', ondelete='CASCADE'), nullable=False)
    method_code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    icon = Column(String(500))
    min_amount = Column(Float)
    max_amount = Column(Float)
    fee_percentage = Column(Float, default=0)
    fee_fixed = Column(Float, default=0)
    status = Column(String(50), default='active')
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    gateway = relationship("PaymentGateway", back_populates="payment_methods")
    invoices = relationship("Invoice", back_populates="payment_method")
    
    __table_args__ = (
        (sa.UniqueConstraint('gateway_id', 'method_code', name='uq_payment_method_gateway_code')),
    )

class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    description = Column(String(500))
    status = Column(String(50), default='pending')
    due_date = Column(DateTime)
    paid_at = Column(DateTime)
    payment_details = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    payment_method = relationship("PaymentMethod", back_populates="invoices")
    transaction = relationship("Transaction", back_populates="invoice", uselist=False)

class CryptoPayment(Base):
    __tablename__ = 'crypto_payments'
    
    id = Column(Integer, primary_key=True)
    payment_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    currency = Column(String(10), nullable=False)
    address = Column(String(255), unique=True, nullable=False)
    amount_crypto = Column(Float, nullable=False)
    amount_usd = Column(Float, nullable=False)
    exchange_rate = Column(Float, nullable=False)
    status = Column(String(50), default='pending')
    confirmations = Column(Integer, default=0)
    required_confirmations = Column(Integer, default=3)
    tx_hash = Column(String(255))
    block_height = Column(Integer)
    expires_at = Column(DateTime, nullable=False)
    paid_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    transaction = relationship("Transaction", back_populates="crypto_payment", uselist=False)

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_id = Column(String(50), nullable=False)
    plan_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    interval = Column(String(50), nullable=False)
    interval_count = Column(Integer, default=1)
    status = Column(String(50), default='active')
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime)
    ended_at = Column(DateTime)
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    invoices = relationship("SubscriptionInvoice", back_populates="subscription", cascade="all, delete-orphan")

class SubscriptionInvoice(Base):
    __tablename__ = 'subscription_invoices'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    paid = Column(Boolean, default=False)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="invoices")
    invoice = relationship("Invoice")
    
    __table_args__ = (
        (sa.UniqueConstraint('subscription_id', 'period_start', name='uq_subscription_invoice_period')),
    )

class PaymentWebhook(Base):
    __tablename__ = 'payment_webhooks'
    
    id = Column(Integer, primary_key=True)
    gateway_id = Column(Integer, ForeignKey('payment_gateways.id', ondelete='CASCADE'), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    signature = Column(String(500))
    status = Column(String(50), default='pending')
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    error_message = Column(String(1000))
    created_at = Column(DateTime, server_default=func.now())

class Refund(Base):
    __tablename__ = 'refunds'
    
    id = Column(Integer, primary_key=True)
    refund_id = Column(String(100), unique=True, nullable=False)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String(500))
    status = Column(String(50), default='pending')
    processed_at = Column(DateTime)
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Database engine and session
def init_database(db_url=None):
    if db_url is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///database/tiktok_bot.db")
    
    # Create directory if it doesn't exist
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    return Session

# Helper function to get database session
def get_db():
    Session = init_database()
    session = Session()
    try:
        yield session
    finally:
        session.close()