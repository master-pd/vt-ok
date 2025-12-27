"""
Worker Manager - Control multiple view workers
"""

import asyncio
import random
from typing import List, Dict
from datetime import datetime
from ..view_methods.browser_v3 import UltraBrowserV3
from ..view_methods.api_v2 import MobileAPIPro
from ..view_methods.cloud_view import CloudHybrid
from ..view_methods.hybrid_ai import AIPowered

class WorkerManager:
    """Manager for multiple view workers"""
    
    def __init__(self):
        self.workers = []
        self.active_workers = 0
        self.max_workers = 10
        self.task_queue = asyncio.Queue()
        self.results = []
        self.is_running = False
        
        # Available methods
        self.methods = {
            'browser_v3': UltraBrowserV3,
            'api_v2': MobileAPIPro,
            'cloud': CloudHybrid,
            'ai': AIPowered
        }
        
    async def start(self, worker_count: int = 5):
        """Start worker pool"""
        print(f"🚀 Starting {worker_count} workers...")
        
        self.is_running = True
        
        # Create workers
        for i in range(worker_count):
            worker = await self.create_worker(f"worker_{i+1}")
            self.workers.append(worker)
        
        self.active_workers = worker_count
        print(f"✅ {worker_count} workers started")
        
        # Start task processor
        asyncio.create_task(self.process_tasks())
        
        return True
    
    async def create_worker(self, worker_id: str):
        """Create a new worker"""
        # Randomly select a method
        method_name = random.choice(list(self.methods.keys()))
        method_class = self.methods[method_name]
        
        worker = {
            'id': worker_id,
            'method': method_name,
            'instance': method_class(),
            'status': 'idle',
            'tasks_completed': 0,
            'last_active': datetime.now(),
            'success_rate': 0.0
        }
        
        # Initialize worker instance
        await worker['instance'].__aenter__()
        
        print(f"👷 Worker {worker_id} created with {method_name}")
        return worker
    
    async def process_tasks(self):
        """Process tasks from queue"""
        while self.is_running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                # Assign task to idle worker
                worker = await self.get_idle_worker()
                if worker:
                    asyncio.create_task(
                        self.execute_task(worker, task)
                    )
                else:
                    # No idle workers, requeue
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.5)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Task processor error: {e}")
    
    async def get_idle_worker(self):
        """Get an idle worker"""
        for worker in self.workers:
            if worker['status'] == 'idle':
                return worker
        return None
    
    async def execute_task(self, worker, task):
        """Execute a task with worker"""
        try:
            worker['status'] = 'busy'
            
            # Execute task based on type
            result = await self.execute_view_task(worker, task)
            
            # Update worker stats
            worker['tasks_completed'] += 1
            worker['last_active'] = datetime.now()
            worker['status'] = 'idle'
            
            # Store result
            self.results.append(result)
            
            # Mark task as done
            self.task_queue.task_done()
            
            return result
            
        except Exception as e:
            print(f"❌ Task execution failed: {e}")
            worker['status'] = 'idle'
            return {'error': str(e), 'success': False}
    
    async def execute_view_task(self, worker, task):
        """Execute view sending task"""
        method = worker['method']
        instance = worker['instance']
        
        if method == 'browser_v3':
            result = await instance.send_view(
                video_url=task['video_url'],
                watch_time=task.get('watch_time', 30)
            )
        elif method == 'api_v2':
            result = await instance.send_views_api(
                video_id=task['video_id'],
                count=task.get('count', 1)
            )
        elif method == 'cloud':
            result = await instance.cloud_send_views(
                video_url=task['video_url'],
                count=task.get('count', 1)
            )
        elif method == 'ai':
            result = await instance.ai_send_views(
                video_url=task['video_url'],
                count=task.get('count', 1),
                pattern=task.get('pattern', 'organic')
            )
        else:
            result = {'error': 'Unknown method', 'success': False}
        
        # Add worker info to result
        result['worker_id'] = worker['id']
        result['method'] = method
        
        return result
    
    async def add_task(self, task: Dict):
        """Add task to queue"""
        await self.task_queue.put(task)
        print(f"📝 Task added to queue: {task.get('video_url', 'Unknown')}")
        return True
    
    async def send_views(self, video_url: str, count: int, method: str = None):
        """Send multiple views"""
        print(f"🎯 Sending {count} views to {video_url}")
        
        # Create tasks
        tasks = []
        for i in range(count):
            task = {
                'task_id': f"view_{datetime.now().timestamp()}_{i}",
                'video_url': video_url,
                'video_id': self.extract_video_id(video_url),
                'count': 1,
                'priority': 'normal',
                'timestamp': datetime.now().isoformat()
            }
            
            if method:
                task['method_preference'] = method
            
            tasks.append(task)
        
        # Add tasks to queue
        for task in tasks:
            await self.add_task(task)
        
        # Wait for completion
        await self.task_queue.join()
        
        # Collect results
        successful = sum(1 for r in self.results[-count:] if r.get('success'))
        
        return {
            'total_ordered': count,
            'successful': successful,
            'failed': count - successful,
            'success_rate': f"{(successful/count*100):.1f}%" if count > 0 else "0%",
            'results': self.results[-count:],
            'timestamp': datetime.now().isoformat()
        }
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from TikTok URL"""
        import re
        
        patterns = [
            r'/video/(\d+)',
            r'video/(\d+)',
            r'/(\d+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If no ID found, use hash of URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:10]
    
    async def get_stats(self):
        """Get worker statistics"""
        idle_workers = sum(1 for w in self.workers if w['status'] == 'idle')
        busy_workers = sum(1 for w in self.workers if w['status'] == 'busy')
        
        total_tasks = sum(w['tasks_completed'] for w in self.workers)
        
        # Calculate success rate from recent results
        recent_results = self.results[-100:] if len(self.results) > 100 else self.results
        success_rate = 0
        if recent_results:
            successful = sum(1 for r in recent_results if r.get('success'))
            success_rate = (successful / len(recent_results)) * 100
        
        return {
            'total_workers': len(self.workers),
            'active_workers': self.active_workers,
            'idle_workers': idle_workers,
            'busy_workers': busy_workers,
            'total_tasks': total_tasks,
            'queue_size': self.task_queue.qsize(),
            'success_rate': f"{success_rate:.1f}%",
            'methods_distribution': {
                'browser_v3': sum(1 for w in self.workers if w['method'] == 'browser_v3'),
                'api_v2': sum(1 for w in self.workers if w['method'] == 'api_v2'),
                'cloud': sum(1 for w in self.workers if w['method'] == 'cloud'),
                'ai': sum(1 for w in self.workers if w['method'] == 'ai')
            }
        }
    
    async def stop(self):
        """Stop all workers"""
        print("🛑 Stopping workers...")
        
        self.is_running = False
        
        # Stop all worker instances
        for worker in self.workers:
            try:
                await worker['instance'].__aexit__(None, None, None)
            except:
                pass
        
        self.workers.clear()
        self.active_workers = 0
        
        print("✅ All workers stopped")