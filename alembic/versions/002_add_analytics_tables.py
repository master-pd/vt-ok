"""Add analytics tables

Revision ID: 002_add_analytics_tables
Revises: 001_initial_migration
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_analytics_tables'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Create daily_analytics table
    op.create_table('daily_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pending_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_views_ordered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_views_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_revenue', sa.Float(), nullable=False, server_default='0'),
        sa.Column('average_order_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('conversion_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    
    # Create indexes for daily_analytics table
    op.create_index('ix_daily_analytics_date', 'daily_analytics', ['date'], unique=True)
    
    # Create user_analytics table
    op.create_table('user_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('orders_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('views_ordered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('views_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_spent', sa.Float(), nullable=False, server_default='0'),
        sa.Column('sessions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_session_duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_user_analytics_user_date')
    )
    
    # Create indexes for user_analytics table
    op.create_index('ix_user_analytics_user_id', 'user_analytics', ['user_id'])
    op.create_index('ix_user_analytics_date', 'user_analytics', ['date'])
    
    # Create order_analytics table
    op.create_table('order_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('views_sent_per_hour', sa.JSON(), nullable=True),
        sa.Column('delivery_timeline', sa.JSON(), nullable=True),
        sa.Column('success_rates', sa.JSON(), nullable=True),
        sa.Column('methods_used', sa.JSON(), nullable=True),
        sa.Column('peak_delivery_time', sa.DateTime(), nullable=True),
        sa.Column('average_delivery_speed', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    
    # Create indexes for order_analytics table
    op.create_index('ix_order_analytics_order_id', 'order_analytics', ['order_id'], unique=True)
    
    # Create performance_analytics table
    op.create_table('performance_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=False),
        sa.Column('method', sa.String(length=100), nullable=False),
        sa.Column('views_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('views_successful', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('average_speed', sa.Float(), nullable=False, server_default='0'),
        sa.Column('accounts_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('proxies_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'hour', 'method', name='uq_performance_date_hour_method')
    )
    
    # Create indexes for performance_analytics table
    op.create_index('ix_performance_analytics_date', 'performance_analytics', ['date'])
    op.create_index('ix_performance_analytics_method', 'performance_analytics', ['method'])
    
    # Create revenue_analytics table
    op.create_table('revenue_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('transactions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('average_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'payment_method', name='uq_revenue_date_payment_method')
    )
    
    # Create indexes for revenue_analytics table
    op.create_index('ix_revenue_analytics_date', 'revenue_analytics', ['date'])
    op.create_index('ix_revenue_analytics_payment_method', 'revenue_analytics', ['payment_method'])
    
    # Create geographic_analytics table
    op.create_table('geographic_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('users_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('orders_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('views_ordered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('revenue', sa.Float(), nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'country', name='uq_geographic_date_country')
    )
    
    # Create indexes for geographic_analytics table
    op.create_index('ix_geographic_analytics_date', 'geographic_analytics', ['date'])
    op.create_index('ix_geographic_analytics_country', 'geographic_analytics', ['country'])
    
    # Add columns to existing analytics table
    op.add_column('analytics', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('analytics', sa.Column('subcategory', sa.String(length=100), nullable=True))
    
    # Update indexes for analytics table
    op.drop_index('uq_analytics_date_metric', table_name='analytics')
    op.create_index('ix_analytics_category', 'analytics', ['category'])
    op.create_index('ix_analytics_subcategory', 'analytics', ['subcategory'])
    op.create_index('uq_analytics_date_metric_category', 'analytics', ['date', 'metric', 'category'], unique=True)
    
    # Insert initial analytics data
    op.execute("""
        INSERT INTO settings (key, value, description)
        VALUES ('analytics_config', 
                '{
                    "retention_days": 365,
                    "auto_generate_reports": true,
                    "report_frequency": "daily",
                    "track_user_behavior": true,
                    "track_performance": true,
                    "track_revenue": true,
                    "track_geographic": true
                }',
                'Analytics configuration')
    """)

def downgrade():
    # Drop new tables
    op.drop_table('geographic_analytics')
    op.drop_table('revenue_analytics')
    op.drop_table('performance_analytics')
    op.drop_table('order_analytics')
    op.drop_table('user_analytics')
    op.drop_table('daily_analytics')
    
    # Remove added columns from analytics table
    op.drop_index('uq_analytics_date_metric_category', table_name='analytics')
    op.drop_index('ix_analytics_subcategory', table_name='analytics')
    op.drop_index('ix_analytics_category', table_name='analytics')
    op.drop_column('analytics', 'subcategory')
    op.drop_column('analytics', 'category')
    
    # Restore original index
    op.create_index('uq_analytics_date_metric', 'analytics', ['date', 'metric'], unique=True)
    
    # Remove analytics config setting
    op.execute("DELETE FROM settings WHERE key = 'analytics_config'")