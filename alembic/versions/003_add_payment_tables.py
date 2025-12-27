"""Add payment tables

Revision ID: 003_add_payment_tables
Revises: 002_add_analytics_tables
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_payment_tables'
down_revision = '002_add_analytics_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Create payment_gateways table
    op.create_table('payment_gateways',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('test_mode', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indexes for payment_gateways table
    op.create_index('ix_payment_gateways_name', 'payment_gateways', ['name'], unique=True)
    op.create_index('ix_payment_gateways_type', 'payment_gateways', ['type'])
    op.create_index('ix_payment_gateways_status', 'payment_gateways', ['status'])
    
    # Create payment_methods table
    op.create_table('payment_methods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gateway_id', sa.Integer(), nullable=False),
        sa.Column('method_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('icon', sa.String(length=500), nullable=True),
        sa.Column('min_amount', sa.Float(), nullable=True),
        sa.Column('max_amount', sa.Float(), nullable=True),
        sa.Column('fee_percentage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('fee_fixed', sa.Float(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['gateway_id'], ['payment_gateways.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gateway_id', 'method_code', name='uq_payment_method_gateway_code')
    )
    
    # Create indexes for payment_methods table
    op.create_index('ix_payment_methods_gateway_id', 'payment_methods', ['gateway_id'])
    op.create_index('ix_payment_methods_method_code', 'payment_methods', ['method_code'])
    op.create_index('ix_payment_methods_status', 'payment_methods', ['status'])
    
    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('payment_method_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('payment_details', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_method_id'], ['payment_methods.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number')
    )
    
    # Create indexes for invoices table
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('ix_invoices_user_id', 'invoices', ['user_id'])
    op.create_index('ix_invoices_payment_method_id', 'invoices', ['payment_method_id'])
    op.create_index('ix_invoices_status', 'invoices', ['status'])
    op.create_index('ix_invoices_created_at', 'invoices', ['created_at'])
    
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.String(length=50), nullable=False),
        sa.Column('plan_name', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('interval', sa.String(length=50), nullable=False),
        sa.Column('interval_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('trial_start', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subscription_id')
    )
    
    # Create indexes for subscriptions table
    op.create_index('ix_subscriptions_subscription_id', 'subscriptions', ['subscription_id'], unique=True)
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_plan_id', 'subscriptions', ['plan_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    
    # Create subscription_invoices table
    op.create_table('subscription_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('paid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subscription_id', 'period_start', name='uq_subscription_invoice_period')
    )
    
    # Create indexes for subscription_invoices table
    op.create_index('ix_subscription_invoices_subscription_id', 'subscription_invoices', ['subscription_id'])
    op.create_index('ix_subscription_invoices_invoice_id', 'subscription_invoices', ['invoice_id'])
    op.create_index('ix_subscription_invoices_paid', 'subscription_invoices', ['paid'])
    
    # Create crypto_payments table
    op.create_table('crypto_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column('amount_crypto', sa.Float(), nullable=False),
        sa.Column('amount_usd', sa.Float(), nullable=False),
        sa.Column('exchange_rate', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('confirmations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_confirmations', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('tx_hash', sa.String(length(255)), nullable=True),
        sa.Column('block_height', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_id'),
        sa.UniqueConstraint('address')
    )
    
    # Create indexes for crypto_payments table
    op.create_index('ix_crypto_payments_payment_id', 'crypto_payments', ['payment_id'], unique=True)
    op.create_index('ix_crypto_payments_address', 'crypto_payments', ['address'], unique=True)
    op.create_index('ix_crypto_payments_user_id', 'crypto_payments', ['user_id'])
    op.create_index('ix_crypto_payments_status', 'crypto_payments', ['status'])
    op.create_index('ix_crypto_payments_created_at', 'crypto_payments', ['created_at'])
    
    # Create payment_webhooks table
    op.create_table('payment_webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gateway_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('signature', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['gateway_id'], ['payment_gateways.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for payment_webhooks table
    op.create_index('ix_payment_webhooks_gateway_id', 'payment_webhooks', ['gateway_id'])
    op.create_index('ix_payment_webhooks_event_type', 'payment_webhooks', ['event_type'])
    op.create_index('ix_payment_webhooks_status', 'payment_webhooks', ['status'])
    op.create_index('ix_payment_webhooks_processed', 'payment_webhooks', ['processed'])
    op.create_index('ix_payment_webhooks_created_at', 'payment_webhooks', ['created_at'])
    
    # Create refunds table
    op.create_table('refunds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('refund_id', sa.String(length=100), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('refund_id')
    )
    
    # Create indexes for refunds table
    op.create_index('ix_refunds_refund_id', 'refunds', ['refund_id'], unique=True)
    op.create_index('ix_refunds_transaction_id', 'refunds', ['transaction_id'])
    op.create_index('ix_refunds_status', 'refunds', ['status'])
    
    # Add columns to existing transactions table
    op.add_column('transactions', sa.Column('invoice_id', sa.Integer(), nullable=True))
    op.add_column('transactions', sa.Column('subscription_id', sa.Integer(), nullable=True))
    op.add_column('transactions', sa.Column('crypto_payment_id', sa.Integer(), nullable=True))
    
    # Create foreign keys for transactions table
    op.create_foreign_key('fk_transactions_invoice_id', 'transactions', 'invoices', ['invoice_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_transactions_subscription_id', 'transactions', 'subscriptions', ['subscription_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_transactions_crypto_payment_id', 'transactions', 'crypto_payments', ['crypto_payment_id'], ['id'], ondelete='SET NULL')
    
    # Create indexes for new columns
    op.create_index('ix_transactions_invoice_id', 'transactions', ['invoice_id'])
    op.create_index('ix_transactions_subscription_id', 'transactions', ['subscription_id'])
    op.create_index('ix_transactions_crypto_payment_id', 'transactions', ['crypto_payment_id'])
    
    # Insert initial payment gateways
    op.bulk_insert('payment_gateways',
        [
            {
                'name': 'Crypto Gateway',
                'type': 'crypto',
                'status': 'active',
                'config': {
                    'currencies': ['BTC', 'ETH', 'USDT', 'LTC'],
                    'network_fee': 0.0005,
                    'confirmations': {
                        'BTC': 3,
                        'ETH': 12,
                        'USDT': 12,
                        'LTC': 6
                    },
                    'exchange_rate_provider': 'coingecko',
                    'update_interval': 60
                },
                'test_mode': False,
                'success_rate': 98.5
            },
            {
                'name': 'PayPal Gateway',
                'type': 'paypal',
                'status': 'active',
                'config': {
                    'client_id': 'your_client_id',
                    'client_secret': 'your_client_secret',
                    'environment': 'sandbox',
                    'webhook_url': 'https://yourdomain.com/paypal/webhook'
                },
                'test_mode': True,
                'success_rate': 99.2
            },
            {
                'name': 'Stripe Gateway',
                'type': 'stripe',
                'status': 'active',
                'config': {
                    'publishable_key': 'your_publishable_key',
                    'secret_key': 'your_secret_key',
                    'webhook_secret': 'your_webhook_secret'
                },
                'test_mode': True,
                'success_rate': 99.5
            }
        ]
    )
    
    # Insert payment methods
    op.execute("""
        INSERT INTO payment_methods (gateway_id, method_code, name, description, fee_percentage, fee_fixed, sort_order)
        VALUES 
        ((SELECT id FROM payment_gateways WHERE name = 'Crypto Gateway'), 'BTC', 'Bitcoin', 'Pay with Bitcoin', 0.5, 0, 1),
        ((SELECT id FROM payment_gateways WHERE name = 'Crypto Gateway'), 'ETH', 'Ethereum', 'Pay with Ethereum', 0.5, 0, 2),
        ((SELECT id FROM payment_gateways WHERE name = 'Crypto Gateway'), 'USDT', 'Tether (USDT)', 'Pay with USDT', 0.5, 0, 3),
        ((SELECT id FROM payment_gateways WHERE name = 'Crypto Gateway'), 'LTC', 'Litecoin', 'Pay with Litecoin', 0.5, 0, 4),
        ((SELECT id FROM payment_gateways WHERE name = 'PayPal Gateway'), 'PAYPAL', 'PayPal', 'Pay with PayPal', 2.9, 0.30, 5),
        ((SELECT id FROM payment_gateways WHERE name = 'Stripe Gateway'), 'CARD', 'Credit/Debit Card', 'Pay with Card', 2.9, 0.30, 6)
    """)
    
    # Update settings with payment configuration
    op.execute("""
        INSERT INTO settings (key, value, description)
        VALUES 
        ('payment_config', 
         '{
            "default_currency": "USD",
            "allowed_currencies": ["USD", "EUR", "GBP"],
            "min_deposit_amount": 5.00,
            "max_deposit_amount": 10000.00,
            "auto_approve_payments": true,
            "payment_timeout_minutes": 30,
            "refund_policy_days": 7,
            "enable_subscriptions": true
         }',
         'Payment system configuration'),
         
        ('subscription_plans',
         '[
            {
                "id": "basic",
                "name": "Basic Plan",
                "description": "Perfect for beginners",
                "price": 9.99,
                "currency": "USD",
                "interval": "month",
                "features": ["1000 views/month", "Standard speed", "Email support"],
                "sort_order": 1
            },
            {
                "id": "pro",
                "name": "Pro Plan",
                "description": "For serious creators",
                "price": 29.99,
                "currency": "USD",
                "interval": "month",
                "features": ["10000 views/month", "High speed", "Priority support", "Analytics"],
                "sort_order": 2
            },
            {
                "id": "business",
                "name": "Business Plan",
                "description": "For agencies and businesses",
                "price": 99.99,
                "currency": "USD",
                "interval": "month",
                "features": ["Unlimited views", "Maximum speed", "24/7 support", "Advanced analytics", "API access"],
                "sort_order": 3
            }
         ]',
         'Subscription plans')
    """)

def downgrade():
    # Remove foreign keys from transactions table
    op.drop_constraint('fk_transactions_crypto_payment_id', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_transactions_subscription_id', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_transactions_invoice_id', 'transactions', type_='foreignkey')
    
    # Drop indexes from transactions table
    op.drop_index('ix_transactions_crypto_payment_id', table_name='transactions')
    op.drop_index('ix_transactions_subscription_id', table_name='transactions')
    op.drop_index('ix_transactions_invoice_id', table_name='transactions')
    
    # Remove columns from transactions table
    op.drop_column('transactions', 'crypto_payment_id')
    op.drop_column('transactions', 'subscription_id')
    op.drop_column('transactions', 'invoice_id')
    
    # Drop new tables
    op.drop_table('refunds')
    op.drop_table('payment_webhooks')
    op.drop_table('crypto_payments')
    op.drop_table('subscription_invoices')
    op.drop_table('subscriptions')
    op.drop_table('invoices')
    op.drop_table('payment_methods')
    op.drop_table('payment_gateways')
    
    # Remove payment configuration settings
    op.execute("DELETE FROM settings WHERE key IN ('payment_config', 'subscription_plans')")