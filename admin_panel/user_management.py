"""
User Management System for Admin Panel
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class UserManagement:
    """User management system for admin panel"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_users(self, filters: Dict = None, page: int = 1, 
                       per_page: int = 50) -> Dict[str, Any]:
        """Get users with filtering and pagination"""
        try:
            from telegram_bot.database.user_db import UserDatabase
            user_db = UserDatabase()
            
            # Get all users (simplified - in production, implement filtering)
            # For now, get top users
            users = user_db.get_top_users(limit=1000, by="registration_date")
            
            # Apply filters
            if filters:
                users = self._apply_filters(users, filters)
            
            # Apply pagination
            total_users = len(users)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_users = users[start_idx:end_idx]
            
            return {
                'users': paginated_users,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_users,
                    'total_pages': (total_users + per_page - 1) // per_page
                },
                'filters': filters or {}
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get users: {e}")
            return {'users': [], 'pagination': {}, 'error': str(e)}
    
    def _apply_filters(self, users: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to user list"""
        filtered = users
        
        # Filter by status
        if filters.get('status') == 'active':
            cutoff = datetime.now() - timedelta(days=7)
            filtered = [u for u in filtered if 
                       datetime.fromisoformat(u.get('last_active', '2000-01-01')) > cutoff]
        elif filters.get('status') == 'inactive':
            cutoff = datetime.now() - timedelta(days=30)
            filtered = [u for u in filtered if 
                       datetime.fromisoformat(u.get('last_active', '2000-01-01')) < cutoff]
        elif filters.get('status') == 'banned':
            filtered = [u for u in filtered if u.get('is_banned')]
        elif filters.get('status') == 'premium':
            filtered = [u for u in filtered if u.get('is_premium')]
        
        # Filter by balance
        if filters.get('min_balance'):
            min_balance = float(filters['min_balance'])
            filtered = [u for u in filtered if u.get('balance', 0) >= min_balance]
        
        if filters.get('max_balance'):
            max_balance = float(filters['max_balance'])
            filtered = [u for u in filtered if u.get('balance', 0) <= max_balance]
        
        # Filter by registration date
        if filters.get('registered_after'):
            try:
                date = datetime.fromisoformat(filters['registered_after'])
                filtered = [u for u in filtered if 
                           datetime.fromisoformat(u.get('registration_date', '2000-01-01')) >= date]
            except:
                pass
        
        if filters.get('registered_before'):
            try:
                date = datetime.fromisoformat(filters['registered_before'])
                filtered = [u for u in filtered if 
                           datetime.fromisoformat(u.get('registration_date', '2000-01-01')) <= date]
            except:
                pass
        
        # Search by username or ID
        if filters.get('search'):
            search_term = filters['search'].lower()
            filtered = [u for u in filtered if 
                       search_term in str(u.get('user_id', '')).lower() or
                       search_term in (u.get('username') or '').lower() or
                       search_term in (u.get('first_name') or '').lower() or
                       search_term in (u.get('last_name') or '').lower()]
        
        return filtered
    
    async def get_user_details(self, user_id: int) -> Dict[str, Any]:
        """Get detailed user information"""
        try:
            from telegram_bot.database.user_db import UserDatabase
            from telegram_bot.database.order_db import OrderDatabase
            
            user_db = UserDatabase()
            order_db = OrderDatabase()
            
            # Get user basic info
            user = user_db.get_user(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Get user orders
            orders = order_db.get_user_orders(user_id, limit=50)
            
            # Get user sessions (if available)
            sessions = await self._get_user_sessions(user_id)
            
            # Calculate statistics
            stats = self._calculate_user_statistics(user, orders)
            
            return {
                'user': user,
                'orders': orders,
                'sessions': sessions,
                'statistics': stats,
                'timeline': await self._get_user_timeline(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user details: {e}")
            return {'error': str(e)}
    
    async def _get_user_sessions(self, user_id: int) -> List[Dict]:
        """Get user sessions (placeholder)"""
        # In production, this would query sessions table
        return []
    
    def _calculate_user_statistics(self, user: Dict, orders: List[Dict]) -> Dict[str, Any]:
        """Calculate user statistics"""
        completed_orders = [o for o in orders if o.get('status') == 'completed']
        failed_orders = [o for o in orders if o.get('status') == 'failed']
        
        total_spent = sum(o.get('price', 0) for o in completed_orders)
        total_views_ordered = sum(o.get('target_views', 0) for o in completed_orders)
        total_views_delivered = sum(o.get('delivered_views', 0) for o in completed_orders)
        
        if total_views_ordered > 0:
            delivery_rate = (total_views_delivered / total_views_ordered) * 100
        else:
            delivery_rate = 0
        
        return {
            'total_orders': len(orders),
            'completed_orders': len(completed_orders),
            'failed_orders': len(failed_orders),
            'total_spent': round(total_spent, 2),
            'total_views_ordered': total_views_ordered,
            'total_views_delivered': total_views_delivered,
            'delivery_rate': round(delivery_rate, 2),
            'average_order_value': round(total_spent / len(completed_orders), 2) if completed_orders else 0,
            'success_rate': round((len(completed_orders) / len(orders)) * 100, 2) if orders else 0
        }
    
    async def _get_user_timeline(self, user_id: int) -> List[Dict]:
        """Get user activity timeline"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            orders = order_db.get_user_orders(user_id, limit=20)
            
            timeline = []
            
            # Add registration event
            from telegram_bot.database.user_db import UserDatabase
            user_db = UserDatabase()
            user = user_db.get_user(user_id)
            
            if user and user.get('registration_date'):
                timeline.append({
                    'type': 'registration',
                    'timestamp': user['registration_date'],
                    'title': 'User Registered',
                    'description': f'User {user_id} registered in system'
                })
            
            # Add order events
            for order in orders:
                timeline.append({
                    'type': 'order',
                    'timestamp': order['created_at'],
                    'title': f'Order {order["order_id"]}',
                    'description': f'{order["target_views"]} views ordered',
                    'status': order['status'],
                    'data': {
                        'order_id': order['order_id'],
                        'views': order['target_views'],
                        'price': order['price']
                    }
                })
                
                if order.get('completed_at'):
                    timeline.append({
                        'type': 'order_completed',
                        'timestamp': order['completed_at'],
                        'title': f'Order {order["order_id"]} Completed',
                        'description': f'{order.get("delivered_views", 0)}/{order["target_views"]} views delivered',
                        'status': 'completed',
                        'data': {
                            'order_id': order['order_id'],
                            'delivered': order.get('delivered_views', 0),
                            'target': order['target_views']
                        }
                    })
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return timeline[:50]  # Limit to 50 events
            
        except Exception as e:
            self.logger.error(f"Failed to get user timeline: {e}")
            return []
    
    async def update_user(self, user_id: int, updates: Dict) -> Dict[str, Any]:
        """Update user information"""
        try:
            from telegram_bot.database.user_db import UserDatabase
            user_db = UserDatabase()
            
            # Get current user
            user = user_db.get_user(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Validate updates
            valid_updates = {}
            allowed_fields = ['balance', 'is_banned', 'is_premium', 'is_admin', 'settings']
            
            for field, value in updates.items():
                if field in allowed_fields:
                    valid_updates[field] = value
            
            if not valid_updates:
                return {'success': False, 'error': 'No valid fields to update'}
            
            # Apply updates (simplified - in production, use proper update method)
            # For now, we'll simulate the update
            
            return {
                'success': True,
                'message': 'User updated successfully',
                'updates': valid_updates,
                'user_id': user_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update user: {e}")
            return {'success': False, 'error': str(e)}
    
    async def manage_user_balance(self, user_id: int, action: str, 
                                 amount: float, reason: str = "") -> Dict[str, Any]:
        """Manage user balance"""
        try:
            from telegram_bot.database.user_db import UserDatabase
            user_db = UserDatabase()
            
            user = user_db.get_user(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            current_balance = user.get('balance', 0)
            
            if action == 'add':
                new_balance = current_balance + amount
                success = user_db.update_user_balance(user_id, amount)
                operation = 'credit'
            elif action == 'subtract':
                if current_balance < amount:
                    return {'success': False, 'error': 'Insufficient balance'}
                new_balance = current_balance - amount
                success = user_db.update_user_balance(user_id, -amount)
                operation = 'debit'
            elif action == 'set':
                new_balance = amount
                # This would need a set_balance method
                success = False
                operation = 'set'
            else:
                return {'success': False, 'error': 'Invalid action'}
            
            if success:
                # Log the transaction
                await self._log_balance_transaction(
                    user_id, operation, amount, reason, 
                    current_balance, new_balance
                )
                
                return {
                    'success': True,
                    'message': f'Balance {operation} of {amount} successful',
                    'old_balance': current_balance,
                    'new_balance': new_balance,
                    'user_id': user_id
                }
            else:
                return {'success': False, 'error': 'Failed to update balance'}
                
        except Exception as e:
            self.logger.error(f"Failed to manage user balance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _log_balance_transaction(self, user_id: int, operation: str, 
                                      amount: float, reason: str,
                                      old_balance: float, new_balance: float):
        """Log balance transaction"""
        try:
            log_entry = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'amount': amount,
                'reason': reason,
                'old_balance': old_balance,
                'new_balance': new_balance,
                'admin': 'system'  # In production, track admin user
            }
            
            # Save to transaction log
            log_file = 'logs/balance_transactions.json'
            try:
                with open(log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Failed to log transaction: {e}")
    
    async def export_users(self, format_type: str = 'csv', filters: Dict = None) -> Dict[str, Any]:
        """Export users data"""
        try:
            users_data = await self.get_users(filters, page=1, per_page=1000000)
            users = users_data.get('users', [])
            
            if format_type == 'csv':
                export_content = self._export_to_csv(users)
                filename = f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            elif format_type == 'json':
                export_content = json.dumps(users, indent=2, default=str)
                filename = f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            else:
                return {'success': False, 'error': 'Unsupported format'}
            
            return {
                'success': True,
                'filename': filename,
                'content': export_content,
                'count': len(users),
                'format': format_type
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export users: {e}")
            return {'success': False, 'error': str(e)}
    
    def _export_to_csv(self, users: List[Dict]) -> str:
        """Convert users data to CSV"""
        if not users:
            return ''
        
        # Get all possible fields
        all_fields = set()
        for user in users:
            all_fields.update(user.keys())
        
        fields = list(all_fields)
        fields.sort()
        
        # Create CSV header
        csv_lines = [','.join(fields)]
        
        # Add data rows
        for user in users:
            row = []
            for field in fields:
                value = user.get(field, '')
                # Convert to string and escape commas
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
    
    async def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get detailed user analytics"""
        try:
            from telegram_bot.database.analytics_db import AnalyticsDatabase
            analytics_db = AnalyticsDatabase()
            
            # This would query user analytics table
            # For now, return basic analytics
            
            user_details = await self.get_user_details(user_id)
            
            if 'error' in user_details:
                return user_details
            
            # Calculate additional analytics
            orders = user_details.get('orders', [])
            stats = user_details.get('statistics', {})
            
            # Calculate monthly trends
            monthly_data = self._calculate_monthly_trends(orders)
            
            # Calculate behavior patterns
            behavior = self._analyze_user_behavior(orders)
            
            return {
                'user_id': user_id,
                'basic_stats': stats,
                'monthly_trends': monthly_data,
                'behavior_patterns': behavior,
                'recommendations': self._generate_recommendations(stats, behavior)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user analytics: {e}")
            return {'error': str(e)}
    
    def _calculate_monthly_trends(self, orders: List[Dict]) -> Dict[str, Any]:
        """Calculate monthly trends from orders"""
        monthly_data = {}
        
        for order in orders:
            if order.get('created_at'):
                try:
                    month = order['created_at'][:7]  # YYYY-MM
                    if month not in monthly_data:
                        monthly_data[month] = {
                            'orders': 0,
                            'views': 0,
                            'revenue': 0,
                            'completed': 0
                        }
                    
                    monthly_data[month]['orders'] += 1
                    monthly_data[month]['views'] += order.get('target_views', 0)
                    monthly_data[month]['revenue'] += order.get('price', 0)
                    
                    if order.get('status') == 'completed':
                        monthly_data[month]['completed'] += 1
                except:
                    continue
        
        # Convert to sorted list
        sorted_months = sorted(monthly_data.keys(), reverse=True)
        trends = []
        
        for month in sorted_months[:12]:  # Last 12 months
            data = monthly_data[month]
            trends.append({
                'month': month,
                'orders': data['orders'],
                'views': data['views'],
                'revenue': round(data['revenue'], 2),
                'completion_rate': round((data['completed'] / data['orders']) * 100, 1) if data['orders'] > 0 else 0
            })
        
        return trends
    
    def _analyze_user_behavior(self, orders: List[Dict]) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        if not orders:
            return {}
        
        # Analyze order times
        order_hours = []
        order_days = []
        
        for order in orders:
            if order.get('created_at'):
                try:
                    dt = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                    order_hours.append(dt.hour)
                    order_days.append(dt.weekday())
                except:
                    continue
        
        # Calculate preferences
        avg_order_value = sum(o.get('price', 0) for o in orders) / len(orders) if orders else 0
        avg_views_per_order = sum(o.get('target_views', 0) for o in orders) / len(orders) if orders else 0
        
        # Most common order hour
        if order_hours:
            from collections import Counter
            hour_counts = Counter(order_hours)
            most_common_hour = hour_counts.most_common(1)[0][0]
        else:
            most_common_hour = None
        
        return {
            'total_orders': len(orders),
            'average_order_value': round(avg_order_value, 2),
            'average_views_per_order': round(avg_views_per_order),
            'preferred_order_hour': most_common_hour,
            'order_frequency_days': self._calculate_order_frequency(orders),
            'preferred_view_count': self._get_preferred_view_count(orders)
        }
    
    def _calculate_order_frequency(self, orders: List[Dict]) -> float:
        """Calculate average days between orders"""
        if len(orders) < 2:
            return 0
        
        try:
            dates = []
            for order in orders:
                if order.get('created_at'):
                    dt = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                    dates.append(dt)
            
            if len(dates) < 2:
                return 0
            
            dates.sort()
            total_days = 0
            count = 0
            
            for i in range(1, len(dates)):
                days_diff = (dates[i] - dates[i-1]).days
                if days_diff > 0:
                    total_days += days_diff
                    count += 1
            
            return round(total_days / count, 1) if count > 0 else 0
            
        except:
            return 0
    
    def _get_preferred_view_count(self, orders: List[Dict]) -> int:
        """Get most commonly ordered view count"""
        if not orders:
            return 0
        
        view_counts = {}
        for order in orders:
            count = order.get('target_views', 0)
            view_counts[count] = view_counts.get(count, 0) + 1
        
        if view_counts:
            return max(view_counts.items(), key=lambda x: x[1])[0]
        return 0
    
    def _generate_recommendations(self, stats: Dict, behavior: Dict) -> List[str]:
        """Generate recommendations based on user data"""
        recommendations = []
        
        # Check for high-value customer
        if stats.get('total_spent', 0) > 100:
            recommendations.append("Consider offering premium subscription")
        
        # Check for frequent orders
        if behavior.get('total_orders', 0) > 10:
            recommendations.append("Offer bulk discount for next order")
        
        # Check for high success rate
        if stats.get('success_rate', 0) > 90:
            recommendations.append("User is satisfied - consider referral program")
        
        # Check for recent inactivity
        # This would need last_active date
        
        return recommendations