"""
Subscription management system
"""
import sqlite3
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import hashlib

class SubscriptionManager:
    def __init__(self, db_path='database/subscriptions.db'):
        self.db_path = db_path
        self._init_database()
        
        # Subscription plans
        self.plans = {
            'basic': {
                'name': 'Basic',
                'price_monthly': 9.99,
                'price_yearly': 99.99,
                'features': ['500 views/day', 'Basic support', '1 method'],
                'limits': {'daily_views': 500, 'methods': 1}
            },
            'pro': {
                'name': 'Pro',
                'price_monthly': 29.99,
                'price_yearly': 299.99,
                'features': ['2000 views/day', 'Priority support', '3 methods', 'AI optimization'],
                'limits': {'daily_views': 2000, 'methods': 3}
            },
            'enterprise': {
                'name': 'Enterprise',
                'price_monthly': 99.99,
                'price_yearly': 999.99,
                'features': ['Unlimited views', '24/7 support', 'All methods', 'Advanced AI', 'API access'],
                'limits': {'daily_views': 10000, 'methods': 10}
            }
        }
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id TEXT PRIMARY KEY,
                user_id TEXT,
                plan_name TEXT,
                billing_cycle TEXT,
                price REAL,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                auto_renew BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                subscription_id TEXT,
                amount REAL,
                currency TEXT DEFAULT 'USD',
                payment_method TEXT,
                transaction_id TEXT,
                status TEXT,
                paid_at TIMESTAMP,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (subscription_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, user_id: str, email: str) -> bool:
        """Create new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (user_id, email) VALUES (?, ?)
            ''', (user_id, email))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def create_subscription(self, user_id: str, plan_name: str, 
                          billing_cycle: str = 'monthly') -> Optional[Dict]:
        """Create new subscription"""
        if plan_name not in self.plans:
            return None
        
        plan = self.plans[plan_name]
        price = plan[f'price_{billing_cycle}']
        subscription_id = hashlib.md5(
            f"{user_id}_{plan_name}_{datetime.now()}".encode()
        ).hexdigest()[:16]
        
        start_date = datetime.now()
        if billing_cycle == 'monthly':
            end_date = start_date + timedelta(days=30)
        else:  # yearly
            end_date = start_date + timedelta(days=365)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO subscriptions 
            (subscription_id, user_id, plan_name, billing_cycle, price, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (subscription_id, user_id, plan_name, billing_cycle, price, 
              start_date.isoformat(), end_date.isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            'subscription_id': subscription_id,
            'plan_name': plan_name,
            'billing_cycle': billing_cycle,
            'price': price,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'features': plan['features'],
            'limits': plan['limits']
        }
    
    def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """Get user's active subscription"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND status = 'active' AND end_date > ?
            ORDER BY start_date DESC LIMIT 1
        ''', (user_id, datetime.now().isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            subscription = dict(row)
            plan_name = subscription['plan_name']
            subscription['plan_details'] = self.plans.get(plan_name, {})
            return subscription
        
        return None
    
    def update_subscription_status(self, subscription_id: str, status: str) -> bool:
        """Update subscription status"""
        valid_statuses = ['active', 'cancelled', 'expired', 'suspended']
        if status not in valid_statuses:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE subscriptions SET status = ? WHERE subscription_id = ?
        ''', (status, subscription_id))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        return affected > 0
    
    def process_payment(self, subscription_id: str, amount: float, 
                       payment_method: str, transaction_id: str) -> bool:
        """Process payment for subscription"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get subscription
        cursor.execute('SELECT * FROM subscriptions WHERE subscription_id = ?', (subscription_id,))
        subscription = cursor.fetchone()
        
        if not subscription:
            conn.close()
            return False
        
        # Record payment
        payment_id = hashlib.md5(
            f"{subscription_id}_{transaction_id}".encode()
        ).hexdigest()[:16]
        
        cursor.execute('''
            INSERT INTO payments 
            (payment_id, subscription_id, amount, payment_method, transaction_id, status, paid_at)
            VALUES (?, ?, ?, ?, ?, 'completed', ?)
        ''', (payment_id, subscription_id, amount, payment_method, 
              transaction_id, datetime.now().isoformat()))
        
        # Update subscription end date
        if subscription[3] == 'monthly':  # billing_cycle
            new_end_date = datetime.fromisoformat(subscription[7]) + timedelta(days=30)
        else:
            new_end_date = datetime.fromisoformat(subscription[7]) + timedelta(days=365)
        
        cursor.execute('''
            UPDATE subscriptions 
            SET end_date = ?, status = 'active'
            WHERE subscription_id = ?
        ''', (new_end_date.isoformat(), subscription_id))
        
        conn.commit()
        conn.close()
        return True
    
    def check_subscription_expiry(self) -> List[Dict]:
        """Check for expiring subscriptions (within 3 days)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        three_days_later = (datetime.now() + timedelta(days=3)).isoformat()
        
        cursor.execute('''
            SELECT s.*, u.email 
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.status = 'active' 
            AND s.end_date <= ?
            AND s.end_date > ?
        ''', (three_days_later, datetime.now().isoformat()))
        
        expiring = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return expiring
    
    def get_subscription_analytics(self, start_date: str, end_date: str) -> Dict:
        """Get subscription analytics for period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total revenue
        cursor.execute('''
            SELECT SUM(amount) FROM payments 
            WHERE paid_at BETWEEN ? AND ? AND status = 'completed'
        ''', (start_date, end_date))
        total_revenue = cursor.fetchone()[0] or 0
        
        # Active subscriptions
        cursor.execute('''
            SELECT COUNT(*) FROM subscriptions 
            WHERE status = 'active' AND end_date > ?
        ''', (datetime.now().isoformat(),))
        active_subs = cursor.fetchone()[0]
        
        # Plan distribution
        cursor.execute('''
            SELECT plan_name, COUNT(*) as count 
            FROM subscriptions 
            WHERE status = 'active'
            GROUP BY plan_name
        ''')
        plan_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # New subscriptions in period
        cursor.execute('''
            SELECT COUNT(*) FROM subscriptions 
            WHERE start_date BETWEEN ? AND ?
        ''', (start_date, end_date))
        new_subs = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'total_revenue': total_revenue,
            'active_subscriptions': active_subs,
            'new_subscriptions': new_subs,
            'plan_distribution': plan_distribution,
            'mrr': self._calculate_mrr(plan_distribution)
        }
    
    def _calculate_mrr(self, plan_distribution: Dict) -> float:
        """Calculate Monthly Recurring Revenue"""
        mrr = 0
        for plan, count in plan_distribution.items():
            if plan in self.plans:
                mrr += self.plans[plan]['price_monthly'] * count
        return mrr
    
    def send_renewal_notifications(self, days_before: int = 3):
        """Send renewal notifications for expiring subscriptions"""
        expiring = self.check_subscription_expiry()
        notifications = []
        
        for sub in expiring:
            user_email = sub['email']
            end_date = datetime.fromisoformat(sub['end_date'])
            days_remaining = (end_date - datetime.now()).days
            
            notification = {
                'user_id': sub['user_id'],
                'email': user_email,
                'subscription_id': sub['subscription_id'],
                'plan_name': sub['plan_name'],
                'end_date': sub['end_date'],
                'days_remaining': days_remaining,
                'message': f"Your {sub['plan_name']} subscription expires in {days_remaining} days",
                'renewal_url': f"https://example.com/renew/{sub['subscription_id']}"
            }
            notifications.append(notification)
        
        return notifications
    
    def cancel_subscription(self, user_id: str, subscription_id: str) -> bool:
        """Cancel user subscription"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE subscriptions 
            SET status = 'cancelled', auto_renew = FALSE 
            WHERE subscription_id = ? AND user_id = ?
        ''', (subscription_id, user_id))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        return affected > 0
    
    def upgrade_subscription(self, user_id: str, new_plan: str) -> Optional[Dict]:
        """Upgrade user subscription"""
        current_sub = self.get_user_subscription(user_id)
        if not current_sub:
            return None
        
        old_plan = current_sub['plan_name']
        if old_plan == new_plan:
            return {'message': 'Already on this plan'}
        
        # Calculate prorated credit
        days_used = (datetime.now() - datetime.fromisoformat(current_sub['start_date'])).days
        total_days = 30 if current_sub['billing_cycle'] == 'monthly' else 365
        unused_percentage = 1 - (days_used / total_days)
        credit = current_sub['price'] * unused_percentage
        
        # Create new subscription
        new_sub = self.create_subscription(user_id, new_plan, current_sub['billing_cycle'])
        if not new_sub:
            return None
        
        # Cancel old subscription
        self.update_subscription_status(current_sub['subscription_id'], 'cancelled')
        
        return {
            'old_subscription': current_sub['subscription_id'],
            'new_subscription': new_sub['subscription_id'],
            'upgraded_from': old_plan,
            'upgraded_to': new_plan,
            'credit_applied': credit,
            'amount_due': new_sub['price'] - credit,
            'effective_date': datetime.now().isoformat()
        }
    
    def export_subscription_data(self, format: str = 'json') -> str:
        """Export subscription data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, u.email, u.created_at as user_created
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
        ''')
        
        subscriptions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if format == 'json':
            return json.dumps(subscriptions, indent=2, default=str)
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=subscriptions[0].keys())
            writer.writeheader()
            writer.writerows(subscriptions)
            return output.getvalue()
        else:
            return str(subscriptions)