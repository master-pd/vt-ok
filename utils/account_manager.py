#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Manager for TikTok Bot
Manages multiple TikTok accounts with rotation and monitoring
"""

import json
import asyncio
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import aiosqlite
from pathlib import Path
import hashlib

class TikTokAccount:
    """Represents a TikTok account"""
    
    def __init__(self, account_data: Dict):
        self.id = account_data.get("id")
        self.username = account_data.get("username")
        self.email = account_data.get("email")
        self.password = account_data.get("password")
        self.session_id = account_data.get("session_id")
        self.device_id = account_data.get("device_id")
        self.user_agent = account_data.get("user_agent")
        self.proxy = account_data.get("proxy")
        self.cookies = account_data.get("cookies", {})
        self.created_at = account_data.get("created_at", datetime.now().isoformat())
        self.last_used = account_data.get("last_used")
        self.use_count = account_data.get("use_count", 0)
        self.success_count = account_data.get("success_count", 0)
        self.fail_count = account_data.get("fail_count", 0)
        self.banned = account_data.get("banned", False)
        self.cooldown_until = account_data.get("cooldown_until")
        self.tags = account_data.get("tags", [])
        self.metadata = account_data.get("metadata", {})
        
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "user_agent": self.user_agent,
            "proxy": self.proxy,
            "cookies": self.cookies,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "use_count": self.use_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "banned": self.banned,
            "cooldown_until": self.cooldown_until,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    def is_available(self) -> bool:
        """Check if account is available for use"""
        if self.banned:
            return False
            
        if self.cooldown_until:
            try:
                cooldown_time = datetime.fromisoformat(self.cooldown_until)
                if datetime.now() < cooldown_time:
                    return False
            except:
                pass
                
        return True
    
    def mark_used(self, success: bool = True):
        """Mark account as used"""
        self.last_used = datetime.now().isoformat()
        self.use_count += 1
        
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
            
        # Apply cooldown based on use
        if self.use_count % 10 == 0:
            self.cooldown_until = (datetime.now() + timedelta(hours=1)).isoformat()
    
    def mark_banned(self):
        """Mark account as banned"""
        self.banned = True
        self.cooldown_until = None

class AccountManager:
    """Manages multiple TikTok accounts"""
    
    def __init__(self, db_path: str = "database/accounts.db"):
        self.db_path = Path(db_path)
        self.accounts: Dict[str, TikTokAccount] = {}
        self.account_queue = asyncio.Queue()
        self.load_accounts()
        
    def load_accounts(self):
        """Load accounts from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    email TEXT,
                    password TEXT,
                    session_id TEXT,
                    device_id TEXT,
                    user_agent TEXT,
                    proxy TEXT,
                    cookies TEXT,
                    created_at TEXT,
                    last_used TEXT,
                    use_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    banned INTEGER DEFAULT 0,
                    cooldown_until TEXT,
                    tags TEXT,
                    metadata TEXT
                )
            """)
            
            # Load accounts
            cursor.execute("SELECT * FROM accounts WHERE banned = 0")
            rows = cursor.fetchall()
            
            for row in rows:
                account = TikTokAccount({
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "password": row[3],
                    "session_id": row[4],
                    "device_id": row[5],
                    "user_agent": row[6],
                    "proxy": row[7],
                    "cookies": json.loads(row[8]) if row[8] else {},
                    "created_at": row[9],
                    "last_used": row[10],
                    "use_count": row[11],
                    "success_count": row[12],
                    "fail_count": row[13],
                    "banned": bool(row[14]),
                    "cooldown_until": row[15],
                    "tags": json.loads(row[16]) if row[16] else [],
                    "metadata": json.loads(row[17]) if row[17] else {}
                })
                
                self.accounts[account.id] = account
                
            conn.close()
            
            print(f"Loaded {len(self.accounts)} accounts")
            
        except Exception as e:
            print(f"Error loading accounts: {e}")
            # Create empty database
            self._init_database()
    
    async def add_account(self, account_data: Dict) -> str:
        """Add new account"""
        account_id = hashlib.md5(
            f"{account_data.get('username')}{account_data.get('email')}".encode()
        ).hexdigest()[:8]
        
        account_data["id"] = account_id
        account_data["created_at"] = datetime.now().isoformat()
        
        account = TikTokAccount(account_data)
        self.accounts[account_id] = account
        
        # Save to database
        await self._save_account(account)
        
        return account_id
    
    async def remove_account(self, account_id: str) -> bool:
        """Remove account"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
                await db.commit()
                
            return True
        return False
    
    async def get_account(self, account_id: str) -> Optional[TikTokAccount]:
        """Get account by ID"""
        return self.accounts.get(account_id)
    
    async def get_available_accounts(self, count: int = 1, 
                                   tags: List[str] = None) -> List[TikTokAccount]:
        """Get available accounts"""
        available = []
        
        for account in self.accounts.values():
            if not account.is_available():
                continue
                
            if tags:
                if not any(tag in account.tags for tag in tags):
                    continue
                    
            available.append(account)
            
        # Sort by use count (least used first)
        available.sort(key=lambda x: x.use_count)
        
        return available[:count]
    
    async def get_account_by_tag(self, tag: str) -> Optional[TikTokAccount]:
        """Get account with specific tag"""
        for account in self.accounts.values():
            if tag in account.tags and account.is_available():
                return account
        return None
    
    async def rotate_accounts(self, count: int = 5) -> List[TikTokAccount]:
        """Get rotated accounts for load balancing"""
        available = await self.get_available_accounts(count=count)
        
        if not available:
            # Try to get accounts that are in cooldown but not banned
            for account in self.accounts.values():
                if not account.banned and account not in available:
                    available.append(account)
                    
                if len(available) >= count:
                    break
        
        return available
    
    async def mark_account_used(self, account_id: str, success: bool = True):
        """Mark account as used"""
        account = await self.get_account(account_id)
        if account:
            account.mark_used(success)
            await self._save_account(account)
    
    async def mark_account_banned(self, account_id: str):
        """Mark account as banned"""
        account = await self.get_account(account_id)
        if account:
            account.mark_banned()
            await self._save_account(account)
    
    async def update_account_cookies(self, account_id: str, cookies: Dict):
        """Update account cookies"""
        account = await self.get_account(account_id)
        if account:
            account.cookies = cookies
            await self._save_account(account)
    
    async def add_account_tag(self, account_id: str, tag: str):
        """Add tag to account"""
        account = await self.get_account(account_id)
        if account and tag not in account.tags:
            account.tags.append(tag)
            await self._save_account(account)
    
    async def remove_account_tag(self, account_id: str, tag: str):
        """Remove tag from account"""
        account = await self.get_account(account_id)
        if account and tag in account.tags:
            account.tags.remove(tag)
            await self._save_account(account)
    
    async def get_account_stats(self) -> Dict:
        """Get account statistics"""
        total = len(self.accounts)
        available = len([a for a in self.accounts.values() if a.is_available()])
        banned = len([a for a in self.accounts.values() if a.banned])
        in_cooldown = len([a for a in self.accounts.values() 
                          if a.cooldown_until and not a.banned])
        
        total_uses = sum(a.use_count for a in self.accounts.values())
        total_success = sum(a.success_count for a in self.accounts.values())
        total_fail = sum(a.fail_count for a in self.accounts.values())
        
        return {
            "total_accounts": total,
            "available_accounts": available,
            "banned_accounts": banned,
            "accounts_in_cooldown": in_cooldown,
            "total_uses": total_uses,
            "total_success": total_success,
            "total_fail": total_fail,
            "success_rate": (total_success / total_uses * 100) if total_uses > 0 else 0
        }
    
    async def export_accounts(self, format: str = "json") -> str:
        """Export accounts to different formats"""
        accounts_data = [acc.to_dict() for acc in self.accounts.values()]
        
        if format == "json":
            return json.dumps(accounts_data, indent=2, default=str)
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "id", "username", "email", "use_count", "success_count", 
                "fail_count", "banned", "last_used"
            ])
            writer.writeheader()
            
            for acc in accounts_data:
                writer.writerow({
                    "id": acc["id"],
                    "username": acc["username"],
                    "email": acc["email"],
                    "use_count": acc["use_count"],
                    "success_count": acc["success_count"],
                    "fail_count": acc["fail_count"],
                    "banned": acc["banned"],
                    "last_used": acc["last_used"]
                })
                
            return output.getvalue()
        else:
            return str(accounts_data)
    
    async def import_accounts(self, data: str, format: str = "json") -> int:
        """Import accounts from data"""
        count = 0
        
        if format == "json":
            accounts_list = json.loads(data)
        elif format == "csv":
            import csv
            import io
            
            reader = csv.DictReader(io.StringIO(data))
            accounts_list = list(reader)
        else:
            return 0
            
        for acc_data in accounts_list:
            # Convert CSV format if needed
            if format == "csv":
                acc_data = {
                    "username": acc_data.get("username"),
                    "email": acc_data.get("email"),
                    "password": acc_data.get("password", ""),
                    "proxy": acc_data.get("proxy", ""),
                    "tags": acc_data.get("tags", "").split(",") if acc_data.get("tags") else []
                }
            
            await self.add_account(acc_data)
            count += 1
            
        return count
    
    async def cleanup_old_accounts(self, days: int = 30):
        """Remove accounts not used for specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        removed = 0
        
        for account_id, account in list(self.accounts.items()):
            if account.last_used:
                try:
                    last_used = datetime.fromisoformat(account.last_used)
                    if last_used < cutoff_date:
                        await self.remove_account(account_id)
                        removed += 1
                except:
                    pass
        
        return removed
    
    async def backup_accounts(self, backup_path: str = "backups/accounts_backup.json"):
        """Backup accounts to file"""
        backup_dir = Path(backup_path).parent
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        accounts_data = [acc.to_dict() for acc in self.accounts.values()]
        
        async with aiofiles.open(backup_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(accounts_data, indent=2, default=str))
        
        return backup_path
    
    async def restore_accounts(self, backup_path: str) -> int:
        """Restore accounts from backup"""
        try:
            async with aiofiles.open(backup_path, 'r', encoding='utf-8') as f:
                data = await f.read()
                
            return await self.import_accounts(data, format="json")
        except Exception as e:
            print(f"Error restoring accounts: {e}")
            return 0
    
    # Private methods
    async def _save_account(self, account: TikTokAccount):
        """Save account to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO accounts 
                (id, username, email, password, session_id, device_id, user_agent, 
                 proxy, cookies, created_at, last_used, use_count, success_count, 
                 fail_count, banned, cooldown_until, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account.id,
                account.username,
                account.email,
                account.password,
                account.session_id,
                account.device_id,
                account.user_agent,
                account.proxy,
                json.dumps(account.cookies),
                account.created_at,
                account.last_used,
                account.use_count,
                account.success_count,
                account.fail_count,
                1 if account.banned else 0,
                account.cooldown_until,
                json.dumps(account.tags),
                json.dumps(account.metadata)
            ))
            await db.commit()
    
    def _init_database(self):
        """Initialize database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    email TEXT,
                    password TEXT,
                    session_id TEXT,
                    device_id TEXT,
                    user_agent TEXT,
                    proxy TEXT,
                    cookies TEXT,
                    created_at TEXT,
                    last_used TEXT,
                    use_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    banned INTEGER DEFAULT 0,
                    cooldown_until TEXT,
                    tags TEXT,
                    metadata TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error initializing database: {e}")

# Account pool for concurrent operations
class AccountPool:
    """Pool of accounts for concurrent operations"""
    
    def __init__(self, account_manager: AccountManager, pool_size: int = 10):
        self.account_manager = account_manager
        self.pool_size = pool_size
        self.active_accounts = set()
        self.lock = asyncio.Lock()
        
    async def acquire_account(self, tags: List[str] = None) -> Optional[TikTokAccount]:
        """Acquire an available account from pool"""
        async with self.lock:
            # Get available accounts
            accounts = await self.account_manager.get_available_accounts(
                count=self.pool_size * 2,
                tags=tags
            )
            
            # Filter out already active accounts
            available = [acc for acc in accounts if acc.id not in self.active_accounts]
            
            if not available:
                return None
                
            # Get least recently used account
            account = min(available, key=lambda x: x.use_count)
            self.active_accounts.add(account.id)
            
            return account
    
    async def release_account(self, account_id: str, success: bool = True):
        """Release account back to pool"""
        async with self.lock:
            if account_id in self.active_accounts:
                self.active_accounts.remove(account_id)
                
        # Update account stats
        await self.account_manager.mark_account_used(account_id, success)
    
    async def get_pool_status(self) -> Dict:
        """Get pool status"""
        async with self.lock:
            return {
                "pool_size": self.pool_size,
                "active_accounts": len(self.active_accounts),
                "available_accounts": await self._count_available_accounts(),
                "account_ids": list(self.active_accounts)
            }
    
    async def _count_available_accounts(self) -> int:
        """Count available accounts"""
        accounts = await self.account_manager.get_available_accounts(count=1000)
        available = [acc for acc in accounts if acc.id not in self.active_accounts]
        return len(available)

# CLI interface for account manager
async def main_cli():
    """Command-line interface for account manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TikTok Account Manager CLI")
    parser.add_argument("--add", action="store_true", help="Add new account")
    parser.add_argument("--list", action="store_true", help="List all accounts")
    parser.add_argument("--stats", action="store_true", help="Show account statistics")
    parser.add_argument("--export", type=str, help="Export accounts to file")
    parser.add_argument("--import", type=str, dest="import_file", help="Import accounts from file")
    parser.add_argument("--cleanup", type=int, help="Cleanup accounts older than X days")
    parser.add_argument("--backup", type=str, help="Backup accounts to file")
    parser.add_argument("--restore", type=str, help="Restore accounts from backup")
    
    args = parser.parse_args()
    
    manager = AccountManager()
    
    if args.add:
        print("Add New Account:")
        username = input("Username: ")
        email = input("Email: ")
        password = input("Password: ")
        proxy = input("Proxy (optional): ")
        
        account_id = await manager.add_account({
            "username": username,
            "email": email,
            "password": password,
            "proxy": proxy
        })
        
        print(f"Account added with ID: {account_id}")
    
    elif args.list:
        stats = await manager.get_account_stats()
        print(f"Total Accounts: {stats['total_accounts']}")
        print(f"Available: {stats['available_accounts']}")
        print(f"Banned: {stats['banned_accounts']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        
        for account in manager.accounts.values():
            status = "🟢 Available" if account.is_available() else "🔴 Unavailable"
            print(f"\nID: {account.id}")
            print(f"Username: {account.username}")
            print(f"Uses: {account.use_count} (✓{account.success_count} ✗{account.fail_count})")
            print(f"Status: {status}")
            print(f"Last Used: {account.last_used}")
    
    elif args.stats:
        stats = await manager.get_account_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.export:
        exported = await manager.export_accounts("json")
        with open(args.export, 'w') as f:
            f.write(exported)
        print(f"Exported to {args.export}")
    
    elif args.import_file:
        with open(args.import_file, 'r') as f:
            data = f.read()
        count = await manager.import_accounts(data, "json")
        print(f"Imported {count} accounts")
    
    elif args.cleanup:
        removed = await manager.cleanup_old_accounts(args.cleanup)
        print(f"Removed {removed} old accounts")
    
    elif args.backup:
        path = await manager.backup_accounts(args.backup)
        print(f"Backup created at {path}")
    
    elif args.restore:
        count = await manager.restore_accounts(args.restore)
        print(f"Restored {count} accounts")

if __name__ == "__main__":
    asyncio.run(main_cli())