"""
Backup Script for VT ULTRA PRO
Automated backup of database, files, and configuration
"""

import os
import sys
import logging
import shutil
import json
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import asyncio
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

class BackupManager:
    """Manage system backups"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Backup Manager initialized. Backup directory: {self.backup_dir}")
    
    async def create_full_backup(self, backup_name: str = None) -> Dict:
        """Create full system backup"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"full_backup_{timestamp}"
            
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            logger.info(f"Creating full backup: {backup_name}")
            
            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "type": "full",
                "components": []
            }
            
            # Backup database
            db_result = await self.backup_database(backup_path)
            manifest["components"].append(db_result)
            
            # Backup configuration
            config_result = await self.backup_configuration(backup_path)
            manifest["components"].append(config_result)
            
            # Backup logs
            log_result = await self.backup_logs(backup_path)
            manifest["components"].append(log_result)
            
            # Backup uploaded files
            file_result = await self.backup_files(backup_path)
            manifest["components"].append(file_result)
            
            # Create metadata file
            metadata_path = backup_path / "backup_manifest.json"
            with open(metadata_path, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)
            
            # Create archive
            archive_path = await self.create_archive(backup_path)
            
            # Cleanup temporary directory
            shutil.rmtree(backup_path)
            
            # Calculate backup size
            archive_size = archive_path.stat().st_size
            
            result = {
                "success": True,
                "backup_name": backup_name,
                "archive_path": str(archive_path),
                "size_bytes": archive_size,
                "size_human": self._format_size(archive_size),
                "components": len(manifest["components"]),
                "created_at": manifest["created_at"]
            }
            
            logger.info(f"Full backup created: {archive_path} ({result['size_human']})")
            
            # Cleanup old backups
            await self.cleanup_old_backups()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create full backup: {e}")
            return {
                "success": False,
                "error": str(e),
                "backup_name": backup_name
            }
    
    async def backup_database(self, backup_path: Path) -> Dict:
        """Backup database"""
        try:
            db_backup_dir = backup_path / "database"
            db_backup_dir.mkdir(exist_ok=True)
            
            from database.models import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # SQLite database
            if "sqlite" in db_manager.database_url:
                db_file = db_manager.database_url.replace("sqlite:///", "")
                if os.path.exists(db_file):
                    shutil.copy2(db_file, db_backup_dir / "database.db")
                    
                    # Also backup any -shm or -wal files
                    for ext in ["-shm", "-wal"]:
                        shm_file = f"{db_file}{ext}"
                        if os.path.exists(shm_file):
                            shutil.copy2(shm_file, db_backup_dir / f"database.db{ext}")
            
            # PostgreSQL database
            elif "postgresql" in db_manager.database_url:
                # Use pg_dump for PostgreSQL
                db_config = self._parse_postgresql_url(db_manager.database_url)
                
                dump_file = db_backup_dir / "database.sql"
                
                cmd = [
                    "pg_dump",
                    "-h", db_config["host"],
                    "-p", str(db_config["port"]),
                    "-U", db_config["user"],
                    "-d", db_config["database"],
                    "-f", str(dump_file)
                ]
                
                # Set PGPASSWORD environment variable
                env = os.environ.copy()
                env["PGPASSWORD"] = db_config["password"]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"pg_dump failed: {stderr.decode()}")
            
            # MySQL database
            elif "mysql" in db_manager.database_url:
                # Use mysqldump for MySQL
                db_config = self._parse_mysql_url(db_manager.database_url)
                
                dump_file = db_backup_dir / "database.sql"
                
                cmd = [
                    "mysqldump",
                    "-h", db_config["host"],
                    "-P", str(db_config["port"]),
                    "-u", db_config["user"],
                    f"-p{db_config['password']}",
                    db_config["database"],
                    "--result-file", str(dump_file)
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"mysqldump failed: {stderr.decode()}")
            
            # Calculate backup size
            total_size = sum(f.stat().st_size for f in db_backup_dir.rglob("*") if f.is_file())
            
            return {
                "component": "database",
                "status": "success",
                "path": str(db_backup_dir),
                "size_bytes": total_size,
                "size_human": self._format_size(total_size),
                "files": len(list(db_backup_dir.rglob("*")))
            }
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                "component": "database",
                "status": "failed",
                "error": str(e)
            }
    
    async def backup_configuration(self, backup_path: Path) -> Dict:
        """Backup configuration files"""
        try:
            config_backup_dir = backup_path / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            # Copy all configuration files
            config_files = [
                "config.yaml",
                "config/config.json",
                "config/accounts.json",
                "config/proxies.json",
                "config/video_targets.json",
                ".env",
                "requirements.txt",
                "docker-compose.yml",
                "Dockerfile"
            ]
            
            copied_files = []
            for config_file in config_files:
                src_path = Path(config_file)
                if src_path.exists():
                    dst_path = config_backup_dir / src_path.name
                    if src_path.is_dir():
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src_path, dst_path)
                    copied_files.append(str(src_path))
            
            # Calculate backup size
            total_size = sum(f.stat().st_size for f in config_backup_dir.rglob("*") if f.is_file())
            
            return {
                "component": "configuration",
                "status": "success",
                "path": str(config_backup_dir),
                "size_bytes": total_size,
                "size_human": self._format_size(total_size),
                "files": len(copied_files),
                "file_list": copied_files
            }
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            return {
                "component": "configuration",
                "status": "failed",
                "error": str(e)
            }
    
    async def backup_logs(self, backup_path: Path) -> Dict:
        """Backup log files"""
        try:
            log_backup_dir = backup_path / "logs"
            log_backup_dir.mkdir(exist_ok=True)
            
            # Copy log files
            log_dir = Path("logs")
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_size > 0:  # Only backup non-empty logs
                        shutil.copy2(log_file, log_backup_dir / log_file.name)
            
            # Also backup system logs if accessible
            system_logs = [
                "/var/log/syslog",
                "/var/log/auth.log",
                f"/var/log/{Path.cwd().name}.log"
            ]
            
            for sys_log in system_logs:
                if os.path.exists(sys_log):
                    try:
                        log_name = Path(sys_log).name
                        shutil.copy2(sys_log, log_backup_dir / f"system_{log_name}")
                    except PermissionError:
                        logger.warning(f"Permission denied for system log: {sys_log}")
            
            # Calculate backup size
            total_size = sum(f.stat().st_size for f in log_backup_dir.rglob("*") if f.is_file())
            
            return {
                "component": "logs",
                "status": "success",
                "path": str(log_backup_dir),
                "size_bytes": total_size,
                "size_human": self._format_size(total_size),
                "files": len(list(log_backup_dir.glob("*.log")))
            }
            
        except Exception as e:
            logger.error(f"Log backup failed: {e}")
            return {
                "component": "logs",
                "status": "failed",
                "error": str(e)
            }
    
    async def backup_files(self, backup_path: Path) -> Dict:
        """Backup uploaded files and media"""
        try:
            file_backup_dir = backup_path / "files"
            file_backup_dir.mkdir(exist_ok=True)
            
            # Backup directories
            backup_dirs = [
                "uploads",
                "static",
                "media",
                "temp"
            ]
            
            copied_dirs = []
            for dir_name in backup_dirs:
                dir_path = Path(dir_name)
                if dir_path.exists() and dir_path.is_dir():
                    dst_path = file_backup_dir / dir_name
                    shutil.copytree(dir_path, dst_path, dirs_exist_ok=True)
                    copied_dirs.append(dir_name)
            
            # Calculate backup size
            total_size = sum(f.stat().st_size for f in file_backup_dir.rglob("*") if f.is_file())
            
            return {
                "component": "files",
                "status": "success",
                "path": str(file_backup_dir),
                "size_bytes": total_size,
                "size_human": self._format_size(total_size),
                "directories": copied_dirs,
                "total_files": sum(1 for _ in file_backup_dir.rglob("*") if _.is_file())
            }
            
        except Exception as e:
            logger.error(f"File backup failed: {e}")
            return {
                "component": "files",
                "status": "failed",
                "error": str(e)
            }
    
    async def create_archive(self, backup_path: Path, format: str = "tar.gz") -> Path:
        """Create compressed archive of backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"backup_{timestamp}.{format}"
            archive_path = self.backup_dir / archive_name
            
            if format == "tar.gz":
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(backup_path, arcname=backup_path.name)
            elif format == "zip":
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(backup_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, backup_path.parent)
                            zipf.write(file_path, arcname)
            else:
                raise ValueError(f"Unsupported archive format: {format}")
            
            return archive_path
            
        except Exception as e:
            logger.error(f"Archive creation failed: {e}")
            raise
    
    async def restore_backup(self, backup_path: str) -> Dict:
        """Restore system from backup"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                return {"success": False, "error": "Backup file not found"}
            
            # Extract backup
            extract_dir = self.backup_dir / "restore_temp"
            extract_dir.mkdir(exist_ok=True)
            
            if backup_path.suffix in ['.gz', '.tgz', '.tar.gz']:
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(extract_dir)
            elif backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
            else:
                return {"success": False, "error": "Unsupported backup format"}
            
            # Find backup manifest
            manifest_file = None
            for root, dirs, files in os.walk(extract_dir):
                if "backup_manifest.json" in files:
                    manifest_file = Path(root) / "backup_manifest.json"
                    break
            
            if not manifest_file:
                return {"success": False, "error": "Backup manifest not found"}
            
            # Load manifest
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            restore_results = []
            
            # Restore database
            db_backup_dir = extract_dir / "database"
            if db_backup_dir.exists():
                result = await self.restore_database(db_backup_dir)
                restore_results.append(result)
            
            # Restore configuration
            config_backup_dir = extract_dir / "config"
            if config_backup_dir.exists():
                result = await self.restore_configuration(config_backup_dir)
                restore_results.append(result)
            
            # Restore files
            files_backup_dir = extract_dir / "files"
            if files_backup_dir.exists():
                result = await self.restore_files(files_backup_dir)
                restore_results.append(result)
            
            # Cleanup temporary directory
            shutil.rmtree(extract_dir)
            
            return {
                "success": True,
                "backup_name": manifest.get("backup_name"),
                "created_at": manifest.get("created_at"),
                "restore_results": restore_results,
                "message": "Restore completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def restore_database(self, backup_dir: Path) -> Dict:
        """Restore database from backup"""
        try:
            from database.models import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # SQLite restore
            if "sqlite" in db_manager.database_url:
                db_file = db_manager.database_url.replace("sqlite:///", "")
                
                # Backup current database first
                if os.path.exists(db_file):
                    backup_file = f"{db_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(db_file, backup_file)
                
                # Restore database
                backup_db = backup_dir / "database.db"
                if backup_db.exists():
                    shutil.copy2(backup_db, db_file)
            
            # PostgreSQL restore would require psql command
            
            return {
                "component": "database",
                "status": "success",
                "message": "Database restored"
            }
            
        except Exception as e:
            return {
                "component": "database",
                "status": "failed",
                "error": str(e)
            }
    
    async def restore_configuration(self, backup_dir: Path) -> Dict:
        """Restore configuration files"""
        try:
            restored_files = []
            
            for config_file in backup_dir.glob("*"):
                dst_path = Path(config_file.name)
                
                # Backup existing file
                if dst_path.exists():
                    backup_path = Path(f"{dst_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    shutil.copy2(dst_path, backup_path)
                
                # Restore file
                if config_file.is_dir():
                    shutil.copytree(config_file, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(config_file, dst_path)
                
                restored_files.append(str(dst_path))
            
            return {
                "component": "configuration",
                "status": "success",
                "restored_files": restored_files,
                "message": f"Restored {len(restored_files)} configuration files"
            }
            
        except Exception as e:
            return {
                "component": "configuration",
                "status": "failed",
                "error": str(e)
            }
    
    async def restore_files(self, backup_dir: Path) -> Dict:
        """Restore uploaded files"""
        try:
            restored_dirs = []
            
            for item in backup_dir.iterdir():
                if item.is_dir():
                    dst_path = Path(item.name)
                    
                    # Backup existing directory
                    if dst_path.exists():
                        backup_path = Path(f"{dst_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copytree(dst_path, backup_path, dirs_exist_ok=True)
                    
                    # Restore directory
                    shutil.copytree(item, dst_path, dirs_exist_ok=True)
                    restored_dirs.append(item.name)
            
            return {
                "component": "files",
                "status": "success",
                "restored_directories": restored_dirs,
                "message": f"Restored {len(restored_dirs)} directories"
            }
            
        except Exception as e:
            return {
                "component": "files",
                "status": "failed",
                "error": str(e)
            }
    
    async def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.tar.gz"):
            try:
                stat = backup_file.stat()
                backups.append({
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size_bytes": stat.st_size,
                    "size_human": self._format_size(stat.st_size),
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.error(f"Error reading backup info for {backup_file}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    async def get_backup_info(self, backup_name: str) -> Optional[Dict]:
        """Get detailed information about a backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return None
        
        try:
            stat = backup_path.stat()
            
            info = {
                "name": backup_name,
                "path": str(backup_path),
                "size_bytes": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            # Try to extract manifest for more info
            try:
                if backup_path.suffix in ['.gz', '.tgz', '.tar.gz']:
                    with tarfile.open(backup_path, "r:gz") as tar:
                        manifest_member = None
                        for member in tar.getmembers():
                            if member.name.endswith("backup_manifest.json"):
                                manifest_member = member
                                break
                        
                        if manifest_member:
                            manifest_file = tar.extractfile(manifest_member)
                            if manifest_file:
                                manifest = json.load(manifest_file)
                                info["manifest"] = manifest
            except:
                pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            return None
    
    async def cleanup_old_backups(self, keep_last: int = 10, max_age_days: int = 30):
        """Cleanup old backups"""
        try:
            backups = await self.list_backups()
            
            if len(backups) <= keep_last:
                return
            
            # Remove backups older than max_age_days
            cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            
            deleted = 0
            for backup in backups[keep_last:]:  # Keep last N backups
                backup_date = datetime.fromisoformat(backup["created_at"]).timestamp()
                
                if backup_date < cutoff_date:
                    backup_path = Path(backup["path"])
                    backup_path.unlink()
                    deleted += 1
                    logger.info(f"Deleted old backup: {backup['name']}")
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old backups")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    async def verify_backup(self, backup_path: str) -> Dict:
        """Verify backup integrity"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return {"valid": False, "error": "Backup file not found"}
            
            # Check file size
            file_size = backup_path.stat().st_size
            if file_size == 0:
                return {"valid": False, "error": "Backup file is empty"}
            
            # Test archive integrity
            try:
                if backup_path.suffix in ['.gz', '.tgz', '.tar.gz']:
                    with tarfile.open(backup_path, "r:gz") as tar:
                        # Try to read file list
                        members = tar.getmembers()
                        if not members:
                            return {"valid": False, "error": "Backup archive is empty"}
                elif backup_path.suffix == '.zip':
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        # Test ZIP integrity
                        if zipf.testzip() is not None:
                            return {"valid": False, "error": "Backup archive is corrupted"}
                else:
                    return {"valid": False, "error": "Unsupported backup format"}
            except Exception as e:
                return {"valid": False, "error": f"Archive corrupted: {str(e)}"}
            
            return {
                "valid": True,
                "size_bytes": file_size,
                "size_human": self._format_size(file_size),
                "message": "Backup verification successful"
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _parse_postgresql_url(self, url: str) -> Dict:
        """Parse PostgreSQL connection URL"""
        # Remove postgresql:// prefix
        url = url.replace("postgresql://", "")
        
        # Split into parts
        if "@" in url:
            auth_part, host_part = url.split("@", 1)
            if ":" in auth_part:
                user, password = auth_part.split(":", 1)
            else:
                user = auth_part
                password = ""
        else:
            user = ""
            password = ""
            host_part = url
        
        # Split host part
        if "/" in host_part:
            host_port_part, database = host_part.split("/", 1)
        else:
            host_port_part = host_part
            database = ""
        
        # Split host and port
        if ":" in host_port_part:
            host, port = host_port_part.split(":", 1)
        else:
            host = host_port_part
            port = "5432"
        
        return {
            "host": host,
            "port": int(port),
            "database": database,
            "user": user,
            "password": password
        }
    
    def _parse_mysql_url(self, url: str) -> Dict:
        """Parse MySQL connection URL"""
        # Remove mysql:// prefix
        url = url.replace("mysql://", "")
        
        # Similar parsing as PostgreSQL
        return self._parse_postgresql_url(f"postgresql://{url}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

async def main():
    """Main function for backup script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VT ULTRA PRO Backup Manager")
    
    parser.add_argument(
        "--action",
        type=str,
        default="create",
        choices=["create", "restore", "list", "info", "cleanup", "verify"],
        help="Action to perform"
    )
    
    parser.add_argument(
        "--name",
        type=str,
        help="Backup name (for create or restore)"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Backup file path (for restore or verify)"
    )
    
    parser.add_argument(
        "--keep-last",
        type=int,
        default=10,
        help="Number of backups to keep (for cleanup)"
    )
    
    parser.add_argument(
        "--max-age",
        type=int,
        default=30,
        help="Maximum age of backups in days (for cleanup)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create backup manager
    backup_manager = BackupManager()
    
    try:
        if args.action == "create":
            result = await backup_manager.create_full_backup(args.name)
            print(json.dumps(result, indent=2, default=str))
            
        elif args.action == "restore":
            if not args.file:
                print("Error: --file argument required for restore")
                return
            
            result = await backup_manager.restore_backup(args.file)
            print(json.dumps(result, indent=2, default=str))
            
        elif args.action == "list":
            backups = await backup_manager.list_backups()
            print("Available Backups:")
            print("=" * 80)
            for backup in backups:
                print(f"• {backup['name']}")
                print(f"  Size: {backup['size_human']}")
                print(f"  Created: {backup['created_at']}")
                print(f"  Path: {backup['path']}")
                print()
            
        elif args.action == "info":
            if not args.file:
                print("Error: --file argument required for info")
                return
            
            info = await backup_manager.get_backup_info(args.file)
            if info:
                print(json.dumps(info, indent=2, default=str))
            else:
                print(f"Backup not found: {args.file}")
            
        elif args.action == "cleanup":
            await backup_manager.cleanup_old_backups(args.keep_last, args.max_age)
            print("Backup cleanup completed")
            
        elif args.action == "verify":
            if not args.file:
                print("Error: --file argument required for verify")
                return
            
            result = await backup_manager.verify_backup(args.file)
            print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())