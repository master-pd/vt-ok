"""
Performance Tracking System for VT ULTRA PRO
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import statistics
from collections import defaultdict, deque
import asyncio

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Performance tracking and analysis system"""
    
    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        self.metrics_store = {}
        self.performance_data = {}
        self.benchmarks = {}
        self.callbacks = []
        
        self._initialize_data_structures()
        logger.info(f"Performance Tracker initialized (retention: {retention_days} days)")
    
    def _initialize_data_structures(self):
        """Initialize data storage structures"""
        # Store for different metric types
        self.metrics_store = {
            'response_times': defaultdict(lambda: deque(maxlen=10000)),
            'throughput': defaultdict(lambda: deque(maxlen=1000)),
            'error_rates': defaultdict(lambda: deque(maxlen=1000)),
            'resource_usage': defaultdict(lambda: deque(maxlen=1000)),
            'business_metrics': defaultdict(lambda: deque(maxlen=1000))
        }
        
        # Performance data aggregated by time periods
        self.performance_data = {
            'hourly': defaultdict(dict),
            'daily': defaultdict(dict),
            'weekly': defaultdict(dict)
        }
        
        # Benchmarks
        self.benchmarks = self._load_benchmarks()
    
    def _load_benchmarks(self) -> Dict[str, Any]:
        """Load performance benchmarks"""
        return {
            'response_time': {
                'excellent': 0.1,   # seconds
                'good': 0.3,
                'fair': 1.0,
                'poor': 3.0
            },
            'throughput': {
                'excellent': 1000,  # requests/second
                'good': 500,
                'fair': 100,
                'poor': 10
            },
            'error_rate': {
                'excellent': 0.001,  # 0.1%
                'good': 0.01,        # 1%
                'fair': 0.05,        # 5%
                'poor': 0.1          # 10%
            },
            'cpu_usage': {
                'excellent': 30,     # percent
                'good': 60,
                'fair': 80,
                'poor': 90
            },
            'memory_usage': {
                'excellent': 40,     # percent
                'good': 60,
                'fair': 80,
                'poor': 90
            },
            'success_rate': {
                'excellent': 99.9,   # percent
                'good': 99.0,
                'fair': 95.0,
                'poor': 90.0
            }
        }
    
    async def track_response_time(self, endpoint: str, method: str, 
                                response_time: float, status_code: int = 200):
        """Track API response time"""
        try:
            timestamp = datetime.now()
            key = f"{method}:{endpoint}"
            
            # Store raw data
            data_point = {
                'timestamp': timestamp.isoformat(),
                'response_time': response_time,
                'status_code': status_code,
                'success': status_code < 400
            }
            
            self.metrics_store['response_times'][key].append(data_point)
            
            # Update aggregated data
            await self._update_aggregated_data('response_times', key, data_point)
            
            # Check against benchmarks
            benchmark_result = self._check_benchmark('response_time', response_time)
            if benchmark_result.get('level') in ['poor', 'fair']:
                await self._trigger_performance_alert(
                    'response_time', endpoint, response_time, benchmark_result
                )
            
            # Notify callbacks
            await self._notify_callbacks('response_time', {
                'endpoint': endpoint,
                'method': method,
                'response_time': response_time,
                'status_code': status_code,
                'benchmark': benchmark_result
            })
            
        except Exception as e:
            logger.error(f"Failed to track response time: {e}")
    
    async def track_throughput(self, endpoint: str, requests_per_second: float):
        """Track request throughput"""
        try:
            timestamp = datetime.now()
            key = endpoint
            
            data_point = {
                'timestamp': timestamp.isoformat(),
                'throughput': requests_per_second
            }
            
            self.metrics_store['throughput'][key].append(data_point)
            await self._update_aggregated_data('throughput', key, data_point)
            
            # Check benchmark
            benchmark_result = self._check_benchmark('throughput', requests_per_second)
            
            await self._notify_callbacks('throughput', {
                'endpoint': endpoint,
                'throughput': requests_per_second,
                'benchmark': benchmark_result
            })
            
        except Exception as e:
            logger.error(f"Failed to track throughput: {e}")
    
    async def track_error_rate(self, endpoint: str, total_requests: int, 
                             errors: int):
        """Track error rate"""
        try:
            if total_requests == 0:
                return
            
            error_rate = errors / total_requests
            timestamp = datetime.now()
            key = endpoint
            
            data_point = {
                'timestamp': timestamp.isoformat(),
                'error_rate': error_rate,
                'total_requests': total_requests,
                'errors': errors
            }
            
            self.metrics_store['error_rates'][key].append(data_point)
            await self._update_aggregated_data('error_rates', key, data_point)
            
            # Check benchmark
            benchmark_result = self._check_benchmark('error_rate', error_rate)
            if benchmark_result.get('level') in ['poor', 'fair']:
                await self._trigger_performance_alert(
                    'error_rate', endpoint, error_rate, benchmark_result
                )
            
            await self._notify_callbacks('error_rate', {
                'endpoint': endpoint,
                'error_rate': error_rate,
                'total_requests': total_requests,
                'errors': errors,
                'benchmark': benchmark_result
            })
            
        except Exception as e:
            logger.error(f"Failed to track error rate: {e}")
    
    async def track_resource_usage(self, resource_type: str, 
                                 usage_percent: float):
        """Track resource usage"""
        try:
            timestamp = datetime.now()
            key = resource_type
            
            data_point = {
                'timestamp': timestamp.isoformat(),
                'usage_percent': usage_percent
            }
            
            self.metrics_store['resource_usage'][key].append(data_point)
            await self._update_aggregated_data('resource_usage', key, data_point)
            
            # Check benchmark
            benchmark_key = f"{resource_type}_usage"
            if benchmark_key in self.benchmarks:
                benchmark_result = self._check_benchmark(benchmark_key, usage_percent)
                if benchmark_result.get('level') in ['poor', 'fair']:
                    await self._trigger_performance_alert(
                        benchmark_key, resource_type, usage_percent, benchmark_result
                    )
            
            await self._notify_callbacks('resource_usage', {
                'resource_type': resource_type,
                'usage_percent': usage_percent
            })
            
        except Exception as e:
            logger.error(f"Failed to track resource usage: {e}")
    
    async def track_business_metric(self, metric_name: str, value: float, 
                                  dimensions: Dict = None):
        """Track business metrics"""
        try:
            timestamp = datetime.now()
            key = metric_name
            
            data_point = {
                'timestamp': timestamp.isoformat(),
                'value': value,
                'dimensions': dimensions or {}
            }
            
            self.metrics_store['business_metrics'][key].append(data_point)
            await self._update_aggregated_data('business_metrics', key, data_point)
            
            await self._notify_callbacks('business_metric', {
                'metric_name': metric_name,
                'value': value,
                'dimensions': dimensions
            })
            
        except Exception as e:
            logger.error(f"Failed to track business metric: {e}")
    
    async def _update_aggregated_data(self, metric_type: str, key: str, 
                                    data_point: Dict):
        """Update aggregated performance data"""
        try:
            timestamp = datetime.fromisoformat(data_point['timestamp'])
            
            # Update hourly data
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            if hour_key not in self.performance_data['hourly'][key]:
                self.performance_data['hourly'][key][hour_key] = {
                    'count': 0,
                    'sum': 0,
                    'min': float('inf'),
                    'max': float('-inf'),
                    'values': []
                }
            
            hourly_data = self.performance_data['hourly'][key][hour_key]
            value = data_point.get('response_time') or data_point.get('throughput') or \
                   data_point.get('error_rate') or data_point.get('usage_percent') or \
                   data_point.get('value')
            
            if value is not None:
                hourly_data['count'] += 1
                hourly_data['sum'] += value
                hourly_data['min'] = min(hourly_data['min'], value)
                hourly_data['max'] = max(hourly_data['max'], value)
                hourly_data['values'].append(value)
            
            # Update daily data (once per day)
            day_key = timestamp.strftime('%Y-%m-%d')
            if day_key not in self.performance_data['daily'][key]:
                # Calculate daily aggregate from hourly data
                self._calculate_daily_aggregate(key, day_key)
            
            # Update weekly data (once per week)
            week_key = timestamp.strftime('%Y-W%W')
            if week_key not in self.performance_data['weekly'][key]:
                self._calculate_weekly_aggregate(key, week_key)
            
        except Exception as e:
            logger.error(f"Failed to update aggregated data: {e}")
    
    def _calculate_daily_aggregate(self, key: str, day_key: str):
        """Calculate daily aggregate from hourly data"""
        hourly_data_for_day = {}
        
        # Find all hourly entries for this day
        for hour_key, hourly_data in self.performance_data['hourly'][key].items():
            if hour_key.startswith(day_key):
                hourly_data_for_day[hour_key] = hourly_data
        
        if not hourly_data_for_day:
            return
        
        # Calculate aggregates
        all_values = []
        for hourly_data in hourly_data_for_day.values():
            all_values.extend(hourly_data['values'])
        
        if all_values:
            self.performance_data['daily'][key][day_key] = {
                'count': len(all_values),
                'sum': sum(all_values),
                'avg': statistics.mean(all_values),
                'min': min(all_values),
                'max': max(all_values),
                'p50': statistics.median(all_values),
                'p95': self._calculate_percentile(all_values, 95),
                'p99': self._calculate_percentile(all_values, 99)
            }
    
    def _calculate_weekly_aggregate(self, key: str, week_key: str):
        """Calculate weekly aggregate from daily data"""
        daily_data_for_week = {}
        
        # Find all daily entries for this week
        for day_key, daily_data in self.performance_data['daily'][key].items():
            if datetime.strptime(day_key, '%Y-%m-%d').strftime('%Y-W%W') == week_key:
                daily_data_for_week[day_key] = daily_data
        
        if not daily_data_for_week:
            return
        
        # Calculate aggregates from daily averages
        daily_averages = [data['avg'] for data in daily_data_for_week.values()]
        
        self.performance_data['weekly'][key][week_key] = {
            'count': len(daily_averages),
            'avg': statistics.mean(daily_averages),
            'min': min(daily_averages),
            'max': max(daily_averages),
            'p50': statistics.median(daily_averages),
            'p95': self._calculate_percentile(daily_averages, 95)
        }
    
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            fraction = index - int(index)
            return lower + fraction * (upper - lower)
    
    def _check_benchmark(self, metric_type: str, value: float) -> Dict[str, Any]:
        """Check value against benchmarks"""
        benchmarks = self.benchmarks.get(metric_type, {})
        
        if not benchmarks:
            return {'level': 'unknown', 'benchmark': None}
        
        # Determine performance level
        if 'excellent' in benchmarks and value <= benchmarks['excellent']:
            level = 'excellent'
        elif 'good' in benchmarks and value <= benchmarks['good']:
            level = 'good'
        elif 'fair' in benchmarks and value <= benchmarks['fair']:
            level = 'fair'
        else:
            level = 'poor'
        
        return {
            'level': level,
            'benchmark': benchmarks.get(level),
            'value': value,
            'metric_type': metric_type
        }
    
    async def _trigger_performance_alert(self, metric_type: str, resource: str,
                                       value: float, benchmark_result: Dict):
        """Trigger performance alert"""
        try:
            alert_message = f"Performance {metric_type} for {resource}: {value:.4f} ({benchmark_result['level']})"
            
            # Import alert system
            from monitoring.alert_system import AlertSystem, AlertLevel
            alert_system = AlertSystem()
            
            alert_level = AlertLevel.WARNING if benchmark_result['level'] == 'fair' else AlertLevel.CRITICAL
            
            # Create custom alert
            custom_rule = {
                'id': f'performance_{metric_type}_{resource}',
                'name': f'Performance Issue: {metric_type}',
                'condition': lambda metrics: True,  # Always true for manual trigger
                'level': alert_level,
                'message_template': alert_message,
                'channels': ['console'],
                'cooldown_minutes': 5
            }
            
            await alert_system.add_custom_rule(custom_rule)
            
            # Trigger alert
            await alert_system.process_metrics({
                'timestamp': datetime.now().isoformat(),
                metric_type: value
            })
            
        except Exception as e:
            logger.error(f"Failed to trigger performance alert: {e}")
    
    async def _notify_callbacks(self, event_type: str, data: Dict):
        """Notify registered callbacks"""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def get_performance_report(self, metric_type: str = None, 
                                   period: str = 'daily',
                                   start_date: str = None,
                                   end_date: str = None) -> Dict[str, Any]:
        """Get performance report"""
        try:
            if period not in ['hourly', 'daily', 'weekly']:
                period = 'daily'
            
            report = {
                'period': period,
                'generated_at': datetime.now().isoformat(),
                'metrics': {}
            }
            
            # Determine date range
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get data for specified metric type or all metrics
            if metric_type and metric_type in self.performance_data[period]:
                metric_data = self._filter_by_date_range(
                    self.performance_data[period][metric_type],
                    start_date, end_date, period
                )
                report['metrics'][metric_type] = metric_data
            else:
                for metric_key, metric_data in self.performance_data[period].items():
                    if metric_type is None or metric_type in metric_key:
                        filtered_data = self._filter_by_date_range(
                            metric_data, start_date, end_date, period
                        )
                        report['metrics'][metric_key] = filtered_data
            
            # Calculate summary statistics
            report['summary'] = self._calculate_report_summary(report['metrics'])
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {'error': str(e)}
    
    def _filter_by_date_range(self, data: Dict, start_date: str, 
                            end_date: str, period: str) -> Dict:
        """Filter data by date range"""
        filtered = {}
        
        for date_key, values in data.items():
            if period == 'hourly':
                # Hourly keys: '2024-01-01 10:00'
                date_part = date_key.split(' ')[0]
            else:
                # Daily keys: '2024-01-01', Weekly keys: '2024-W01'
                date_part = date_key
            
            if start_date <= date_part <= end_date:
                filtered[date_key] = values
        
        return filtered
    
    def _calculate_report_summary(self, metrics_data: Dict) -> Dict[str, Any]:
        """Calculate summary statistics for report"""
        summary = {
            'total_metrics': len(metrics_data),
            'time_periods': 0,
            'performance_levels': {
                'excellent': 0,
                'good': 0,
                'fair': 0,
                'poor': 0
            }
        }
        
        all_values = []
        
        for metric_name, period_data in metrics_data.items():
            for period_key, data in period_data.items():
                summary['time_periods'] += 1
                
                if 'avg' in data:
                    all_values.append(data['avg'])
                    
                    # Check performance level
                    benchmark_result = self._check_benchmark(
                        metric_name.split(':')[0] if ':' in metric_name else metric_name,
                        data['avg']
                    )
                    summary['performance_levels'][benchmark_result['level']] += 1
        
        if all_values:
            summary['overall_avg'] = statistics.mean(all_values)
            summary['overall_min'] = min(all_values)
            summary['overall_max'] = max(all_values)
            summary['overall_p95'] = self._calculate_percentile(all_values, 95)
        
        return summary
    
    async def get_endpoint_performance(self, endpoint: str) -> Dict[str, Any]:
        """Get detailed performance for specific endpoint"""
        try:
            endpoint_data = {}
            
            # Get response times
            response_key = f"GET:{endpoint}"  # Assuming GET method
            if response_key in self.metrics_store['response_times']:
                recent_times = list(self.metrics_store['response_times'][response_key])
                if recent_times:
                    times = [rt['response_time'] for rt in recent_times[-100:]]  # Last 100
                    endpoint_data['response_times'] = {
                        'recent': times[-10:],  # Last 10
                        'avg': statistics.mean(times) if times else 0,
                        'p95': self._calculate_percentile(times, 95) if times else 0,
                        'p99': self._calculate_percentile(times, 99) if times else 0,
                        'min': min(times) if times else 0,
                        'max': max(times) if times else 0
                    }
            
            # Get error rates
            if endpoint in self.metrics_store['error_rates']:
                error_rates = list(self.metrics_store['error_rates'][endpoint])
                if error_rates:
                    rates = [er['error_rate'] for er in error_rates[-100:]]
                    endpoint_data['error_rates'] = {
                        'current': rates[-1] if rates else 0,
                        'avg': statistics.mean(rates) if rates else 0,
                        'trend': self._calculate_trend(rates)
                    }
            
            # Get throughput
            if endpoint in self.metrics_store['throughput']:
                throughputs = list(self.metrics_store['throughput'][endpoint])
                if throughputs:
                    tps = [tp['throughput'] for tp in throughputs[-100:]]
                    endpoint_data['throughput'] = {
                        'current': tps[-1] if tps else 0,
                        'avg': statistics.mean(tps) if tps else 0,
                        'peak': max(tps) if tps else 0
                    }
            
            # Calculate performance score
            endpoint_data['performance_score'] = self._calculate_performance_score(endpoint_data)
            
            # Get recommendations
            endpoint_data['recommendations'] = self._generate_recommendations(endpoint_data)
            
            return endpoint_data
            
        except Exception as e:
            logger.error(f"Failed to get endpoint performance: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return 'stable'
        
        recent = values[-5:]  # Last 5 values
        if len(recent) < 2:
            return 'stable'
        
        # Simple linear trend
        x = list(range(len(recent)))
        y = recent
        
        try:
            # Calculate slope
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x_i * x_i for x_i in x)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'stable'
        except:
            return 'stable'
    
    def _calculate_performance_score(self, endpoint_data: Dict) -> float:
        """Calculate performance score (0-100)"""
        score = 100
        
        # Deduct for high response times
        if 'response_times' in endpoint_data:
            avg_response = endpoint_data['response_times'].get('avg', 0)
            if avg_response > 1.0:
                score -= 30
            elif avg_response > 0.5:
                score -= 20
            elif avg_response > 0.3:
                score -= 10
        
        # Deduct for high error rates
        if 'error_rates' in endpoint_data:
            avg_error_rate = endpoint_data['error_rates'].get('avg', 0)
            score -= avg_error_rate * 1000  # Scale appropriately
        
        # Deduct for low throughput
        if 'throughput' in endpoint_data:
            avg_throughput = endpoint_data['throughput'].get('avg', 0)
            if avg_throughput < 10:
                score -= 20
            elif avg_throughput < 50:
                score -= 10
        
        return max(0, min(100, round(score, 1)))
    
    def _generate_recommendations(self, endpoint_data: Dict) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Check response times
        if 'response_times' in endpoint_data:
            avg_response = endpoint_data['response_times'].get('avg', 0)
            if avg_response > 1.0:
                recommendations.append("Consider optimizing database queries")
            elif avg_response > 0.5:
                recommendations.append("Implement caching for frequent requests")
            elif avg_response > 0.3:
                recommendations.append("Review endpoint logic for optimizations")
        
        # Check error rates
        if 'error_rates' in endpoint_data:
            avg_error_rate = endpoint_data['error_rates'].get('avg', 0)
            if avg_error_rate > 0.05:
                recommendations.append("Investigate and fix frequent errors")
            elif avg_error_rate > 0.01:
                recommendations.append("Add better error handling and logging")
        
        # Check throughput
        if 'throughput' in endpoint_data:
            avg_throughput = endpoint_data['throughput'].get('avg', 0)
            if avg_throughput < 10:
                recommendations.append("Consider horizontal scaling")
            elif avg_throughput < 50:
                recommendations.append("Optimize resource usage")
        
        return recommendations
    
    async def register_callback(self, callback: Callable):
        """Register callback for performance events"""
        self.callbacks.append(callback)
    
    async def unregister_callback(self, callback: Callable):
        """Unregister callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def cleanup_old_data(self):
        """Cleanup old performance data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Cleanup metrics store
            for metric_type in self.metrics_store:
                for key in list(self.metrics_store[metric_type].keys()):
                    # Keep only recent data points
                    data_points = list(self.metrics_store[metric_type][key])
                    recent_points = [
                        dp for dp in data_points 
                        if datetime.fromisoformat(dp['timestamp']) > cutoff_date
                    ]
                    self.metrics_store[metric_type][key] = deque(recent_points, maxlen=10000)
            
            # Cleanup aggregated data
            for period in self.performance_data:
                for metric_key in list(self.performance_data[period].keys()):
                    for date_key in list(self.performance_data[period][metric_key].keys()):
                        if period == 'hourly':
                            # Hourly keys: '2024-01-01 10:00'
                            date_part = date_key.split(' ')[0]
                        else:
                            date_part = date_key
                        
                        if datetime.strptime(date_part, '%Y-%m-%d' if period != 'weekly' else '%Y-W%W') < cutoff_date:
                            del self.performance_data[period][metric_key][date_key]
            
            logger.info(f"Cleaned up performance data older than {self.retention_days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")