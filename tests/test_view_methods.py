"""
Unit Tests for VT ULTRA PRO View Methods
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tiktok_engine.view_methods.browser_v3 import BrowserViewMethod
from tiktok_engine.view_methods.api_v2 import APIViewMethod
from tiktok_engine.view_methods.cloud_view import CloudViewMethod
from tiktok_engine.view_methods.hybrid_ai import HybridAIMethod
from tiktok_engine.utils.proxy_rotator import ProxyRotator
from tiktok_engine.utils.device_fingerprint import DeviceFingerprintGenerator

class TestBrowserViewMethod(unittest.TestCase):
    """Test Browser View Method"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.browser_method = BrowserViewMethod()
        self.test_video_url = "https://www.tiktok.com/@testuser/video/1234567890"
        
    @patch('selenium.webdriver.Chrome')
    def test_initialize_browser(self, mock_chrome):
        """Test browser initialization"""
        # Setup mock
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Test initialization
        success = self.browser_method.initialize_browser(use_proxy=False)
        
        self.assertTrue(success)
        mock_chrome.assert_called_once()
        
    @patch('selenium.webdriver.Chrome')
    def test_send_view_basic(self, mock_chrome):
        """Test basic view sending"""
        # Setup mock driver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock page elements
        mock_driver.find_element.return_value.text = "100 views"
        mock_driver.execute_script.return_value = None
        
        # Test sending view
        result = self.browser_method.send_view(self.test_video_url)
        
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertIn('watch_time', result)
        
    @patch('selenium.webdriver.Chrome')
    def test_send_view_with_interaction(self, mock_chrome):
        """Test view sending with interactions"""
        # Setup mock
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock interactions
        mock_driver.find_element.side_effect = [
            Mock(text="100 views"),  # Initial views
            Mock(),  # Like button
            Mock(text="101 views")   # Final views
        ]
        
        # Test with interactions
        result = self.browser_method.send_view(
            self.test_video_url,
            interactions=['like', 'comment_view']
        )
        
        self.assertTrue(result['success'])
        self.assertGreaterEqual(result.get('interaction_count', 0), 0)
        
    @patch('selenium.webdriver.Chrome')
    def test_send_view_error_handling(self, mock_chrome):
        """Test error handling"""
        # Setup mock to raise exception
        mock_driver = Mock()
        mock_driver.get.side_effect = Exception("Page load failed")
        mock_chrome.return_value = mock_driver
        
        # Test error case
        result = self.browser_method.send_view(self.test_video_url)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
    def test_generate_human_behavior(self):
        """Test human behavior generation"""
        behavior = self.browser_method.generate_human_behavior()
        
        self.assertIn('scroll_pattern', behavior)
        self.assertIn('click_delay', behavior)
        self.assertIn('watch_time_variation', behavior)
        
        # Validate ranges
        self.assertGreaterEqual(behavior['click_delay'], 0.5)
        self.assertLessEqual(behavior['click_delay'], 3.0)
        
    @patch('selenium.webdriver.Chrome')
    def test_batch_view_sending(self, mock_chrome):
        """Test batch view sending"""
        # Setup mock
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock view counts
        mock_driver.find_element.return_value.text = "100 views"
        
        # Test batch
        results = self.browser_method.send_batch_views(
            [self.test_video_url] * 3,
            views_per_video=10
        )
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('success', result)

