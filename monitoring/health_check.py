"""
Health Check System for VT ULTRA PRO
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import psutil
import socket
import ssl

logger = logging.getLogger(__name__)

class HealthCheck:
    """System health check and monitoring"""
    
    def __init__(self):
        self.health_status = {}
        self.check_history = []
        self.dependencies = []
        
        self._initialize_dependencies()
        logger.info("Health Check system initialized")
    
    def _initialize_dependencies(self):
        """Initialize dependency checks"""
        self.dependencies = [
            {
                'name': 'database',
                'type': 'internal',
                'check_method': self._check_database,
                'required': True,
                'timeout': 5
            },
            {
                'name': 'redis',
                'type': 'cache',
                'check_method': self._check_redis,
                'required': False,
                'timeout': 3
            },
            {
                'name': 'telegram_api',
                'type': 'external',
                'check_method': self._check_telegram_api,
                'required': True,
                'timeout': 10
            },
            {
                'name': 'tiktok_api',
                'type': 'external',
                'check_method': self._check_tiktok_api,
                'required': False,
                'timeout': 10
            },
            {
                'name': 'payment_gateway',
                'type': 'external',
                'check_method': self._check_payment_gateway,
                'required': False,
                'timeout': 10
            },
            {
                'name': 'smtp_server',
                'type': 'external',
                'check_method': self._check_smtp_server,
                'required': False,
                'timeout': 5
            },
            {
                'name': 'web_server',
                'type': 'internal',
                'check_method': self._check_web_server,
                'required': True,
                'timeout': 3
            },
            {
                'name': 'file_system',
                'type': 'internal',
                'check_method': self._check_file_system,
                'required': True,
                'timeout': 2
            },
            {
                'name': 'network',
                'type': 'internal',
                'check_method': self._check_network,
                'required': True,
                'timeout': 3
            }
        ]
    
    async def perform_health_check(self, full_check: bool = True) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        check_start = datetime.now()
        results = []
        
        try:
            # Perform basic system check
            system_status = await self._check_system_resources()
            results.append({
                'name': 'system',
                'status': 'healthy' if system_status['healthy'] else 'unhealthy',
                'details': system_status,
                'duration': system_status.get('check_duration', 0),
                'timestamp': check_start.isoformat()
            })
            
            # Check dependencies
            dependency_checks = []
            for dependency in self.dependencies:
                if not full_check and not dependency['required']:
                    continue
                
                try:
                    dep_result = await self._check_dependency(dependency)
                    dependency_checks.append(dep_result)
                    results.append(dep_result)
                except asyncio.TimeoutError:
                    dep_result = {
                        'name': dependency['name'],
                        'status': 'timeout',
                        'details': {'error': f"Timeout after {dependency['timeout']} seconds"},
                        'duration': dependency['timeout'],
                        'timestamp': datetime.now().isoformat()
                    }
                    dependency_checks.append(dep_result)
                    results.append(dep_result)
                except Exception as e:
                    dep_result = {
                        'name': dependency['name'],
                        'status': 'error',
                        'details': {'error': str(e)},
                        'duration': 0,
                        'timestamp': datetime.now().isoformat()
                    }
                    dependency_checks.append(dep_result)
                    results.append(dep_result)
            
            # Calculate overall status
            overall_status = self._calculate_overall_status(system_status, dependency_checks)
            
            # Prepare response
            check_end = datetime.now()
            check_duration = (check_end - check_start).total_seconds()
            
            health_status = {
                'status': overall_status['status'],
                'timestamp': check_start.isoformat(),
                'duration_seconds': round(check_duration, 3),
                'system': system_status,
                'dependencies': dependency_checks,
                'detailed_results': results,
                'summary': {
                    'total_checks': len(results),
                    'healthy': overall_status['healthy_count'],
                    'unhealthy': overall_status['unhealthy_count'],
                    'degraded': overall_status['degraded_count']
                }
            }
            
            # Store in history
            self.health_status = health_status
            self.check_history.append({
                'timestamp': check_start.isoformat(),
                'status': overall_status['status'],
                'duration': check_duration,
                'summary': health_status['summary']
            })
            
            # Keep only recent history
            self.check_history = self.check_history[-100:]
            
            logger.info(f"Health check completed: {overall_status['status']} ({check_duration:.2f}s)")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources"""
        check_start = time.time()
        
        try:
            # CPU check
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_healthy = cpu_percent < 90
            
            # Memory check
            memory = psutil.virtual_memory()
            memory_healthy = memory.percent < 90
            
            # Disk check
            disk = psutil.disk_usage('/')
            disk_healthy = disk.percent < 95
            
            # Load average
            load_avg = psutil.getloadavg()
            cpu_count = psutil.cpu_count()
            load_healthy = load_avg[0] < cpu_count * 2
            
            # Process check
            process_count = len(psutil.pids())
            process_healthy = process_count < 1000
            
            # Network check
            net_io = psutil.net_io_counters()
            network_healthy = net_io.errin == 0 and net_io.errout == 0
            
            check_end = time.time()
            
            return {
                'healthy': all([cpu_healthy, memory_healthy, disk_healthy, 
                               load_healthy, process_healthy, network_healthy]),
                'cpu': {
                    'percent': cpu_percent,
                    'healthy': cpu_healthy,
                    'threshold': 90
                },
                'memory': {
                    'percent': memory.percent,
                    'used_gb': round(memory.used / (1024**3), 2),
                    'total_gb': round(memory.total / (1024**3), 2),
                    'healthy': memory_healthy,
                    'threshold': 90
                },
                'disk': {
                    'percent': disk.percent,
                    'used_gb': round(disk.used / (1024**3), 2),
                    'total_gb': round(disk.total / (1024**3), 2),
                    'healthy': disk_healthy,
                    'threshold': 95
                },
                'load': {
                    '1min': load_avg[0],
                    '5min': load_avg[1],
                    '15min': load_avg[2],
                    'cpu_count': cpu_count,
                    'healthy': load_healthy
                },
                'processes': {
                    'count': process_count,
                    'healthy': process_healthy,
                    'threshold': 1000
                },
                'network': {
                    'errors_in': net_io.errin,
                    'errors_out': net_io.errout,
                    'healthy': network_healthy
                },
                'check_duration': check_end - check_start
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'check_duration': time.time() - check_start
            }
    
    async def _check_dependency(self, dependency: Dict) -> Dict[str, Any]:
        """Check a single dependency"""
        check_start = time.time()
        
        try:
            # Run the check with timeout
            result = await asyncio.wait_for(
                dependency['check_method'](),
                timeout=dependency['timeout']
            )
            
            check_end = time.time()
            
            return {
                'name': dependency['name'],
                'type': dependency['type'],
                'required': dependency['required'],
                'status': result.get('status', 'unknown'),
                'details': result.get('details', {}),
                'duration': check_end - check_start,
                'timestamp': datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            check_end = time.time()
            return {
                'name': dependency['name'],
                'type': dependency['type'],
                'required': dependency['required'],
                'status': 'error',
                'details': {'error': str(e)},
                'duration': check_end - check_start,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from telegram_bot.database.user_db import UserDatabase
            
            db = UserDatabase()
            
            # Try to query user count
            stats = db.get_user_count()
            
            return {
                'status': 'healthy',
                'details': {
                    'user_count': stats.get('total', 0),
                    'connection': 'established'
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            import redis
            
            # Try to connect to Redis
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_connect_timeout=2
            )
            
            # Ping Redis
            response = redis_client.ping()
            
            if response:
                return {
                    'status': 'healthy',
                    'details': {
                        'connection': 'established',
                        'response_time': 'ok'
                    }
                }
            else:
                return {
                    'status': 'unhealthy',
                    'details': {'error': 'Redis ping failed'}
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
    
    async def _check_telegram_api(self) -> Dict[str, Any]:
        """Check Telegram API connectivity"""
        try:
            import os
            import requests
            
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            
            if not bot_token:
                return {
                    'status': 'degraded',
                    'details': {'error': 'Bot token not configured'}
                }
            
            # Test Telegram API
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return {
                        'status': 'healthy',
                        'details': {
                            'bot_username': data['result']['username'],
                            'response_time_ms': response.elapsed.total_seconds() * 1000
                        }
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'details': {'error': 'Telegram API returned error'}
                    }
            else:
                return {
                    'status': 'unhealthy',
                    'details': {
                        'error': f'HTTP {response.status_code}',
                        'response': response.text[:100]
                    }
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
    
    async def _check_tiktok_api(self) -> Dict[str, Any]:
        """Check TikTok API connectivity"""
        try:
            import requests
            
            # Try to access TikTok (simplified check)
            url = "https://www.tiktok.com"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'details': {
                        'accessible': True,
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    }
                }
            else:
                return {
                    'status': 'degraded',
                    'details': {
                        'error': f'HTTP {response.status_code}',
                        'accessible': False
                    }
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
    
    async def _check_payment_gateway(self) -> Dict[str, Any]:
        """Check payment gateway connectivity"""
        try:
            # This would check Stripe/PayPal/etc.
            # For now, simulate check
            
            await asyncio.sleep(0.5)  # Simulate API call
            
            return {
                'status': 'healthy',
                'details': {
                    'gateway': 'simulated',
                    'status': 'operational'
                }
            }
            
        except Exception as e:
            return {
                'status': 'degraded',
                'details': {'error': str(e)}
            }
    
    async def _check_smtp_server(self) -> Dict[str, Any]:
        """Check SMTP server connectivity"""
        try:
            import os
            import smtplib
            
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            
            # Test connection
            with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                
                return {
                    'status': 'healthy',
                    'details': {
                        'server': smtp_server,
                        'port': smtp_port,
                        'tls': 'enabled'
                    }
                }
                
        except Exception as e:
            return {
                'status': 'degraded',
                'details': {'error': str(e)}
            }
    
    async def _check_web_server(self) -> Dict[str, Any]:
        """Check web server status"""
        try:
            import requests
            
            # Check local web server
            url = "http://localhost:8000/health"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'details': {
                        'url': url,
                        'status_code': response.status_code,
                        'response': response.text.strip()
                    }
                }
            else:
                return {
                    'status': 'unhealthy',
                    'details': {
                        'url': url,
                        'status_code': response.status_code
                    }
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
    
    async def _check_file_system(self) -> Dict[str, Any]:
        """Check file system health"""
        try:
            import os
            import tempfile
            
            # Test write permission
            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                tmp.write(b'test')
                tmp.flush()
            
            # Check important directories
            directories = ['logs', 'database', 'config', 'backups']
            dir_status = {}
            
            for dir_name in directories:
                dir_path = os.path.join(os.getcwd(), dir_name)
                exists = os.path.exists(dir_path)
                writable = os.access(dir_path, os.W_OK) if exists else False
                
                dir_status[dir_name] = {
                    'exists': exists,
                    'writable': writable
                }
            
            return {
                'status': 'healthy',
                'details': {
                    'temp_write': 'ok',
                    'directories': dir_status
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
    
    async def _check_network(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            import requests
            
            # Test internet connectivity
            test_urls = [
                'https://www.google.com',
                'https://www.cloudflare.com',
                'https://api.telegram.org'
            ]
            
            results = []
            all_successful = True
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    results.append({
                        'url': url,
                        'status': 'success',
                        'status_code': response.status_code,
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    })
                except Exception as e:
                    results.append({
                        'url': url,
                        'status': 'failed',
                        'error': str(e)
                    })
                    all_successful = False
            
            # Test DNS resolution
            try:
                socket.gethostbyname('google.com')
                dns_status = 'healthy'
            except:
                dns_status = 'failed'
                all_successful = False
            
            status = 'healthy' if all_successful else 'degraded'
            
            return {
                'status': status,
                'details': {
                    'internet_connectivity': results,
                    'dns_resolution': dns_status
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
    
    def _calculate_overall_status(self, system_status: Dict, 
                                dependency_checks: List[Dict]) -> Dict[str, Any]:
        """Calculate overall system status"""
        # Count statuses
        status_counts = {
            'healthy': 0,
            'degraded': 0,
            'unhealthy': 0,
            'timeout': 0,
            'error': 0
        }
        
        # Count system status
        if system_status.get('healthy'):
            status_counts['healthy'] += 1
        else:
            status_counts['unhealthy'] += 1
        
        # Count dependency statuses
        for dep in dependency_checks:
            status = dep.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
        
        # Determine overall status
        if status_counts['unhealthy'] > 0:
            overall_status = 'unhealthy'
        elif status_counts['degraded'] > 0:
            overall_status = 'degraded'
        elif status_counts['timeout'] > 0:
            overall_status = 'degraded'
        elif status_counts['error'] > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        return {
            'status': overall_status,
            'healthy_count': status_counts['healthy'],
            'unhealthy_count': status_counts['unhealthy'],
            'degraded_count': status_counts['degraded'] + status_counts['timeout'] + status_counts['error'],
            'counts': status_counts
        }
    
    async def get_current_status(self) -> Dict[str, Any]:
        """Get current health status"""
        if not self.health_status:
            await self.perform_health_check(full_check=False)
        
        return self.health_status
    
    async def get_status_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health status history"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        return [
            check for check in self.check_history
            if datetime.fromisoformat(check['timestamp']) > cutoff
        ]
    
    async def get_status_summary(self) -> Dict[str, Any]:
        """Get health status summary"""
        if not self.check_history:
            await self.perform_health_check(full_check=False)
        
        # Calculate uptime based on recent checks
        recent_checks = self.check_history[-100:]  # Last 100 checks
        if not recent_checks:
            return {'uptime_percent': 0, 'total_checks': 0}
        
        healthy_checks = sum(1 for check in recent_checks 
                           if check['status'] == 'healthy')
        
        uptime_percent = (healthy_checks / len(recent_checks)) * 100
        
        # Get last check status
        last_check = recent_checks[-1] if recent_checks else {}
        
        return {
            'uptime_percent': round(uptime_percent, 2),
            'total_checks': len(recent_checks),
            'healthy_checks': healthy_checks,
            'last_check': {
                'timestamp': last_check.get('timestamp'),
                'status': last_check.get('status'),
                'duration': last_check.get('duration')
            }
        }
    
    async def add_custom_check(self, name: str, check_method: callable,
                              required: bool = False, timeout: int = 5):
        """Add custom health check"""
        self.dependencies.append({
            'name': name,
            'type': 'custom',
            'check_method': check_method,
            'required': required,
            'timeout': timeout
        })
        
        logger.info(f"Added custom health check: {name}")
    
    async def remove_check(self, name: str) -> bool:
        """Remove health check"""
        initial_count = len(self.dependencies)
        self.dependencies = [d for d in self.dependencies if d['name'] != name]
        
        if len(self.dependencies) < initial_count:
            logger.info(f"Removed health check: {name}")
            return True
        
        return False