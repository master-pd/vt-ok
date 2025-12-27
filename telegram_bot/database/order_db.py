#!/usr/bin/env python3
"""
Telegram Bot Order Database Management
"""
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import uuid

logger = logging.getLogger(__name__)

class OrderDatabase:
    def __init__(self, db_path: str = "database/orders.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                video_url TEXT NOT NULL,
                video_id TEXT,
                view_count INTEGER NOT NULL,
                view_count_sent INTEGER DEFAULT 0,
                view_count_delivered INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                price REAL NOT NULL,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                priority TEXT DEFAULT 'normal',
                notes TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Order progress tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views_sent INTEGER DEFAULT 0,
                views_delivered INTEGER DEFAULT 0,
                progress_percent REAL DEFAULT 0,
                status TEXT,
                details TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
        ''')
        
        # Order methods used
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                method_name TEXT NOT NULL,
                views_sent INTEGER DEFAULT 0,
                views_delivered INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
        ''')
        
        # Failed orders retry queue
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_retry_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                original_status TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                next_retry_at TIMESTAMP,
                retry_reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
        ''')
        
        # Bulk orders (multiple videos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bulk_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bulk_order_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                total_orders INTEGER DEFAULT 0,
                completed_orders INTEGER DEFAULT 0,
                failed_orders INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                total_price REAL DEFAULT 0,
                status TEXT DEFAULT 'processing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        # Bulk order items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bulk_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bulk_order_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                video_url TEXT NOT NULL,
                view_count INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (bulk_order_id) REFERENCES bulk_orders (id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
        ''')
        
        # Recurring orders (subscription-like)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recurring_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                video_url TEXT NOT NULL,
                view_count INTEGER NOT NULL,
                frequency TEXT NOT NULL,
                next_delivery TIMESTAMP NOT NULL,
                total_deliveries INTEGER DEFAULT 0,
                completed_deliveries INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Order analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_duration REAL,
                avg_views_per_hour REAL,
                peak_delivery_time TIMESTAMP,
                success_rate REAL,
                methods_used TEXT,
                delivery_pattern TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
                UNIQUE(order_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Order database initialized at {self.db_path}")
    
    def generate_order_id(self) -> str:
        """Generate unique order ID"""
        return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    def create_order(self, user_id: int, video_url: str, view_count: int, 
                    price: float, **kwargs) -> Optional[str]:
        """Create new order"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            order_id = self.generate_order_id()
            video_id = kwargs.get('video_id')
            payment_method = kwargs.get('payment_method')
            priority = kwargs.get('priority', 'normal')
            notes = kwargs.get('notes')
            metadata = json.dumps(kwargs.get('metadata', {}))
            
            cursor.execute('''
                INSERT INTO orders 
                (order_id, user_id, video_url, video_id, view_count, price, 
                 payment_method, priority, notes, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, user_id, video_url, video_id, view_count, price,
                  payment_method, priority, notes, metadata))
            
            order_db_id = cursor.lastrowid
            
            # Create initial progress entry
            cursor.execute('''
                INSERT INTO order_progress 
                (order_id, progress_percent, status)
                VALUES (?, 0, 'created')
            ''', (order_db_id,))
            
            conn.commit()
            logger.info(f"Order created: {order_id} for user {user_id}")
            return order_id
        except sqlite3.Error as e:
            logger.error(f"Error creating order: {e}")
            return None
        finally:
            conn.close()
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by order ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
            row = cursor.fetchone()
            
            if row:
                order = dict(row)
                # Parse metadata if exists
                if order.get('metadata'):
                    try:
                        order['metadata'] = json.loads(order['metadata'])
                    except:
                        order['metadata'] = {}
                return order
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting order: {e}")
            return None
        finally:
            conn.close()
    
    def get_user_orders(self, user_id: int, limit: int = 50, 
                       offset: int = 0) -> List[Dict]:
        """Get all orders for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM orders 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            rows = cursor.fetchall()
            orders = []
            for row in rows:
                order = dict(row)
                if order.get('metadata'):
                    try:
                        order['metadata'] = json.loads(order['metadata'])
                    except:
                        order['metadata'] = {}
                orders.append(order)
            return orders
        except sqlite3.Error as e:
            logger.error(f"Error getting user orders: {e}")
            return []
        finally:
            conn.close()
    
    def update_order_status(self, order_id: str, status: str, 
                          **kwargs) -> bool:
        """Update order status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            values = [status]
            
            # Handle special status updates
            if status == 'processing' and not kwargs.get('started_at'):
                updates.append("started_at = CURRENT_TIMESTAMP")
            elif status == 'completed' and not kwargs.get('completed_at'):
                updates.append("completed_at = CURRENT_TIMESTAMP")
            elif status == 'cancelled' and not kwargs.get('cancelled_at'):
                updates.append("cancelled_at = CURRENT_TIMESTAMP")
            
            # Add view counts if provided
            if 'view_count_sent' in kwargs:
                updates.append("view_count_sent = ?")
                values.append(kwargs['view_count_sent'])
            
            if 'view_count_delivered' in kwargs:
                updates.append("view_count_delivered = ?")
                values.append(kwargs['view_count_delivered'])
            
            if 'payment_status' in kwargs:
                updates.append("payment_status = ?")
                values.append(kwargs['payment_status'])
            
            values.append(order_id)
            
            query = f'''
                UPDATE orders 
                SET {', '.join(updates)}
                WHERE order_id = ?
            '''
            
            cursor.execute(query, values)
            
            # Log progress
            if cursor.rowcount > 0:
                cursor.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,))
                order_db_id = cursor.fetchone()[0]
                
                progress_percent = 0
                if status == 'completed':
                    progress_percent = 100
                elif status == 'processing':
                    progress_percent = 10
                
                cursor.execute('''
                    INSERT INTO order_progress 
                    (order_id, progress_percent, status, details)
                    VALUES (?, ?, ?, ?)
                ''', (order_db_id, progress_percent, status, 
                     json.dumps(kwargs.get('details', {}))))
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating order status: {e}")
            return False
        finally:
            conn.close()
    
    def update_order_progress(self, order_id: str, views_sent: int = None,
                            views_delivered: int = None, 
                            progress_percent: float = None,
                            status: str = None, details: Dict = None) -> bool:
        """Update order progress"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get order database ID
            cursor.execute('SELECT id, view_count FROM orders WHERE order_id = ?', (order_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            order_db_id, total_views = result
            
            # Calculate progress if not provided
            if progress_percent is None and views_delivered is not None:
                progress_percent = (views_delivered / total_views) * 100
            
            # Update order if view counts provided
            if views_sent is not None or views_delivered is not None:
                order_updates = []
                order_values = []
                
                if views_sent is not None:
                    order_updates.append("view_count_sent = ?")
                    order_values.append(views_sent)
                
                if views_delivered is not None:
                    order_updates.append("view_count_delivered = ?")
                    order_values.append(views_delivered)
                
                if order_updates:
                    order_updates.append("updated_at = CURRENT_TIMESTAMP")
                    order_values.append(order_id)
                    
                    query = f'''
                        UPDATE orders 
                        SET {', '.join(order_updates)}
                        WHERE id = ?
                    '''
                    cursor.execute(query, order_values)
            
            # Log progress
            cursor.execute('''
                INSERT INTO order_progress 
                (order_id, timestamp, views_sent, views_delivered, 
                 progress_percent, status, details)
                VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
            ''', (order_db_id, views_sent, views_delivered, 
                 progress_percent, status, 
                 json.dumps(details) if details else None))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating order progress: {e}")
            return False
        finally:
            conn.close()
    
    def add_order_method(self, order_id: str, method_name: str, 
                        views_sent: int = 0, views_delivered: int = 0,
                        success_rate: float = 0, status: str = 'started') -> bool:
        """Add or update order method"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get order database ID
            cursor.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            order_db_id = result[0]
            
            # Check if method already exists
            cursor.execute('''
                SELECT id FROM order_methods 
                WHERE order_id = ? AND method_name = ?
            ''', (order_db_id, method_name))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing method
                method_id = existing[0]
                cursor.execute('''
                    UPDATE order_methods 
                    SET views_sent = ?, views_delivered = ?, 
                        success_rate = ?, end_time = CURRENT_TIMESTAMP, status = ?
                    WHERE id = ?
                ''', (views_sent, views_delivered, success_rate, status, method_id))
            else:
                # Insert new method
                cursor.execute('''
                    INSERT INTO order_methods 
                    (order_id, method_name, views_sent, views_delivered, 
                     success_rate, start_time, status)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ''', (order_db_id, method_name, views_sent, views_delivered, 
                     success_rate, status))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding order method: {e}")
            return False
        finally:
            conn.close()
    
    def get_order_progress(self, order_id: str, limit: int = 20) -> List[Dict]:
        """Get order progress history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get order database ID
            cursor.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,))
            result = cursor.fetchone()
            if not result:
                return []
            
            order_db_id = result[0]
            
            cursor.execute('''
                SELECT * FROM order_progress 
                WHERE order_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (order_db_id, limit))
            
            rows = cursor.fetchall()
            progress = []
            for row in rows:
                item = dict(row)
                if item.get('details'):
                    try:
                        item['details'] = json.loads(item['details'])
                    except:
                        item['details'] = {}
                progress.append(item)
            
            return progress
        except sqlite3.Error as e:
            logger.error(f"Error getting order progress: {e}")
            return []
        finally:
            conn.close()
    
    def get_order_methods(self, order_id: str) -> List[Dict]:
        """Get methods used for an order"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get order database ID
            cursor.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,))
            result = cursor.fetchone()
            if not result:
                return []
            
            order_db_id = result[0]
            
            cursor.execute('''
                SELECT * FROM order_methods 
                WHERE order_id = ? 
                ORDER BY start_time
            ''', (order_db_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting order methods: {e}")
            return []
        finally:
            conn.close()
    
    def get_orders_by_status(self, status: str, limit: int = 100) -> List[Dict]:
        """Get orders by status"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM orders 
                WHERE status = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (status, limit))
            
            rows = cursor.fetchall()
            orders = []
            for row in rows:
                order = dict(row)
                if order.get('metadata'):
                    try:
                        order['metadata'] = json.loads(order['metadata'])
                    except:
                        order['metadata'] = {}
                orders.append(order)
            return orders
        except sqlite3.Error as e:
            logger.error(f"Error getting orders by status: {e}")
            return []
        finally:
            conn.close()
    
    def search_orders(self, query: str, limit: int = 50) -> List[Dict]:
        """Search orders by video URL, order ID, or video ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM orders 
                WHERE order_id LIKE ? OR video_url LIKE ? OR video_id LIKE ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            rows = cursor.fetchall()
            orders = []
            for row in rows:
                order = dict(row)
                if order.get('metadata'):
                    try:
                        order['metadata'] = json.loads(order['metadata'])
                    except:
                        order['metadata'] = {}
                orders.append(order)
            return orders
        except sqlite3.Error as e:
            logger.error(f"Error searching orders: {e}")
            return []
        finally:
            conn.close()
    
    def get_order_stats(self, order_id: str = None, user_id: int = None) -> Dict:
        """Get order statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            if order_id:
                # Single order stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_progress_entries,
                        MIN(timestamp) as first_update,
                        MAX(timestamp) as last_update,
                        AVG(progress_percent) as avg_progress
                    FROM order_progress op
                    JOIN orders o ON op.order_id = o.id
                    WHERE o.order_id = ?
                ''', (order_id,))
                
                row = cursor.fetchone()
                if row:
                    stats['progress_entries'] = row[0]
                    stats['first_update'] = row[1]
                    stats['last_update'] = row[2]
                    stats['avg_progress'] = row[3]
                
                # Methods stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_methods,
                        SUM(views_sent) as total_sent,
                        SUM(views_delivered) as total_delivered,
                        AVG(success_rate) as avg_success_rate
                    FROM order_methods om
                    JOIN orders o ON om.order_id = o.id
                    WHERE o.order_id = ?
                ''', (order_id,))
                
                row = cursor.fetchone()
                if row:
                    stats['total_methods'] = row[0]
                    stats['total_sent'] = row[1] or 0
                    stats['total_delivered'] = row[2] or 0
                    stats['avg_success_rate'] = row[3] or 0
            
            if user_id:
                # User order stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(view_count) as total_views_ordered,
                        SUM(view_count_delivered) as total_views_delivered,
                        SUM(price) as total_spent,
                        AVG(view_count_delivered * 100.0 / view_count) as avg_success_rate
                    FROM orders 
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    stats['total_orders'] = row[0] or 0
                    stats['total_views_ordered'] = row[1] or 0
                    stats['total_views_delivered'] = row[2] or 0
                    stats['total_spent'] = row[3] or 0
                    stats['avg_success_rate'] = row[4] or 0
                
                # Status breakdown
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM orders 
                    WHERE user_id = ?
                    GROUP BY status
                ''', (user_id,))
                
                stats['status_breakdown'] = dict(cursor.fetchall())
            
            # Global stats (if no specific query)
            if not order_id and not user_id:
                cursor.execute('SELECT COUNT(*) FROM orders')
                stats['total_orders'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT SUM(price) FROM orders')
                stats['total_revenue'] = cursor.fetchone()[0] or 0
                
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM orders 
                    GROUP BY status
                ''')
                stats['status_breakdown'] = dict(cursor.fetchall())
                
                cursor.execute('''
                    SELECT DATE(created_at) as date, COUNT(*) as count 
                    FROM orders 
                    GROUP BY DATE(created_at) 
                    ORDER BY date DESC 
                    LIMIT 7
                ''')
                stats['last_7_days'] = dict(cursor.fetchall())
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting order stats: {e}")
            return {}
        finally:
            conn.close()
    
    def queue_order_retry(self, order_id: str, reason: str, 
                         max_retries: int = 3) -> bool:
        """Queue order for retry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get order database ID and current status
            cursor.execute('''
                SELECT id, status FROM orders WHERE order_id = ?
            ''', (order_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            order_db_id, current_status = result
            
            # Calculate next retry time (incrementing delay)
            from datetime import datetime, timedelta
            cursor.execute('''
                SELECT retry_count FROM order_retry_queue 
                WHERE order_id = ? AND status = 'pending'
            ''', (order_db_id,))
            
            retry_row = cursor.fetchone()
            if retry_row:
                retry_count = retry_row[0] + 1
                # Update existing retry
                next_retry = datetime.now() + timedelta(minutes=retry_count * 5)
                cursor.execute('''
                    UPDATE order_retry_queue 
                    SET retry_count = ?, next_retry_at = ?, retry_reason = ?
                    WHERE order_id = ? AND status = 'pending'
                ''', (retry_count, next_retry.isoformat(), reason, order_db_id))
            else:
                # Create new retry entry
                retry_count = 1
                next_retry = datetime.now() + timedelta(minutes=5)
                cursor.execute('''
                    INSERT INTO order_retry_queue 
                    (order_id, original_status, retry_count, max_retries, 
                     next_retry_at, retry_reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (order_db_id, current_status, retry_count, max_retries,
                     next_retry.isoformat(), reason))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error queuing order retry: {e}")
            return False
        finally:
            conn.close()
    
    def get_pending_retries(self, limit: int = 20) -> List[Dict]:
        """Get pending order retries"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT q.*, o.order_id, o.video_url, o.view_count
                FROM order_retry_queue q
                JOIN orders o ON q.order_id = o.id
                WHERE q.status = 'pending' 
                AND q.next_retry_at <= CURRENT_TIMESTAMP
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting pending retries: {e}")
            return []
        finally:
            conn.close()
    
    def create_bulk_order(self, user_id: int, items: List[Dict]) -> Optional[str]:
        """Create bulk order with multiple videos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            bulk_order_id = f"BULK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            total_views = sum(item.get('view_count', 0) for item in items)
            total_price = sum(item.get('price', 0) for item in items)
            
            cursor.execute('''
                INSERT INTO bulk_orders 
                (bulk_order_id, user_id, total_orders, total_views, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (bulk_order_id, user_id, len(items), total_views, total_price))
            
            bulk_db_id = cursor.lastrowid
            
            # Create individual orders
            for item in items:
                order_id = self.create_order(
                    user_id=user_id,
                    video_url=item['video_url'],
                    view_count=item['view_count'],
                    price=item.get('price', 0),
                    video_id=item.get('video_id'),
                    priority='bulk'
                )
                
                if order_id:
                    # Get order database ID
                    cursor.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,))
                    order_db_id = cursor.fetchone()[0]
                    
                    # Link to bulk order
                    cursor.execute('''
                        INSERT INTO bulk_order_items 
                        (bulk_order_id, order_id, video_url, view_count)
                        VALUES (?, ?, ?, ?)
                    ''', (bulk_db_id, order_db_id, item['video_url'], item['view_count']))
            
            conn.commit()
            return bulk_order_id
        except sqlite3.Error as e:
            logger.error(f"Error creating bulk order: {e}")
            return None
        finally:
            conn.close()
    
    def update_bulk_order_status(self, bulk_order_id: str) -> bool:
        """Update bulk order status based on individual orders"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get bulk order ID
            cursor.execute('''
                SELECT bo.id, bo.total_orders,
                       COUNT(CASE WHEN o.status = 'completed' THEN 1 END) as completed,
                       COUNT(CASE WHEN o.status = 'failed' THEN 1 END) as failed
                FROM bulk_orders bo
                JOIN bulk_order_items boi ON bo.id = boi.bulk_order_id
                JOIN orders o ON boi.order_id = o.id
                WHERE bo.bulk_order_id = ?
                GROUP BY bo.id
            ''', (bulk_order_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            bulk_db_id, total_orders, completed, failed = result
            
            # Update bulk order
            new_status = 'processing'
            if completed == total_orders:
                new_status = 'completed'
            elif failed > 0:
                new_status = 'partial'
            
            cursor.execute('''
                UPDATE bulk_orders 
                SET completed_orders = ?, failed_orders = ?, status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (completed, failed, new_status, bulk_db_id))
            
            if new_status == 'completed':
                cursor.execute('''
                    UPDATE bulk_orders 
                    SET completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (bulk_db_id,))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating bulk order status: {e}")
            return False
        finally:
            conn.close()
    
    def create_recurring_order(self, user_id: int, video_url: str, 
                              view_count: int, frequency: str) -> Optional[str]:
        """Create recurring order"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            recurring_id = f"REC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Calculate next delivery based on frequency
            from datetime import datetime, timedelta
            next_delivery = datetime.now()
            
            if frequency == 'daily':
                next_delivery += timedelta(days=1)
            elif frequency == 'weekly':
                next_delivery += timedelta(weeks=1)
            elif frequency == 'monthly':
                # Simplified: add 30 days
                next_delivery += timedelta(days=30)
            else:
                next_delivery += timedelta(days=1)
            
            cursor.execute('''
                INSERT INTO recurring_orders 
                (recurring_id, user_id, video_url, view_count, 
                 frequency, next_delivery)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (recurring_id, user_id, video_url, view_count, 
                 frequency, next_delivery.isoformat()))
            
            conn.commit()
            return recurring_id
        except sqlite3.Error as e:
            logger.error(f"Error creating recurring order: {e}")
            return None
        finally:
            conn.close()
    
    def process_recurring_orders(self) -> List[str]:
        """Process due recurring orders"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get due recurring orders
            cursor.execute('''
                SELECT recurring_id, user_id, video_url, view_count, id
                FROM recurring_orders 
                WHERE status = 'active' 
                AND next_delivery <= CURRENT_TIMESTAMP
            ''')
            
            due_orders = cursor.fetchall()
            created_orders = []
            
            for recurring_id, user_id, video_url, view_count, rec_id in due_orders:
                # Create new order
                order_id = self.create_order(
                    user_id=user_id,
                    video_url=video_url,
                    view_count=view_count,
                    price=0,  # Recurring orders might have different pricing
                    priority='recurring'
                )
                
                if order_id:
                    # Update recurring order
                    from datetime import datetime, timedelta
                    next_delivery = datetime.now()
                    
                    cursor.execute('''
                        SELECT frequency FROM recurring_orders WHERE id = ?
                    ''', (rec_id,))
                    
                    frequency = cursor.fetchone()[0]
                    
                    if frequency == 'daily':
                        next_delivery += timedelta(days=1)
                    elif frequency == 'weekly':
                        next_delivery += timedelta(weeks=1)
                    elif frequency == 'monthly':
                        next_delivery += timedelta(days=30)
                    
                    cursor.execute('''
                        UPDATE recurring_orders 
                        SET next_delivery = ?, 
                            total_deliveries = total_deliveries + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (next_delivery.isoformat(), rec_id))
                    
                    created_orders.append(order_id)
            
            conn.commit()
            return created_orders
        except sqlite3.Error as e:
            logger.error(f"Error processing recurring orders: {e}")
            return []
        finally:
            conn.close()
    
    def save_order_analytics(self, order_id: str, analytics_data: Dict) -> bool:
        """Save order analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get order database ID
            cursor.execute('SELECT id FROM orders WHERE order_id = ?', (order_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            order_db_id = result[0]
            
            cursor.execute('''
                INSERT OR REPLACE INTO order_analytics 
                (order_id, start_time, end_time, total_duration, 
                 avg_views_per_hour, peak_delivery_time, success_rate,
                 methods_used, delivery_pattern)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_db_id,
                analytics_data.get('start_time'),
                analytics_data.get('end_time'),
                analytics_data.get('total_duration'),
                analytics_data.get('avg_views_per_hour'),
                analytics_data.get('peak_delivery_time'),
                analytics_data.get('success_rate'),
                json.dumps(analytics_data.get('methods_used', [])),
                json.dumps(analytics_data.get('delivery_pattern', {}))
            ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving order analytics: {e}")
            return False
        finally:
            conn.close()
    
    def export_order_data(self, order_id: str) -> Dict:
        """Export complete order data"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get order
            order = self.get_order(order_id)
            if not order:
                return {}
            
            data = {'order': order}
            
            # Get progress
            data['progress'] = self.get_order_progress(order_id, limit=100)
            
            # Get methods
            data['methods'] = self.get_order_methods(order_id)
            
            # Get analytics if exists
            cursor.execute('''
                SELECT * FROM order_analytics oa
                JOIN orders o ON oa.order_id = o.id
                WHERE o.order_id = ?
            ''', (order_id,))
            
            analytics = cursor.fetchone()
            if analytics:
                data['analytics'] = dict(analytics)
                # Parse JSON fields
                if data['analytics'].get('methods_used'):
                    try:
                        data['analytics']['methods_used'] = json.loads(data['analytics']['methods_used'])
                    except:
                        data['analytics']['methods_used'] = []
                if data['analytics'].get('delivery_pattern'):
                    try:
                        data['analytics']['delivery_pattern'] = json.loads(data['analytics']['delivery_pattern'])
                    except:
                        data['analytics']['delivery_pattern'] = {}
            
            return data
        except sqlite3.Error as e:
            logger.error(f"Error exporting order data: {e}")
            return {}
        finally:
            conn.close()
    
    def cleanup_old_data(self, days: int = 30) -> Dict:
        """Cleanup old order data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Archive completed orders older than X days
            cursor.execute('''
                SELECT COUNT(*) FROM orders 
                WHERE status = 'completed' 
                AND completed_at <= datetime('now', ?)
            ''', (f'-{days} days',))
            
            old_orders = cursor.fetchone()[0]
            stats['old_orders'] = old_orders
            
            # In production, you would archive instead of delete
            # For demo, we'll just count
            
            # Cleanup old progress entries (keep only 10 per order)
            cursor.execute('''
                DELETE FROM order_progress 
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (
                            PARTITION BY order_id ORDER BY timestamp DESC
                        ) as rn
                        FROM order_progress
                    ) WHERE rn > 10
                )
            ''')
            
            stats['cleaned_progress'] = cursor.rowcount
            
            conn.commit()
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {}
        finally:
            conn.close()

# Singleton instance
order_db = OrderDatabase()

# Quick test
if __name__ == "__main__":
    # Test database
    db = OrderDatabase()
    
    # Create test order
    order_id = db.create_order(
        user_id=123456789,
        video_url="https://tiktok.com/@test/video/123",
        view_count=1000,
        price=5.0
    )
    
    if order_id:
        print(f"Order created: {order_id}")
        
        # Get order
        order = db.get_order(order_id)
        print(f"Order details: {order}")
        
        # Update progress
        db.update_order_progress(order_id, views_sent=100, views_delivered=80, 
                               progress_percent=8, status="processing")
        
        # Add method
        db.add_order_method(order_id, "browser_automation", 100, 80, 80.0, "completed")
        
        # Get progress
        progress = db.get_order_progress(order_id)
        print(f"Progress: {progress}")
        
        # Get methods
        methods = db.get_order_methods(order_id)
        print(f"Methods: {methods}")
        
        # Get stats
        stats = db.get_order_stats(order_id=order_id)
        print(f"Stats: {stats}")
    
    print("✅ Order database test completed successfully")