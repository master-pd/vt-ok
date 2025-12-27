"""
Inline Query Handlers for Telegram Bot
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from aiogram import types, Dispatcher
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.markdown import hbold, hcode, hlink

logger = logging.getLogger(__name__)

async def register_inline(dp: Dispatcher):
    """Register inline query handlers"""
    
    @dp.inline_handler()
    async def inline_query_handler(inline_query: InlineQuery):
        await handle_inline_query(inline_query)
    
    logger.info("Registered inline query handlers")

async def handle_inline_query(inline_query: InlineQuery):
    """Handle inline queries"""
    query = inline_query.query.strip().lower()
    user_id = inline_query.from_user.id
    
    logger.info(f"Inline query from user {user_id}: {query}")
    
    results = []
    
    if not query or query == "help":
        # Show help/info
        results.append(
            InlineQueryResultArticle(
                id="1",
                title="VT ULTRA PRO Bot Help",
                description="Get help with the bot commands",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🎯 <b>VT ULTRA PRO TikTok Bot</b>\n\n"
                        "Use these commands in chat:\n"
                        "/start - Start the bot\n"
                        "/send - Send views to TikTok video\n"
                        "/balance - Check your credits\n"
                        "/stats - View your statistics\n"
                        "/help - Show all commands\n\n"
                        "Send a TikTok URL to get started!"
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/tiktok.png"
            )
        )
    
    elif "send" in query or "views" in query:
        # Show send options
        results.append(
            InlineQueryResultArticle(
                id="2",
                title="Send TikTok Views",
                description="Send views to a TikTok video",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "📤 <b>Send TikTok Views</b>\n\n"
                        "To send views, use:\n"
                        "<code>/send https://tiktok.com/@user/video/123 500</code>\n\n"
                        "Or just send me a TikTok URL!"
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/upload.png"
            )
        )
    
    elif "balance" in query or "credits" in query:
        # Show balance info
        results.append(
            InlineQueryResultArticle(
                id="3",
                title="Check Balance",
                description="Check your view credits",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "💰 <b>Your Balance</b>\n\n"
                        "Use /balance to check your view credits.\n\n"
                        "Free users get 100 views daily!\n"
                        "Upgrade with /subscribe for more."
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/money-bag.png"
            )
        )
    
    elif "stats" in query or "statistics" in query:
        # Show stats info
        results.append(
            InlineQueryResultArticle(
                id="4",
                title="View Statistics",
                description="Check your view statistics",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "📊 <b>Your Statistics</b>\n\n"
                        "Use /stats to view:\n"
                        "• Total views sent\n"
                        "• Success rate\n"
                        "• Active orders\n"
                        "• Subscription info"
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/statistics.png"
            )
        )
    
    elif "status" in query or "order" in query:
        # Show status info
        results.append(
            InlineQueryResultArticle(
                id="5",
                title="Check Order Status",
                description="Check your order status",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "📋 <b>Order Status</b>\n\n"
                        "Use /status to check active orders:\n"
                        "<code>/status ORDER_ID</code>\n\n"
                        "Or use /status without ID to see all active orders."
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/checked.png"
            )
        )
    
    elif "subscribe" in query or "upgrade" in query:
        # Show subscription info
        results.append(
            InlineQueryResultArticle(
                id="6",
                title="Upgrade Subscription",
                description="Upgrade your plan for more features",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "💎 <b>Upgrade Subscription</b>\n\n"
                        "Use /subscribe to view plans:\n"
                        "• Free: 100 views/day\n"
                        "• Basic: $9.99/month\n"
                        "• Pro: $29.99/month\n"
                        "• Enterprise: $99.99/month"
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/diamond.png"
            )
        )
    
    elif "methods" in query or "how" in query:
        # Show methods info
        results.append(
            InlineQueryResultArticle(
                id="7",
                title="View Methods",
                description="Learn about view methods",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "⚡ <b>View Methods</b>\n\n"
                        "Use /methods to see available methods:\n"
                        "• Browser: High quality (85-95%)\n"
                        "• API: Fast delivery (70-85%)\n"
                        "• Cloud: Bulk views (60-75%)\n"
                        "• Hybrid: Best of all (90-98%)"
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/rocket.png"
            )
        )
    
    elif "support" in query or "help" in query:
        # Show support info
        results.append(
            InlineQueryResultArticle(
                id="8",
                title="Contact Support",
                description="Get help from support team",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🆘 <b>Support & Help</b>\n\n"
                        "Use /support for assistance:\n"
                        "• Telegram: @vtultrapro_support\n"
                        "• Email: support@vtultrapro.com\n"
                        "• Website: https://vtultrapro.com"
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/customer-support.png"
            )
        )
    
    elif "admin" in query:
        # Show admin info (only for admins)
        admin_ids = [123456789]  # Example admin ID
        if inline_query.from_user.id in admin_ids:
            results.append(
                InlineQueryResultArticle(
                    id="9",
                    title="Admin Panel",
                    description="Access admin features",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            "👨‍💼 <b>Admin Panel</b>\n\n"
                            "Admin commands:\n"
                            "/admin - Admin dashboard\n"
                            "/broadcast - Send to all users\n"
                            "/users - User management\n"
                            "/system - System monitoring\n"
                            "/logs - View system logs"
                        ),
                        parse_mode="HTML"
                    ),
                    thumb_url="https://img.icons8.com/color/96/000000/administrator-male.png"
                )
            )
    
    # Add quick send templates for common URLs
    if "tiktok.com" in query or "vm.tiktok.com" in query or "vt.tiktok.com" in query:
        # If user is typing a TikTok URL
        if "http" in query:
            url = query
            results.append(
                InlineQueryResultArticle(
                    id="10",
                    title="Send Views to This Video",
                    description="Send 100 views to this TikTok",
                    input_message_content=InputTextMessageContent(
                        message_text=f"/send {url} 100",
                        parse_mode=None
                    ),
                    thumb_url="https://img.icons8.com/color/96/000000/tiktok.png"
                )
            )
            
            results.append(
                InlineQueryResultArticle(
                    id="11",
                    title="Send 500 Views",
                    description="Send 500 views to this TikTok",
                    input_message_content=InputTextMessageContent(
                        message_text=f"/send {url} 500",
                        parse_mode=None
                    ),
                    thumb_url="https://img.icons8.com/color/96/000000/tiktok.png"
                )
            )
            
            results.append(
                InlineQueryResultArticle(
                    id="12",
                    title="Send 1000 Views",
                    description="Send 1000 views to this TikTok",
                    input_message_content=InputTextMessageContent(
                        message_text=f"/send {url} 1000",
                        parse_mode=None
                    ),
                    thumb_url="https://img.icons8.com/color/96/000000/tiktok.png"
                )
            )
    
    # If no specific results, show general help
    if not results:
        results.append(
            InlineQueryResultArticle(
                id="0",
                title="VT ULTRA PRO Bot",
                description="Type a command or TikTok URL",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🎯 <b>VT ULTRA PRO TikTok Bot</b>\n\n"
                        "I can help you send views to TikTok videos!\n\n"
                        "Try these:\n"
                        "• Send a TikTok URL\n"
                        "• Type 'send' for sending options\n"
                        "• Type 'balance' to check credits\n"
                        "• Type 'help' for all commands"
                    ),
                    parse_mode="HTML"
                ),
                thumb_url="https://img.icons8.com/color/96/000000/robot.png"
            )
        )
    
    # Answer the inline query
    try:
        await inline_query.answer(results, cache_time=300, is_personal=True)
    except Exception as e:
        logger.error(f"Failed to answer inline query: {e}")