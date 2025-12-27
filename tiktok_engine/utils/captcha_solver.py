"""
Advanced Captcha Solving System for TikTok
"""
import asyncio
import aiohttp
import base64
from typing import Dict, List, Optional, Tuple
import json
import time
from PIL import Image
import io

class CaptchaSolver:
    def __init__(self, config: Dict):
        self.config = config
        self.services = {
            '2captcha': {
                'api_key': config.get('2captcha_api_key'),
                'url': 'http://2captcha.com',
                'balance_url': 'http://2captcha.com/res.php'
            },
            'anticaptcha': {
                'api_key': config.get('anticaptcha_api_key'),
                'url': 'https://api.anti-captcha.com',
                'balance_url': 'https://api.anti-captcha.com/getBalance'
            },
            'deathbycaptcha': {
                'username': config.get('dbc_username'),
                'password': config.get('dbc_password'),
                'url': 'http://api.dbcapi.me/api'
            }
        }
        
        self.service_priority = ['anticaptcha', '2captcha', 'deathbycaptcha']
        self.session = None
    
    async def initialize(self):
        """Initialize async session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
    
    async def solve_image_captcha(self, image_data: bytes, 
                                 service: str = 'auto') -> Optional[str]:
        """Solve image captcha"""
        if service == 'auto':
            for svc in self.service_priority:
                result = await self._solve_with_service(svc, image_data)
                if result:
                    return result
            return None
        else:
            return await self._solve_with_service(service, image_data)
    
    async def _solve_with_service(self, service: str, 
                                 image_data: bytes) -> Optional[str]:
        """Solve using specific service"""
        if service == '2captcha':
            return await self._solve_2captcha(image_data)
        elif service == 'anticaptcha':
            return await self._solve_anticaptcha(image_data)
        elif service == 'deathbycaptcha':
            return await self._solve_deathbycaptcha(image_data)
        return None
    
    async def _solve_2captcha(self, image_data: bytes) -> Optional[str]:
        """Solve using 2Captcha"""
        api_key = self.services['2captcha']['api_key']
        if not api_key:
            return None
        
        # Convert image to base64
        img_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Submit captcha
        submit_url = f"{self.services['2captcha']['url']}/in.php"
        data = {
            'key': api_key,
            'method': 'base64',
            'body': img_base64,
            'json': 1,
            'regsense': 1  # For TikTok style captchas
        }
        
        try:
            async with self.session.post(submit_url, data=data) as response:
                result = await response.json()
                
                if result.get('status') == 1:
                    captcha_id = result['request']
                    
                    # Wait for solution
                    for _ in range(60):  # Wait up to 60 seconds
                        await asyncio.sleep(5)
                        
                        check_url = f"{self.services['2captcha']['url']}/res.php"
                        params = {
                            'key': api_key,
                            'action': 'get',
                            'id': captcha_id,
                            'json': 1
                        }
                        
                        async with self.session.get(check_url, params=params) as check_res:
                            check_result = await check_res.json()
                            
                            if check_result.get('status') == 1:
                                return check_result['request']
                            elif check_result.get('status') == 0 and check_result.get('request') != 'CAPCHA_NOT_READY':
                                break
                    
                    return None
                else:
                    return None
                    
        except Exception as e:
            print(f"2Captcha error: {e}")
            return None
    
    async def _solve_anticaptcha(self, image_data: bytes) -> Optional[str]:
        """Solve using AntiCaptcha"""
        api_key = self.services['anticaptcha']['api_key']
        if not api_key:
            return None
        
        # Create task
        task_url = f"{self.services['anticaptcha']['url']}/createTask"
        
        task_data = {
            "clientKey": api_key,
            "task": {
                "type": "ImageToTextTask",
                "body": base64.b64encode(image_data).decode('utf-8'),
                "phrase": False,
                "case": False,
                "numeric": 0,  # 0 - any, 1 - numbers only, 2 - letters only
                "math": False,
                "minLength": 4,
                "maxLength": 6
            }
        }
        
        try:
            async with self.session.post(task_url, json=task_data) as response:
                result = await response.json()
                
                if result.get('errorId') == 0:
                    task_id = result['taskId']
                    
                    # Check result
                    result_url = f"{self.services['anticaptcha']['url']}/getTaskResult"
                    
                    for _ in range(60):  # Wait up to 60 seconds
                        await asyncio.sleep(5)
                        
                        result_data = {
                            "clientKey": api_key,
                            "taskId": task_id
                        }
                        
                        async with self.session.post(result_url, json=result_data) as result_res:
                            result_result = await result_res.json()
                            
                            if result_result.get('errorId') == 0:
                                if result_result['status'] == 'ready':
                                    return result_result['solution']['text']
                                elif result_result['status'] == 'processing':
                                    continue
                                else:
                                    break
                    
                    return None
                else:
                    return None
                    
        except Exception as e:
            print(f"AntiCaptcha error: {e}")
            return None
    
    async def _solve_deathbycaptcha(self, image_data: bytes) -> Optional[str]:
        """Solve using DeathByCaptcha"""
        username = self.services['deathbycaptcha'].get('username')
        password = self.services['deathbycaptcha'].get('password')
        
        if not username or not password:
            return None
        
        auth = aiohttp.BasicAuth(username, password)
        
        try:
            # Upload captcha
            upload_url = f"{self.services['deathbycaptcha']['url']}/captcha"
            
            form_data = aiohttp.FormData()
            form_data.add_field('captchafile', 
                              base64.b64encode(image_data).decode('utf-8'))
            
            async with self.session.post(upload_url, auth=auth, data=form_data) as response:
                result = await response.json()
                
                if result.get('is_correct'):
                    captcha_id = result['captcha']
                    
                    # Get result
                    result_url = f"{self.services['deathbycaptcha']['url']}/captcha/{captcha_id}"
                    
                    for _ in range(60):  # Wait up to 60 seconds
                        await asyncio.sleep(5)
                        
                        async with self.session.get(result_url, auth=auth) as result_res:
                            captcha_result = await result_res.json()
                            
                            if captcha_result.get('text'):
                                return captcha_result['text']
                            elif captcha_result.get('status') == 'completed':
                                continue
                    
                    return None
                else:
                    return None
                    
        except Exception as e:
            print(f"DeathByCaptcha error: {e}")
            return None
    
    async def solve_recaptcha_v2(self, site_key: str, page_url: str,
                                service: str = 'auto') -> Optional[str]:
        """Solve reCAPTCHA v2"""
        if service == 'auto':
            for svc in self.service_priority:
                result = await self._solve_recaptcha_with_service(svc, site_key, page_url)
                if result:
                    return result
            return None
        else:
            return await self._solve_recaptcha_with_service(service, site_key, page_url)
    
    async def _solve_recaptcha_with_service(self, service: str,
                                          site_key: str, page_url: str) -> Optional[str]:
        """Solve reCAPTCHA with specific service"""
        if service == '2captcha':
            return await self._solve_recaptcha_2captcha(site_key, page_url)
        elif service == 'anticaptcha':
            return await self._solve_recaptcha_anticaptcha(site_key, page_url)
        return None
    
    async def _solve_recaptcha_2captcha(self, site_key: str, 
                                       page_url: str) -> Optional[str]:
        """Solve reCAPTCHA with 2Captcha"""
        api_key = self.services['2captcha']['api_key']
        if not api_key:
            return None
        
        submit_url = f"{self.services['2captcha']['url']}/in.php"
        data = {
            'key': api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1,
            'invisible': 0
        }
        
        try:
            async with self.session.post(submit_url, data=data) as response:
                result = await response.json()
                
                if result.get('status') == 1:
                    captcha_id = result['request']
                    
                    # Wait for solution
                    for _ in range(120):  # Wait up to 120 seconds for reCAPTCHA
                        await asyncio.sleep(5)
                        
                        check_url = f"{self.services['2captcha']['url']}/res.php"
                        params = {
                            'key': api_key,
                            'action': 'get',
                            'id': captcha_id,
                            'json': 1
                        }
                        
                        async with self.session.get(check_url, params=params) as check_res:
                            check_result = await check_res.json()
                            
                            if check_result.get('status') == 1:
                                return check_result['request']
                            elif check_result.get('status') == 0 and check_result.get('request') != 'CAPCHA_NOT_READY':
                                break
                    
                    return None
                else:
                    return None
                    
        except Exception as e:
            print(f"2Captcha reCAPTCHA error: {e}")
            return None
    
    async def _solve_recaptcha_anticaptcha(self, site_key: str,
                                         page_url: str) -> Optional[str]:
        """Solve reCAPTCHA with AntiCaptcha"""
        api_key = self.services['anticaptcha']['api_key']
        if not api_key:
            return None
        
        task_url = f"{self.services['anticaptcha']['url']}/createTask"
        
        task_data = {
            "clientKey": api_key,
            "task": {
                "type": "NoCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": site_key
            }
        }
        
        try:
            async with self.session.post(task_url, json=task_data) as response:
                result = await response.json()
                
                if result.get('errorId') == 0:
                    task_id = result['taskId']
                    
                    # Check result
                    result_url = f"{self.services['anticaptcha']['url']}/getTaskResult"
                    
                    for _ in range(120):  # Wait up to 120 seconds
                        await asyncio.sleep(5)
                        
                        result_data = {
                            "clientKey": api_key,
                            "taskId": task_id
                        }
                        
                        async with self.session.post(result_url, json=result_data) as result_res:
                            result_result = await result_res.json()
                            
                            if result_result.get('errorId') == 0:
                                if result_result['status'] == 'ready':
                                    return result_result['solution']['gRecaptchaResponse']
                                elif result_result['status'] == 'processing':
                                    continue
                                else:
                                    break
                    
                    return None
                else:
                    return None
                    
        except Exception as e:
            print(f"AntiCaptcha reCAPTCHA error: {e}")
            return None
    
    async def solve_hcaptcha(self, site_key: str, page_url: str,
                            service: str = 'auto') -> Optional[str]:
        """Solve hCaptcha"""
        if service == 'auto':
            for svc in ['2captcha', 'anticaptcha']:
                result = await self._solve_hcaptcha_with_service(svc, site_key, page_url)
                if result:
                    return result
            return None
        else:
            return await self._solve_hcaptcha_with_service(service, site_key, page_url)
    
    async def _solve_hcaptcha_with_service(self, service: str,
                                         site_key: str, page_url: str) -> Optional[str]:
        """Solve hCaptcha with specific service"""
        if service == '2captcha':
            api_key = self.services['2captcha']['api_key']
            if not api_key:
                return None
            
            submit_url = f"{self.services['2captcha']['url']}/in.php"
            data = {
                'key': api_key,
                'method': 'hcaptcha',
                'sitekey': site_key,
                'pageurl': page_url,
                'json': 1
            }
            
            try:
                async with self.session.post(submit_url, data=data) as response:
                    result = await response.json()
                    
                    if result.get('status') == 1:
                        captcha_id = result['request']
                        
                        # Wait for solution
                        for _ in range(120):
                            await asyncio.sleep(5)
                            
                            check_url = f"{self.services['2captcha']['url']}/res.php"
                            params = {
                                'key': api_key,
                                'action': 'get',
                                'id': captcha_id,
                                'json': 1
                            }
                            
                            async with self.session.get(check_url, params=params) as check_res:
                                check_result = await check_res.json()
                                
                                if check_result.get('status') == 1:
                                    return check_result['request']
                                elif check_result.get('status') == 0 and check_result.get('request') != 'CAPCHA_NOT_READY':
                                    break
                        
                        return None
                    else:
                        return None
                        
            except Exception as e:
                print(f"2Captcha hCaptcha error: {e}")
                return None
        
        return None
    
    async def get_balance(self, service: str) -> Optional[float]:
        """Get service balance"""
        if service == '2captcha':
            api_key = self.services['2captcha']['api_key']
            if not api_key:
                return None
            
            url = f"{self.services['2captcha']['balance_url']}"
            params = {
                'key': api_key,
                'action': 'getbalance',
                'json': 1
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    result = await response.json()
                    if result.get('status') == 1:
                        return float(result['request'])
            except:
                pass
        
        elif service == 'anticaptcha':
            api_key = self.services['anticaptcha']['api_key']
            if not api_key:
                return None
            
            url = f"{self.services['anticaptcha']['balance_url']}"
            data = {
                "clientKey": api_key
            }
            
            try:
                async with self.session.post(url, json=data) as response:
                    result = await response.json()
                    if result.get('errorId') == 0:
                        return result['balance']
            except:
                pass
        
        return None
    
    async def report_bad(self, captcha_id: str, service: str) -> bool:
        """Report bad captcha solution"""
        if service == '2captcha':
            api_key = self.services['2captcha']['api_key']
            if not api_key:
                return False
            
            url = f"{self.services['2captcha']['url']}/res.php"
            params = {
                'key': api_key,
                'action': 'reportbad',
                'id': captcha_id,
                'json': 1
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    result = await response.json()
                    return result.get('status') == 1
            except:
                return False
        
        return False
    
    async def solve_slider_captcha(self, image_data: bytes, 
                                  slider_bg: bytes) -> Optional[Dict]:
        """Solve slider captcha (TikTok specific)"""
        # This is a simplified version
        # In production, use ML model or external service
        
        try:
            # Load images
            slider_img = Image.open(io.BytesIO(image_data))
            bg_img = Image.open(io.BytesIO(slider_bg))
            
            # Simple template matching (very basic)
            # In reality, use OpenCV or other computer vision
            
            width, height = slider_img.size
            bg_width, bg_height = bg_img.size
            
            # Calculate required slide distance
            # This is mock logic
            slide_distance = width * 0.7  # 70% of slider width
            
            return {
                'distance': int(slide_distance),
                'track_length': bg_width,
                'required_movement': slide_distance / bg_width * 100
            }
            
        except Exception as e:
            print(f"Slider captcha error: {e}")
            return None
    
    async def solve_audio_captcha(self, audio_data: bytes) -> Optional[str]:
        """Solve audio captcha"""
        # Convert audio to text using speech recognition
        # This is a placeholder
        
        try:
            # In production, use speech recognition service
            # or external captcha solving service
            
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            # Save audio to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_data)
                audio_file = f.name
            
            # Recognize
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
                
                import os
                os.unlink(audio_file)
                
                return text
                
        except Exception as e:
            print(f"Audio captcha error: {e}")
            return None
    
    def preprocess_captcha_image(self, image_data: bytes) -> bytes:
        """Preprocess captcha image for better recognition"""
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to grayscale
            if img.mode != 'L':
                img = img.convert('L')
            
            # Enhance contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Remove noise (simple threshold)
            import numpy as np
            img_array = np.array(img)
            img_array = np.where(img_array > 128, 255, 0).astype(np.uint8)
            
            img = Image.fromarray(img_array)
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            print(f"Image preprocessing error: {e}")
            return image_data
    
    async def auto_solve_tiktok_captcha(self, page_html: str, 
                                       page_url: str) -> Optional[Dict]:
        """Auto-detect and solve TikTok captcha"""
        captcha_info = {}
        
        # Detect captcha type
        if 'recaptcha' in page_html.lower() or 'g-recaptcha' in page_html:
            # Find reCAPTCHA site key
            import re
            recaptcha_match = re.search(r'sitekey=["\']([^"\']+)["\']', page_html)
            if recaptcha_match:
                site_key = recaptcha_match.group(1)
                solution = await self.solve_recaptcha_v2(site_key, page_url)
                if solution:
                    captcha_info['type'] = 'recaptcha'
                    captcha_info['solution'] = solution
                    captcha_info['site_key'] = site_key
        
        elif 'hcaptcha' in page_html.lower():
            # Find hCaptcha site key
            import re
            hcaptcha_match = re.search(r'data-sitekey=["\']([^"\']+)["\']', page_html)
            if hcaptcha_match:
                site_key = hcaptcha_match.group(1)
                solution = await self.solve_hcaptcha(site_key, page_url)
                if solution:
                    captcha_info['type'] = 'hcaptcha'
                    captcha_info['solution'] = solution
                    captcha_info['site_key'] = site_key
        
        # Check for image captcha
        elif 'captcha' in page_html.lower() and 'img' in page_html.lower():
            # Extract captcha image URL
            import re
            img_match = re.search(r'<img[^>]*src=["\']([^"\']*captcha[^"\']*)["\']', page_html, re.I)
            if img_match:
                img_url = img_match.group(1)
                
                # Download image
                try:
                    async with self.session.get(img_url) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            
                            # Preprocess
                            processed = self.preprocess_captcha_image(image_data)
                            
                            # Solve
                            solution = await self.solve_image_captcha(processed)
                            if solution:
                                captcha_info['type'] = 'image'
                                captcha_info['solution'] = solution
                                captcha_info['image_url'] = img_url
                except:
                    pass
        
        return captcha_info if captcha_info else None