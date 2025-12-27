"""
Advanced Task Scheduler for VT ULTRA PRO
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiosqlite

logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    id: str
    video_url: str
    views: int
    schedule_time: datetime
    interval_minutes: Optional[int] = None
    recurring: bool = False
    status: str = "pending"
    priority: int = 5
    user_id: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class TaskScheduler:
    def __init__(self, db_path: str = "database/scheduler.db"):
        self.db_path = db_path
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_task = None
        self.task_queue = asyncio.PriorityQueue()
        
    async def initialize(self):
        """Initialize scheduler database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id TEXT PRIMARY KEY,
                    video_url TEXT,
                    views INTEGER,
                    schedule_time TEXT,
                    interval_minutes INTEGER,
                    recurring INTEGER,
                    status TEXT,
                    priority INTEGER,
                    user_id TEXT,
                    created_at TEXT,
                    completed_at TEXT
                )
            ''')
            await db.commit()
            
            # Load existing tasks
            async with db.execute('SELECT * FROM scheduled_tasks WHERE status IN (?, ?)', ('pending', 'running')) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    task = ScheduledTask(
                        id=row[0],
                        video_url=row[1],
                        views=row[2],
                        schedule_time=datetime.fromisoformat(row[3]),
                        interval_minutes=row[4],
                        recurring=bool(row[5]),
                        status=row[6],
                        priority=row[7],
                        user_id=row[8],
                        created_at=datetime.fromisoformat(row[9]),
                        completed_at=datetime.fromisoformat(row[10]) if row[10] else None
                    )
                    self.tasks[task.id] = task
                    
        logger.info(f"Loaded {len(self.tasks)} tasks from database")
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Task scheduler started")
        
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
        logger.info("Task scheduler stopped")
    
    async def schedule_view_task(self, video_url: str, views: int, 
                               schedule_time: datetime = None,
                               interval_minutes: int = None,
                               recurring: bool = False,
                               priority: int = 5,
                               user_id: str = None) -> str:
        """Schedule a new view task"""
        task_id = str(uuid.uuid4())[:8]
        
        if schedule_time is None:
            schedule_time = datetime.now() + timedelta(minutes=5)
        
        task = ScheduledTask(
            id=task_id,
            video_url=video_url,
            views=views,
            schedule_time=schedule_time,
            interval_minutes=interval_minutes,
            recurring=recurring,
            priority=priority,
            user_id=user_id
        )
        
        self.tasks[task_id] = task
        await self.task_queue.put((-priority, task))
        
        # Save to database
        await self._save_task(task)
        
        logger.info(f"✅ Task {task_id} scheduled: {views} views for {video_url} at {schedule_time}")
        return task_id
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                now = datetime.now()
                
                # Check for tasks to execute
                for task_id, task in list(self.tasks.items()):
                    if task.status == "pending" and task.schedule_time <= now:
                        await self._execute_task(task)
                
                # Process priority queue
                if not self.task_queue.empty():
                    try:
                        _, task = await asyncio.wait_for(self.task_queue.get(), timeout=1)
                        if task.status == "pending" and task.schedule_time <= now:
                            await self._execute_task(task)
                    except asyncio.TimeoutError:
                        pass
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(30)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        try:
            task.status = "running"
            await self._update_task_status(task.id, "running")
            
            # Import load balancer
            from tiktok_engine.workers.load_balancer import ViewLoadBalancer
            
            logger.info(f"🚀 Executing task {task.id}: {task.views} views for {task.video_url}")
            
            balancer = ViewLoadBalancer()
            
            # Send views
            result = await balancer.send_views(
                video_url=task.video_url,
                target_views=task.views,
                priority=task.priority
            )
            
            task.status = "completed"
            task.completed_at = datetime.now()
            await self._update_task_status(task.id, "completed", task.completed_at)
            
            logger.info(f"✅ Task {task.id} completed: {result.get('successful_views', 0)} views sent")
            
            # Handle recurring tasks
            if task.recurring and task.interval_minutes:
                next_time = datetime.now() + timedelta(minutes=task.interval_minutes)
                new_task_id = await self.schedule_view_task(
                    video_url=task.video_url,
                    views=task.views,
                    schedule_time=next_time,
                    interval_minutes=task.interval_minutes,
                    recurring=True,
                    priority=task.priority,
                    user_id=task.user_id
                )
                logger.info(f"🔄 Recurring task scheduled: {new_task_id} at {next_time}")
                
        except Exception as e:
            task.status = "failed"
            await self._update_task_status(task.id, "failed")
            logger.error(f"❌ Task {task.id} failed: {e}")
    
    async def _save_task(self, task: ScheduledTask):
        """Save task to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO scheduled_tasks 
                    (id, video_url, views, schedule_time, interval_minutes, recurring, status, priority, user_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.id,
                    task.video_url,
                    task.views,
                    task.schedule_time.isoformat(),
                    task.interval_minutes,
                    1 if task.recurring else 0,
                    task.status,
                    task.priority,
                    task.user_id,
                    task.created_at.isoformat()
                ))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
    
    async def _update_task_status(self, task_id: str, status: str, completed_at: datetime = None):
        """Update task status in database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if completed_at:
                    await db.execute('''
                        UPDATE scheduled_tasks 
                        SET status = ?, completed_at = ?
                        WHERE id = ?
                    ''', (status, completed_at.isoformat(), task_id))
                else:
                    await db.execute('''
                        UPDATE scheduled_tasks 
                        SET status = ?
                        WHERE id = ?
                    ''', (status, task_id))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        task = self.tasks.get(task_id)
        if task:
            return asdict(task)
        return None
    
    def get_user_tasks(self, user_id: str) -> List[Dict]:
        """Get all tasks for a user"""
        return [asdict(task) for task in self.tasks.values() 
                if task.user_id == user_id]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status in ["pending", "running"]:
                task.status = "cancelled"
                await self._update_task_status(task_id, "cancelled")
                logger.info(f"Task {task_id} cancelled")
                return True
        return False
    
    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        total = len(self.tasks)
        pending = sum(1 for t in self.tasks.values() if t.status == "pending")
        running = sum(1 for t in self.tasks.values() if t.status == "running")
        completed = sum(1 for t in self.tasks.values() if t.status == "completed")
        
        return {
            "total_tasks": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "success_rate": (completed / total * 100) if total > 0 else 0
        }