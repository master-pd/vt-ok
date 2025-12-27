"""
Auto Update System for VT ULTRA PRO
"""
import asyncio
import aiohttp
import json
import os
import sys
import subprocess
import hashlib
import tempfile
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import platform
import shutil

class AutoUpdateSystem:
    def __init__(self, config_path: str = 'config/update_config.json'):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        
        # Update repositories
        self.repositories = {
            'main': 'https://api.github.com/repos/vtultrapro/vt-ultra-pro/releases/latest',
            'ai_models': 'https://api.github.com/repos/vtultrapro/ai-models/releases/latest',
            'view_methods': 'https://api.github.com/repos/vtultrapro/view-methods/releases/latest'
        }
        
        # Current version
        self.current_version = self._get_current_version()
        
        # Update status
        self.update_status = {
            'last_check': None,
            'available_updates': [],
            'pending_updates': [],
            'update_history': []
        }
        
    def _load_config(self, config_path: str) -> Dict:
        """Load update configuration"""
        default_config = {
            'auto_check': True,
            'auto_install': False,
            'check_interval': 3600,  # 1 hour
            'backup_before_update': True,
            'notify_on_update': True,
            'update_channels': ['stable'],  # stable, beta, alpha
            'excluded_files': ['config/*', 'database/*', 'logs/*'],
            'rollback_on_failure': True,
            'max_rollback_versions': 5
        }
        
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except:
            pass
        
        return default_config
    
    def _setup_logger(self):
        """Setup update logger"""
        logger = logging.getLogger('auto_update')
        logger.setLevel(logging.INFO)
        
        # File handler
        os.makedirs('logs/updates', exist_ok=True)
        file_handler = logging.FileHandler('logs/updates/update.log')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )
        logger.addHandler(console_handler)
        
        return logger
    
    def _get_current_version(self) -> Dict:
        """Get current version information"""
        version_file = 'VERSION.json'
        
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default version
        return {
            'version': '1.0.0',
            'build': 'unknown',
            'commit': 'unknown',
            'release_date': '2024-01-01',
            'components': {}
        }
    
    async def check_for_updates(self) -> List[Dict]:
        """Check for available updates"""
        self.logger.info("Checking for updates...")
        
        available_updates = []
        
        async with aiohttp.ClientSession() as session:
            for repo_name, repo_url in self.repositories.items():
                try:
                    update = await self._check_repository_update(session, repo_name, repo_url)
                    if update:
                        available_updates.append(update)
                        self.logger.info(f"Update available for {repo_name}: {update['version']}")
                except Exception as e:
                    self.logger.error(f"Error checking {repo_name}: {e}")
        
        self.update_status['last_check'] = datetime.now().isoformat()
        self.update_status['available_updates'] = available_updates
        
        # Save update status
        self._save_update_status()
        
        return available_updates
    
    async def _check_repository_update(self, session: aiohttp.ClientSession,
                                      repo_name: str, repo_url: str) -> Optional[Dict]:
        """Check specific repository for updates"""
        headers = {
            'User-Agent': 'VT-ULTRA-PRO-Updater/1.0',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        async with session.get(repo_url, headers=headers) as response:
            if response.status == 200:
                release_data = await response.json()
                
                # Check if newer version
                latest_version = release_data['tag_name'].lstrip('v')
                current_version = self.current_version.get(repo_name, {}).get('version', '0.0.0')
                
                if self._compare_versions(latest_version, current_version) > 0:
                    return {
                        'repository': repo_name,
                        'current_version': current_version,
                        'latest_version': latest_version,
                        'release_notes': release_data.get('body', ''),
                        'download_url': release_data['assets'][0]['browser_download_url'] if release_data.get('assets') else None,
                        'published_at': release_data['published_at'],
                        'prerelease': release_data.get('prerelease', False)
                    }
        
        return None
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare version strings"""
        def parse_version(version: str):
            return tuple(map(int, version.split('.')))
        
        try:
            v1_parts = parse_version(v1)
            v2_parts = parse_version(v2)
            
            if v1_parts > v2_parts:
                return 1
            elif v1_parts < v2_parts:
                return -1
            else:
                return 0
        except:
            return 0
    
    async def download_update(self, update_info: Dict, 
                            download_path: Optional[str] = None) -> str:
        """Download update package"""
        if not update_info.get('download_url'):
            raise ValueError("No download URL available")
        
        if download_path is None:
            download_path = tempfile.mkdtemp(prefix='vt_update_')
        
        os.makedirs(download_path, exist_ok=True)
        
        download_file = os.path.join(download_path, f"update_{update_info['repository']}.zip")
        
        self.logger.info(f"Downloading update for {update_info['repository']}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(update_info['download_url']) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(download_file, 'wb') as f:
                        downloaded = 0
                        
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Log progress
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                if int(percent) % 10 == 0:
                                    self.logger.info(f"Download progress: {percent:.1f}%")
                
                    self.logger.info(f"Download completed: {download_file}")
                    
                    # Verify download
                    if self._verify_download(download_file, response):
                        return download_file
                    else:
                        raise ValueError("Download verification failed")
                else:
                    raise ValueError(f"Download failed: {response.status}")
    
    def _verify_download(self, file_path: str, response: aiohttp.ClientResponse) -> bool:
        """Verify downloaded file"""
        # Check file size
        expected_size = int(response.headers.get('content-length', 0))
        actual_size = os.path.getsize(file_path)
        
        if expected_size > 0 and actual_size != expected_size:
            self.logger.error(f"File size mismatch: expected {expected_size}, got {actual_size}")
            return False
        
        # TODO: Add checksum verification if provided
        return True
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create system backup before update"""
        if not self.config['backup_before_update']:
            return ""
        
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}"
        
        backup_dir = os.path.join('backups', backup_name)
        os.makedirs(backup_dir, exist_ok=True)
        
        self.logger.info(f"Creating backup: {backup_name}")
        
        # Backup important directories
        backup_items = [
            ('config', os.path.join(backup_dir, 'config')),
            ('database', os.path.join(backup_dir, 'database')),
            ('logs', os.path.join(backup_dir, 'logs')),
            ('models', os.path.join(backup_dir, 'models'))
        ]
        
        for source, target in backup_items:
            if os.path.exists(source):
                try:
                    if os.path.isdir(source):
                        shutil.copytree(source, target)
                    else:
                        shutil.copy2(source, target)
                    self.logger.info(f"Backed up: {source}")
                except Exception as e:
                    self.logger.error(f"Failed to backup {source}: {e}")
        
        # Create backup manifest
        manifest = {
            'backup_name': backup_name,
            'created_at': datetime.now().isoformat(),
            'version': self.current_version,
            'items': [source for source, _ in backup_items if os.path.exists(source)]
        }
        
        with open(os.path.join(backup_dir, 'manifest.json'), 'w') as f:
            json.dump(manifest, f, indent=2)
        
        self.logger.info(f"Backup created: {backup_dir}")
        return backup_dir
    
    def install_update(self, update_file: str, 
                      update_info: Dict) -> Dict:
        """Install downloaded update"""
        self.logger.info(f"Installing update: {update_info['repository']}")
        
        # Create backup
        backup_dir = self.create_backup()
        
        try:
            # Extract update
            extract_dir = tempfile.mkdtemp(prefix='vt_extract_')
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Read update instructions
            instructions_file = os.path.join(extract_dir, 'update_instructions.json')
            if os.path.exists(instructions_file):
                with open(instructions_file, 'r') as f:
                    instructions = json.load(f)
            else:
                instructions = self._generate_default_instructions(extract_dir)
            
            # Execute pre-install scripts
            self._execute_scripts(extract_dir, 'pre_install')
            
            # Apply file updates
            self._apply_file_updates(extract_dir, instructions.get('files', []))
            
            # Execute post-install scripts
            self._execute_scripts(extract_dir, 'post_install')
            
            # Update version information
            self._update_version_info(update_info)
            
            # Cleanup
            shutil.rmtree(extract_dir)
            
            # Record update
            update_record = {
                'repository': update_info['repository'],
                'from_version': update_info['current_version'],
                'to_version': update_info['latest_version'],
                'installed_at': datetime.now().isoformat(),
                'backup_location': backup_dir,
                'status': 'success'
            }
            
            self.update_status['update_history'].append(update_record)
            self._save_update_status()
            
            self.logger.info(f"Update installed successfully: {update_info['latest_version']}")
            
            return {
                'success': True,
                'message': 'Update installed successfully',
                'update_record': update_record
            }
            
        except Exception as e:
            self.logger.error(f"Update installation failed: {e}")
            
            # Rollback if configured
            if self.config['rollback_on_failure'] and backup_dir:
                self.logger.info("Attempting rollback...")
                rollback_result = self.rollback_update(backup_dir)
                
                if rollback_result['success']:
                    self.logger.info("Rollback successful")
                else:
                    self.logger.error("Rollback failed")
            
            # Record failed update
            update_record = {
                'repository': update_info['repository'],
                'from_version': update_info['current_version'],
                'to_version': update_info['latest_version'],
                'installed_at': datetime.now().isoformat(),
                'error': str(e),
                'status': 'failed'
            }
            
            self.update_status['update_history'].append(update_record)
            self._save_update_status()
            
            return {
                'success': False,
                'error': str(e),
                'update_record': update_record
            }
    
    def _generate_default_instructions(self, extract_dir: str) -> Dict:
        """Generate default update instructions"""
        files = []
        
        # Walk through extracted directory
        for root, dirs, filenames in os.walk(extract_dir):
            for filename in filenames:
                if filename.endswith('.py') or filename.endswith('.json') or filename.endswith('.yaml'):
                    rel_path = os.path.relpath(os.path.join(root, filename), extract_dir)
                    files.append({
                        'source': rel_path,
                        'destination': rel_path,
                        'action': 'copy'  # copy, move, delete, patch
                    })
        
        return {
            'files': files,
            'pre_install': [],
            'post_install': [
                {
                    'type': 'command',
                    'command': 'pip install -r requirements.txt --upgrade'
                },
                {
                    'type': 'restart',
                    'service': 'vt_ultra_pro'
                }
            ]
        }
    
    def _apply_file_updates(self, extract_dir: str, file_updates: List[Dict]):
        """Apply file updates from instructions"""
        for file_update in file_updates:
            source = os.path.join(extract_dir, file_update['source'])
            destination = file_update['destination']
            action = file_update.get('action', 'copy')
            
            # Handle exclusions
            if self._is_excluded(destination):
                self.logger.info(f"Skipping excluded file: {destination}")
                continue
            
            try:
                if action == 'copy':
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    
                    if os.path.exists(destination):
                        # Create backup of existing file
                        backup_path = f"{destination}.backup"
                        shutil.copy2(destination, backup_path)
                    
                    shutil.copy2(source, destination)
                    self.logger.info(f"Copied: {destination}")
                    
                elif action == 'move':
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    shutil.move(source, destination)
                    self.logger.info(f"Moved: {destination}")
                    
                elif action == 'delete':
                    if os.path.exists(destination):
                        os.remove(destination)
                        self.logger.info(f"Deleted: {destination}")
                    
                elif action == 'patch':
                    self._apply_patch(source, destination)
                    
            except Exception as e:
                self.logger.error(f"Failed to {action} {destination}: {e}")
                raise
    
    def _is_excluded(self, file_path: str) -> bool:
        """Check if file is excluded from updates"""
        for pattern in self.config['excluded_files']:
            if file_path.startswith(pattern.rstrip('*')):
                return True
        return False
    
    def _apply_patch(self, patch_file: str, target_file: str):
        """Apply patch to file"""
        # This is a simplified patch system
        # In production, use proper patch library
        
        if not os.path.exists(target_file):
            self.logger.warning(f"Target file not found for patch: {target_file}")
            return
        
        with open(patch_file, 'r') as pf, open(target_file, 'r') as tf:
            patch_content = pf.read()
            target_content = tf.read()
        
        # Simple string replacement for demonstration
        # Real implementation would use diff/patch
        updated_content = target_content  # Placeholder
        
        with open(target_file, 'w') as f:
            f.write(updated_content)
        
        self.logger.info(f"Patched: {target_file}")
    
    def _execute_scripts(self, extract_dir: str, script_type: str):
        """Execute pre/post install scripts"""
        scripts_file = os.path.join(extract_dir, f'{script_type}_scripts.json')
        
        if not os.path.exists(scripts_file):
            return
        
        with open(scripts_file, 'r') as f:
            scripts = json.load(f)
        
        for script in scripts:
            script_type = script.get('type', 'command')
            
            if script_type == 'command':
                command = script['command']
                self.logger.info(f"Executing command: {command}")
                
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        cwd=os.getcwd()
                    )
                    
                    if result.returncode != 0:
                        self.logger.error(f"Command failed: {result.stderr}")
                        raise RuntimeError(f"Command failed: {command}")
                    
                    self.logger.info(f"Command output: {result.stdout}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to execute command: {e}")
                    raise
            
            elif script_type == 'python':
                script_file = os.path.join(extract_dir, script['file'])
                self.logger.info(f"Executing Python script: {script_file}")
                
                try:
                    # Add extract_dir to path temporarily
                    sys.path.insert(0, extract_dir)
                    
                    with open(script_file, 'r') as f:
                        script_code = f.read()
                    
                    exec(script_code, {
                        '__file__': script_file,
                        'extract_dir': extract_dir,
                        'current_dir': os.getcwd()
                    })
                    
                    sys.path.remove(extract_dir)
                    
                except Exception as e:
                    self.logger.error(f"Python script failed: {e}")
                    raise
            
            elif script_type == 'restart':
                service = script.get('service')
                self.logger.info(f"Restarting service: {service}")
                
                # Service restart logic would go here
                # This is platform-dependent
    
    def _update_version_info(self, update_info: Dict):
        """Update version information"""
        version_file = 'VERSION.json'
        
        # Update current version
        if update_info['repository'] == 'main':
            self.current_version['version'] = update_info['latest_version']
            self.current_version['release_date'] = datetime.now().isoformat()
        else:
            if 'components' not in self.current_version:
                self.current_version['components'] = {}
            
            self.current_version['components'][update_info['repository']] = {
                'version': update_info['latest_version'],
                'updated_at': datetime.now().isoformat()
            }
        
        # Save version file
        with open(version_file, 'w') as f:
            json.dump(self.current_version, f, indent=2)
    
    def rollback_update(self, backup_dir: str) -> Dict:
        """Rollback to previous version using backup"""
        try:
            # Read backup manifest
            manifest_file = os.path.join(backup_dir, 'manifest.json')
            
            if not os.path.exists(manifest_file):
                return {'success': False, 'error': 'Backup manifest not found'}
            
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            self.logger.info(f"Rolling back to backup: {manifest['backup_name']}")
            
            # Restore backed up items
            for item in manifest.get('items', []):
                backup_path = os.path.join(backup_dir, item)
                if os.path.exists(backup_path):
                    if os.path.isdir(backup_path):
                        if os.path.exists(item):
                            shutil.rmtree(item)
                        shutil.copytree(backup_path, item)
                    else:
                        shutil.copy2(backup_path, item)
                    
                    self.logger.info(f"Restored: {item}")
            
            # Restore version
            if 'version' in manifest:
                with open('VERSION.json', 'w') as f:
                    json.dump(manifest['version'], f, indent=2)
                self.current_version = manifest['version']
            
            # Record rollback
            rollback_record = {
                'backup_name': manifest['backup_name'],
                'rolled_back_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
            self.update_status.setdefault('rollback_history', []).append(rollback_record)
            self._save_update_status()
            
            return {
                'success': True,
                'message': f"Rolled back to {manifest['backup_name']}",
                'rollback_record': rollback_record
            }
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_available_rollbacks(self) -> List[Dict]:
        """Get available rollback points"""
        rollbacks = []
        backups_dir = 'backups'
        
        if os.path.exists(backups_dir):
            for backup_name in sorted(os.listdir(backups_dir), reverse=True):
                backup_path = os.path.join(backups_dir, backup_name)
                manifest_file = os.path.join(backup_path, 'manifest.json')
                
                if os.path.exists(manifest_file):
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                        
                        rollbacks.append({
                            'name': backup_name,
                            'created_at': manifest.get('created_at'),
                            'version': manifest.get('version', {}).get('version', 'unknown'),
                            'path': backup_path,
                            'size': self._get_directory_size(backup_path)
                        })
                    except:
                        pass
        
        # Limit number of rollbacks
        if self.config['max_rollback_versions']:
            rollbacks = rollbacks[:self.config['max_rollback_versions']]
        
        return rollbacks
    
    def _get_directory_size(self, directory: str) -> int:
        """Get directory size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    def _save_update_status(self):
        """Save update status to file"""
        status_file = 'logs/updates/update_status.json'
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        
        with open(status_file, 'w') as f:
            json.dump(self.update_status, f, indent=2, default=str)
    
    def load_update_status(self) -> Dict:
        """Load update status from file"""
        status_file = 'logs/updates/update_status.json'
        
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    self.update_status = json.load(f)
            except:
                pass
        
        return self.update_status
    
    async def auto_update_loop(self):
        """Main auto-update loop"""
        self.logger.info("Auto-update loop started")
        
        while True:
            try:
                # Check for updates
                if self.config['auto_check']:
                    updates = await self.check_for_updates()
                    
                    if updates and self.config['auto_install']:
                        for update in updates:
                            # Skip pre-releases if not in beta channel
                            if update.get('prerelease') and 'beta' not in self.config['update_channels']:
                                continue
                            
                            self.logger.info(f"Auto-installing update: {update['repository']}")
                            
                            # Download and install
                            try:
                                update_file = await self.download_update(update)
                                result = self.install_update(update_file, update)
                                
                                if result['success']:
                                    self.logger.info("Auto-update successful")
                                    
                                    # Notify if configured
                                    if self.config['notify_on_update']:
                                        self._send_update_notification(update, 'installed')
                                else:
                                    self.logger.error(f"Auto-update failed: {result.get('error')}")
                            
                            except Exception as e:
                                self.logger.error(f"Auto-update error: {e}")
                
                # Wait for next check
                await asyncio.sleep(self.config['check_interval'])
                
            except asyncio.CancelledError:
                self.logger.info("Auto-update loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in auto-update loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    def _send_update_notification(self, update_info: Dict, action: str):
        """Send update notification"""
        # This would send email, push notification, etc.
        # For now, just log it
        
        message = f"Update {action}: {update_info['repository']} from {update_info['current_version']} to {update_info['latest_version']}"
        self.logger.info(f"Notification: {message}")
    
    def verify_system_integrity(self) -> Dict:
        """Verify system integrity"""
        self.logger.info("Verifying system integrity...")
        
        integrity_report = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'issues': [],
            'status': 'healthy'
        }
        
        # Check required files
        required_files = [
            'main.py',
            'requirements.txt',
            'config/config.yaml',
            'VERSION.json'
        ]
        
        for file_path in required_files:
            check_result = {
                'file': file_path,
                'exists': os.path.exists(file_path),
                'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'readable': os.access(file_path, os.R_OK) if os.path.exists(file_path) else False
            }
            
            integrity_report['checks'].append(check_result)
            
            if not check_result['exists']:
                integrity_report['issues'].append(f"Missing file: {file_path}")
                integrity_report['status'] = 'unhealthy'
        
        # Check directory permissions
        required_dirs = [
            'config',
            'database',
            'logs',
            'models'
        ]
        
        for dir_path in required_dirs:
            if os.path.exists(dir_path):
                check_result = {
                    'directory': dir_path,
                    'writable': os.access(dir_path, os.W_OK)
                }
                
                integrity_report['checks'].append(check_result)
                
                if not check_result['writable']:
                    integrity_report['issues'].append(f"Directory not writable: {dir_path}")
                    integrity_report['status'] = 'warning'
        
        # Check Python dependencies
        try:
            import pkg_resources
            
            with open('requirements.txt', 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            for req in requirements[:10]:  # Check first 10 to avoid being too slow
                try:
                    pkg_resources.require(req)
                    integrity_report['checks'].append({
                        'dependency': req,
                        'installed': True
                    })
                except pkg_resources.DistributionNotFound:
                    integrity_report['issues'].append(f"Missing dependency: {req}")
                    integrity_report['status'] = 'unhealthy'
                except pkg_resources.VersionConflict:
                    integrity_report['issues'].append(f"Dependency version conflict: {req}")
                    integrity_report['status'] = 'warning'
        
        except Exception as e:
            integrity_report['issues'].append(f"Dependency check error: {e}")
            integrity_report['status'] = 'warning'
        
        self.logger.info(f"Integrity check completed: {integrity_report['status']}")
        return integrity_report
    
    def cleanup_old_backups(self):
        """Cleanup old backups"""
        backups_dir = 'backups'
        
        if not os.path.exists(backups_dir):
            return
        
        backups = []
        for backup_name in os.listdir(backups_dir):
            backup_path = os.path.join(backups_dir, backup_name)
            if os.path.isdir(backup_path):
                created_time = os.path.getctime(backup_path)
                backups.append((backup_path, created_time))
        
        # Sort by creation time (oldest first)
        backups.sort(key=lambda x: x[1])
        
        # Keep only most recent N backups
        keep_count = self.config.get('max_rollback_versions', 5)
        if len(backups) > keep_count:
            for backup_path, _ in backups[:-keep_count]:
                try:
                    shutil.rmtree(backup_path)
                    self.logger.info(f"Removed old backup: {os.path.basename(backup_path)}")
                except Exception as e:
                    self.logger.error(f"Failed to remove backup {backup_path}: {e}")
    
    def get_update_report(self) -> Dict:
        """Generate update report"""
        return {
            'current_version': self.current_version,
            'update_status': self.update_status,
            'available_updates': self.update_status.get('available_updates', []),
            'last_check': self.update_status.get('last_check'),
            'system_integrity': self.verify_system_integrity(),
            'available_rollbacks': self.get_available_rollbacks()
        }

# Command-line interface
def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VT ULTRA PRO Auto Update System')
    parser.add_argument('command', choices=[
        'check', 'download', 'install', 'rollback',
        'status', 'verify', 'cleanup', 'daemon'
    ], help='Command to execute')
    
    parser.add_argument('--repository', help='Specific repository')
    parser.add_argument('--backup', help='Backup name for rollback')
    parser.add_argument('--config', default='config/update_config.json',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    # Initialize update system
    update_system = AutoUpdateSystem(args.config)
    
    if args.command == 'check':
        # Check for updates
        updates = asyncio.run(update_system.check_for_updates())
        
        if updates:
            print(f"Found {len(updates)} updates:")
            for update in updates:
                print(f"  - {update['repository']}: {update['current_version']} -> {update['latest_version']}")
        else:
            print("No updates available")
    
    elif args.command == 'download':
        # Download specific update
        updates = asyncio.run(update_system.check_for_updates())
        
        if args.repository:
            update = next((u for u in updates if u['repository'] == args.repository), None)
            if update:
                update_file = asyncio.run(update_system.download_update(update))
                print(f"Downloaded: {update_file}")
            else:
                print(f"No update found for repository: {args.repository}")
        else:
            print("Please specify repository with --repository")
    
    elif args.command == 'install':
        # Install update
        updates = asyncio.run(update_system.check_for_updates())
        
        if args.repository:
            update = next((u for u in updates if u['repository'] == args.repository), None)
            if update:
                update_file = asyncio.run(update_system.download_update(update))
                result = update_system.install_update(update_file, update)
                print(f"Installation result: {result['success']}")
                if not result['success']:
                    print(f"Error: {result.get('error')}")
            else:
                print(f"No update found for repository: {args.repository}")
        else:
            print("Please specify repository with --repository")
    
    elif args.command == 'rollback':
        # Rollback to backup
        if args.backup:
            result = update_system.rollback_update(os.path.join('backups', args.backup))
            print(f"Rollback result: {result['success']}")
            if not result['success']:
                print(f"Error: {result.get('error')}")
        else:
            # Show available rollbacks
            rollbacks = update_system.get_available_rollbacks()
            print("Available rollbacks:")
            for rb in rollbacks:
                print(f"  - {rb['name']} (v{rb['version']}, {rb['created_at']})")
    
    elif args.command == 'status':
        # Show update status
        report = update_system.get_update_report()
        print(json.dumps(report, indent=2))
    
    elif args.command == 'verify':
        # Verify system integrity
        integrity = update_system.verify_system_integrity()
        print(json.dumps(integrity, indent=2))
    
    elif args.command == 'cleanup':
        # Cleanup old backups
        update_system.cleanup_old_backups()
        print("Cleanup completed")
    
    elif args.command == 'daemon':
        # Run as daemon
        print("Starting auto-update daemon...")
        asyncio.run(update_system.auto_update_loop())

if __name__ == '__main__':
    main()