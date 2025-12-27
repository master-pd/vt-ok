"""
View Tracker - Real-time view analytics
"""

import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import sqlite3

class ViewTracker:
    """Track and analyze view performance"""
    
    def __init__(self, db_path: str = "data/view_analytics.db"):
        self.db_path = db_path
        self.setup_database()
        self.real_time_data = {}
        self.analytics_cache = {}
        
    def setup_database(self):
        """Setup analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Views table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_url TEXT NOT NULL,
                video_id TEXT NOT NULL,
                initial_views INTEGER DEFAULT 0,
                final_views INTEGER DEFAULT 0,
                views_sent INTEGER DEFAULT 0,
                views_increased INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                method_used TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds INTEGER,
                cost REAL DEFAULT 0.0,
                user_id INTEGER,
                order_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Real-time tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS view_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                view_count INTEGER,
                likes INTEGER,
                comments INTEGER,
                shares INTEGER,
                engagement_rate REAL,
                source TEXT
            )
        """)
        
        # Performance analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                method TEXT NOT NULL,
                total_views_sent INTEGER DEFAULT 0,
                successful_views INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_duration REAL,
                avg_cost_per_view REAL,
                unique_videos INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_id ON views(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON view_tracking(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_method ON performance_analytics(date, method)")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Analytics database setup at {self.db_path}")
    
    async def track_view_session(self, video_url: str, video_id: str, 
                                initial_data: Dict) -> str:
        """Start tracking a view session"""
        session_id = f"session_{int(time.time())}_{hash(video_id) % 10000}"
        
        self.real_time_data[session_id] = {
            'video_url': video_url,
            'video_id': video_id,
            'initial_views': initial_data.get('views', 0),
            'initial_likes': initial_data.get('likes', 0),
            'initial_comments': initial_data.get('comments', 0),
            'initial_shares': initial_data.get('shares', 0),
            'start_time': datetime.now(),
            'tracking_points': [],
            'methods_used': [],
            'cost': 0.0,
            'user_id': initial_data.get('user_id'),
            'order_id': initial_data.get('order_id')
        }
        
        # Record initial state
        await self.record_view_point(
            video_id, 
            self.real_time_data[session_id]['initial_views'],
            'initial'
        )
        
        print(f"📊 Started tracking session {session_id} for {video_url}")
        return session_id
    
    async def record_view_point(self, video_id: str, view_count: int, 
                               source: str = 'tracking'):
        """Record a view count point"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO view_tracking 
            (video_id, view_count, timestamp, source)
            VALUES (?, ?, ?, ?)
        """, (video_id, view_count, datetime.now(), source))
        
        conn.commit()
        conn.close()
    
    async def update_session(self, session_id: str, update_data: Dict):
        """Update view session with new data"""
        if session_id not in self.real_time_data:
            return False
        
        session = self.real_time_data[session_id]
        
        # Update tracking points
        tracking_point = {
            'timestamp': datetime.now(),
            'views': update_data.get('views', 0),
            'likes': update_data.get('likes', 0),
            'comments': update_data.get('comments', 0),
            'shares': update_data.get('shares', 0),
            'method': update_data.get('method'),
            'cost': update_data.get('cost', 0.0)
        }
        
        session['tracking_points'].append(tracking_point)
        
        # Record view point
        await self.record_view_point(
            session['video_id'],
            update_data.get('views', 0),
            update_data.get('method', 'unknown')
        )
        
        # Update methods used
        method = update_data.get('method')
        if method and method not in session['methods_used']:
            session['methods_used'].append(method)
        
        # Update cost
        session['cost'] += update_data.get('cost', 0.0)
        
        return True
    
    async def complete_session(self, session_id: str, final_data: Dict) -> Dict:
        """Complete a view session and save results"""
        if session_id not in self.real_time_data:
            return {'error': 'Session not found'}
        
        session = self.real_time_data[session_id]
        
        # Calculate results
        initial_views = session['initial_views']
        final_views = final_data.get('views', initial_views)
        views_sent = final_data.get('views_sent', 0)
        
        if views_sent > 0:
            views_increased = final_views - initial_views
            success_rate = (views_increased / views_sent) * 100
        else:
            views_increased = 0
            success_rate = 0.0
        
        # Calculate duration
        start_time = session['start_time']
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO views 
            (video_url, video_id, initial_views, final_views, 
             views_sent, views_increased, success_rate, method_used,
             start_time, end_time, duration_seconds, cost,
             user_id, order_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session['video_url'],
            session['video_id'],
            initial_views,
            final_views,
            views_sent,
            views_increased,
            success_rate,
            ','.join(session['methods_used']),
            start_time,
            end_time,
            duration,
            session['cost'],
            session.get('user_id'),
            session.get('order_id')
        ))
        
        view_id = cursor.lastrowid
        
        # Update performance analytics
        await self.update_performance_analytics(session, success_rate)
        
        conn.commit()
        conn.close()
        
        # Generate report
        report = await self.generate_session_report(session_id, {
            'view_id': view_id,
            'initial_views': initial_views,
            'final_views': final_views,
            'views_sent': views_sent,
            'views_increased': views_increased,
            'success_rate': success_rate,
            'duration': duration,
            'cost': session['cost'],
            'methods_used': session['methods_used']
        })
        
        # Cleanup
        del self.real_time_data[session_id]
        
        print(f"📈 Completed session {session_id} with {success_rate:.1f}% success")
        
        return report
    
    async def update_performance_analytics(self, session: Dict, success_rate: float):
        """Update performance analytics"""
        today = datetime.now().date()
        methods = session['methods_used']
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for method in methods:
            # Check if entry exists for today
            cursor.execute("""
                SELECT id, total_views_sent, successful_views 
                FROM performance_analytics 
                WHERE date = ? AND method = ?
            """, (today, method))
            
            row = cursor.fetchone()
            
            views_sent = session.get('views_sent_estimate', 100)
            successful_views = int(views_sent * (success_rate / 100))
            
            if row:
                # Update existing entry
                entry_id, current_sent, current_success = row
                new_sent = current_sent + views_sent
                new_success = current_success + successful_views
                new_rate = (new_success / new_sent) * 100 if new_sent > 0 else 0
                
                cursor.execute("""
                    UPDATE performance_analytics 
                    SET total_views_sent = ?, successful_views = ?, success_rate = ?
                    WHERE id = ?
                """, (new_sent, new_success, new_rate, entry_id))
            else:
                # Create new entry
                cursor.execute("""
                    INSERT INTO performance_analytics 
                    (date, method, total_views_sent, successful_views, success_rate)
                    VALUES (?, ?, ?, ?, ?)
                """, (today, method, views_sent, successful_views, success_rate))
        
        conn.commit()
        conn.close()
    
    async def generate_session_report(self, session_id: str, results: Dict) -> Dict:
        """Generate detailed session report"""
        return {
            'session_id': session_id,
            'results': results,
            'analytics': {
                'cost_per_view': results['cost'] / results['views_sent'] if results['views_sent'] > 0 else 0,
                'views_per_hour': (results['views_increased'] / (results['duration'] / 3600)) if results['duration'] > 0 else 0,
                'efficiency_score': self.calculate_efficiency_score(results),
                'roi': self.calculate_roi(results),
                'method_effectiveness': await self.analyze_method_effectiveness(results['methods_used'])
            },
            'recommendations': await self.generate_recommendations(results),
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_efficiency_score(self, results: Dict) -> float:
        """Calculate efficiency score (0-100)"""
        success_rate = results['success_rate']
        cost_per_view = results.get('cost_per_view', 0)
        views_per_hour = results.get('views_per_hour', 0)
        
        # Normalize factors
        success_score = success_rate  # Already 0-100
        cost_score = max(0, 100 - (cost_per_view * 1000))  # Lower cost = higher score
        speed_score = min(100, views_per_hour / 10)  # 1000 views/hour = 100 score
        
        # Weighted average
        efficiency = (
            success_score * 0.5 +
            cost_score * 0.3 +
            speed_score * 0.2
        )
        
        return min(100, max(0, efficiency))
    
    def calculate_roi(self, results: Dict) -> float:
        """Calculate Return on Investment"""
        cost = results['cost']
        views_increased = results['views_increased']
        
        if cost <= 0:
            return 0
        
        # Estimated value per view (simplified)
        value_per_view = 0.01  # $0.01 per view
        total_value = views_increased * value_per_view
        
        roi = ((total_value - cost) / cost) * 100
        
        return roi
    
    async def analyze_method_effectiveness(self, methods_used: List[str]) -> Dict:
        """Analyze effectiveness of methods used"""
        if not methods_used:
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        effectiveness = {}
        
        for method in methods_used:
            cursor.execute("""
                SELECT 
                    AVG(success_rate) as avg_success,
                    COUNT(*) as total_sessions,
                    AVG(duration_seconds) as avg_duration,
                    AVG(cost) as avg_cost
                FROM views 
                WHERE method_used LIKE ? 
                AND created_at >= datetime('now', '-7 days')
            """, (f'%{method}%',))
            
            row = cursor.fetchone()
            
            if row and row[0] is not None:
                effectiveness[method] = {
                    'average_success_rate': row[0],
                    'total_sessions': row[1],
                    'average_duration': row[2],
                    'average_cost': row[3],
                    'reliability_score': min(100, row[0] * 1.2)  # Convert to 0-100 scale
                }
        
        conn.close()
        return effectiveness
    
    async def generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on results"""
        recommendations = []
        
        success_rate = results['success_rate']
        cost_per_view = results.get('cost_per_view', 0)
        
        if success_rate < 80:
            recommendations.append("Consider using hybrid method for better success rate")
        
        if cost_per_view > 0.005:  # More than $0.005 per view
            recommendations.append("Try browser method for lower cost per view")
        
        if len(results['methods_used']) == 1:
            recommendations.append("Using multiple methods can improve reliability")
        
        if results.get('views_per_hour', 0) > 5000:
            recommendations.append("High speed detected. Consider slowing down for better organic appearance")
        
        return recommendations
    
    async def get_video_analytics(self, video_id: str, 
                                 days: int = 7) -> Dict:
        """Get analytics for a specific video"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get view sessions for this video
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                SUM(views_sent) as total_views_sent,
                SUM(views_increased) as total_views_increased,
                AVG(success_rate) as avg_success_rate,
                AVG(duration_seconds) as avg_duration,
                AVG(cost) as avg_cost,
                GROUP_CONCAT(DISTINCT method_used) as methods_used
            FROM views 
            WHERE video_id = ? 
            AND created_at >= datetime('now', ?)
        """, (video_id, f'-{days} days'))
        
        row = cursor.fetchone()
        
        if not row or row[0] is None:
            conn.close()
            return {'no_data': True}
        
        # Get view tracking data
        cursor.execute("""
            SELECT 
                timestamp,
                view_count,
                source
            FROM view_tracking 
            WHERE video_id = ?
            AND timestamp >= datetime('now', ?)
            ORDER BY timestamp
        """, (video_id, f'-{days} days'))
        
        tracking_data = cursor.fetchall()
        
        conn.close()
        
        # Process tracking data
        view_history = []
        for timestamp, view_count, source in tracking_data:
            view_history.append({
                'timestamp': timestamp,
                'views': view_count,
                'source': source
            })
        
        return {
            'video_id': video_id,
            'period_days': days,
            'total_sessions': row[0],
            'total_views_sent': row[1] or 0,
            'total_views_increased': row[2] or 0,
            'average_success_rate': row[3] or 0,
            'average_duration': row[4] or 0,
            'average_cost': row[5] or 0,
            'methods_used': row[6].split(',') if row[6] else [],
            'view_history': view_history,
            'performance_trend': self.calculate_performance_trend(view_history)
        }
    
    def calculate_performance_trend(self, view_history: List[Dict]) -> str:
        """Calculate performance trend"""
        if len(view_history) < 2:
            return 'stable'
        
        # Get first and last views
        first_views = view_history[0]['views']
        last_views = view_history[-1]['views']
        
        if last_views > first_views * 1.2:
            return 'improving'
        elif last_views < first_views * 0.8:
            return 'declining'
        else:
            return 'stable'
    
    async def get_method_analytics(self, method: str, 
                                  days: int = 7) -> Dict:
        """Get analytics for a specific method"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                date,
                total_views_sent,
                successful_views,
                success_rate,
                unique_videos,
                unique_users
            FROM performance_analytics 
            WHERE method = ? 
            AND date >= date('now', ?)
            ORDER BY date
        """, (method, f'-{days} days'))
        
        rows = cursor.fetchall()
        
        conn.close()
        
        if not rows:
            return {'no_data': True}
        
        # Process data
        daily_data = []
        for row in rows:
            daily_data.append({
                'date': row[0],
                'total_views_sent': row[1],
                'successful_views': row[2],
                'success_rate': row[3],
                'unique_videos': row[4],
                'unique_users': row[5]
            })
        
        # Calculate totals
        totals = {
            'total_views_sent': sum(d['total_views_sent'] for d in daily_data),
            'total_successful': sum(d['successful_views'] for d in daily_data),
            'avg_success_rate': sum(d['success_rate'] for d in daily_data) / len(daily_data) if daily_data else 0,
            'total_unique_videos': len(set(d['unique_videos'] for d in daily_data)),
            'total_unique_users': len(set(d['unique_users'] for d in daily_data))
        }
        
        return {
            'method': method,
            'period_days': days,
            'daily_data': daily_data,
            'totals': totals,
            'trend': self.calculate_method_trend(daily_data)
        }
    
    def calculate_method_trend(self, daily_data: List[Dict]) -> Dict:
        """Calculate method performance trend"""
        if len(daily_data) < 3:
            return {'trend': 'insufficient_data'}
        
        # Get success rates
        success_rates = [d['success_rate'] for d in daily_data]
        
        # Simple trend calculation
        first_half = success_rates[:len(success_rates)//2]
        second_half = success_rates[len(success_rates)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        if avg_second > avg_first * 1.1:
            trend = 'improving'
        elif avg_second < avg_first * 0.9:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'current_rate': success_rates[-1] if success_rates else 0,
            'average_rate': sum(success_rates) / len(success_rates) if success_rates else 0
        }
    
    async def get_real_time_dashboard(self) -> Dict:
        """Get real-time dashboard data"""
        active_sessions = len(self.real_time_data)
        
        # Calculate current performance
        success_rates = []
        views_per_hour = []
        
        for session_id, session in self.real_time_data.items():
            if session['tracking_points']:
                latest = session['tracking_points'][-1]
                initial = session['initial_views']
                current = latest['views']
                
                if hasattr(session, 'views_sent_estimate'):
                    sent = session['views_sent_estimate']
                    if sent > 0:
                        increased = current - initial
                        rate = (increased / sent) * 100
                        success_rates.append(rate)
        
        avg_success = sum(success_rates) / len(success_rates) if success_rates else 0
        
        return {
            'active_sessions': active_sessions,
            'average_success_rate': avg_success,
            'total_views_today': await self.get_today_views(),
            'methods_distribution': await self.get_methods_distribution(),
            'performance_alerts': await self.check_performance_alerts(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_today_views(self) -> int:
        """Get total views sent today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(total_views_sent) 
            FROM performance_analytics 
            WHERE date = date('now')
        """)
        
        result = cursor.fetchone()[0] or 0
        conn.close()
        
        return result
    
    async def get_methods_distribution(self) -> Dict:
        """Get today's methods distribution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT method, SUM(total_views_sent) as views
            FROM performance_analytics 
            WHERE date = date('now')
            GROUP BY method
        """)
        
        distribution = {}
        total = 0
        
        for method, views in cursor.fetchall():
            distribution[method] = views
            total += views
        
        conn.close()
        
        # Calculate percentages
        if total > 0:
            for method in distribution:
                distribution[method] = {
                    'views': distribution[method],
                    'percentage': (distribution[method] / total) * 100
                }
        
        return distribution
    
    async def check_performance_alerts(self) -> List[Dict]:
        """Check for performance alerts"""
        alerts = []
        
        # Check method performance
        methods = ['browser', 'api', 'cloud', 'hybrid']
        
        for method in methods:
            analytics = await self.get_method_analytics(method, 1)  # Today
            
            if 'no_data' not in analytics and analytics.get('totals', {}).get('avg_success_rate', 0) < 70:
                alerts.append({
                    'type': 'low_performance',
                    'method': method,
                    'success_rate': analytics['totals']['avg_success_rate'],
                    'message': f'{method} method showing low performance today'
                })
        
        # Check total volume
        today_views = await self.get_today_views()
        if today_views > 100000:
            alerts.append({
                'type': 'high_volume',
                'views': today_views,
                'message': 'High view volume detected today'
            })
        
        return alerts