#!/usr/bin/env python3
"""
VT ULTRA PRO - Main Application
Advanced TikTok View Bot with 20+ Telegram API Methods
Author: RANA (Master)
Version: 1.0.0 Ultra Pro
"""

import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from core.bot_core import VTCore
from telegram_bot.bot_20_api import TelegramBotAPI
from tiktok_engine.workers.worker_manager import WorkerManager
from admin_panel.admin_dashboard import AdminDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vt_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VTUltraPro:
    def __init__(self):
        self.version = "1.0.0 Ultra Pro Max"
        self.author = "RANA (Master)"
        self.start_time = datetime.now()
        
        # Initialize core systems
        self.core = VTCore()
        self.telegram_bot = TelegramBotAPI()
        self.worker_manager = WorkerManager()
        self.admin_panel = AdminDashboard()
        
        logger.info(f"🚀 VT ULTRA PRO {self.version} by {self.author}")
        
    async def initialize(self):
        """Initialize all systems"""
        try:
            logger.info("🔧 Initializing VT Ultra Pro...")
            
            # 1. Load configuration
            await self.core.load_config()
            
            # 2. Initialize database
            await self.core.init_database()
            
            # 3. Start Telegram Bot with 20+ API methods
            await self.telegram_bot.start()
            
            # 4. Start Worker Manager
            await self.worker_manager.start()
            
            # 5. Start Admin Panel
            await self.admin_panel.start()
            
            # 6. Start AI Engine
            await self.core.ai_engine.start()
            
            logger.info("✅ All systems initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def run(self):
        """Main run loop"""
        logger.info("▶️ Starting VT Ultra Pro...")
        
        try:
            # Start all services
            await asyncio.gather(
                self.telegram_bot.polling(),
                self.worker_manager.run(),
                self.admin_panel.monitor(),
                self.core.analytics.collect()
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down gracefully...")
        except Exception as e:
            logger.error(f"💥 Critical error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🔌 Shutting down systems...")
        
        await self.telegram_bot.stop()
        await self.worker_manager.stop()
        await self.admin_panel.stop()
        await self.core.shutdown()
        
        runtime = datetime.now() - self.start_time
        logger.info(f"🕒 Total runtime: {runtime}")
        logger.info("👋 VT Ultra Pro stopped")

async def main():
    """Main entry point"""
    bot = VTUltraPro()
    
    try:
        await bot.initialize()
        await bot.run()
    except Exception as e:
        logger.critical(f"💀 Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    # Run with UV loop for better performance
    import uvloop
    uvloop.install()
    
    asyncio.run(main())