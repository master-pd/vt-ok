"""
JSON Database Manager - Simple file-based storage
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading

class JSONDatabase:
    """JSON file-based database manager"""
    
    def __init__(self, db_path: str = "database/data.json"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Ensure database file exists"""
        if not os.path.exists(self.db_path):
            default_data = {
                'view_sessions': [],
                'accounts': [],
                'proxies': [],
                'analytics': [],
                'settings': {},
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
            }
            self.save_data(default_data)
            print("✅ JSON database created")
    
    def load_data(self) -> Dict:
        """Load data from JSON file"""
        with self.lock:
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}
    
    def save_data(self, data: Dict):
        """Save data to JSON file"""
        with self.lock:
            # Update metadata
            if 'metadata' in data:
                data['metadata']['last_updated'] = datetime.now().isoformat()
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def insert_view_session(self, session_data: Dict) -> str:
        """Insert view session"""
        data = self.load_data()
        
        # Generate session ID
        session_id = f"session_{datetime.now().timestamp()}_{len(data['view_sessions'])}"
        session_data['id'] = session_id
        session_data['created_at'] = datetime.now().isoformat()
        session_data['status'] = 'pending'
        
        data['view_sessions'].append(session_data)
        self.save_data(data)
        
        return session_id
    
    def update_view_session(self, session_id: str, updates: Dict) -> bool:
        """Update view session"""
        data = self.load_data()
        
        for i, session in enumerate(data['view_sessions']):
            if session.get('id') == session_id:
                data['view_sessions'][i].update(updates)
                data['view_sessions'][i]['updated_at'] = datetime.now().isoformat()
                self.save_data(data)
                return True
        
        return False
    
    def get_view_session(self, session_id: str) -> Optional[Dict]:
        """Get view session by ID"""
        data = self.load_data()
        
        for session in data['view_sessions']:
            if session.get('id') == session_id:
                return session
        
        return None
    
    def get_active_accounts(self, limit: int = 10) -> List[Dict]:
        """Get active accounts"""
        data = self.load_data()
        
        active_accounts = [
            acc for acc in data.get('accounts', [])
            if acc.get('status', 'active') == 'active'
        ]
        
        # Sort by last used (oldest first)
        active_accounts.sort(key=lambda x: x.get('last_used', '1970-01-01'))
        
        return active_accounts[:limit]
    
    def update_account_usage(self, username: str, views_sent: int = 1):
        """Update account usage"""
        data = self.load_data()
        
        for i, account in enumerate(data.get('accounts', [])):
            if account.get('username') == username:
                current_views = account.get('views_sent', 0)
                data['accounts'][i]['views_sent'] = current_views + views_sent
                data['accounts'][i]['last_used'] = datetime.now().isoformat()
                self.save_data(data)
                return True
        
        return False
    
    def get_proxies(self, min_success_rate: float = 0.5, limit: int = 20) -> List[Dict]:
        """Get proxies with minimum success rate"""
        data = self.load_data()
        
        proxies = [
            proxy for proxy in data.get('proxies', [])
            if proxy.get('success_rate', 0) >= min_success_rate
            and proxy.get('status', 'active') == 'active'
        ]
        
        # Sort by success rate (highest first)
        proxies.sort(key=lambda x: x.get('success_rate', 0), reverse=True)
        
        return proxies[:limit]
    
    def update_proxy_stats(self, proxy_url: str, success: bool):
        """Update proxy statistics"""
        data = self.load_data()
        
        proxy_found = False
        for i, proxy in enumerate(data.get('proxies', [])):
            if proxy.get('proxy_url') == proxy_url:
                proxy_found = True
                
                # Calculate new success rate
                old_rate = proxy.get('success_rate', 0.5)
                total_req = proxy.get('total_requests', 0)
                new_total = total_req + 1
                
                if success:
                    new_rate = (old_rate * total_req + 1) / new_total
                else:
                    new_rate = (old_rate * total_req) / new_total
                
                data['proxies'][i]['success_rate'] = new_rate
                data['proxies'][i]['total_requests'] = new_total
                data['proxies'][i]['last_used'] = datetime.now().isoformat()
                break
        
        if not proxy_found:
            # Add new proxy
            new_proxy = {
                'proxy_url': proxy_url,
                'success_rate': 1.0 if success else 0.0,
                'total_requests': 1,
                'last_used': datetime.now().isoformat(),
                'status': 'active'
            }
            data['proxies'].append(new_proxy)
        
        self.save_data(data)
    
    def save_analytics(self, analytics_data: Dict):
        """Save analytics data"""
        data = self.load_data()
        
        # Add date if not present
        if 'date' not in analytics_data:
            analytics_data['date'] = datetime.now().date().isoformat()
        
        data['analytics'].append(analytics_data)
        self.save_data(data)
    
    def get_settings(self) -> Dict:
        """Get settings"""
        data = self.load_data()
        return data.get('settings', {})
    
    def update_settings(self, new_settings: Dict):
        """Update settings"""
        data = self.load_data()
        
        if 'settings' not in data:
            data['settings'] = {}
        
        data['settings'].update(new_settings)
        self.save_data(data)