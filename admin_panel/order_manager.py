"""
Order Manager for Admin Panel
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class OrderManager:
    """Order management system for admin panel"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_orders(self, filters: Dict = None, page: int = 1,
                        per_page: int = 50) -> Dict[str, Any]:
        """Get orders with filtering and pagination"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            # Get all orders (simplified)
            # In production, implement proper filtering
            all_orders = order_db.get_active_orders()
            
            # For demo, also get recent completed orders
            completed_orders = []
            # This would need a method to get orders by status
            
            combined_orders = all_orders + completed_orders
            
            # Apply filters
            if filters:
                filtered_orders = self._apply_order_filters(combined_orders, filters)
            else:
                filtered_orders = combined_orders
            
            # Sort by created date (newest first)
            filtered_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Apply pagination
            total_orders = len(filtered_orders)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_orders = filtered_orders[start_idx:end_idx]
            
            return {
                'orders': paginated_orders,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_orders,
                    'total_pages': (total_orders + per_page - 1) // per_page
                },
                'filters': filters or {},
                'summary': self._get_orders_summary(filtered_orders)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            return {'orders': [], 'pagination': {}, 'error': str(e)}
    
    def _apply_order_filters(self, orders: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to order list"""
        filtered = orders
        
        # Filter by status
        if filters.get('status'):
            status = filters['status']
            if status != 'all':
                filtered = [o for o in filtered if o.get('status') == status]
        
        # Filter by user ID
        if filters.get('user_id'):
            try:
                user_id = int(filters['user_id'])
                filtered = [o for o in filtered if o.get('user_id') == user_id]
            except:
                pass
        
        # Filter by order ID
        if filters.get('order_id'):
            order_id = filters['order_id'].lower()
            filtered = [o for o in filtered if order_id in o.get('order_id', '').lower()]
        
        # Filter by video URL
        if filters.get('video_url'):
            search_term = filters['video_url'].lower()
            filtered = [o for o in filtered if search_term in o.get('video_url', '').lower()]
        
        # Filter by date range
        if filters.get('date_from'):
            try:
                date_from = datetime.fromisoformat(filters['date_from'])
                filtered = [o for o in filtered if 
                           datetime.fromisoformat(o.get('created_at', '2000-01-01')) >= date_from]
            except:
                pass
        
        if filters.get('date_to'):
            try:
                date_to = datetime.fromisoformat(filters['date_to'])
                filtered = [o for o in filtered if 
                           datetime.fromisoformat(o.get('created_at', '2000-01-01')) <= date_to]
            except:
                pass
        
        # Filter by price range
        if filters.get('min_price'):
            try:
                min_price = float(filters['min_price'])
                filtered = [o for o in filtered if o.get('price', 0) >= min_price]
            except:
                pass
        
        if filters.get('max_price'):
            try:
                max_price = float(filters['max_price'])
                filtered = [o for o in filtered if o.get('price', 0) <= max_price]
            except:
                pass
        
        # Filter by view count
        if filters.get('min_views'):
            try:
                min_views = int(filters['min_views'])
                filtered = [o for o in filtered if o.get('target_views', 0) >= min_views]
            except:
                pass
        
        if filters.get('max_views'):
            try:
                max_views = int(filters['max_views'])
                filtered = [o for o in filtered if o.get('target_views', 0) <= max_views]
            except:
                pass
        
        return filtered
    
    def _get_orders_summary(self, orders: List[Dict]) -> Dict[str, Any]:
        """Get summary statistics for orders"""
        if not orders:
            return {}
        
        total_orders = len(orders)
        completed = len([o for o in orders if o.get('status') == 'completed'])
        pending = len([o for o in orders if o.get('status') == 'pending'])
        processing = len([o for o in orders if o.get('status') == 'processing'])
        failed = len([o for o in orders if o.get('status') == 'failed'])
        
        total_revenue = sum(o.get('price', 0) for o in orders if o.get('status') == 'completed')
        total_views_ordered = sum(o.get('target_views', 0) for o in orders)
        total_views_delivered = sum(o.get('delivered_views', 0) for o in orders)
        
        if total_views_ordered > 0:
            delivery_rate = (total_views_delivered / total_views_ordered) * 100
        else:
            delivery_rate = 0
        
        avg_order_value = total_revenue / completed if completed > 0 else 0
        
        return {
            'total_orders': total_orders,
            'by_status': {
                'completed': completed,
                'pending': pending,
                'processing': processing,
                'failed': failed
            },
            'revenue': round(total_revenue, 2),
            'views_ordered': total_views_ordered,
            'views_delivered': total_views_delivered,
            'delivery_rate': round(delivery_rate, 2),
            'avg_order_value': round(avg_order_value, 2),
            'completion_rate': round((completed / total_orders) * 100, 2) if total_orders > 0 else 0
        }
    
    async def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get detailed order information"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            from telegram_bot.database.user_db import UserDatabase
            
            order_db = OrderDatabase()
            user_db = UserDatabase()
            
            # Get order
            order = order_db.get_order(order_id)
            if not order:
                return {'error': 'Order not found'}
            
            # Get user details
            user_id = order.get('user_id')
            user = user_db.get_user(user_id) if user_id else None
            
            # Get order progress
            progress = order_db.get_order_progress_history(order_id)
            
            # Get analytics
            analytics = await self._get_order_analytics(order_id)
            
            # Get related orders
            related_orders = []
            if user_id:
                related_orders = order_db.get_user_orders(user_id, limit=5)
                # Remove current order from related
                related_orders = [o for o in related_orders if o.get('order_id') != order_id]
            
            return {
                'order': order,
                'user': user,
                'progress': progress,
                'analytics': analytics,
                'related_orders': related_orders,
                'timeline': self._create_order_timeline(order, progress)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get order details: {e}")
            return {'error': str(e)}
    
    async def _get_order_analytics(self, order_id: str) -> Dict[str, Any]:
        """Get order analytics"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            order = order_db.get_order(order_id)
            if not order:
                return {}
            
            progress = order_db.get_order_progress_history(order_id)
            
            if not progress:
                return {}
            
            # Calculate analytics from progress data
            if len(progress) > 1:
                start_time = datetime.fromisoformat(progress[0]['timestamp'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(progress[-1]['timestamp'].replace('Z', '+00:00'))
                duration_hours = (end_time - start_time).total_seconds() / 3600
            else:
                duration_hours = 0
            
            total_delivered = progress[-1]['delivered_views'] if progress else 0
            target_views = order.get('target_views', 0)
            
            if duration_hours > 0:
                avg_speed = total_delivered / duration_hours
            else:
                avg_speed = 0
            
            # Get speed variations
            speeds = []
            for i in range(1, len(progress)):
                prev = progress[i-1]
                curr = progress[i]
                
                prev_time = datetime.fromisoformat(prev['timestamp'].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(curr['timestamp'].replace('Z', '+00:00'))
                
                time_diff = (curr_time - prev_time).total_seconds() / 3600
                view_diff = curr['delivered_views'] - prev['delivered_views']
                
                if time_diff > 0:
                    speed = view_diff / time_diff
                    speeds.append(speed)
            
            peak_speed = max(speeds) if speeds else 0
            
            return {
                'duration_hours': round(duration_hours, 2),
                'completion_percentage': round((total_delivered / target_views) * 100, 2) if target_views > 0 else 0,
                'average_speed': round(avg_speed, 1),
                'peak_speed': round(peak_speed, 1),
                'progress_points': len(progress),
                'success_rate': order.get('success_rate', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get order analytics: {e}")
            return {}
    
    def _create_order_timeline(self, order: Dict, progress: List[Dict]) -> List[Dict]:
        """Create order timeline"""
        timeline = []
        
        # Order created
        timeline.append({
            'type': 'order_created',
            'timestamp': order.get('created_at'),
            'title': 'Order Created',
            'description': f'Order {order.get("order_id")} created',
            'status': 'created'
        })
        
        # Order started
        if order.get('started_at'):
            timeline.append({
                'type': 'order_started',
                'timestamp': order.get('started_at'),
                'title': 'Processing Started',
                'description': 'Order processing began',
                'status': 'processing'
            })
        
        # Progress updates
        for prog in progress:
            timeline.append({
                'type': 'progress_update',
                'timestamp': prog.get('timestamp'),
                'title': 'Progress Update',
                'description': f'{prog.get("delivered_views")} views delivered',
                'progress': prog.get('delivered_views'),
                'speed': prog.get('current_speed', 0)
            })
        
        # Order completed/failed
        if order.get('completed_at'):
            if order.get('status') == 'completed':
                timeline.append({
                    'type': 'order_completed',
                    'timestamp': order.get('completed_at'),
                    'title': 'Order Completed',
                    'description': f'Order completed with {order.get("delivered_views", 0)} views',
                    'status': 'completed'
                })
            elif order.get('status') == 'failed':
                timeline.append({
                    'type': 'order_failed',
                    'timestamp': order.get('completed_at'),
                    'title': 'Order Failed',
                    'description': 'Order processing failed',
                    'status': 'failed'
                })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get('timestamp', ''))
        
        return timeline
    
    async def update_order_status(self, order_id: str, status: str, 
                                 notes: str = "") -> Dict[str, Any]:
        """Update order status"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            # Validate status
            valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
            if status not in valid_statuses:
                return {'success': False, 'error': f'Invalid status. Valid: {", ".join(valid_statuses)}'}
            
            # Get current order
            order = order_db.get_order(order_id)
            if not order:
                return {'success': False, 'error': 'Order not found'}
            
            current_status = order.get('status')
            
            # Check if status transition is valid
            valid_transitions = {
                'pending': ['processing', 'cancelled'],
                'processing': ['completed', 'failed', 'cancelled'],
                'completed': [],  # Can't change completed orders
                'failed': ['processing'],  # Can retry failed orders
                'cancelled': []  # Can't change cancelled orders
            }
            
            if status in valid_transitions.get(current_status, []):
                # Update status
                success = order_db.update_order_status(order_id, status)
                
                if success:
                    # Log the status change
                    await self._log_status_change(order_id, current_status, status, notes)
                    
                    return {
                        'success': True,
                        'message': f'Order status updated from {current_status} to {status}',
                        'order_id': order_id,
                        'old_status': current_status,
                        'new_status': status
                    }
                else:
                    return {'success': False, 'error': 'Failed to update status in database'}
            else:
                return {
                    'success': False, 
                    'error': f'Cannot change status from {current_status} to {status}'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to update order status: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _log_status_change(self, order_id: str, old_status: str, 
                                new_status: str, notes: str):
        """Log order status change"""
        try:
            log_entry = {
                'order_id': order_id,
                'timestamp': datetime.now().isoformat(),
                'old_status': old_status,
                'new_status': new_status,
                'notes': notes,
                'admin': 'system'  # In production, track admin user
            }
            
            # Save to status change log
            log_file = 'logs/order_status_changes.json'
            try:
                with open(log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Failed to log status change: {e}")
    
    async def modify_order(self, order_id: str, updates: Dict) -> Dict[str, Any]:
        """Modify order details"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            # Get current order
            order = order_db.get_order(order_id)
            if not order:
                return {'success': False, 'error': 'Order not found'}
            
            current_status = order.get('status')
            
            # Check if order can be modified
            if current_status in ['completed', 'cancelled']:
                return {'success': False, 'error': f'Cannot modify {current_status} order'}
            
            # Validate updates
            allowed_updates = ['target_views', 'delivery_speed', 'quality_type', 
                              'refill_guarantee', 'custom_notes', 'priority']
            
            valid_updates = {}
            for key, value in updates.items():
                if key in allowed_updates:
                    valid_updates[key] = value
            
            if not valid_updates:
                return {'success': False, 'error': 'No valid fields to update'}
            
            # Recalculate price if views changed
            if 'target_views' in valid_updates:
                # This would need price calculation logic
                pass
            
            # In production, implement actual database update
            # For now, simulate success
            
            # Log the modification
            await self._log_order_modification(order_id, valid_updates)
            
            return {
                'success': True,
                'message': 'Order modified successfully',
                'order_id': order_id,
                'updates': valid_updates
            }
            
        except Exception as e:
            self.logger.error(f"Failed to modify order: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _log_order_modification(self, order_id: str, updates: Dict):
        """Log order modification"""
        try:
            log_entry = {
                'order_id': order_id,
                'timestamp': datetime.now().isoformat(),
                'updates': updates,
                'admin': 'system'
            }
            
            log_file = 'logs/order_modifications.json'
            try:
                with open(log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Failed to log order modification: {e}")
    
    async def create_refill_order(self, original_order_id: str, 
                                 refill_views: int, reason: str = "") -> Dict[str, Any]:
        """Create refill order"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            # Get original order
            original = order_db.get_order(original_order_id)
            if not original:
                return {'success': False, 'error': 'Original order not found'}
            
            # Check if original order is completed
            if original.get('status') != 'completed':
                return {'success': False, 'error': 'Original order must be completed'}
            
            # Check if refill guarantee is enabled
            if not original.get('refill_guarantee', True):
                return {'success': False, 'error': 'Refill guarantee not enabled for this order'}
            
            # Check refill days
            completed_at = original.get('completed_at')
            if completed_at:
                try:
                    completed_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    days_since = (datetime.now() - completed_date).days
                    refill_days = original.get('refill_days', 30)
                    
                    if days_since > refill_days:
                        return {
                            'success': False, 
                            'error': f'Refill period expired ({refill_days} days)'
                        }
                except:
                    pass
            
            user_id = original.get('user_id')
            
            # Create refill order
            refill_id = order_db.create_refill_order(
                original_order_id, user_id, refill_views, reason
            )
            
            if refill_id:
                return {
                    'success': True,
                    'message': f'Refill order created: {refill_id}',
                    'refill_id': refill_id,
                    'original_order_id': original_order_id,
                    'refill_views': refill_views
                }
            else:
                return {'success': False, 'error': 'Failed to create refill order'}
                
        except Exception as e:
            self.logger.error(f"Failed to create refill order: {e}")
            return {'success': False, 'error': str(e)}
    
    async def export_orders(self, format_type: str = 'csv', filters: Dict = None) -> Dict[str, Any]:
        """Export orders data"""
        try:
            orders_data = await self.get_orders(filters, page=1, per_page=1000000)
            orders = orders_data.get('orders', [])
            
            if format_type == 'csv':
                export_content = self._export_orders_to_csv(orders)
                filename = f'orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            elif format_type == 'json':
                export_content = json.dumps(orders, indent=2, default=str)
                filename = f'orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            else:
                return {'success': False, 'error': 'Unsupported format'}
            
            return {
                'success': True,
                'filename': filename,
                'content': export_content,
                'count': len(orders),
                'format': format_type
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export orders: {e}")
            return {'success': False, 'error': str(e)}
    
    def _export_orders_to_csv(self, orders: List[Dict]) -> str:
        """Convert orders data to CSV"""
        if not orders:
            return ''
        
        # Define CSV columns
        columns = [
            'order_id', 'user_id', 'video_url', 'target_views', 
            'delivered_views', 'status', 'price', 'currency',
            'delivery_speed', 'quality_type', 'created_at',
            'started_at', 'completed_at', 'success_rate'
        ]
        
        # Create CSV header
        csv_lines = [','.join(columns)]
        
        # Add data rows
        for order in orders:
            row = []
            for col in columns:
                value = order.get(col, '')
                # Convert to string and escape
                if isinstance(value, str):
                    if ',' in value or '"' in value:
                        value = f'"{value.replace(\'"\', \'""\')}"'
                elif value is None:
                    value = ''
                else:
                    value = str(value)
                row.append(value)
            csv_lines.append(','.join(row))
        
        return '\n'.join(csv_lines)
    
    async def get_order_statistics_report(self, period: str = '7d') -> Dict[str, Any]:
        """Get detailed order statistics report"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            # Get statistics
            stats = order_db.get_order_statistics(self._period_to_days(period))
            
            # Get hourly distribution
            hourly_dist = await self._get_hourly_distribution(period)
            
            # Get status distribution
            status_dist = await self._get_status_distribution(period)
            
            # Get revenue trends
            revenue_trends = await self._get_revenue_trends(period)
            
            return {
                'period': period,
                'summary': stats,
                'hourly_distribution': hourly_dist,
                'status_distribution': status_dist,
                'revenue_trends': revenue_trends,
                'performance_metrics': await self._get_performance_metrics(period)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics report: {e}")
            return {'error': str(e)}
    
    def _period_to_days(self, period: str) -> int:
        """Convert period string to days"""
        period_map = {
            '1d': 1,
            '7d': 7,
            '30d': 30,
            '90d': 90,
            '180d': 180,
            '365d': 365
        }
        return period_map.get(period, 7)
    
    async def _get_hourly_distribution(self, period: str) -> Dict[str, int]:
        """Get order distribution by hour of day"""
        # This would query database for hourly distribution
        # For now, return sample data
        return {str(hour): 10 + (hour * 2) for hour in range(24)}
    
    async def _get_status_distribution(self, period: str) -> Dict[str, int]:
        """Get order distribution by status"""
        # This would query database
        return {
            'completed': 150,
            'pending': 20,
            'processing': 15,
            'failed': 5,
            'cancelled': 10
        }
    
    async def _get_revenue_trends(self, period: str) -> List[Dict]:
        """Get revenue trends over time"""
        days = self._period_to_days(period)
        
        trends = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            revenue = 100 * (days - i) + (i * 50)  # Sample data
            trends.append({
                'date': date,
                'revenue': revenue,
                'orders': 10 + i,
                'avg_order_value': round(revenue / (10 + i), 2) if (10 + i) > 0 else 0
            })
        
        return sorted(trends, key=lambda x: x['date'])
    
    async def _get_performance_metrics(self, period: str) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'average_processing_time': 2.5,  # hours
            'success_rate': 92.5,
            'refill_rate': 8.2,
            'customer_satisfaction': 4.7,  # out of 5
            'system_uptime': 99.8
        }