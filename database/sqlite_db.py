"""
SQLite Database Manager - No hardcode, dynamic configuration
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

class SQLiteDatabase:
    """SQLite database manager with dynamic configuration"""
    
    def __init__(self, db_path: str = "database/data.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Setup database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create tables dynamically
        tables = self.get_table_schemas()
        
        for table_name, schema in tables.items():
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {', '.join(schema['columns'])}
                )
            """)
        
        conn.commit()
        conn.close()
        print("✅ SQLite database initialized")
    
    def get_table_schemas(self) -> Dict:
        """Get table schemas from JSON configuration"""
        return {
            'view_sessions': {
                'columns': [
                    'video_url TEXT NOT NULL',
                    'video_id TEXT',
                    'initial_views INTEGER DEFAULT 0',
                    'final_views INTEGER DEFAULT 0',
                    'views_sent INTEGER DEFAULT 0',
                    'views_increased INTEGER DEFAULT 0',
                    'success_rate REAL DEFAULT 0.0',
                    'method_used TEXT',
                    'start_time TIMESTAMP',
                    'end_time TIMESTAMP',
                    'duration_seconds INTEGER',
                    'status TEXT DEFAULT "pending"',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ]
            },
            'accounts': {
                'columns': [
                    'username TEXT UNIQUE',
                    'session_id TEXT',
                    'token TEXT',
                    'proxy TEXT',
                    'status TEXT DEFAULT "active"',
                    'views_sent INTEGER DEFAULT 0',
                    'last_used TIMESTAMP',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ]
            },
            'proxies': {
                'columns': [
                    'proxy_url TEXT UNIQUE',
                    'type TEXT',
                    'country TEXT',
                    'speed REAL',
                    'success_rate REAL DEFAULT 0.0',
                    'last_used TIMESTAMP',
                    'status TEXT DEFAULT "active"',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ]
            },
            'analytics': {
                'columns': [
                    'date DATE NOT NULL',
                    'method TEXT',
                    'views_sent INTEGER DEFAULT 0',
                    'views_increased INTEGER DEFAULT 0',
                    'success_rate REAL DEFAULT 0.0',
                    'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ]
            }
        }
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def insert_view_session(self, data: Dict) -> int:
        """Insert view session record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        columns = []
        values = []
        placeholders = []
        
        for key, value in data.items():
            columns.append(key)
            values.append(value)
            placeholders.append('?')
        
        sql = f"""
            INSERT INTO view_sessions ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        cursor.execute(sql, values)
        conn.commit()
        session_id = cursor.lastrowid
        conn.close()
        
        return session_id
    
    def update_view_session(self, session_id: int, data: Dict) -> bool:
        """Update view session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        
        sql = f"""
            UPDATE view_sessions 
            SET {set_clause}
            WHERE id = ?
        """
        
        values = list(data.values()) + [session_id]
        cursor.execute(sql, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        return success
    
    def get_active_accounts(self, limit: int = 10) -> List[Dict]:
        """Get active accounts"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM accounts 
            WHERE status = 'active' 
            ORDER BY last_used ASC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_account_usage(self, account_id: int, views_sent: int = 1):
        """Update account usage stats"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE accounts 
            SET views_sent = views_sent + ?,
                last_used = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (views_sent, account_id))
        
        conn.commit()
        conn.close()
    
    def get_working_proxies(self, limit: int = 20) -> List[Dict]:
        """Get working proxies"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM proxies 
            WHERE status = 'active' 
            AND success_rate > 0.5 
            ORDER BY success_rate DESC, last_used ASC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_proxy_stats(self, proxy_url: str, success: bool):
        """Update proxy statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute("SELECT success_rate, total_requests FROM proxies WHERE proxy_url = ?", (proxy_url,))
        row = cursor.fetchone()
        
        if row:
            old_rate, total_req = row
            total_req = total_req or 0
            
            # Calculate new success rate
            new_total = total_req + 1
            if success:
                new_success = (old_rate * total_req + 1) / new_total
            else:
                new_success = (old_rate * total_req) / new_total
            
            cursor.execute("""
                UPDATE proxies 
                SET success_rate = ?,
                    total_requests = ?,
                    last_used = CURRENT_TIMESTAMP
                WHERE proxy_url = ?
            """, (new_success, new_total, proxy_url))
        else:
            # Insert new proxy
            success_rate = 1.0 if success else 0.0
            cursor.execute("""
                INSERT INTO proxies (proxy_url, success_rate, total_requests, last_used)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            """, (proxy_url, success_rate))
        
        conn.commit()
        conn.close()
    
    def get_analytics(self, days: int = 7) -> Dict:
        """Get analytics data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                date,
                SUM(views_sent) as total_views_sent,
                SUM(views_increased) as total_views_increased,
                AVG(success_rate) as avg_success_rate
            FROM analytics 
            WHERE date >= date('now', ?)
            GROUP BY date
            ORDER BY date
        """, (f'-{days} days',))
        
        rows = cursor.fetchall()
        conn.close()
        
        analytics = []
        for row in rows:
            analytics.append({
                'date': row[0],
                'views_sent': row[1] or 0,
                'views_increased': row[2] or 0,
                'success_rate': row[3] or 0
            })
        
        return analytics
    
    def close(self):
        """Close database connection"""
        pass  # SQLite handles connection closing automatically