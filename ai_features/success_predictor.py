"""
ML model to predict view success rates
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pickle
import json
from datetime import datetime

class SuccessPredictor:
    def __init__(self):
        self.models = {}
        self.features = [
            'video_length', 'video_age', 'creator_followers',
            'time_of_day', 'day_of_week', 'geo_diversity',
            'previous_success_rate', 'method_used'
        ]
        
    def prepare_dataset(self, historical_data):
        """Prepare dataset from historical data"""
        df = pd.DataFrame(historical_data)
        
        # Feature engineering
        df['success_rate'] = df['views_increased'] / df['views_sent']
        df['success_label'] = (df['success_rate'] > 0.7).astype(int)
        
        # Encode categorical features
        df = pd.get_dummies(df, columns=['method_used', 'time_of_day'])
        
        return df
    
    def train_random_forest(self, df):
        """Train Random Forest model"""
        X = df.drop(['success_label', 'success_rate', 'views_increased', 'views_sent'], axis=1, errors='ignore')
        y = df['success_label']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        
        y_pred = rf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.models['random_forest'] = rf
        return rf, accuracy, classification_report(y_test, y_pred)
    
    def train_xgboost(self, df):
        """Train XGBoost model"""
        X = df.drop(['success_label', 'success_rate', 'views_increased', 'views_sent'], axis=1, errors='ignore')
        y = df['success_label']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        xgb_model.fit(X_train, y_train)
        
        y_pred = xgb_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.models['xgboost'] = xgb_model
        return xgb_model, accuracy, classification_report(y_test, y_pred)
    
    class SuccessDataset(Dataset):
        def __init__(self, features, labels):
            self.features = torch.FloatTensor(features)
            self.labels = torch.FloatTensor(labels)
        
        def __len__(self):
            return len(self.features)
        
        def __getitem__(self, idx):
            return self.features[idx], self.labels[idx]
    
    class NeuralNetwork(nn.Module):
        def __init__(self, input_size):
            super().__init__()
            self.fc1 = nn.Linear(input_size, 64)
            self.fc2 = nn.Linear(64, 32)
            self.fc3 = nn.Linear(32, 16)
            self.fc4 = nn.Linear(16, 1)
            self.relu = nn.ReLU()
            self.sigmoid = nn.Sigmoid()
            self.dropout = nn.Dropout(0.2)
        
        def forward(self, x):
            x = self.relu(self.fc1(x))
            x = self.dropout(x)
            x = self.relu(self.fc2(x))
            x = self.dropout(x)
            x = self.relu(self.fc3(x))
            x = self.fc4(x)
            return self.sigmoid(x)
    
    def train_neural_network(self, df, epochs=50):
        """Train Neural Network model"""
        X = df.drop(['success_label', 'success_rate', 'views_increased', 'views_sent'], axis=1, errors='ignore')
        y = df['success_label']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Convert to numpy
        X_train_np = X_train.values
        X_test_np = X_test.values
        y_train_np = y_train.values.reshape(-1, 1)
        y_test_np = y_test.values.reshape(-1, 1)
        
        # Create datasets
        train_dataset = self.SuccessDataset(X_train_np, y_train_np)
        test_dataset = self.SuccessDataset(X_test_np, y_test_np)
        
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=32)
        
        # Initialize model
        input_size = X_train_np.shape[1]
        model = self.NeuralNetwork(input_size)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # Training loop
        train_losses = []
        for epoch in range(epochs):
            model.train()
            epoch_loss = 0
            for batch_features, batch_labels in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_features)
                loss = criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            train_losses.append(epoch_loss / len(train_loader))
            
            if (epoch + 1) % 10 == 0:
                print(f'Epoch {epoch+1}/{epochs}, Loss: {epoch_loss/len(train_loader):.4f}')
        
        # Evaluation
        model.eval()
        test_predictions = []
        test_labels = []
        
        with torch.no_grad():
            for batch_features, batch_labels in test_loader:
                outputs = model(batch_features)
                predictions = (outputs > 0.5).float()
                test_predictions.extend(predictions.numpy())
                test_labels.extend(batch_labels.numpy())
        
        accuracy = accuracy_score(test_labels, test_predictions)
        self.models['neural_network'] = model
        
        return model, accuracy
    
    def predict_success(self, video_data, method='xgboost'):
        """Predict success probability for video"""
        if method not in self.models:
            raise ValueError(f"Model {method} not trained")
        
        model = self.models[method]
        
        # Prepare features
        features = self._extract_features(video_data)
        
        if method == 'neural_network':
            features_tensor = torch.FloatTensor(features).unsqueeze(0)
            with torch.no_grad():
                probability = model(features_tensor).item()
        else:
            probability = model.predict_proba([features])[0][1]
        
        return {
            'success_probability': probability,
            'confidence': 'high' if probability > 0.8 else 'medium' if probability > 0.6 else 'low',
            'recommended_method': self._recommend_method(video_data, probability)
        }
    
    def _extract_features(self, video_data):
        """Extract features from video data"""
        # Placeholder implementation
        features = [
            video_data.get('length', 60),
            video_data.get('age_hours', 24),
            video_data.get('followers', 1000),
            14,  # time_of_day (2PM)
            3,   # day_of_week (Wednesday)
            0.7, # geo_diversity
            0.85,# previous_success_rate
            1    # method_used (browser)
        ]
        return features
    
    def _recommend_method(self, video_data, probability):
        """Recommend best method based on prediction"""
        if probability > 0.85:
            return 'browser_automation'
        elif probability > 0.70:
            return 'api_method'
        elif probability > 0.60:
            return 'cloud_view'
        else:
            return 'hybrid_ai'
    
    def save_model(self, model_name, filename):
        """Save trained model to file"""
        model = self.models.get(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not found")
        
        if model_name == 'neural_network':
            torch.save(model.state_dict(), filename)
        else:
            with open(filename, 'wb') as f:
                pickle.dump(model, f)
    
    def load_model(self, model_name, filename):
        """Load trained model from file"""
        if model_name == 'neural_network':
            input_size = 8  # Number of features
            model = self.NeuralNetwork(input_size)
            model.load_state_dict(torch.load(filename))
            model.eval()
        else:
            with open(filename, 'rb') as f:
                model = pickle.load(f)
        
        self.models[model_name] = model
        return model