"""
Alert System for VT ULTRA PRO
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    CONSOLE = "console"

class AlertSystem:
    """Alert notification system"""
    
    def __init__(self):
        self.alerts = []
        self.alert_rules = []
        self.notification_channels = []
        self.silenced_alerts = []
        
        self._load_alert_rules()
        self._setup_notification_channels()
        
        logger.info("Alert System initialized")
    
    def _load_alert_rules(self):
        """Load alert rules from configuration"""
        default_rules = [
            {
                'id': 'cpu_high',
                'name': 'High CPU Usage',
                'condition': lambda metrics: metrics.get('system', {}).get('cpu_percent', 0) > 90,
                'level': AlertLevel.CRITICAL,
                'message_template': 'CPU usage is {cpu_percent}% (threshold: 90%)',
                'channels': [AlertChannel.EMAIL, AlertChannel.TELEGRAM],
                'cooldown_minutes': 30
            },
            {
                'id': 'cpu_warning',
                'name': 'High CPU Warning',
                'condition': lambda metrics: metrics.get('system', {}).get('cpu_percent', 0) > 80,
                'level': AlertLevel.WARNING,
                'message_template': 'CPU usage is {cpu_percent}% (threshold: 80%)',
                'channels': [AlertChannel.CONSOLE],
                'cooldown_minutes': 15
            },
            {
                'id': 'memory_high',
                'name': 'High Memory Usage',
                'condition': lambda metrics: metrics.get('system', {}).get('memory_percent', 0) > 90,
                'level': AlertLevel.CRITICAL,
                'message_template': 'Memory usage is {memory_percent}% (threshold: 90%)',
                'channels': [AlertChannel.EMAIL, AlertChannel.TELEGRAM],
                'cooldown_minutes': 30
            },
            {
                'id': 'disk_high',
                'name': 'High Disk Usage',
                'condition': lambda metrics: metrics.get('disk', {}).get('root_percent', 0) > 95,
                'level': AlertLevel.CRITICAL,
                'message_template': 'Disk usage is {disk_percent}% (threshold: 95%)',
                'channels': [AlertChannel.EMAIL, AlertChannel.TELEGRAM],
                'cooldown_minutes': 60
            },
            {
                'id': 'queue_large',
                'name': 'Large Queue Size',
                'condition': lambda metrics: metrics.get('application', {}).get('queue_size', 0) > 100,
                'level': AlertLevel.WARNING,
                'message_template': 'Queue size is {queue_size} orders (threshold: 100)',
                'channels': [AlertChannel.CONSOLE, AlertChannel.SLACK],
                'cooldown_minutes': 10
            },
            {
                'id': 'error_rate_high',
                'name': 'High Error Rate',
                'condition': lambda metrics: metrics.get('application', {}).get('error_rate', 0) > 0.1,
                'level': AlertLevel.CRITICAL,
                'message_template': 'Error rate is {error_rate:.1%} (threshold: 10%)',
                'channels': [AlertChannel.EMAIL, AlertChannel.TELEGRAM, AlertChannel.SLACK],
                'cooldown_minutes': 5
            },
            {
                'id': 'no_orders',
                'name': 'No Orders Processed',
                'condition': lambda metrics: metrics.get('application', {}).get('orders_completed_24h', 0) == 0,
                'level': AlertLevel.WARNING,
                'message_template': 'No orders completed in last 24 hours',
                'channels': [AlertChannel.CONSOLE],
                'cooldown_minutes': 1440  # 24 hours
            }
        ]
        
        self.alert_rules = default_rules
        logger.info(f"Loaded {len(self.alert_rules)} alert rules")
    
    def _setup_notification_channels(self):
        """Setup notification channels"""
        # Console channel (always available)
        self.notification_channels.append({
            'type': AlertChannel.CONSOLE,
            'enabled': True,
            'config': {}
        })
        
        # Email channel (configured via environment)
        import os
        email_config = {
            'smtp_server': os.getenv('ALERT_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('ALERT_SMTP_PORT', 587)),
            'username': os.getenv('ALERT_EMAIL_USER'),
            'password': os.getenv('ALERT_EMAIL_PASSWORD'),
            'from_address': os.getenv('ALERT_FROM_EMAIL', 'alerts@vt-ultra-pro.com'),
            'to_addresses': os.getenv('ALERT_TO_EMAILS', '').split(',')
        }
        
        if email_config['username'] and email_config['password']:
            self.notification_channels.append({
                'type': AlertChannel.EMAIL,
                'enabled': True,
                'config': email_config
            })
            logger.info("Email notification channel configured")
        
        # Telegram channel
        telegram_bot_token = os.getenv('ALERT_TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('ALERT_TELEGRAM_CHAT_ID')
        
        if telegram_bot_token and telegram_chat_id:
            self.notification_channels.append({
                'type': AlertChannel.TELEGRAM,
                'enabled': True,
                'config': {
                    'bot_token': telegram_bot_token,
                    'chat_id': telegram_chat_id
                }
            })
            logger.info("Telegram notification channel configured")
        
        # Slack channel
        slack_webhook_url = os.getenv('ALERT_SLACK_WEBHOOK_URL')
        if slack_webhook_url:
            self.notification_channels.append({
                'type': AlertChannel.SLACK,
                'enabled': True,
                'config': {
                    'webhook_url': slack_webhook_url
                }
            })
            logger.info("Slack notification channel configured")
        
        # Webhook channel
        webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        if webhook_url:
            self.notification_channels.append({
                'type': AlertChannel.WEBHOOK,
                'enabled': True,
                'config': {
                    'url': webhook_url,
                    'headers': json.loads(os.getenv('ALERT_WEBHOOK_HEADERS', '{}'))
                }
            })
            logger.info("Webhook notification channel configured")
    
    async def process_metrics(self, metrics: Dict[str, Any]):
        """Process metrics and trigger alerts"""
        triggered_alerts = []
        
        for rule in self.alert_rules:
            try:
                # Check if rule condition is met
                if rule['condition'](metrics):
                    # Check cooldown
                    if not self._is_on_cooldown(rule['id']):
                        # Create alert
                        alert = self._create_alert(rule, metrics)
                        
                        # Check if silenced
                        if not self._is_silenced(alert):
                            triggered_alerts.append(alert)
                            
                            # Send notifications
                            await self._send_notifications(alert, rule['channels'])
                            
                            # Log alert
                            self.alerts.append(alert)
                            logger.warning(f"Alert triggered: {alert['name']} - {alert['message']}")
                        
                        # Update cooldown
                        self._update_cooldown(rule['id'])
                        
            except Exception as e:
                logger.error(f"Error processing alert rule {rule.get('id')}: {e}")
        
        # Keep only recent alerts
        self.alerts = self.alerts[-1000:]
        
        return triggered_alerts
    
    def _create_alert(self, rule: Dict, metrics: Dict) -> Dict[str, Any]:
        """Create alert object"""
        # Format message template with metrics
        message = rule['message_template']
        
        # Extract metrics for template
        template_vars = {
            'cpu_percent': metrics.get('system', {}).get('cpu_percent', 0),
            'memory_percent': metrics.get('system', {}).get('memory_percent', 0),
            'disk_percent': metrics.get('disk', {}).get('root_percent', 0),
            'queue_size': metrics.get('application', {}).get('queue_size', 0),
            'error_rate': metrics.get('application', {}).get('error_rate', 0)
        }
        
        # Format message
        try:
            message = message.format(**template_vars)
        except:
            pass
        
        alert = {
            'id': f"{rule['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'rule_id': rule['id'],
            'name': rule['name'],
            'level': rule['level'].value,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metrics_snapshot': {
                'cpu_percent': template_vars['cpu_percent'],
                'memory_percent': template_vars['memory_percent'],
                'disk_percent': template_vars['disk_percent']
            },
            'notified_channels': [],
            'acknowledged': False,
            'resolved': False
        }
        
        return alert
    
    def _is_on_cooldown(self, rule_id: str) -> bool:
        """Check if rule is on cooldown"""
        # Check last triggered time
        for alert in reversed(self.alerts):
            if alert.get('rule_id') == rule_id:
                alert_time = datetime.fromisoformat(alert['timestamp'])
                # Find rule cooldown
                rule = next((r for r in self.alert_rules if r['id'] == rule_id), None)
                if rule:
                    cooldown = rule.get('cooldown_minutes', 5)
                    if datetime.now() - alert_time < timedelta(minutes=cooldown):
                        return True
                break
        
        return False
    
    def _update_cooldown(self, rule_id: str):
        """Update cooldown timestamp"""
        # Implementation handled by _is_on_cooldown checking timestamps
        pass
    
    def _is_silenced(self, alert: Dict) -> bool:
        """Check if alert is silenced"""
        for silenced in self.silenced_alerts:
            # Check if alert matches silenced pattern
            if silenced.get('rule_id') and silenced['rule_id'] == alert['rule_id']:
                if datetime.now() < datetime.fromisoformat(silenced.get('until', '2000-01-01')):
                    return True
        
        return False
    
    async def _send_notifications(self, alert: Dict, channels: List[AlertChannel]):
        """Send notifications through configured channels"""
        sent_channels = []
        
        for channel_type in channels:
            try:
                channel_config = next(
                    (c for c in self.notification_channels 
                     if c['type'] == channel_type and c['enabled']),
                    None
                )
                
                if channel_config:
                    if channel_type == AlertChannel.CONSOLE:
                        await self._send_console_notification(alert, channel_config)
                        sent_channels.append('console')
                    
                    elif channel_type == AlertChannel.EMAIL:
                        await self._send_email_notification(alert, channel_config)
                        sent_channels.append('email')
                    
                    elif channel_type == AlertChannel.TELEGRAM:
                        await self._send_telegram_notification(alert, channel_config)
                        sent_channels.append('telegram')
                    
                    elif channel_type == AlertChannel.SLACK:
                        await self._send_slack_notification(alert, channel_config)
                        sent_channels.append('slack')
                    
                    elif channel_type == AlertChannel.WEBHOOK:
                        await self._send_webhook_notification(alert, channel_config)
                        sent_channels.append('webhook')
                        
            except Exception as e:
                logger.error(f"Failed to send {channel_type.value} notification: {e}")
        
        # Update alert with notified channels
        alert['notified_channels'] = sent_channels
    
    async def _send_console_notification(self, alert: Dict, config: Dict):
        """Send console notification"""
        level_color = {
            'critical': '\033[91m',  # Red
            'warning': '\033[93m',   # Yellow
            'info': '\033[94m'       # Blue
        }
        
        color = level_color.get(alert['level'], '\033[0m')
        reset = '\033[0m'
        
        print(f"\n{color}🚨 ALERT: {alert['name']}{reset}")
        print(f"{color}Level: {alert['level'].upper()}{reset}")
        print(f"{color}Time: {alert['timestamp']}{reset}")
        print(f"{color}Message: {alert['message']}{reset}")
        print(f"{color}{'='*50}{reset}\n")
    
    async def _send_email_notification(self, alert: Dict, config: Dict):
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = config['config']['from_address']
            msg['To'] = ', '.join(config['config']['to_addresses'])
            msg['Subject'] = f"[{alert['level'].upper()}] VT ULTRA PRO Alert: {alert['name']}"
            
            # Create HTML content
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background-color: {'#ff4444' if alert['level'] == 'critical' else '#ffbb33' if alert['level'] == 'warning' else '#33b5e5'}; 
                            color: white; padding: 20px; border-radius: 5px;">
                    <h2>🚨 VT ULTRA PRO Alert</h2>
                    <h3>{alert['name']}</h3>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                    <p><strong>Level:</strong> {alert['level'].upper()}</p>
                    <p><strong>Time:</strong> {alert['timestamp']}</p>
                    <p><strong>Message:</strong> {alert['message']}</p>
                    
                    <h4>Metrics:</h4>
                    <ul>
                        <li>CPU: {alert['metrics_snapshot'].get('cpu_percent', 0)}%</li>
                        <li>Memory: {alert['metrics_snapshot'].get('memory_percent', 0)}%</li>
                        <li>Disk: {alert['metrics_snapshot'].get('disk_percent', 0)}%</li>
                    </ul>
                    
                    <p>Please check the system immediately.</p>
                </div>
                
                <div style="margin-top: 20px; font-size: 12px; color: #777;">
                    <p>This is an automated alert from VT ULTRA PRO Monitoring System.</p>
                    <p>Alert ID: {alert['id']}</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(config['config']['smtp_server'], config['config']['smtp_port']) as server:
                server.starttls()
                server.login(config['config']['username'], config['config']['password'])
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {alert['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    async def _send_telegram_notification(self, alert: Dict, config: Dict):
        """Send Telegram notification"""
        try:
            import requests
            
            bot_token = config['config']['bot_token']
            chat_id = config['config']['chat_id']
            
            # Format message
            level_emoji = {
                'critical': '🔴',
                'warning': '🟡',
                'info': '🔵'
            }
            
            emoji = level_emoji.get(alert['level'], '⚪')
            
            message = f"""
{emoji} <b>VT ULTRA PRO Alert</b>

