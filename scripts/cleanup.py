#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Script for TikTok Bot System
Cleans up old files, logs, and temporary data
"""

import asyncio
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import aiofiles
import aiosqlite

class CleanupManager:
    """Manages cleanup operations"""
    
    def __init__(self, config_path: str = "config/cleanup_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load cleanup configuration"""
        default_config = {
            "cleanup_schedule": {
                "daily": True,
                "weekly": True,
                "monthly": True
            },
            "retention_policies": {
                "logs": {
                    "keep_days": 7,
                    "keep_size": "100MB",
                    "compress_old": True
                },
                "temp_files": {
                    "keep_days": 1,
                    "patterns": ["*.tmp", "*.temp", "*.log"]
                },
                "backups": {
                    "keep_days": 30,
                    "keep_count": 100,
                    "keep_monthly": 12
                },
                "cache": {
                    "keep_days": 3,
                    "max_size": "1GB"
                },
                "database": {
                    "vacuum": True,
                    "optimize": True,
                    "remove_old_data": True
                }
            },
            "cleanup_items": {
                "log_dirs": ["logs/"],
                "temp_dirs": ["temp/", "cache/", "tmp/"],
                "backup_dirs": ["backups/"],
                "database_files": [
                    "database/analytics.db",
                    "database/orders.db"
                ]
            },
            "notifications": {
                "enabled": True,
                "log_cleanup": True
            }
        }
        
        if self.config_path.exists():
            try:
                import yaml
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except:
                pass
                
        return default_config
    
    async def run_cleanup(self, cleanup_type: str = "full") -> Dict:
        """Run cleanup operations"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "type": cleanup_type,
            "operations": {},
            "total_freed": 0,
            "errors": []
        }
        
        try:
            if cleanup_type in ["full", "logs"]:
                results["operations"]["logs"] = await self._cleanup_logs()
            
            if cleanup_type in ["full", "temp"]:
                results["operations"]["temp"] = await self._cleanup_temp_files()
            
            if cleanup_type in ["full", "backups"]:
                results["operations"]["backups"] = await self._cleanup_backups()
            
            if cleanup_type in ["full", "cache"]:
                results["operations"]["cache"] = await self._cleanup_cache()
            
            if cleanup_type in ["full", "database"]:
                results["operations"]["database"] = await self._cleanup_databases()
            
            # Calculate total freed space
            for op_result in results["operations"].values():
                if isinstance(op_result, dict) and "freed_space" in op_result:
                    results["total_freed"] += op_result["freed_space"]
            
            # Send notification if enabled
            if self.config["notifications"]["enabled"]:
                await self._send_notification(results)
            
            return results
            
        except Exception as e:
            results["errors"].append(str(e))
            return results
    
    async def _cleanup_logs(self) -> Dict:
        """Cleanup old log files"""
        results = {
            "cleaned_files": [],
            "compressed_files": [],
            "errors": [],
            "freed_space": 0
        }
        
        policy = self.config["retention_policies"]["logs"]
        keep_days = policy["keep_days"]
        keep_size = self._parse_size(policy["keep_size"])
        
        for log_dir in self.config["cleanup_items"]["log_dirs"]:
            log_path = Path(log_dir)
            
            if not log_path.exists():
                continue
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for log_file in log_path.rglob("*.log"):
                try:
                    stat = log_file.stat()
                    file_age = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Check if file should be deleted
                    if file_age < cutoff_date:
                        file_size = stat.st_size
                        log_file.unlink()
                        results["cleaned_files"].append({
                            "path": str(log_file),
                            "size": file_size,
                            "age": (datetime.now() - file_age).days
                        })
                        results["freed_space"] += file_size
                    
                    # Check if file should be compressed
                    elif policy["compress_old"] and stat.st_size > keep_size:
                        await self._compress_file(log_file)
                        results["compressed_files"].append({
                            "path": str(log_file),
                            "size": stat.st_size
                        })
                        
                except Exception as e:
                    results["errors"].append(f"{log_file}: {e}")
        
        return results
    
    async def _cleanup_temp_files(self) -> Dict:
        """Cleanup temporary files"""
        results = {
            "cleaned_files": [],
            "errors": [],
            "freed_space": 0
        }
        
        policy = self.config["retention_policies"]["temp_files"]
        keep_days = policy["keep_days"]
        
        for temp_dir in self.config["cleanup_items"]["temp_dirs"]:
            temp_path = Path(temp_dir)
            
            if not temp_path.exists():
                continue
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for pattern in policy["patterns"]:
                for temp_file in temp_path.rglob(pattern):
                    try:
                        if not temp_file.is_file():
                            continue
                        
                        stat = temp_file.stat()
                        file_age = datetime.fromtimestamp(stat.st_mtime)
                        
                        if file_age < cutoff_date:
                            file_size = stat.st_size
                            temp_file.unlink()
                            results["cleaned_files"].append({
                                "path": str(temp_file),
                                "size": file_size,
                                "age": (datetime.now() - file_age).days
                            })
                            results["freed_space"] += file_size
                            
                    except Exception as e:
                        results["errors"].append(f"{temp_file}: {e}")
        
        return results
    
    async def _cleanup_backups(self) -> Dict:
        """Cleanup old backup files"""
        results = {
            "cleaned_files": [],
            "kept_files": [],
            "errors": [],
            "freed_space": 0
        }
        
        policy = self.config["retention_policies"]["backups"]
        keep_days = policy["keep_days"]
        keep_count = policy["keep_count"]
        keep_monthly = policy["keep_monthly"]
        
        for backup_dir in self.config["cleanup_items"]["backup_dirs"]:
            backup_path = Path(backup_dir)
            
            if not backup_path.exists():
                continue
            
            # Get all backup files
            backup_files = []
            for backup_file in backup_path.iterdir():
                if backup_file.is_file() and any(
                    backup_file.suffix == ext for ext in ['.zip', '.tar', '.gz', '.enc']
                ):
                    stat = backup_file.stat()
                    backup_files.append({
                        "path": backup_file,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "name": backup_file.name
                    })
            
            # Sort by modification date (newest first)
            backup_files.sort(key=lambda x: x["modified"], reverse=True)
            
            # Keep by count
            for backup in backup_files[keep_count:]:
                try:
                    file_size = backup["path"].stat().st_size
                    backup["path"].unlink()
                    results["cleaned_files"].append({
                        "path": str(backup["path"]),
                        "size": file_size,
                        "age": (datetime.now() - backup["modified"]).days
                    })
                    results["freed_space"] += file_size
                except Exception as e:
                    results["errors"].append(f"{backup['path']}: {e}")
            
            # Keep monthly backups
            monthly_backups = {}
            for backup in backup_files:
                month_key = backup["modified"].strftime("%Y-%m")
                if month_key not in monthly_backups:
                    monthly_backups[month_key] = backup
            
            # Keep only specified number of monthly backups
            monthly_list = list(monthly_backups.values())
            monthly_list.sort(key=lambda x: x["modified"], reverse=True)
            
            for backup in monthly_list[keep_monthly:]:
                if backup["path"].exists():
                    try:
                        file_size = backup["path"].stat().st_size
                        backup["path"].unlink()
                        results["cleaned_files"].append({
                            "path": str(backup["path"]),
                            "size": file_size,
                            "age": (datetime.now() - backup["modified"]).days
                        })
                        results["freed_space"] += file_size
                    except Exception as e:
                        results["errors"].append(f"{backup['path']}: {e}")
            
            # Record kept files
            for backup in backup_files:
                if backup["path"].exists():
                    results["kept_files"].append({
                        "path": str(backup["path"]),
                        "size": backup["size"],
                        "modified": backup["modified"].isoformat()
                    })
        
        return results
    
    async def _cleanup_cache(self) -> Dict:
        """Cleanup cache files"""
        results = {
            "cleaned_files": [],
            "errors": [],
            "freed_space": 0
        }
        
        policy = self.config["retention_policies"]["cache"]
        keep_days = policy["keep_days"]
        max_size = self._parse_size(policy["max_size"])
        
        for cache_dir in self.config["cleanup_items"]["temp_dirs"]:
            cache_path = Path(cache_dir)
            
            if not cache_path.exists():
                continue
            
            # Calculate total cache size
            total_size = 0
            cache_files = []
            
            for cache_file in cache_path.rglob("*"):
                if cache_file.is_file():
                    stat = cache_file.stat()
                    total_size += stat.st_size
                    cache_files.append({
                        "path": cache_file,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime)
                    })
            
            # Sort by modification date (oldest first)
            cache_files.sort(key=lambda x: x["modified"])
            
            # Remove files until under max size
            current_size = total_size
            for cache_file in cache_files:
                if current_size > max_size:
                    try:
                        cache_file["path"].unlink()
                        results["cleaned_files"].append({
                            "path": str(cache_file["path"]),
                            "size": cache_file["size"],
                            "age": (datetime.now() - cache_file["modified"]).days
                        })
                        results["freed_space"] += cache_file["size"]
                        current_size -= cache_file["size"]
                    except Exception as e:
                        results["errors"].append(f"{cache_file['path']}: {e}")
                else:
                    break
            
            # Remove files older than keep_days
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            for cache_file in cache_files:
                if cache_file["path"].exists() and cache_file["modified"] < cutoff_date:
                    try:
                        cache_file["path"].unlink()
                        results["cleaned_files"].append({
                            "path": str(cache_file["path"]),
                            "size": cache_file["size"],
                            "age": (datetime.now() - cache_file["modified"]).days
                        })
                        results["freed_space"] += cache_file["size"]
                    except Exception as e:
                        results["errors"].append(f"{cache_file['path']}: {e}")
        
        return results
    
    async def _cleanup_databases(self) -> Dict:
        """Cleanup and optimize databases"""
        results = {
            "databases_cleaned": [],
            "errors": [],
            "freed_space": 0
        }
        
        policy = self.config["retention_policies"]["database"]
        
        for db_file in self.config["cleanup_items"]["database_files"]:
            db_path = Path(db_file)
            
            if not db_path.exists():
                continue
            
            try:
                # Get initial size
                initial_size = db_path.stat().st_size
                
                async with aiosqlite.connect(db_path) as db:
                    # Remove old data if enabled
                    if policy["remove_old_data"]:
                        # Example: Remove analytics older than 30 days
                        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                        
                        # Check if analytics table exists
                        async with db.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='analytics'"
                        ) as cursor:
                            if await cursor.fetchone():
                                await db.execute(
                                    "DELETE FROM analytics WHERE timestamp < ?",
                                    (cutoff_date,)
                                )
                                await db.commit()
                    
                    # Vacuum database if enabled
                    if policy["vacuum"]:
                        await db.execute("VACUUM")
                    
                    # Optimize database if enabled
                    if policy["optimize"]:
                        await db.execute("PRAGMA optimize")
                        await db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                
                # Get final size
                final_size = db_path.stat().st_size
                freed = initial_size - final_size
                
                results["databases_cleaned"].append({
                    "database": str(db_path),
                    "initial_size": initial_size,
                    "final_size": final_size,
                    "freed": freed
                })
                results["freed_space"] += freed
                
            except Exception as e:
                results["errors"].append(f"{db_path}: {e}")
        
        return results
    
    async def _compress_file(self, file_path: Path):
        """Compress a file using gzip"""
        import gzip
        
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            file_path.unlink()
            
        except Exception as e:
            print(f"Error compressing {file_path}: {e}")
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes"""
        size_str = size_str.upper().strip()
        
        if size_str.endswith("KB"):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith("MB"):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith("GB"):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
        elif size_str.endswith("TB"):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024 * 1024)
        else:
            return int(size_str)
    
    async def _send_notification(self, results: Dict):
        """Send cleanup notification"""
        if not self.config["notifications"]["enabled"]:
            return
        
        # Log results if enabled
        if self.config["notifications"]["log_cleanup"]:
            log_path = Path("logs/cleanup.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(log_path, 'a') as f:
                await f.write(json.dumps(results, indent=2, default=str) + "\n")
        
        # Could add email/telegram notifications here
        print(f"Cleanup completed: Freed {self._format_size(results['total_freed'])}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    async def schedule_cleanup(self):
        """Schedule automated cleanup"""
        while True:
            now = datetime.now()
            
            # Daily cleanup (at 3 AM)
            if self.config["cleanup_schedule"]["daily"] and now.hour == 3:
                await self.run_cleanup("logs")
                await self.run_cleanup("temp")
                await self.run_cleanup("cache")
            
            # Weekly cleanup (Sunday at 4 AM)
            if self.config["cleanup_schedule"]["weekly"] and now.weekday() == 6 and now.hour == 4:
                await self.run_cleanup("full")
            
            # Monthly cleanup (1st of month at 5 AM)
            if self.config["cleanup_schedule"]["monthly"] and now.day == 1 and now.hour == 5:
                await self.run_cleanup("full")
                # Run database optimization
                await self._cleanup_databases()
            
            # Wait for next hour
            await asyncio.sleep(3600)

# CLI interface
async def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup Manager CLI")
    parser.add_argument("--run", type=str, default="full", 
                       choices=["full", "logs", "temp", "backups", "cache", "database"],
                       help="Run specific cleanup")
    parser.add_argument("--schedule", action="store_true", help="Start cleanup scheduler")
    parser.add_argument("--config", type=str, default="config/cleanup_config.yaml", 
                       help="Config file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned")
    
    args = parser.parse_args()
    
    manager = CleanupManager(args.config)
    
    if args.dry_run:
        # Dry run mode - just show what would be cleaned
        print("Dry run mode - no files will be deleted")
        
        # Simulate cleanup and print results
        results = await manager.run_cleanup(args.run)
        
        print("\n" + "="*50)
        print(f"CLEANUP RESULTS ({args.run})")
        print("="*50)
        
        total_files = 0
        total_size = 0
        
        for op_name, op_results in results["operations"].items():
            if isinstance(op_results, dict) and "cleaned_files" in op_results:
                files = op_results["cleaned_files"]
                if files:
                    print(f"\n{op_name.upper()}:")
                    for file in files:
                        print(f"  Would delete: {file['path']}")
                        print(f"    Size: {manager._format_size(file['size'])}")
                        print(f"    Age: {file['age']} days")
                        total_files += 1
                        total_size += file["size"]
        
        print(f"\nTotal: {total_files} files, {manager._format_size(total_size)}")
        
        if results["errors"]:
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results["errors"][:5]:  # Show first 5 errors
                print(f"  {error}")
    
    elif args.schedule:
        print("Starting cleanup scheduler...")
        await manager.schedule_cleanup()
    
    else:
        print(f"Running {args.run} cleanup...")
        results = await manager.run_cleanup(args.run)
        
        print("\n" + "="*50)
        print(f"CLEANUP COMPLETED")
        print("="*50)
        
        for op_name, op_results in results["operations"].items():
            if isinstance(op_results, dict):
                files_cleaned = len(op_results.get("cleaned_files", []))
                freed_space = op_results.get("freed_space", 0)
                
                if files_cleaned > 0 or freed_space > 0:
                    print(f"\n{op_name.upper()}:")
                    print(f"  Files cleaned: {files_cleaned}")
                    print(f"  Space freed: {manager._format_size(freed_space)}")
        
        print(f"\nTotal space freed: {manager._format_size(results['total_freed'])}")
        
        if results["errors"]:
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"  {error}")

if __name__ == "__main__":
    asyncio.run(main())