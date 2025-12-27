#!/usr/bin/env python3
"""
Telegram Bot User Database Management
"""
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self, db_path: str = "database/users.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'en',
                balance REAL DEFAULT 0,
                total_spent REAL DEFAULT 0,
                views_bought INTEGER DEFAULT 0,
                role TEXT DEFAULT 'user',
                status TEXT DEFAULT 'active',
                registered_at TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notifications INTEGER DEFAULT 1,
                auto_renew INTEGER DEFAULT 0,
                theme TEXT DEFAULT 'dark',
                vip_level INTEGER DEFAULT 0,
                custom_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id)
            )
        ''')
        
        # User activity log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # User referrals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                bonus_credited INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (referred_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(referred_id)
            )
        ''')
        
        # User sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                device_info TEXT,
                ip_address TEXT,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def add_user(self, telegram_id: int, username: str = None, 
                 first_name: str = None, last_name: str = None) -> bool:
        """Add new user to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (telegram_id, username, first_name, last_name, registered_at, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name, current_time, current_time))
            
            if cursor.rowcount > 0:
                # Add default settings for new user
                user_id = cursor.lastrowid
                cursor.execute('''
                    INSERT INTO user_settings (user_id) VALUES (?)
                ''', (user_id,))
                
                conn.commit()
                logger.info(f"New user added: {telegram_id} ({username})")
                return True
            else:
                # Update last_seen for existing user
                cursor.execute('''
                    UPDATE users SET last_seen = ? WHERE telegram_id = ?
                ''', (current_time, telegram_id))
                conn.commit()
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error adding user: {e}")
            return False
        finally:
            conn.close()
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.*, us.notifications, us.auto_renew, us.theme, us.vip_level
                FROM users u
                LEFT JOIN user_settings us ON u.id = us.user_id
                WHERE u.telegram_id = ?
            ''', (telegram_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting user: {e}")
            return None
        finally:
            conn.close()
    
    def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Update user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query
            valid_fields = ['username', 'first_name', 'last_name', 'language', 
                          'balance', 'total_spent', 'views_bought', 'role', 'status']
            
            updates = []
            values = []
            
            for key, value in kwargs.items():
                if key in valid_fields:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            values.append(telegram_id)
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f'''
                UPDATE users 
                SET {', '.join(updates)}
                WHERE telegram_id = ?
            '''
            
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating user: {e}")
            return False
        finally:
            conn.close()
    
    def update_user_settings(self, telegram_id: int, **kwargs) -> bool:
        """Update user settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user ID first
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return False
            
            user_id = user_row[0]
            
            # Build update query
            valid_fields = ['notifications', 'auto_renew', 'theme', 'vip_level', 'custom_data']
            
            updates = []
            values = []
            
            for key, value in kwargs.items():
                if key in valid_fields:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            values.append(user_id)
            
            query = f'''
                UPDATE user_settings 
                SET {', '.join(updates)}
                WHERE user_id = ?
            '''
            
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating user settings: {e}")
            return False
        finally:
            conn.close()
    
    def update_balance(self, telegram_id: int, amount: float, 
                      operation: str = 'add') -> bool:
        """Update user balance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if operation == 'add':
                cursor.execute('''
                    UPDATE users 
                    SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (amount, telegram_id))
            elif operation == 'subtract':
                cursor.execute('''
                    UPDATE users 
                    SET balance = balance - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (amount, telegram_id))
            elif operation == 'set':
                cursor.execute('''
                    UPDATE users 
                    SET balance = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (amount, telegram_id))
            else:
                return False
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating balance: {e}")
            return False
        finally:
            conn.close()
    
    def log_activity(self, telegram_id: int, action: str, 
                    details: str = None, ip_address: str = None,
                    user_agent: str = None) -> bool:
        """Log user activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return False
            
            user_id = user_row[0]
            
            cursor.execute('''
                INSERT INTO user_activity 
                (user_id, action, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, action, details, ip_address, user_agent))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging activity: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_stats(self, telegram_id: int) -> Dict:
        """Get user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get basic user info
            cursor.execute('''
                SELECT u.*, us.notifications, us.auto_renew, us.theme, us.vip_level
                FROM users u
                LEFT JOIN user_settings us ON u.id = us.user_id
                WHERE u.telegram_id = ?
            ''', (telegram_id,))
            
            user = cursor.fetchone()
            if not user:
                return {}
            
            # Get activity count for today
            cursor.execute('''
                SELECT COUNT(*) as activity_count
                FROM user_activity
                WHERE user_id = ? AND DATE(created_at) = DATE('now')
            ''', (user['id'],))
            
            activity = cursor.fetchone()
            
            # Get referrals count
            cursor.execute('''
                SELECT COUNT(*) as referrals_count
                FROM referrals
                WHERE referrer_id = ? AND status = 'completed'
            ''', (user['id'],))
            
            referrals = cursor.fetchone()
            
            # Get active sessions
            cursor.execute('''
                SELECT COUNT(*) as active_sessions
                FROM user_sessions
                WHERE user_id = ? AND is_active = 1 AND expires_at > CURRENT_TIMESTAMP
            ''', (user['id'],))
            
            sessions = cursor.fetchone()
            
            stats = dict(user)
            stats['today_activity'] = activity['activity_count'] if activity else 0
            stats['referrals_count'] = referrals['referrals_count'] if referrals else 0
            stats['active_sessions'] = sessions['active_sessions'] if sessions else 0
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
        finally:
            conn.close()
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users with pagination"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.*, us.notifications, us.auto_renew, us.vip_level
                FROM users u
                LEFT JOIN user_settings us ON u.id = us.user_id
                ORDER BY u.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting all users: {e}")
            return []
        finally:
            conn.close()
    
    def search_users(self, query: str, limit: int = 50) -> List[Dict]:
        """Search users by username or Telegram ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try to parse as Telegram ID
            try:
                telegram_id = int(query)
                cursor.execute('''
                    SELECT u.*, us.notifications, us.auto_renew, us.vip_level
                    FROM users u
                    LEFT JOIN user_settings us ON u.id = us.user_id
                    WHERE u.telegram_id = ?
                    LIMIT ?
                ''', (telegram_id, limit))
            except ValueError:
                # Search by username
                cursor.execute('''
                    SELECT u.*, us.notifications, us.auto_renew, us.vip_level
                    FROM users u
                    LEFT JOIN user_settings us ON u.id = us.user_id
                    WHERE u.username LIKE ? OR u.first_name LIKE ? OR u.last_name LIKE ?
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error searching users: {e}")
            return []
        finally:
            conn.close()
    
    def get_users_count(self) -> Dict:
        """Get total users count with breakdown"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['total'] = cursor.fetchone()[0]
            
            # Active users (seen in last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_seen >= datetime('now', '-7 days')
            ''')
            stats['active_7d'] = cursor.fetchone()[0]
            
            # New users today
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(registered_at) = DATE('now')
            ''')
            stats['new_today'] = cursor.fetchone()[0]
            
            # Users by role
            cursor.execute('''
                SELECT role, COUNT(*) as count 
                FROM users 
                GROUP BY role
            ''')
            stats['by_role'] = dict(cursor.fetchall())
            
            # Users by status
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM users 
                GROUP BY status
            ''')
            stats['by_status'] = dict(cursor.fetchall())
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting users count: {e}")
            return {}
        finally:
            conn.close()
    
    def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all related data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE telegram_id = ?', (telegram_id,))
            
            conn.commit()
            deleted = cursor.rowcount > 0
            
            if deleted:
                logger.info(f"User deleted: {telegram_id}")
            
            return deleted
        except sqlite3.Error as e:
            logger.error(f"Error deleting user: {e}")
            return False
        finally:
            conn.close()
    
    def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Add referral relationship"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO referrals (referrer_id, referred_id)
                VALUES (?, ?)
            ''', (referrer_id, referred_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error adding referral: {e}")
            return False
        finally:
            conn.close()
    
    def complete_referral(self, referred_id: int) -> bool:
        """Mark referral as completed and give bonus"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get referral
            cursor.execute('''
                SELECT id, referrer_id FROM referrals 
                WHERE referred_id = ? AND status = 'pending'
            ''', (referred_id,))
            
            referral = cursor.fetchone()
            if not referral:
                return False
            
            referral_id, referrer_id = referral
            
            # Update referral status
            cursor.execute('''
                UPDATE referrals 
                SET status = 'completed', bonus_credited = 1 
                WHERE id = ?
            ''', (referral_id,))
            
            # Add bonus to referrer
            cursor.execute('''
                UPDATE users 
                SET balance = balance + 5.0 
                WHERE id = ?
            ''', (referrer_id,))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error completing referral: {e}")
            return False
        finally:
            conn.close()
    
    def create_session(self, telegram_id: int, session_id: str, 
                      device_info: str = None, ip_address: str = None,
                      expires_hours: int = 24) -> bool:
        """Create user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return False
            
            user_id = user_row[0]
            
            # Calculate expiry
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            cursor.execute('''
                INSERT INTO user_sessions 
                (user_id, session_id, device_info, ip_address, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_id, device_info, ip_address, expires_at.isoformat()))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating session: {e}")
            return False
        finally:
            conn.close()
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT us.*, u.telegram_id, u.username
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_id = ? 
                AND us.is_active = 1 
                AND us.expires_at > CURRENT_TIMESTAMP
            ''', (session_id,))
            
            session = cursor.fetchone()
            if session:
                # Update last activity
                cursor.execute('''
                    UPDATE user_sessions 
                    SET last_activity = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (session['id'],))
                conn.commit()
                
                return dict(session)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error validating session: {e}")
            return None
        finally:
            conn.close()
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = 0 
                WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error invalidating session: {e}")
            return False
        finally:
            conn.close()
    
    def export_user_data(self, telegram_id: int) -> Dict:
        """Export all user data"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get user
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()
            if not user:
                return {}
            
            user_data = dict(user)
            
            # Get settings
            cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user['id'],))
            settings = cursor.fetchone()
            user_data['settings'] = dict(settings) if settings else {}
            
            # Get recent activity
            cursor.execute('''
                SELECT * FROM user_activity 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 100
            ''', (user['id'],))
            user_data['activity'] = [dict(row) for row in cursor.fetchall()]
            
            # Get referrals
            cursor.execute('''
                SELECT r.*, u.username as referred_username
                FROM referrals r
                JOIN users u ON r.referred_id = u.id
                WHERE r.referrer_id = ?
            ''', (user['id'],))
            user_data['referrals'] = [dict(row) for row in cursor.fetchall()]
            
            return user_data
        except sqlite3.Error as e:
            logger.error(f"Error exporting user data: {e}")
            return {}
        finally:
            conn.close()
    
    def backup_database(self, backup_path: str) -> bool:
        """Create backup of database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False

# Singleton instance
user_db = UserDatabase()

# Quick test
if __name__ == "__main__":
    # Test database
    db = UserDatabase()
    
    # Add test user
    db.add_user(123456789, "test_user", "Test", "User")
    
    # Get user
    user = db.get_user(123456789)
    print(f"User: {user}")
    
    # Update balance
    db.update_balance(123456789, 10.0, 'add')
    
    # Get updated user
    user = db.get_user(123456789)
    print(f"User after balance update: {user}")
    
    # Log activity
    db.log_activity(123456789, "test_action", "Testing activity logging")
    
    # Get stats
    stats = db.get_user_stats(123456789)
    print(f"User stats: {stats}")
    
    print("✅ User database test completed successfully")