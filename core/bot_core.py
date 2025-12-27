"""
VT Core - Main Brain of the System
"""

import json
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict
import aiosqlite
import redis.asyncio as redis

@dataclass
class BotConfig:
    """Bot Configuration"""
    bot_token: str
    admin_ids: list
    database_url: str
    redis_url: str
    proxy_enabled: bool
    max_workers: int
    view_methods: list
    ai_enabled: bool
    payment_gateways: list
    cloud_provider: str

class VTCore:
    """Main Core System"""
    
    def __init__(self):
        self.config = None
        self.db = None
        self.redis = None
        self.ai_engine = None
        self.is_running = False
        
        # Paths
        self.base_dir = Path(__file__).parent.parent
        self.config_path = self.base_dir / "config.yaml"
        self.data_dir = self.base_dir / "data"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        
    async def load_config(self):
        """Load configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            self.config = BotConfig(**config_data['bot'])
            
            # Load sensitive data from .env
            from dotenv import load_dotenv
            load_dotenv()
            import os
            
            self.config.bot_token = os.getenv('BOT_TOKEN')
            self.config.database_url = os.getenv('DATABASE_URL', 'sqlite:///data/vt_bot.db')
            
            print(f"✅ Config loaded: {self.config}")
            return True
            
        except Exception as e:
            print(f"❌ Config load failed: {e}")
            raise
    
    async def init_database(self):
        """Initialize databases"""
        try:
            # SQLite database
            self.db = await aiosqlite.connect('data/vt_bot.db')
            
            # Create tables
            await self.create_tables()
            
            # Redis for caching
            self.redis = redis.from_url(
                self.config.redis_url,
                decode_responses=True
            )
            
            print("✅ Databases initialized")
            return True
            
        except Exception as e:
            print(f"❌ Database init failed: {e}")
            raise
    
    async def create_tables(self):
        """Create database tables"""
        tables = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance REAL DEFAULT 0.0,
                total_spent REAL DEFAULT 0.0,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                is_premium BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE,
                settings TEXT DEFAULT '{}'
            )
            """,
            
            # Orders table
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_type TEXT NOT NULL,
                target_url TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                delivered INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                price REAL NOT NULL,
                method_used TEXT,
                success_rate REAL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            # Analytics table
            """
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_orders INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0.0,
                active_users INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Sessions table
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                session_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            
            # Workers table
            """
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id TEXT UNIQUE NOT NULL,
                worker_type TEXT NOT NULL,
                status TEXT DEFAULT 'idle',
                tasks_completed INTEGER DEFAULT 0,
                last_active TIMESTAMP,
                ip_address TEXT,
                location TEXT
            )
            """
        ]
        
        for table_sql in tables:
            await self.db.execute(table_sql)
        
        await self.db.commit()
        print("✅ Database tables created")
    
    async def shutdown(self):
        """Shutdown core systems"""
        if self.db:
            await self.db.close()
        if self.redis:
            await self.redis.close()
        print("🔌 Core systems shutdown")