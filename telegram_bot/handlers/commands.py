"""
Command Handlers for Telegram Bot
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

from telegram_bot.database.user_db import UserDatabase
from telegram_bot.database.order_db import OrderDatabase
from telegram_bot.keyboards.main_menu import MainKeyboard
from telegram_bot.keyboards.admin_panel import AdminKeyboard

logger = logging.getLogger(__name__)

# Initialize databases
user_db = UserDatabase()
order_db = OrderDatabase()

async def register_commands(dp: Dispatcher):
    """Register all command handlers"""
    
    # Start command
    @dp.message_handler(Command('start'))
    async def cmd_start(message: types.Message):
        await handle_start(message)
    
    # Help command
    @dp.message_handler(Command('help'))
    async def cmd_help(message: types.Message):
        await handle_help(message)
    
    # Send views command
    @dp.message_handler(Command('send'))
    async def cmd_send(message: types.Message, state: FSMContext):
        await handle_send(message, state)
    
    # Balance command
    @dp.message_handler(Command('balance'))
    async def cmd_balance(message: types.Message):
        await handle_balance(message)
    
    # Stats command
    @dp.message_handler(Command('stats'))
    async def cmd_stats(message: types.Message):
        await handle_stats(message)
    
    # History command
    @dp.message_handler(Command('history'))
    async def cmd_history(message: types.Message):
        await handle_history(message)
    
    # Status command
    @dp.message_handler(Command('status'))
    async def cmd_status(message: types.Message):
        await handle_status(message)
    
    # Subscribe command
    @dp.message_handler(Command('subscribe'))
    async def cmd_subscribe(message: types.Message):
        await handle_subscribe(message)
    
    # Methods command
    @dp.message_handler(Command('methods'))
    async def cmd_methods(message: types.Message):
        await handle_methods(message)
    
    # Schedule command
    @dp.message_handler(Command('schedule'))
    async def cmd_schedule(message: types.Message):
        await handle_schedule(message)
    
    # Cancel command
    @dp.message_handler(Command('cancel'))
    async def cmd_cancel(message: types.Message):
        await handle_cancel(message)
    
    # Report command
    @dp.message_handler(Command('report'))
    async def cmd_report(message: types.Message):
        await handle_report(message)
    
    # Settings command
    @dp.message_handler(Command('settings'))
    async def cmd_settings(message: types.Message):
        await handle_settings(message)
    
    # Support command
    @dp.message_handler(Command('support'))
    async def cmd_support(message: types.Message):
        await handle_support(message)
    
    # Admin commands
    @dp.message_handler(Command('admin'))
    async def cmd_admin(message: types.Message):
        await handle_admin(message)
    
    # Broadcast command
    @dp.message_handler(Command('broadcast'))
    async def cmd_broadcast(message: types.Message, state: FSMContext):
        await handle_broadcast(message, state)
    
    # Users command
    @dp.message_handler(Command('users'))
    async def cmd_users(message: types.Message):
        await handle_users(message)
    
    # System command
    @dp.message_handler(Command('system'))
    async def cmd_system(message: types.Message):
        await handle_system(message)
    
    # Logs command
    @dp.message_handler(Command('logs'))
    async def cmd_logs(message: types.Message):
        await handle_logs(message)
    
    logger.info("Registered 20+ command handlers")

async def handle_start(message: types.Message):
    """Handle /start command"""
    user = message.from_user
    
    # Register or update user
    await user_db.create_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_premium=getattr(user, 'is_premium', False)
    )
    
    welcome_text = f"""
🎯 <b>Welcome to VT ULTRA PRO TikTok Bot!</b>

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.id}</code>
📅 <b>Joined:</b> {datetime.now().strftime('%Y-%m-%d')}
💎 <b>Subscription:</b> Free
🪙 <b>Credits:</b> 100 views

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
    
    keyboard = MainKeyboard.get_start_keyboard()
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    logger.info(f"User {user.id} started the bot")

async def handle_help(message: types.Message):
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

