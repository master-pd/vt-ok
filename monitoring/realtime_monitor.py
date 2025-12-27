"""
Real-time Monitoring System for VT ULTRA PRO
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psutil
import socket
import threading

logger = logging.getLogger(__name__)

class RealTimeMonitor:
    """Real-time system monitoring"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
        self.subscribers = []
        self.running = False
        self.monitoring_thread = None
        
        logger.info("RealTime Monitor initialized")
    
    async def start_monitoring(self, interval: int = 5):
        """Start real-time monitoring"""
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info(f"Started monitoring with {interval} second interval")
    
    def _monitoring_loop(self, interval: int):
        """Monitoring loop running in background thread"""
        while self.running:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                self.metrics = metrics
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Notify subscribers
                self._notify_subscribers(metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval)
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self._get_system_metrics(),
            'network': self._get_network_metrics(),
            'disk': self._get_disk_metrics(),
            'process': self._get_process_metrics(),
            'application': self._get_application_metrics(),
            'performance': self._get_performance_metrics()
        }
        return metrics
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            load_avg = psutil.getloadavg()
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'cpu_freq_current': cpu_freq.current if cpu_freq else 0,
                'memory_percent': memory.percent,
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'swap_percent': swap.percent,
                'load_avg_1min': load_avg[0],
                'load_avg_5min': load_avg[1],
                'load_avg_15min': load_avg[2],
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'uptime_seconds': int(time.time() - psutil.boot_time())
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network metrics"""
        try:
            net_io = psutil.net_io_counters()
            connections = psutil.net_connections()
            
            # Get active connections by type
            tcp_connections = len([c for c in connections if c.type == socket.SOCK_STREAM])
            udp_connections = len([c for c in connections if c.type == socket.SOCK_DGRAM])
            
            # Get network interfaces
            interfaces = {}
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces[interface] = addr.address
                        break
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'tcp_connections': tcp_connections,
                'udp_connections': udp_connections,
                'total_connections': len(connections),
                'interfaces': interfaces,
                'error_in': net_io.errin,
                'error_out': net_io.errout,
                'drop_in': net_io.dropin,
                'drop_out': net_io.dropout
            }
        except Exception as e:
            logger.error(f"Failed to get network metrics: {e}")
            return {}
    
    def _get_disk_metrics(self) -> Dict[str, Any]:
        """Get disk metrics"""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Get all partitions
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'percent': usage.percent
                    })
                except:
                    continue
            
            return {
                'root_total_gb': round(disk_usage.total / (1024**3), 2),
                'root_used_gb': round(disk_usage.used / (1024**3), 2),
                'root_free_gb': round(disk_usage.free / (1024**3), 2),
                'root_percent': disk_usage.percent,
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes,
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count,
                'read_time': disk_io.read_time,
                'write_time': disk_io.write_time,
                'partitions': partitions
            }
        except Exception as e:
            logger.error(f"Failed to get disk metrics: {e}")
            return {}
    
    def _get_process_metrics(self) -> Dict[str, Any]:
        """Get process metrics"""
        try:
            processes = []
            total_processes = 0
            running_processes = 0
            sleeping_processes = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
                try:
                    total_processes += 1
                    info = proc.info
                    
                    if info['status'] == psutil.STATUS_RUNNING:
                        running_processes += 1
                    elif info['status'] == psutil.STATUS_SLEEPING:
                        sleeping_processes += 1
                    
                    # Get top 10 processes by CPU
                    if len(processes) < 10 and info['cpu_percent'] > 0.1:
                        processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'cpu_percent': info['cpu_percent'],
                            'memory_percent': info['memory_percent'],
                            'status': info['status']
                        })
                        # Sort by CPU usage
                        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'total_processes': total_processes,
                'running_processes': running_processes,
                'sleeping_processes': sleeping_processes,
                'top_processes': processes[:10]
            }
        except Exception as e:
            logger.error(f"Failed to get process metrics: {e}")
            return {}
    
    def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            # Import application modules
            from telegram_bot.database.user_db import UserDatabase
            from telegram_bot.database.order_db import OrderDatabase
            from telegram_bot.database.analytics_db import AnalyticsDatabase
            
            user_db = UserDatabase()
            order_db = OrderDatabase()
            analytics_db = AnalyticsDatabase()
            
            # Get user statistics
            user_stats = user_db.get_user_count()
            
            # Get order statistics
            order_stats = order_db.get_order_statistics(1)  # Last 24 hours
            
            # Get performance analytics
            performance = analytics_db.get_performance_report(1)
            
            # Calculate queue size (simulated)
            active_orders = order_db.get_active_orders()
            queue_size = len(active_orders)
            
            return {
                'users_total': user_stats.get('total', 0),
                'users_active_24h': user_stats.get('active_24_hours', 0),
                'orders_total_24h': order_stats.get('total_orders', 0),
                'orders_completed_24h': order_stats.get('completed_orders', 0),
                'revenue_24h': order_stats.get('total_revenue', 0),
                'success_rate': order_stats.get('average_success_rate', 0),
                'queue_size': queue_size,
                'active_workers': self._get_active_worker_count(),
                'average_response_time': 0.5,  # Simulated
                'error_rate': 0.02  # Simulated
            }
        except Exception as e:
            logger.error(f"Failed to get application metrics: {e}")
            return {}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            import gc
            
            # Garbage collection metrics
            gc_stats = gc.get_stats()
            gc_count = gc.get_count()
            
            # Python memory usage
            import sys
            python_memory = sys.getsizeof([])
            
            # Response time simulation
            response_times = self._simulate_response_times()
            
            return {
                'gc_collections': sum(stat['collections'] for stat in gc_stats),
                'gc_collected': sum(stat['collected'] for stat in gc_stats),
                'gc_uncollectable': sum(stat['uncollectable'] for stat in gc_stats),
                'gc_count_gen0': gc_count[0],
                'gc_count_gen1': gc_count[1],
                'gc_count_gen2': gc_count[2],
                'python_memory_mb': round(python_memory / (1024**2), 2),
                'response_time_avg': response_times.get('avg', 0),
                'response_time_95th': response_times.get('p95', 0),
                'response_time_99th': response_times.get('p99', 0),
                'throughput_requests_per_second': self._calculate_throughput()
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def _get_active_worker_count(self) -> int:
        """Get active worker count"""
        # This would query worker manager
        # For now, return simulated count
        return 5
    
    def _simulate_response_times(self) -> Dict[str, float]:
        """Simulate response times"""
        return {
            'avg': 0.15,
            'p50': 0.12,
            'p95': 0.25,
            'p99': 0.35,
            'max': 1.2
        }
    
    def _calculate_throughput(self) -> float:
        """Calculate throughput"""
        # Simulated throughput
        return 150.5
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        alerts = []
        
        # CPU alert
        cpu_percent = metrics.get('system', {}).get('cpu_percent', 0)
        if cpu_percent > 90:
            alerts.append({
                'level': 'critical',
                'type': 'cpu',
                'message': f'High CPU usage: {cpu_percent}%',
                'timestamp': metrics['timestamp'],
                'value': cpu_percent,
                'threshold': 90
            })
        elif cpu_percent > 80:
            alerts.append({
                'level': 'warning',
                'type': 'cpu',
                'message': f'High CPU usage: {cpu_percent}%',
                'timestamp': metrics['timestamp'],
                'value': cpu_percent,
                'threshold': 80
            })
        
        # Memory alert
        memory_percent = metrics.get('system', {}).get('memory_percent', 0)
        if memory_percent > 90:
            alerts.append({
                'level': 'critical',
                'type': 'memory',
                'message': f'High memory usage: {memory_percent}%',
                'timestamp': metrics['timestamp'],
                'value': memory_percent,
                'threshold': 90
            })
        elif memory_percent > 85:
            alerts.append({
                'level': 'warning',
                'type': 'memory',
                'message': f'High memory usage: {memory_percent}%',
                'timestamp': metrics['timestamp'],
                'value': memory_percent,
                'threshold': 85
            })
        
        # Disk alert
        disk_percent = metrics.get('disk', {}).get('root_percent', 0)
        if disk_percent > 95:
            alerts.append({
                'level': 'critical',
                'type': 'disk',
                'message': f'High disk usage: {disk_percent}%',
                'timestamp': metrics['timestamp'],
                'value': disk_percent,
                'threshold': 95
            })
        elif disk_percent > 90:
            alerts.append({
                'level': 'warning',
                'type': 'disk',
                'message': f'High disk usage: {disk_percent}%',
                'timestamp': metrics['timestamp'],
                'value': disk_percent,
                'threshold': 90
            })
        
        # Application alerts
        error_rate = metrics.get('application', {}).get('error_rate', 0)
        if error_rate > 0.1:  # 10% error rate
            alerts.append({
                'level': 'critical',
                'type': 'application',
                'message': f'High error rate: {error_rate*100:.1f}%',
                'timestamp': metrics['timestamp'],
                'value': error_rate,
                'threshold': 0.1
            })
        
        # Queue size alert
        queue_size = metrics.get('application', {}).get('queue_size', 0)
        if queue_size > 100:
            alerts.append({
                'level': 'warning',
                'type': 'queue',
                'message': f'Large queue size: {queue_size} orders',
                'timestamp': metrics['timestamp'],
                'value': queue_size,
                'threshold': 100
            })
        
        # Add new alerts
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"Alert: {alert['message']}")
        
        # Keep only recent alerts (last 100)
        self.alerts = self.alerts[-100:]
    
    def _notify_subscribers(self, metrics: Dict[str, Any]):
        """Notify subscribers of new metrics"""
        for subscriber in self.subscribers:
            try:
                subscriber(metrics)
            except Exception as e:
                logger.error(f"Failed to notify subscriber: {e}")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics
    
    async def get_metrics_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get metrics history"""
        # This would query from database or cache
        # For now, return current metrics
        return [self.metrics] if self.metrics else []
    
    async def get_alerts(self, level: str = None, recent: bool = True) -> List[Dict[str, Any]]:
        """Get alerts"""
        alerts = self.alerts
        
        if level:
            alerts = [a for a in alerts if a['level'] == level]
        
        if recent:
            # Return alerts from last hour
            cutoff = datetime.now() - timedelta(hours=1)
            alerts = [a for a in alerts if datetime.fromisoformat(a['timestamp']) > cutoff]
        
        return alerts
    
    async def subscribe(self, callback):
        """Subscribe to metrics updates"""
        self.subscribers.append(callback)
    
    async def unsubscribe(self, callback):
        """Unsubscribe from metrics updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("Monitoring stopped")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        metrics = self.metrics
        
        # Calculate trends (simplified)
        trends = {
            'cpu_trend': 'stable',
            'memory_trend': 'stable',
            'disk_trend': 'stable',
            'network_trend': 'stable'
        }
        
        # Calculate uptime
        uptime_seconds = metrics.get('system', {}).get('uptime_seconds', 0)
        uptime_str = self._format_uptime(uptime_seconds)
        
        # Calculate health score
        health_score = self._calculate_health_score(metrics)
        
        return {
            'current_metrics': metrics,
            'trends': trends,
            'uptime': uptime_str,
            'health_score': health_score,
            'alerts_count': len(self.alerts),
            'subscribers_count': len(self.subscribers)
        }
    
    def _format_uptime(self, seconds: int) -> str:
        """Format uptime as human readable string"""
        days = seconds // (24 * 3600)
        seconds = seconds % (24 * 3600)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate system health score (0-100)"""
        score = 100
        
        # Deduct for CPU usage
        cpu_percent = metrics.get('system', {}).get('cpu_percent', 0)
        if cpu_percent > 90:
            score -= 30
        elif cpu_percent > 80:
            score -= 20
        elif cpu_percent > 70:
            score -= 10
        
        # Deduct for memory usage
        memory_percent = metrics.get('system', {}).get('memory_percent', 0)
        if memory_percent > 90:
            score -= 30
        elif memory_percent > 80:
            score -= 20
        elif memory_percent > 70:
            score -= 10
        
        # Deduct for disk usage
        disk_percent = metrics.get('disk', {}).get('root_percent', 0)
        if disk_percent > 95:
            score -= 30
        elif disk_percent > 90:
            score -= 20
        elif disk_percent > 85:
            score -= 10
        
        # Deduct for error rate
        error_rate = metrics.get('application', {}).get('error_rate', 0)
        score -= error_rate * 100
        
        # Ensure score is between 0 and 100
        return max(0, min(100, round(score, 1)))