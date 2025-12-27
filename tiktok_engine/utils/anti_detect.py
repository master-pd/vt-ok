"""
Advanced Anti-Detection System for TikTok Automation
"""
import random
import string
from typing import Dict, List, Optional, Tuple
import platform
import hashlib
import json
from datetime import datetime
import uuid
import socket
import struct

class AntiDetectSystem:
    def __init__(self):
        self.fingerprints = {}
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load anti-detection configuration"""
        return {
            'browser_profiles': self._generate_browser_profiles(),
            'device_profiles': self._generate_device_profiles(),
            'network_profiles': self._generate_network_profiles(),
            'behavior_profiles': self._generate_behavior_profiles()
        }
    
    def _generate_browser_profiles(self) -> List[Dict]:
        """Generate browser fingerprint profiles"""
        profiles = []
        
        # Chrome profiles
        chrome_versions = [
            '120.0.0.0', '119.0.0.0', '118.0.0.0', 
            '117.0.0.0', '116.0.0.0', '115.0.0.0'
        ]
        
        for i in range(10):
            profile = {
                'user_agent': self._generate_chrome_ua(random.choice(chrome_versions)),
                'screen_resolution': random.choice(['1920x1080', '1366x768', '1536x864', '1440x900']),
                'timezone': random.choice(['America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney']),
                'language': random.choice(['en-US', 'en-GB', 'fr-FR', 'de-DE', 'ja-JP']),
                'platform': random.choice(['Win32', 'MacIntel', 'Linux x86_64']),
                'hardware_concurrency': random.choice([4, 6, 8, 12]),
                'device_memory': random.choice([4, 8, 16]),
                'max_touch_points': 0,
                'webgl_vendor': 'Google Inc.',
                'webgl_renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)',
                'canvas_fingerprint': self._generate_canvas_fp(),
                'webgl_fingerprint': self._generate_webgl_fp(),
                'fonts': self._generate_font_list(),
                'plugins': self._generate_plugin_list(),
                'mime_types': self._generate_mime_types()
            }
            profiles.append(profile)
        
        return profiles
    
    def _generate_chrome_ua(self, version: str) -> str:
        """Generate Chrome user agent"""
        os_choices = [
            f"Windows NT 10.0; Win64; x64",
            f"Macintosh; Intel Mac OS X 10_15_7",
            f"X11; Linux x86_64"
        ]
        
        os_string = random.choice(os_choices)
        return f"Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
    
    def _generate_canvas_fp(self) -> str:
        """Generate canvas fingerprint"""
        # In real implementation, this would generate actual canvas image hash
        return hashlib.md5(str(random.random()).encode()).hexdigest()
    
    def _generate_webgl_fp(self) -> str:
        """Generate WebGL fingerprint"""
        vendors = ['Google Inc.', 'Intel Inc.', 'NVIDIA Corporation', 'AMD']
        renderers = [
            'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'WebKit WebGL'
        ]
        
        return f"{random.choice(vendors)}|{random.choice(renderers)}"
    
    def _generate_font_list(self) -> List[str]:
        """Generate font list"""
        base_fonts = [
            'Arial', 'Arial Black', 'Times New Roman', 
            'Courier New', 'Verdana', 'Georgia'
        ]
        
        extra_fonts = random.sample([
            'Tahoma', 'Trebuchet MS', 'Impact', 'Comic Sans MS',
            'Lucida Console', 'Palatino Linotype', 'Garamond'
        ], 3)
        
        return base_fonts + extra_fonts
    
    def _generate_plugin_list(self) -> List[str]:
        """Generate plugin list"""
        plugins = [
            'Chrome PDF Plugin',
            'Chrome PDF Viewer',
            'Native Client'
        ]
        
        if random.random() > 0.5:
            plugins.append('Widevine Content Decryption Module')
        
        return plugins
    
    def _generate_mime_types(self) -> List[Dict]:
        """Generate MIME types"""
        return [
            {'type': 'application/pdf', 'description': 'Portable Document Format'},
            {'type': 'text/pdf', 'description': 'Portable Document Format'}
        ]
    
    def _generate_device_profiles(self) -> List[Dict]:
        """Generate device profiles"""
        profiles = []
        
        mobile_devices = [
            {
                'type': 'mobile',
                'brand': 'Apple',
                'model': 'iPhone',
                'versions': ['15', '14', '13', '12'],
                'resolutions': ['1170x2532', '1284x2778', '1170x2532'],
                'dpr': [3, 2]
            },
            {
                'type': 'mobile',
                'brand': 'Samsung',
                'model': 'Galaxy',
                'versions': ['S23', 'S22', 'S21', 'A54'],
                'resolutions': ['1080x2340', '1440x3088', '1080x2400'],
                'dpr': [2, 3]
            },
            {
                'type': 'tablet',
                'brand': 'Apple',
                'model': 'iPad',
                'versions': ['Pro', 'Air', 'Mini'],
                'resolutions': ['2048x2732', '1640x2360', '1488x2266'],
                'dpr': [2]
            }
        ]
        
        for device in mobile_devices:
            for _ in range(3):
                version = random.choice(device['versions'])
                resolution = random.choice(device['resolutions'])
                dpr = random.choice(device['dpr'])
                
                profile = {
                    'device_type': device['type'],
                    'brand': device['brand'],
                    'model': f"{device['model']} {version}",
                    'screen_resolution': resolution,
                    'device_pixel_ratio': dpr,
                    'touch_support': True,
                    'mobile': True,
                    'orientation': random.choice(['portrait', 'landscape'])
                }
                profiles.append(profile)
        
        return profiles
    
    def _generate_network_profiles(self) -> List[Dict]:
        """Generate network profiles"""
        profiles = []
        
        connection_types = [
            {'type': 'wifi', 'downlink': 50, 'rtt': 50},
            {'type': '4g', 'downlink': 20, 'rtt': 100},
            {'type': '3g', 'downlink': 5, 'rtt': 200},
            {'type': 'ethernet', 'downlink': 100, 'rtt': 30}
        ]
        
        for conn in connection_types:
            profile = {
                'connection_type': conn['type'],
                'downlink': conn['downlink'] * random.uniform(0.8, 1.2),
                'effective_type': conn['type'],
                'rtt': int(conn['rtt'] * random.uniform(0.8, 1.2)),
                'save_data': random.choice([True, False])
            }
            profiles.append(profile)
        
        return profiles
    
    def _generate_behavior_profiles(self) -> List[Dict]:
        """Generate behavior profiles"""
        profiles = []
        
        behavior_patterns = [
            {
                'name': 'casual_scroller',
                'scroll_speed': random.uniform(1.0, 3.0),
                'click_delay': random.uniform(0.5, 2.0),
                'watch_time_multiplier': random.uniform(0.8, 1.2),
                'interaction_probability': 0.3
            },
            {
                'name': 'engaged_viewer',
                'scroll_speed': random.uniform(0.5, 1.5),
                'click_delay': random.uniform(0.2, 0.8),
                'watch_time_multiplier': random.uniform(1.5, 2.5),
                'interaction_probability': 0.7
            },
            {
                'name': 'fast_scroller',
                'scroll_speed': random.uniform(3.0, 5.0),
                'click_delay': random.uniform(0.1, 0.5),
                'watch_time_multiplier': random.uniform(0.5, 1.0),
                'interaction_probability': 0.1
            }
        ]
        
        for pattern in behavior_patterns:
            profiles.append(pattern)
        
        return profiles
    
    def create_fingerprint(self, profile_type: str = 'balanced') -> Dict:
        """Create complete browser fingerprint"""
        if profile_type == 'mobile':
            device = random.choice([p for p in self.config['device_profiles'] if p['device_type'] == 'mobile'])
            browser = random.choice(self.config['browser_profiles'])
        elif profile_type == 'desktop':
            device = {
                'device_type': 'desktop',
                'brand': 'Custom PC',
                'model': 'Desktop',
                'screen_resolution': random.choice(['1920x1080', '2560x1440', '3840x2160']),
                'device_pixel_ratio': 1,
                'touch_support': False,
                'mobile': False,
                'orientation': 'landscape'
            }
            browser = random.choice(self.config['browser_profiles'])
        else:  # balanced
            device = random.choice(self.config['device_profiles'])
            browser = random.choice(self.config['browser_profiles'])
        
        network = random.choice(self.config['network_profiles'])
        behavior = random.choice(self.config['behavior_profiles'])
        
        fingerprint = {
            'fingerprint_id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'device': device,
            'browser': browser,
            'network': network,
            'behavior': behavior,
            'navigator': self._generate_navigator_props(device, browser),
            'screen': self._generate_screen_props(device),
            'timezone': browser['timezone'],
            'language': browser['language'],
            'platform': browser['platform']
        }
        
        # Store fingerprint
        self.fingerprints[fingerprint['fingerprint_id']] = fingerprint
        
        return fingerprint
    
    def _generate_navigator_props(self, device: Dict, browser: Dict) -> Dict:
        """Generate navigator properties"""
        return {
            'userAgent': browser['user_agent'],
            'platform': browser['platform'],
            'language': browser['language'],
            'languages': [browser['language'], 'en-US', 'en'],
            'hardwareConcurrency': browser['hardware_concurrency'],
            'deviceMemory': browser['device_memory'],
            'maxTouchPoints': device.get('max_touch_points', 0),
            'vendor': 'Google Inc.',
            'webdriver': False,
            'pdfViewerEnabled': True
        }
    
    def _generate_screen_props(self, device: Dict) -> Dict:
        """Generate screen properties"""
        width, height = map(int, device['screen_resolution'].split('x'))
        
        return {
            'width': width,
            'height': height,
            'availWidth': width,
            'availHeight': height - 100,  # Account for taskbar
            'colorDepth': 24,
            'pixelDepth': 24,
            'orientation': {
                'type': device.get('orientation', 'landscape'),
                'angle': 0
            }
        }
    
    def get_headers(self, fingerprint_id: str) -> Dict[str, str]:
        """Get HTTP headers for fingerprint"""
        if fingerprint_id not in self.fingerprints:
            fingerprint = self.create_fingerprint()
            fingerprint_id = fingerprint['fingerprint_id']
        else:
            fingerprint = self.fingerprints[fingerprint_id]
        
        browser = fingerprint['browser']
        device = fingerprint['device']
        
        headers = {
            'User-Agent': browser['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': browser['language'],
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        if device['mobile']:
            headers['X-Requested-With'] = 'com.zhiliaoapp.musically'
            headers['Sec-CH-UA-Mobile'] = '?1'
        else:
            headers['Sec-CH-UA-Mobile'] = '?0'
        
        # Add Chrome hints
        headers['Sec-CH-UA'] = f'"Chromium";v="{browser["user_agent"].split("Chrome/")[1].split(".")[0]}", "Google Chrome";v="{browser["user_agent"].split("Chrome/")[1].split(".")[0]}", "Not=A?Brand";v="24"'
        headers['Sec-CH-UA-Platform'] = f'"{browser["platform"].split(";")[0]}"'
        
        return headers
    
    def get_cookies(self, fingerprint_id: str) -> List[Dict]:
        """Get cookies for fingerprint"""
        cookies = [
            {
                'name': 'tt_webid',
                'value': str(random.randint(1000000000000000000, 9999999999999999999)),
                'domain': '.tiktok.com',
                'path': '/',
                'secure': True,
                'httpOnly': True,
                'sameSite': 'Lax'
            },
            {
                'name': 'tt_webid_v2',
                'value': str(random.randint(1000000000000000000, 9999999999999999999)),
                'domain': '.tiktok.com',
                'path': '/',
                'secure': True,
                'httpOnly': True,
                'sameSite': 'Lax'
            },
            {
                'name': 'tt_csrf_token',
                'value': self._generate_token(),
                'domain': '.tiktok.com',
                'path': '/',
                'secure': True,
                'httpOnly': True,
                'sameSite': 'Lax'
            }
        ]
        
        return cookies
    
    def _generate_token(self) -> str:
        """Generate random token"""
        return hashlib.md5(str(random.random()).encode()).hexdigest()
    
    def simulate_human_behavior(self, behavior_profile: Dict, 
                               action: str) -> Dict:
        """Simulate human behavior for action"""
        if action == 'scroll':
            delay = random.expovariate(1.0 / behavior_profile['scroll_speed'])
            distance = random.randint(100, 500)
            
            return {
                'action': 'scroll',
                'delay': delay,
                'distance': distance,
                'smooth': random.choice([True, False]),
                'pattern': random.choice(['linear', 'ease-in-out', 'random'])
            }
        
        elif action == 'click':
            delay = random.expovariate(1.0 / behavior_profile['click_delay'])
            
            return {
                'action': 'click',
                'delay': delay,
                'position': {
                    'x': random.randint(50, 300),
                    'y': random.randint(50, 300)
                },
                'double_click': random.random() < 0.1
            }
        
        elif action == 'watch':
            base_time = random.randint(15, 60)
            watch_time = base_time * behavior_profile['watch_time_multiplier']
            
            return {
                'action': 'watch',
                'duration': watch_time,
                'interactions': self._generate_video_interactions(behavior_profile)
            }
        
        else:
            return {'action': action, 'delay': random.uniform(0.5, 2.0)}
    
    def _generate_video_interactions(self, behavior_profile: Dict) -> List[Dict]:
        """Generate video interactions"""
        interactions = []
        
        if random.random() < behavior_profile['interaction_probability']:
            # Like
            if random.random() < 0.3:
                interactions.append({
                    'type': 'like',
                    'time': random.uniform(5, 30),
                    'duration': random.uniform(0.5, 1.0)
                })
            
            # Comment view
            if random.random() < 0.2:
                interactions.append({
                    'type': 'comment_view',
                    'time': random.uniform(10, 40),
                    'duration': random.uniform(2, 5)
                })
            
            # Share click
            if random.random() < 0.1:
                interactions.append({
                    'type': 'share_click',
                    'time': random.uniform(20, 50),
                    'duration': random.uniform(1, 3)
                })
        
        return interactions
    
    def rotate_fingerprint(self, old_fingerprint_id: str) -> Dict:
        """Rotate to new fingerprint"""
        # Invalidate old fingerprint
        if old_fingerprint_id in self.fingerprints:
            self.fingerprints[old_fingerprint_id]['invalidated'] = True
        
        # Create new fingerprint
        return self.create_fingerprint()
    
    def get_fingerprint_hash(self, fingerprint: Dict) -> str:
        """Calculate fingerprint hash"""
        fingerprint_str = json.dumps(fingerprint, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    def validate_fingerprint(self, fingerprint_id: str) -> bool:
        """Validate fingerprint"""
        if fingerprint_id not in self.fingerprints:
            return False
        
        fingerprint = self.fingerprints[fingerprint_id]
        
        # Check if invalidated
        if fingerprint.get('invalidated'):
            return False
        
        # Check age (rotate after 24 hours)
        created_at = datetime.fromisoformat(fingerprint['created_at'])
        age_hours = (datetime.now() - created_at).total_seconds() / 3600
        
        if age_hours > 24:
            return False
        
        return True
    
    def detect_bot_patterns(self, activity_log: List[Dict]) -> List[str]:
        """Detect bot-like patterns in activity"""
        warnings = []
        
        if len(activity_log) < 10:
            return warnings
        
        # Check timing patterns
        timings = [log.get('response_time', 0) for log in activity_log]
        
        # Too consistent timing
        if len(set(round(t, 2) for t in timings)) < len(timings) * 0.3:
            warnings.append("Consistent timing patterns detected")
        
        # Check request frequency
        request_times = [log.get('timestamp') for log in activity_log]
        intervals = []
        
        for i in range(1, len(request_times)):
            try:
                t1 = datetime.fromisoformat(request_times[i-1])
                t2 = datetime.fromisoformat(request_times[i])
                intervals.append((t2 - t1).total_seconds())
            except:
                pass
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval < 1.0:  # Too frequent requests
                warnings.append("Request frequency too high")
            
            # Check for exact intervals
            rounded_intervals = [round(i, 1) for i in intervals]
            if len(set(rounded_intervals)) < len(intervals) * 0.5:
                warnings.append("Predictable request intervals")
        
        # Check user agent rotation
        user_agents = [log.get('user_agent', '') for log in activity_log]
        unique_agents = len(set(user_agents))
        
        if unique_agents > len(activity_log) * 0.5:  # Too many user agents
            warnings.append("Excessive user agent rotation")
        
        # Check for automation headers
        for log in activity_log:
            headers = log.get('headers', {})
            if headers.get('X-Requested-With') == 'XMLHttpRequest' and 'automation' in str(headers).lower():
                warnings.append("Automation headers detected")
        
        return warnings
    
    def generate_ip_address(self, country_code: str = 'US') -> str:
        """Generate realistic IP address for country"""
        # Country IP ranges (simplified)
        ip_ranges = {
            'US': [
                ('104.16.0.0', '104.31.255.255'),
                ('172.217.0.0', '172.217.255.255'),
                ('216.58.192.0', '216.58.223.255')
            ],
            'UK': [
                ('31.13.0.0', '31.13.255.255'),
                ('77.111.0.0', '77.111.255.255'),
                ('212.58.0.0', '212.58.255.255')
            ],
            'DE': [
                ('87.138.0.0', '87.138.255.255'),
                ('178.162.0.0', '178.162.255.255'),
                ('213.61.0.0', '213.61.255.255')
            ]
        }
        
        if country_code not in ip_ranges:
            country_code = 'US'
        
        ip_range = random.choice(ip_ranges[country_code])
        start_ip = self._ip_to_int(ip_range[0])
        end_ip = self._ip_to_int(ip_range[1])
        
        random_ip_int = random.randint(start_ip, end_ip)
        return self._int_to_ip(random_ip_int)
    
    def _ip_to_int(self, ip: str) -> int:
        """Convert IP to integer"""
        return struct.unpack("!I", socket.inet_aton(ip))[0]
    
    def _int_to_ip(self, ip_int: int) -> str:
        """Convert integer to IP"""
        return socket.inet_ntoa(struct.pack("!I", ip_int))
    
    def get_geolocation(self, ip_address: str) -> Dict:
        """Get geolocation for IP (mock)"""
        # In production, use IP geolocation service
        return {
            'ip': ip_address,
            'country': 'US',
            'country_code': 'US',
            'region': 'California',
            'city': 'Los Angeles',
            'latitude': 34.0522,
            'longitude': -118.2437,
            'timezone': 'America/Los_Angeles',
            'isp': 'Google LLC',
            'asn': 'AS15169'
        }