class TestAPIViewMethod(unittest.TestCase):
    """Test API View Method"""
    
    def setUp(self):
        self.api_method = APIViewMethod()
        self.test_video_id = "1234567890"
        
    @patch('requests.Session')
    def test_get_video_info(self, mock_session):
        """Test getting video information"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'itemInfo': {
                'itemStruct': {
                    'id': self.test_video_id,
                    'desc': 'Test video',
                    'stats': {'playCount': 100}
                }
            }
        }
        
        mock_session.return_value.get.return_value = mock_response
        
        # Test
        video_info = self.api_method.get_video_info(self.test_video_id)
        
        self.assertIsNotNone(video_info)
        self.assertEqual(video_info['video_id'], self.test_video_id)
        self.assertEqual(video_info['current_views'], 100)
        
    @patch('requests.Session')
    def test_send_view_api(self, mock_session):
        """Test sending view via API"""
        # Setup mock responses
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {'status_code': 0}
        
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            'itemInfo': {
                'itemStruct': {
                    'stats': {'playCount': 101}
                }
            }
        }
        
        mock_session.return_value.post.return_value = mock_response1
        mock_session.return_value.get.return_value = mock_response2
        
        # Test
        result = self.api_method.send_view(self.test_video_id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['views_sent'], 1)
        
    @patch('requests.Session')
    def test_send_view_api_failure(self, mock_session):
        """Test API view sending failure"""
        # Setup mock failure
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {'status_code': 1009, 'status_msg': 'Rate limited'}
        
        mock_session.return_value.post.return_value = mock_response
        
        # Test
        result = self.api_method.send_view(self.test_video_id)
        
        self.assertFalse(result['success'])
        self.assertIn('rate_limit', result.get('error', '').lower())
        
    def test_generate_api_headers(self):
        """Test API header generation"""
        headers = self.api_method._generate_headers()
        
        self.assertIn('User-Agent', headers)
        self.assertIn('X-Tt-Token', headers)
        self.assertIn('Content-Type', headers)
        
        # Check User-Agent format
        self.assertIn('TikTok', headers['User-Agent'])
        
    def test_extract_video_id_from_url(self):
        """Test video ID extraction"""
        test_cases = [
            ("https://www.tiktok.com/@user/video/1234567890", "1234567890"),
            ("https://vm.tiktok.com/ABCDEF/", "ABCDEF"),
            ("https://m.tiktok.com/v/123456.html", "123456"),
            ("invalid_url", None)
        ]
        
        for url, expected_id in test_cases:
            extracted = self.api_method._extract_video_id(url)
            self.assertEqual(extracted, expected_id)
            
    @patch('requests.Session')
    def test_batch_api_views(self, mock_session):
        """Test batch API views"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status_code': 0}
        
        mock_session.return_value.post.return_value = mock_response
        
        # Test batch
        video_ids = [str(i) for i in range(5)]
        results = self.api_method.send_batch_views(video_ids, views_per_video=2)
        
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertTrue(result['success'])
            self.assertEqual(result['views_sent'], 2)

class TestCloudViewMethod(unittest.IsolatedAsyncioTestCase):
    """Test Cloud View Method (async)"""
    
    async def asyncSetUp(self):
        self.cloud_method = CloudViewMethod()
        await self.cloud_method.initialize()
        
    async def asyncTearDown(self):
        await self.cloud_method.close()
        
    @patch('aiohttp.ClientSession')
    async def test_send_cloud_view(self, mock_session):
        """Test sending cloud view"""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = 'View counted'
        
        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        # Test
        result = await self.cloud_method.send_view(
            "https://www.tiktok.com/@test/video/123"
        )
        
        self.assertTrue(result['success'])
        
    @patch('aiohttp.ClientSession')
    async def test_batch_cloud_views(self, mock_session):
        """Test batch cloud views"""
        # Setup mock
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        # Test batch
        urls = [f"https://tiktok.com/video/{i}" for i in range(3)]
        results = await self.cloud_method.send_batch_views(urls, concurrent_limit=2)
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r['success'] for r in results))
        
    async def test_cloud_method_configuration(self):
        """Test cloud method configuration"""
        config = {
            'concurrent_workers': 10,
            'request_timeout': 30,
            'retry_attempts': 3
        }
        
        self.cloud_method.configure(config)
        
        self.assertEqual(self.cloud_method.concurrent_workers, 10)
        self.assertEqual(self.cloud_method.request_timeout, 30)
        self.assertEqual(self.cloud_method.retry_attempts, 3)

