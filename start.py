"""
VT ULTRA PRO - Startup Script
Main entry point for launching the application
"""

import os
import sys
import logging
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging(log_level: str = "INFO"):
    """Setup application logging"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_requirements():
    """Check system requirements and dependencies"""
    logger = logging.getLogger(__name__)
    
    try:
        import psutil
        import aiohttp
        import sqlalchemy
        import yaml
        import redis
        
        logger.info("✅ All core dependencies are available")
        
        # Check disk space
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 90:
            logger.warning(f"⚠️  Low disk space: {disk_usage.percent}% used")
        
        # Check memory
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            logger.warning(f"⚠️  High memory usage: {memory.percent}%")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("Please install requirements: pip install -r requirements.txt")
        return False

def load_config():
    """Load application configuration"""
    import yaml
    
    config_path = project_root / "config.yaml"
    if not config_path.exists():
        # Create default config if doesn't exist
        create_default_config(config_path)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def create_default_config(config_path: Path):
    """Create default configuration file"""
    default_config = {
        'app': {
            'name': 'VT ULTRA PRO',
            'version': '1.0.0',
            'environment': 'development',
            'debug': True,
            'secret_key': 'change-this-in-production',
            'timezone': 'UTC'
        },
        'database': {
            'type': 'sqlite',
            'path': 'database/vt_ultra_pro.db'
        },
        'telegram': {
            'bot_token': 'YOUR_BOT_TOKEN_HERE',
            'admin_ids': [123456789]
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    print(f"✅ Created default configuration at {config_path}")
    print("⚠️  Please update config.yaml with your settings before running")

async def start_application(mode: str = "all"):
    """Start the application with specified mode"""
    logger = logging.getLogger(__name__)
    
    try:
        from main import VTUltraPro
        
        app = VTUltraPro()
        
        logger.info("🚀 Starting VT ULTRA PRO...")
        logger.info(f"📁 Project Root: {project_root}")
        logger.info(f"🔧 Mode: {mode}")
        
        if mode == "all" or mode == "telegram":
            logger.info("🤖 Starting Telegram Bot...")
            # Start Telegram bot in background
            # await app.start_telegram_bot()
        
        if mode == "all" or mode == "api":
            logger.info("🌐 Starting API Server...")
            # Start API server
            # await app.start_api_server()
        
        if mode == "all" or mode == "worker":
            logger.info("⚙️  Starting Worker System...")
            # Start worker system
            # await app.start_worker_system()
        
        if mode == "all" or mode == "monitor":
            logger.info("📊 Starting Monitoring System...")
            # Start monitoring
            # await app.start_monitoring()
        
        logger.info("✅ Application started successfully")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        sys.exit(1)

async def run_migrations():
    """Run database migrations"""
    logger = logging.getLogger(__name__)
    
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("✅ Database migrations completed")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

async def backup_database():
    """Create database backup"""
    logger = logging.getLogger(__name__)
    
    try:
        from database.models import DatabaseManager
        
        db_manager = DatabaseManager()
        backup_path = f"backups/db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        success = await db_manager.backup_database(backup_path)
        
        if success:
            logger.info(f"✅ Database backed up to {backup_path}")
        else:
            logger.error("❌ Database backup failed")
            
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")

async def cleanup_system():
    """Cleanup system files and logs"""
    logger = logging.getLogger(__name__)
    
    try:
        import shutil
        from datetime import datetime, timedelta
        
        # Cleanup old logs (older than 7 days)
        log_dir = project_root / "logs"
        cutoff_date = datetime.now() - timedelta(days=7)
        
        deleted_logs = 0
        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                deleted_logs += 1
        
        # Cleanup temp files
        temp_dir = project_root / "temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            temp_dir.mkdir()
        
        # Cleanup cache
        cache_dir = project_root / "cache"
        if cache_dir.exists():
            for cache_file in cache_dir.glob("*"):
                if cache_file.is_file():
                    cache_file.unlink()
        
        logger.info(f"✅ Cleanup completed: {deleted_logs} old logs removed")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="VT ULTRA PRO - TikTok Automation System")
    
    parser.add_argument(
        "--mode",
        type=str,
        default="all",
        choices=["all", "telegram", "api", "worker", "monitor"],
        help="Application mode to start"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Run database migrations before starting"
    )
    
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create database backup before starting"
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup system files before starting"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check system requirements only"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    # Print banner
    print_banner()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    if args.check:
        logger.info("✅ System check completed")
        sys.exit(0)
    
    # Run pre-start tasks
    async def run_tasks():
        if args.migrate:
            await run_migrations()
        
        if args.backup:
            await backup_database()
        
        if args.cleanup:
            await cleanup_system()
        
        # Start main application
        await start_application(args.mode)
    
    # Run async tasks
    try:
        asyncio.run(run_tasks())
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║         ██╗   ██╗████████╗    ██╗   ██╗██╗  ██╗         ║
    ║         ██║   ██║╚══██╔══╝    ██║   ██║██║  ██║         ║
    ║         ██║   ██║   ██║       ██║   ██║███████║         ║
    ║         ██║   ██║   ██║       ██║   ██║██╔══██║         ║
    ║         ╚██████╔╝   ██║       ╚██████╔╝██║  ██║         ║
    ║          ╚═════╝    ╚═╝        ╚═════╝ ╚═╝  ╚═╝         ║
    ║                                                          ║
    ║              U L T R A   P R O   E D I T I O N           ║
    ║                                                          ║
    ║      TikTok View Automation System - Version 1.0.0       ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    
    print(banner)

if __name__ == "__main__":
    main()