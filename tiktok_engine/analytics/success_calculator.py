"""
AI-Powered Success Rate Calculator and Predictor
"""

import asyncio
import logging
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import statistics
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class SuccessFactor:
    name: str
    weight: float
    current_value: float
    optimal_value: float
    impact: float = 0.0

@dataclass
class PredictionResult:
    predicted_success_rate: float
    confidence: float
    factors: Dict[str, float]
    recommendations: List[str]
    estimated_views: int
    risk_level: str

class SuccessCalculator:
    def __init__(self):
        self.factors: Dict[str, SuccessFactor] = {}
        self.historical_data = []
        self.ml_model = None
        self._init_factors()
        
    def _init_factors(self):
        """Initialize success factors with weights"""
        self.factors = {
            'time_of_day': SuccessFactor(
                name='Time of Day',
                weight=0.15,
                current_value=0.5,
                optimal_value=0.85
            ),
            'method_quality': SuccessFactor(
                name='Method Quality',
                weight=0.25,
                current_value=0.7,
                optimal_value=0.95
            ),
            'proxy_quality': SuccessFactor(
                name='Proxy Quality',
                weight=0.20,
                current_value=0.6,
                optimal_value=0.9
            ),
            'account_age': SuccessFactor(
                name='Account Age',
                weight=0.10,
                current_value=0.5,
                optimal_value=0.8
            ),
            'view_duration': SuccessFactor(
                name='View Duration',
                weight=0.15,
                current_value=0.65,
                optimal_value=0.88
            ),
            'geo_location': SuccessFactor(
                name='Geo Location',
                weight=0.10,
                current_value=0.55,
                optimal_value=0.75
            ),
            'device_quality': SuccessFactor(
                name='Device Quality',
                weight=0.05,
                current_value=0.7,
                optimal_value=0.85
            )
        }
    
    async def calculate_success_rate(self, video_data: Dict, 
                                   historical_data: List[Dict] = None) -> PredictionResult:
        """
        Calculate predicted success rate for a video
        
        Args:
            video_data: Video information including URL, category, etc.
            historical_data: Previous success data for similar videos
            
        Returns:
            PredictionResult with success rate and recommendations
        """
        logger.info(f"Calculating success rate for: {video_data.get('video_url', 'Unknown')}")
        
        # Update factors based on video data
        self._update_factors_from_data(video_data)
        
        # Calculate base success rate
        base_rate = self._calculate_base_success_rate()
        
        # Apply historical data adjustments
        if historical_data:
            historical_adjustment = self._calculate_historical_adjustment(historical_data)
            base_rate *= historical_adjustment
        
        # Apply time-based adjustments
        time_adjustment = self._calculate_time_adjustment()
        base_rate *= time_adjustment
        
        # Apply method-specific adjustments
        method = video_data.get('method', 'browser')
        method_adjustment = self._get_method_adjustment(method)
        base_rate *= method_adjustment
        
        # Calculate confidence
        confidence = self._calculate_confidence(video_data)
        
        # Calculate factor impacts
        factor_impacts = self._calculate_factor_impacts()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(factor_impacts)
        
        # Estimate views
        estimated_views = self._estimate_views(base_rate, video_data)
        
        # Determine risk level
        risk_level = self._determine_risk_level(base_rate, confidence)
        
        # Ensure bounds
        predicted_rate = max(0.1, min(0.99, base_rate))
        
        result = PredictionResult(
            predicted_success_rate=predicted_rate,
            confidence=confidence,
            factors=factor_impacts,
            recommendations=recommendations,
            estimated_views=estimated_views,
            risk_level=risk_level
        )
        
        logger.info(f"Success prediction: {predicted_rate:.1%} (confidence: {confidence:.1%})")
        
        return result
    
    def _update_factors_from_data(self, video_data: Dict):
        """Update factors based on video data"""
        current_hour = datetime.now().hour
        
        # Time of day factor
        if 18 <= current_hour <= 22:  # Peak hours
            self.factors['time_of_day'].current_value = 0.85
        elif 0 <= current_hour <= 6:  # Night
            self.factors['time_of_day'].current_value = 0.65
        else:  # Day
            self.factors['time_of_day'].current_value = 0.75
        
        # Method quality factor
        method = video_data.get('method', 'browser')
        method_quality = {
            'browser': 0.85,
            'api': 0.70,
            'cloud': 0.60,
            'hybrid': 0.92
        }.get(method, 0.7)
        self.factors['method_quality'].current_value = method_quality
        
        # Proxy quality (simulated - would use actual proxy metrics)
        self.factors['proxy_quality'].current_value = 0.6 + (random.random() * 0.3)
        
        # View duration (simulated)
        view_duration = video_data.get('view_duration', 30)
        if view_duration >= 45:
            self.factors['view_duration'].current_value = 0.85
        elif view_duration >= 30:
            self.factors['view_duration'].current_value = 0.75
        else:
            self.factors['view_duration'].current_value = 0.60
    
    def _calculate_base_success_rate(self) -> float:
        """Calculate base success rate from factors"""
        total_weight = sum(factor.weight for factor in self.factors.values())
        
        if total_weight == 0:
            return 0.5
        
        weighted_sum = sum(
            factor.weight * factor.current_value 
            for factor in self.factors.values()
        )
        
        base_rate = weighted_sum / total_weight
        
        # Apply non-linear scaling (better factors have higher impact)
        scaled_rate = 1 / (1 + math.exp(-10 * (base_rate - 0.5)))
        
        return scaled_rate
    
    def _calculate_historical_adjustment(self, historical_data: List[Dict]) -> float:
        """Calculate adjustment based on historical success rates"""
        if not historical_data:
            return 1.0
        
        success_rates = []
        for data in historical_data[-100:]:  # Last 100 entries
            if 'success_rate' in data:
                success_rates.append(data['success_rate'])
        
        if not success_rates:
            return 1.0
        
        avg_rate = statistics.mean(success_rates)
        std_dev = statistics.stdev(success_rates) if len(success_rates) > 1 else 0.1
        
        # Normalize to 0.5-1.5 range
        adjustment = 0.5 + (avg_rate / 2)
        
        # Reduce adjustment if high variability
        if std_dev > 0.2:
            adjustment *= 0.8
        
        return max(0.3, min(1.5, adjustment))
    
    def _calculate_time_adjustment(self) -> float:
        """Calculate time-based adjustment"""
        now = datetime.now()
        day_of_week = now.weekday()
        hour = now.hour
        
        # Weekend adjustment
        if day_of_week >= 5:  # Saturday or Sunday
            weekend_factor = 1.1
        else:
            weekend_factor = 1.0
        
        # Hour adjustment
        if 18 <= hour <= 22:  # Evening peak
            hour_factor = 1.2
        elif 12 <= hour <= 17:  # Afternoon
            hour_factor = 1.0
        elif 7 <= hour <= 11:  # Morning
            hour_factor = 0.9
        else:  # Night
            hour_factor = 0.8
        
        return weekend_factor * hour_factor
    
    def _get_method_adjustment(self, method: str) -> float:
        """Get adjustment factor for method"""
        adjustments = {
            'browser': 1.0,
            'api': 0.85,
            'cloud': 0.75,
            'hybrid': 1.15
        }
        return adjustments.get(method, 1.0)
    
    def _calculate_confidence(self, video_data: Dict) -> float:
        """Calculate prediction confidence"""
        confidence_factors = []
        
        # Data completeness
        required_fields = ['video_url', 'method', 'target_views']
        completeness = sum(1 for field in required_fields if field in video_data) / len(required_fields)
        confidence_factors.append(completeness * 0.3)
        
        # Historical data availability
        historical_count = len(self.historical_data)
        if historical_count >= 100:
            historical_confidence = 1.0
        elif historical_count >= 50:
            historical_confidence = 0.8
        elif historical_count >= 20:
            historical_confidence = 0.6
        elif historical_count >= 10:
            historical_confidence = 0.4
        else:
            historical_confidence = 0.2
        confidence_factors.append(historical_confidence * 0.4)
        
        # Factor variance (low variance = higher confidence)
        factor_values = [f.current_value for f in self.factors.values()]
        if len(factor_values) > 1:
            variance = statistics.variance(factor_values)
            variance_confidence = 1 / (1 + variance * 10)
        else:
            variance_confidence = 0.5
        confidence_factors.append(variance_confidence * 0.3)
        
        total_confidence = sum(confidence_factors)
        
        return max(0.1, min(0.99, total_confidence))
    
    def _calculate_factor_impacts(self) -> Dict[str, float]:
        """Calculate impact of each factor on success rate"""
        impacts = {}
        
        for name, factor in self.factors.items():
            # Calculate improvement potential
            improvement_potential = factor.optimal_value - factor.current_value
            
            # Calculate impact (weight * improvement_potential)
            impact = factor.weight * improvement_potential * 100
            
            # Normalize to percentage
            impacts[name] = max(0, min(100, impact))
        
        return impacts
    
    def _generate_recommendations(self, factor_impacts: Dict[str, float]) -> List[str]:
        """Generate recommendations based on factor impacts"""
        recommendations = []
        
        # Sort factors by impact (descending)
        sorted_factors = sorted(factor_impacts.items(), key=lambda x: x[1], reverse=True)
        
        for factor_name, impact in sorted_factors[:3]:  # Top 3 factors
            if impact > 10:  # Only recommend if significant impact
                factor = self.factors[factor_name]
                
                if factor_name == 'time_of_day':
                    recommendations.append(
                        f"🕐 Schedule views during peak hours (18:00-22:00) "
                        f"to improve {factor_name} by {impact:.1f}%"
                    )
                elif factor_name == 'method_quality':
                    recommendations.append(
                        f"⚡ Use 'hybrid' or 'browser' method instead of current "
                        f"to improve {factor_name} by {impact:.1f}%"
                    )
                elif factor_name == 'proxy_quality':
                    recommendations.append(
                        f"🌐 Upgrade to residential proxies "
                        f"to improve {factor_name} by {impact:.1f}%"
                    )
                elif factor_name == 'view_duration':
                    recommendations.append(
                        f"⏱️ Increase minimum view duration to 45+ seconds "
                        f"to improve {factor_name} by {impact:.1f}%"
                    )
        
        # Add general recommendations
        if len(recommendations) < 3:
            recommendations.append("📊 Use multiple methods simultaneously for better results")
            recommendations.append("🎯 Focus on organic-looking view patterns")
            recommendations.append("🔄 Rotate accounts regularly to avoid detection")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _estimate_views(self, success_rate: float, video_data: Dict) -> int:
        """Estimate number of views needed"""
        target_views = video_data.get('target_views', 100)
        
        # Adjust based on success rate
        if success_rate > 0.8:
            multiplier = 1.0
        elif success_rate > 0.6:
            multiplier = 1.1
        elif success_rate > 0.4:
            multiplier = 1.25
        else:
            multiplier = 1.5
        
        estimated = int(target_views * multiplier)
        
        # Add safety margin
        estimated = int(estimated * 1.1)
        
        return max(target_views, estimated)
    
    def _determine_risk_level(self, success_rate: float, confidence: float) -> str:
        """Determine risk level based on success rate and confidence"""
        if success_rate >= 0.8 and confidence >= 0.8:
            return "LOW"
        elif success_rate >= 0.6 and confidence >= 0.6:
            return "MEDIUM"
        elif success_rate >= 0.4:
            return "HIGH"
        else:
            return "VERY HIGH"
    
    async def update_with_results(self, actual_results: Dict):
        """Update calculator with actual results"""
        self.historical_data.append({
            'timestamp': datetime.now().isoformat(),
            'success_rate': actual_results.get('success_rate', 0),
            'method': actual_results.get('method', 'unknown'),
            'views_sent': actual_results.get('views_sent', 0),
            'successful_views': actual_results.get('successful_views', 0)
        })
        
        # Keep only last 1000 records
        if len(self.historical_data) > 1000:
            self.historical_data = self.historical_data[-1000:]
        
        # Update factor weights based on results
        self._adjust_factor_weights(actual_results)
    
    def _adjust_factor_weights(self, results: Dict):
        """Adjust factor weights based on actual results"""
        actual_success = results.get('success_rate', 0.5)
        predicted_success = self._calculate_base_success_rate()
        
        error = abs(actual_success - predicted_success)
        
        if error > 0.2:  # Large error
            # Increase weights of factors that were far from optimal
            for factor in self.factors.values():
                if factor.current_value < factor.optimal_value * 0.7:
                    factor.weight *= 1.1
        
        # Normalize weights
        total_weight = sum(factor.weight for factor in self.factors.values())
        if total_weight > 0:
            for factor in self.factors.values():
                factor.weight /= total_weight
    
    async def get_factor_analysis(self) -> Dict:
        """Get detailed factor analysis"""
        analysis = {
            'factors': {},
            'summary': {},
            'improvement_opportunities': []
        }
        
        for name, factor in self.factors.items():
            improvement = factor.optimal_value - factor.current_value
            improvement_percentage = (improvement / factor.optimal_value * 100) if factor.optimal_value > 0 else 0
            
            analysis['factors'][name] = {
                'current_value': factor.current_value,
                'optimal_value': factor.optimal_value,
                'weight': factor.weight,
                'improvement_needed': improvement,
                'improvement_percentage': improvement_percentage,
                'status': 'GOOD' if factor.current_value >= factor.optimal_value * 0.9 else
                         'OK' if factor.current_value >= factor.optimal_value * 0.7 else
                         'NEEDS_IMPROVEMENT'
            }
            
            if improvement_percentage > 20:
                analysis['improvement_opportunities'].append({
                    'factor': name,
                    'improvement_potential': improvement_percentage,
                    'impact': factor.weight * improvement * 100
                })
        
        # Calculate overall metrics
        current_score = sum(f.current_value * f.weight for f in self.factors.values())
        optimal_score = sum(f.optimal_value * f.weight for f in self.factors.values())
        efficiency = (current_score / optimal_score * 100) if optimal_score > 0 else 0
        
        analysis['summary'] = {
            'current_overall_score': current_score,
            'optimal_overall_score': optimal_score,
            'efficiency_percentage': efficiency,
            'total_factors': len(self.factors),
            'factors_needing_improvement': sum(1 for f in analysis['factors'].values() 
                                             if f['status'] != 'GOOD')
        }
        
        return analysis
    
    async def predict_batch_success(self, batch_data: List[Dict]) -> Dict:
        """Predict success for a batch of videos"""
        predictions = []
        total_predicted_views = 0
        total_estimated_views = 0
        
        for video_data in batch_data:
            try:
                prediction = await self.calculate_success_rate(video_data)
                
                predictions.append({
                    'video_url': video_data.get('video_url', 'Unknown'),
                    'predicted_success_rate': prediction.predicted_success_rate,
                    'confidence': prediction.confidence,
                    'estimated_views': prediction.estimated_views,
                    'risk_level': prediction.risk_level
                })
                
                total_predicted_views += video_data.get('target_views', 0)
                total_estimated_views += prediction.estimated_views
                
            except Exception as e:
                logger.error(f"Failed to predict for video: {e}")
                predictions.append({
                    'video_url': video_data.get('video_url', 'Unknown'),
                    'error': str(e)
                })
        
        # Calculate batch statistics
        if predictions:
            success_rates = [p.get('predicted_success_rate', 0) for p in predictions 
                           if 'predicted_success_rate' in p]
            confidences = [p.get('confidence', 0) for p in predictions 
                         if 'confidence' in p]
            
            avg_success = statistics.mean(success_rates) if success_rates else 0
            avg_confidence = statistics.mean(confidences) if confidences else 0
            
            risk_distribution = {}
            for pred in predictions:
                if 'risk_level' in pred:
                    risk = pred['risk_level']
                    risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        else:
            avg_success = 0
            avg_confidence = 0
            risk_distribution = {}
        
        return {
            'batch_predictions': predictions,
            'statistics': {
                'total_videos': len(batch_data),
                'successful_predictions': len([p for p in predictions if 'error' not in p]),
                'average_success_rate': avg_success,
                'average_confidence': avg_confidence,
                'total_predicted_views': total_predicted_views,
                'total_estimated_views': total_estimated_views,
                'efficiency_ratio': total_predicted_views / total_estimated_views if total_estimated_views > 0 else 0,
                'risk_distribution': risk_distribution
            },
            'batch_recommendations': self._generate_batch_recommendations(predictions)
        }
    
    def _generate_batch_recommendations(self, predictions: List[Dict]) -> List[str]:
        """Generate batch-level recommendations"""
        recommendations = []
        
        if not predictions:
            return ["No data available for recommendations"]
        
        # Check risk levels
        high_risk = sum(1 for p in predictions 
                       if p.get('risk_level') in ['HIGH', 'VERY HIGH'])
        
        if high_risk > len(predictions) * 0.3:  # More than 30% high risk
            recommendations.append(
                f"⚠️ {high_risk}/{len(predictions)} videos have high risk. "
                "Consider improving proxy quality and method selection."
            )
        
        # Check confidence levels
        low_confidence = sum(1 for p in predictions 
                           if p.get('confidence', 0) < 0.6)
        
        if low_confidence > 0:
            recommendations.append(
                f"📉 {low_confidence} predictions have low confidence. "
                "Gather more historical data for better accuracy."
            )
        
        # General recommendations
        success_rates = [p.get('predicted_success_rate', 0) for p in predictions 
                       if 'predicted_success_rate' in p]
        
        if success_rates:
            avg_success = statistics.mean(success_rates)
            
            if avg_success < 0.6:
                recommendations.append(
                    f"🎯 Average success rate ({avg_success:.1%}) is low. "
                    "Focus on improving time scheduling and method selection."
                )
            elif avg_success > 0.8:
                recommendations.append(
                    f"✅ Excellent average success rate ({avg_success:.1%})! "
                    "Current strategy is working well."
                )
        
        # Add optimization tip
        recommendations.append(
            "💡 Consider using the 'hybrid' method for high-value videos "
            "and 'cloud' method for bulk operations"
        )
        
        return recommendations[:5]