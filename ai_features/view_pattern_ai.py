"""
AI-powered view pattern generation for organic appearance
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import random
from datetime import datetime, timedelta
import json

class ViewPatternAI:
    def __init__(self):
        self.patterns = []
        self.model = None
        
    def generate_organic_pattern(self, total_views, duration_hours=24):
        """Generate organic viewing pattern"""
        patterns = []
        
        # Peak hours (7PM-11PM)
        peak_start = 19
        peak_end = 23
        
        # Mid-peak (12PM-4PM)
        mid_start = 12
        mid_end = 16
        
        # Off-peak (2AM-6AM)
        off_start = 2
        off_end = 6
        
        # Distribute views
        peak_views = int(total_views * 0.5)
        mid_views = int(total_views * 0.3)
        off_views = total_views - peak_views - mid_views
        
        # Generate timestamps
        current_time = datetime.now()
        
        # Peak hours views
        for _ in range(peak_views):
            hour = random.randint(peak_start, peak_end)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = current_time.replace(hour=hour, minute=minute, second=second)
            patterns.append({
                'timestamp': timestamp.isoformat(),
                'watch_time': random.randint(30, 180),
                'action_type': random.choice(['view', 'view_like', 'view_comment']),
                'device': random.choice(['mobile', 'desktop', 'tablet'])
            })
        
        # Mid-peak hours
        for _ in range(mid_views):
            hour = random.randint(mid_start, mid_end)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = current_time.replace(hour=hour, minute=minute, second=second)
            patterns.append({
                'timestamp': timestamp.isoformat(),
                'watch_time': random.randint(15, 90),
                'action_type': 'view',
                'device': random.choice(['mobile', 'desktop'])
            })
        
        # Off-peak hours
        for _ in range(off_views):
            hour = random.randint(off_start, off_end)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = current_time.replace(hour=hour, minute=minute, second=second)
            patterns.append({
                'timestamp': timestamp.isoformat(),
                'watch_time': random.randint(5, 30),
                'action_type': 'view',
                'device': 'mobile'
            })
        
        # Sort by timestamp
        patterns.sort(key=lambda x: x['timestamp'])
        return patterns
    
    def create_geo_distribution(self, views_count):
        """Create geographic distribution of views"""
        countries = [
            {'country': 'US', 'weight': 0.35},
            {'country': 'UK', 'weight': 0.15},
            {'country': 'Canada', 'weight': 0.10},
            {'country': 'Australia', 'weight': 0.08},
            {'country': 'India', 'weight': 0.12},
            {'country': 'Germany', 'weight': 0.07},
            {'country': 'France', 'weight': 0.06},
            {'country': 'Brazil', 'weight': 0.05},
            {'country': 'Japan', 'weight': 0.02}
        ]
        
        geo_views = []
        for country in countries:
            count = int(views_count * country['weight'])
            for i in range(count):
                geo_views.append({
                    'country': country['country'],
                    'city': self._get_random_city(country['country']),
                    'timezone': self._get_timezone(country['country'])
                })
        
        return geo_views
    
    def _get_random_city(self, country):
        """Get random city for country"""
        cities = {
            'US': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
            'UK': ['London', 'Manchester', 'Birmingham', 'Liverpool'],
            'Canada': ['Toronto', 'Vancouver', 'Montreal', 'Calgary'],
            'Australia': ['Sydney', 'Melbourne', 'Brisbane', 'Perth'],
            'India': ['Mumbai', 'Delhi', 'Bangalore', 'Chennai'],
            'Germany': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt'],
            'France': ['Paris', 'Marseille', 'Lyon', 'Toulouse'],
            'Brazil': ['Sao Paulo', 'Rio de Janeiro', 'Brasilia'],
            'Japan': ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama']
        }
        return random.choice(cities.get(country, ['Unknown']))
    
    def _get_timezone(self, country):
        """Get timezone for country"""
        timezones = {
            'US': ['America/New_York', 'America/Los_Angeles', 'America/Chicago'],
            'UK': ['Europe/London'],
            'Canada': ['America/Toronto', 'America/Vancouver'],
            'Australia': ['Australia/Sydney', 'Australia/Melbourne'],
            'India': ['Asia/Kolkata'],
            'Germany': ['Europe/Berlin'],
            'France': ['Europe/Paris'],
            'Brazil': ['America/Sao_Paulo'],
            'Japan': ['Asia/Tokyo']
        }
        return random.choice(timezones.get(country, ['UTC']))
    
    def generate_device_mix(self, total_views):
        """Generate device type mixture"""
        devices = [
            {'type': 'mobile', 'percentage': 0.75, 'brands': ['iPhone', 'Samsung', 'Google', 'Xiaomi']},
            {'type': 'desktop', 'percentage': 0.20, 'os': ['Windows', 'macOS', 'Linux']},
            {'type': 'tablet', 'percentage': 0.05, 'brands': ['iPad', 'Samsung Tablet']}
        ]
        
        device_views = []
        for device in devices:
            count = int(total_views * device['percentage'])
            for _ in range(count):
                if device['type'] == 'mobile':
                    brand = random.choice(device['brands'])
                    device_views.append({
                        'type': 'mobile',
                        'brand': brand,
                        'model': self._get_mobile_model(brand),
                        'os': 'iOS' if brand == 'iPhone' else 'Android'
                    })
                elif device['type'] == 'desktop':
                    os = random.choice(device['os'])
                    device_views.append({
                        'type': 'desktop',
                        'os': os,
                        'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])
                    })
                else:  # tablet
                    brand = random.choice(device['brands'])
                    device_views.append({
                        'type': 'tablet',
                        'brand': brand,
                        'os': 'iOS' if brand == 'iPad' else 'Android'
                    })
        
        return device_views
    
    def _get_mobile_model(self, brand):
        """Get mobile model for brand"""
        models = {
            'iPhone': ['iPhone 15', 'iPhone 14', 'iPhone 13', 'iPhone 12'],
            'Samsung': ['Galaxy S23', 'Galaxy S22', 'Galaxy A54', 'Galaxy Z Flip'],
            'Google': ['Pixel 8', 'Pixel 7', 'Pixel 6a'],
            'Xiaomi': ['Redmi Note 12', 'Mi 13', 'Poco X5']
        }
        return random.choice(models.get(brand, ['Unknown']))
    
    def analyze_pattern(self, patterns):
        """Analyze and learn from patterns"""
        if len(patterns) < 10:
            return None
        
        # Convert to features
        df = pd.DataFrame(patterns)
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        
        # Train KMeans for pattern clustering
        features = df[['hour', 'watch_time']].values
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        self.model = KMeans(n_clusters=3, random_state=42)
        clusters = self.model.fit_predict(features_scaled)
        
        # Analyze clusters
        df['cluster'] = clusters
        cluster_stats = df.groupby('cluster').agg({
            'hour': ['mean', 'std'],
            'watch_time': ['mean', 'std']
        })
        
        return {
            'clusters': cluster_stats.to_dict(),
            'total_patterns': len(patterns),
            'pattern_summary': {
                'avg_watch_time': df['watch_time'].mean(),
                'peak_hours': df['hour'].mode().tolist(),
                'device_distribution': df['device'].value_counts().to_dict() if 'device' in df.columns else None
            }
        }
    
    def save_patterns(self, patterns, filename='patterns.json'):
        """Save patterns to file"""
        with open(filename, 'w') as f:
            json.dump(patterns, f, indent=2)
    
    def load_patterns(self, filename='patterns.json'):
        """Load patterns from file"""
        with open(filename, 'r') as f:
            return json.load(f)