class TestHybridAIMethod(unittest.IsolatedAsyncioTestCase):
    """Test Hybrid AI Method"""
    
    async def asyncSetUp(self):
        self.hybrid_method = HybridAIMethod()
        await self.hybrid_method.initialize()
        
    async def asyncTearDown(self):
        await self.hybrid_method.close()
        
    @patch('tiktok_engine.view_methods.browser_v3.BrowserViewMethod')
    @patch('tiktok_engine.view_methods.api_v2.APIViewMethod')
    async def test_hybrid_strategy_selection(self, mock_api, mock_browser):
        """Test strategy selection"""
        # Setup mocks
        mock_browser_instance = Mock()
        mock_browser_instance.send_view.return_value = {'success': True, 'method': 'browser'}
        
        mock_api_instance = Mock()
        mock_api_instance.send_view.return_value = {'success': True, 'method': 'api'}
        
        mock_browser.return_value = mock_browser_instance
        mock_api.return_value = mock_api_instance
        
        # Test with different video types
        test_cases = [
            ("new_video", "browser"),  # New videos use browser
            ("popular_video", "api"),   # Popular videos use API
            ("sensitive_video", "browser")  # Sensitive content uses browser
        ]
        
        for video_type, expected_method in test_cases:
            result = await self.hybrid_method.send_view(
                f"https://tiktok.com/video/{video_type}",
                video_metadata={'type': video_type}
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['method_used'], expected_method)
            
    async def test_ai_pattern_generation(self):
        """Test AI pattern generation"""
        pattern = await self.hybrid_method.generate_view_pattern(
            total_views=100,
            duration_hours=24
        )
        
        self.assertIsInstance(pattern, list)
        self.assertEqual(len(pattern), 100)
        
        # Check pattern structure
        for entry in pattern[:10]:  # Check first 10 entries
            self.assertIn('timestamp', entry)
            self.assertIn('watch_time', entry)
            self.assertIn('device', entry)
            self.assertIn('location', entry)
            
    @patch('tiktok_engine.view_methods.browser_v3.BrowserViewMethod')
    @patch('tiktok_engine.view_methods.api_v2.APIViewMethod')
    async def test_adaptive_switching(self, mock_api, mock_browser):
        """Test adaptive method switching"""
        # Setup mocks with different success rates
        mock_browser_instance = Mock()
        mock_browser_instance.send_view.side_effect = [
            {'success': True},
            {'success': False},  # Second attempt fails
            {'success': True}
        ]
        
        mock_api_instance = Mock()
        mock_api_instance.send_view.return_value = {'success': True}
        
        mock_browser.return_value = mock_browser_instance
        mock_api.return_value = mock_api_instance
        
        # Test adaptive switching
        results = []
        for _ in range(3):
            result = await self.hybrid_method.send_view(
                "https://tiktok.com/video/test"
            )
            results.append(result)
        
        # Should switch to API after browser failure
        self.assertEqual(results[0]['method_used'], 'browser')
        self.assertEqual(results[1]['method_used'], 'api')  # Switched after failure
        self.assertEqual(results[2]['method_used'], 'api')  # Stayed with API
        
    async def test_performance_analytics(self):
        """Test performance analytics"""
        # Add some mock results
        mock_results = [
            {'success': True, 'method': 'browser', 'response_time': 2.5},
            {'success': False, 'method': 'browser', 'response_time': 5.0},
            {'success': True, 'method': 'api', 'response_time': 1.0},
            {'success': True, 'method': 'api', 'response_time': 1.5}
        ]
        
        for result in mock_results:
            self.hybrid_method._update_performance_stats(result)
        
        # Get analytics
        analytics = self.hybrid_method.get_performance_analytics()
        
        self.assertIn('browser', analytics)
        self.assertIn('api', analytics)
        
        # Check calculations
        browser_stats = analytics['browser']
        self.assertEqual(browser_stats['total_attempts'], 2)
        self.assertEqual(browser_stats['successful'], 1)
        self.assertEqual(browser_stats['success_rate'], 50.0)

