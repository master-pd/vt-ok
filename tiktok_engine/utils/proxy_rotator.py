"""
Proxy Rotator - Intelligent proxy management
"""

import asyncio
import aiohttp
import random
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

class ProxyRotator:
    """Intelligent proxy rotation system"""
    
    def __init__(self):
        self.proxies = []
        self.proxy_stats = {}
        self.blacklist = set()
        self.provider_stats = {}
        self.rotation_strategy = 'smart'
        
        # Proxy providers
        self.providers = {
            'free': [
                'https://free-proxy-list.net',
                'https://proxy-scrape.com/free-proxy-list',
                'https://geonode.com/free-proxy-list'
            ],
            'paid': [],  # Would be configured with API keys
            'residential': [],  # Residential proxy services
            'mobile': []  # Mobile proxy services
        }
    
    async def load_proxies(self, sources: List[str] = None):
        """Load proxies from various sources"""
        print("📥 Loading proxies...")
        
        if sources is None:
            sources = self.providers['free']
        
        all_proxies = []
        
        for source in sources:
            try:
                proxies = await self.fetch_proxies_from_source(source)
                all_proxies.extend(proxies)
                
                print(f"✅ Loaded {len(proxies)} proxies from {source}")
                
            except Exception as e:
                print(f"❌ Failed to load proxies from {source}: {e}")
        
        # Process and validate proxies
        validated_proxies = await self.validate_proxies(all_proxies)
        
        self.proxies = validated_proxies
        
        # Initialize stats
        for proxy in self.proxies:
            self.proxy_stats[proxy] = {
                'success_count': 0,
                'fail_count': 0,
                'total_requests': 0,
                'avg_response_time': 0,
                'last_used': None,
                'last_success': None,
                'last_failure': None,
                'consecutive_failures': 0,
                'country': 'unknown',
                'type': 'unknown',
                'speed_score': 0.5,
                'reliability_score': 0.5
            }
        
        print(f"🎯 Loaded {len(self.proxies)} validated proxies")
        return len(self.proxies)
    
    async def fetch_proxies_from_source(self, source: str) -> List[str]:
        """Fetch proxies from a source"""
        async with aiohttp.ClientSession() as session:
            async with session.get(source, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.parse_proxy_html(html)
                else:
                    return []
    
    def parse_proxy_html(self, html: str) -> List[str]:
        """Parse proxy HTML (simplified)"""
        # In production, use proper parsing for each source
        proxies = []
        
        # Simple regex for IP:PORT pattern
        import re
        ip_port_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}'
        
        matches = re.findall(ip_port_pattern, html)
        
        # Format as http://ip:port
        for match in matches:
            proxies.append(f"http://{match}")
        
        # Add some socks proxies
        socks_proxies = [
            'socks5://proxy1:1080',
            'socks5://proxy2:1080',
            'socks5://proxy3:1080'
        ]
        
        proxies.extend(socks_proxies)
        
        return list(set(proxies))  # Remove duplicates
    
    async def validate_proxies(self, proxies: List[str]) -> List[str]:
        """Validate proxies by testing them"""
        print("🔍 Validating proxies...")
        
        valid_proxies = []
        test_url = "http://httpbin.org/ip"  # Test endpoint
        
        # Test in batches
        batch_size = 10
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i+batch_size]
            
            tasks = [self.test_proxy(proxy, test_url) for proxy in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for proxy, result in zip(batch, results):
                if isinstance(result, dict) and result.get('success'):
                    valid_proxies.append(proxy)
            
            # Progress update
            print(f"  Validated {min(i+batch_size, len(proxies))}/{len(proxies)}")
        
        return valid_proxies
    
    async def test_proxy(self, proxy: str, test_url: str) -> Dict:
        """Test a single proxy"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            ) as session:
                
                start_time = time.time()
                
                async with session.get(
                    test_url,
                    proxy=proxy,
                    headers={'User-Agent': 'Proxy-Tester/1.0'}
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract proxy info
                        country = self.detect_country(proxy)
                        proxy_type = self.detect_proxy_type(proxy)
                        
                        return {
                            'success': True,
                            'proxy': proxy,
                            'response_time': response_time,
                            'country': country,
                            'type': proxy_type,
                            'ip': data.get('origin', 'unknown')
                        }
        
        except Exception as e:
            return {
                'success': False,
                'proxy': proxy,
                'error': str(e)
            }
    
    def detect_country(self, proxy: str) -> str:
        """Detect proxy country (simplified)"""
        # In production, use IP geolocation service
        country_codes = ['US', 'UK', 'DE', 'FR', 'CA', 'AU', 'JP', 'BR', 'IN', 'RU']
        return random.choice(country_codes)
    
    def detect_proxy_type(self, proxy: str) -> str:
        """Detect proxy type"""
        if 'socks5' in proxy:
            return 'socks5'
        elif 'socks4' in proxy:
            return 'socks4'
        elif 'https' in proxy:
            return 'https'
        else:
            return 'http'
    
    async def get_proxy(self, requirements: Dict = None) -> Optional[str]:
        """Get a proxy based on requirements"""
        if not self.proxies:
            await self.load_proxies()
        
        if not self.proxies:
            return None
        
        if requirements is None:
            requirements = {}
        
        # Filter proxies based on requirements
        suitable_proxies = self.filter_proxies(requirements)
        
        if not suitable_proxies:
            # No suitable proxies, use any
            suitable_proxies = self.proxies
        
        # Select proxy based on rotation strategy
        if self.rotation_strategy == 'random':
            proxy = random.choice(suitable_proxies)
        elif self.rotation_strategy == 'round_robin':
            proxy = self.round_robin_selection(suitable_proxies)
        elif self.rotation_strategy == 'performance':
            proxy = self.performance_based_selection(suitable_proxies)
        else:  # smart
            proxy = self.smart_selection(suitable_proxies, requirements)
        
        # Update stats
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['last_used'] = datetime.now()
            self.proxy_stats[proxy]['total_requests'] += 1
        
        return proxy
    
    def filter_proxies(self, requirements: Dict) -> List[str]:
        """Filter proxies based on requirements"""
        filtered = []
        
        for proxy in self.proxies:
            stats = self.proxy_stats.get(proxy, {})
            
            # Check blacklist
            if proxy in self.blacklist:
                continue
            
            # Check consecutive failures
            if stats.get('consecutive_failures', 0) > 3:
                continue
            
            # Check country requirement
            req_country = requirements.get('country')
            if req_country and stats.get('country') != req_country:
                continue
            
            # Check type requirement
            req_type = requirements.get('type')
            if req_type and stats.get('type') != req_type:
                continue
            
            # Check minimum reliability
            min_reliability = requirements.get('min_reliability', 0.3)
            if stats.get('reliability_score', 0) < min_reliability:
                continue
            
            # Check minimum speed
            min_speed = requirements.get('min_speed', 0.3)
            if stats.get('speed_score', 0) < min_speed:
                continue
            
            filtered.append(proxy)
        
        return filtered
    
    def round_robin_selection(self, proxies: List[str]) -> str:
        """Round-robin proxy selection"""
        if not hasattr(self, '_rr_index'):
            self._rr_index = 0
        
        proxy = proxies[self._rr_index % len(proxies)]
        self._rr_index = (self._rr_index + 1) % len(proxies)
        
        return proxy
    
    def performance_based_selection(self, proxies: List[str]) -> str:
        """Performance-based proxy selection"""
        scored_proxies = []
        
        for proxy in proxies:
            stats = self.proxy_stats.get(proxy, {})
            
            # Calculate score
            reliability = stats.get('reliability_score', 0.5)
            speed = stats.get('speed_score', 0.5)
            freshness = self.calculate_freshness_score(stats.get('last_success'))
            
            score = (reliability * 0.5 + speed * 0.3 + freshness * 0.2)
            scored_proxies.append((proxy, score))
        
        # Sort by score (descending)
        scored_proxies.sort(key=lambda x: x[1], reverse=True)
        
        # Weighted random selection from top 5
        top_n = min(5, len(scored_proxies))
        top_proxies = scored_proxies[:top_n]
        
        # Use scores as weights
        proxies, weights = zip(*top_proxies)
        
        return random.choices(proxies, weights=weights, k=1)[0]
    
    def smart_selection(self, proxies: List[str], requirements: Dict) -> str:
        """Smart proxy selection"""
        # Check if we need high reliability
        if requirements.get('high_reliability', False):
            return self.select_most_reliable(proxies)
        
        # Check if we need high speed
        if requirements.get('high_speed', False):
            return self.select_fastest(proxies)
        
        # Check if we need stealth (less used proxies)
        if requirements.get('stealth', False):
            return self.select_stealthy(proxies)
        
        # Default: balanced selection
        return self.select_balanced(proxies)
    
    def select_most_reliable(self, proxies: List[str]) -> str:
        """Select most reliable proxy"""
        most_reliable = None
        best_score = -1
        
        for proxy in proxies:
            stats = self.proxy_stats.get(proxy, {})
            reliability = stats.get('reliability_score', 0)
            
            if reliability > best_score:
                best_score = reliability
                most_reliable = proxy
        
        return most_reliable or random.choice(proxies)
    
    def select_fastest(self, proxies: List[str]) -> str:
        """Select fastest proxy"""
        fastest = None
        best_speed = -1
        
        for proxy in proxies:
            stats = self.proxy_stats.get(proxy, {})
            speed = stats.get('speed_score', 0)
            
            if speed > best_speed:
                best_speed = speed
                fastest = proxy
        
        return fastest or random.choice(proxies)
    
    def select_stealthy(self, proxies: List[str]) -> str:
        """Select less-used proxy for stealth"""
        least_used = None
        min_uses = float('inf')
        
        for proxy in proxies:
            stats = self.proxy_stats.get(proxy, {})
            uses = stats.get('total_requests', 0)
            
            if uses < min_uses:
                min_uses = uses
                least_used = proxy
        
        return least_used or random.choice(proxies)
    
    def select_balanced(self, proxies: List[str]) -> str:
        """Select balanced proxy (reliability + speed)"""
        best_balanced = None
        best_score = -1
        
        for proxy in proxies:
            stats = self.proxy_stats.get(proxy, {})
            
            reliability = stats.get('reliability_score', 0.5)
            speed = stats.get('speed_score', 0.5)
            freshness = self.calculate_freshness_score(stats.get('last_success'))
            
            # Balanced score
            score = (reliability * 0.4 + speed * 0.4 + freshness * 0.2)
            
            if score > best_score:
                best_score = score
                best_balanced = proxy
        
        return best_balanced or random.choice(proxies)
    
    def calculate_freshness_score(self, last_success: Optional[datetime]) -> float:
        """Calculate freshness score (recent success = higher score)"""
        if last_success is None:
            return 0.1
        
        hours_since = (datetime.now() - last_success).total_seconds() / 3600
        
        # Score decreases over time
        if hours_since < 1:
            return 1.0
        elif hours_since < 6:
            return 0.7
        elif hours_since < 24:
            return 0.4
        else:
            return 0.1
    
    async def report_success(self, proxy: str, response_time: float):
        """Report successful proxy usage"""
        if proxy in self.proxy_stats:
            stats = self.proxy_stats[proxy]
            
            stats['success_count'] += 1
            stats['last_success'] = datetime.now()
            stats['consecutive_failures'] = 0
            
            # Update average response time
            old_avg = stats['avg_response_time']
            total_requests = stats['total_requests']
            
            if total_requests == 1:
                stats['avg_response_time'] = response_time
            else:
                stats['avg_response_time'] = (
                    (old_avg * (total_requests - 1) + response_time) / total_requests
                )
            
            # Update scores
            stats['reliability_score'] = self.calculate_reliability_score(stats)
            stats['speed_score'] = self.calculate_speed_score(stats)
            
            # Remove from blacklist if present
            if proxy in self.blacklist:
                self.blacklist.remove(proxy)
    
    async def report_failure(self, proxy: str, error: str = None):
        """Report failed proxy usage"""
        if proxy in self.proxy_stats:
            stats = self.proxy_stats[proxy]
            
            stats['fail_count'] += 1
            stats['last_failure'] = datetime.now()
            stats['consecutive_failures'] += 1
            
            # Update reliability score
            stats['reliability_score'] = self.calculate_reliability_score(stats)
            
            # Blacklist if too many consecutive failures
            if stats['consecutive_failures'] >= 5:
                self.blacklist.add(proxy)
                print(f"🚫 Blacklisted proxy: {proxy}")
    
    def calculate_reliability_score(self, stats: Dict) -> float:
        """Calculate reliability score (0-1)"""
        success = stats.get('success_count', 0)
        total = stats.get('total_requests', 1)
        
        if total == 0:
            return 0.5
        
        base_score = success / total
        
        # Penalize recent failures
        consecutive_failures = stats.get('consecutive_failures', 0)
        failure_penalty = consecutive_failures * 0.1
        
        # Boost for high volume
        volume_boost = min(0.2, total / 1000)
        
        score = base_score - failure_penalty + volume_boost
        
        return max(0.1, min(1.0, score))
    
    def calculate_speed_score(self, stats: Dict) -> float:
        """Calculate speed score (0-1)"""
        avg_time = stats.get('avg_response_time', 5.0)
        
        # Convert to score (lower time = higher score)
        if avg_time < 1:
            return 1.0
        elif avg_time < 3:
            return 0.8
        elif avg_time < 5:
            return 0.6
        elif avg_time < 10:
            return 0.4
        else:
            return 0.2
    
    async def get_proxy_stats(self) -> Dict:
        """Get proxy statistics"""
        total_proxies = len(self.proxies)
        active_proxies = total_proxies - len(self.blacklist)
        
        # Calculate overall metrics
        reliability_scores = [
            s.get('reliability_score', 0) 
            for s in self.proxy_stats.values()
        ]
        
        speed_scores = [
            s.get('speed_score', 0) 
            for s in self.proxy_stats.values()
        ]
        
        avg_reliability = sum(reliability_scores) / len(reliability_scores) if reliability_scores else 0
        avg_speed = sum(speed_scores) / len(speed_scores) if speed_scores else 0
        
        # Count by type
        by_type = {}
        by_country = {}
        
        for proxy, stats in self.proxy_stats.items():
            proxy_type = stats.get('type', 'unknown')
            country = stats.get('country', 'unknown')
            
            by_type[proxy_type] = by_type.get(proxy_type, 0) + 1
            by_country[country] = by_country.get(country, 0) + 1
        
        # Top performers
        top_proxies = sorted(
            self.proxy_stats.items(),
            key=lambda x: x[1].get('reliability_score', 0),
            reverse=True
        )[:5]
        
        top_proxies_formatted = []
        for proxy, stats in top_proxies:
            top_proxies_formatted.append({
                'proxy': proxy[:30] + '...' if len(proxy) > 30 else proxy,
                'reliability': stats.get('reliability_score', 0),
                'speed': stats.get('speed_score', 0),
                'requests': stats.get('total_requests', 0),
                'success_rate': (stats.get('success_count', 0) / stats.get('total_requests', 1)) * 100
            })
        
        return {
            'total_proxies': total_proxies,
            'active_proxies': active_proxies,
            'blacklisted': len(self.blacklist),
            'average_reliability': avg_reliability,
            'average_speed': avg_speed,
            'distribution_by_type': by_type,
            'distribution_by_country': by_country,
            'top_performers': top_proxies_formatted,
            'rotation_strategy': self.rotation_strategy
        }
    
    async def cleanup_old_proxies(self, max_age_hours: int = 24):
        """Cleanup old/unreliable proxies"""
        removed = 0
        
        for proxy in list(self.proxies):
            stats = self.proxy_stats.get(proxy, {})
            
            # Check last success
            last_success = stats.get('last_success')
            if last_success:
                hours_since = (datetime.now() - last_success).total_seconds() / 3600
                
                if hours_since > max_age_hours:
                    # Remove old proxy
                    self.proxies.remove(proxy)
                    if proxy in self.proxy_stats:
                        del self.proxy_stats[proxy]
                    removed += 1
                    continue
            
            # Check reliability
            reliability = stats.get('reliability_score', 0.5)
            if reliability < 0.2:
                # Remove unreliable proxy
                self.proxies.remove(proxy)
                if proxy in self.proxy_stats:
                    del self.proxy_stats[proxy]
                removed += 1
        
        print(f"🧹 Cleaned up {removed} old/unreliable proxies")
        return removed
    
    async def refresh_proxies(self):
        """Refresh proxy list"""
        print("🔄 Refreshing proxy list...")
        
        # Cleanup old proxies
        await self.cleanup_old_proxies()
        
        # Load new proxies
        await self.load_proxies()
        
        print("✅ Proxy refresh complete")