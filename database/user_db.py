"""
User Database Management for Telegram Bot
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class UserDatabase:
    """Manage user data for Telegram bot"""
    
    def __init__(self, db_path: str = "database/users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'en',
                    balance REAL DEFAULT 0.0,
                    total_spent REAL DEFAULT 0.0,
                    total_orders INTEGER DEFAULT 0,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned BOOLEAN DEFAULT FALSE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_premium BOOLEAN DEFAULT FALSE,
                    settings TEXT DEFAULT '{}'
                )
            ''')
            
            # User sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # User statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    daily_views INTEGER DEFAULT 0,
                    weekly_views INTEGER DEFAULT 0,
                    monthly_views INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    successful_orders INTEGER DEFAULT 0,
                    failed_orders INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("User database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize user database: {e}")
            raise
    
    def add_user(self, user_id: int, username: str = "", 
                 first_name: str = "", last_name: str = "", 
                 language_code: str = "en") -> bool:
        """Add new user to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, language_code, registration_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, language_code, datetime.now()))
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"User {user_id} added to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.*, s.daily_views, s.weekly_views, s.monthly_views, 
                       s.total_views, s.successful_orders, s.failed_orders
                FROM users u
                LEFT JOIN user_stats s ON u.user_id = s.user_id
                WHERE u.user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    def update_user_balance(self, user_id: int, amount: float) -> bool:
        """Update user balance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET balance = balance + ?, 
                    total_spent = total_spent + ABS(?) 
                WHERE user_id = ? AND balance + ? >= 0
            ''', (amount, amount if amount < 0 else 0, user_id, amount))
            
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update balance for user {user_id}: {e}")
            return False
    
    def update_user_stats(self, user_id: int, views: int = 0, 
                         successful: bool = True) -> bool:
        """Update user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update total views
            cursor.execute('''
                UPDATE user_stats 
                SET total_views = total_views + ?,
                    daily_views = daily_views + ?,
                    weekly_views = weekly_views + ?,
                    monthly_views = monthly_views + ?,
                    last_updated = ?
                WHERE user_id = ?
            ''', (views, views, views, views, datetime.now(), user_id))
            
            # Update order stats
            if successful:
                cursor.execute('''
                    UPDATE user_stats 
                    SET successful_orders = successful_orders + 1
                    WHERE user_id = ?
                ''', (user_id,))
            else:
                cursor.execute('''
                    UPDATE user_stats 
                    SET failed_orders = failed_orders + 1
                    WHERE user_id = ?
                ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update stats for user {user_id}: {e}")
            return False
    
    def get_top_users(self, limit: int = 10, by: str = "total_views") -> List[Dict]:
        """Get top users by specified metric"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            valid_columns = ["total_views", "total_spent", "balance", "successful_orders"]
            if by not in valid_columns:
                by = "total_views"
            
            cursor.execute(f'''
                SELECT u.user_id, u.username, u.balance, u.total_spent, 
                       s.total_views, s.successful_orders
                FROM users u
                LEFT JOIN user_stats s ON u.user_id = s.user_id
                WHERE u.is_banned = FALSE
                ORDER BY u.{by} DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get top users: {e}")
            return []
    
    def add_session(self, user_id: int, session_id: str, 
                   ip_address: str = "", user_agent: str = "") -> bool:
        """Add user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions 
                (session_id, user_id, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (session_id, user_id, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add session: {e}")
            return False
    
    def update_last_active(self, user_id: int) -> bool:
        """Update user's last active timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_active = ? 
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update last active for user {user_id}: {e}")
            return False
    
    def get_user_count(self) -> Dict[str, int]:
        """Get user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total'] = cursor.fetchone()[0]
            
            # Active users (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_active >= datetime('now', '-7 days')
            ''')
            stats['active_7_days'] = cursor.fetchone()[0]
            
            # Active users (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_active >= datetime('now', '-1 day')
            ''')
            stats['active_24_hours'] = cursor.fetchone()[0]
            
            # Premium users
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = TRUE")
            stats['premium'] = cursor.fetchone()[0]
            
            # Banned users
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = TRUE")
            stats['banned'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user count: {e}")
            return {}
    
    def backup_database(self, backup_path: str = "backups/users_backup.db") -> bool:
        """Create database backup"""
        try:
            import shutil
            from pathlib import Path
            
            Path("backups").mkdir(exist_ok=True)
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False