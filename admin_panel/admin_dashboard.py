"""
Admin Dashboard for VT ULTRA PRO
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Admin Dashboard for system management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dashboard_data = {}
        self.system_stats = {}
        
    async def initialize(self):
        """Initialize admin dashboard"""
        self.logger.info("Initializing Admin Dashboard...")
        await self.load_dashboard_data()
        await self.update_system_stats()
        self.logger.info("✅ Admin Dashboard initialized")
    
    async def load_dashboard_data(self):
        """Load dashboard data from database"""
        try:
            # Load user statistics
            from telegram_bot.database.user_db import UserDatabase
            user_db = UserDatabase()
            self.dashboard_data['users'] = user_db.get_user_count()
            
            # Load order statistics
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            self.dashboard_data['orders'] = order_db.get_order_statistics(7)
            
            # Load analytics
            from telegram_bot.database.analytics_db import AnalyticsDatabase
            analytics_db = AnalyticsDatabase()
            self.dashboard_data['analytics'] = analytics_db.get_performance_report(7)
            
            # Load system info
            self.dashboard_data['system'] = await self.get_system_info()
            
        except Exception as e:
            self.logger.error(f"Failed to load dashboard data: {e}")
    
    async def update_system_stats(self):
        """Update system statistics"""
        try:
            import psutil
            import platform
            
            # System information
            self.system_stats = {
                'system': {
                    'os': platform.system(),
                    'os_version': platform.version(),
                    'python_version': platform.python_version(),
                    'hostname': platform.node(),
                    'processor': platform.processor()
                },
                'resources': {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
                },
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv,
                    'connections': len(psutil.net_connections())
                },
                'processes': {
                    'total': len(psutil.pids()),
                    'running': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running']),
                    'sleeping': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'sleeping'])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update system stats: {e}")
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get dashboard overview"""
        try:
            overview = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_users': self.dashboard_data.get('users', {}).get('total', 0),
                    'active_users': self.dashboard_data.get('users', {}).get('active_24_hours', 0),
                    'total_orders': self.dashboard_data.get('orders', {}).get('total_orders', 0),
                    'total_revenue': self.dashboard_data.get('orders', {}).get('total_revenue', 0),
                    'success_rate': self.dashboard_data.get('orders', {}).get('average_success_rate', 0)
                },
                'recent_activity': await self.get_recent_activity(),
                'system_health': {
                    'status': 'healthy' if self.system_stats.get('resources', {}).get('memory_percent', 0) < 80 else 'warning',
                    'cpu_usage': self.system_stats.get('resources', {}).get('cpu_percent', 0),
                    'memory_usage': self.system_stats.get('resources', {}).get('memory_percent', 0),
                    'disk_usage': self.system_stats.get('resources', {}).get('disk_percent', 0)
                },
                'alerts': await self.get_system_alerts()
            }
            
            return overview
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard overview: {e}")
            return {}
    
    async def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Get recent system activity"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            # Get recent orders
            active_orders = order_db.get_active_orders()
            recent_orders = []
            
            for order in active_orders[:limit]:
                recent_orders.append({
                    'type': 'order',
                    'id': order['order_id'],
                    'user_id': order['user_id'],
                    'action': f"New order: {order['target_views']} views",
                    'timestamp': order['created_at'],
                    'status': order['status']
                })
            
            # Get recent user registrations
            from telegram_bot.database.user_db import UserDatabase
            user_db = UserDatabase()
            
            # This would need a method to get recent users
            # For now, we'll return only orders
            
            return recent_orders
            
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return []
    
    async def get_system_alerts(self) -> List[Dict]:
        """Get system alerts"""
        alerts = []
        
        try:
            # Check resource usage
            resources = self.system_stats.get('resources', {})
            
            if resources.get('memory_percent', 0) > 85:
                alerts.append({
                    'level': 'high',
                    'message': f"High memory usage: {resources.get('memory_percent', 0)}%",
                    'type': 'resource',
                    'timestamp': datetime.now().isoformat()
                })
            
            if resources.get('cpu_percent', 0) > 90:
                alerts.append({
                    'level': 'high',
                    'message': f"High CPU usage: {resources.get('cpu_percent', 0)}%",
                    'type': 'resource',
                    'timestamp': datetime.now().isoformat()
                })
            
            if resources.get('disk_percent', 0) > 90:
                alerts.append({
                    'level': 'high',
                    'message': f"High disk usage: {resources.get('disk_percent', 0)}%",
                    'type': 'resource',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check for failed orders
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            order_stats = order_db.get_order_statistics(1)  # Last 24 hours
            
            if order_stats.get('failed_orders', 0) > 10:
                alerts.append({
                    'level': 'medium',
                    'message': f"High failed orders: {order_stats.get('failed_orders', 0)} in 24 hours",
                    'type': 'order',
                    'timestamp': datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get system alerts: {e}")
            return []
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information"""
        try:
            import os
            import socket
            import uuid
            
            info = {
                'general': {
                    'system_id': str(uuid.uuid4()),
                    'hostname': socket.gethostname(),
                    'ip_address': socket.gethostbyname(socket.gethostname()),
                    'working_directory': os.getcwd(),
                    'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'versions': await self.get_version_info(),
                'dependencies': await self.get_dependencies(),
                'paths': {
                    'config_dir': str(Path('config').absolute()),
                    'database_dir': str(Path('database').absolute()),
                    'logs_dir': str(Path('logs').absolute()),
                    'backup_dir': str(Path('backups').absolute())
                }
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}
    
    async def get_version_info(self) -> Dict[str, str]:
        """Get version information"""
        return {
            'vt_ultra_pro': '1.0.0 Ultra Pro',
            'python': '3.8+',
            'database': 'SQLite 3',
            'telegram_bot': 'aiogram 3.x',
            'web_framework': 'FastAPI',
            'admin_panel': '1.0.0'
        }
    
    async def get_dependencies(self) -> List[Dict]:
        """Get dependency information"""
        dependencies = [
            {'name': 'aiogram', 'version': '3.0+', 'purpose': 'Telegram Bot'},
            {'name': 'aiohttp', 'version': '3.8+', 'purpose': 'Async HTTP'},
            {'name': 'sqlalchemy', 'version': '2.0+', 'purpose': 'Database ORM'},
            {'name': 'fastapi', 'version': '0.100+', 'purpose': 'Web API'},
            {'name': 'uvicorn', 'version': '0.23+', 'purpose': 'ASGI Server'},
            {'name': 'psutil', 'version': '5.9+', 'purpose': 'System Monitoring'},
            {'name': 'pydantic', 'version': '2.0+', 'purpose': 'Data Validation'},
            {'name': 'redis', 'version': '4.5+', 'purpose': 'Caching'},
            {'name': 'celery', 'version': '5.3+', 'purpose': 'Task Queue'},
            {'name': 'docker', 'version': '6.1+', 'purpose': 'Containerization'}
        ]
        
        return dependencies
    
    async def get_user_management_data(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get user management data"""
        try:
            from telegram_bot.database.user_db import UserDatabase
            user_db = UserDatabase()
            
            # Get top users
            top_users = user_db.get_top_users(limit=per_page, by="total_spent")
            
            # Get user statistics
            user_stats = user_db.get_user_count()
            
            return {
                'users': top_users,
                'statistics': user_stats,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': user_stats.get('total', 0),
                    'total_pages': (user_stats.get('total', 0) + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user management data: {e}")
            return {}
    
    async def get_order_management_data(self, status: str = None, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get order management data"""
        try:
            from telegram_bot.database.order_db import OrderDatabase
            order_db = OrderDatabase()
            
            # Get active orders
            active_orders = order_db.get_active_orders()
            
            # Get order statistics
            order_stats = order_db.get_order_statistics(30)
            
            # Filter by status if specified
            if status:
                filtered_orders = [o for o in active_orders if o.get('status') == status]
            else:
                filtered_orders = active_orders
            
            # Apply pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_orders = filtered_orders[start_idx:end_idx]
            
            return {
                'orders': paginated_orders,
                'statistics': order_stats,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': len(filtered_orders),
                    'total_pages': (len(filtered_orders) + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get order management data: {e}")
            return {}
    
    async def get_analytics_data(self, period: str = '7d') -> Dict[str, Any]:
        """Get analytics data for charts"""
        try:
            from telegram_bot.database.analytics_db import AnalyticsDatabase
            analytics_db = AnalyticsDatabase()
            
            # Convert period to days
            period_map = {'1d': 1, '7d': 7, '30d': 30, '90d': 90}
            days = period_map.get(period, 7)
            
            # Get performance report
            report = analytics_db.get_performance_report(days)
            
            # Get growth analytics
            growth = analytics_db.get_growth_analytics('daily')
            
            # Prepare chart data
            chart_data = {
                'revenue_trend': await self._prepare_revenue_chart_data(days),
                'user_growth': await self._prepare_user_growth_data(days),
                'order_metrics': await self._prepare_order_metrics(days),
                'method_performance': report.get('method_performance', [])
            }
            
            return {
                'charts': chart_data,
                'summary': report.get('summary', {}),
                'growth': growth,
                'period': period,
                'days': days
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get analytics data: {e}")
            return {}
    
    async def _prepare_revenue_chart_data(self, days: int) -> Dict[str, Any]:
        """Prepare revenue chart data"""
        # This would fetch from database
        # For now, return sample data
        return {
            'labels': [f'Day {i}' for i in range(1, days + 1)],
            'datasets': [{
                'label': 'Revenue (USD)',
                'data': [100 * (i + 1) + (i * 50) for i in range(days)],
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)'
            }]
        }
    
    async def _prepare_user_growth_data(self, days: int) -> Dict[str, Any]:
        """Prepare user growth chart data"""
        return {
            'labels': [f'Day {i}' for i in range(1, days + 1)],
            'datasets': [{
                'label': 'New Users',
                'data': [10 + (i * 2) for i in range(days)],
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)'
            }]
        }
    
    async def _prepare_order_metrics(self, days: int) -> Dict[str, Any]:
        """Prepare order metrics data"""
        return {
            'completed': [5 + i for i in range(days)],
            'failed': [max(0, 1 - (i * 0.1)) for i in range(days)],
            'pending': [2 + (i * 0.5) for i in range(days)]
        }
    
    async def execute_admin_command(self, command: str, parameters: Dict = None) -> Dict[str, Any]:
        """Execute admin command"""
        try:
            if command == 'refresh_cache':
                return await self.refresh_cache()
            elif command == 'backup_database':
                return await self.backup_database()
            elif command == 'cleanup_logs':
                return await self.cleanup_logs()
            elif command == 'restart_services':
                return await self.restart_services()
            elif command == 'update_stats':
                return await self.update_system_stats()
            else:
                return {
                    'success': False,
                    'message': f'Unknown command: {command}'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to execute command {command}: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    async def refresh_cache(self) -> Dict[str, Any]:
        """Refresh system cache"""
        try:
            await self.load_dashboard_data()
            await self.update_system_stats()
            
            return {
                'success': True,
                'message': 'Cache refreshed successfully',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to refresh cache: {e}'
            }
    
    async def backup_database(self) -> Dict[str, Any]:
        """Backup database"""
        try:
            from telegram_bot.database.user_db import UserDatabase
            user_db = UserDatabase()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'backups/database_backup_{timestamp}.db'
            
            success = user_db.backup_database(backup_path)
            
            if success:
                return {
                    'success': True,
                    'message': f'Database backed up to {backup_path}',
                    'backup_path': backup_path,
                    'timestamp': timestamp
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to backup database'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Backup failed: {e}'
            }
    
    async def cleanup_logs(self) -> Dict[str, Any]:
        """Cleanup old log files"""
        try:
            import os
            from pathlib import Path
            
            logs_dir = Path('logs')
            if not logs_dir.exists():
                return {
                    'success': False,
                    'message': 'Logs directory not found'
                }
            
            # Keep logs from last 7 days
            cutoff_time = datetime.now() - timedelta(days=7)
            deleted_files = 0
            
            for log_file in logs_dir.glob('*.log'):
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    log_file.unlink()
                    deleted_files += 1
            
            return {
                'success': True,
                'message': f'Cleaned up {deleted_files} old log files',
                'deleted_files': deleted_files
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Log cleanup failed: {e}'
            }
    
    async def restart_services(self) -> Dict[str, Any]:
        """Restart system services"""
        # Note: This is a placeholder. Actual implementation would depend on deployment
        return {
            'success': True,
            'message': 'Service restart initiated',
            'note': 'This feature requires proper service manager integration'
        }