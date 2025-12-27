"""
Heroku Deployment Automation for VT ULTRA PRO
"""

import logging
import os
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path
import heroku3
import requests

logger = logging.getLogger(__name__)

class HerokuDeployManager:
    """Heroku deployment and management automation"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HEROKU_API_KEY')
        self.heroku_conn = None
        self._initialize_connection()
        
        logger.info("Heroku Deploy Manager initialized")
    
    def _initialize_connection(self):
        """Initialize Heroku connection"""
        try:
            if self.api_key:
                self.heroku_conn = heroku3.from_key(self.api_key)
                logger.info("Heroku connection established")
            else:
                logger.warning("Heroku API key not provided")
        except Exception as e:
            logger.error(f"Failed to initialize Heroku connection: {e}")
    
    async def create_app(self, app_name: str, region: str = 'us',
                        stack: str = 'container') -> Dict[str, Any]:
        """Create a new Heroku app"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            # Check if app name is available
            try:
                requests.get(f'https://{app_name}.herokuapp.com')
                return {'success': False, 'error': 'App name already taken'}
            except:
                pass
            
            # Create the app
            app = self.heroku_conn.create_app(
                name=app_name,
                region=region,
                stack_id_or_name=stack
            )
            
            logger.info(f"Created Heroku app: {app.name}")
            
            return {
                'success': True,
                'app_name': app.name,
                'web_url': app.web_url,
                'git_url': app.git_url,
                'region': region,
                'stack': stack,
                'id': app.id
            }
            
        except Exception as e:
            logger.error(f"Failed to create Heroku app: {e}")
            return {'success': False, 'error': str(e)}
    
    async def deploy_from_github(self, app_name: str, 
                               github_repo: str,
                               branch: str = 'main') -> Dict[str, Any]:
        """Deploy from GitHub repository"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Set up GitHub integration
            integration = app.create_github_integration(
                repository=github_repo,
                silent=False,
                auto_deploy=True,
                wait_for_ci=False
            )
            
            # Enable automatic deploys
            app.enable_automatic_deploys(branch=branch)
            
            # Trigger a manual deploy
            build = app.builds().create(
                source_blob={
                    'url': f'https://github.com/{github_repo}/archive/{branch}.tar.gz',
                    'version': branch
                }
            )
            
            logger.info(f"Triggered deployment for {app_name} from {github_repo}/{branch}")
            
            return {
                'success': True,
                'app_name': app_name,
                'github_repo': github_repo,
                'branch': branch,
                'build_id': build.id,
                'build_status': build.status,
                'output_stream_url': build.output_stream_url
            }
            
        except Exception as e:
            logger.error(f"Failed to deploy from GitHub: {e}")
            return {'success': False, 'error': str(e)}
    
    async def deploy_from_docker(self, app_name: str,
                               dockerfile_path: str = 'Dockerfile',
                               context_path: str = '.') -> Dict[str, Any]:
        """Deploy using Docker container"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Check if app has container stack
            if app.stack.name != 'container':
                app.update_buildstack('container')
            
            # Build and push Docker image
            # Note: This requires Heroku CLI and Docker to be installed locally
            process = subprocess.run([
                'heroku', 'container:push', 'web',
                '--app', app_name,
                '--context-path', context_path
            ], capture_output=True, text=True)
            
            if process.returncode != 0:
                return {
                    'success': False,
                    'error': f'Docker build failed: {process.stderr}'
                }
            
            # Release the container
            process = subprocess.run([
                'heroku', 'container:release', 'web',
                '--app', app_name
            ], capture_output=True, text=True)
            
            if process.returncode != 0:
                return {
                    'success': False,
                    'error': f'Container release failed: {process.stderr}'
                }
            
            logger.info(f"Deployed Docker container to {app_name}")
            
            return {
                'success': True,
                'app_name': app_name,
                'deployment_method': 'docker',
                'dockerfile': dockerfile_path,
                'context_path': context_path
            }
            
        except Exception as e:
            logger.error(f"Failed to deploy with Docker: {e}")
            return {'success': False, 'error': str(e)}
    
    async def configure_addons(self, app_name: str,
                             addons: List[Dict]) -> Dict[str, Any]:
        """Configure Heroku addons"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            installed_addons = []
            
            for addon_config in addons:
                addon_name = addon_config.get('name')
                plan = addon_config.get('plan', 'hobby-dev')
                
                try:
                    # Install addon
                    addon = app.install_addon(
                        addon_name,
                        plan=plan,
                        config=addon_config.get('config', {})
                    )
                    
                    installed_addons.append({
                        'name': addon.name,
                        'plan': plan,
                        'state': addon.state,
                        'config': addon.config
                    })
                    
                    logger.info(f"Installed addon: {addon_name} ({plan})")
                    
                except Exception as e:
                    logger.error(f"Failed to install addon {addon_name}: {e}")
                    continue
            
            return {
                'success': True,
                'app_name': app_name,
                'installed_addons': installed_addons
            }
            
        except Exception as e:
            logger.error(f"Failed to configure addons: {e}")
            return {'success': False, 'error': str(e)}
    
    async def setup_database(self, app_name: str,
                           database_type: str = 'postgresql',
                           plan: str = 'hobby-dev') -> Dict[str, Any]:
        """Setup database addon"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Install database addon
            if database_type.lower() == 'postgresql':
                addon_name = 'heroku-postgresql'
            elif database_type.lower() == 'redis':
                addon_name = 'heroku-redis'
            else:
                return {'success': False, 'error': f'Unsupported database type: {database_type}'}
            
            # Check if already installed
            existing_addons = app.addons()
            for addon in existing_addons:
                if addon_name in addon.name:
                    return {
                        'success': True,
                        'message': f'{database_type} already installed',
                        'database': addon.config
                    }
            
            # Install new database
            database = app.install_addon(
                addon_name,
                plan=plan
            )
            
            # Wait for database to be ready
            import time
            time.sleep(10)
            
            logger.info(f"Setup {database_type} database for {app_name}")
            
            return {
                'success': True,
                'database_type': database_type,
                'plan': plan,
                'config': database.config,
                'connection_string': database.config.get('DATABASE_URL')
            }
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            return {'success': False, 'error': str(e)}
    
    async def scale_dynos(self, app_name: str,
                         dyno_type: str = 'web',
                         size: str = 'standard-1x',
                         quantity: int = 1) -> Dict[str, Any]:
        """Scale Heroku dynos"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Get formation
            formation = app.process_formation()[dyno_type]
            
            # Scale dynos
            formation.scale(quantity=quantity, size=size)
            
            logger.info(f"Scaled {dyno_type} dynos to {quantity}x{size}")
            
            return {
                'success': True,
                'app_name': app_name,
                'dyno_type': dyno_type,
                'size': size,
                'quantity': quantity,
                'hourly_cost': self._calculate_dyno_cost(size, quantity)
            }
            
        except Exception as e:
            logger.error(f"Failed to scale dynos: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_dyno_cost(self, size: str, quantity: int) -> float:
        """Calculate estimated hourly cost"""
        # Heroku dyno pricing (approx)
        pricing = {
            'eco': 0.005,
            'basic': 0.007,
            'standard-1x': 0.025,
            'standard-2x': 0.050,
            'performance-m': 0.250,
            'performance-l': 0.500
        }
        
        hourly_rate = pricing.get(size, 0.025)
        return round(hourly_rate * quantity, 4)
    
    async def configure_environment(self, app_name: str,
                                  env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Configure environment variables"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Update config vars
            config = app.config()
            
            for key, value in env_vars.items():
                config[key] = value
            
            config.update()
            
            logger.info(f"Updated environment variables for {app_name}")
            
            return {
                'success': True,
                'app_name': app_name,
                'updated_vars': list(env_vars.keys()),
                'total_vars': len(config)
            }
            
        except Exception as e:
            logger.error(f"Failed to configure environment: {e}")
            return {'success': False, 'error': str(e)}
    
    async def setup_log_drain(self, app_name: str,
                            log_drain_url: str) -> Dict[str, Any]:
        """Setup log drain for centralized logging"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Create log drain
            log_drain = app.create_log_drain(log_drain_url)
            
            logger.info(f"Setup log drain for {app_name}")
            
            return {
                'success': True,
                'app_name': app_name,
                'log_drain_url': log_drain_url,
                'token': log_drain.token
            }
            
        except Exception as e:
            logger.error(f"Failed to setup log drain: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_app_status(self, app_name: str) -> Dict[str, Any]:
        """Get Heroku app status"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Get app info
            app_info = {
                'name': app.name,
                'web_url': app.web_url,
                'git_url': app.git_url,
                'region': app.region.name,
                'stack': app.stack.name,
                'created_at': app.created_at.isoformat(),
                'updated_at': app.updated_at.isoformat() if app.updated_at else None
            }
            
            # Get dyno info
            dynos = []
            for dyno in app.dynos():
                dynos.append({
                    'type': dyno.type,
                    'size': dyno.size,
                    'state': dyno.state,
                    'command': dyno.command,
                    'updated_at': dyno.updated_at.isoformat()
                })
            
            # Get addons
            addons = []
            for addon in app.addons():
                addons.append({
                    'name': addon.name,
                    'plan': addon.plan.name,
                    'state': addon.state,
                    'price': addon.plan.price.cents / 100 if addon.plan.price else 0
                })
            
            # Get releases
            releases = []
            for release in app.releases()[:5]:  # Last 5 releases
                releases.append({
                    'version': release.version,
                    'description': release.description,
                    'created_at': release.created_at.isoformat(),
                    'status': 'success' if release.status == 'succeeded' else 'failed'
                })
            
            # Get config vars (sensitive ones masked)
            config_vars = {}
            for key in app.config().keys():
                if not any(sensitive in key.lower() for sensitive in ['key', 'secret', 'password', 'token']):
                    config_vars[key] = '***MASKED***'
                else:
                    config_vars[key] = '***SENSITIVE***'
            
            return {
                'success': True,
                'app': app_info,
                'dynos': dynos,
                'addons': addons,
                'releases': releases[:5],
                'config_vars_count': len(app.config()),
                'safe_config_vars': config_vars
            }
            
        except Exception as e:
            logger.error(f"Failed to get app status: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_app_logs(self, app_name: str,
                          lines: int = 100,
                          dyno: str = None,
                          source: str = None) -> Dict[str, Any]:
        """Get application logs"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Build log options
            options = {'lines': lines}
            if dyno:
                options['dyno'] = dyno
            if source:
                options['source'] = source
            
            # Get logs
            logs = app.get_log(**options)
            
            return {
                'success': True,
                'app_name': app_name,
                'log_lines': lines,
                'logs': logs,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get app logs: {e}")
            return {'success': False, 'error': str(e)}
    
    async def restart_app(self, app_name: str) -> Dict[str, Any]:
        """Restart Heroku app"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            app = self.heroku_conn.apps()[app_name]
            
            # Restart all dynos
            app.restart()
            
            logger.info(f"Restarted Heroku app: {app_name}")
            
            return {
                'success': True,
                'app_name': app_name,
                'message': 'App restart initiated',
                'restart_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to restart app: {e}")
            return {'success': False, 'error': str(e)}
    
    async def backup_database(self, app_name: str,
                            database_id: str = 'DATABASE_URL') -> Dict[str, Any]:
        """Backup Heroku database"""
        try:
            if not self.heroku_conn:
                return {'success': False, 'error': 'Heroku connection not available'}
            
            # Using Heroku CLI for database backup
            process = subprocess.run([
                'heroku', 'pg:backups:capture',
                '--app', app_name
            ], capture_output=True, text=True)
            
            if process.returncode != 0:
                return {
                    'success': False,
                    'error': f'Database backup failed: {process.stderr}'
                }
            
            # Get backup info
            process = subprocess.run([
                'heroku', 'pg:backups:info',
                '--app', app_name
            ], capture_output=True, text=True)
            
            logger.info(f"Created database backup for {app_name}")
            
            return {
                'success': True,
                'app_name': app_name,
                'backup_output': process.stdout,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_one_click_deploy(self, app_name: str,
                                    deploy_url: str) -> Dict[str, Any]:
        """Create one-click deploy button configuration"""
        try:
            # Heroku one-click deploy button configuration
            deploy_config = {
                'app.json': {
                    'name': f'VT ULTRA PRO - {app_name}',
                    'description': 'TikTok View Automation System',
                    'repository': 'https://github.com/username/vt-ultra-pro',
                    'logo': 'https://raw.githubusercontent.com/username/vt-ultra-pro/main/logo.png',
                    'keywords': ['tiktok', 'automation', 'views', 'python', 'bot'],
                    'env': {
                        'TELEGRAM_BOT_TOKEN': {
                            'description': 'Telegram Bot API Token',
                            'required': True
                        },
                        'ADMIN_USER_ID': {
                            'description': 'Admin User ID for Telegram',
                            'required': True
                        },
                        'DATABASE_URL': {
                            'description': 'PostgreSQL Database URL',
                            'required': True,
                            'generator': 'secret'
                        }
                    },
                    'formation': {
                        'web': {
                            'quantity': 1,
                            'size': 'standard-1x'
                        },
                        'worker': {
                            'quantity': 1,
                            'size': 'standard-1x'
                        }
                    },
                    'addons': [
                        'heroku-postgresql:hobby-dev',
                        'heroku-redis:hobby-dev'
                    ],
                    'buildpacks': [
                        {'url': 'heroku/python'},
                        {'url': 'heroku/nodejs'}
                    ]
                }
            }
            
            # Save config
            config_path = f'deploy/{app_name}/app.json'
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(deploy_config, f, indent=2)
            
            # Create deploy button URL
            deploy_button_url = (
                f'https://heroku.com/deploy?template={deploy_url}'
            )
            
            return {
                'success': True,
                'app_name': app_name,
                'config_path': config_path,
                'deploy_button_url': deploy_button_url,
                'deploy_config': deploy_config
            }
            
        except Exception as e:
            logger.error(f"Failed to create one-click deploy: {e}")
            return {'success': False, 'error': str(e)}