"""
Smart Scheduler for Optimal View Distribution
"""

import asyncio
import logging
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class UrgencyLevel(Enum):
    ULTRA = "ultra"      # Immediate, within 1 hour
    HIGH = "high"        # Within 3 hours
    NORMAL = "normal"    # Within 6 hours
    LOW = "low"         # Within 24 hours
    GRADUAL = "gradual"  # Over multiple days

@dataclass
class TimeSlot:
    hour: int
    day_of_week: int
    success_rate: float
    recommended_intensity: float  # 0.0 to 1.0
    is_peak: bool = False
    description: str = ""

class SmartScheduler:
    def __init__(self):
        self.time_slots: Dict[Tuple[int, int], TimeSlot] = {}
        self.user_timezone = "UTC"
        self._init_time_slots()
        self.historical_data = {}
        self.peak_hours = {
            "weekday": [18, 19, 20, 21, 22],  # 6PM-10PM
            "weekend": [12, 13, 14, 15, 16, 19, 20, 21, 22, 23]  # More spread out
        }
        
    def _init_time_slots(self):
        """Initialize time slots with AI-optimized values"""
        for day in range(7):  # 0=Monday, 6=Sunday
            is_weekend = day >= 5
            peak_hours = self.peak_hours["weekend" if is_weekend else "weekday"]
            
            for hour in range(24):
                is_peak = hour in peak_hours
                
                # Base success rate
                if is_peak:
                    base_rate = random.uniform(0.80, 0.95)
                    intensity = random.uniform(0.7, 1.0)
                    description = "PEAK - High engagement"
                elif hour >= 0 and hour <= 6:  # Night
                    base_rate = random.uniform(0.65, 0.80)
                    intensity = random.uniform(0.3, 0.6)
                    description = "NIGHT - Low competition"
                elif hour >= 7 and hour <= 11:  # Morning
                    base_rate = random.uniform(0.70, 0.85)
                    intensity = random.uniform(0.4, 0.7)
                    description = "MORNING - Steady growth"
                else:  # Afternoon
                    base_rate = random.uniform(0.75, 0.90)
                    intensity = random.uniform(0.5, 0.8)
                    description = "AFTERNOON - Active users"
                
                # Weekend adjustment
                if is_weekend:
                    base_rate *= 1.1  # 10% higher on weekends
                    intensity *= 1.2
                    description += " (Weekend)"
                
                self.time_slots[(day, hour)] = TimeSlot(
                    hour=hour,
                    day_of_week=day,
                    success_rate=min(base_rate, 0.99),
                    recommended_intensity=min(intensity, 1.0),
                    is_peak=is_peak,
                    description=description
                )
        
        logger.info(f"Initialized {len(self.time_slots)} time slots")
    
    async def generate_optimal_schedule(self, video_url: str, total_views: int,
                                      urgency: UrgencyLevel = UrgencyLevel.NORMAL,
                                      budget: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate AI-optimized schedule for view distribution
        
        Args:
            video_url: Target TikTok video URL
            total_views: Total views to distribute
            urgency: Urgency level for distribution
            budget: Optional budget for premium methods
            
        Returns:
            Complete schedule with optimization details
        """
        logger.info(f"Generating optimal schedule for {total_views} views (urgency: {urgency.value})")
        
        # Calculate distribution parameters based on urgency
        distribution_params = self._get_distribution_params(urgency)
        
        # Get current datetime
        now = datetime.now()
        current_day = now.weekday()
        current_hour = now.hour
        
        # Generate schedule slots
        schedule = []
        views_remaining = total_views
        slot_number = 0
        
        # Calculate total time slots
        total_slots = distribution_params["total_hours"]
        
        for hour_offset in range(total_slots):
            slot_day = (current_day + (hour_offset // 24)) % 7
            slot_hour = (current_hour + hour_offset) % 24
            
            time_slot = self.time_slots.get((slot_day, slot_hour))
            if not time_slot:
                continue
            
            # Calculate views for this slot
            slot_weight = (
                time_slot.success_rate * 
                time_slot.recommended_intensity *
                (1.5 if time_slot.is_peak else 0.7) *
                distribution_params["concentration_factor"]
            )
            
            # Apply urgency multiplier
            if urgency == UrgencyLevel.ULTRA:
                slot_weight *= 2.0
            elif urgency == UrgencyLevel.HIGH:
                slot_weight *= 1.5
            
            # Calculate views for this slot
            slot_views = int(total_views * (slot_weight / self._get_total_weight(total_slots, distribution_params)))
            
            # Ensure minimum and maximum per slot
            min_views = distribution_params.get("min_views_per_slot", 5)
            max_views = distribution_params.get("max_views_per_slot", 
                                              100 if urgency == UrgencyLevel.ULTRA else 50)
            
            slot_views = max(min_views, min(slot_views, max_views, views_remaining))
            
            if slot_views > 0:
                slot_time = now + timedelta(hours=hour_offset)
                
                # Select optimal method for this slot
                recommended_method = self._select_optimal_method(
                    time_slot=time_slot,
                    views=slot_views,
                    budget=budget
                )
                
                schedule.append({
                    'slot_id': f"slot_{slot_number:03d}",
                    'scheduled_time': slot_time.isoformat(),
                    'day_of_week': slot_day,
                    'hour': slot_hour,
                    'views': slot_views,
                    'success_rate': time_slot.success_rate,
                    'intensity': time_slot.recommended_intensity,
                    'is_peak': time_slot.is_peak,
                    'description': time_slot.description,
                    'recommended_method': recommended_method,
                    'estimated_completion_minutes': random.randint(5, 30)
                })
                
                views_remaining -= slot_views
                slot_number += 1
            
            if views_remaining <= 0:
                break
        
        # Distribute any remaining views
        if views_remaining > 0:
            self._distribute_remaining_views(schedule, views_remaining)
        
        # Calculate statistics
        total_scheduled_views = sum(entry['views'] for entry in schedule)
        avg_success_rate = sum(
            entry['success_rate'] * entry['views'] for entry in schedule
        ) / total_scheduled_views if total_scheduled_views > 0 else 0
        
        # Generate optimization insights
        insights = self._generate_optimization_insights(schedule, urgency)
        
        result = {
            'video_url': video_url,
            'total_views': total_views,
            'scheduled_views': total_scheduled_views,
            'urgency_level': urgency.value,
            'estimated_success_rate': avg_success_rate,
            'estimated_completion_time': schedule[-1]['scheduled_time'] if schedule else None,
            'total_slots': len(schedule),
            'peak_slots': sum(1 for s in schedule if s['is_peak']),
            'schedule': schedule,
            'optimization_insights': insights,
            'recommendations': [
                f"Start: {schedule[0]['scheduled_time'] if schedule else 'N/A'}",
                f"Peak hours utilization: {sum(1 for s in schedule if s['is_peak'])} slots",
                f"Estimated success: {avg_success_rate:.1%}",
                f"Optimal methods: {', '.join(set(s['recommended_method'] for s in schedule))}"
            ],
            'generated_at': now.isoformat()
        }
        
        logger.info(f"Generated schedule with {len(schedule)} slots, {total_scheduled_views} views")
        return result
    
    def _get_distribution_params(self, urgency: UrgencyLevel) -> Dict:
        """Get distribution parameters based on urgency"""
        params = {
            UrgencyLevel.ULTRA: {
                "total_hours": 2,
                "concentration_factor": 0.9,
                "min_views_per_slot": 20,
                "max_views_per_slot": 100
            },
            UrgencyLevel.HIGH: {
                "total_hours": 6,
                "concentration_factor": 0.7,
                "min_views_per_slot": 10,
                "max_views_per_slot": 50
            },
            UrgencyLevel.NORMAL: {
                "total_hours": 12,
                "concentration_factor": 0.5,
                "min_views_per_slot": 5,
                "max_views_per_slot": 30
            },
            UrgencyLevel.LOW: {
                "total_hours": 24,
                "concentration_factor": 0.3,
                "min_views_per_slot": 3,
                "max_views_per_slot": 20
            },
            UrgencyLevel.GRADUAL: {
                "total_hours": 72,
                "concentration_factor": 0.1,
                "min_views_per_slot": 1,
                "max_views_per_slot": 10
            }
        }
        return params.get(urgency, params[UrgencyLevel.NORMAL])
    
    def _get_total_weight(self, total_slots: int, params: Dict) -> float:
        """Calculate total weight for all slots"""
        total_weight = 0.0
        now = datetime.now()
        
        for hour_offset in range(total_slots):
            slot_day = (now.weekday() + (hour_offset // 24)) % 7
            slot_hour = (now.hour + hour_offset) % 24
            
            time_slot = self.time_slots.get((slot_day, slot_hour))
            if time_slot:
                slot_weight = (
                    time_slot.success_rate * 
                    time_slot.recommended_intensity *
                    (1.5 if time_slot.is_peak else 0.7) *
                    params["concentration_factor"]
                )
                total_weight += slot_weight
        
        return total_weight if total_weight > 0 else 1.0
    
    def _select_optimal_method(self, time_slot: TimeSlot, views: int, 
                             budget: Optional[float]) -> str:
        """Select optimal method for time slot"""
        if budget and budget > 100:  # High budget
            if time_slot.is_peak:
                return "hybrid"  # Best quality during peak
            else:
                return random.choice(["browser", "hybrid"])
        elif views > 50:  # Large batch
            return "cloud"  # High capacity
        elif time_slot.success_rate > 0.85:  # High success slot
            return "browser"  # Reliable method
        else:
            return random.choice(["api", "browser"])
    
    def _distribute_remaining_views(self, schedule: List[Dict], remaining_views: int):
        """Distribute remaining views across schedule"""
        if not schedule:
            return
        
        # Sort by success rate (highest first)
        schedule.sort(key=lambda x: x['success_rate'], reverse=True)
        
        for entry in schedule:
            if remaining_views <= 0:
                break
            
            additional = min(remaining_views, 
                           int(entry['views'] * 0.3),  # Max 30% increase
                           20)  # Absolute max
            
            entry['views'] += additional
            remaining_views -= additional
        
        # If still remaining, add to first entry
        if remaining_views > 0 and schedule:
            schedule[0]['views'] += remaining_views
    
    def _generate_optimization_insights(self, schedule: List[Dict], 
                                      urgency: UrgencyLevel) -> List[str]:
        """Generate AI optimization insights"""
        insights = []
        
        # Calculate metrics
        peak_views = sum(s['views'] for s in schedule if s['is_peak'])
        total_views = sum(s['views'] for s in schedule)
        peak_percentage = (peak_views / total_views * 100) if total_views > 0 else 0
        
        # Generate insights
        insights.append(f"Peak hour utilization: {peak_percentage:.1f}% of views during peak hours")
        
        if urgency == UrgencyLevel.ULTRA:
            insights.append("⚡ ULTRA urgency: Maximum concentration for immediate impact")
            insights.append("Recommendation: Use premium methods during peak slots")
        elif urgency == UrgencyLevel.HIGH:
            insights.append("🔥 HIGH urgency: Aggressive distribution within 6 hours")
            insights.append("Recommendation: Focus on browser and hybrid methods")
        elif urgency == UrgencyLevel.NORMAL:
            insights.append("✅ NORMAL urgency: Balanced distribution for organic growth")
            insights.append("Recommendation: Mix of methods for natural appearance")
        elif urgency == UrgencyLevel.GRADUAL:
            insights.append("🐢 GRADUAL urgency: Slow, steady growth over 3 days")
            insights.append("Recommendation: Focus on API and cloud methods for consistency")
        
        # Method distribution insight
        methods = {}
        for slot in schedule:
            method = slot['recommended_method']
            methods[method] = methods.get(method, 0) + slot['views']
        
        if methods:
            top_method = max(methods.items(), key=lambda x: x[1])
            insights.append(f"Primary method: {top_method[0]} ({top_method[1]} views)")
        
        return insights
    
    def update_from_results(self, results: List[Dict]):
        """Update scheduler based on actual results"""
        for result in results:
            if 'success_rate' in result and 'hour' in result:
                hour = result['hour']
                day = result.get('day_of_week', datetime.now().weekday())
                success_rate = result['success_rate']
                
                key = (day, hour)
                if key in self.time_slots:
                    # Weighted update
                    old_rate = self.time_slots[key].success_rate
                    new_rate = 0.8 * old_rate + 0.2 * success_rate
                    self.time_slots[key].success_rate = min(new_rate, 0.99)
                    
                    # Adjust intensity
                    if success_rate > 0.8:
                        self.time_slots[key].recommended_intensity = min(
                            self.time_slots[key].recommended_intensity * 1.1, 1.0
                        )
    
    def get_time_slot_analysis(self, day_of_week: Optional[int] = None) -> List[Dict]:
        """Get analysis of time slots"""
        analysis = []
        
        for (day, hour), slot in self.time_slots.items():
            if day_of_week is not None and day != day_of_week:
                continue
            
            analysis.append({
                'day_of_week': day,
                'hour': hour,
                'success_rate': slot.success_rate,
                'intensity': slot.recommended_intensity,
                'is_peak': slot.is_peak,
                'description': slot.description,
                'recommended_for': self._get_recommendation(slot)
            })
        
        return sorted(analysis, key=lambda x: (x['day_of_week'], x['hour']))
    
    def _get_recommendation(self, slot: TimeSlot) -> str:
        """Get recommendation for time slot"""
        if slot.is_peak:
            return "Premium campaigns, high-value content"
        elif slot.success_rate > 0.85:
            return "High-impact content, important videos"
        elif slot.recommended_intensity > 0.7:
            return "Regular campaigns, steady growth"
        else:
            return "Background growth, testing content"
    
    def get_optimal_start_time(self, target_views: int, 
                             urgency: UrgencyLevel = UrgencyLevel.NORMAL) -> datetime:
        """Calculate optimal start time"""
        now = datetime.now()
        
        if urgency in [UrgencyLevel.ULTRA, UrgencyLevel.HIGH]:
            return now  # Start immediately
        
        # Find next peak hour
        for hour_offset in range(1, 49):  # Check next 48 hours
            check_time = now + timedelta(hours=hour_offset)
            day = check_time.weekday()
            hour = check_time.hour
            
            slot = self.time_slots.get((day, hour))
            if slot and slot.is_peak:
                # Set to exact hour start
                return check_time.replace(minute=0, second=0, microsecond=0)
        
        # Default: start at next 18:00 (6 PM)
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)