class TestProxyRotator(unittest.TestCase):
    """Test Proxy Rotator"""
    
    def setUp(self):
        self.proxy_rotator = ProxyRotator()
        
    def test_proxy_validation(self):
        """Test proxy validation"""
        valid_proxies = [
            "http://user:pass@proxy.com:8080",
            "socks5://127.0.0.1:9050",
            "https://proxy.example.com:3128"
        ]
        
        invalid_proxies = [
            "invalid_proxy",
            "http://",
            "ftp://proxy.com:8080"
        ]
        
        for proxy in valid_proxies:
            self.assertTrue(self.proxy_rotator.validate_proxy(proxy))
            
        for proxy in invalid_proxies:
            self.assertFalse(self.proxy_rotator.validate_proxy(proxy))
            
    def test_proxy_rotation(self):
        """Test proxy rotation logic"""
        proxies = [
            "http://proxy1.com:8080",
            "http://proxy2.com:8080",
            "http://proxy3.com:8080"
        ]
        
        self.proxy_rotator.add_proxies(proxies)
        
        # Test round-robin rotation
        used_proxies = set()
        for _ in range(10):
            proxy = self.proxy_rotator.get_next_proxy()
            used_proxies.add(proxy)
            
        # Should use all proxies
        self.assertEqual(len(used_proxies), 3)
        
    def test_proxy_health_check(self):
        """Test proxy health checking"""
        # Note: In real tests, this would mock network requests
        self.proxy_rotator.add_proxies([
            "http://healthy-proxy.com:8080",
            "http://unhealthy-proxy.com:8080"
        ])
        
        # Mark one as unhealthy
        self.proxy_rotator.mark_unhealthy("http://unhealthy-proxy.com:8080")
        
        # Should skip unhealthy proxy
        for _ in range(5):
            proxy = self.proxy_rotator.get_next_proxy()
            self.assertNotEqual(proxy, "http://unhealthy-proxy.com:8080")
            
    def test_proxy_statistics(self):
        """Test proxy statistics"""
        proxies = ["http://proxy1.com:8080", "http://proxy2.com:8080"]
        self.proxy_rotator.add_proxies(proxies)
        
        # Simulate some usage
        for _ in range(10):
            proxy = self.proxy_rotator.get_next_proxy()
            if proxy == proxies[0]:
                self.proxy_rotator.record_success(proxy)
            else:
                self.proxy_rotator.record_failure(proxy)
                
        # Check stats
        stats = self.proxy_rotator.get_statistics()
        
        self.assertEqual(stats['total_proxies'], 2)
        self.assertEqual(stats['healthy_proxies'], 1)
        self.assertEqual(stats['unhealthy_proxies'], 1)