<b>{alert['name']}</b>

<b>Level:</b> {alert['level'].upper()}
<b>Time:</b> {alert['timestamp']}
<b>Message:</b> {alert['message']}

<b>Metrics:</b>
• CPU: {alert['metrics_snapshot'].get('cpu_percent', 0)}%
• Memory: {alert['metrics_snapshot'].get('memory_percent', 0)}%
• Disk: {alert['metrics_snapshot'].get('disk_percent', 0)}%

Alert ID: {alert['id']}
            """
            
            # Send via Telegram Bot API
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Telegram alert sent: {alert['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise
    
    async def _send_slack_notification(self, alert: Dict, config: Dict):
        """Send Slack notification"""
        try:
            import requests
            
            webhook_url = config['config']['webhook_url']
            
            # Format Slack message
            color = {
                'critical': '#ff0000',
                'warning': '#ff9900',
                'info': '#3366ff'
            }.get(alert['level'], '#808080')
            
            slack_message = {
                'attachments': [
                    {
                        'color': color,
                        'title': f"🚨 VT ULTRA PRO Alert: {alert['name']}",
                        'fields': [
                            {
                                'title': 'Level',
                                'value': alert['level'].upper(),
                                'short': True
                            },
                            {
                                'title': 'Time',
                                'value': alert['timestamp'],
                                'short': True
                            },
                            {
                                'title': 'Message',
                                'value': alert['message'],
                                'short': False
                            },
                            {
                                'title': 'CPU Usage',
                                'value': f"{alert['metrics_snapshot'].get('cpu_percent', 0)}%",
                                'short': True
                            },
                            {
                                'title': 'Memory Usage',
                                'value': f"{alert['metrics_snapshot'].get('memory_percent', 0)}%",
                                'short': True
                            }
                        ],
                        'footer': f"Alert ID: {alert['id']}",
                        'ts': int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=slack_message)
            response.raise_for_status()
            
            logger.info(f"Slack alert sent: {alert['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise
    
    async def _send_webhook_notification(self, alert: Dict, config: Dict):
        """Send webhook notification"""
        try:
            import requests
            
            url = config['config']['url']
            headers = config['config'].get('headers', {})
            
            # Prepare payload
            payload = {
                'event': 'alert',
                'alert': alert,
                'timestamp': datetime.now().isoformat(),
                'system': 'vt-ultra-pro'
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent: {alert['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            raise
    
    async def get_alerts(self, filters: Dict = None) -> List[Dict]:
        """Get alerts with optional filtering"""
        alerts = self.alerts
        
        if filters:
            if filters.get('level'):
                alerts = [a for a in alerts if a['level'] == filters['level']]
            
            if filters.get('rule_id'):
                alerts = [a for a in alerts if a['rule_id'] == filters['rule_id']]
            
            if filters.get('start_time'):
                start_time = datetime.fromisoformat(filters['start_time'])
                alerts = [a for a in alerts if datetime.fromisoformat(a['timestamp']) >= start_time]
            
            if filters.get('end_time'):
                end_time = datetime.fromisoformat(filters['end_time'])
                alerts = [a for a in alerts if datetime.fromisoformat(a['timestamp']) <= end_time]
            
            if filters.get('resolved') is not None:
                alerts = [a for a in alerts if a['resolved'] == filters['resolved']]
            
            if filters.get('acknowledged') is not None:
                alerts = [a for a in alerts if a['acknowledged'] == filters['acknowledged']]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply limit
        limit = filters.get('limit', 100) if filters else 100
        return alerts[:limit]
    
    async def acknowledge_alert(self, alert_id: str, user: str = 'system') -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_by'] = user
                alert['acknowledged_at'] = datetime.now().isoformat()
                
                logger.info(f"Alert {alert_id} acknowledged by {user}")
                return True
        
        return False
    
    async def resolve_alert(self, alert_id: str, notes: str = '') -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['resolved'] = True
                alert['resolved_at'] = datetime.now().isoformat()
                alert['resolution_notes'] = notes
                
                logger.info(f"Alert {alert_id} resolved")
                return True
        
        return False
    
    async def silence_alert(self, rule_id: str, hours: int = 24, reason: str = '') -> bool:
        """Silence alerts for a rule"""
        silence_until = datetime.now() + timedelta(hours=hours)
        
        self.silenced_alerts.append({
            'rule_id': rule_id,
            'silenced_at': datetime.now().isoformat(),
            'silenced_by': 'system',
            'until': silence_until.isoformat(),
            'reason': reason
        })
        
        # Clean up expired silences
        self.silenced_alerts = [
            s for s in self.silenced_alerts 
            if datetime.fromisoformat(s['until']) > datetime.now()
        ]
        
        logger.info(f"Alerts for rule {rule_id} silenced until {silence_until}")
        return True
    
    async def remove_silence(self, rule_id: str) -> bool:
        """Remove silence for a rule"""
        initial_count = len(self.silenced_alerts)
        self.silenced_alerts = [s for s in self.silenced_alerts if s['rule_id'] != rule_id]
        
        if len(self.silenced_alerts) < initial_count:
            logger.info(f"Removed silence for rule {rule_id}")
            return True
        
        return False
    
    async def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            a for a in self.alerts 
            if datetime.fromisoformat(a['timestamp']) >= cutoff
        ]
        
        # Count by level
        by_level = {}
        for alert in recent_alerts:
            level = alert['level']
            by_level[level] = by_level.get(level, 0) + 1
        
        # Count by rule
        by_rule = {}
        for alert in recent_alerts:
            rule_id = alert['rule_id']
            by_rule[rule_id] = by_rule.get(rule_id, 0) + 1
        
        # Calculate response times
        acknowledged_alerts = [a for a in recent_alerts if a.get('acknowledged')]
        response_times = []
        
        for alert in acknowledged_alerts:
            if alert.get('acknowledged_at'):
                alert_time = datetime.fromisoformat(alert['timestamp'])
                ack_time = datetime.fromisoformat(alert['acknowledged_at'])
                response_time = (ack_time - alert_time).total_seconds() / 60  # minutes
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'time_range_hours': hours,
            'total_alerts': len(recent_alerts),
            'by_level': by_level,
            'by_rule': by_rule,
            'acknowledged_count': len(acknowledged_alerts),
            'resolved_count': len([a for a in recent_alerts if a.get('resolved')]),
            'avg_response_time_minutes': round(avg_response_time, 2),
            'silenced_rules': len(self.silenced_alerts)
        }
    
    async def add_custom_rule(self, rule: Dict) -> bool:
        """Add custom alert rule"""
        try:
            # Validate rule
            required_fields = ['id', 'name', 'condition', 'level']
            for field in required_fields:
                if field not in rule:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check if rule ID already exists
            if any(r['id'] == rule['id'] for r in self.alert_rules):
                raise ValueError(f"Rule ID already exists: {rule['id']}")
            
            # Ensure level is AlertLevel enum
            if isinstance(rule['level'], str):
                rule['level'] = AlertLevel(rule['level'])
            
            # Ensure channels are AlertChannel enums
            if 'channels' in rule:
                rule['channels'] = [AlertChannel(c) if isinstance(c, str) else c 
                                   for c in rule['channels']]
            
            # Add default values
            rule.setdefault('message_template', '{rule_name} triggered')
            rule.setdefault('cooldown_minutes', 5)
            
            self.alert_rules.append(rule)
            logger.info(f"Added custom alert rule: {rule['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom rule: {e}")
            return False
    
    async def remove_rule(self, rule_id: str) -> bool:
        """Remove alert rule"""
        initial_count = len(self.alert_rules)
        self.alert_rules = [r for r in self.alert_rules if r['id'] != rule_id]
        
        if len(self.alert_rules) < initial_count:
            logger.info(f"Removed alert rule: {rule_id}")
            return True
        
        return False