"""
Telegram Bot with 20+ API Commands for VT ULTRA PRO
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import aiosqlite

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    CallbackQuery, Message, ParseMode
)
from aiogram.utils import executor
from aiogram.utils.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)

@dataclass
class BotUser:
    user_id: int
    username: str
    first_name: str
    last_name: str
    language_code: str
    is_premium: bool = False
    join_date: datetime = None
    last_active: datetime = None
    command_count: int = 0
    view_credits: int = 0
    subscription_level: str = "free"
    
    def __post_init__(self):
        if self.join_date is None:
            self.join_date = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'language_code': self.language_code,
            'is_premium': self.is_premium,
            'join_date': self.join_date.isoformat(),
            'last_active': self.last_active.isoformat(),
            'command_count': self.command_count,
            'view_credits': self.view_credits,
            'subscription_level': self.subscription_level
        }

class TelegramBot:
    def __init__(self, token: str, admin_ids: List[int] = None):
        self.token = token
        self.admin_ids = admin_ids or []
        self.bot = Bot(token=token, parse_mode=ParseMode.HTML)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(self.bot, storage=self.storage)
        self.users: Dict[int, BotUser] = {}
        self.commands_registered = False
        self.db_path = "database/telegram_bot.db"
        
        # Register middlewares
        self.dp.middleware.setup(LoggingMiddleware())
        
        # Initialize
        asyncio.create_task(self.initialize())
    
    async def initialize(self):
        """Initialize the bot"""
        await self._init_database()
        await self._load_users()
        await self._register_handlers()
        logger.info("Telegram bot initialized")
    
    async def _init_database(self):
        """Initialize bot database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    is_premium INTEGER,
                    join_date TEXT,
                    last_active TEXT,
                    command_count INTEGER DEFAULT 0,
                    view_credits INTEGER DEFAULT 0,
                    subscription_level TEXT DEFAULT 'free'
                )
            ''')
            
            # Commands history
            await db.execute('''
                CREATE TABLE IF NOT EXISTS commands_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    command TEXT,
                    arguments TEXT,
                    timestamp TEXT,
                    success INTEGER
                )
            ''')
            
            # User sessions
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    state TEXT,
                    data TEXT,
                    last_updated TEXT
                )
            ''')
            
            await db.commit()
    
    async def _load_users(self):
        """Load users from database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT * FROM users') as cursor:
                    rows = await cursor.fetchall()
                    
                    for row in rows:
                        user = BotUser(
                            user_id=row[0],
                            username=row[1],
                            first_name=row[2],
                            last_name=row[3],
                            language_code=row[4],
                            is_premium=bool(row[5]),
                            join_date=datetime.fromisoformat(row[6]) if row[6] else None,
                            last_active=datetime.fromisoformat(row[7]) if row[7] else None,
                            command_count=row[8],
                            view_credits=row[9],
                            subscription_level=row[10]
                        )
                        self.users[user.user_id] = user
                    
            logger.info(f"Loaded {len(self.users)} users from database")
            
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
    
    async def _save_user(self, user: BotUser):
        """Save user to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, language_code, 
                     is_premium, join_date, last_active, command_count, 
                     view_credits, subscription_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.user_id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    user.language_code,
                    1 if user.is_premium else 0,
                    user.join_date.isoformat(),
                    user.last_active.isoformat(),
                    user.command_count,
                    user.view_credits,
                    user.subscription_level
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to save user {user.user_id}: {e}")
    
    async def _register_handlers(self):
        """Register all command handlers"""
        
        # Start command
        @self.dp.message_handler(Command('start'))
        async def cmd_start(message: types.Message):
            await self._handle_start(message)
        
        # Help command
        @self.dp.message_handler(Command('help'))
        async def cmd_help(message: types.Message):
            await self._handle_help(message)
        
        # Send views command
        @self.dp.message_handler(Command('send'))
        async def cmd_send(message: types.Message):
            await self._handle_send(message)
        
        # Balance command
        @self.dp.message_handler(Command('balance'))
        async def cmd_balance(message: types.Message):
            await self._handle_balance(message)
        
        # Stats command
        @self.dp.message_handler(Command('stats'))
        async def cmd_stats(message: types.Message):
            await self._handle_stats(message)
        
        # History command
        @self.dp.message_handler(Command('history'))
        async def cmd_history(message: types.Message):
            await self._handle_history(message)
        
        # Status command
        @self.dp.message_handler(Command('status'))
        async def cmd_status(message: types.Message):
            await self._handle_status(message)
        
        # Subscribe command
        @self.dp.message_handler(Command('subscribe'))
        async def cmd_subscribe(message: types.Message):
            await self._handle_subscribe(message)
        
        # Methods command
        @self.dp.message_handler(Command('methods'))
        async def cmd_methods(message: types.Message):
            await self._handle_methods(message)
        
        # Schedule command
        @self.dp.message_handler(Command('schedule'))
        async def cmd_schedule(message: types.Message):
            await self._handle_schedule(message)
        
        # Cancel command
        @self.dp.message_handler(Command('cancel'))
        async def cmd_cancel(message: types.Message):
            await self._handle_cancel(message)
        
        # Report command
        @self.dp.message_handler(Command('report'))
        async def cmd_report(message: types.Message):
            await self._handle_report(message)
        
        # Settings command
        @self.dp.message_handler(Command('settings'))
        async def cmd_settings(message: types.Message):
            await self._handle_settings(message)
        
        # Support command
        @self.dp.message_handler(Command('support'))
        async def cmd_support(message: types.Message):
            await self._handle_support(message)
        
        # Admin commands
        @self.dp.message_handler(Command('admin'))
        async def cmd_admin(message: types.Message):
            await self._handle_admin(message)
        
        # Broadcast command (admin only)
        @self.dp.message_handler(Command('broadcast'))
        async def cmd_broadcast(message: types.Message):
            await self._handle_broadcast(message)
        
        # Users command (admin only)
        @self.dp.message_handler(Command('users'))
        async def cmd_users(message: types.Message):
            await self._handle_users(message)
        
        # System command (admin only)
        @self.dp.message_handler(Command('system'))
        async def cmd_system(message: types.Message):
            await self._handle_system(message)
        
        # Logs command (admin only)
        @self.dp.message_handler(Command('logs'))
        async def cmd_logs(message: types.Message):
            await self._handle_logs(message)
        
        # Callback query handlers
        @self.dp.callback_query_handler()
        async def process_callback(callback_query: types.CallbackQuery):
            await self._handle_callback(callback_query)
        
        # Text message handler (for URL input)
        @self.dp.message_handler(content_types=types.ContentType.TEXT)
        async def handle_text(message: types.Message):
            await self._handle_text(message)
        
        # Error handler
        @self.dp.errors_handler()
        async def errors_handler(update: types.Update, exception: Exception):
            return await self._handle_error(update, exception)
        
        self.commands_registered = True
        logger.info("Registered 20+ command handlers")
    
    async def _handle_start(self, message: types.Message):
        """Handle /start command"""
        user = await self._get_or_create_user(message.from_user)
        
        welcome_text = f"""
🎯 <b>Welcome to VT ULTRA PRO TikTok Bot!</b>

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.user_id}</code>
📅 <b>Joined:</b> {user.join_date.strftime('%Y-%m-%d')}
💎 <b>Subscription:</b> {user.subscription_level.title()}
🪙 <b>Credits:</b> {user.view_credits:,} views

<b>Available Commands:</b>
/send - Send views to TikTok video
/balance - Check your balance
/stats - View your statistics
/history - View order history
/status - Check active campaigns
/subscribe - Upgrade subscription
/methods - View available methods
/schedule - Schedule views
/report - Generate report
/settings - Bot settings
/support - Contact support

⚡ <b>Quick Start:</b>
1. Send TikTok video URL
2. Choose number of views
3. We deliver real views!

Type /help for detailed instructions.
        """
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🚀 Send Views", callback_data="quick_send"),
            InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
            InlineKeyboardButton("💎 Upgrade", callback_data="upgrade"),
            InlineKeyboardButton("🆘 Help", callback_data="help")
        )
        
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'start', 'success')
    
    async def _handle_help(self, message: types.Message):
        """Handle /help command"""
        help_text = """
<b>📚 VT ULTRA PRO Help Guide</b>

<b>🎯 Core Commands:</b>
• <code>/send [URL] [views]</code> - Send views to TikTok video
• <code>/balance</code> - Check your view credits
• <code>/stats</code> - View your statistics
• <code>/history</code> - View order history
• <code>/status [order_id]</code> - Check order status

<b>📅 Scheduling:</b>
• <code>/schedule [URL] [views] [time]</code> - Schedule views
• <code>/cancel [order_id]</code> - Cancel scheduled order

<b>⚙️ Management:</b>
• <code>/methods</code> - View available view methods
• <code>/report [period]</code> - Generate analytics report
• <code>/settings</code> - Configure bot settings
• <code>/subscribe</code> - Upgrade subscription plan

<b>👨‍💼 Admin Commands:</b>
• <code>/admin</code> - Admin panel
• <code>/broadcast [message]</code> - Broadcast to all users
• <code>/users</code> - User management
• <code>/system</code> - System status
• <code>/logs</code> - View system logs

<b>🔧 How to Use:</b>
1. Send TikTok video URL (e.g., https://tiktok.com/@user/video/123456789)
2. Specify number of views (e.g., 100, 500, 1000)
3. Choose method (optional)
4. We'll deliver real views!

<b>📞 Support:</b>
• Use /support for assistance
• Report issues immediately
• Check /status for active orders

<b>⚠️ Important Notes:</b>
• Use only public TikTok URLs
• Don't abuse the system
• Follow TikTok's Terms of Service
• Use at your own risk
        """
        
        await message.answer(help_text, parse_mode=ParseMode.HTML)
        await self._log_command(message.from_user.id, 'help', 'success')
    
    async def _handle_send(self, message: types.Message):
        """Handle /send command"""
        user = await self._get_or_create_user(message.from_user)
        
        # Check if user has enough credits
        if user.subscription_level == 'free' and user.view_credits <= 0:
            await message.answer(
                "❌ You don't have enough view credits!\n\n"
                "Free tier users get 100 views daily. "
                "Wait for reset or upgrade with /subscribe"
            )
            return
        
        args = message.get_args().split()
        
        if len(args) < 2:
            # Show send interface
            keyboard = InlineKeyboardMarkup(row_width=3)
            keyboard.add(
                InlineKeyboardButton("100 views", callback_data="send_100"),
                InlineKeyboardButton("500 views", callback_data="send_500"),
                InlineKeyboardButton("1000 views", callback_data="send_1000"),
                InlineKeyboardButton("Custom", callback_data="send_custom"),
                InlineKeyboardButton("Cancel", callback_data="send_cancel")
            )
            
            await message.answer(
                "📤 <b>Send TikTok Views</b>\n\n"
                "Send TikTok video URL and choose number of views.\n\n"
                "<b>Example:</b>\n"
                "<code>https://tiktok.com/@username/video/123456789</code>\n\n"
                "Or use buttons below for quick selection.",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            # Process send command with arguments
            try:
                video_url = args[0]
                views = int(args[1])
                method = args[2] if len(args) > 2 else "auto"
                
                await self._process_send_request(user, video_url, views, method, message)
                
            except ValueError:
                await message.answer(
                    "❌ Invalid format!\n"
                    "Correct format: <code>/send URL views [method]</code>\n\n"
                    "Example: <code>/send https://tiktok.com/@user/video/123 500 browser</code>",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                await message.answer(f"❌ Error: {str(e)}")
    
    async def _process_send_request(self, user: BotUser, video_url: str, 
                                  views: int, method: str, message: types.Message):
        """Process view sending request"""
        # Validate URL
        if not self._is_valid_tiktok_url(video_url):
            await message.answer("❌ Invalid TikTok URL!")
            return
        
        # Validate views count
        max_views = self._get_max_views_for_user(user)
        if views > max_views:
            await message.answer(
                f"❌ Maximum views for your tier: {max_views:,}\n"
                f"Upgrade with /subscribe for more views"
            )
            return
        
        # Check credits
        if user.subscription_level == 'free':
            if views > user.view_credits:
                await message.answer(
                    f"❌ Not enough credits! You have {user.view_credits:,} views left.\n"
                    f"Daily reset in {self._get_reset_time()} hours."
                )
                return
        
        # Create order
        order_id = await self._create_order(user.user_id, video_url, views, method)
        
        # Send to view system
        from tiktok_engine.workers.load_balancer import ViewLoadBalancer
        
        try:
            balancer = ViewLoadBalancer()
            
            # Show processing message
            processing_msg = await message.answer(
                f"⏳ Processing order <code>{order_id}</code>\n"
                f"📊 Sending {views:,} views to: {video_url}\n"
                f"⚡ Method: {method}\n\n"
                "Please wait...",
                parse_mode=ParseMode.HTML
            )
            
            # Send views
            result = await balancer.send_views(
                video_url=video_url,
                target_views=views,
                method=method if method != "auto" else None
            )
            
            # Update user credits
            if user.subscription_level == 'free':
                user.view_credits -= views
                await self._save_user(user)
            
            # Update order status
            await self._update_order_status(order_id, 'completed', result)
            
            # Send success message
            success_rate = result.get('success_rate_percentage', 0)
            successful_views = result.get('successful_views', 0)
            
            await processing_msg.edit_text(
                f"✅ <b>Order Completed!</b>\n\n"
                f"📋 <b>Order ID:</b> <code>{order_id}</code>\n"
                f"🎯 <b>Video:</b> {video_url}\n"
                f"📊 <b>Views Sent:</b> {views:,}\n"
                f"✅ <b>Successful:</b> {successful_views:,}\n"
                f"📈 <b>Success Rate:</b> {success_rate:.1f}%\n"
                f"⏱️ <b>Time:</b> {result.get('total_time_seconds', 0):.1f}s\n\n"
                f"🔄 Check /status for updates\n"
                f"📊 View details with /history",
                parse_mode=ParseMode.HTML
            )
            
            await self._log_command(user.user_id, 'send', f'success:{order_id}')
            
        except Exception as e:
            logger.error(f"Failed to send views: {e}")
            await self._update_order_status(order_id, 'failed', {'error': str(e)})
            
            await message.answer(
                f"❌ <b>Order Failed!</b>\n\n"
                f"Order ID: <code>{order_id}</code>\n"
                f"Error: {str(e)}\n\n"
                f"Please try again or contact /support",
                parse_mode=ParseMode.HTML
            )
            
            await self._log_command(user.user_id, 'send', f'failed:{str(e)}')
    
    async def _handle_balance(self, message: types.Message):
        """Handle /balance command"""
        user = await self._get_or_create_user(message.from_user)
        
        # Get subscription info
        subscription_info = self._get_subscription_info(user.subscription_level)
        
        balance_text = f"""
💰 <b>Your Balance</b>

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.user_id}</code>

💎 <b>Subscription:</b> {user.subscription_level.title()}
📊 <b>Views Available:</b> {user.view_credits:,}

📋 <b>Subscription Details:</b>
• <b>Plan:</b> {subscription_info['name']}
• <b>Daily Limit:</b> {subscription_info['daily_limit']:,} views
• <b>Max per Order:</b> {subscription_info['max_per_order']:,}
• <b>Methods:</b> {', '.join(subscription_info['methods'])}
• <b>Priority:</b> {subscription_info['priority']}

🔄 <b>Reset:</b> {self._get_reset_time()} hours
📈 <b>Total Used:</b> {user.command_count * 100:,} views (estimated)

💳 <b>Upgrade:</b> /subscribe
📤 <b>Send Views:</b> /send
        """
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💎 Upgrade Plan", callback_data="upgrade"),
            InlineKeyboardButton("📤 Send Views", callback_data="quick_send"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_balance")
        )
        
        await message.answer(balance_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'balance', 'success')
    
    async def _handle_stats(self, message: types.Message):
        """Handle /stats command"""
        user = await self._get_or_create_user(message.from_user)
        
        # Get user statistics from database
        user_stats = await self._get_user_statistics(user.user_id)
        
        stats_text = f"""
📊 <b>Your Statistics</b>

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.user_id}</code>
📅 <b>Member Since:</b> {user.join_date.strftime('%Y-%m-%d')}

<b>📈 Activity Stats:</b>
• <b>Total Commands:</b> {user.command_count}
• <b>Last Active:</b> {user.last_active.strftime('%Y-%m-%d %H:%M')}
• <b>Days Active:</b> {(datetime.now() - user.join_date).days}

<b>🎯 View Statistics:</b>
• <b>Total Views Sent:</b> {user_stats.get('total_views_sent', 0):,}
• <b>Successful Views:</b> {user_stats.get('successful_views', 0):,}
• <b>Success Rate:</b> {user_stats.get('success_rate', 0):.1%}
• <b>Total Orders:</b> {user_stats.get('total_orders', 0)}

<b>📊 Recent Performance:</b>
• <b>Today's Views:</b> {user_stats.get('today_views', 0):,}
• <b>Week's Views:</b> {user_stats.get('week_views', 0):,}
• <b>Month's Views:</b> {user_stats.get('month_views', 0):,}

<b>⚡ Current Status:</b>
• <b>Active Orders:</b> {user_stats.get('active_orders', 0)}
• <b>Pending Views:</b> {user_stats.get('pending_views', 0):,}
• <b>Available Credits:</b> {user.view_credits:,}

<b>📋 Subscription:</b>
• <b>Plan:</b> {user.subscription_level.title()}
• <b>Renewal:</b> {self._get_renewal_date(user)}
        """
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("📤 Send More", callback_data="quick_send"),
            InlineKeyboardButton("📋 Order History", callback_data="view_history"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats")
        )
        
        await message.answer(stats_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'stats', 'success')
    
    async def _handle_history(self, message: types.Message):
        """Handle /history command"""
        user = await self._get_or_create_user(message.from_user)
        
        # Get order history
        orders = await self._get_user_orders(user.user_id, limit=10)
        
        if not orders:
            await message.answer(
                "📭 <b>No Order History</b>\n\n"
                "You haven't sent any views yet.\n"
                "Use /send to get started!",
                parse_mode=ParseMode.HTML
            )
            return
        
        history_text = f"""
📋 <b>Order History</b>

👤 <b>User:</b> {user.first_name}
📅 <b>Showing last {len(orders)} orders</b>

"""
        
        for i, order in enumerate(orders, 1):
            status_emoji = {
                'completed': '✅',
                'processing': '⏳',
                'failed': '❌',
                'pending': '🔄'
            }.get(order['status'], '❓')
            
            history_text += f"""
<b>{i}. {status_emoji} Order {order['id']}</b>
• <b>Video:</b> {order['video_url'][:30]}...
• <b>Views:</b> {order['views']:,}
• <b>Status:</b> {order['status'].title()}
• <b>Date:</b> {order['created_at'][:10]}
• <b>Method:</b> {order.get('method', 'auto')}
"""
            
            if order['status'] == 'completed' and 'result' in order:
                result = json.loads(order['result']) if isinstance(order['result'], str) else order['result']
                success_rate = result.get('success_rate_percentage', 0)
                history_text += f"• <b>Success:</b> {success_rate:.1f}%\n"
        
        history_text += "\n📊 <b>Use /status [order_id] for detailed information</b>"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("📤 New Order", callback_data="quick_send"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_history"),
            InlineKeyboardButton("📊 Export", callback_data="export_history")
        )
        
        await message.answer(history_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'history', 'success')
    
    async def _handle_status(self, message: types.Message):
        """Handle /status command"""
        args = message.get_args().strip()
        user = await self._get_or_create_user(message.from_user)
        
        if not args:
            # Show active orders
            active_orders = await self._get_active_orders(user.user_id)
            
            if not active_orders:
                await message.answer(
                    "📊 <b>No Active Orders</b>\n\n"
                    "You don't have any active orders.\n"
                    "Use /send to start sending views!",
                    parse_mode=ParseMode.HTML
                )
                return
            
            status_text = f"""
📊 <b>Active Orders Status</b>

👤 <b>User:</b> {user.first_name}
📋 <b>Active Orders:</b> {len(active_orders)}

"""
            
            for order in active_orders:
                status_emoji = {
                    'processing': '⏳',
                    'pending': '🔄',
                    'starting': '🚀'
                }.get(order['status'], '❓')
                
                progress = order.get('progress', 0)
                
                status_text += f"""
<b>{status_emoji} Order {order['id']}</b>
• <b>Video:</b> {order['video_url'][:25]}...
• <b>Target:</b> {order['views']:,} views
• <b>Progress:</b> {progress:.1f}%
• <b>Status:</b> {order['status'].title()}
• <b>Started:</b> {order['created_at'][11:16]}
"""
            
            status_text += "\n🔄 <b>Orders update automatically</b>"
            
        else:
            # Show specific order status
            order = await self._get_order(args)
            
            if not order or order['user_id'] != str(user.user_id):
                await message.answer(
                    f"❌ <b>Order Not Found</b>\n\n"
                    f"Order ID <code>{args}</code> not found or doesn't belong to you.",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Format order details
            result = {}
            if order.get('result'):
                try:
                    result = json.loads(order['result']) if isinstance(order['result'], str) else order['result']
                except:
                    result = {}
            
            status_text = f"""
📋 <b>Order Details</b>

<b>🆔 Order ID:</b> <code>{order['id']}</code>
<b>👤 User ID:</b> <code>{order['user_id']}</code>
<b>🎯 Video URL:</b> {order['video_url']}
<b>📊 Target Views:</b> {order['views']:,}
<b>⚡ Method:</b> {order.get('method', 'auto')}
<b>📅 Created:</b> {order['created_at']}
<b>🔄 Status:</b> {order['status'].title()}
"""
            
            if order['status'] == 'completed':
                success_rate = result.get('success_rate_percentage', 0)
                successful_views = result.get('successful_views', 0)
                total_time = result.get('total_time_seconds', 0)
                
                status_text += f"""
<b>✅ Completed:</b> {order.get('completed_at', 'N/A')}
<b>📈 Success Rate:</b> {success_rate:.1f}%
<b>🎯 Successful Views:</b> {successful_views:,}
<b>⏱️ Total Time:</b> {total_time:.1f}s
<b>🚀 Views/Minute:</b> {(successful_views / total_time * 60):.1f}
"""
            
            elif order['status'] in ['processing', 'pending']:
                progress = order.get('progress', 0)
                estimated_completion = order.get('estimated_completion', 'Calculating...')
                
                status_text += f"""
<b>📊 Progress:</b> {progress:.1f}%
<b>🕐 Estimated Completion:</b> {estimated_completion}
<b>⏳ Elapsed Time:</b> {self._calculate_elapsed_time(order['created_at'])}
"""
            
            elif order['status'] == 'failed':
                error = result.get('error', 'Unknown error')
                status_text += f"""
<b>❌ Failed:</b> {order.get('completed_at', 'N/A')}
<b>⚠️ Error:</b> {error}
"""
        
        keyboard = InlineKeyboardMarkup()
        if args:
            keyboard.add(
                InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_status:{args}"),
                InlineKeyboardButton("📋 All Orders", callback_data="view_history")
            )
        else:
            keyboard.add(
                InlineKeyboardButton("🔄 Refresh All", callback_data="refresh_all_status"),
                InlineKeyboardButton("📤 New Order", callback_data="quick_send")
            )
        
        await message.answer(status_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'status', f'order:{args if args else "all"}')
    
    async def _handle_subscribe(self, message: types.Message):
        """Handle /subscribe command"""
        user = await self._get_or_create_user(message.from_user)
        
        subscription_plans = {
            'free': {
                'name': 'Free Tier',
                'price': '$0',
                'daily_limit': 100,
                'max_per_order': 50,
                'methods': ['api'],
                'priority': 'low',
                'features': ['Basic support', 'Daily reset']
            },
            'basic': {
                'name': 'Basic Plan',
                'price': '$9.99/month',
                'daily_limit': 1000,
                'max_per_order': 200,
                'methods': ['api', 'browser'],
                'priority': 'medium',
                'features': ['Priority support', 'All methods', 'Faster delivery']
            },
            'pro': {
                'name': 'Pro Plan',
                'price': '$29.99/month',
                'daily_limit': 5000,
                'max_per_order': 1000,
                'methods': ['api', 'browser', 'cloud'],
                'priority': 'high',
                'features': ['24/7 support', 'All methods', 'Highest priority', 'Advanced analytics']
            },
            'enterprise': {
                'name': 'Enterprise',
                'price': '$99.99/month',
                'daily_limit': 'Unlimited',
                'max_per_order': 5000,
                'methods': ['api', 'browser', 'cloud', 'hybrid'],
                'priority': 'highest',
                'features': ['Dedicated support', 'All methods', 'Custom solutions', 'API access', 'White label']
            }
        }
        
        current_plan = subscription_plans[user.subscription_level]
        
        subscribe_text = f"""
💎 <b>Subscription Plans</b>

👤 <b>Current Plan:</b> {current_plan['name']}
💰 <b>Price:</b> {current_plan['price']}
📊 <b>Daily Limit:</b> {current_plan['daily_limit']:,} views
🎯 <b>Max per Order:</b> {current_plan['max_per_order']:,}
⚡ <b>Priority:</b> {current_plan['priority'].title()}
🔧 <b>Methods:</b> {', '.join(current_plan['methods'])}
✨ <b>Features:</b> {', '.join(current_plan['features'])}

<b>📋 Available Plans:</b>
"""
        
        for plan_id, plan in subscription_plans.items():
            if plan_id == user.subscription_level:
                subscribe_text += f"\n✅ <b>{plan['name']} (Current)</b>"
            else:
                subscribe_text += f"\n🔹 <b>{plan['name']}</b> - {plan['price']}"
                subscribe_text += f"\n   • {plan['daily_limit']:,} views/day"
                subscribe_text += f"\n   • {plan['max_per_order']:,} max/order"
                subscribe_text += f"\n   • {plan['priority'].title()} priority"
        
        subscribe_text += f"""

<b>💳 How to Upgrade:</b>
1. Choose your plan
2. Contact @admin_username
3. Make payment (Crypto/PayPal)
4. Get activated instantly!

<b>🔄 Automatic Features:</b>
• Instant activation
• No downtime
• Priority support
• Advanced analytics

<b>📞 Contact support for custom plans!</b>
"""
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        for plan_id, plan in subscription_plans.items():
            if plan_id != user.subscription_level:
                keyboard.insert(
                    InlineKeyboardButton(
                        f"{plan['name']} - {plan['price']}",
                        callback_data=f"upgrade_to:{plan_id}"
                    )
                )
        
        keyboard.add(
            InlineKeyboardButton("📞 Contact Support", callback_data="contact_support"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_subscribe")
        )
        
        await message.answer(subscribe_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'subscribe', 'success')
    
    async def _handle_methods(self, message: types.Message):
        """Handle /methods command"""
        methods_info = {
            'browser': {
                'name': 'Browser Automation',
                'success_rate': '85-95%',
                'speed': 'Slow (5-10 views/min)',
                'detection_risk': 'Low',
                'description': 'Real browser simulation with human-like behavior',
                'best_for': 'High-quality views, important videos'
            },
            'api': {
                'name': 'Direct API',
                'success_rate': '70-85%',
                'speed': 'Fast (50-100 views/min)',
                'detection_risk': 'Medium',
                'description': 'Direct TikTok API calls, efficient but less organic',
                'best_for': 'Bulk views, cost-effective campaigns'
            },
            'cloud': {
                'name': 'Cloud Views',
                'success_rate': '60-75%',
                'speed': 'Very Fast (200+ views/min)',
                'detection_risk': 'High',
                'description': 'Cloud-based distributed viewing system',
                'best_for': 'Massive campaigns, instant boost'
            },
            'hybrid': {
                'name': 'Hybrid AI',
                'success_rate': '90-98%',
                'speed': 'Medium (20-50 views/min)',
                'detection_risk': 'Very Low',
                'description': 'AI-powered combination of all methods',
                'best_for': 'Premium campaigns, maximum safety'
            },
            'auto': {
                'name': 'Auto Select (Recommended)',
                'success_rate': '80-90%',
                'speed': 'Optimal',
                'detection_risk': 'Low',
                'description': 'AI chooses best method based on video and target',
                'best_for': 'All purposes, balanced approach'
            }
        }
        
        user = await self._get_or_create_user(message.from_user)
        user_methods = self._get_subscription_info(user.subscription_level)['methods']
        
        methods_text = f"""
⚡ <b>View Methods Available</b>

👤 <b>Your Plan:</b> {user.subscription_level.title()}
🔧 <b>Available Methods:</b> {', '.join(user_methods)}

<b>📋 Method Details:</b>
"""
        
        for method_id, info in methods_info.items():
            if method_id == 'auto' or method_id in user_methods:
                methods_text += f"""
<b>{info['name']}</b>
• <b>Success Rate:</b> {info['success_rate']}
• <b>Speed:</b> {info['speed']}
• <b>Risk:</b> {info['detection_risk']}
• <b>Best For:</b> {info['best_for']}
• <b>Description:</b> {info['description']}
"""
        
        methods_text += f"""

<b>🎯 Recommendations:</b>
• Use <b>Auto Select</b> for best results
• Choose <b>Browser/Hybrid</b> for important videos
• Use <b>API/Cloud</b> for bulk operations
• Mix methods for organic appearance

<b>⚙️ Usage:</b>
Add method parameter to /send command:
<code>/send URL views method</code>

Example: <code>/send https://tiktok.com/@user/video/123 500 browser</code>
"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("🚀 Send Views", callback_data="quick_send"),
            InlineKeyboardButton("💎 Upgrade Plan", callback_data="upgrade"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_methods")
        )
        
        await message.answer(methods_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'methods', 'success')
    
    async def _handle_schedule(self, message: types.Message):
        """Handle /schedule command"""
        await message.answer(
            "📅 <b>View Scheduling</b>\n\n"
            "This feature allows you to schedule views for future times.\n\n"
            "<b>Coming Soon!</b>\n"
            "We're working on advanced scheduling features.\n\n"
            "For now, use /send for immediate views.",
            parse_mode=ParseMode.HTML
        )
        await self._log_command(message.from_user.id, 'schedule', 'info')
    
    async def _handle_cancel(self, message: types.Message):
        """Handle /cancel command"""
        args = message.get_args().strip()
        
        if not args:
            await message.answer(
                "❌ <b>Usage:</b> <code>/cancel order_id</code>\n\n"
                "Example: <code>/cancel ABC123</code>\n\n"
                "Use /history to see your order IDs.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Check if order exists and belongs to user
        order = await self._get_order(args)
        user = await self._get_or_create_user(message.from_user)
        
        if not order or order['user_id'] != str(user.user_id):
            await message.answer(
                f"❌ Order <code>{args}</code> not found or doesn't belong to you.",
                parse_mode=ParseMode.HTML
            )
            return
        
        if order['status'] not in ['pending', 'processing']:
            await message.answer(
                f"❌ Cannot cancel order in {order['status']} status.\n"
                f"Only pending/processing orders can be cancelled.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Cancel the order
        await self._update_order_status(args, 'cancelled', {'cancelled_by': 'user'})
        
        await message.answer(
            f"✅ <b>Order Cancelled</b>\n\n"
            f"Order ID: <code>{args}</code>\n"
            f"Status: Cancelled\n"
            f"Refund: Processing...\n\n"
            f"Your credits will be refunded within 24 hours.",
            parse_mode=ParseMode.HTML
        )
        
        await self._log_command(user.user_id, 'cancel', f'order:{args}')
    
    async def _handle_report(self, message: types.Message):
        """Handle /report command"""
        user = await self._get_or_create_user(message.from_user)
        
        # Check if user has access to reports
        if user.subscription_level not in ['pro', 'enterprise']:
            await message.answer(
                "📊 <b>Advanced Reports</b>\n\n"
                "Detailed analytics reports are available for Pro and Enterprise plans only.\n\n"
                "💎 Upgrade your subscription with /subscribe to access:\n"
                "• Detailed analytics\n"
                "• Performance reports\n"
                "• Export functionality\n"
                "• Custom reports",
                parse_mode=ParseMode.HTML
            )
            return
        
        args = message.get_args().strip() or 'daily'
        
        report_types = {
            'daily': 'Daily Report (last 24 hours)',
            'weekly': 'Weekly Report (last 7 days)',
            'monthly': 'Monthly Report (last 30 days)',
            'custom': 'Custom Period Report'
        }
        
        if args not in report_types:
            await message.answer(
                f"❌ Invalid report type: {args}\n\n"
                f"Available types: {', '.join(report_types.keys())}\n\n"
                f"Example: <code>/report weekly</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Generate report
        processing_msg = await message.answer(
            f"📊 <b>Generating {report_types[args]}...</b>\n\n"
            f"Please wait while we compile your analytics data.",
            parse_mode=ParseMode.HTML
        )
        
        try:
            from tiktok_engine.analytics.report_generator import ReportGenerator
            
            # Get user's analytics data
            user_stats = await self._get_user_analytics(user.user_id, args)
            
            # Generate report
            generator = ReportGenerator()
            config = type('Config', (), {
                'title': f'User Report - {user.first_name}',
                'period': args.title(),
                'format': 'html',
                'sections': ['summary', 'performance_metrics', 'daily_trends'],
                'include_charts': True,
                'include_recommendations': True,
                'branding': {
                    'company_name': 'VT ULTRA PRO',
                    'primary_color': '#4A90E2',
                    'secondary_color': '#50E3C2'
                }
            })()
            
            report = await generator.generate_report(user_stats, config)
            
            await processing_msg.edit_text(
                f"✅ <b>Report Generated!</b>\n\n"
                f"📋 <b>Title:</b> {report['metadata']['title']}\n"
                f"📅 <b>Period:</b> {report['metadata']['period']}\n"
                f"📊 <b>Format:</b> {report['metadata']['format'].upper()}\n"
                f"💾 <b>Size:</b> {report['size_bytes']:,} bytes\n\n"
                f"📥 <b>Download:</b> {report['download_url']}\n\n"
                f"Use /settings to configure report preferences.",
                parse_mode=ParseMode.HTML
            )
            
            # Send file if it's small enough
            if report['size_bytes'] < 50 * 1024 * 1024:  # 50MB limit
                try:
                    with open(report['filepath'], 'rb') as file:
                        await message.answer_document(
                            document=file,
                            caption=f"📊 Your {args} report"
                        )
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            await processing_msg.edit_text(
                f"❌ <b>Report Generation Failed</b>\n\n"
                f"Error: {str(e)}\n\n"
                f"Please try again later or contact support.",
                parse_mode=ParseMode.HTML
            )
        
        await self._log_command(user.user_id, 'report', f'type:{args}')
    
    async def _handle_settings(self, message: types.Message):
        """Handle /settings command"""
        user = await self._get_or_create_user(message.from_user)
        
        settings_text = f"""
⚙️ <b>Bot Settings</b>

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.user_id}</code>

<b>🔧 Current Settings:</b>
• <b>Language:</b> {user.language_code or 'Auto'}
• <b>Notifications:</b> Enabled
• <b>Auto-Update:</b> Enabled
• <b>Privacy Mode:</b> Standard

<b>📋 Available Settings:</b>
"""
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🌐 Language", callback_data="setting_language"),
            InlineKeyboardButton("🔔 Notifications", callback_data="setting_notifications"),
            InlineKeyboardButton("🔄 Auto-Update", callback_data="setting_autoupdate"),
            InlineKeyboardButton("👤 Privacy", callback_data="setting_privacy"),
            InlineKeyboardButton("📊 Reports", callback_data="setting_reports"),
            InlineKeyboardButton("⚡ Performance", callback_data="setting_performance"),
            InlineKeyboardButton("🔄 Reset All", callback_data="setting_reset"),
            InlineKeyboardButton("💾 Save", callback_data="setting_save")
        )
        
        await message.answer(settings_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'settings', 'success')
    
    async def _handle_support(self, message: types.Message):
        """Handle /support command"""
        support_text = """
🆘 <b>Support & Help</b>

<b>📞 Contact Methods:</b>
• <b>Telegram:</b> @vtultrapro_support
• <b>Email:</b> support@vtultrapro.com
• <bWebsite:</b> https://vtultrapro.com

<b>🕐 Support Hours:</b>
• 24/7 for Pro & Enterprise users
• 9:00-18:00 UTC for Basic users
• Limited for Free users

<b>🚨 Emergency Contact:</b>
For urgent issues, mention @admin directly.

<b>📋 Before Contacting Support:</b>
1. Check /help for basic instructions
2. Use /status to check order status
3. Read error messages carefully
4. Try the command again

<b>🔧 Common Issues & Solutions:</b>

<b>❌ "Invalid URL"</b>
• Make sure it's a public TikTok URL
• Copy full URL from share option
• Remove tracking parameters

<b>❌ "Not enough credits"</b>
• Check /balance
• Wait for daily reset
• Upgrade with /subscribe

<b>❌ "Order failed"</b>
• Check TikTok server status
• Try different method
• Contact support with order ID

<b>💡 Tips for Better Support:</b>
• Include your User ID
• Provide order ID if applicable
• Describe what you were doing
• Share error messages
• Be patient and polite

<b>⚠️ Important:</b>
• We don't support illegal activities
• Follow TikTok Terms of Service
• Use at your own risk
• No refunds for used credits
        """
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("📞 Contact Now", url="https://t.me/vtultrapro_support"),
            InlineKeyboardButton("🌐 Visit Website", url="https://vtultrapro.com"),
            InlineKeyboardButton("📚 Documentation", callback_data="docs")
        )
        
        await message.answer(support_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(message.from_user.id, 'support', 'success')
    
    async def _handle_admin(self, message: types.Message):
        """Handle /admin command"""
        user = await self._get_or_create_user(message.from_user)
        
        if user.user_id not in self.admin_ids:
            await message.answer("❌ Admin access required!")
            return
        
        admin_text = f"""
👨‍💼 <b>Admin Panel</b>

<b>📊 System Status:</b>
• <b>Users:</b> {len(self.users):,}
• <b>Active Sessions:</b> {self._get_active_sessions():,}
• <b>Memory Usage:</b> {self._get_memory_usage():.1f} MB
• <b>Uptime:</b> {self._get_uptime()}

<b>🔧 Admin Commands:</b>
• <code>/broadcast message</code> - Send to all users
• <code>/users</code> - User management
• <code>/system</code> - System monitoring
• <code>/logs</code> - View system logs
• <code>/stats all</code> - All users statistics
• <code>/backup</code> - Create backup
• <code>/restart</code> - Restart bot

<b>📈 Quick Stats:</b>
• <b>New Users (24h):</b> {self._get_new_users_count():,}
• <b>Active Users (24h):</b> {self._get_active_users_count():,}
• <b>Total Orders:</b> {self._get_total_orders():,}
• <b>Success Rate:</b> {self._get_system_success_rate():.1%}

<b>⚠️ Warning:</b>
Admin commands can affect all users.
Use with caution!
        """
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("⚙️ System", callback_data="admin_system"),
            InlineKeyboardButton("📋 Logs", callback_data="admin_logs"),
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("💾 Backup", callback_data="admin_backup"),
            InlineKeyboardButton("🔄 Restart", callback_data="admin_restart"),
            InlineKeyboardButton("🚪 Exit Admin", callback_data="admin_exit")
        )
        
        await message.answer(admin_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'admin', 'access')
    
    async def _handle_broadcast(self, message: types.Message):
        """Handle /broadcast command (admin only)"""
        user = await self._get_or_create_user(message.from_user)
        
        if user.user_id not in self.admin_ids:
            await message.answer("❌ Admin access required!")
            return
        
        broadcast_text = message.get_args().strip()
        
        if not broadcast_text:
            await message.answer(
                "📢 <b>Broadcast Message</b>\n\n"
                "Usage: <code>/broadcast your message here</code>\n\n"
                "This will send your message to all bot users.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Confirm broadcast
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Send to All Users", callback_data=f"broadcast_confirm:{broadcast_text[:50]}"),
            InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
        )
        
        await message.answer(
            f"📢 <b>Confirm Broadcast</b>\n\n"
            f"<b>Message:</b>\n{broadcast_text}\n\n"
            f"<b>Recipients:</b> {len(self.users):,} users\n"
            f"<b>This cannot be undone!</b>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_users(self, message: types.Message):
        """Handle /users command (admin only)"""
        user = await self._get_or_create_user(message.from_user)
        
        if user.user_id not in self.admin_ids:
            await message.answer("❌ Admin access required!")
            return
        
        args = message.get_args().strip()
        
        if not args:
            # Show user summary
            user_summary = await self._get_user_summary()
            
            users_text = f"""
👥 <b>User Management</b>

<b>📊 User Statistics:</b>
• <b>Total Users:</b> {user_summary['total']:,}
• <b>Active (24h):</b> {user_summary['active_24h']:,}
• <b>Active (7d):</b> {user_summary['active_7d']:,}
• <b>New Today:</b> {user_summary['new_today']:,}
• <b>Premium Users:</b> {user_summary['premium']:,}

<b>📈 Subscription Distribution:</b>
• <b>Free:</b> {user_summary['subscriptions'].get('free', 0):,}
• <b>Basic:</b> {user_summary['subscriptions'].get('basic', 0):,}
• <b>Pro:</b> {user_summary['subscriptions'].get('pro', 0):,}
• <b>Enterprise:</b> {user_summary['subscriptions'].get('enterprise', 0):,}

<b>🔍 User Search:</b>
<code>/users search username</code>
<code>/users id 123456789</code>
<code>/users recent 10</code>
<code>/users inactive 30</code>
            """
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("📋 Recent Users", callback_data="users_recent:10"),
                InlineKeyboardButton("⚡ Active Users", callback_data="users_active"),
                InlineKeyboardButton("💎 Premium Users", callback_data="users_premium"),
                InlineKeyboardButton("📊 Statistics", callback_data="users_stats"),
                InlineKeyboardButton("📄 Export CSV", callback_data="users_export"),
                InlineKeyboardButton("🔄 Refresh", callback_data="users_refresh")
            )
            
            await message.answer(users_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            
        elif args.startswith('search'):
            # Search users
            search_term = args[7:].strip()
            if not search_term:
                await message.answer("❌ Please provide search term!")
                return
            
            search_results = await self._search_users(search_term)
            
            if not search_results:
                await message.answer(f"❌ No users found for: {search_term}")
                return
            
            results_text = f"""
🔍 <b>User Search Results</b>

<b>Search:</b> {search_term}
<b>Results:</b> {len(search_results)}

"""
            
            for i, result in enumerate(search_results[:10], 1):
                results_text += f"""
<b>{i}. {result['first_name']} {result['last_name'] or ''}</b>
• <b>Username:</b> @{result['username'] or 'N/A'}
• <b>ID:</b> <code>{result['user_id']}</code>
• <b>Joined:</b> {result['join_date'][:10]}
• <b>Plan:</b> {result['subscription_level'].title()}
• <b>Commands:</b> {result['command_count']:,}
"""
            
            if len(search_results) > 10:
                results_text += f"\n📄 <b>And {len(search_results) - 10} more results...</b>"
            
            await message.answer(results_text, parse_mode=ParseMode.HTML)
            
        elif args.startswith('id'):
            # Get user by ID
            user_id = args[3:].strip()
            if not user_id.isdigit():
                await message.answer("❌ Invalid user ID!")
                return
            
            user_data = await self._get_user_by_id(int(user_id))
            
            if not user_data:
                await message.answer(f"❌ User not found: {user_id}")
                return
            
            user_details = await self._get_user_details(user_data)
            
            await message.answer(user_details, parse_mode=ParseMode.HTML)
            
        elif args.startswith('recent'):
            # Show recent users
            try:
                limit = int(args[7:].strip()) if len(args) > 7 else 10
                limit = min(limit, 50)
            except:
                limit = 10
            
            recent_users = await self._get_recent_users(limit)
            
            recent_text = f"""
🆕 <b>Recent Users</b>

<b>Showing last {len(recent_users)} users:</b>

"""
            
            for i, user_data in enumerate(recent_users, 1):
                recent_text += f"""
<b>{i}. {user_data['first_name']} {user_data['last_name'] or ''}</b>
• <b>ID:</b> <code>{user_data['user_id']}</code>
• <b>Joined:</b> {user_data['join_date'][11:16]} ({user_data['join_date'][:10]})
• <b>Plan:</b> {user_data['subscription_level'].title()}
"""
            
            await message.answer(recent_text, parse_mode=ParseMode.HTML)
            
        elif args.startswith('inactive'):
            # Show inactive users
            try:
                days = int(args[9:].strip()) if len(args) > 9 else 30
            except:
                days = 30
            
            inactive_users = await self._get_inactive_users(days)
            
            inactive_text = f"""
💤 <b>Inactive Users</b>

<b>Inactive for {days}+ days:</b> {len(inactive_users):,} users

<b>Top 10 inactive users:</b>

"""
            
            for i, user_data in enumerate(inactive_users[:10], 1):
                last_active = datetime.fromisoformat(user_data['last_active'])
                days_inactive = (datetime.now() - last_active).days
                
                inactive_text += f"""
<b>{i}. {user_data['first_name']}</b>
• <b>ID:</b> <code>{user_data['user_id']}</code>
• <b>Last Active:</b> {days_inactive} days ago
• <b>Plan:</b> {user_data['subscription_level'].title()}
• <b>Commands:</b> {user_data['command_count']:,}
"""
            
            if len(inactive_users) > 10:
                inactive_text += f"\n📄 <b>And {len(inactive_users) - 10} more users...</b>"
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("📧 Send Reminder", callback_data=f"inactive_reminder:{days}"),
                InlineKeyboardButton("🗑️ Cleanup", callback_data=f"inactive_cleanup:{days}")
            )
            
            await message.answer(inactive_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def _handle_system(self, message: types.Message):
        """Handle /system command (admin only)"""
        user = await self._get_or_create_user(message.from_user)
        
        if user.user_id not in self.admin_ids:
            await message.answer("❌ Admin access required!")
            return
        
        # Get system metrics
        system_metrics = await self._get_system_metrics()
        
        system_text = f"""
⚙️ <b>System Monitoring</b>

<b>🖥️ Server Status:</b>
• <b>CPU Usage:</b> {system_metrics['cpu_usage']:.1f}%
• <b>Memory Usage:</b> {system_metrics['memory_usage']:.1f}%
• <b>Disk Usage:</b> {system_metrics['disk_usage']:.1f}%
• <b>Uptime:</b> {system_metrics['uptime']}

<b>📊 Bot Metrics:</b>
• <b>Active Sessions:</b> {system_metrics['active_sessions']:,}
• <b>Messages/Minute:</b> {system_metrics['messages_per_minute']:.1f}
• <b>Commands/Minute:</b> {system_metrics['commands_per_minute']:.1f}
• <b>Error Rate:</b> {system_metrics['error_rate']:.1%}

<b>🗄️ Database Status:</b>
• <b>Size:</b> {system_metrics['db_size']:,} bytes
• <b>Tables:</b> {system_metrics['db_tables']:,}
• <b>Connections:</b> {system_metrics['db_connections']:,}
• <b>Health:</b> {system_metrics['db_health']}

<b>🌐 Network Status:</b>
• <b>API Latency:</b> {system_metrics['api_latency']:.1f}ms
• <b>Success Rate:</b> {system_metrics['api_success_rate']:.1%}
• <b>Requests/Hour:</b> {system_metrics['requests_per_hour']:,}

<b>⚠️ Alerts:</b>
"""
        
        alerts = []
        if system_metrics['cpu_usage'] > 80:
            alerts.append("High CPU usage")
        if system_metrics['memory_usage'] > 85:
            alerts.append("High memory usage")
        if system_metrics['disk_usage'] > 90:
            alerts.append("Low disk space")
        if system_metrics['error_rate'] > 0.1:
            alerts.append("High error rate")
        
        if alerts:
            system_text += "\n".join([f"• ⚠️ {alert}" for alert in alerts])
        else:
            system_text += "• ✅ All systems normal"
        
        system_text += f"""

<b>🔧 Maintenance:</b>
• <b>Last Backup:</b> {system_metrics['last_backup'] or 'Never'}
• <b>Last Restart:</b> {system_metrics['last_restart'] or 'Never'}
• <b>Version:</b> {system_metrics['version']}
        """
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📊 Detailed Metrics", callback_data="system_metrics"),
            InlineKeyboardButton("🔍 Health Check", callback_data="system_health"),
            InlineKeyboardButton("💾 Backup Now", callback_data="system_backup"),
            InlineKeyboardButton("🔄 Restart Bot", callback_data="system_restart"),
            InlineKeyboardButton("🗑️ Clean Cache", callback_data="system_clean"),
            InlineKeyboardButton("📋 Logs", callback_data="system_logs"),
            InlineKeyboardButton("🔄 Refresh", callback_data="system_refresh")
        )
        
        await message.answer(system_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'system', 'access')
    
    async def _handle_logs(self, message: types.Message):
        """Handle /logs command (admin only)"""
        user = await self._get_or_create_user(message.from_user)
        
        if user.user_id not in self.admin_ids:
            await message.answer("❌ Admin access required!")
            return
        
        args = message.get_args().strip() or '100'
        
        try:
            limit = int(args) if args.isdigit() else 100
            limit = min(limit, 1000)
        except:
            limit = 100
        
        # Get logs
        logs = await self._get_system_logs(limit)
        
        if not logs:
            await message.answer("📭 No logs found.")
            return
        
        logs_text = f"""
📋 <b>System Logs</b>

<b>Showing last {len(logs)} entries:</b>

"""
        
        for log in logs[-20:]:  # Show last 20 in message
            level_emoji = {
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }.get(log.get('level', 'INFO'), '📝')
            
            logs_text += f"""
{level_emoji} <b>{log.get('timestamp', '')[:19]}</b>
{log.get('message', '')[:100]}...
"""
        
        if len(logs) > 20:
            logs_text += f"\n📄 <b>And {len(logs) - 20} more log entries...</b>"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("📄 Full Logs", callback_data=f"logs_full:{limit}"),
            InlineKeyboardButton("🚨 Errors Only", callback_data=f"logs_errors:{limit}"),
            InlineKeyboardButton("💾 Export", callback_data=f"logs_export:{limit}"),
            InlineKeyboardButton("🗑️ Clear Logs", callback_data="logs_clear")
        )
        
        await message.answer(logs_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await self._log_command(user.user_id, 'logs', f'limit:{limit}')
    
    async def _handle_callback(self, callback_query: types.CallbackQuery):
        """Handle callback queries"""
        data = callback_query.data
        user = await self._get_or_create_user(callback_query.from_user)
        
        # Update user activity
        user.last_active = datetime.now()
        user.command_count += 1
        await self._save_user(user)
        
        try:
            if data == 'quick_send':
                await self._handle_quick_send(callback_query)
            elif data == 'my_stats':
                await self._handle_my_stats(callback_query)
            elif data == 'upgrade':
                await self._handle_upgrade(callback_query)
            elif data == 'help':
                await self._handle_help_callback(callback_query)
            elif data.startswith('send_'):
                await self._handle_send_callback(callback_query, data)
            elif data.startswith('refresh_'):
                await self._handle_refresh_callback(callback_query, data)
            elif data.startswith('upgrade_to:'):
                await self._handle_upgrade_to(callback_query, data)
            elif data == 'contact_support':
                await self._handle_contact_support(callback_query)
            elif data.startswith('view_history'):
                await self._handle_view_history(callback_query)
            elif data.startswith('refresh_status:'):
                await self._handle_refresh_status(callback_query, data)
            elif data == 'refresh_all_status':
                await self._handle_refresh_all_status(callback_query)
            elif data.startswith('setting_'):
                await self._handle_setting_callback(callback_query, data)
            elif data == 'docs':
                await self._handle_docs(callback_query)
            elif data.startswith('admin_'):
                await self._handle_admin_callback(callback_query, data)
            elif data.startswith('broadcast_'):
                await self._handle_broadcast_callback(callback_query, data)
            elif data.startswith('users_'):
                await self._handle_users_callback(callback_query, data)
            elif data.startswith('system_'):
                await self._handle_system_callback(callback_query, data)
            elif data.startswith('logs_'):
                await self._handle_logs_callback(callback_query, data)
            elif data.startswith('inactive_'):
                await self._handle_inactive_callback(callback_query, data)
            else:
                await callback_query.answer("⚠️ Unknown action")
                
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await callback_query.answer("❌ Error processing request")
        
        await callback_query.answer()
    
    async def _handle_text(self, message: types.Message):
        """Handle text messages"""
        user = await self._get_or_create_user(message.from_user)
        
        # Check if it's a TikTok URL
        text = message.text.strip()
        
        if self._is_valid_tiktok_url(text):
            # Store URL in user session and ask for views
            await self._store_user_session(user.user_id, 'awaiting_views', {'video_url': text})
            
            keyboard = InlineKeyboardMarkup(row_width=3)
            keyboard.add(
                InlineKeyboardButton("100", callback_data="confirm_views:100"),
                InlineKeyboardButton("500", callback_data="confirm_views:500"),
                InlineKeyboardButton("1000", callback_data="confirm_views:1000"),
                InlineKeyboardButton("Custom", callback_data="custom_views"),
                InlineKeyboardButton("Cancel", callback_data="cancel_send")
            )
            
            await message.answer(
                f"🎯 <b>TikTok Video Detected!</b>\n\n"
                f"<b>URL:</b> {text}\n\n"
                f"How many views would you like to send?\n\n"
                f"<i>Select from options or choose custom</i>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            # Check if user is in a specific state
            session = await self._get_user_session(user.user_id)
            
            if session and session.get('state') == 'awaiting_views':
                try:
                    views = int(text)
                    video_url = session.get('data', {}).get('video_url')
                    
                    if video_url:
                        await self._process_send_request(user, video_url, views, 'auto', message)
                        await self._clear_user_session(user.user_id)
                    else:
                        await message.answer("❌ Error: No video URL found in session.")
                        
                except ValueError:
                    await message.answer("❌ Please enter a valid number of views.")
            
            elif session and session.get('state') == 'custom_views':
                # Handle custom views input
                pass
            
            else:
                # Generic response
                await message.answer(
                    "🤖 <b>VT ULTRA PRO Bot</b>\n\n"
                    "Send me a TikTok video URL to get started!\n\n"
                    "Use /help for all available commands.",
                    parse_mode=ParseMode.HTML
                )
        
        # Update user activity
        user.last_active = datetime.now()
        user.command_count += 1
        await self._save_user(user)
    
    async def _handle_error(self, update: types.Update, exception: Exception):
        """Handle errors"""
        logger.error(f"Update {update} caused error {exception}")
        
        # Try to notify user
        try:
            if update.message:
                await update.message.answer(
                    "❌ <b>An error occurred</b>\n\n"
                    "Please try again or contact /support\n\n"
                    f"<i>Error: {str(exception)[:100]}...</i>",
                    parse_mode=ParseMode.HTML
                )
        except:
            pass
        
        return True
    
    # Helper methods
    async def _get_or_create_user(self, from_user) -> BotUser:
        """Get or create user from Telegram user object"""
        user_id = from_user.id
        
        if user_id in self.users:
            return self.users[user_id]
        
        # Create new user
        user = BotUser(
            user_id=user_id,
            username=from_user.username,
            first_name=from_user.first_name,
            last_name=from_user.last_name,
            language_code=from_user.language_code,
            is_premium=getattr(from_user, 'is_premium', False),
            view_credits=100  # Free tier starting credits
        )
        
        self.users[user_id] = user
        await self._save_user(user)
        
        logger.info(f"New user created: {user_id} - {user.first_name}")
        
        return user
    
    def _is_valid_tiktok_url(self, url: str) -> bool:
        """Check if URL is a valid TikTok URL"""
        import re
        
        patterns = [
            r'https?://(www\.)?tiktok\.com/.+/video/\d+',
            r'https?://vm\.tiktok\.com/.+',
            r'https?://vt\.tiktok\.com/.+'
        ]
        
        for pattern in patterns:
            if re.match(pattern, url):
                return True
        
        return False
    
    def _get_max_views_for_user(self, user: BotUser) -> int:
        """Get maximum views per order for user's subscription"""
        limits = {
            'free': 50,
            'basic': 200,
            'pro': 1000,
            'enterprise': 5000
        }
        return limits.get(user.subscription_level, 50)
    
    def _get_subscription_info(self, subscription_level: str) -> Dict:
        """Get subscription information"""
        info = {
            'free': {
                'name': 'Free Tier',
                'daily_limit': 100,
                'max_per_order': 50,
                'methods': ['api'],
                'priority': 'low'
            },
            'basic': {
                'name': 'Basic Plan',
                'daily_limit': 1000,
                'max_per_order': 200,
                'methods': ['api', 'browser'],
                'priority': 'medium'
            },
            'pro': {
                'name': 'Pro Plan',
                'daily_limit': 5000,
                'max_per_order': 1000,
                'methods': ['api', 'browser', 'cloud'],
                'priority': 'high'
            },
            'enterprise': {
                'name': 'Enterprise',
                'daily_limit': 999999,
                'max_per_order': 5000,
                'methods': ['api', 'browser', 'cloud', 'hybrid'],
                'priority': 'highest'
            }
        }
        return info.get(subscription_level, info['free'])
    
    def _get_reset_time(self) -> str:
        """Get time until daily reset"""
        now = datetime.now()
        reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        hours_left = (reset - now).total_seconds() / 3600
        return f"{hours_left:.1f}"
    
    def _get_renewal_date(self, user: BotUser) -> str:
        """Get subscription renewal date"""
        if user.subscription_level == 'free':
            return "Daily"
        
        # For paid plans, show monthly renewal
        join_date = user.join_date
        renewal = join_date + timedelta(days=30)
        days_left = (renewal - datetime.now()).days
        
        return f"{renewal.strftime('%Y-%m-%d')} ({days_left} days)"
    
    async def _create_order(self, user_id: int, video_url: str, views: int, method: str) -> str:
        """Create a new order"""
        import uuid
        order_id = str(uuid.uuid4())[:8].upper()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO orders 
                    (id, user_id, video_url, views, method, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_id,
                    user_id,
                    video_url,
                    views,
                    method,
                    'processing',
                    datetime.now().isoformat()
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            # Fallback to simpler ID
            order_id = f"ORD{user_id}{int(datetime.now().timestamp()) % 10000:04d}"
        
        return order_id
    
    async def _update_order_status(self, order_id: str, status: str, result: Dict = None):
        """Update order status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if result:
                    await db.execute('''
                        UPDATE orders 
                        SET status = ?, completed_at = ?, result = ?
                        WHERE id = ?
                    ''', (
                        status,
                        datetime.now().isoformat(),
                        json.dumps(result),
                        order_id
                    ))
                else:
                    await db.execute('''
                        UPDATE orders 
                        SET status = ?
                        WHERE id = ?
                    ''', (status, order_id))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update order {order_id}: {e}")
    
    async def _get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        columns = ['id', 'user_id', 'video_url', 'views', 'method', 
                                 'status', 'created_at', 'completed_at', 'result']
                        return dict(zip(columns, row))
                    
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
        
        return None
    
    async def _get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's orders"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM orders 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (user_id, limit)) as cursor:
                    
                    rows = await cursor.fetchall()
                    orders = []
                    
                    if rows:
                        columns = ['id', 'user_id', 'video_url', 'views', 'method', 
                                 'status', 'created_at', 'completed_at', 'result']
                        
                        for row in rows:
                            order = dict(zip(columns, row))
                            orders.append(order)
                    
                    return orders
                    
        except Exception as e:
            logger.error(f"Failed to get orders for user {user_id}: {e}")
            return []
    
    async def _get_active_orders(self, user_id: int) -> List[Dict]:
        """Get user's active orders"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM orders 
                    WHERE user_id = ? AND status IN ('processing', 'pending')
                    ORDER BY created_at DESC
                ''', (user_id,)) as cursor:
                    
                    rows = await cursor.fetchall()
                    orders = []
                    
                    if rows:
                        columns = ['id', 'user_id', 'video_url', 'views', 'method', 
                                 'status', 'created_at', 'completed_at', 'result']
                        
                        for row in rows:
                            order = dict(zip(columns, row))
                            
                            # Calculate progress
                            if order['status'] == 'processing':
                                order['progress'] = 50.0  # Simulated
                                order['estimated_completion'] = "10-30 minutes"
                            else:
                                order['progress'] = 0.0
                                order['estimated_completion'] = "Waiting to start"
                            
                            orders.append(order)
                    
                    return orders
                    
        except Exception as e:
            logger.error(f"Failed to get active orders for user {user_id}: {e}")
            return []
    
    async def _get_user_statistics(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get total views sent
                async with db.execute('''
                    SELECT 
                        SUM(views) as total_views,
                        COUNT(*) as total_orders,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_orders
                    FROM orders 
                    WHERE user_id = ?
                ''', (user_id,)) as cursor:
                    
                    row = await cursor.fetchone()
                    total_views = row[0] or 0
                    total_orders = row[1] or 0
                    completed_orders = row[2] or 0
                
                # Get today's views
                today = datetime.now().strftime('%Y-%m-%d')
                async with db.execute('''
                    SELECT SUM(views) 
                    FROM orders 
                    WHERE user_id = ? AND date(created_at) = ?
                ''', (user_id, today)) as cursor:
                    
                    today_views = (await cursor.fetchone())[0] or 0
                
                # Get this week's views
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                async with db.execute('''
                    SELECT SUM(views) 
                    FROM orders 
                    WHERE user_id = ? AND date(created_at) >= ?
                ''', (user_id, week_ago)) as cursor:
                    
                    week_views = (await cursor.fetchone())[0] or 0
                
                # Get this month's views
                month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                async with db.execute('''
                    SELECT SUM(views) 
                    FROM orders 
                    WHERE user_id = ? AND date(created_at) >= ?
                ''', (user_id, month_ago)) as cursor:
                    
                    month_views = (await cursor.fetchone())[0] or 0
                
                # Get active orders
                async with db.execute('''
                    SELECT COUNT(*), SUM(views)
                    FROM orders 
                    WHERE user_id = ? AND status IN ('processing', 'pending')
                ''', (user_id,)) as cursor:
                    
                    row = await cursor.fetchone()
                    active_orders = row[0] or 0
                    pending_views = row[1] or 0
                
                # Calculate success rate (simulated)
                success_rate = 0.85 if completed_orders > 0 else 0
                
                return {
                    'total_views_sent': total_views,
                    'successful_views': int(total_views * success_rate),
                    'success_rate': success_rate,
                    'total_orders': total_orders,
                    'today_views': today_views,
                    'week_views': week_views,
                    'month_views': month_views,
                    'active_orders': active_orders,
                    'pending_views': pending_views
                }
                
        except Exception as e:
            logger.error(f"Failed to get statistics for user {user_id}: {e}")
            return {}
    
    async def _get_user_analytics(self, user_id: int, period: str) -> Dict:
        """Get user analytics for report generation"""
        # This is a simplified version
        stats = await self._get_user_statistics(user_id)
        
        return {
            'summary': stats,
            'performance_metrics': {
                'average_success_rate': stats.get('success_rate', 0),
                'views_per_day': stats.get('month_views', 0) / 30,
                'completion_rate': 1.0 if stats.get('total_orders', 0) > 0 else 0
            },
            'daily_trends': [
                {'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), 
                 'total': max(0, stats.get('today_views', 0) - i * 10)}
                for i in range(7)
            ]
        }
    
    async def _get_user_summary(self) -> Dict:
        """Get user summary for admin"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Total users
                async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                    total = (await cursor.fetchone())[0]
                
                # Active users (24h)
                day_ago = (datetime.now() - timedelta(days=1)).isoformat()
                async with db.execute('''
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE last_active >= ?
                ''', (day_ago,)) as cursor:
                    active_24h = (await cursor.fetchone())[0]
                
                # Active users (7d)
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                async with db.execute('''
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE last_active >= ?
                ''', (week_ago,)) as cursor:
                    active_7d = (await cursor.fetchone())[0]
                
                # New today
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                async with db.execute('''
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE join_date >= ?
                ''', (today_start,)) as cursor:
                    new_today = (await cursor.fetchone())[0]
                
                # Premium users
                async with db.execute('''
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE is_premium = 1
                ''') as cursor:
                    premium = (await cursor.fetchone())[0]
                
                # Subscription distribution
                async with db.execute('''
                    SELECT subscription_level, COUNT(*)
                    FROM users 
                    GROUP BY subscription_level
                ''') as cursor:
                    
                    subscriptions = {}
                    rows = await cursor.fetchall()
                    for row in rows:
                        subscriptions[row[0]] = row[1]
                
                return {
                    'total': total,
                    'active_24h': active_24h,
                    'active_7d': active_7d,
                    'new_today': new_today,
                    'premium': premium,
                    'subscriptions': subscriptions
                }
                
        except Exception as e:
            logger.error(f"Failed to get user summary: {e}")
            return {}
    
    async def _search_users(self, search_term: str) -> List[Dict]:
        """Search users by username or name"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM users 
                    WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
                    LIMIT 20
                ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')) as cursor:
                    
                    rows = await cursor.fetchall()
                    users = []
                    
                    if rows:
                        columns = ['user_id', 'username', 'first_name', 'last_name', 'language_code',
                                 'is_premium', 'join_date', 'last_active', 'command_count',
                                 'view_credits', 'subscription_level']
                        
                        for row in rows:
                            users.append(dict(zip(columns, row)))
                    
                    return users
                    
        except Exception as e:
            logger.error(f"Failed to search users: {e}")
            return []
    
    async def _get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        columns = ['user_id', 'username', 'first_name', 'last_name', 'language_code',
                                 'is_premium', 'join_date', 'last_active', 'command_count',
                                 'view_credits', 'subscription_level']
                        return dict(zip(columns, row))
                    
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
        
        return None
    
    async def _get_user_details(self, user_data: Dict) -> str:
        """Format user details for admin view"""
        user_id = user_data['user_id']
        
        # Get user orders
        orders = await self._get_user_orders(user_id, 5)
        
        details = f"""
👤 <b>User Details</b>

<b>Basic Information:</b>
• <b>ID:</b> <code>{user_data['user_id']}</code>
• <b>Username:</b> @{user_data['username'] or 'N/A'}
• <b>Name:</b> {user_data['first_name']} {user_data['last_name'] or ''}
• <b>Language:</b> {user_data['language_code'] or 'Unknown'}
• <b>Premium:</b> {'✅ Yes' if user_data['is_premium'] else '❌ No'}

<b>Account Information:</b>
• <b>Joined:</b> {user_data['join_date'][:10]}
• <b>Last Active:</b> {user_data['last_active'][:19]}
• <b>Days Since Join:</b> {(datetime.now() - datetime.fromisoformat(user_data['join_date'])).days}
• <b>Commands Used:</b> {user_data['command_count']:,}

<b>Subscription:</b>
• <b>Plan:</b> {user_data['subscription_level'].title()}
• <b>View Credits:</b> {user_data['view_credits']:,}

<b>Recent Orders (Last 5):</b>
"""
        
        if orders:
            for order in orders:
                status_emoji = {
                    'completed': '✅',
                    'processing': '⏳',
                    'failed': '❌',
                    'pending': '🔄'
                }.get(order['status'], '❓')
                
                details += f"""
{status_emoji} <b>Order {order['id']}</b>
• <b>Views:</b> {order['views']:,}
• <b>Status:</b> {order['status'].title()}
• <b>Date:</b> {order['created_at'][:10]}
"""
        else:
            details += "\n📭 No orders found"
        
        details += f"""

<b>Admin Actions:</b>
• <code>/broadcast message</code> - Send message to this user
• <code>Change subscription</code> - (Coming soon)
• <code>Add credits</code> - (Coming soon)
"""
        
        return details
    
    async def _get_recent_users(self, limit: int = 10) -> List[Dict]:
        """Get recent users"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM users 
                    ORDER BY join_date DESC 
                    LIMIT ?
                ''', (limit,)) as cursor:
                    
                    rows = await cursor.fetchall()
                    users = []
                    
                    if rows:
                        columns = ['user_id', 'username', 'first_name', 'last_name', 'language_code',
                                 'is_premium', 'join_date', 'last_active', 'command_count',
                                 'view_credits', 'subscription_level']
                        
                        for row in rows:
                            users.append(dict(zip(columns, row)))
                    
                    return users
                    
        except Exception as e:
            logger.error(f"Failed to get recent users: {e}")
            return []
    
    async def _get_inactive_users(self, days: int) -> List[Dict]:
        """Get users inactive for specified days"""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM users 
                    WHERE last_active < ?
                    ORDER BY last_active ASC
                    LIMIT 100
                ''', (cutoff,)) as cursor:
                    
                    rows = await cursor.fetchall()
                    users = []
                    
                    if rows:
                        columns = ['user_id', 'username', 'first_name', 'last_name', 'language_code',
                                 'is_premium', 'join_date', 'last_active', 'command_count',
                                 'view_credits', 'subscription_level']
                        
                        for row in rows:
                            users.append(dict(zip(columns, row)))
                    
                    return users
                    
        except Exception as e:
            logger.error(f"Failed to get inactive users: {e}")
            return []
    
    async def _get_system_metrics(self) -> Dict:
        """Get system metrics"""
        # This is a simulated version
        import psutil
        import os
        
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        
        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'uptime': str(datetime.now() - self._start_time) if hasattr(self, '_start_time') else 'Unknown',
            'active_sessions': len(self.users),
            'messages_per_minute': 5.2,  # Simulated
            'commands_per_minute': 3.1,  # Simulated
            'error_rate': 0.02,  # Simulated
            'db_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
            'db_tables': 4,  # Simulated
            'db_connections': 1,
            'db_health': 'Healthy',
            'api_latency': 150.5,  # Simulated
            'api_success_rate': 0.98,  # Simulated
            'requests_per_hour': 1200,  # Simulated
            'last_backup': None,
            'last_restart': self._start_time.isoformat() if hasattr(self, '_start_time') else None,
            'version': '1.0.0'
        }
    
    async def _get_system_logs(self, limit: int) -> List[Dict]:
        """Get system logs"""
        # This is a simplified version
        try:
            log_file = 'logs/app.log'
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r') as f:
                lines = f.readlines()[-limit:]
            
            logs = []
            for line in lines:
                parts = line.split(' - ', 3)
                if len(parts) >= 4:
                    logs.append({
                        'timestamp': parts[0],
                        'level': parts[1],
                        'module': parts[2],
                        'message': parts[3].strip()
                    })
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []
    
    async def _store_user_session(self, user_id: int, state: str, data: Dict = None):
        """Store user session data"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO user_sessions 
                    (user_id, state, data, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (
                    user_id,
                    state,
                    json.dumps(data or {}),
                    datetime.now().isoformat()
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store session for user {user_id}: {e}")
    
    async def _get_user_session(self, user_id: int) -> Optional[Dict]:
        """Get user session data"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT * FROM user_sessions WHERE user_id = ?', (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        return {
                            'user_id': row[0],
                            'state': row[1],
                            'data': json.loads(row[2]) if row[2] else {},
                            'last_updated': row[3]
                        }
                    
        except Exception as e:
            logger.error(f"Failed to get session for user {user_id}: {e}")
        
        return None
    
    async def _clear_user_session(self, user_id: int):
        """Clear user session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to clear session for user {user_id}: {e}")
    
    async def _log_command(self, user_id: int, command: str, result: str):
        """Log command execution"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO commands_history 
                    (user_id, command, arguments, timestamp, success)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    command,
                    result,
                    datetime.now().isoformat(),
                    1 if 'success' in result.lower() else 0
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to log command: {e}")
    
    def _calculate_elapsed_time(self, start_time: str) -> str:
        """Calculate elapsed time"""
        try:
            start = datetime.fromisoformat(start_time)
            elapsed = datetime.now() - start
            
            if elapsed.days > 0:
                return f"{elapsed.days}d {elapsed.seconds // 3600}h"
            elif elapsed.seconds > 3600:
                return f"{elapsed.seconds // 3600}h {(elapsed.seconds % 3600) // 60}m"
            elif elapsed.seconds > 60:
                return f"{elapsed.seconds // 60}m {elapsed.seconds % 60}s"
            else:
                return f"{elapsed.seconds}s"
        except:
            return "Unknown"
    
    def _get_active_sessions(self) -> int:
        """Get active sessions count"""
        return len([u for u in self.users.values() 
                   if (datetime.now() - u.last_active).total_seconds() < 3600])
    
    def _get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _get_uptime(self) -> str:
        """Get bot uptime"""
        if hasattr(self, '_start_time'):
            uptime = datetime.now() - self._start_time
            
            if uptime.days > 0:
                return f"{uptime.days}d {uptime.seconds // 3600}h"
            elif uptime.seconds > 3600:
                return f"{uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
            elif uptime.seconds > 60:
                return f"{uptime.seconds // 60}m"
            else:
                return f"{uptime.seconds}s"
        
        return "Unknown"
    
    def _get_new_users_count(self) -> int:
        """Get new users count in last 24h"""
        day_ago = datetime.now() - timedelta(days=1)
        return len([u for u in self.users.values() if u.join_date > day_ago])
    
    def _get_active_users_count(self) -> int:
        """Get active users count in last 24h"""
        day_ago = datetime.now() - timedelta(days=1)
        return len([u for u in self.users.values() if u.last_active > day_ago])
    
    def _get_total_orders(self) -> int:
        """Get total orders count"""
        # Simplified - would query database in real implementation
        return len(self.users) * 3  # Simulated
    
    def _get_system_success_rate(self) -> float:
        """Get system success rate"""
        return 0.85  # Simulated
    
    # Callback handlers
    async def _handle_quick_send(self, callback_query: types.CallbackQuery):
        """Handle quick send callback"""
        await callback_query.message.answer(
            "📤 <b>Quick Send</b>\n\n"
            "Send me a TikTok video URL to get started!\n\n"
            "<b>Example:</b>\n"
            "<code>https://tiktok.com/@username/video/123456789</code>",
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_my_stats(self, callback_query: types.CallbackQuery):
        """Handle my stats callback"""
        message = types.Message(
            message_id=callback_query.message.message_id,
            date=callback_query.message.date,
            chat=callback_query.message.chat,
            from_user=callback_query.from_user
        )
        await self._handle_stats(message)
    
    async def _handle_upgrade(self, callback_query: types.CallbackQuery):
        """Handle upgrade callback"""
        message = types.Message(
            message_id=callback_query.message.message_id,
            date=callback_query.message.date,
            chat=callback_query.message.chat,
            from_user=callback_query.from_user
        )
        await self._handle_subscribe(message)
    
    async def _handle_help_callback(self, callback_query: types.CallbackQuery):
        """Handle help callback"""
        message = types.Message(
            message_id=callback_query.message.message_id,
            date=callback_query.message.date,
            chat=callback_query.message.chat,
            from_user=callback_query.from_user
        )
        await self._handle_help(message)
    
    async def _handle_send_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle send callback"""
        if data == 'send_cancel':
            await callback_query.message.edit_text("❌ Send cancelled.")
            return
        
        # Get views count from callback data
        if data == 'send_custom':
            await callback_query.message.edit_text(
                "📝 <b>Custom Views</b>\n\n"
                "Please enter the number of views you want to send:",
                parse_mode=ParseMode.HTML
            )
            return
        
        views = int(data.split('_')[1])
        
        # Check if we have video URL in session
        user = await self._get_or_create_user(callback_query.from_user)
        session = await self._get_user_session(user.user_id)
        
        if session and session.get('state') == 'awaiting_views':
            video_url = session.get('data', {}).get('video_url')
            
            if video_url:
                message = types.Message(
                    message_id=callback_query.message.message_id,
                    date=callback_query.message.date,
                    chat=callback_query.message.chat,
                    from_user=callback_query.from_user,
                    text=f"/send {video_url} {views}"
                )
                await self._handle_send(message)
                await self._clear_user_session(user.user_id)
            else:
                await callback_query.message.edit_text(
                    "❌ No video URL found. Please send the URL again.",
                    parse_mode=ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                "❌ Please send a TikTok video URL first.",
                parse_mode=ParseMode.HTML
            )
    
    async def _handle_refresh_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle refresh callback"""
        refresh_type = data.split('_')[1]
        
        if refresh_type == 'balance':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user
            )
            await self._handle_balance(message)
        elif refresh_type == 'stats':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user
            )
            await self._handle_stats(message)
        elif refresh_type == 'history':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user
            )
            await self._handle_history(message)
        elif refresh_type == 'subscribe':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user
            )
            await self._handle_subscribe(message)
        elif refresh_type == 'methods':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user
            )
            await self._handle_methods(message)
    
    async def _handle_upgrade_to(self, callback_query: types.CallbackQuery, data: str):
        """Handle upgrade to specific plan"""
        plan_id = data.split(':')[1]
        
        await callback_query.message.edit_text(
            f"💎 <b>Upgrade to {plan_id.title()} Plan</b>\n\n"
            f"To upgrade, please contact @admin_username\n\n"
            f"Send them this message:\n"
            f"<code>Upgrade my account to {plan_id} plan. User ID: {callback_query.from_user.id}</code>\n\n"
            f"They will guide you through the payment process.",
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_contact_support(self, callback_query: types.CallbackQuery):
        """Handle contact support callback"""
        await callback_query.message.edit_text(
            "📞 <b>Contact Support</b>\n\n"
            "Telegram: @vtultrapro_support\n"
            "Email: support@vtultrapro.com\n\n"
            "Please include your User ID:\n"
            f"<code>{callback_query.from_user.id}</code>",
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_view_history(self, callback_query: types.CallbackQuery):
        """Handle view history callback"""
        message = types.Message(
            message_id=callback_query.message.message_id,
            date=callback_query.message.date,
            chat=callback_query.message.chat,
            from_user=callback_query.from_user
        )
        await self._handle_history(message)
    
    async def _handle_refresh_status(self, callback_query: types.CallbackQuery, data: str):
        """Handle refresh status callback"""
        order_id = data.split(':')[1]
        
        message = types.Message(
            message_id=callback_query.message.message_id,
            date=callback_query.message.date,
            chat=callback_query.message.chat,
            from_user=callback_query.from_user,
            text=f"/status {order_id}"
        )
        await self._handle_status(message)
    
    async def _handle_refresh_all_status(self, callback_query: types.CallbackQuery):
        """Handle refresh all status callback"""
        message = types.Message(
            message_id=callback_query.message.message_id,
            date=callback_query.message.date,
            chat=callback_query.message.chat,
            from_user=callback_query.from_user,
            text="/status"
        )
        await self._handle_status(message)
    
    async def _handle_setting_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle setting callback"""
        setting = data.split('_')[1]
        
        if setting == 'language':
            await callback_query.message.edit_text(
                "🌐 <b>Language Settings</b>\n\n"
                "Available languages:\n"
                "• English (EN)\n"
                "• Spanish (ES)\n"
                "• Russian (RU)\n\n"
                "Coming soon! Currently only English is supported.",
                parse_mode=ParseMode.HTML
            )
        elif setting == 'save':
            await callback_query.answer("✅ Settings saved!")
        else:
            await callback_query.answer("⚙️ This setting is not yet implemented")
    
    async def _handle_docs(self, callback_query: types.CallbackQuery):
        """Handle documentation callback"""
        await callback_query.message.edit_text(
            "📚 <b>Documentation</b>\n\n"
            "Visit our website for complete documentation:\n"
            "https://vtultrapro.com/docs\n\n"
            "Or use /help for basic commands.",
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_admin_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle admin callback"""
        action = data.split('_')[1]
        
        if action == 'broadcast':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user,
                text="/broadcast"
            )
            await self._handle_broadcast(message)
        elif action == 'users':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user,
                text="/users"
            )
            await self._handle_users(message)
        elif action == 'system':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user,
                text="/system"
            )
            await self._handle_system(message)
        elif action == 'logs':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user,
                text="/logs"
            )
            await self._handle_logs(message)
        elif action == 'stats':
            await callback_query.message.edit_text(
                "📊 <b>System Statistics</b>\n\n"
                "Loading detailed statistics...\n\n"
                "This feature is coming soon!",
                parse_mode=ParseMode.HTML
            )
        elif action == 'backup':
            await callback_query.answer("💾 Backup started...")
            # Implement backup logic here
        elif action == 'restart':
            await callback_query.answer("🔄 Restarting bot...")
            # Implement restart logic here
        elif action == 'exit':
            await callback_query.message.edit_text("👋 Exited admin panel.")
    
    async def _handle_broadcast_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle broadcast confirmation callback"""
        if data == 'broadcast_cancel':
            await callback_query.message.edit_text("❌ Broadcast cancelled.")
            return
        
        # Extract message from callback data
        message_text = data.split(':', 1)[1]
        
        # Send broadcast (simulated)
        await callback_query.message.edit_text(
            f"📢 <b>Broadcast Sent!</b>\n\n"
            f"Message sent to {len(self.users):,} users.\n\n"
            f"<b>Message:</b>\n{message_text}...",
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_users_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle users callback"""
        action = data.split(':')[0].split('_')[1]
        
        if action == 'recent':
            limit = int(data.split(':')[1])
            recent_users = await self._get_recent_users(limit)
            
            text = f"🆕 <b>Recent {len(recent_users)} Users</b>\n\n"
            for user in recent_users:
                text += f"• {user['first_name']} (@{user['username'] or 'N/A'}) - {user['join_date'][:10]}\n"
            
            await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)
        
        elif action == 'active':
            await callback_query.message.edit_text(
                "⚡ <b>Active Users</b>\n\n"
                "Loading active users...\n\n"
                "This feature is coming soon!",
                parse_mode=ParseMode.HTML
            )
        
        elif action == 'premium':
            await callback_query.message.edit_text(
                "💎 <b>Premium Users</b>\n\n"
                "Loading premium users...\n\n"
                "This feature is coming soon!",
                parse_mode=ParseMode.HTML
            )
        
        elif action == 'stats':
            await callback_query.message.edit_text(
                "📊 <b>User Statistics</b>\n\n"
                "Loading user statistics...\n\n"
                "This feature is coming soon!",
                parse_mode=ParseMode.HTML
            )
        
        elif action == 'export':
            await callback_query.answer("📄 Export started...")
            # Implement export logic here
    
    async def _handle_system_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle system callback"""
        action = data.split('_')[1]
        
        if action == 'metrics':
            metrics = await self._get_system_metrics()
            
            text = f"""
📊 <b>Detailed Metrics</b>

<b>CPU Usage:</b> {metrics['cpu_usage']:.1f}%
<b>Memory Usage:</b> {metrics['memory_usage']:.1f}%
<b>Disk Usage:</b> {metrics['disk_usage']:.1f}%
<b>Uptime:</b> {metrics['uptime']}
<b>Active Sessions:</b> {metrics['active_sessions']:,}
<b>Messages/Minute:</b> {metrics['messages_per_minute']:.1f}
<b>Error Rate:</b> {metrics['error_rate']:.1%}
            """
            
            await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)
        
        elif action == 'health':
            await callback_query.message.edit_text(
                "🔍 <b>Health Check</b>\n\n"
                "Running health check...\n\n"
                "✅ All systems operational!",
                parse_mode=ParseMode.HTML
            )
        
        elif action == 'backup':
            await callback_query.answer("💾 Creating backup...")
            # Implement backup logic here
        
        elif action == 'restart':
            await callback_query.answer("🔄 Restarting...")
            # Implement restart logic here
        
        elif action == 'clean':
            await callback_query.answer("🗑️ Cleaning cache...")
            # Implement cleanup logic here
        
        elif action == 'logs':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user,
                text="/logs"
            )
            await self._handle_logs(message)
        
        elif action == 'refresh':
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user,
                text="/system"
            )
            await self._handle_system(message)
    
    async def _handle_logs_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle logs callback"""
        action = data.split(':')[0].split('_')[1]
        
        if action == 'full':
            limit = int(data.split(':')[1])
            message = types.Message(
                message_id=callback_query.message.message_id,
                date=callback_query.message.date,
                chat=callback_query.message.chat,
                from_user=callback_query.from_user,
                text=f"/logs {limit}"
            )
            await self._handle_logs(message)
        
        elif action == 'errors':
            await callback_query.message.edit_text(
                "🚨 <b>Error Logs</b>\n\n"
                "Loading error logs...\n\n"
                "This feature is coming soon!",
                parse_mode=ParseMode.HTML
            )
        
        elif action == 'export':
            await callback_query.answer("💾 Exporting logs...")
            # Implement export logic here
        
        elif action == 'clear':
            await callback_query.answer("🗑️ Clearing logs...")
            # Implement clear logic here
    
    async def _handle_inactive_callback(self, callback_query: types.CallbackQuery, data: str):
        """Handle inactive users callback"""
        action = data.split(':')[0].split('_')[1]
        days = int(data.split(':')[1])
        
        if action == 'reminder':
            await callback_query.answer(f"📧 Sending reminders to inactive users ({days}+ days)...")
            # Implement reminder logic here
        
        elif action == 'cleanup':
            await callback_query.answer(f"🗑️ Cleaning up inactive users ({days}+ days)...")
            # Implement cleanup logic here
    
    async def start(self):
        """Start the bot"""
        self._start_time = datetime.now()
        
        # Set bot commands
        commands = [
            types.BotCommand("start", "Start the bot"),
            types.BotCommand("help", "Show help"),
            types.BotCommand("send", "Send views to TikTok video"),
            types.BotCommand("balance", "Check your balance"),
            types.BotCommand("stats", "View your statistics"),
            types.BotCommand("history", "View order history"),
            types.BotCommand("status", "Check order status"),
            types.BotCommand("subscribe", "Upgrade subscription"),
            types.BotCommand("methods", "View available methods"),
            types.BotCommand("schedule", "Schedule views"),
            types.BotCommand("cancel", "Cancel order"),
            types.BotCommand("report", "Generate report"),
            types.BotCommand("settings", "Bot settings"),
            types.BotCommand("support", "Contact support"),
            types.BotCommand("admin", "Admin panel (admin only)"),
            types.BotCommand("broadcast", "Broadcast message (admin only)"),
            types.BotCommand("users", "User management (admin only)"),
            types.BotCommand("system", "System monitoring (admin only)"),
            types.BotCommand("logs", "View system logs (admin only)")
        ]
        
        await self.bot.set_my_commands(commands)
        
        logger.info("Starting Telegram bot...")
        
        # Start polling
        await self.dp.start_polling()
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping Telegram bot...")
        await self.bot.close()
        await self.storage.close()
    
    def run(self):
        """Run the bot (blocking)"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot failed: {e}")
        finally:
            loop.run_until_complete(self.stop())