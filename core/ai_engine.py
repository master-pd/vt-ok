"""
Central AI Engine for VT ULTRA PRO
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import pickle
import os

class AIEngine:
    def __init__(self, config_path: str = 'config/ai_config.json'):
        self.config = self._load_config(config_path)
        self.models = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize sub-modules
        self.view_predictor = ViewSuccessPredictor()
        self.pattern_generator = PatternGenerator()
        self.anomaly_detector = AnomalyDetector()
        self.optimizer = AutoOptimizer()
        
        # Create models directory
        os.makedirs('models', exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load AI configuration"""
        default_config = {
            'model_settings': {
                'view_predictor': {
                    'input_size': 20,
                    'hidden_size': 64,
                    'output_size': 1,
                    'learning_rate': 0.001,
                    'epochs': 100
                },
                'pattern_generator': {
                    'latent_size': 32,
                    'hidden_size': 128,
                    'sequence_length': 24,
                    'learning_rate': 0.0005
                }
            },
            'training': {
                'batch_size': 32,
                'validation_split': 0.2,
                'early_stopping_patience': 10
            },
            'inference': {
                'confidence_threshold': 0.7,
                'max_predictions': 1000
            }
        }
        
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Merge with default
                default_config.update(user_config)
        except:
            pass
        
        return default_config
    
    class ViewSuccessDataset(Dataset):
        """Dataset for view success prediction"""
        def __init__(self, features, labels):
            self.features = torch.FloatTensor(features)
            self.labels = torch.FloatTensor(labels)
        
        def __len__(self):
            return len(self.features)
        
        def __getitem__(self, idx):
            return self.features[idx], self.labels[idx]
    
    class ViewSuccessPredictor(nn.Module):
        """Neural network for view success prediction"""
        def __init__(self, input_size: int, hidden_size: int = 64):
            super().__init__()
            self.model = nn.Sequential(
                nn.Linear(input_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(hidden_size // 2, 1),
                nn.Sigmoid()
            )
        
        def forward(self, x):
            return self.model(x)
    
    def train_view_predictor(self, training_data: pd.DataFrame) -> Dict:
        """Train view success predictor"""
        try:
            # Prepare data
            features = self._extract_features(training_data)
            labels = training_data['success_rate'].values
            
            # Split data
            from sklearn.model_selection import train_test_split
            X_train, X_val, y_train, y_val = train_test_split(
                features, labels, 
                test_size=self.config['training']['validation_split'],
                random_state=42
            )
            
            # Create datasets
            train_dataset = self.ViewSuccessDataset(X_train, y_train)
            val_dataset = self.ViewSuccessDataset(X_val, y_val)
            
            train_loader = DataLoader(
                train_dataset, 
                batch_size=self.config['training']['batch_size'],
                shuffle=True
            )
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config['training']['batch_size']
            )
            
            # Initialize model
            input_size = features.shape[1]
            model = self.ViewSuccessPredictor(input_size).to(self.device)
            criterion = nn.MSELoss()
            optimizer = optim.Adam(
                model.parameters(), 
                lr=self.config['model_settings']['view_predictor']['learning_rate']
            )
            
            # Training loop
            best_loss = float('inf')
            patience_counter = 0
            train_losses = []
            val_losses = []
            
            for epoch in range(self.config['model_settings']['view_predictor']['epochs']):
                # Training
                model.train()
                train_loss = 0
                for batch_features, batch_labels in train_loader:
                    batch_features = batch_features.to(self.device)
                    batch_labels = batch_labels.to(self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_features)
                    loss = criterion(outputs.squeeze(), batch_labels)
                    loss.backward()
                    optimizer.step()
                    
                    train_loss += loss.item()
                
                # Validation
                model.eval()
                val_loss = 0
                with torch.no_grad():
                    for batch_features, batch_labels in val_loader:
                        batch_features = batch_features.to(self.device)
                        batch_labels = batch_labels.to(self.device)
                        
                        outputs = model(batch_features)
                        loss = criterion(outputs.squeeze(), batch_labels)
                        val_loss += loss.item()
                
                # Calculate averages
                train_loss_avg = train_loss / len(train_loader)
                val_loss_avg = val_loss / len(val_loader)
                
                train_losses.append(train_loss_avg)
                val_losses.append(val_loss_avg)
                
                # Early stopping
                if val_loss_avg < best_loss:
                    best_loss = val_loss_avg
                    patience_counter = 0
                    # Save best model
                    torch.save(model.state_dict(), 'models/best_view_predictor.pth')
                else:
                    patience_counter += 1
                
                if patience_counter >= self.config['training']['early_stopping_patience']:
                    print(f"Early stopping at epoch {epoch}")
                    break
                
                if (epoch + 1) % 10 == 0:
                    print(f"Epoch {epoch+1}: Train Loss: {train_loss_avg:.4f}, Val Loss: {val_loss_avg:.4f}")
            
            # Load best model
            model.load_state_dict(torch.load('models/best_view_predictor.pth'))
            self.models['view_predictor'] = model
            
            return {
                'status': 'success',
                'train_losses': train_losses,
                'val_losses': val_losses,
                'best_val_loss': best_loss,
                'epochs_trained': epoch + 1
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract features from data"""
        features = []
        
        for _, row in data.iterrows():
            feature_vector = []
            
            # Time features
            if 'timestamp' in row:
                dt = pd.to_datetime(row['timestamp'])
                feature_vector.extend([
                    dt.hour / 24.0,
                    dt.day / 31.0,
                    dt.month / 12.0,
                    dt.dayofweek / 7.0
                ])
            
            # Video features
            feature_vector.extend([
                row.get('video_length', 60) / 300.0,  # Normalized to 5 minutes
                row.get('video_age_hours', 24) / 720.0,  # Normalized to 30 days
                row.get('creator_followers', 1000) / 1000000.0  # Normalized to 1M
            ])
            
            # Method features (one-hot encoded)
            methods = ['browser', 'api', 'cloud', 'hybrid']
            method = row.get('method', 'browser')
            for m in methods:
                feature_vector.append(1.0 if m == method else 0.0)
            
            # Previous performance
            feature_vector.append(row.get('previous_success_rate', 0.8))
            feature_vector.append(row.get('previous_views', 1000) / 10000.0)
            
            # Geographic diversity
            feature_vector.append(row.get('geo_diversity', 0.5))
            
            # Device mix
            feature_vector.append(row.get('device_mix', 0.7))
            
            # Add noise for robustness
            feature_vector.append(np.random.normal(0, 0.01))
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def predict_view_success(self, video_data: Dict) -> Dict:
        """Predict view success probability"""
        try:
            if 'view_predictor' not in self.models:
                return {
                    'success_probability': 0.85,  # Default
                    'confidence': 'medium',
                    'model_loaded': False
                }
            
            model = self.models['view_predictor']
            model.eval()
            
            # Prepare features
            features = self._extract_single_features(video_data)
            features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                prediction = model(features_tensor).item()
            
            # Calculate confidence
            confidence = self._calculate_confidence(prediction)
            
            # Recommend method
            recommended_method = self._recommend_method(prediction, video_data)
            
            return {
                'success_probability': prediction,
                'confidence': confidence,
                'recommended_method': recommended_method,
                'estimated_delivery_time': self._estimate_delivery_time(prediction),
                'risk_level': self._assess_risk(prediction)
            }
            
        except Exception as e:
            return {
                'success_probability': 0.85,
                'confidence': 'low',
                'error': str(e)
            }
    
    def _extract_single_features(self, video_data: Dict) -> List[float]:
        """Extract features for single prediction"""
        features = []
        
        # Time features (current time)
        dt = datetime.now()
        features.extend([
            dt.hour / 24.0,
            dt.day / 31.0,
            dt.month / 12.0,
            dt.weekday() / 7.0
        ])
        
        # Video features
        features.extend([
            video_data.get('length', 60) / 300.0,
            video_data.get('age_hours', 24) / 720.0,
            video_data.get('creator_followers', 1000) / 1000000.0
        ])
        
        # Method features (default to browser)
        methods = ['browser', 'api', 'cloud', 'hybrid']
        method = video_data.get('preferred_method', 'browser')
        for m in methods:
            features.append(1.0 if m == method else 0.0)
        
        # Historical data
        features.extend([
            video_data.get('historical_success_rate', 0.8),
            video_data.get('historical_views', 1000) / 10000.0,
            video_data.get('geo_diversity', 0.5),
            video_data.get('device_mix', 0.7)
        ])
        
        # Random noise
        features.append(np.random.normal(0, 0.01))
        
        return features
    
    def _calculate_confidence(self, probability: float) -> str:
        """Calculate prediction confidence"""
        if probability > 0.9 or probability < 0.1:
            return 'high'
        elif probability > 0.8 or probability < 0.2:
            return 'medium'
        else:
            return 'low'
    
    def _recommend_method(self, probability: float, video_data: Dict) -> str:
        """Recommend best method based on prediction"""
        if probability > 0.9:
            return 'browser'  # Most reliable
        elif probability > 0.8:
            return 'api'  # Fast and reliable
        elif probability > 0.7:
            return 'cloud'  # Good balance
        elif probability > 0.6:
            return 'hybrid'  # Mixed approach
        else:
            return 'browser'  # Safest option
    
    def _estimate_delivery_time(self, probability: float) -> int:
        """Estimate delivery time in hours"""
        if probability > 0.9:
            return 1  # 1 hour
        elif probability > 0.8:
            return 2  # 2 hours
        elif probability > 0.7:
            return 4  # 4 hours
        elif probability > 0.6:
            return 8  # 8 hours
        else:
            return 12  # 12 hours
    
    def _assess_risk(self, probability: float) -> str:
        """Assess risk level"""
        if probability > 0.9:
            return 'very_low'
        elif probability > 0.8:
            return 'low'
        elif probability > 0.7:
            return 'medium'
        elif probability > 0.6:
            return 'high'
        else:
            return 'very_high'
    
    class PatternGenerator(nn.Module):
        """GAN for generating organic view patterns"""
        def __init__(self, latent_size: int = 32, output_size: int = 24):
            super().__init__()
            self.generator = nn.Sequential(
                nn.Linear(latent_size, 64),
                nn.ReLU(),
                nn.Linear(64, 128),
                nn.ReLU(),
                nn.Linear(128, 256),
                nn.ReLU(),
                nn.Linear(256, output_size),
                nn.Sigmoid()
            )
            
            self.discriminator = nn.Sequential(
                nn.Linear(output_size, 128),
                nn.LeakyReLU(0.2),
                nn.Linear(128, 64),
                nn.LeakyReLU(0.2),
                nn.Linear(64, 1),
                nn.Sigmoid()
            )
        
        def forward(self, z):
            return self.generator(z)
    
    def generate_organic_pattern(self, views_count: int, 
                                duration_hours: int = 24) -> List[Dict]:
        """Generate organic view pattern"""
        try:
            # Generate base pattern
            base_pattern = self.pattern_generator.generate_pattern(
                views_count, 
                duration_hours
            )
            
            # Add randomness
            pattern = self._add_organic_noise(base_pattern)
            
            # Ensure total views
            pattern = self._normalize_pattern(pattern, views_count)
            
            # Add geographic distribution
            pattern = self._add_geographic_distribution(pattern)
            
            # Add device mix
            pattern = self._add_device_mix(pattern)
            
            # Add timezone adjustments
            pattern = self._adjust_for_timezones(pattern)
            
            return pattern
            
        except Exception as e:
            # Fallback to basic pattern
            return self._generate_basic_pattern(views_count, duration_hours)
    
    def _add_organic_noise(self, pattern: List[Dict]) -> List[Dict]:
        """Add organic noise to pattern"""
        for entry in pattern:
            # Random watch time variation
            if 'watch_time' in entry:
                entry['watch_time'] *= np.random.uniform(0.8, 1.2)
                entry['watch_time'] = max(5, min(180, entry['watch_time']))
            
            # Random interaction probability
            if random.random() < 0.3:
                entry['interaction'] = random.choice(['like', 'comment_view', 'share'])
            
            # Random device switch
            if random.random() < 0.1:
                entry['device'] = random.choice(['mobile', 'desktop', 'tablet'])
        
        return pattern
    
    def _normalize_pattern(self, pattern: List[Dict], target_views: int) -> List[Dict]:
        """Normalize pattern to target views"""
        current_views = len(pattern)
        
        if current_views < target_views:
            # Add more views
            views_to_add = target_views - current_views
            new_entries = self._generate_additional_entries(views_to_add, pattern)
            pattern.extend(new_entries)
        
        elif current_views > target_views:
            # Remove excess views (randomly)
            indices_to_remove = np.random.choice(
                len(pattern), 
                current_views - target_views, 
                replace=False
            )
            pattern = [entry for i, entry in enumerate(pattern) 
                      if i not in indices_to_remove]
        
        return pattern
    
    def _add_geographic_distribution(self, pattern: List[Dict]) -> List[Dict]:
        """Add geographic distribution to pattern"""
        countries = ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'JP', 'BR', 'IN']
        weights = [0.35, 0.15, 0.10, 0.08, 0.07, 0.06, 0.05, 0.05, 0.09]
        
        for entry in pattern:
            country = np.random.choice(countries, p=weights)
            entry['country'] = country
            entry['city'] = self._get_random_city(country)
            entry['timezone'] = self._get_timezone(country)
        
        return pattern
    
    def _get_random_city(self, country: str) -> str:
        """Get random city for country"""
        cities = {
            'US': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
            'UK': ['London', 'Manchester', 'Birmingham', 'Liverpool'],
            'CA': ['Toronto', 'Vancouver', 'Montreal', 'Calgary'],
            'AU': ['Sydney', 'Melbourne', 'Brisbane', 'Perth'],
            'DE': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt'],
            'FR': ['Paris', 'Marseille', 'Lyon', 'Toulouse'],
            'JP': ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama'],
            'BR': ['Sao Paulo', 'Rio de Janeiro', 'Brasilia'],
            'IN': ['Mumbai', 'Delhi', 'Bangalore', 'Chennai']
        }
        return random.choice(cities.get(country, ['Unknown']))
    
    def _get_timezone(self, country: str) -> str:
        """Get timezone for country"""
        timezones = {
            'US': 'America/New_York',
            'UK': 'Europe/London',
            'CA': 'America/Toronto',
            'AU': 'Australia/Sydney',
            'DE': 'Europe/Berlin',
            'FR': 'Europe/Paris',
            'JP': 'Asia/Tokyo',
            'BR': 'America/Sao_Paulo',
            'IN': 'Asia/Kolkata'
        }
        return timezones.get(country, 'UTC')
    
    def _add_device_mix(self, pattern: List[Dict]) -> List[Dict]:
        """Add device mix to pattern"""
        device_distribution = {
            'mobile': 0.75,
            'desktop': 0.20,
            'tablet': 0.05
        }
        
        devices = list(device_distribution.keys())
        probs = list(device_distribution.values())
        
        for entry in pattern:
            device = np.random.choice(devices, p=probs)
            entry['device'] = device
            
            if device == 'mobile':
                brands = ['iPhone', 'Samsung', 'Google', 'Xiaomi']
                entry['device_brand'] = random.choice(brands)
                entry['os'] = 'iOS' if entry['device_brand'] == 'iPhone' else 'Android'
            elif device == 'desktop':
                entry['os'] = random.choice(['Windows', 'macOS', 'Linux'])
                entry['browser'] = random.choice(['Chrome', 'Firefox', 'Safari'])
            else:  # tablet
                entry['device_brand'] = random.choice(['iPad', 'Samsung Tablet'])
                entry['os'] = 'iOS' if entry['device_brand'] == 'iPad' else 'Android'
        
        return pattern
    
    def _adjust_for_timezones(self, pattern: List[Dict]) -> List[Dict]:
        """Adjust pattern for different timezones"""
        for entry in pattern:
            if 'country' in entry and 'timezone' in entry:
                # Adjust hour based on timezone
                hour = entry.get('hour', 12)
                country = entry['country']
                
                # Simple timezone offset (in reality, use pytz)
                offsets = {
                    'US': -5, 'UK': 0, 'CA': -5, 'AU': 10,
                    'DE': 1, 'FR': 1, 'JP': 9, 'BR': -3, 'IN': 5.5
                }
                
                offset = offsets.get(country, 0)
                adjusted_hour = (hour + offset) % 24
                entry['local_hour'] = adjusted_hour
        
        return pattern
    
    def _generate_basic_pattern(self, views_count: int, 
                               duration_hours: int) -> List[Dict]:
        """Generate basic pattern as fallback"""
        pattern = []
        views_per_hour = max(1, views_count // duration_hours)
        
        for hour in range(duration_hours):
            hour_views = views_per_hour + random.randint(-2, 2)
            hour_views = max(0, hour_views)
            
            for _ in range(hour_views):
                entry = {
                    'hour': hour,
                    'minute': random.randint(0, 59),
                    'second': random.randint(0, 59),
                    'watch_time': random.randint(15, 60),
                    'device': random.choice(['mobile', 'desktop']),
                    'country': random.choice(['US', 'UK', 'CA']),
                    'interaction': random.choice(['none', 'like', 'view']) if random.random() < 0.3 else 'none'
                }
                pattern.append(entry)
        
        # Trim or extend to exact count
        if len(pattern) > views_count:
            pattern = pattern[:views_count]
        else:
            while len(pattern) < views_count:
                hour = random.randint(0, duration_hours - 1)
                entry = {
                    'hour': hour,
                    'minute': random.randint(0, 59),
                    'second': random.randint(0, 59),
                    'watch_time': random.randint(15, 60),
                    'device': random.choice(['mobile', 'desktop']),
                    'country': random.choice(['US', 'UK', 'CA']),
                    'interaction': 'none'
                }
                pattern.append(entry)
        
        return pattern
    
    def _generate_additional_entries(self, count: int, 
                                   base_pattern: List[Dict]) -> List[Dict]:
        """Generate additional pattern entries"""
        new_entries = []
        
        for _ in range(count):
            # Copy random entry from base pattern
            base_entry = random.choice(base_pattern)
            new_entry = base_entry.copy()
            
            # Add some variation
            new_entry['hour'] = (new_entry.get('hour', 12) + random.randint(-2, 2)) % 24
            new_entry['minute'] = random.randint(0, 59)
            new_entry['watch_time'] = new_entry.get('watch_time', 30) * random.uniform(0.8, 1.2)
            
            new_entries.append(new_entry)
        
        return new_entries
    
    class AnomalyDetector:
        """Anomaly detection for view patterns"""
        def __init__(self):
            self.thresholds = {
                'view_spike': 3.0,
                'success_drop': 0.5,
                'pattern_deviation': 2.0
            }
        
        def detect(self, pattern: List[Dict], 
                  historical_patterns: List[List[Dict]]) -> List[Dict]:
            """Detect anomalies in pattern"""
            anomalies = []
            
            # Check view spikes
            spikes = self._detect_view_spikes(pattern)
            anomalies.extend(spikes)
            
            # Check pattern deviation
            deviations = self._detect_pattern_deviations(pattern, historical_patterns)
            anomalies.extend(deviations)
            
            # Check geographic anomalies
            geo_anomalies = self._detect_geo_anomalies(pattern)
            anomalies.extend(geo_anomalies)
            
            return anomalies
        
        def _detect_view_spikes(self, pattern: List[Dict]) -> List[Dict]:
            """Detect sudden spikes in views"""
            anomalies = []
            
            # Group by hour
            hourly_counts = {}
            for entry in pattern:
                hour = entry.get('hour', 0)
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            
            # Calculate statistics
            counts = list(hourly_counts.values())
            if len(counts) > 1:
                mean = np.mean(counts)
                std = np.std(counts)
                
                for hour, count in hourly_counts.items():
                    if count > mean + 3 * std:
                        anomalies.append({
                            'type': 'view_spike',
                            'hour': hour,
                            'count': count,
                            'expected_max': int(mean + 2 * std),
                            'severity': 'high'
                        })
            
            return anomalies
        
        def _detect_pattern_deviations(self, pattern: List[Dict],
                                     historical_patterns: List[List[Dict]]) -> List[Dict]:
            """Detect deviations from historical patterns"""
            anomalies = []
            
            if not historical_patterns:
                return anomalies
            
            # Calculate historical averages
            hist_hourly = []
            for hist_pattern in historical_patterns:
                hourly_counts = {}
                for entry in hist_pattern:
                    hour = entry.get('hour', 0)
                    hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
                hist_hourly.append(hourly_counts)
            
            # Compare with current pattern
            current_hourly = {}
            for entry in pattern:
                hour = entry.get('hour', 0)
                current_hourly[hour] = current_hourly.get(hour, 0) + 1
            
            for hour in set(list(current_hourly.keys()) + 
                          [h for hist in hist_hourly for h in hist.keys()]):
                current = current_hourly.get(hour, 0)
                historical = [hist.get(hour, 0) for hist in hist_hourly]
                
                if historical:
                    hist_mean = np.mean(historical)
                    hist_std = np.std(historical)
                    
                    if hist_std > 0:
                        z_score = (current - hist_mean) / hist_std
                        
                        if abs(z_score) > self.thresholds['pattern_deviation']:
                            anomalies.append({
                                'type': 'pattern_deviation',
                                'hour': hour,
                                'current': current,
                                'historical_mean': hist_mean,
                                'z_score': z_score,
                                'severity': 'high' if abs(z_score) > 3 else 'medium'
                            })
            
            return anomalies
        
        def _detect_geo_anomalies(self, pattern: List[Dict]) -> List[Dict]:
            """Detect geographic anomalies"""
            anomalies = []
            
            # Count by country
            country_counts = {}
            for entry in pattern:
                country = entry.get('country', 'Unknown')
                country_counts[country] = country_counts.get(country, 0) + 1
            
            total = len(pattern)
            
            for country, count in country_counts.items():
                percentage = count / total
                
                # Check for concentration
                if percentage > 0.8:
                    anomalies.append({
                        'type': 'geo_concentration',
                        'country': country,
                        'percentage': percentage * 100,
                        'severity': 'high'
                    })
                
                # Check for unusual countries
                unusual = ['KP', 'SY', 'IR', 'CU', 'RU']  # High-risk countries
                if country in unusual:
                    anomalies.append({
                        'type': 'unusual_country',
                        'country': country,
                        'count': count,
                        'severity': 'high'
                    })
            
            return anomalies
    
    class AutoOptimizer:
        """Auto-optimization for view parameters"""
        def __init__(self):
            self.parameters = {
                'watch_time': {'min': 5, 'max': 180, 'current': 30},
                'views_per_hour': {'min': 1, 'max': 100, 'current': 10},
                'delay_between': {'min': 1.0, 'max': 10.0, 'current': 3.0},
                'interaction_rate': {'min': 0.0, 'max': 0.5, 'current': 0.1},
                'geo_diversity': {'min': 0.1, 'max': 1.0, 'current': 0.5}
            }
            
            self.history = []
        
        def optimize(self, performance_data: List[Dict]) -> Dict:
            """Optimize parameters based on performance"""
            if not performance_data:
                return self.parameters
            
            # Calculate success rates
            success_rates = []
            for data in performance_data:
                if data.get('views_sent', 0) > 0:
                    rate = data.get('views_delivered', 0) / data.get('views_sent', 1)
                    success_rates.append({
                        'rate': rate,
                        'parameters': data.get('parameters', {})
                    })
            
            if not success_rates:
                return self.parameters
            
            # Find best performing parameters
            best = max(success_rates, key=lambda x: x['rate'])
            
            # Adjust parameters towards best performing
            for param_name in self.parameters:
                if param_name in best['parameters']:
                    best_value = best['parameters'][param_name]
                    current = self.parameters[param_name]['current']
                    
                    # Move 10% towards best value
                    new_value = current + 0.1 * (best_value - current)
                    
                    # Clamp to valid range
                    min_val = self.parameters[param_name]['min']
                    max_val = self.parameters[param_name]['max']
                    new_value = max(min_val, min(max_val, new_value))
                    
                    self.parameters[param_name]['current'] = new_value
            
            # Save to history
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'parameters': {k: v['current'] for k, v in self.parameters.items()},
                'success_rate': best['rate']
            })
            
            return self.parameters
        
        def get_recommendations(self) -> List[str]:
            """Get optimization recommendations"""
            recommendations = []
            
            if self.parameters['watch_time']['current'] < 15:
                recommendations.append("Increase minimum watch time to at least 15 seconds")
            
            if self.parameters['views_per_hour']['current'] > 50:
                recommendations.append("Reduce views per hour for more organic appearance")
            
            if self.parameters['geo_diversity']['current'] < 0.3:
                recommendations.append("Increase geographic diversity")
            
            if self.parameters['interaction_rate']['current'] < 0.05:
                recommendations.append("Add some interactions (likes/comments)")
            
            return recommendations
    
    def save_model(self, model_name: str, path: str = None):
        """Save AI model"""
        if model_name not in self.models:
            return False
        
        if path is None:
            path = f"models/{model_name}.pth"
        
        try:
            torch.save(self.models[model_name].state_dict(), path)
            
            # Save metadata
            metadata = {
                'model_name': model_name,
                'saved_at': datetime.now().isoformat(),
                'device': str(self.device),
                'config': self.config['model_settings'].get(model_name, {})
            }
            
            with open(f"models/{model_name}_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, model_name: str, path: str = None):
        """Load AI model"""
        if path is None:
            path = f"models/{model_name}.pth"
        
        try:
            # Load metadata
            metadata_path = f"models/{model_name}_metadata.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Initialize model
            if model_name == 'view_predictor':
                input_size = self.config['model_settings']['view_predictor']['input_size']
                model = self.ViewSuccessPredictor(input_size)
            else:
                return False
            
            # Load weights
            model.load_state_dict(torch.load(path, map_location=self.device))
            model.to(self.device)
            model.eval()
            
            self.models[model_name] = model
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def get_system_status(self) -> Dict:
        """Get AI system status"""
        return {
            'models_loaded': list(self.models.keys()),
            'device': str(self.device),
            'config': self.config,
            'pattern_generator': 'ready',
            'anomaly_detector': 'ready',
            'optimizer': 'ready',
            'memory_usage': self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> Dict:
        """Get memory usage"""
        if torch.cuda.is_available():
            return {
                'cuda_allocated': torch.cuda.memory_allocated() / 1024**3,
                'cuda_reserved': torch.cuda.memory_reserved() / 1024**3,
                'cuda_max_allocated': torch.cuda.max_memory_allocated() / 1024**3
            }
        else:
            import psutil
            process = psutil.Process()
            return {
                'memory_percent': process.memory_percent(),
                'memory_rss': process.memory_info().rss / 1024**3
            }