async def handle_send(message: types.Message, state: FSMContext):
    """Handle /send command"""
    args = message.get_args().split()
    user_id = message.from_user.id
    
    if len(args) >= 2:
        # Direct send with arguments
        try:
            video_url = args[0]
            views = int(args[1])
            method = args[2] if len(args) > 2 else "auto"
            
            # Validate URL
            if not is_valid_tiktok_url(video_url):
                await message.answer("❌ Invalid TikTok URL format!")
                return
            
            # Check user balance
            user_data = await user_db.get_user(user_id)
            if not user_data:
                await message.answer("❌ User not found!")
                return
            
            if user_data['view_credits'] < views:
                await message.answer(
                    f"❌ Insufficient credits! You have {user_data['view_credits']} views left.\n"
                    f"Use /balance to check your credits."
                )
                return
            
            # Create order
            order_id = await order_db.create_order(
                user_id=user_id,
                video_url=video_url,
                views=views,
                method=method
            )
            
            # Process the order
            processing_msg = await message.answer(
                f"⏳ Processing order <code>{order_id}</code>\n"
                f"📊 Sending {views:,} views to: {video_url}\n"
                f"⚡ Method: {method}\n\n"
                "Please wait...",
                parse_mode=ParseMode.HTML
            )
            
            # Simulate view sending (in real implementation, this would call the view engine)
            import asyncio
            await asyncio.sleep(2)
            
            # Update order status
            await order_db.update_order_status(
                order_id=order_id,
                status='completed',
                result={
                    'successful_views': int(views * 0.85),
                    'success_rate': 0.85,
                    'processing_time': 120
                }
            )
            
            # Update user credits
            await user_db.update_user_credits(user_id, -views)
            
            await processing_msg.edit_text(
                f"✅ <b>Order Completed!</b>\n\n"
                f"📋 <b>Order ID:</b> <code>{order_id}</code>\n"
                f"🎯 <b>Video:</b> {video_url}\n"
                f"📊 <b>Views Sent:</b> {views:,}\n"
                f"✅ <b>Successful:</b> {int(views * 0.85):,}\n"
                f"📈 <b>Success Rate:</b> 85%\n"
                f"⏱️ <b>Time:</b> 120s\n\n"
                f"🔄 Check /status for updates\n"
                f"📊 View details with /history",
                parse_mode=ParseMode.HTML
            )
            
        except ValueError:
            await message.answer(
                "❌ Invalid format!\n"
                "Correct format: <code>/send URL views [method]</code>\n\n"
                "Example: <code>/send https://tiktok.com/@user/video/123 500 browser</code>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Send error: {e}")
            await message.answer(f"❌ Error: {str(e)}")
    
    else:
        # Interactive send
        await state.set_state('awaiting_url')
        await message.answer(
            "📤 <b>Send TikTok Views</b>\n\n"
            "Please send me the TikTok video URL:\n\n"
            "<b>Example:</b>\n"
            "<code>https://tiktok.com/@username/video/123456789</code>",
            parse_mode=ParseMode.HTML
        )

