#!/usr/bin/env python3
import sys
sys.path.append('/opt/tiktok-views-bot')

from scripts.backup import BackupManager

def main():
    manager = BackupManager()
    
    # Database backup
    manager.backup_database()
    
    # Configuration backup
    manager.backup_configs()
    
    # Logs backup
    manager.backup_logs()
    
    # Upload to cloud
    manager.upload_to_s3()
    
    # Cleanup old backups
    manager.cleanup_old_backups(days=30)

if __name__ == "__main__":
    main()