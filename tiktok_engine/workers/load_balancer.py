"""
Load Balancer - Intelligent task distribution
"""

import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

class LoadBalancer:
    """Intelligent load balancer for view distribution"""
    
    def __init__(self):
        self.workers = {}
        self.worker_groups = defaultdict(list)
        self.task_history = []
        self.performance_metrics = {}
        self.distribution_strategies = [
            'round_robin',
            'weighted',
            'performance_based',
            'geographic',
            'intelligent'
        ]
        
    def register_worker(self, worker_id: str, worker_info: Dict):
        """Register a worker"""
        self.workers[worker_id] = worker_info
        worker_type = worker_info.get('type', 'generic')
        self.worker_groups[worker_type].append(worker_id)
        
        print(f"📋 Registered worker {worker_id} ({worker_type})")
    
    def unregister_worker(self, worker_id: str):
        """Unregister a worker"""
        if worker_id in self.workers:
            worker_info = self.workers[worker_id]
            worker_type = worker_info.get('type', 'generic')
            
            if worker_id in self.worker_groups[worker_type]:
                self.worker_groups[worker_type].remove(worker_id)
            
            del self.workers[worker_id]
            
            print(f"🗑️ Unregistered worker {worker_id}")
    
    async def distribute_task(self, task: Dict, strategy: str = 'intelligent') -> Optional[str]:
        """Distribute task to optimal worker"""
        if not self.workers:
            return None
        
        if strategy == 'round_robin':
            worker_id = self.round_robin(task)
        elif strategy == 'weighted':
            worker_id = self.weighted_distribution(task)
        elif strategy == 'performance_based':
            worker_id = self.performance_based(task)
        elif strategy == 'geographic':
            worker_id = self.geographic_distribution(task)
        else:  # intelligent
            worker_id = self.intelligent_distribution(task)
        
        if worker_id:
            self.record_distribution(task, worker_id, strategy)
        
        return worker_id
    
    def round_robin(self, task: Dict) -> Optional[str]:
        """Round-robin distribution"""
        suitable_workers = self.get_suitable_workers(task)
        
        if not suitable_workers:
            return None
        
        # Get next worker in sequence
        task_type = task.get('type', 'generic')
        if task_type not in self.worker_groups:
            task_type = 'generic'
        
        workers = self.worker_groups[task_type]
        if not workers:
            return None
        
        # Simple round-robin
        if not hasattr(self, '_rr_index'):
            self._rr_index = {}
        
        if task_type not in self._rr_index:
            self._rr_index[task_type] = 0
        
        index = self._rr_index[task_type]
        worker_id = workers[index % len(workers)]
        self._rr_index[task_type] = (index + 1) % len(workers)
        
        return worker_id
    
    def weighted_distribution(self, task: Dict) -> Optional[str]:
        """Weighted distribution based on capacity"""
        suitable_workers = self.get_suitable_workers(task)
        
        if not suitable_workers:
            return None
        
        # Calculate weights based on worker capacity
        weights = []
        worker_list = []
        
        for worker_id in suitable_workers:
            worker = self.workers[worker_id]
            
            # Weight based on success rate and current load
            success_weight = worker.get('success_rate', 0.5)
            load_weight = 1.0 - (worker.get('current_tasks', 0) / worker.get('max_tasks', 10))
            
            total_weight = success_weight * load_weight
            weights.append(total_weight)
            worker_list.append(worker_id)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(worker_list)
        
        normalized_weights = [w / total_weight for w in weights]
        
        # Select worker based on weights
        return random.choices(worker_list, weights=normalized_weights, k=1)[0]
    
    def performance_based(self, task: Dict) -> Optional[str]:
        """Distribution based on historical performance"""
        suitable_workers = self.get_suitable_workers(task)
        
        if not suitable_workers:
            return None
        
        # Get performance for similar tasks
        similar_tasks = self.get_similar_tasks(task)
        
        # Calculate performance scores
        scores = {}
        for worker_id in suitable_workers:
            score = self.calculate_performance_score(worker_id, similar_tasks)
            scores[worker_id] = score
        
        # Select worker with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return random.choice(suitable_workers)
    
    def geographic_distribution(self, task: Dict) -> Optional[str]:
        """Distribution based on geographic requirements"""
        suitable_workers = self.get_suitable_workers(task)
        
        if not suitable_workers:
            return None
        
        task_region = task.get('region', 'global')
        
        if task_region == 'global':
            return random.choice(suitable_workers)
        
        # Filter workers by region
        regional_workers = []
        for worker_id in suitable_workers:
            worker = self.workers[worker_id]
            worker_region = worker.get('region', 'unknown')
            
            if worker_region == task_region or worker_region == 'global':
                regional_workers.append(worker_id)
        
        if regional_workers:
            return random.choice(regional_workers)
        
        # Fallback to any suitable worker
        return random.choice(suitable_workers)
    
    def intelligent_distribution(self, task: Dict) -> Optional[str]:
        """Intelligent distribution using multiple factors"""
        suitable_workers = self.get_suitable_workers(task)
        
        if not suitable_workers:
            return None
        
        # Calculate composite score for each worker
        scores = {}
        for worker_id in suitable_workers:
            score = self.calculate_intelligent_score(worker_id, task)
            scores[worker_id] = score
        
        # Select worker with highest score
        if scores:
            best_worker = max(scores.items(), key=lambda x: x[1])[0]
            
            # Occasionally explore other workers (epsilon-greedy)
            if random.random() < 0.1:  # 10% exploration
                return random.choice(suitable_workers)
            
            return best_worker
        
        return random.choice(suitable_workers)
    
    def calculate_intelligent_score(self, worker_id: str, task: Dict) -> float:
        """Calculate intelligent score for worker"""
        worker = self.workers[worker_id]
        
        # Base score components
        components = {
            'success_rate': worker.get('success_rate', 0.5) * 0.3,
            'current_load': (1.0 - worker.get('load_percentage', 0.5)) * 0.2,
            'response_time': self.get_response_time_score(worker_id) * 0.15,
            'task_similarity': self.get_task_similarity_score(worker_id, task) * 0.2,
            'resource_efficiency': self.get_resource_efficiency(worker) * 0.15
        }
        
        # Additional factors
        if task.get('priority') == 'high':
            components['success_rate'] *= 1.2
        
        if task.get('type') == worker.get('specialty'):
            components['task_similarity'] *= 1.3
        
        # Calculate total score
        total_score = sum(components.values())
        
        return total_score
    
    def get_suitable_workers(self, task: Dict) -> List[str]:
        """Get workers suitable for task"""
        suitable = []
        task_type = task.get('type', 'generic')
        task_requirements = task.get('requirements', {})
        
        for worker_id, worker in self.workers.items():
            if self.is_worker_suitable(worker, task_type, task_requirements):
                suitable.append(worker_id)
        
        return suitable
    
    def is_worker_suitable(self, worker: Dict, task_type: str, 
                          requirements: Dict) -> bool:
        """Check if worker is suitable for task"""
        # Check type compatibility
        worker_types = worker.get('supported_types', [])
        if task_type not in worker_types and 'generic' not in worker_types:
            return False
        
        # Check requirements
        for req_key, req_value in requirements.items():
            worker_value = worker.get(req_key)
            
            if worker_value is None:
                return False
            
            if isinstance(req_value, (int, float)):
                if worker_value < req_value:
                    return False
            elif isinstance(req_value, str):
                if worker_value != req_value:
                    return False
        
        # Check availability
        if worker.get('status') != 'available':
            return False
        
        # Check load
        current_load = worker.get('current_tasks', 0)
        max_load = worker.get('max_tasks', 10)
        
        if current_load >= max_load:
            return False
        
        return True
    
    def get_similar_tasks(self, task: Dict) -> List[Dict]:
        """Get similar tasks from history"""
        similar = []
        task_type = task.get('type')
        
        for hist_task in self.task_history[-100:]:  # Last 100 tasks
            if hist_task.get('type') == task_type:
                similar.append(hist_task)
        
        return similar
    
    def calculate_performance_score(self, worker_id: str, 
                                   similar_tasks: List[Dict]) -> float:
        """Calculate performance score for similar tasks"""
        if not similar_tasks:
            return 0.5  # Default score
        
        # Count successful similar tasks for this worker
        success_count = 0
        total_count = 0
        
        for task in similar_tasks:
            task_worker = task.get('assigned_worker')
            if task_worker == worker_id:
                total_count += 1
                if task.get('success', False):
                    success_count += 1
        
        if total_count == 0:
            return 0.5
        
        return success_count / total_count
    
    def get_response_time_score(self, worker_id: str) -> float:
        """Get response time score (higher is better)"""
        # This would query real metrics in production
        default_times = {
            'browser': 2.5,
            'api': 1.0,
            'cloud': 3.0,
            'mobile': 1.5
        }
        
        worker = self.workers[worker_id]
        worker_type = worker.get('type', 'generic')
        
        avg_time = default_times.get(worker_type, 2.0)
        
        # Convert to score (lower time = higher score)
        score = max(0.1, 1.0 - (avg_time / 10.0))
        
        return score
    
    def get_task_similarity_score(self, worker_id: str, task: Dict) -> float:
        """Get task similarity score"""
        worker = self.workers[worker_id]
        
        # Check if worker has specialty for this task type
        task_type = task.get('type')
        worker_specialty = worker.get('specialty')
        
        if worker_specialty == task_type:
            return 0.9
        
        # Check historical performance on similar tasks
        similar_tasks = self.get_similar_tasks(task)
        if similar_tasks:
            return self.calculate_performance_score(worker_id, similar_tasks)
        
        return 0.5
    
    def get_resource_efficiency(self, worker: Dict) -> float:
        """Get resource efficiency score"""
        # Calculate efficiency based on resource usage
        cpu = worker.get('cpu_usage', 0.5)
        memory = worker.get('memory_usage', 0.5)
        bandwidth = worker.get('bandwidth_usage', 0.5)
        
        # Lower usage = higher efficiency
        cpu_score = 1.0 - cpu
        memory_score = 1.0 - memory
        bandwidth_score = 1.0 - bandwidth
        
        # Weighted average
        efficiency = (cpu_score * 0.4 + memory_score * 0.3 + bandwidth_score * 0.3)
        
        return max(0.1, efficiency)
    
    def record_distribution(self, task: Dict, worker_id: str, strategy: str):
        """Record task distribution"""
        record = {
            'task_id': task.get('task_id'),
            'worker_id': worker_id,
            'strategy': strategy,
            'timestamp': datetime.now().isoformat(),
            'task_type': task.get('type'),
            'task_priority': task.get('priority')
        }
        
        self.task_history.append(record)
        
        # Keep history limited
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]
    
    async def analyze_distribution(self) -> Dict:
        """Analyze distribution performance"""
        if not self.task_history:
            return {'no_data': True}
        
        # Calculate success rates by strategy
        strategy_stats = {}
        
        for record in self.task_history[-500:]:  # Last 500 records
            strategy = record['strategy']
            
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'total': 0,
                    'successful': 0,
                    'workers_used': set()
                }
            
            stats = strategy_stats[strategy]
            stats['total'] += 1
            
            # Check if task was successful (this would query task results)
            # For now, assume 80% success rate
            if random.random() < 0.8:
                stats['successful'] += 1
            
            stats['workers_used'].add(record['worker_id'])
        
        # Calculate metrics
        analysis = {}
        for strategy, stats in strategy_stats.items():
            total = stats['total']
            successful = stats['successful']
            
            analysis[strategy] = {
                'total_tasks': total,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'unique_workers': len(stats['workers_used']),
                'tasks_per_worker': total / len(stats['workers_used']) if stats['workers_used'] else 0
            }
        
        # Overall metrics
        total_tasks = sum(s['total'] for s in strategy_stats.values())
        total_successful = sum(s['successful'] for s in strategy_stats.values())
        
        return {
            'strategy_analysis': analysis,
            'overall_success_rate': (total_successful / total_tasks * 100) if total_tasks > 0 else 0,
            'total_tasks_analyzed': total_tasks,
            'unique_workers_used': len(set(
                w for s in strategy_stats.values() 
                for w in s['workers_used']
            )),
            'recommended_strategy': max(
                analysis.items(),
                key=lambda x: x[1]['success_rate']
            )[0] if analysis else 'intelligent'
        }
    
    async def optimize_distribution(self):
        """Optimize distribution based on analysis"""
        analysis = await self.analyze_distribution()
        
        if 'no_data' in analysis:
            return
        
        # Get best performing strategy
        best_strategy = analysis.get('recommended_strategy', 'intelligent')
        
        print(f"🎯 Optimization complete. Best strategy: {best_strategy}")
        
        # Update worker scores based on performance
        self.update_worker_scores()
        
        return best_strategy
    
    def update_worker_scores(self):
        """Update worker performance scores"""
        for worker_id in self.workers:
            worker = self.workers[worker_id]
            
            # Calculate new score based on recent performance
            recent_tasks = [
                t for t in self.task_history[-100:]
                if t['worker_id'] == worker_id
            ]
            
            if recent_tasks:
                success_count = sum(1 for t in recent_tasks if random.random() < 0.8)  # Placeholder
                new_success_rate = success_count / len(recent_tasks)
                
                # Update with moving average
                current_rate = worker.get('success_rate', 0.5)
                updated_rate = current_rate * 0.7 + new_success_rate * 0.3
                
                worker['success_rate'] = updated_rate
                
                # Update performance metrics
                self.performance_metrics[worker_id] = {
                    'success_rate': updated_rate,
                    'tasks_completed': len(recent_tasks),
                    'last_updated': datetime.now().isoformat()
                }