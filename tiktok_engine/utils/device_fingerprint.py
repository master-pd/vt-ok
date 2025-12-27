"""
Device Fingerprint - Generate unique device fingerprints
"""

import random
import uuid
import hashlib
from typing import Dict, List
import json

class DeviceFingerprint:
    """Generate realistic device fingerprints"""
    
    def __init__(self):
        self.device_templates = self.load_device_templates()
        self.browser_profiles = self.load_browser_profiles()
        
    def load_device_templates(self) -> List[Dict]:
        """Load device templates"""
        return [
            {
                'type': 'mobile',
                'brands': ['Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi', 'Huawei'],
                'models': {
                    'Apple': ['iPhone 14', 'iPhone 13', 'iPhone 12', 'iPhone 11', 'iPhone SE'],
                    'Samsung': ['Galaxy S23', 'Galaxy S22', 'Galaxy S21', 'Galaxy A54', 'Galaxy A34'],
                    'Google': ['Pixel 7', 'Pixel 6', 'Pixel 5', 'Pixel 4a'],
                    'OnePlus': ['OnePlus 11', 'OnePlus 10', 'OnePlus 9', 'OnePlus Nord'],
                    'Xiaomi': ['Redmi Note 12', 'Redmi Note 11', 'Xiaomi 13', 'Xiaomi 12'],
                    'Huawei': ['P50 Pro', 'P40 Pro', 'Mate 40', 'Nova 10']
                },
                'os_versions': {
                    'iOS': ['16.6', '16.5', '16.4', '16.3', '16.2'],
                    'Android': ['13', '12', '11', '10']
                }
            },
            {
                'type': 'desktop',
                'brands': ['Windows', 'Mac', 'Linux'],
                'models': {
                    'Windows': ['Windows 11', 'Windows 10', 'Windows 8.1'],
                    'Mac': ['macOS Ventura', 'macOS Monterey', 'macOS Big Sur'],
                    'Linux': ['Ubuntu 22.04', 'Ubuntu 20.04', 'Debian 11', 'Fedora 38']
                },
                'browsers': ['Chrome', 'Firefox', 'Safari', 'Edge']
            }
        ]
    
    def load_browser_profiles(self) -> List[Dict]:
        """Load browser profiles"""
        return [
            {
                'name': 'Chrome',
                'versions': ['120', '119', '118', '117', '116'],
                'user_agent_templates': [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36'
                ]
            },
            {
                'name': 'Firefox',
                'versions': ['120', '119', '118', '117', '116'],
                'user_agent_templates': [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}.0) Gecko/20100101 Firefox/{version}.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{version}.0) Gecko/20100101 Firefox/{version}.0',
                    'Mozilla/5.0 (X11; Linux x86_64; rv:{version}.0) Gecko/20100101 Firefox/{version}.0'
                ]
            },
            {
                'name': 'Safari',
                'versions': ['16.6', '16.5', '16.4', '16.3'],
                'user_agent_templates': [
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15',
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Mobile/15E148 Safari/604.1'
                ]
            }
        ]
    
    def generate_device_fingerprint(self, device_type: str = None) -> Dict:
        """Generate a complete device fingerprint"""
        if device_type is None:
            device_type = random.choice(['mobile', 'desktop'])
        
        if device_type == 'mobile':
            return self.generate_mobile_fingerprint()
        else:
            return self.generate_desktop_fingerprint()
    
    def generate_mobile_fingerprint(self) -> Dict:
        """Generate mobile device fingerprint"""
        template = next(t for t in self.device_templates if t['type'] == 'mobile')
        
        # Select random brand and model
        brand = random.choice(template['brands'])
        model = random.choice(template['models'][brand])
        
        # Select OS
        if brand == 'Apple':
            os_name = 'iOS'
            os_version = random.choice(template['os_versions']['iOS'])
        else:
            os_name = 'Android'
            os_version = random.choice(template['os_versions']['Android'])
        
        # Generate device ID
        device_id = self.generate_device_id()
        
        # Generate browser fingerprint
        browser = self.generate_browser_fingerprint('mobile')
        
        # Screen resolution
        if brand == 'Apple':
            resolutions = [
                {'width': 1170, 'height': 2532},  # iPhone 14 Pro
                {'width': 1284, 'height': 2778},  # iPhone 14 Pro Max
                {'width': 1080, 'height': 2340},  # iPhone 13
                {'width': 828, 'height': 1792},   # iPhone 11
            ]
        else:
            resolutions = [
                {'width': 1080, 'height': 2400},
                {'width': 1440, 'height': 3200},
                {'width': 720, 'height': 1600},
            ]
        
        resolution = random.choice(resolutions)
        
        # Generate additional mobile-specific data
        fingerprint = {
            'device_type': 'mobile',
            'brand': brand,
            'model': model,
            'os_name': os_name,
            'os_version': os_version,
            'device_id': device_id,
            'screen_resolution': resolution,
            'pixel_density': random.choice([326, 401, 476, 538]),  # PPI
            'language': random.choice(['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE']),
            'timezone': random.choice(['America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney']),
            'network_type': random.choice(['wifi', '4g', '5g']),
            'carrier': random.choice(['AT&T', 'Verizon', 'T-Mobile', 'Vodafone', 'Orange']),
            'battery_level': random.randint(20, 100),
            'is_charging': random.choice([True, False]),
            'storage_free': random.randint(1024, 10240),  # MB
            'ram_total': random.choice([4096, 6144, 8192]),  # MB
            'cpu_cores': random.choice([4, 6, 8]),
            'cpu_architecture': random.choice(['arm64-v8a', 'armeabi-v7a']),
            'gpu_vendor': random.choice(['Qualcomm', 'ARM', 'Apple']),
            'gpu_renderer': random.choice(['Adreno 650', 'Mali-G78', 'Apple GPU']),
            'browser': browser,
            'fingerprint_hash': self.calculate_fingerprint_hash({
                'brand': brand,
                'model': model,
                'device_id': device_id,
                'browser': browser['user_agent']
            })
        }
        
        return fingerprint
    
    def generate_desktop_fingerprint(self) -> Dict:
        """Generate desktop device fingerprint"""
        template = next(t for t in self.device_templates if t['type'] == 'desktop')
        
        # Select OS
        os_name = random.choice(template['brands'])
        os_version = random.choice(template['models'][os_name])
        
        # Generate device ID
        device_id = self.generate_device_id()
        
        # Generate browser fingerprint
        browser_name = random.choice(template['browsers'])
        browser = self.generate_browser_fingerprint('desktop', browser_name)
        
        # Screen resolution
        resolutions = [
            {'width': 1920, 'height': 1080},
            {'width': 2560, 'height': 1440},
            {'width': 3840, 'height': 2160},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
        ]
        
        resolution = random.choice(resolutions)
        
        # Generate additional desktop-specific data
        fingerprint = {
            'device_type': 'desktop',
            'os_name': os_name,
            'os_version': os_version,
            'device_id': device_id,
            'screen_resolution': resolution,
            'color_depth': random.choice([24, 30, 32]),
            'language': random.choice(['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE']),
            'timezone': random.choice(['America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney']),
            'cpu_cores': random.choice([4, 6, 8, 12, 16]),
            'cpu_architecture': random.choice(['x86_64', 'arm64']),
            'ram_total': random.choice([8192, 16384, 32768, 65536]),  # MB
            'gpu_vendor': random.choice(['NVIDIA', 'AMD', 'Intel']),
            'gpu_renderer': random.choice(['NVIDIA GeForce RTX 3080', 'AMD Radeon RX 6800', 'Intel UHD Graphics 630']),
            'browser': browser,
            'plugins': self.generate_browser_plugins(browser_name),
            'fonts': self.generate_font_list(),
            'canvas_fingerprint': self.generate_canvas_fingerprint(),
            'webgl_fingerprint': self.generate_webgl_fingerprint(),
            'audio_fingerprint': self.generate_audio_fingerprint(),
            'fingerprint_hash': self.calculate_fingerprint_hash({
                'os_name': os_name,
                'os_version': os_version,
                'device_id': device_id,
                'browser': browser['user_agent'],
                'screen_resolution': resolution
            })
        }
        
        return fingerprint
    
    def generate_browser_fingerprint(self, device_type: str, 
                                   browser_name: str = None) -> Dict:
        """Generate browser fingerprint"""
        if browser_name is None:
            if device_type == 'mobile':
                browser_name = random.choice(['Chrome', 'Safari'])
            else:
                browser_name = random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])
        
        browser_profile = next(b for b in self.browser_profiles if b['name'] == browser_name)
        
        version = random.choice(browser_profile['versions'])
        template = random.choice(browser_profile['user_agent_templates'])
        
        user_agent = template.format(version=version)
        
        # Generate browser-specific data
        browser_data = {
            'name': browser_name,
            'version': version,
            'user_agent': user_agent,
            'language': random.choice(['en-US', 'en', 'en-GB']),
            'platform': 'Win32' if 'Windows' in user_agent else 
                       'MacIntel' if 'Macintosh' in user_agent else 
                       'Linux x86_64',
            'vendor': 'Google Inc.' if browser_name == 'Chrome' else
                     'Apple Computer, Inc.' if browser_name == 'Safari' else
                     'Mozilla Foundation',
            'product': 'Gecko' if browser_name == 'Firefox' else 'AppleWebKit',
            'app_version': version + '.0',
            'build_id': str(random.randint(1000000000, 9999999999))
        }
        
        return browser_data
    
    def generate_device_id(self) -> str:
        """Generate unique device ID"""
        # Generate a unique but consistent ID
        components = [
            str(uuid.uuid4()),
            str(random.randint(1000000000, 9999999999)),
            hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        ]
        
        device_id = ':'.join(components)
        return device_id
    
    def generate_browser_plugins(self, browser_name: str) -> List[str]:
        """Generate browser plugins list"""
        common_plugins = [
            'Chrome PDF Viewer',
            'Chrome PDF Plugin',
            'Native Client',
            'Widevine Content Decryption Module',
            'Microsoft Office'
        ]
        
        browser_specific = {
            'Chrome': ['Chrome Remote Desktop Viewer', 'Google Talk Plugin'],
            'Firefox': ['OpenH264 Video Codec', 'Primetime Content Decryption Module'],
            'Safari': ['QuickTime Plug-in 7.7.3', 'Flash Player'],
            'Edge': ['Microsoft Edge PDF Viewer', 'Microsoft Office']
        }
        
        plugins = common_plugins[:random.randint(2, 4)]
        
        if browser_name in browser_specific:
            plugins.extend(browser_specific[browser_name][:random.randint(1, 2)])
        
        return plugins
    
    def generate_font_list(self) -> List[str]:
        """Generate font list"""
        common_fonts = [
            'Arial', 'Arial Black', 'Arial Narrow', 'Calibri', 'Cambria',
            'Comic Sans MS', 'Courier New', 'Georgia', 'Impact', 'Lucida Console',
            'Microsoft Sans Serif', 'Segoe UI', 'Tahoma', 'Times New Roman',
            'Trebuchet MS', 'Verdana', 'Webdings', 'Wingdings'
        ]
        
        # Select random subset
        font_count = random.randint(10, 20)
        return random.sample(common_fonts, font_count)
    
    def generate_canvas_fingerprint(self) -> str:
        """Generate canvas fingerprint"""
        # Simulate canvas fingerprint hash
        components = [
            str(random.randint(1000, 9999)),
            str(random.randint(1000, 9999)),
            str(random.randint(1000, 9999))
        ]
        
        return hashlib.md5(''.join(components).encode()).hexdigest()
    
    def generate_webgl_fingerprint(self) -> Dict:
        """Generate WebGL fingerprint"""
        vendors = ['WebKit', 'Mozilla', 'Google Inc.', 'Apple Inc.']
        renderers = [
            'WebKit WebGL', 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'ANGLE (AMD, AMD Radeon RX 6800 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)'
        ]
        
        return {
            'vendor': random.choice(vendors),
            'renderer': random.choice(renderers),
            'version': f'{random.randint(1, 3)}.{random.randint(0, 9)}',
            'shading_language_version': f'{random.randint(1, 4)}.{random.randint(0, 9)}0',
            'max_texture_size': random.choice([16384, 8192, 4096]),
            'max_vertex_texture_units': random.choice([16, 32, 64])
        }
    
    def generate_audio_fingerprint(self) -> str:
        """Generate audio fingerprint"""
        # Simulate audio fingerprint hash
        components = [
            str(random.uniform(0.1, 0.9)),
            str(random.uniform(0.1, 0.9)),
            str(random.uniform(0.1, 0.9))
        ]
        
        return hashlib.md5(''.join(components).encode()).hexdigest()
    
    def calculate_fingerprint_hash(self, data: Dict) -> str:
        """Calculate fingerprint hash"""
        import json
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def get_fingerprint_as_headers(self, fingerprint: Dict) -> Dict:
        """Convert fingerprint to HTTP headers"""
        headers = {
            'User-Agent': fingerprint['browser']['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': fingerprint.get('language', 'en-US,en;q=0.9'),
            'Accept-Encoding': 'gzip, deflate, br',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Add mobile-specific headers
        if fingerprint['device_type'] == 'mobile':
            headers.update({
                'Viewport-Width': str(fingerprint['screen_resolution']['width']),
                'Device-Memory': str(fingerprint.get('ram_total', 4096) // 1024),  # GB
                'Downlink': str(random.choice([10, 50, 100, 1000])),  # Mbps
                'ECT': random.choice(['4g', '3g', '2g', 'slow-2g']),
                'RTT': str(random.randint(50, 300)),  # ms
                'Save-Data': random.choice(['on', 'off'])
            })
        
        return headers
    
    def get_fingerprint_as_cookies(self, fingerprint: Dict) -> Dict:
        """Convert fingerprint to cookies"""
        cookies = {
            'device_id': fingerprint['device_id'],
            'session_id': str(uuid.uuid4()),
            'user_id': str(random.randint(1000000, 9999999)),
            'last_visit': str(int(time.time())),
            'preferences': 'en_US' + str(random.randint(1, 100))
        }
        
        return cookies
    
    def save_fingerprint(self, fingerprint: Dict, filename: str = None):
        """Save fingerprint to file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"fingerprints/device_{timestamp}.json"
        
        import os
        os.makedirs('fingerprints', exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(fingerprint, f, indent=2)
        
        print(f"💾 Saved fingerprint to {filename}")
        return filename
    
    def load_fingerprint(self, filename: str) -> Dict:
        """Load fingerprint from file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Fingerprint file not found: {filename}")
            return {}
    
    def generate_batch_fingerprints(self, count: int, 
                                   device_type: str = None) -> List[Dict]:
        """Generate batch of fingerprints"""
        fingerprints = []
        
        for i in range(count):
            fp = self.generate_device_fingerprint(device_type)
            fingerprints.append(fp)
            
            # Save every 10th fingerprint
            if (i + 1) % 10 == 0:
                self.save_fingerprint(fp, f"fingerprints/batch_{i+1}.json")
        
        print(f"✅ Generated {count} device fingerprints")
        return fingerprints
    
    def analyze_fingerprint_uniqueness(self, fingerprints: List[Dict]) -> Dict:
        """Analyze fingerprint uniqueness"""
        hashes = [fp['fingerprint_hash'] for fp in fingerprints]
        
        unique_hashes = set(hashes)
        duplicate_count = len(hashes) - len(unique_hashes)
        
        # Analyze device type distribution
        device_types = {}
        for fp in fingerprints:
            device_type = fp['device_type']
            device_types[device_type] = device_types.get(device_type, 0) + 1
        
        # Analyze browser distribution
        browsers = {}
        for fp in fingerprints:
            browser = fp['browser']['name']
            browsers[browser] = browsers.get(browser, 0) + 1
        
        return {
            'total_fingerprints': len(fingerprints),
            'unique_fingerprints': len(unique_hashes),
            'duplicate_count': duplicate_count,
            'uniqueness_rate': (len(unique_hashes) / len(fingerprints)) * 100,
            'device_type_distribution': device_types,
            'browser_distribution': browsers,
            'is_sufficiently_unique': duplicate_count == 0
        }