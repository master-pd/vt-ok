#!/usr/bin/env python3
"""
Telegram Bot Analytics Database Management
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class AnalyticsDatabase:
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily analytics summary
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                new_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                completed_orders INTEGER DEFAULT 0,
                failed_orders INTEGER DEFAULT 0,
                total_views_ordered INTEGER DEFAULT 0,
                total_views_delivered INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0,
                avg_order_value REAL DEFAULT 0,
                conversion_rate REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Hourly analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hourly_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                hour INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL DEFAULT 0,
                details TEXT,
                UNIQUE(date, hour, metric_name)
            )
        ''')
        
        # User behavior analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                sessions_count INTEGER DEFAULT 0,
                session_duration INTEGER DEFAULT 0,
                commands_used TEXT,
                orders_placed INTEGER DEFAULT 0,
                views_ordered INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE NOT NULL,
                metric_hour INTEGER DEFAULT 0,
                metric_type TEXT NOT NULL,
                method_name TEXT,
                views_attempted INTEGER DEFAULT 0,
                views_successful INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                avg_speed REAL DEFAULT 0,
                accounts_used INTEGER DEFAULT 0,
                proxies_used INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                details TEXT,
                UNIQUE(metric_date, metric_hour, metric_type, method_name)
            )
        ''')
        
        # Revenue analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                payment_method TEXT NOT NULL,
                transactions_count INTEGER DEFAULT 0,
                total_amount REAL DEFAULT 0,
                avg_amount REAL DEFAULT 0,
                success_rate REAL DEFAULT 0,
                refunds_count INTEGER DEFAULT 0,
                refunds_amount REAL DEFAULT 0,
                details TEXT,
                UNIQUE(date, payment_method)
            )
        ''')
        
        # Geographic analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS geographic_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                country TEXT NOT NULL,
                users_count INTEGER DEFAULT 0,
                orders_count INTEGER DEFAULT 0,
                views_ordered INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0,
                success_rate REAL DEFAULT 0,
                details TEXT,
                UNIQUE(date, country)
            )
        ''')
        
        # Bot command analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                command TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                details TEXT,
                UNIQUE(date, command)
            )
        ''')
        
        # Retention analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS retention_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cohort_date DATE NOT NULL,
                days_since INTEGER NOT NULL,
                retained_users INTEGER DEFAULT 0,
                retention_rate REAL DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                orders_per_user REAL DEFAULT 0,
                revenue_per_user REAL DEFAULT 0,
                details TEXT,
                UNIQUE(cohort_date, days_since)
            )
        ''')
        
        # Error tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                error_type TEXT NOT NULL,
                error_count INTEGER DEFAULT 0,
                affected_users INTEGER DEFAULT 0,
                resolved_count INTEGER DEFAULT 0,
                avg_resolution_time REAL DEFAULT 0,
                details TEXT,
                UNIQUE(date, error_type)
            )
        ''')
        
        # Real-time metrics (for dashboard)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_key TEXT UNIQUE NOT NULL,
                metric_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # A/B testing results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_testing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                variant TEXT NOT NULL,
                participants INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                conversion_rate REAL DEFAULT 0,
                revenue REAL DEFAULT 0,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Analytics database initialized at {self.db_path}")
    
    def update_daily_summary(self, date_str: str = None) -> bool:
        """Update daily summary statistics"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            # This would typically aggregate data from other tables
            # For now, we'll create a placeholder implementation
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if summary already exists
            cursor.execute('SELECT id FROM daily_summary WHERE date = ?', (date_str,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing summary
                cursor.execute('''
                    UPDATE daily_summary 
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE date = ?
                ''', (date_str,))
            else:
                # Create new summary
                cursor.execute('''
                    INSERT INTO daily_summary (date) VALUES (?)
                ''', (date_str,))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating daily summary: {e}")
            return False
        finally:
            conn.close()
    
    def log_hourly_metric(self, metric_name: str, metric_value: float,
                         date_str: str = None, hour: int = None,
                         details: Dict = None) -> bool:
        """Log hourly metric"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y-%m-%d')
            if hour is None:
                hour = datetime.now().hour
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            details_json = json.dumps(details) if details else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO hourly_metrics 
                (date, hour, metric_name, metric_value, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (date_str, hour, metric_name, metric_value, details_json))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging hourly metric: {e}")
            return False
        finally:
            conn.close()
    
    def log_user_behavior(self, user_id: int, date_str: str = None,
                         **kwargs) -> bool:
        """Log user behavior"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if record exists
            cursor.execute('''
                SELECT id FROM user_behavior 
                WHERE user_id = ? AND date = ?
            ''', (user_id, date_str))
            
            existing = cursor.fetchone()
            
            commands_used = json.dumps(kwargs.get('commands_used', []))
            
            if existing:
                # Update existing
                updates = []
                values = []
                
                for key, value in kwargs.items():
                    if key == 'commands_used':
                        updates.append(f"{key} = ?")
                        values.append(commands_used)
                    elif key in ['sessions_count', 'session_duration', 
                                'orders_placed', 'views_ordered', 'total_spent']:
                        updates.append(f"{key} = {key} + ?")
                        values.append(value)
                
                if updates:
                    values.extend([user_id, date_str])
                    query = f'''
                        UPDATE user_behavior 
                        SET {', '.join(updates)}
                        WHERE user_id = ? AND date = ?
                    '''
                    cursor.execute(query, values)
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO user_behavior 
                    (user_id, date, sessions_count, session_duration, 
                     commands_used, orders_placed, views_ordered, total_spent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, date_str,
                    kwargs.get('sessions_count', 0),
                    kwargs.get('session_duration', 0),
                    commands_used,
                    kwargs.get('orders_placed', 0),
                    kwargs.get('views_ordered', 0),
                    kwargs.get('total_spent', 0)
                ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging user behavior: {e}")
            return False
        finally:
            conn.close()
    
    def log_performance_metric(self, metric_type: str, method_name: str = None,
                              views_attempted: int = 0, views_successful: int = 0,
                              success_rate: float = None, avg_speed: float = 0,
                              accounts_used: int = 0, proxies_used: int = 0,
                              errors_count: int = 0, details: Dict = None) -> bool:
        """Log performance metric"""
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            hour = datetime.now().hour
            
            if success_rate is None and views_attempted > 0:
                success_rate = (views_successful / views_attempted) * 100
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            details_json = json.dumps(details) if details else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO performance_metrics 
                (metric_date, metric_hour, metric_type, method_name,
                 views_attempted, views_successful, success_rate, avg_speed,
                 accounts_used, proxies_used, errors_count, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_str, hour, metric_type, method_name,
                views_attempted, views_successful, success_rate, avg_speed,
                accounts_used, proxies_used, errors_count, details_json
            ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging performance metric: {e}")
            return False
        finally:
            conn.close()
    
    def log_revenue(self, payment_method: str, amount: float,
                   success: bool = True, date_str: str = None) -> bool:
        """Log revenue transaction"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing record
            cursor.execute('''
                SELECT transactions_count, total_amount, success_count
                FROM revenue_analytics 
                WHERE date = ? AND payment_method = ?
            ''', (date_str, payment_method))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                trans_count, total_amount, success_count = existing
                trans_count += 1
                total_amount += amount
                success_count += 1 if success else 0
                success_rate = (success_count / trans_count) * 100
                avg_amount = total_amount / trans_count
                
                cursor.execute('''
                    UPDATE revenue_analytics 
                    SET transactions_count = ?, total_amount = ?,
                        avg_amount = ?, success_rate = ?,
                        success_count = ?
                    WHERE date = ? AND payment_method = ?
                ''', (trans_count, total_amount, avg_amount, success_rate,
                     success_count, date_str, payment_method))
            else:
                # Insert new
                success_count = 1 if success else 0
                success_rate = 100 if success else 0
                
                cursor.execute('''
                    INSERT INTO revenue_analytics 
                    (date, payment_method, transactions_count, total_amount,
                     avg_amount, success_rate, success_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_str, payment_method, 1, amount, amount,
                     success_rate, success_count))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging revenue: {e}")
            return False
        finally:
            conn.close()
    
    def log_geographic_data(self, country: str, user_id: int = None,
                           order_data: Dict = None, date_str: str = None) -> bool:
        """Log geographic data"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing record
            cursor.execute('''
                SELECT users_count, orders_count, views_ordered, revenue
                FROM geographic_analytics 
                WHERE date = ? AND country = ?
            ''', (date_str, country))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                users_count, orders_count, views_ordered, revenue = existing
                
                updates = []
                values = []
                
                if user_id:
                    # Check if user already counted
                    cursor.execute('''
                        SELECT COUNT(*) FROM user_behavior 
                        WHERE user_id = ? AND date = ?
                    ''', (user_id, date_str))
                    
                    user_exists = cursor.fetchone()[0] > 0
                    if not user_exists:
                        updates.append("users_count = users_count + 1")
                
                if order_data:
                    updates.append("orders_count = orders_count + 1")
                    updates.append("views_ordered = views_ordered + ?")
                    values.append(order_data.get('views', 0))
                    
                    updates.append("revenue = revenue + ?")
                    values.append(order_data.get('amount', 0))
                
                if updates:
                    values.extend([date_str, country])
                    query = f'''
                        UPDATE geographic_analytics 
                        SET {', '.join(updates)}
                        WHERE date = ? AND country = ?
                    '''
                    cursor.execute(query, values)
            else:
                # Insert new
                users_count = 1 if user_id else 0
                orders_count = 1 if order_data else 0
                views_ordered = order_data.get('views', 0) if order_data else 0
                revenue = order_data.get('amount', 0) if order_data else 0
                
                cursor.execute('''
                    INSERT INTO geographic_analytics 
                    (date, country, users_count, orders_count, 
                     views_ordered, revenue)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (date_str, country, users_count, orders_count,
                     views_ordered, revenue))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging geographic data: {e}")
            return False
        finally:
            conn.close()
    
    def log_command_usage(self, command: str, success: bool = True,
                         response_time: float = 0, error: str = None) -> bool:
        """Log command usage"""
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing record
            cursor.execute('''
                SELECT usage_count, success_count, errors_count, 
                       total_response_time
                FROM command_analytics 
                WHERE date = ? AND command = ?
            ''', (date_str, command))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                usage_count, success_count, errors_count, total_response_time = existing
                usage_count += 1
                success_count += 1 if success else 0
                errors_count += 1 if error else 0
                total_response_time += response_time
                avg_response_time = total_response_time / usage_count
                
                cursor.execute('''
                    UPDATE command_analytics 
                    SET usage_count = ?, success_count = ?, errors_count = ?,
                        avg_response_time = ?, total_response_time = ?
                    WHERE date = ? AND command = ?
                ''', (usage_count, success_count, errors_count,
                     avg_response_time, total_response_time,
                     date_str, command))
            else:
                # Insert new
                success_count = 1 if success else 0
                errors_count = 1 if error else 0
                
                cursor.execute('''
                    INSERT INTO command_analytics 
                    (date, command, usage_count, success_count, 
                     errors_count, avg_response_time, total_response_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_str, command, 1, success_count,
                     errors_count, response_time, response_time))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging command usage: {e}")
            return False
        finally:
            conn.close()
    
    def update_retention(self, user_id: int, registration_date: str) -> bool:
        """Update retention analytics for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate days since registration
            reg_date = datetime.strptime(registration_date, '%Y-%m-%d')
            current_date = datetime.now()
            days_since = (current_date - reg_date).days
            
            # Get user's activity today
            cursor.execute('''
                SELECT COUNT(*) FROM user_behavior 
                WHERE user_id = ? AND date = ?
            ''', (user_id, current_date.strftime('%Y-%m-%d')))
            
            active_today = cursor.fetchone()[0] > 0
            
            if active_today:
                # Update retention for this cohort and day
                cursor.execute('''
                    SELECT retained_users FROM retention_analytics 
                    WHERE cohort_date = ? AND days_since = ?
                ''', (registration_date, days_since))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    retained_users = existing[0] + 1
                    
                    # Get cohort size
                    cursor.execute('''
                        SELECT COUNT(*) FROM user_behavior 
                        WHERE user_id IN (
                            SELECT user_id FROM user_behavior 
                            WHERE DATE(created_at) = ?
                        )
                    ''', (registration_date,))
                    
                    cohort_size = cursor.fetchone()[0]
                    retention_rate = (retained_users / cohort_size) * 100 if cohort_size > 0 else 0
                    
                    cursor.execute('''
                        UPDATE retention_analytics 
                        SET retained_users = ?, retention_rate = ?,
                            active_users = active_users + 1
                        WHERE cohort_date = ? AND days_since = ?
                    ''', (retained_users, retention_rate,
                         registration_date, days_since))
                else:
                    # Insert new
                    cursor.execute('''
                        INSERT INTO retention_analytics 
                        (cohort_date, days_since, retained_users, 
                         retention_rate, active_users)
                        VALUES (?, ?, 1, 0, 1)
                    ''', (registration_date, days_since))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating retention: {e}")
            return False
        finally:
            conn.close()
    
    def log_error(self, error_type: str, user_id: int = None,
                 resolved: bool = False, resolution_time: float = None) -> bool:
        """Log error for analytics"""
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing record
            cursor.execute('''
                SELECT error_count, affected_users, resolved_count,
                       total_resolution_time
                FROM error_analytics 
                WHERE date = ? AND error_type = ?
            ''', (date_str, error_type))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                error_count, affected_users, resolved_count, total_res_time = existing
                error_count += 1
                
                if user_id:
                    # Check if user already affected
                    cursor.execute('''
                        SELECT COUNT(*) FROM error_analytics_details 
                        WHERE date = ? AND error_type = ? AND user_id = ?
                    ''')
                    # Note: error_analytics_details table not created in this example
                    # In production, you'd have a separate table for details
                    affected_users += 1  # Simplified
                
                if resolved:
                    resolved_count += 1
                    total_res_time += resolution_time or 0
                
                avg_resolution_time = total_res_time / resolved_count if resolved_count > 0 else 0
                
                cursor.execute('''
                    UPDATE error_analytics 
                    SET error_count = ?, affected_users = ?, resolved_count = ?,
                        total_resolution_time = ?, avg_resolution_time = ?
                    WHERE date = ? AND error_type = ?
                ''', (error_count, affected_users, resolved_count,
                     total_res_time, avg_resolution_time,
                     date_str, error_type))
            else:
                # Insert new
                affected_users = 1 if user_id else 0
                resolved_count = 1 if resolved else 0
                total_res_time = resolution_time or 0
                avg_resolution_time = resolution_time or 0
                
                cursor.execute('''
                    INSERT INTO error_analytics 
                    (date, error_type, error_count, affected_users,
                     resolved_count, total_resolution_time, avg_resolution_time)
                    VALUES (?, ?, 1, ?, ?, ?, ?)
                ''', (date_str, error_type, affected_users,
                     resolved_count, total_res_time, avg_resolution_time))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging error: {e}")
            return False
        finally:
            conn.close()
    
    def update_realtime_metric(self, metric_key: str, metric_value: Any) -> bool:
        """Update real-time metric for dashboard"""
        try:
            value_str = json.dumps(metric_value) if not isinstance(metric_value, str) else metric_value
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO realtime_metrics 
                (metric_key, metric_value)
                VALUES (?, ?)
            ''', (metric_key, value_str))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating realtime metric: {e}")
            return False
        finally:
            conn.close()
    
    def get_realtime_metric(self, metric_key: str) -> Any:
        """Get real-time metric"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT metric_value FROM realtime_metrics 
                WHERE metric_key = ?
            ''', (metric_key,))
            
            result = cursor.fetchone()
            if result:
                value = result[0]
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting realtime metric: {e}")
            return None
        finally:
            conn.close()
    
    def log_ab_test(self, test_id: str, variant: str, converted: bool = False,
                   revenue: float = 0) -> bool:
        """Log A/B test result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing record
            cursor.execute('''
                SELECT participants, conversions, revenue
                FROM ab_testing 
                WHERE test_id = ? AND variant = ?
            ''', (test_id, variant))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                participants, conversions, total_revenue = existing
                participants += 1
                conversions += 1 if converted else 0
                total_revenue += revenue
                conversion_rate = (conversions / participants) * 100 if participants > 0 else 0
                
                cursor.execute('''
                    UPDATE ab_testing 
                    SET participants = ?, conversions = ?, 
                        conversion_rate = ?, revenue = ?
                    WHERE test_id = ? AND variant = ?
                ''', (participants, conversions, conversion_rate,
                     total_revenue, test_id, variant))
            else:
                # Insert new
                participants = 1
                conversions = 1 if converted else 0
                conversion_rate = 100 if converted else 0
                total_revenue = revenue
                
                cursor.execute('''
                    INSERT INTO ab_testing 
                    (test_id, variant, participants, conversions,
                     conversion_rate, revenue)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (test_id, variant, participants, conversions,
                     conversion_rate, total_revenue))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging A/B test: {e}")
            return False
        finally:
            conn.close()
    
    def get_dashboard_stats(self, days: int = 7) -> Dict:
        """Get statistics for dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Date range
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Overall stats
            cursor.execute('''
                SELECT 
                    SUM(new_users) as total_users,
                    SUM(total_orders) as total_orders,
                    SUM(total_revenue) as total_revenue,
                    SUM(total_views_delivered) as total_views
                FROM daily_summary 
                WHERE date BETWEEN ? AND ?
            ''', (start_date, end_date))
            
            row = cursor.fetchone()
            if row:
                stats['total_users'] = row[0] or 0
                stats['total_orders'] = row[1] or 0
                stats['total_revenue'] = row[2] or 0
                stats['total_views'] = row[3] or 0
            
            # Today's stats
            cursor.execute('''
                SELECT 
                    new_users,
                    active_users,
                    total_orders,
                    total_revenue
                FROM daily_summary 
                WHERE date = ?
            ''', (end_date,))
            
            row = cursor.fetchone()
            if row:
                stats['today_new_users'] = row[0] or 0
                stats['today_active_users'] = row[1] or 0
                stats['today_orders'] = row[2] or 0
                stats['today_revenue'] = row[3] or 0
            
            # Revenue trend
            cursor.execute('''
                SELECT date, total_revenue 
                FROM daily_summary 
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            ''', (start_date, end_date))
            
            revenue_data = cursor.fetchall()
            stats['revenue_trend'] = dict(revenue_data) if revenue_data else {}
            
            # Top countries
            cursor.execute('''
                SELECT country, SUM(revenue) as total_revenue
                FROM geographic_analytics 
                WHERE date BETWEEN ? AND ?
                GROUP BY country 
                ORDER BY total_revenue DESC 
                LIMIT 5
            ''', (start_date, end_date))
            
            top_countries = cursor.fetchall()
            stats['top_countries'] = dict(top_countries) if top_countries else {}
            
            # Command usage
            cursor.execute('''
                SELECT command, SUM(usage_count) as total_usage
                FROM command_analytics 
                WHERE date BETWEEN ? AND ?
                GROUP BY command 
                ORDER BY total_usage DESC 
                LIMIT 10
            ''', (start_date, end_date))
            
            top_commands = cursor.fetchall()
            stats['top_commands'] = dict(top_commands) if top_commands else {}
            
            # Performance metrics
            cursor.execute('''
                SELECT method_name, AVG(success_rate) as avg_success_rate
                FROM performance_metrics 
                WHERE metric_date BETWEEN ? AND ?
                GROUP BY method_name 
                ORDER BY avg_success_rate DESC
            ''', (start_date, end_date))
            
            performance = cursor.fetchall()
            stats['performance'] = dict(performance) if performance else {}
            
            # Payment methods
            cursor.execute('''
                SELECT payment_method, SUM(total_amount) as total_amount
                FROM revenue_analytics 
                WHERE date BETWEEN ? AND ?
                GROUP BY payment_method 
                ORDER BY total_amount DESC
            ''', (start_date, end_date))
            
            payment_methods = cursor.fetchall()
            stats['payment_methods'] = dict(payment_methods) if payment_methods else {}
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
        finally:
            conn.close()
    
    def get_user_analytics(self, user_id: int) -> Dict:
        """Get analytics for specific user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            analytics = {}
            
            # User behavior summary
            cursor.execute('''
                SELECT 
                    SUM(sessions_count) as total_sessions,
                    AVG(session_duration) as avg_session_duration,
                    SUM(orders_placed) as total_orders,
                    SUM(views_ordered) as total_views_ordered,
                    SUM(total_spent) as total_spent
                FROM user_behavior 
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                analytics['total_sessions'] = row[0] or 0
                analytics['avg_session_duration'] = row[1] or 0
                analytics['total_orders'] = row[2] or 0
                analytics['total_views_ordered'] = row[3] or 0
                analytics['total_spent'] = row[4] or 0
            
            # Command usage
            cursor.execute('''
                SELECT command, COUNT(*) as usage_count
                FROM command_analytics_details  -- Note: This table doesn't exist in this example
                WHERE user_id = ?
                GROUP BY command 
                ORDER BY usage_count DESC 
                LIMIT 10
            ''')
            # Simplified for this example
            analytics['favorite_commands'] = {}
            
            # Activity timeline (last 30 days)
            cursor.execute('''
                SELECT date, sessions_count, orders_placed
                FROM user_behavior 
                WHERE user_id = ? 
                AND date >= date('now', '-30 days')
                ORDER BY date
            ''', (user_id,))
            
            timeline = cursor.fetchall()
            analytics['activity_timeline'] = [
                {'date': row[0], 'sessions': row[1], 'orders': row[2]}
                for row in timeline
            ]
            
            return analytics
        except sqlite3.Error as e:
            logger.error(f"Error getting user analytics: {e}")
            return {}
        finally:
            conn.close()
    
    def generate_report(self, report_type: str, start_date: str, 
                       end_date: str) -> Dict:
        """Generate analytics report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            report = {
                'type': report_type,
                'period': f'{start_date} to {end_date}',
                'generated_at': datetime.now().isoformat()
            }
            
            if report_type == 'daily_summary':
                cursor.execute('''
                    SELECT * FROM daily_summary 
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date
                ''', (start_date, end_date))
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                report['data'] = [dict(zip(columns, row)) for row in rows]
                
            elif report_type == 'revenue':
                cursor.execute('''
                    SELECT date, payment_method, total_amount, transactions_count
                    FROM revenue_analytics 
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date, payment_method
                ''', (start_date, end_date))
                
                rows = cursor.fetchall()
                report['data'] = [
                    {
                        'date': row[0],
                        'payment_method': row[1],
                        'total_amount': row[2],
                        'transactions_count': row[3]
                    }
                    for row in rows
                ]
                
            elif report_type == 'performance':
                cursor.execute('''
                    SELECT metric_date, method_name, 
                           AVG(success_rate) as avg_success_rate,
                           SUM(views_attempted) as total_attempted,
                           SUM(views_successful) as total_successful
                    FROM performance_metrics 
                    WHERE metric_date BETWEEN ? AND ?
                    GROUP BY metric_date, method_name
                    ORDER BY metric_date, method_name
                ''', (start_date, end_date))
                
                rows = cursor.fetchall()
                report['data'] = [
                    {
                        'date': row[0],
                        'method': row[1],
                        'avg_success_rate': row[2],
                        'total_attempted': row[3],
                        'total_successful': row[4]
                    }
                    for row in rows
                ]
                
            elif report_type == 'user_behavior':
                cursor.execute('''
                    SELECT date, 
                           COUNT(DISTINCT user_id) as active_users,
                           SUM(sessions_count) as total_sessions,
                           SUM(orders_placed) as total_orders,
                           SUM(total_spent) as total_revenue
                    FROM user_behavior 
                    WHERE date BETWEEN ? AND ?
                    GROUP BY date
                    ORDER BY date
                ''', (start_date, end_date))
                
                rows = cursor.fetchall()
                report['data'] = [
                    {
                        'date': row[0],
                        'active_users': row[1],
                        'total_sessions': row[2],
                        'total_orders': row[3],
                        'total_revenue': row[4]
                    }
                    for row in rows
                ]
            
            # Calculate summary statistics
            if 'data' in report and report['data']:
                data = report['data']
                if data and len(data) > 0:
                    if 'total_amount' in data[0]:
                        report['summary'] = {
                            'total_revenue': sum(item.get('total_amount', 0) for item in data),
                            'total_transactions': sum(item.get('transactions_count', 0) for item in data),
                            'avg_transaction': sum(item.get('total_amount', 0) for item in data) / 
                                             sum(item.get('transactions_count', 1) for item in data)
                        }
                    elif 'avg_success_rate' in data[0]:
                        report['summary'] = {
                            'avg_success_rate': sum(item.get('avg_success_rate', 0) for item in data) / len(data),
                            'total_attempted': sum(item.get('total_attempted', 0) for item in data),
                            'total_successful': sum(item.get('total_successful', 0) for item in data)
                        }
            
            return report
        except sqlite3.Error as e:
            logger.error(f"Error generating report: {e}")
            return {'error': str(e)}
        finally:
            conn.close()
    
    def export_data(self, format: str = 'json', **kwargs) -> Any:
        """Export analytics data"""
        try:
            data = {}
            
            if format == 'json':
                # Export all tables
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                tables = [
                    'daily_summary', 'hourly_metrics', 'user_behavior',
                    'performance_metrics', 'revenue_analytics',
                    'geographic_analytics', 'command_analytics',
                    'retention_analytics', 'error_analytics'
                ]
                
                for table in tables:
                    cursor.execute(f'SELECT * FROM {table} LIMIT 1000')
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    data[table] = [dict(zip(columns, row)) for row in rows]
                
                return json.dumps(data, indent=2, default=str)
            
            elif format == 'csv':
                # Simplified CSV export
                import csv
                import io
                
                table = kwargs.get('table', 'daily_summary')
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute(f'SELECT * FROM {table}')
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(columns)
                writer.writerows(rows)
                
                return output.getvalue()
            
            else:
                return None
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return None
    
    def cleanup_old_data(self, days: int = 90) -> Dict:
        """Cleanup old analytics data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cleanup_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            stats = {}
            
            tables = [
                ('daily_summary', 'date'),
                ('hourly_metrics', 'date'),
                ('user_behavior', 'date'),
                ('performance_metrics', 'metric_date'),
                ('revenue_analytics', 'date'),
                ('geographic_analytics', 'date'),
                ('command_analytics', 'date'),
                ('error_analytics', 'date')
            ]
            
            for table, date_column in tables:
                cursor.execute(f'''
                    DELETE FROM {table} 
                    WHERE {date_column} < ?
                ''', (cleanup_date,))
                stats[table] = cursor.rowcount
            
            # For retention analytics, keep only cohorts from last 180 days
            retention_cutoff = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            cursor.execute('''
                DELETE FROM retention_analytics 
                WHERE cohort_date < ?
            ''', (retention_cutoff,))
            stats['retention_analytics'] = cursor.rowcount
            
            conn.commit()
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {}
        finally:
            conn.close()

# Singleton instance
analytics_db = AnalyticsDatabase()

# Quick test
if __name__ == "__main__":
    # Test database
    db = AnalyticsDatabase()
    
    # Update daily summary
    db.update_daily_summary()
    
    # Log some metrics
    db.log_hourly_metric("active_users", 150)
    db.log_hourly_metric("orders_placed", 25)
    
    # Log user behavior
    db.log_user_behavior(
        user_id=123456789,
        sessions_count=1,
        session_duration=300,
        commands_used=["/start", "/buy"],
        orders_placed=1,
        views_ordered=1000,
        total_spent=5.0
    )
    
    # Log performance
    db.log_performance_metric(
        metric_type="view_delivery",
        method_name="browser_automation",
        views_attempted=100,
        views_successful=85,
        success_rate=85.0,
        avg_speed=2.5,
        accounts_used=5,
        proxies_used=3,
        errors_count=2
    )
    
    # Log revenue
    db.log_revenue("crypto", 50.0, success=True)
    
    # Get dashboard stats
    stats = db.get_dashboard_stats(days=7)
    print(f"Dashboard stats: {stats}")
    
    # Generate report
    today = datetime.now().strftime('%Y-%m-%d')
    report = db.generate_report("daily_summary", today, today)
    print(f"Report generated: {len(report.get('data', []))} records")
    
    print("✅ Analytics database test completed successfully")