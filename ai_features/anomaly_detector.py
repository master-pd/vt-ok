"""
Detect anomalies in view patterns
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
import pandas as pd
from datetime import datetime, timedelta
import json

class AnomalyDetector:
    def __init__(self):
        self.models = {}
        self.thresholds = {
            'view_spike': 3.0,  # 3x normal rate
            'success_drop': 0.5,  # 50% drop
            'pattern_deviation': 2.0,  # 2 standard deviations
            'geo_anomaly': 0.8  # 80% from single location
        }
        
    def detect_view_spikes(self, view_data, window_hours=24):
        """Detect sudden spikes in views"""
        df = pd.DataFrame(view_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Resample to hourly
        hourly_views = df.resample('1H').size()
        
        # Calculate rolling statistics
        rolling_mean = hourly_views.rolling(window=window_hours, min_periods=1).mean()
        rolling_std = hourly_views.rolling(window=window_hours, min_periods=1).std()
        
        # Detect spikes (more than 3 standard deviations from mean)
        spikes = hourly_views[
            (hourly_views > rolling_mean + 3 * rolling_std) |
            (hourly_views > rolling_mean * self.thresholds['view_spike'])
        ]
        
        anomalies = []
        for timestamp, count in spikes.items():
            anomalies.append({
                'type': 'view_spike',
                'timestamp': timestamp.isoformat(),
                'view_count': count,
                'expected_max': int(rolling_mean[timestamp] * self.thresholds['view_spike']),
                'severity': min(1.0, (count - rolling_mean[timestamp]) / rolling_mean[timestamp])
            })
        
        return anomalies
    
    def detect_success_rate_drops(self, success_data, threshold=None):
        """Detect drops in success rates"""
        if threshold is None:
            threshold = self.thresholds['success_drop']
        
        df = pd.DataFrame(success_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Calculate rolling success rate
        df['success_rate'] = df['successful_views'] / df['total_views']
        rolling_success = df['success_rate'].rolling(window=12, min_periods=1).mean()
        
        # Detect drops (more than threshold drop from average)
        avg_success = rolling_success.mean()
        drops = df[df['success_rate'] < avg_success * threshold]
        
        anomalies = []
        for timestamp, row in drops.iterrows():
            anomalies.append({
                'type': 'success_drop',
                'timestamp': timestamp.isoformat(),
                'success_rate': row['success_rate'],
                'expected_min': avg_success * threshold,
                'drop_percentage': (1 - row['success_rate'] / avg_success) * 100
            })
        
        return anomalies
    
    def detect_geo_anomalies(self, geo_data):
        """Detect geographic anomalies"""
        df = pd.DataFrame(geo_data)
        
        # Count views per country
        country_counts = df['country'].value_counts()
        total_views = len(df)
        
        anomalies = []
        for country, count in country_counts.items():
            percentage = count / total_views
            
            if percentage > self.thresholds['geo_anomaly']:
                anomalies.append({
                    'type': 'geo_concentration',
                    'country': country,
                    'percentage': percentage * 100,
                    'view_count': count,
                    'threshold': self.thresholds['geo_anomaly'] * 100,
                    'recommendation': f'Diversify views from other countries'
                })
        
        # Check for unusual countries
        unusual_countries = ['North Korea', 'Syria', 'Iran', 'Cuba', 'Russia']
        for country in unusual_countries:
            if country in country_counts:
                anomalies.append({
                    'type': 'unusual_country',
                    'country': country,
                    'view_count': country_counts[country],
                    'warning': 'Views from high-risk country detected'
                })
        
        return anomalies
    
    def detect_pattern_deviations(self, pattern_data):
        """Detect deviations from normal patterns using Isolation Forest"""
        df = pd.DataFrame(pattern_data)
        
        # Extract features
        features = self._extract_pattern_features(df)
        
        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        iso_forest.fit(features)
        predictions = iso_forest.predict(features)
        scores = iso_forest.decision_function(features)
        
        # Detect anomalies
        anomalies = []
        for idx, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly
                anomalies.append({
                    'type': 'pattern_deviation',
                    'index': idx,
                    'anomaly_score': float(score),
                    'features': features[idx].tolist(),
                    'timestamp': df.iloc[idx]['timestamp'] if 'timestamp' in df.columns else None
                })
        
        return anomalies
    
    def _extract_pattern_features(self, df):
        """Extract features for pattern analysis"""
        features = []
        
        for _, row in df.iterrows():
            feature_vector = []
            
            # Time-based features
            if 'timestamp' in row:
                dt = pd.to_datetime(row['timestamp'])
                feature_vector.extend([
                    dt.hour,
                    dt.minute,
                    dt.dayofweek,
                    dt.day / 31,  # Normalized day of month
                ])
            
            # View pattern features
            if 'watch_time' in row:
                feature_vector.append(row['watch_time'])
            
            if 'action_type' in row:
                # Encode action type
                action_map = {'view': 0, 'view_like': 1, 'view_comment': 2}
                feature_vector.append(action_map.get(row['action_type'], 0))
            
            if 'device' in row:
                # Encode device type
                device_map = {'mobile': 0, 'desktop': 1, 'tablet': 2}
                feature_vector.append(device_map.get(row['device'], 0))
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def detect_multi_account_patterns(self, account_data):
        """Detect patterns indicating multiple accounts from same source"""
        df = pd.DataFrame(account_data)
        
        anomalies = []
        
        # Check for same IP with multiple accounts
        ip_counts = df['ip_address'].value_counts()
        for ip, count in ip_counts.items():
            if count > 3:  # More than 3 accounts from same IP
                accounts = df[df['ip_address'] == ip]['account_id'].unique()
                anomalies.append({
                    'type': 'multi_account_ip',
                    'ip_address': ip,
                    'account_count': count,
                    'accounts': accounts.tolist(),
                    'risk_level': 'high' if count > 5 else 'medium'
                })
        
        # Check for same user agent patterns
        ua_counts = df['user_agent'].value_counts()
        for ua, count in ua_counts.items():
            if count > 2:
                anomalies.append({
                    'type': 'common_user_agent',
                    'user_agent': ua[:50],  # Truncate for readability
                    'count': count,
                    'risk_level': 'medium'
                })
        
        # Check for timing patterns (accounts created at same time)
        if 'created_at' in df.columns:
            df['created_hour'] = pd.to_datetime(df['created_at']).dt.hour
            hour_counts = df['created_hour'].value_counts()
            for hour, count in hour_counts.items():
                if count > 5:  # More than 5 accounts created in same hour
                    anomalies.append({
                        'type': 'batch_account_creation',
                        'hour': hour,
                        'count': count,
                        'risk_level': 'high'
                    })
        
        return anomalies
    
    def generate_anomaly_report(self, all_anomalies, severity_threshold=0.5):
        """Generate comprehensive anomaly report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_anomalies': len(all_anomalies),
            'anomalies_by_type': {},
            'high_risk_anomalies': [],
            'recommended_actions': []
        }
        
        # Categorize anomalies
        for anomaly in all_anomalies:
            anomaly_type = anomaly['type']
            if anomaly_type not in report['anomalies_by_type']:
                report['anomalies_by_type'][anomaly_type] = 0
            report['anomalies_by_type'][anomaly_type] += 1
            
            # Check severity
            severity = anomaly.get('severity', 0)
            if severity > severity_threshold:
                report['high_risk_anomalies'].append(anomaly)
        
        # Generate recommendations
        if report['anomalies_by_type'].get('view_spike', 0) > 0:
            report['recommended_actions'].append(
                "Gradually increase views instead of sudden spikes"
            )
        
        if report['anomalies_by_type'].get('success_drop', 0) > 0:
            report['recommended_actions'].append(
                "Review recent changes to view methods or parameters"
            )
        
        if report['anomalies_by_type'].get('geo_concentration', 0) > 0:
            report['recommended_actions'].append(
                "Diversify geographic sources of views"
            )
        
        if report['anomalies_by_type'].get('multi_account_ip', 0) > 0:
            report['recommended_actions'].append(
                "Use different IP addresses for different accounts"
            )
        
        return report
    
    def save_anomalies(self, anomalies, filename='anomalies_detected.json'):
        """Save detected anomalies to file"""
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'anomalies': anomalies,
                'count': len(anomalies)
            }, f, indent=2)
    
    def load_anomalies(self, filename='anomalies_detected.json'):
        """Load previously detected anomalies"""
        with open(filename, 'r') as f:
            data = json.load(f)
        return data.get('anomalies', [])