class TestDeviceFingerprint(unittest.TestCase):
    """Test Device Fingerprint Generator"""
    
    def setUp(self):
        self.fingerprint_gen = DeviceFingerprintGenerator()
        
    def test_fingerprint_generation(self):
        """Test fingerprint generation"""
        fingerprint = self.fingerprint_gen.generate_fingerprint()
        
        # Check required fields
        required_fields = [
            'user_agent', 'screen_resolution', 'timezone',
            'language', 'platform', 'hardware_concurrency',
            'device_memory', 'webgl_vendor', 'webgl_renderer'
        ]
        
        for field in required_fields:
            self.assertIn(field, fingerprint)
            self.assertIsNotNone(fingerprint[field])
            
    def test_mobile_fingerprint(self):
        """Test mobile fingerprint generation"""
        mobile_fp = self.fingerprint_gen.generate_mobile_fingerprint()
        
        self.assertIn('mobile', mobile_fp['user_agent'].lower())
        self.assertIn('touch', mobile_fp['user_agent'].lower())
        self.assertTrue(mobile_fp.get('mobile', False))
        
    def test_desktop_fingerprint(self):
        """Test desktop fingerprint generation"""
        desktop_fp = self.fingerprint_gen.generate_desktop_fingerprint()
        
        self.assertIn('windows', desktop_fp['user_agent'].lower()) or \
        self.assertIn('mac', desktop_fp['user_agent'].lower()) or \
        self.assertIn('linux', desktop_fp['user_agent'].lower())
        self.assertFalse(desktop_fp.get('mobile', True))
        
    def test_fingerprint_uniqueness(self):
        """Test fingerprint uniqueness"""
        fingerprints = []
        
        for _ in range(10):
            fp = self.fingerprint_gen.generate_fingerprint()
            fingerprints.append(fp)
            
        # Check that fingerprints are not identical
        user_agents = [fp['user_agent'] for fp in fingerprints]
        self.assertEqual(len(set(user_agents)), len(fingerprints))
        
    def test_fingerprint_persistence(self):
        """Test fingerprint persistence"""
        fp1 = self.fingerprint_gen.generate_fingerprint()
        fp_id = fp1['fingerprint_id']
        
        # Retrieve same fingerprint
        fp2 = self.fingerprint_gen.get_fingerprint(fp_id)
        
        self.assertEqual(fp1['fingerprint_id'], fp2['fingerprint_id'])
        self.assertEqual(fp1['user_agent'], fp2['user_agent'])
        
    def test_browser_consistency(self):
        """Test browser consistency in fingerprints"""
        # Generate multiple fingerprints for same browser type
        chrome_fps = []
        
        for _ in range(5):
            fp = self.fingerprint_gen.generate_fingerprint(browser_type='chrome')
            chrome_fps.append(fp)
            
        # All should be Chrome
        for fp in chrome_fps:
            self.assertIn('chrome', fp['user_agent'].lower())
            
    def test_canvas_fingerprint(self):
        """Test canvas fingerprint generation"""
        canvas_fp = self.fingerprint_gen._generate_canvas_fingerprint()
        
        self.assertIsInstance(canvas_fp, str)
        self.assertEqual(len(canvas_fp), 32)  # MD5 hash length
        
    def test_webgl_fingerprint(self):
        """Test WebGL fingerprint generation"""
        webgl_fp = self.fingerprint_gen._generate_webgl_fingerprint()
        
        self.assertIsInstance(webgl_fp, dict)
        self.assertIn('vendor', webgl_fp)
        self.assertIn('renderer', webgl_fp)
        
    def test_font_detection(self):
        """Test font detection"""
        fonts = self.fingerprint_gen._detect_fonts()
        
        self.assertIsInstance(fonts, list)
        self.assertGreater(len(fonts), 0)
        
        # Common fonts should be present
        common_fonts = ['Arial', 'Times New Roman', 'Verdana']
        for font in common_fonts:
            self.assertIn(font, fonts)

class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for multiple components"""
    
    async def asyncSetUp(self):
        """Set up integration test"""
        self.browser_method = BrowserViewMethod()
        self.api_method = APIViewMethod()
        self.proxy_rotator = ProxyRotator()
        self.fingerprint_gen = DeviceFingerprintGenerator()
        
    async def test_complete_view_flow(self):
        """Test complete view flow with all components"""
        # Generate fingerprint
        fingerprint = self.fingerprint_gen.generate_fingerprint()
        
        # Setup proxy
        self.proxy_rotator.add_proxies(["http://test-proxy:8080"])
        proxy = self.proxy_rotator.get_next_proxy()
        
        # Configure browser with fingerprint and proxy
        self.browser_method.configure({
            'user_agent': fingerprint['user_agent'],
            'proxy': proxy,
            'screen_resolution': fingerprint['screen_resolution']
        })
        
        # This is a mock test - in real test would actually run browser
        success = self.browser_method.initialize_browser()
        self.assertTrue(success)
        
    async def test_fallback_mechanism(self):
        """Test fallback from API to browser method"""
        video_url = "https://tiktok.com/video/test"
        
        # Try API first
        api_result = self.api_method.send_view(video_url)
        
        if not api_result['success']:
            # Fallback to browser
            browser_result = self.browser_method.send_view(video_url)
            self.assertTrue(browser_result['success'])
            
    async def test_concurrent_operations(self):
        """Test concurrent operations with multiple methods"""
        import asyncio
        
        video_urls = [f"https://tiktok.com/video/{i}" for i in range(5)]
        
        # Run browser and API methods concurrently
        browser_tasks = []
        api_tasks = []
        
        for url in video_urls:
            browser_tasks.append(
                asyncio.to_thread(self.browser_method.send_view, url)
            )
            api_tasks.append(
                asyncio.to_thread(self.api_method.send_view, url)
            )
        
        # Execute concurrently
        browser_results = await asyncio.gather(*browser_tasks, return_exceptions=True)
        api_results = await asyncio.gather(*api_tasks, return_exceptions=True)
        
        # Verify results
        self.assertEqual(len(browser_results), 5)
        self.assertEqual(len(api_results), 5)
        
        # Check that at least some succeeded
        browser_success = sum(1 for r in browser_results if isinstance(r, dict) and r.get('success'))
        api_success = sum(1 for r in api_results if isinstance(r, dict) and r.get('success'))
        
        self.assertGreater(browser_success + api_success, 0)

class TestPerformance(unittest.TestCase):
    """Performance tests"""
    
    def test_browser_method_performance(self):
        """Test browser method performance"""
        import time
        
        method = BrowserViewMethod()
        
        start_time = time.time()
        
        # Test initialization performance
        with patch('selenium.webdriver.Chrome'):
            success = method.initialize_browser()
            
        init_time = time.time() - start_time
        
        self.assertTrue(success)
        self.assertLess(init_time, 5.0)  # Should initialize within 5 seconds
        
    def test_api_method_throughput(self):
        """Test API method throughput"""
        method = APIViewMethod()
        
        # Simulate batch processing
        start_time = time.time()
        
        with patch('requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status_code': 0}
            mock_session.return_value.post.return_value = mock_response
            
            # Send 10 views
            for _ in range(10):
                method.send_view("123")
                
        total_time = time.time() - start_time
        
        # Should handle at least 2 requests per second
        self.assertLess(total_time, 5.0)
        
    def test_memory_usage(self):
        """Test memory usage of components"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        initial_memory = process.memory_info().rss
        
        # Create multiple instances
        instances = []
        for _ in range(100):
            instances.append(DeviceFingerprintGenerator())
            
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # Less than 100MB
        
        # Cleanup
        del instances

