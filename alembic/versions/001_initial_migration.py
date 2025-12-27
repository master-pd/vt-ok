"""Initial migration

Revision ID: 001_initial_migration
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True, server_default='en'),
        sa.Column('balance', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_spent', sa.Float(), nullable=False, server_default='0'),
        sa.Column('views_bought', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('registered_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    
    # Create indexes for users table
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('video_id', sa.String(length=100), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('view_count_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('view_count_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    
    # Create indexes for orders table
    op.create_index('ix_orders_order_id', 'orders', ['order_id'], unique=True)
    op.create_index('ix_orders_user_id', 'orders', ['user_id'])
    op.create_index('ix_orders_video_id', 'orders', ['video_id'])
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_payment_status', 'orders', ['payment_status'])
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('balance_before', sa.Float(), nullable=False),
        sa.Column('balance_after', sa.Float(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )
    
    # Create indexes for transactions table
    op.create_index('ix_transactions_transaction_id', 'transactions', ['transaction_id'], unique=True)
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_type', 'transactions', ['type'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])
    
    # Create analytics table
    op.create_table('analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('metric', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'metric', name='uq_analytics_date_metric')
    )
    
    # Create indexes for analytics table
    op.create_index('ix_analytics_date', 'analytics', ['date'])
    op.create_index('ix_analytics_metric', 'analytics', ['metric'])
    
    # Create accounts table for TikTok accounts
    op.create_table('tiktok_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=500), nullable=True),
        sa.Column('session_id', sa.String(length=500), nullable=True),
        sa.Column('cookies', sa.JSON(), nullable=True),
        sa.Column('device_id', sa.String(length=255), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('proxy', sa.String(length=500), nullable=True),
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fail_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cooldown_until', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id')
    )
    
    # Create indexes for tiktok_accounts table
    op.create_index('ix_tiktok_accounts_account_id', 'tiktok_accounts', ['account_id'], unique=True)
    op.create_index('ix_tiktok_accounts_username', 'tiktok_accounts', ['username'])
    op.create_index('ix_tiktok_accounts_banned', 'tiktok_accounts', ['banned'])
    op.create_index('ix_tiktok_accounts_last_used', 'tiktok_accounts', ['last_used'])
    
    # Create proxies table
    op.create_table('proxies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proxy_string', sa.String(length=500), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('latency', sa.Float(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True, server_default='0'),
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fail_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('last_checked', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('proxy_string')
    )
    
    # Create indexes for proxies table
    op.create_index('ix_proxies_proxy_string', 'proxies', ['proxy_string'], unique=True)
    op.create_index('ix_proxies_type', 'proxies', ['type'])
    op.create_index('ix_proxies_country', 'proxies', ['country'])
    op.create_index('ix_proxies_success_rate', 'proxies', ['success_rate'])
    op.create_index('ix_proxies_banned', 'proxies', ['banned'])
    
    # Create view_logs table
    op.create_table('view_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('proxy_id', sa.Integer(), nullable=True),
        sa.Column('method', sa.String(length=100), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('views_sent', sa.Integer(), nullable=False),
        sa.Column('views_delivered', sa.Integer(), nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['tiktok_accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['proxy_id'], ['proxies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for view_logs table
    op.create_index('ix_view_logs_order_id', 'view_logs', ['order_id'])
    op.create_index('ix_view_logs_account_id', 'view_logs', ['account_id'])
    op.create_index('ix_view_logs_proxy_id', 'view_logs', ['proxy_id'])
    op.create_index('ix_view_logs_method', 'view_logs', ['method'])
    op.create_index('ix_view_logs_status', 'view_logs', ['status'])
    op.create_index('ix_view_logs_created_at', 'view_logs', ['created_at'])
    
    # Create system_logs table
    op.create_table('system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(length=50), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=False),
        sa.Column('message', sa.String(length=2000), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for system_logs table
    op.create_index('ix_system_logs_level', 'system_logs', ['level'])
    op.create_index('ix_system_logs_module', 'system_logs', ['module'])
    op.create_index('ix_system_logs_created_at', 'system_logs', ['created_at'])
    
    # Create settings table
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    
    # Create indexes for settings table
    op.create_index('ix_settings_key', 'settings', ['key'], unique=True)
    
    # Insert initial settings
    op.bulk_insert('settings',
        [
            {
                'key': 'view_prices',
                'value': {
                    '100': 0.50,
                    '500': 2.00,
                    '1000': 3.50,
                    '5000': 15.00,
                    '10000': 25.00,
                    '50000': 100.00,
                    '100000': 180.00
                },
                'description': 'Price per view count'
            },
            {
                'key': 'payment_methods',
                'value': ['crypto', 'paypal', 'credit_card'],
                'description': 'Available payment methods'
            },
            {
                'key': 'system_status',
                'value': {'active': True, 'maintenance': False},
                'description': 'System status'
            },
            {
                'key': 'admin_ids',
                'value': [123456789],  # Replace with actual admin Telegram IDs
                'description': 'Admin Telegram IDs'
            }
        ]
    )

def downgrade():
    # Drop tables in reverse order
    op.drop_table('settings')
    op.drop_table('system_logs')
    op.drop_table('view_logs')
    op.drop_table('proxies')
    op.drop_table('tiktok_accounts')
    op.drop_table('analytics')
    op.drop_table('transactions')
    op.drop_table('orders')
    op.drop_table('users')