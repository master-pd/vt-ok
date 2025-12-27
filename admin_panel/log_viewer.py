"""
System log viewing and analysis system
"""
import sqlite3
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import re
import gzip
import io

class LogViewer:
    def __init__(self, db_path='database/logs.db'):
        self.db_path = db_path
        self._init_database()
        
        # Log levels
        self.levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # System logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                module TEXT,
                function TEXT,
                message TEXT,
                extra_data TEXT,
                ip_address TEXT,
                user_id TEXT,
                session_id TEXT,
                INDEX idx_timestamp (timestamp),
                INDEX idx_level (level),
                INDEX idx_module (module)
            )
        ''')
        
        # Error logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                error_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_type TEXT,
                error_message TEXT,
                traceback TEXT,
                module TEXT,
                function TEXT,
                user_id TEXT,
                ip_address TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP,
                resolved_by TEXT,
                notes TEXT,
                INDEX idx_timestamp (timestamp),
                INDEX idx_resolved (resolved)
            )
        ''')
        
        # Access logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                access_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                method TEXT,
                endpoint TEXT,
                status_code INTEGER,
                response_time REAL,
                user_id TEXT,
                request_size INTEGER,
                response_size INTEGER,
                INDEX idx_timestamp (timestamp),
                INDEX idx_endpoint (endpoint),
                INDEX idx_status (status_code)
            )
        ''')
        
        # Audit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                action TEXT,
                resource_type TEXT,
                resource_id TEXT,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                user_agent TEXT,
                notes TEXT,
                INDEX idx_timestamp (timestamp),
                INDEX idx_user (user_id),
                INDEX idx_action (action)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_system_event(self, level: str, module: str, function: str, 
                        message: str, extra_data: Dict = None, 
                        ip_address: str = None, user_id: str = None, 
                        session_id: str = None):
        """Log system event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        extra_json = json.dumps(extra_data) if extra_data else None
        
        cursor.execute('''
            INSERT INTO system_logs 
            (level, module, function, message, extra_data, 
             ip_address, user_id, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (level, module, function, message, extra_json,
              ip_address, user_id, session_id))
        
        conn.commit()
        conn.close()
    
    def log_error(self, error_type: str, error_message: str, 
                 traceback: str, module: str, function: str,
                 user_id: str = None, ip_address: str = None):
        """Log error with traceback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_logs 
            (error_type, error_message, traceback, module, function, 
             user_id, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (error_type, error_message, traceback, module, function,
              user_id, ip_address))
        
        error_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return error_id
    
    def log_access(self, ip_address: str, user_agent: str, method: str,
                  endpoint: str, status_code: int, response_time: float,
                  user_id: str = None, request_size: int = None,
                  response_size: int = None):
        """Log access request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO access_logs 
            (ip_address, user_agent, method, endpoint, status_code,
             response_time, user_id, request_size, response_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ip_address, user_agent, method, endpoint, status_code,
              response_time, user_id, request_size, response_size))
        
        conn.commit()
        conn.close()
    
    def log_audit(self, user_id: str, action: str, resource_type: str,
                 resource_id: str, old_value: str = None,
                 new_value: str = None, ip_address: str = None,
                 user_agent: str = None, notes: str = None):
        """Log audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_logs 
            (user_id, action, resource_type, resource_id, old_value,
             new_value, ip_address, user_agent, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action, resource_type, resource_id, old_value,
              new_value, ip_address, user_agent, notes))
        
        conn.commit()
        conn.close()
    
    def get_system_logs(self, filters: Dict = None, 
                       page: int = 1, per_page: int = 100) -> Dict:
        """Get system logs with filters"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM system_logs WHERE 1=1'
        count_query = 'SELECT COUNT(*) FROM system_logs WHERE 1=1'
        params = []
        
        if filters:
            if filters.get('level'):
                query += ' AND level = ?'
                count_query += ' AND level = ?'
                params.append(filters['level'])
            
            if filters.get('module'):
                query += ' AND module LIKE ?'
                count_query += ' AND module LIKE ?'
                params.append(f"%{filters['module']}%")
            
            if filters.get('search'):
                query += ' AND (message LIKE ? OR function LIKE ?)'
                count_query += ' AND (message LIKE ? OR function LIKE ?)'
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
            
            if filters.get('date_from'):
                query += ' AND DATE(timestamp) >= ?'
                count_query += ' AND DATE(timestamp) >= ?'
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                query += ' AND DATE(timestamp) <= ?'
                count_query += ' AND DATE(timestamp) <= ?'
                params.append(filters['date_to'])
            
            if filters.get('user_id'):
                query += ' AND user_id = ?'
                count_query += ' AND user_id = ?'
                params.append(filters['user_id'])
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Apply pagination and ordering
        offset = (page - 1) * per_page
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        logs = []
        
        for row in cursor.fetchall():
            log = dict(row)
            if log['extra_data']:
                log['extra_data'] = json.loads(log['extra_data'])
            logs.append(log)
        
        conn.close()
        
        return {
            'logs': logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
    
    def get_error_logs(self, unresolved_only: bool = False,
                      page: int = 1, per_page: int = 50) -> Dict:
        """Get error logs"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM error_logs WHERE 1=1'
        count_query = 'SELECT COUNT(*) FROM error_logs WHERE 1=1'
        params = []
        
        if unresolved_only:
            query += ' AND resolved = FALSE'
            count_query += ' AND resolved = FALSE'
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Apply pagination
        offset = (page - 1) * per_page
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        errors = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'errors': errors,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
    
    def mark_error_resolved(self, error_id: int, resolved_by: str, 
                           notes: str = None) -> bool:
        """Mark error as resolved"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE error_logs 
            SET resolved = TRUE, resolved_at = ?, resolved_by = ?, notes = ?
            WHERE error_id = ?
        ''', (datetime.now().isoformat(), resolved_by, notes, error_id))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        return affected > 0
    
    def get_access_stats(self, period: str = 'daily') -> Dict:
        """Get access statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if period == 'hourly':
            group_by = "STRFTIME('%Y-%m-%d %H:00', timestamp)"
        elif period == 'daily':
            group_by = "DATE(timestamp)"
        elif period == 'weekly':
            group_by = "STRFTIME('%Y-%W', timestamp)"
        else:
            group_by = "DATE(timestamp)"
        
        # Requests per period
        cursor.execute(f'''
            SELECT {group_by} as period,
                   COUNT(*) as request_count,
                   AVG(response_time) as avg_response_time,
                   SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
            FROM access_logs
            GROUP BY {group_by}
            ORDER BY period DESC
            LIMIT 30
        ''')
        
        stats = []
        for row in cursor.fetchall():
            stats.append({
                'period': row[0],
                'request_count': row[1],
                'avg_response_time': row[2] or 0,
                'error_count': row[3],
                'error_rate': (row[3] / row[1] * 100) if row[1] > 0 else 0
            })
        
        # Top endpoints
        cursor.execute('''
            SELECT endpoint,
                   COUNT(*) as request_count,
                   AVG(response_time) as avg_response_time,
                   SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
            FROM access_logs
            GROUP BY endpoint
            ORDER BY request_count DESC
            LIMIT 10
        ''')
        
        top_endpoints = []
        for row in cursor.fetchall():
            top_endpoints.append({
                'endpoint': row[0],
                'request_count': row[1],
                'avg_response_time': row[2] or 0,
                'error_count': row[3]
            })
        
        # Status code distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN status_code < 300 THEN '2xx'
                    WHEN status_code < 400 THEN '3xx'
                    WHEN status_code < 500 THEN '4xx'
                    ELSE '5xx'
                END as status_group,
                COUNT(*) as count
            FROM access_logs
            GROUP BY status_group
        ''')
        
        status_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'period_stats': stats,
            'top_endpoints': top_endpoints,
            'status_distribution': status_distribution,
            'summary': {
                'total_requests': sum(s['request_count'] for s in stats),
                'avg_response_time': sum(s['avg_response_time'] for s in stats) / len(stats) if stats else 0,
                'total_errors': sum(s['error_count'] for s in stats)
            }
        }
    
    def search_logs(self, search_term: str, log_type: str = 'all',
                   case_sensitive: bool = False) -> List[Dict]:
        """Search logs with regex support"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        results = []
        
        if log_type in ['all', 'system']:
            cursor = conn.cursor()
            query = '''
                SELECT * FROM system_logs 
                WHERE message LIKE ? OR function LIKE ? OR module LIKE ?
                ORDER BY timestamp DESC
                LIMIT 100
            '''
            
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            results.extend([dict(row) for row in cursor.fetchall()])
        
        if log_type in ['all', 'error']:
            cursor = conn.cursor()
            query = '''
                SELECT * FROM error_logs 
                WHERE error_message LIKE ? OR traceback LIKE ?
                ORDER BY timestamp DESC
                LIMIT 100
            '''
            
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern))
            results.extend([dict(row) for row in cursor.fetchall()])
        
        conn.close()
        
        # Sort all results by timestamp
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return results[:200]  # Limit to 200 results
    
    def export_logs(self, log_type: str, start_date: str, 
                   end_date: str, format: str = 'json') -> str:
        """Export logs in various formats"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        if log_type == 'system':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM system_logs 
                WHERE DATE(timestamp) BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_date, end_date))
            data = [dict(row) for row in cursor.fetchall()]
        
        elif log_type == 'error':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM error_logs 
                WHERE DATE(timestamp) BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_date, end_date))
            data = [dict(row) for row in cursor.fetchall()]
        
        elif log_type == 'access':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM access_logs 
                WHERE DATE(timestamp) BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_date, end_date))
            data = [dict(row) for row in cursor.fetchall()]
        
        else:
            data = []
        
        conn.close()
        
        if format == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format == 'csv':
            import csv
            import io
            
            if not data:
                return ""
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        elif format == 'gzip':
            # Compress JSON data
            json_data = json.dumps(data, default=str)
            compressed = gzip.compress(json_data.encode())
            return compressed
        else:
            return str(data)
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> Dict:
        """Cleanup old logs"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count records to be deleted
        cursor.execute('SELECT COUNT(*) FROM system_logs WHERE DATE(timestamp) < ?', (cutoff_date,))
        system_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM access_logs WHERE DATE(timestamp) < ?', (cutoff_date,))
        access_count = cursor.fetchone()[0]
        
        # Archive before deletion (in production, you might want to archive)
        # For now, just delete
        cursor.execute('DELETE FROM system_logs WHERE DATE(timestamp) < ?', (cutoff_date,))
        cursor.execute('DELETE FROM access_logs WHERE DATE(timestamp) < ?', (cutoff_date,))
        
        # Keep error logs for longer (90 days)
        error_cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        cursor.execute('SELECT COUNT(*) FROM error_logs WHERE DATE(timestamp) < ? AND resolved = TRUE', 
                      (error_cutoff,))
        error_count = cursor.fetchone()[0]
        cursor.execute('DELETE FROM error_logs WHERE DATE(timestamp) < ? AND resolved = TRUE', 
                      (error_cutoff,))
        
        conn.commit()
        conn.close()
        
        return {
            'system_logs_deleted': system_count,
            'access_logs_deleted': access_count,
            'error_logs_deleted': error_count,
            'cutoff_date': cutoff_date,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_log_analytics(self) -> Dict:
        """Get log analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Log levels distribution (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT level, COUNT(*) as count 
            FROM system_logs 
            WHERE DATE(timestamp) >= ?
            GROUP BY level
            ORDER BY count DESC
        ''', (week_ago,))
        
        level_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Error trends
        cursor.execute('''
            SELECT DATE(timestamp) as date,
                   COUNT(*) as error_count
            FROM error_logs
            WHERE DATE(timestamp) >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (week_ago,))
        
        error_trends = []
        for row in cursor.fetchall():
            error_trends.append({
                'date': row[0],
                'error_count': row[1]
            })
        
        # Most common errors
        cursor.execute('''
            SELECT error_type, COUNT(*) as count
            FROM error_logs
            WHERE resolved = FALSE
            GROUP BY error_type
            ORDER BY count DESC
            LIMIT 10
        ''')
        
        common_errors = []
        for row in cursor.fetchall():
            common_errors.append({
                'error_type': row[0],
                'count': row[1]
            })
        
        # Busiest hours
        cursor.execute('''
            SELECT STRFTIME('%H', timestamp) as hour,
                   COUNT(*) as request_count
            FROM access_logs
            WHERE DATE(timestamp) >= ?
            GROUP BY STRFTIME('%H', timestamp)
            ORDER BY request_count DESC
            LIMIT 5
        ''', (week_ago,))
        
        busy_hours = []
        for row in cursor.fetchall():
            busy_hours.append({
                'hour': row[0],
                'request_count': row[1]
            })
        
        conn.close()
        
        return {
            'level_distribution': level_distribution,
            'error_trends': error_trends,
            'common_errors': common_errors,
            'busy_hours': busy_hours,
            'period': f"Last 7 days (from {week_ago})",
            'summary': {
                'total_logs': sum(level_distribution.values()),
                'total_errors': sum(e['error_count'] for e in error_trends),
                'unresolved_errors': sum(e['count'] for e in common_errors)
            }
        }
    
    def stream_logs(self, filters: Dict = None):
        """Stream logs in real-time (generator)"""
        # This is a simplified version. In production, you might use
        # a message queue or WebSockets for real-time streaming.
        
        last_id = 0
        
        while True:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM system_logs WHERE log_id > ?'
            params = [last_id]
            
            if filters:
                if filters.get('level'):
                    query += ' AND level = ?'
                    params.append(filters['level'])
                
                if filters.get('module'):
                    query += ' AND module = ?'
                    params.append(filters['module'])
            
            query += ' ORDER BY log_id LIMIT 10'
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            if logs:
                last_id = logs[-1]['log_id']
                
                for log in logs:
                    yield dict(log)
            
            conn.close()
            
            # Wait before next check
            import time
            time.sleep(1)