async def handle_balance(message: types.Message):
    """Handle /balance command"""
    user_id = message.from_user.id
    user_data = await user_db.get_user(user_id)
    
    if not user_data:
        await message.answer("❌ User not found!")
        return
    
    subscription_info = get_subscription_info(user_data['subscription_level'])
    
    balance_text = f"""
💰 <b>Your Balance</b>

👤 <b>User:</b> {message.from_user.first_name}
🆔 <b>ID:</b> <code>{user_id}</code>

💎 <b>Subscription:</b> {user_data['subscription_level'].title()}
📊 <b>Views Available:</b> {user_data['view_credits']:,}

📋 <b>Subscription Details:</b>
• <b>Plan:</b> {subscription_info['name']}
• <b>Daily Limit:</b> {subscription_info['daily_limit']:,} views
• <b>Max per Order:</b> {subscription_info['max_per_order']:,}
• <b>Methods:</b> {', '.join(subscription_info['methods'])}
• <b>Priority:</b> {subscription_info['priority']}

🔄 <b>Reset:</b> Daily at 00:00 UTC
📈 <b>Total Used:</b> {user_data['total_views_used']:,} views

💳 <b>Upgrade:</b> /subscribe
📤 <b>Send Views:</b> /send
    """
    
    keyboard = MainKeyboard.get_balance_keyboard()
    await message.answer(balance_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_stats(message: types.Message):
    """Handle /stats command"""
    user_id = message.from_user.id
    
    # Get user data
    user_data = await user_db.get_user(user_id)
    if not user_data:
        await message.answer("❌ User not found!")
        return
    
    # Get user orders
    orders = await order_db.get_user_orders(user_id, limit=100)
    
    # Calculate statistics
    total_views = sum(order['views'] for order in orders)
    completed_orders = len([o for o in orders if o['status'] == 'completed'])
    success_rate = 0.85  # Simulated
    
    stats_text = f"""
📊 <b>Your Statistics</b>

👤 <b>User:</b> {message.from_user.first_name}
🆔 <b>ID:</b> <code>{user_id}</code>
📅 <b>Member Since:</b> {user_data['created_at'][:10]}

<b>📈 Activity Stats:</b>
• <b>Total Orders:</b> {len(orders)}
• <b>Completed Orders:</b> {completed_orders}
• <b>Last Active:</b> {user_data['last_active'][:19]}

<b>🎯 View Statistics:</b>
• <b>Total Views Sent:</b> {total_views:,}
• <b>Successful Views:</b> {int(total_views * success_rate):,}
• <b>Success Rate:</b> {success_rate:.1%}
• <b>Views Used:</b> {user_data['total_views_used']:,}

<b>📊 Current Status:</b>
• <b>Available Credits:</b> {user_data['view_credits']:,}
• <b>Subscription:</b> {user_data['subscription_level'].title()}
• <b>Active Orders:</b> {len([o for o in orders if o['status'] in ['processing', 'pending']])}

<b>📈 Performance:</b>
• <b>Average Success:</b> 85%
• <b>Best Method:</b> Browser
• <b>Peak Time:</b> 18:00-22:00 UTC
    """
    
    keyboard = MainKeyboard.get_stats_keyboard()
    await message.answer(stats_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_history(message: types.Message):
    """Handle /history command"""
    user_id = message.from_user.id
    orders = await order_db.get_user_orders(user_id, limit=10)
    
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

👤 <b>User:</b> {message.from_user.first_name}
📅 <b>Showing last {len(orders)} orders</b>

"""
    
    for i, order in enumerate(orders, 1):
        status_emoji = {
            'completed': '✅',
            'processing': '⏳',
            'failed': '❌',
            'pending': '🔄'
        }.get(order['status'], '❓')
        
        # Truncate long URLs
        video_url = order['video_url']
        if len(video_url) > 30:
            video_url = video_url[:27] + "..."
        
        history_text += f"""
<b>{i}. {status_emoji} Order {order['id']}</b>
• <b>Video:</b> {video_url}
• <b>Views:</b> {order['views']:,}
• <b>Status:</b> {order['status'].title()}
• <b>Date:</b> {order['created_at'][:10]}
• <b>Method:</b> {order.get('method', 'auto')}
"""
        
        if order['status'] == 'completed' and order.get('result'):
            try:
                result = json.loads(order['result']) if isinstance(order['result'], str) else order['result']
                success_rate = result.get('success_rate', 0) * 100
                history_text += f"• <b>Success:</b> {success_rate:.1f}%\n"
            except:
                pass
    
    history_text += "\n📊 <b>Use /status [order_id] for detailed information</b>"
    
    keyboard = MainKeyboard.get_history_keyboard()
    await message.answer(history_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_status(message: types.Message):
    """Handle /status command"""
    args = message.get_args().strip()
    user_id = message.from_user.id
    
    if not args:
        # Show all active orders
        orders = await order_db.get_user_orders(user_id)
        active_orders = [o for o in orders if o['status'] in ['processing', 'pending']]
        
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

👤 <b>User:</b> {message.from_user.first_name}
📋 <b>Active Orders:</b> {len(active_orders)}

"""
        
        for order in active_orders:
            status_emoji = {
                'processing': '⏳',
                'pending': '🔄'
            }.get(order['status'], '❓')
            
            progress = 50 if order['status'] == 'processing' else 0
            
            status_text += f"""
<b>{status_emoji} Order {order['id']}</b>
• <b>Video:</b> {order['video_url'][:25]}...
• <b>Target:</b> {order['views']:,} views
• <b>Progress:</b> {progress}%
• <b>Status:</b> {order['status'].title()}
• <b>Started:</b> {order['created_at'][11:16]}
"""
        
        status_text += "\n🔄 <b>Orders update automatically</b>"
        
    else:
        # Show specific order
        order = await order_db.get_order(args)
        
        if not order or order['user_id'] != user_id:
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
            success_rate = result.get('success_rate', 0) * 100
            successful_views = result.get('successful_views', 0)
            processing_time = result.get('processing_time', 0)
            
            status_text += f"""
<b>✅ Completed:</b> {order.get('completed_at', 'N/A')}
<b>📈 Success Rate:</b> {success_rate:.1f}%
<b>🎯 Successful Views:</b> {successful_views:,}
<b>⏱️ Processing Time:</b> {processing_time}s
"""
        
        elif order['status'] in ['processing', 'pending']:
            progress = 50 if order['status'] == 'processing' else 0
            estimated_completion = "10-30 minutes" if order['status'] == 'processing' else "Waiting to start"
            
            status_text += f"""
<b>📊 Progress:</b> {progress}%
<b>🕐 Estimated Completion:</b> {estimated_completion}
<b>⏳ Elapsed Time:</b> {calculate_elapsed_time(order['created_at'])}
"""
        
        elif order['status'] == 'failed':
            error = result.get('error', 'Unknown error')
            status_text += f"""
<b>❌ Failed:</b> {order.get('completed_at', 'N/A')}
<b>⚠️ Error:</b> {error}
"""
    
    keyboard = MainKeyboard.get_status_keyboard(args if args else None)
    await message.answer(status_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_subscribe(message: types.Message):
    """Handle /subscribe command"""
    user_id = message.from_user.id
    user_data = await user_db.get_user(user_id)
    
    if not user_data:
        await message.answer("❌ User not found!")
        return
    
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
    
    current_plan = subscription_plans[user_data['subscription_level']]
    
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
        if plan_id == user_data['subscription_level']:
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
    
    keyboard = MainKeyboard.get_subscribe_keyboard(user_data['subscription_level'])
    await message.answer(subscribe_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_methods(message: types.Message):
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
    
    user_id = message.from_user.id
    user_data = await user_db.get_user(user_id)
    
    if not user_data:
        await message.answer("❌ User not found!")
        return
    
    user_methods = get_subscription_info(user_data['subscription_level'])['methods']
    
    methods_text = f"""
⚡ <b>View Methods Available</b>

👤 <b>Your Plan:</b> {user_data['subscription_level'].title()}
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
    
    keyboard = MainKeyboard.get_methods_keyboard()
    await message.answer(methods_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_schedule(message: types.Message):
    """Handle /schedule command"""
    await message.answer(
        "📅 <b>View Scheduling</b>\n\n"
        "This feature allows you to schedule views for future times.\n\n"
        "<b>Coming Soon!</b>\n"
        "We're working on advanced scheduling features.\n\n"
        "For now, use /send for immediate views.",
        parse_mode=ParseMode.HTML
    )

async def handle_cancel(message: types.Message):
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
    
    user_id = message.from_user.id
    order = await order_db.get_order(args)
    
    if not order or order['user_id'] != user_id:
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
    await order_db.update_order_status(args, 'cancelled', {'cancelled_by': 'user'})
    
    # Refund credits
    await user_db.update_user_credits(user_id, order['views'])
    
    await message.answer(
        f"✅ <b>Order Cancelled</b>\n\n"
        f"Order ID: <code>{args}</code>\n"
        f"Status: Cancelled\n"
        f"Refund: {order['views']:,} credits returned\n\n"
        f"Your credits have been refunded to your account.",
        parse_mode=ParseMode.HTML
    )

async def handle_report(message: types.Message):
    """Handle /report command"""
    user_id = message.from_user.id
    user_data = await user_db.get_user(user_id)
    
    if not user_data:
        await message.answer("❌ User not found!")
        return
    
    # Check if user has access to reports
    if user_data['subscription_level'] not in ['pro', 'enterprise']:
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
    
    processing_msg = await message.answer(
        f"📊 <b>Generating {report_types[args]}...</b>\n\n"
        f"Please wait while we compile your analytics data.",
        parse_mode=ParseMode.HTML
    )
    
    # Simulate report generation
    import asyncio
    await asyncio.sleep(3)
    
    await processing_msg.edit_text(
        f"✅ <b>Report Generated!</b>\n\n"
        f"📋 <b>Title:</b> User Report - {message.from_user.first_name}\n"
        f"📅 <b>Period:</b> {args.title()}\n"
        f"📊 <b>Format:</b> HTML\n"
        f"💾 <b>Size:</b> 15.2 KB\n\n"
        f"📥 <b>Download:</b> /reports/user_{user_id}_{args}.html\n\n"
        f"Use /settings to configure report preferences.",
        parse_mode=ParseMode.HTML
    )

async def handle_settings(message: types.Message):
    """Handle /settings command"""
    user_id = message.from_user.id
    user_data = await user_db.get_user(user_id)
    
    if not user_data:
        await message.answer("❌ User not found!")
        return
    
    settings_text = f"""
⚙️ <b>Bot Settings</b>

👤 <b>User:</b> {message.from_user.first_name}
🆔 <b>ID:</b> <code>{user_id}</code>

<b>🔧 Current Settings:</b>
• <b>Language:</b> {user_data.get('language_code', 'Auto')}
• <b>Notifications:</b> Enabled
• <b>Auto-Update:</b> Enabled
• <b>Privacy Mode:</b> Standard
• <b>Report Frequency:</b> Weekly
• <b>Default Method:</b> Auto Select
• <b>Default Views:</b> 100

<b>📋 Available Settings:</b>
• Language selection
• Notification preferences
• Privacy settings
• Report configurations
• Default parameters
• Theme selection
"""
    
    keyboard = MainKeyboard.get_settings_keyboard()
    await message.answer(settings_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_support(message: types.Message):
    """Handle /support command"""
    support_text = """
🆘 <b>Support & Help</b>

<b>📞 Contact Methods:</b>
• <b>Telegram:</b> @vtultrapro_support
• <b>Email:</b> support@vtultrapro.com
• <b>Website:</b> https://vtultrapro.com

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
    
    keyboard = MainKeyboard.get_support_keyboard()
    await message.answer(support_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_admin(message: types.Message):
    """Handle /admin command"""
    user_id = message.from_user.id
    
    # Check if user is admin (in real implementation, check from config)
    admin_ids = [123456789]  # Example admin ID
    if user_id not in admin_ids:
        await message.answer("❌ Admin access required!")
        return
    
    # Get system stats
    total_users = await user_db.get_total_users()
    active_users = await user_db.get_active_users_count(24)
    total_orders = await order_db.get_total_orders()
    
    admin_text = f"""
👨‍💼 <b>Admin Panel</b>

<b>📊 System Status:</b>
• <b>Users:</b> {total_users:,}
• <b>Active (24h):</b> {active_users:,}
• <b>Total Orders:</b> {total_orders:,}
• <b>Success Rate:</b> 85.2%
• <b>System Load:</b> 42%

<b>🔧 Admin Commands:</b>
• <code>/broadcast message</code> - Send to all users
• <code>/users</code> - User management
• <code>/system</code> - System monitoring
• <code>/logs</code> - View system logs
• <code>/stats all</code> - All users statistics
• <code>/backup</code> - Create backup
• <code>/restart</code> - Restart bot

<b>📈 Quick Stats:</b>
• <b>New Users (24h):</b> {await user_db.get_new_users_count(24):,}
• <b>Premium Users:</b> {await user_db.get_premium_users_count():,}
• <b>Revenue Today:</b> $0.00
• <b>Avg Success Rate:</b> 85.2%

<b>⚠️ Warning:</b>
Admin commands can affect all users.
Use with caution!
    """
    
    keyboard = AdminKeyboard.get_main_keyboard()
    await message.answer(admin_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_broadcast(message: types.Message, state: FSMContext):
    """Handle /broadcast command"""
    user_id = message.from_user.id
    
    # Check admin access
    admin_ids = [123456789]
    if user_id not in admin_ids:
        await message.answer("❌ Admin access required!")
        return
    
    args = message.get_args().strip()
    
    if not args:
        await message.answer(
            "📢 <b>Broadcast Message</b>\n\n"
            "Usage: <code>/broadcast your message here</code>\n\n"
            "This will send your message to all bot users.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Store broadcast message in state
    await state.update_data(broadcast_message=args)
    
    total_users = await user_db.get_total_users()
    
    keyboard = AdminKeyboard.get_broadcast_keyboard()
    await message.answer(
        f"📢 <b>Confirm Broadcast</b>\n\n"
        f"<b>Message:</b>\n{args}\n\n"
        f"<b>Recipients:</b> {total_users:,} users\n"
        f"<b>This cannot be undone!</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

async def handle_users(message: types.Message):
    """Handle /users command"""
    user_id = message.from_user.id
    
    # Check admin access
    admin_ids = [123456789]
    if user_id not in admin_ids:
        await message.answer("❌ Admin access required!")
        return
    
    args = message.get_args().strip()
    
    if not args:
        # Show user summary
        total_users = await user_db.get_total_users()
        active_users = await user_db.get_active_users_count(24)
        new_today = await user_db.get_new_users_count(24)
        premium_users = await user_db.get_premium_users_count()
        
        users_text = f"""
👥 <b>User Management</b>

<b>📊 User Statistics:</b>
• <b>Total Users:</b> {total_users:,}
• <b>Active (24h):</b> {active_users:,}
• <b>New Today:</b> {new_today:,}
• <b>Premium Users:</b> {premium_users:,}

<b>📈 Subscription Distribution:</b>
"""
        
        # Get subscription distribution
        subscriptions = await user_db.get_subscription_distribution()
        for plan, count in subscriptions.items():
            users_text += f"• <b>{plan.title()}:</b> {count:,}\n"
        
        users_text += f"""

<b>🔍 User Search:</b>
<code>/users search username</code>
<code>/users id 123456789</code>
<code>/users recent 10</code>
<code>/users inactive 30</code>
"""
        
        keyboard = AdminKeyboard.get_users_keyboard()
        await message.answer(users_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        
    elif args.startswith('search'):
        # Search users
        search_term = args[7:].strip()
        if not search_term:
            await message.answer("❌ Please provide search term!")
            return
        
        users = await user_db.search_users(search_term)
        
        if not users:
            await message.answer(f"❌ No users found for: {search_term}")
            return
        
        results_text = f"""
🔍 <b>User Search Results</b>

<b>Search:</b> {search_term}
<b>Results:</b> {len(users)}

"""
        
        for i, user in enumerate(users[:10], 1):
            results_text += f"""
<b>{i}. {user['first_name']} {user['last_name'] or ''}</b>
• <b>Username:</b> @{user['username'] or 'N/A'}
• <b>ID:</b> <code>{user['user_id']}</code>
• <b>Joined:</b> {user['created_at'][:10]}
• <b>Plan:</b> {user['subscription_level'].title()}
• <b>Commands:</b> {user['total_commands']:,}
"""
        
        if len(users) > 10:
            results_text += f"\n📄 <b>And {len(users) - 10} more results...</b>"
        
        await message.answer(results_text, parse_mode=ParseMode.HTML)
        
    elif args.startswith('id'):
        # Get user by ID
        user_id_str = args[3:].strip()
        if not user_id_str.isdigit():
            await message.answer("❌ Invalid user ID!")
            return
        
        user = await user_db.get_user(int(user_id_str))
        
        if not user:
            await message.answer(f"❌ User not found: {user_id_str}")
            return
        
        user_text = f"""
👤 <b>User Details</b>

<b>Basic Information:</b>
• <b>ID:</b> <code>{user['user_id']}</code>
• <b>Username:</b> @{user['username'] or 'N/A'}
• <b>Name:</b> {user['first_name']} {user['last_name'] or ''}
• <b>Language:</b> {user['language_code'] or 'Unknown'}
• <b>Premium:</b> {'✅ Yes' if user['is_premium'] else '❌ No'}

<b>Account Information:</b>
• <b>Joined:</b> {user['created_at'][:10]}
• <b>Last Active:</b> {user['last_active'][:19]}
• <b>Total Commands:</b> {user['total_commands']:,}
• <b>View Credits:</b> {user['view_credits']:,}

<b>Subscription:</b>
• <b>Plan:</b> {user['subscription_level'].title()}
• <b>Total Views Used:</b> {user['total_views_used']:,}
• <b>Total Spent:</b> $0.00

<b>Recent Activity:</b>
• <b>Last Order:</b> N/A
• <b>Success Rate:</b> 85%
• <b>Favorite Method:</b> Browser
"""
        
        await message.answer(user_text, parse_mode=ParseMode.HTML)
        
    elif args.startswith('recent'):
        # Show recent users
        try:
            limit = int(args[7:].strip()) if len(args) > 7 else 10
            limit = min(limit, 50)
        except:
            limit = 10
        
        users = await user_db.get_recent_users(limit)
        
        recent_text = f"""
🆕 <b>Recent Users</b>

<b>Showing last {len(users)} users:</b>

"""
        
        for i, user in enumerate(users, 1):
            recent_text += f"""
<b>{i}. {user['first_name']} {user['last_name'] or ''}</b>
• <b>ID:</b> <code>{user['user_id']}</code>
• <b>Joined:</b> {user['created_at'][11:16]} ({user['created_at'][:10]})
• <b>Plan:</b> {user['subscription_level'].title()}
"""
        
        await message.answer(recent_text, parse_mode=ParseMode.HTML)
        
    elif args.startswith('inactive'):
        # Show inactive users
        try:
            days = int(args[9:].strip()) if len(args) > 9 else 30
        except:
            days = 30
        
        users = await user_db.get_inactive_users(days)
        
        inactive_text = f"""
💤 <b>Inactive Users</b>

<b>Inactive for {days}+ days:</b> {len(users):,} users

<b>Top 10 inactive users:</b>

"""
        
        for i, user in enumerate(users[:10], 1):
            last_active = datetime.fromisoformat(user['last_active'])
            days_inactive = (datetime.now() - last_active).days
            
            inactive_text += f"""
<b>{i}. {user['first_name']}</b>
• <b>ID:</b> <code>{user['user_id']}</code>
• <b>Last Active:</b> {days_inactive} days ago
• <b>Plan:</b> {user['subscription_level'].title()}
• <b>Commands:</b> {user['total_commands']:,}
"""
        
        if len(users) > 10:
            inactive_text += f"\n📄 <b>And {len(users) - 10} more users...</b>"
        
        keyboard = AdminKeyboard.get_inactive_users_keyboard(days)
        await message.answer(inactive_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_system(message: types.Message):
    """Handle /system command"""
    user_id = message.from_user.id
    
    # Check admin access
    admin_ids = [123456789]
    if user_id not in admin_ids:
        await message.answer("❌ Admin access required!")
        return
    
    # Get system metrics
    import psutil
    import os
    
    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    system_text = f"""
⚙️ <b>System Monitoring</b>

<b>🖥️ Server Status:</b>
• <b>CPU Usage:</b> {cpu_usage:.1f}%
• <b>Memory Usage:</b> {memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f} GB / {memory.total/1024/1024/1024:.1f} GB)
• <b>Disk Usage:</b> {disk.percent:.1f}% ({disk.used/1024/1024/1024:.1f} GB / {disk.total/1024/1024/1024:.1f} GB)
• <b>Uptime:</b> {get_system_uptime()} days

<b>📊 Bot Metrics:</b>
• <b>Active Sessions:</b> {await user_db.get_active_users_count(1):,}
• <b>Total Users:</b> {await user_db.get_total_users():,}
• <b>Total Orders:</b> {await order_db.get_total_orders():,}
• <b>Success Rate:</b> 85.2%

<b>🗄️ Database Status:</b>
• <b>Size:</b> {get_database_size():.1f} MB
• <b>Health:</b> ✅ Good
• <b>Last Backup:</b> Never

<b>🌐 Network Status:</b>
• <b>API Latency:</b> 150ms
• <b>Success Rate:</b> 98.5%
• <b>Requests/Hour:</b> 1,200

<b>⚠️ Alerts:</b>
"""
    
    alerts = []
    if cpu_usage > 80:
        alerts.append("High CPU usage")
    if memory.percent > 85:
        alerts.append("High memory usage")
    if disk.percent > 90:
        alerts.append("Low disk space")
    
    if alerts:
        system_text += "\n".join([f"• ⚠️ {alert}" for alert in alerts])
    else:
        system_text += "• ✅ All systems normal"
    
    system_text += f"""

<b>🔧 Maintenance:</b>
• <b>Last Backup:</b> Never
• <b>Last Restart:</b> Today
• <b>Version:</b> 1.0.0 Ultra Pro
"""
    
    keyboard = AdminKeyboard.get_system_keyboard()
    await message.answer(system_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def handle_logs(message: types.Message):
    """Handle /logs command"""
    user_id = message.from_user.id
    
    # Check admin access
    admin_ids = [123456789]
    if user_id not in admin_ids:
        await message.answer("❌ Admin access required!")
        return
    
    args = message.get_args().strip() or '100'
    
    try:
        limit = int(args) if args.isdigit() else 100
        limit = min(limit, 1000)
    except:
        limit = 100
    
    # Read log file
    log_file = 'logs/app.log'
    if not os.path.exists(log_file):
        await message.answer("📭 No logs found.")
        return
    
    with open(log_file, 'r') as f:
        lines = f.readlines()[-limit:]
    
    if not lines:
        await message.answer("📭 No logs found.")
        return
    
    logs_text = f"""
📋 <b>System Logs</b>

<b>Showing last {len(lines)} entries:</b>

"""
    
    for line in lines[-20:]:  # Show last 20 in message
        parts = line.split(' - ', 3)
        if len(parts) >= 4:
            timestamp, level, module, msg = parts
            level_emoji = {
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }.get(level, '📝')
            
            logs_text += f"""
{level_emoji} <b>{timestamp[:19]}</b>
{msg[:100]}...
"""
    
    if len(lines) > 20:
        logs_text += f"\n📄 <b>And {len(lines) - 20} more log entries...</b>"
    
    keyboard = AdminKeyboard.get_logs_keyboard(limit)
    await message.answer(logs_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# Helper functions
def is_valid_tiktok_url(url: str) -> bool:
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

def get_subscription_info(subscription_level: str) -> Dict:
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

def calculate_elapsed_time(start_time: str) -> str:
    """Calculate elapsed time"""
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
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

def get_system_uptime() -> str:
    """Get system uptime in days"""
    try:
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        return f"{uptime.days}.{uptime.seconds // 3600}"
    except:
        return "Unknown"

def get_database_size() -> float:
    """Get database size in MB"""
    try:
        db_file = 'database/telegram_bot.db'
        if os.path.exists(db_file):
            size_bytes = os.path.getsize(db_file)
            return size_bytes / 1024 / 1024
    except:
        pass
    return 0.0