class TestErrorRecovery(unittest.TestCase):
    """Test error recovery mechanisms"""
    
    def test_browser_crash_recovery(self):
        """Test browser crash recovery"""
        method = BrowserViewMethod()
        
        with patch('selenium.webdriver.Chrome') as mock_chrome:
            # Simulate crash on first attempt
            mock_driver = Mock()
            mock_driver.get.side_effect = [Exception("Browser crashed"), None]
            mock_chrome.return_value = mock_driver
            
            # Should retry and succeed
            result = method.send_view("https://tiktok.com/video/test", max_retries=2)
            
            self.assertTrue(result['success'])
            self.assertEqual(mock_driver.get.call_count, 2)
            
    def test_api_rate_limit_recovery(self):
        """Test API rate limit recovery"""
        method = APIViewMethod()
        
        with patch('requests.Session') as mock_session:
            # First request: rate limited
            mock_response1 = Mock()
            mock_response1.status_code = 429
            mock_response1.headers = {'Retry-After': '1'}
            
            # Second request: success
            mock_response2 = Mock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {'status_code': 0}
            
            mock_session.return_value.post.side_effect = [mock_response1, mock_response2]
            
            # Should retry after rate limit
            result = method.send_view("123", max_retries=2)
            
            self.assertTrue(result['success'])
            self.assertEqual(mock_session.return_value.post.call_count, 2)
            
    def test_network_failure_recovery(self):
        """Test network failure recovery"""
        method = APIViewMethod()
        
        with patch('requests.Session') as mock_session:
            # Simulate network failures
            mock_session.return_value.post.side_effect = [
                Exception("Network error"),
                Exception("Timeout"),
                Mock(status_code=200, json=lambda: {'status_code': 0})
            ]
            
            # Should retry and eventually succeed
            result = method.send_view("123", max_retries=3)
            
            self.assertTrue(result['success'])
            self.assertEqual(mock_session.return_value.post.call_count, 3)

def run_all_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBrowserViewMethod))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAPIViewMethod))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCloudViewMethod))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHybridAIMethod))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestProxyRotator))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDeviceFingerprint))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPerformance))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestErrorRecovery))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == '__main__':
    # Run tests
    test_result = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if test_result.wasSuccessful() else 1)