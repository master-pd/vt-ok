"""
Worker Pool - Advanced worker management
"""

import asyncio
import random
from typing import Dict, List, Optional, Callable
from datetime import datetime
import uuid

class WorkerPool:
    """Advanced worker pool with load balancing"""
    
    def __init__(self, max_workers: int = 20):
        self.max_workers = max_workers
        self.workers = {}
        self.task_queue = asyncio.Queue()
        self.results = {}
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_runtime': 0,
            'avg_success_rate': 0.0
        }
        self.is_running = False
        self.worker_types = ['browser', 'api', 'mobile', 'cloud', 'hybrid']
        
    async def start(self):
        """Start worker pool"""
        print(f"🚀 Starting worker pool with {self.max_workers} workers...")
        
        self.is_running = True
        
        # Create initial workers
        for i in range(self.max_workers):
            worker_id = f"worker_{uuid.uuid4().hex[:8]}"
            await self.create_worker(worker_id)
        
        # Start task processor
        asyncio.create_task(self.process_tasks())
        
        # Start health monitor
        asyncio.create_task(self.health_monitor())
        
        print(f"✅ Worker pool started with {len(self.workers)} workers")
        return True
    
    async def create_worker(self, worker_id: str, worker_type: str = None):
        """Create a new worker"""
        if worker_type is None:
            worker_type = random.choice(self.worker_types)
        
        worker = {
            'id': worker_id,
            'type': worker_type,
            'status': 'idle',
            'created_at': datetime.now(),
            'last_active': datetime.now(),
            'tasks_completed': 0,
            'tasks_failed': 0,
            'success_rate': 1.0,
            'current_task': None,
            'performance_score': 1.0,
            'resources': {
                'cpu': random.uniform(0.1, 0.5),
                'memory': random.uniform(100, 500),  # MB
                'bandwidth': random.uniform(1, 10)  # Mbps
            }
        }
        
        self.workers[worker_id] = worker
        print(f"👷 Created {worker_type} worker: {worker_id}")
        
        # Start worker loop
        asyncio.create_task(self.worker_loop(worker_id))
        
        return worker_id
    
    async def worker_loop(self, worker_id: str):
        """Worker main loop"""
        worker = self.workers[worker_id]
        
        while self.is_running:
            try:
                # Wait for task
                task = await self.get_task_for_worker(worker_id)
                if not task:
                    await asyncio.sleep(0.1)
                    continue
                
                # Execute task
                result = await self.execute_task(worker, task)
                
                # Update worker stats
                worker['last_active'] = datetime.now()
                worker['tasks_completed'] += 1
                
                if result.get('success', False):
                    worker['success_rate'] = (
                        worker['success_rate'] * 0.9 + 0.1
                    )  # Moving average
                else:
                    worker['tasks_failed'] += 1
                    worker['success_rate'] = (
                        worker['success_rate'] * 0.9
                    )  # Decrease on failure
                
                # Update performance score
                worker['performance_score'] = self.calculate_performance_score(worker)
                
                # Store result
                self.results[task['task_id']] = result
                
                # Mark task as done
                self.task_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
    
    async def get_task_for_worker(self, worker_id: str) -> Optional[Dict]:
        """Get appropriate task for worker"""
        worker = self.workers[worker_id]
        
        # Check if worker is suitable for any queued tasks
        # This is simplified - in production, match tasks to worker capabilities
        
        try:
            # Peek at next task
            task = self.task_queue._queue[0] if self.task_queue._queue else None
            
            if task and self.is_worker_suitable(worker, task):
                return await self.task_queue.get()
            
            return None
            
        except IndexError:
            return None
    
    def is_worker_suitable(self, worker: Dict, task: Dict) -> bool:
        """Check if worker is suitable for task"""
        worker_type = worker['type']
        task_method = task.get('method', 'any')
        
        if task_method == 'any':
            return True
        
        # Type compatibility matrix
        compatibility = {
            'browser': ['browser', 'organic', 'high_quality'],
            'api': ['api', 'fast', 'mobile'],
            'mobile': ['mobile', 'api', 'fast'],
            'cloud': ['cloud', 'bulk', 'scalable'],
            'hybrid': ['any', 'hybrid', 'optimal']
        }
        
        if task_method in compatibility.get(worker_type, []):
            return True
        
        # Check performance requirements
        task_priority = task.get('priority', 'normal')
        if task_priority == 'high' and worker['performance_score'] < 0.7:
            return False
        
        return True
    
    async def execute_task(self, worker: Dict, task: Dict) -> Dict:
        """Execute task with worker"""
        worker_id = worker['id']
        task_id = task['task_id']
        
        print(f"⚡ Worker {worker_id} executing task {task_id}")
        
        worker['status'] = 'busy'
        worker['current_task'] = task_id
        
        start_time = datetime.now()
        
        try:
            # Simulate task execution
            await asyncio.sleep(random.uniform(0.5, 3.0))
            
            # Simulate success/failure
            success = random.random() < worker['success_rate']
            
            result = {
                'task_id': task_id,
                'worker_id': worker_id,
                'success': success,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'method_used': worker['type'],
                'result_data': task.get('data', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                print(f"✅ Worker {worker_id} completed task {task_id}")
            else:
                print(f"❌ Worker {worker_id} failed task {task_id}")
            
            return result
            
        except Exception as e:
            return {
                'task_id': task_id,
                'worker_id': worker_id,
                'success': False,
                'error': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            worker['status'] = 'idle'
            worker['current_task'] = None
    
    def calculate_performance_score(self, worker: Dict) -> float:
        """Calculate worker performance score"""
        success_rate = worker['success_rate']
        tasks_completed = worker['tasks_completed']
        uptime = (datetime.now() - worker['created_at']).total_seconds() / 3600  # hours
        
        # Base score from success rate
        score = success_rate
        
        # Bonus for experience (more tasks)
        if tasks_completed > 10:
            experience_bonus = min(0.2, tasks_completed / 100)
            score += experience_bonus
        
        # Bonus for uptime
        if uptime > 1:  # More than 1 hour
            uptime_bonus = min(0.1, uptime / 10)
            score += uptime_bonus
        
        # Penalty for recent failures
        failure_penalty = worker['tasks_failed'] * 0.05
        score -= failure_penalty
        
        return max(0.1, min(1.0, score))  # Clamp between 0.1 and 1.0
    
    async def add_task(self, task: Dict, priority: int = 0):
        """Add task to queue with priority"""
        task['added_at'] = datetime.now()
        task['priority'] = priority
        
        await self.task_queue.put(task)
        
        print(f"📝 Task added: {task.get('task_id', 'unknown')}")
        return True
    
    async def add_batch_tasks(self, tasks: List[Dict]):
        """Add batch of tasks"""
        for task in tasks:
            await self.add_task(task)
        
        print(f"📦 Added {len(tasks)} tasks to queue")
        return True
    
    async def process_tasks(self):
        """Process tasks from queue"""
        print("🔄 Task processor started")
        
        while self.is_running:
            try:
                # Check queue status
                queue_size = self.task_queue.qsize()
                
                if queue_size > len(self.workers) * 5:
                    # Queue too large, scale up workers
                    await self.scale_up()
                elif queue_size < len(self.workers) and len(self.workers) > 5:
                    # Queue small, scale down
                    await self.scale_down()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"❌ Task processor error: {e}")
                await asyncio.sleep(10)
    
    async def scale_up(self):
        """Scale up workers"""
        current_count = len(self.workers)
        
        if current_count >= self.max_workers:
            return
        
        # Calculate how many workers to add
        queue_size = self.task_queue.qsize()
        needed_workers = min(
            queue_size // 10,  # 1 worker per 10 tasks
            self.max_workers - current_count
        )
        
        if needed_workers > 0:
            print(f"📈 Scaling up: adding {needed_workers} workers")
            
            for _ in range(needed_workers):
                worker_id = f"worker_{uuid.uuid4().hex[:8]}"
                await self.create_worker(worker_id)
    
    async def scale_down(self):
        """Scale down workers"""
        current_count = len(self.workers)
        
        if current_count <= 5:  # Keep minimum 5 workers
            return
        
        # Find lowest performing workers
        workers_by_performance = sorted(
            self.workers.items(),
            key=lambda x: x[1]['performance_score']
        )
        
        # Remove up to 2 lowest performers
        to_remove = min(2, current_count - 5)
        
        for i in range(to_remove):
            worker_id, worker = workers_by_performance[i]
            
            # Only remove idle workers
            if worker['status'] == 'idle':
                await self.remove_worker(worker_id)
                print(f"📉 Removed low-performing worker: {worker_id}")
    
    async def remove_worker(self, worker_id: str):
        """Remove worker from pool"""
        if worker_id in self.workers:
            del self.workers[worker_id]
            return True
        return False
    
    async def health_monitor(self):
        """Monitor worker health"""
        print("🏥 Health monitor started")
        
        while self.is_running:
            try:
                unhealthy_workers = []
                
                for worker_id, worker in self.workers.items():
                    # Check if worker is responsive
                    last_active = worker['last_active']
                    inactive_time = (datetime.now() - last_active).total_seconds()
                    
                    if inactive_time > 300:  # 5 minutes
                        unhealthy_workers.append(worker_id)
                    
                    # Check resource usage
                    resources = worker['resources']
                    if resources['cpu'] > 0.9 or resources['memory'] > 800:
                        print(f"⚠️ Worker {worker_id} high resource usage")
                
                # Restart unhealthy workers
                for worker_id in unhealthy_workers:
                    print(f"🔄 Restarting unhealthy worker: {worker_id}")
                    await self.restart_worker(worker_id)
                
                # Update pool statistics
                await self.update_stats()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"❌ Health monitor error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def restart_worker(self, worker_id: str):
        """Restart a worker"""
        if worker_id in self.workers:
            worker = self.workers[worker_id]
            
            # Create new worker with same type
            new_id = f"worker_{uuid.uuid4().hex[:8]}"
            await self.create_worker(new_id, worker['type'])
            
            # Remove old worker
            await self.remove_worker(worker_id)
            
            print(f"🔄 Worker {worker_id} restarted as {new_id}")
            return new_id
        
        return None
    
    async def update_stats(self):
        """Update pool statistics"""
        total_tasks = sum(w['tasks_completed'] for w in self.workers.values())
        failed_tasks = sum(w['tasks_failed'] for w in self.workers.values())
        
        if total_tasks > 0:
            success_rate = ((total_tasks - failed_tasks) / total_tasks) * 100
        else:
            success_rate = 0
        
        self.stats.update({
            'tasks_completed': total_tasks,
            'tasks_failed': failed_tasks,
            'avg_success_rate': success_rate,
            'active_workers': sum(1 for w in self.workers.values() if w['status'] == 'busy'),
            'idle_workers': sum(1 for w in self.workers.values() if w['status'] == 'idle'),
            'queue_size': self.task_queue.qsize()
        })
    
    async def get_stats(self) -> Dict:
        """Get pool statistics"""
        await self.update_stats()
        
        # Worker type distribution
        type_distribution = {}
        for worker in self.workers.values():
            worker_type = worker['type']
            type_distribution[worker_type] = type_distribution.get(worker_type, 0) + 1
        
        return {
            **self.stats,
            'total_workers': len(self.workers),
            'worker_distribution': type_distribution,
            'avg_performance_score': sum(
                w['performance_score'] for w in self.workers.values()
            ) / max(1, len(self.workers)),
            'uptime': (
                datetime.now() - min(
                    w['created_at'] for w in self.workers.values()
                )
            ).total_seconds() / 3600 if self.workers else 0
        }
    
    async def stop(self):
        """Stop worker pool"""
        print("🛑 Stopping worker pool...")
        
        self.is_running = False
        
        # Wait for tasks to complete
        print("⏳ Waiting for tasks to complete...")
        await self.task_queue.join()
        
        # Clear workers
        self.workers.clear()
        
        print("✅ Worker pool stopped")
    
    async def emergency_stop(self):
        """Emergency stop - kill all workers immediately"""
        print("🚨 EMERGENCY STOP - Killing all workers!")
        
        self.is_running = False
        self.workers.clear()
        
        # Clear task queue
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except:
                pass
        
        print("✅ Emergency stop complete")