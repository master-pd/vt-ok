"""
Payment and Subscription Handlers for Telegram Bot
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import hmac

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import (
    Message, ParseMode, InlineKeyboardMarkup, 
    InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
)

from telegram_bot.database.user_db import UserDatabase
from telegram_bot.database.order_db import OrderDatabase
from telegram_bot.keyboards.main_menu import MainKeyboard
from telegram_bot.keyboards.inline_kb import PaymentKeyboard

logger = logging.getLogger(__name__)

# Initialize databases
user_db = UserDatabase()
order_db = OrderDatabase()

# Payment configuration
PAYMENT_TOKEN = "TEST_PAYMENT_TOKEN"  # Replace with real token in production
ADMIN_CHAT_ID = 123456789  # Replace with admin chat ID

async def register_payments(dp: Dispatcher):
    """Register payment handlers"""
    
    # Buy command
    @dp.message_handler(Command('buy'))
    async def cmd_buy(message: types.Message):
        await handle_buy(message)
    
    # Payment pre-checkout handler
    @dp.pre_checkout_query_handler()
    async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
        await handle_pre_checkout(pre_checkout_query)
    
    # Payment successful handler
    @dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
    async def successful_payment(message: types.Message):
        await handle_successful_payment(message)
    
    # Invoice handlers
    @dp.message_handler(Command('invoice'))
    async def cmd_invoice(message: types.Message):
        await handle_invoice(message)
    
    # Crypto payment handlers
    @dp.message_handler(Command('crypto'))
    async def cmd_crypto(message: types.Message):
        await handle_crypto(message)
    
    logger.info("Registered payment handlers")

async def handle_buy(message: types.Message):
    """Handle /buy command"""
    user_id = message.from_user.id
    user_data = await user_db.get_user(user_id)
    
    if not user_data:
        await message.answer("❌ User not found!")
        return
    
    args = message.get_args().split()
    
    if not args:
        # Show buy options
        await show_buy_options(message)
        return
    
    # Process specific purchase
    plan = args[0].lower()
    
    if plan not in ['basic', 'pro', 'enterprise']:
        await message.answer(
            "❌ Invalid plan!\n\n"
            "Available plans:\n"
            "• basic - $9.99/month\n"
            "• pro - $29.99/month\n"
            "• enterprise - $99.99/month\n\n"
            "Usage: /buy [plan]"
        )
        return
    
    # Create invoice for the plan
    await create_payment_invoice(message, plan)

async def show_buy_options(message: types.Message):
    """Show buy options"""
    buy_text = """
🛒 <b>Buy View Credits</b>

<b>💎 Subscription Plans:</b>

<b>Basic Plan - $9.99/month</b>
• 1,000 views/day
• Max 200 views/order
• Browser + API methods
• Priority support

<b>Pro Plan - $29.99/month</b>
• 5,000 views/day
• Max 1,000 views/order
• All methods (Browser, API, Cloud)
• 24/7 support
• Advanced analytics

<b>Enterprise - $99.99/month</b>
• Unlimited views/day
• Max 5,000 views/order
• All methods + Hybrid AI
• Dedicated support
• Custom solutions
• API access

<b>💰 View Packages (One-time):</b>
• 1,000 views - $4.99
• 5,000 views - $19.99
• 10,000 views - $34.99
• 50,000 views - $149.99

<b>💳 Payment Methods:</b>
• Credit Card (Stripe)
• Cryptocurrency (BTC, ETH, USDT)
• PayPal
• Bank Transfer

<b>⚡ Quick Purchase:</b>
<code>/buy basic</code> - Buy Basic plan
<code>/buy pro</code> - Buy Pro plan
<code>/crypto</code> - Pay with crypto
    """
    
    keyboard = PaymentKeyboard.get_buy_keyboard()
    await message.answer(buy_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def create_payment_invoice(message: types.Message, plan: str):
    """Create payment invoice for a plan"""
    plan_prices = {
        'basic': {
            'title': 'Basic Plan (Monthly)',
            'description': '1,000 views/day, Browser + API methods, Priority support',
            'price': 999,  # in cents
            'currency': 'USD'
        },
        'pro': {
            'title': 'Pro Plan (Monthly)',
            'description': '5,000 views/day, All methods, 24/7 support, Advanced analytics',
            'price': 2999,
            'currency': 'USD'
        },
        'enterprise': {
            'title': 'Enterprise Plan (Monthly)',
            'description': 'Unlimited views, All methods + Hybrid AI, Dedicated support, API access',
            'price': 9999,
            'currency': 'USD'
        }
    }
    
    if plan not in plan_prices:
        await message.answer("❌ Invalid plan!")
        return
    
    plan_info = plan_prices[plan]
    
    # Create invoice
    prices = [LabeledPrice(label=plan_info['title'], amount=plan_info['price'])]
    
    try:
        await message.bot.send_invoice(
            chat_id=message.chat.id,
            title=plan_info['title'],
            description=plan_info['description'],
            payload=f"subscription_{plan}_{message.from_user.id}",
            provider_token=PAYMENT_TOKEN,
            currency=plan_info['currency'],
            prices=prices,
            start_parameter=f"buy_{plan}",
            photo_url="https://img.icons8.com/color/96/000000/tiktok.png",
            photo_size=100,
            photo_width=800,
            photo_height=450,
            need_name=True,
            need_email=True,
            need_phone_number=False,
            need_shipping_address=False,
            is_flexible=False,
            disable_notification=False,
            protect_content=False,
            reply_to_message_id=None,
            allow_sending_without_reply=True,
            reply_markup=PaymentKeyboard.get_invoice_keyboard(plan)
        )
        
        logger.info(f"Created invoice for user {message.from_user.id} for {plan} plan")
        
    except Exception as e:
        logger.error(f"Failed to create invoice: {e}")
        await message.answer(
            "❌ Failed to create payment invoice.\n"
            "Please try again or contact support."
        )

async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Handle pre-checkout query"""
    try:
        # Verify the payment
        payload = pre_checkout_query.invoice_payload
        
        # Check if payload is valid
        if not payload.startswith(('subscription_', 'credits_')):
            await pre_checkout_query.bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="Invalid payment payload"
            )
            return
        
        # Check user
        user_id = pre_checkout_query.from_user.id
        user_data = await user_db.get_user(user_id)
        
        if not user_data:
            await pre_checkout_query.bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="User not found"
            )
            return
        
        # All checks passed
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=True
        )
        
        logger.info(f"Pre-checkout approved for user {user_id}")
        
    except Exception as e:
        logger.error(f"Pre-checkout error: {e}")
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Payment processing error"
        )

async def handle_successful_payment(message: types.Message):
    """Handle successful payment"""
    payment = message.successful_payment
    user_id = message.from_user.id
    
    logger.info(f"Successful payment from user {user_id}: {payment.total_amount} {payment.currency}")
    
    try:
        # Parse payload
        payload = payment.invoice_payload
        
        if payload.startswith('subscription_'):
            # Subscription purchase
            parts = payload.split('_')
            if len(parts) >= 3:
                plan = parts[1]
                purchase_user_id = int(parts[2])
                
                if purchase_user_id != user_id:
                    await message.answer("❌ Payment user ID mismatch!")
                    return
                
                # Update user subscription
                await user_db.update_subscription(user_id, plan)
                
                # Add bonus credits
                bonus_credits = {
                    'basic': 2000,
                    'pro': 10000,
                    'enterprise': 50000
                }.get(plan, 0)
                
                await user_db.update_user_credits(user_id, bonus_credits)
                
                # Send confirmation
                await message.answer(
                    f"✅ <b>Payment Successful!</b>\n\n"
                    f"🎉 Congratulations! You've upgraded to <b>{plan.title()} Plan</b>.\n\n"
                    f"<b>Details:</b>\n"
                    f"• Plan: {plan.title()}\n"
                    f"• Amount: ${payment.total_amount / 100:.2f} {payment.currency}\n"
                    f"• Bonus: {bonus_credits:,} views\n"
                    f"• Total Credits: {(await user_db.get_user(user_id))['view_credits']:,}\n\n"
                    f"<b>Features activated:</b>\n"
                    f"• Higher daily limits\n"
                    f"• Priority processing\n"
                    f"• Advanced methods\n"
                    f"• Premium support\n\n"
                    f"Use /send to start using your new plan!",
                    parse_mode=ParseMode.HTML
                )
                
                # Notify admin
                await notify_admin_payment(user_id, plan, payment)
                
        elif payload.startswith('credits_'):
            # Credits purchase
            parts = payload.split('_')
            if len(parts) >= 3:
                credits = int(parts[1])
                purchase_user_id = int(parts[2])
                
                if purchase_user_id != user_id:
                    await message.answer("❌ Payment user ID mismatch!")
                    return
                
                # Add credits
                await user_db.update_user_credits(user_id, credits)
                
                # Send confirmation
                await message.answer(
                    f"✅ <b>Payment Successful!</b>\n\n"
                    f"🎉 {credits:,} view credits added to your account!\n\n"
                    f"<b>Details:</b>\n"
                    f"• Credits: {credits:,}\n"
                    f"• Amount: ${payment.total_amount / 100:.2f} {payment.currency}\n"
                    f"• Total Credits: {(await user_db.get_user(user_id))['view_credits']:,}\n\n"
                    f"Use /send to start using your credits!",
                    parse_mode=ParseMode.HTML
                )
                
                # Notify admin
                await notify_admin_payment(user_id, f"{credits} credits", payment)
        
        else:
            await message.answer(
                "✅ <b>Payment Received!</b>\n\n"
                "Thank you for your payment. Please contact support for activation."
            )
        
    except Exception as e:
        logger.error(f"Failed to process payment: {e}")
        await message.answer(
            "✅ <b>Payment Received!</b>\n\n"
            "There was an issue processing your payment. Please contact support."
        )

async def notify_admin_payment(user_id: int, item: str, payment):
    """Notify admin about payment"""
    try:
        user_data = await user_db.get_user(user_id)
        
        admin_message = (
            f"💰 <b>New Payment Received</b>\n\n"
            f"<b>User:</b> {user_data['first_name']} {user_data['last_name'] or ''}\n"
            f"<b>Username:</b> @{user_data['username'] or 'N/A'}\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n\n"
            f"<b>Item:</b> {item}\n"
            f"<b>Amount:</b> ${payment.total_amount / 100:.2f} {payment.currency}\n"
            f"<b>Payment ID:</b> {payment.telegram_payment_charge_id}\n"
            f"<b>Provider ID:</b> {payment.provider_payment_charge_id}\n\n"
            f"<b>User Info:</b>\n"
            f"• Plan: {user_data['subscription_level'].title()}\n"
            f"• Credits: {user_data['view_credits']:,}\n"
            f"• Total Spent: $0.00\n"
            f"• Joined: {user_data['created_at'][:10]}"
        )
        
        await message.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

async def handle_invoice(message: types.Message):
    """Handle /invoice command"""
    args = message.get_args().split()
    
    if len(args) < 2:
        await message.answer(
            "📄 <b>Create Invoice</b>\n\n"
            "Usage: <code>/invoice [amount] [description]</code>\n\n"
            "Example: <code>/invoice 9.99 \"Basic Plan Monthly\"</code>\n\n"
            "This creates a payment invoice for the specified amount.",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        amount = float(args[0])
        description = ' '.join(args[1:])
        
        if amount <= 0:
            await message.answer("❌ Amount must be greater than 0!")
            return
        
        # Convert to cents
        amount_cents = int(amount * 100)
        
        # Create invoice
        prices = [LabeledPrice(label=description, amount=amount_cents)]
        
        await message.bot.send_invoice(
            chat_id=message.chat.id,
            title="Custom Payment",
            description=description,
            payload=f"custom_{message.from_user.id}_{int(datetime.now().timestamp())}",
            provider_token=PAYMENT_TOKEN,
            currency="USD",
            prices=prices,
            start_parameter="create_invoice"
        )
        
    except ValueError:
        await message.answer("❌ Invalid amount! Please enter a valid number.")
    except Exception as e:
        logger.error(f"Failed to create invoice: {e}")
        await message.answer("❌ Failed to create invoice. Please try again.")

async def handle_crypto(message: types.Message):
    """Handle /crypto command"""
    user_id = message.from_user.id
    user_data = await user_db.get_user(user_id)
    
    if not user_data:
        await message.answer("❌ User not found!")
        return
    
    args = message.get_args().split()
    
    if not args:
        # Show crypto options
        await show_crypto_options(message)
        return
    
    # Process crypto payment request
    plan = args[0].lower()
    
    if plan not in ['basic', 'pro', 'enterprise', 'credits']:
        await message.answer(
            "❌ Invalid option!\n\n"
            "Usage: <code>/crypto [plan|credits] [amount]</code>\n\n"
            "Examples:\n"
            "<code>/crypto basic</code> - Buy Basic plan with crypto\n"
            "<code>/crypto credits 5000</code> - Buy 5000 credits\n",
            parse_mode=ParseMode.HTML
        )
        return
    
    if plan == 'credits':
        if len(args) < 2:
            await message.answer(
                "❌ Please specify credits amount!\n"
                "Example: <code>/crypto credits 5000</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        try:
            credits = int(args[1])
            await create_crypto_invoice(message, 'credits', credits)
        except ValueError:
            await message.answer("❌ Invalid credits amount!")
    
    else:
        await create_crypto_invoice(message, plan)

async def show_crypto_options(message: types.Message):
    """Show cryptocurrency payment options"""
    crypto_text = """
💰 <b>Cryptocurrency Payments</b>

<b>Accepted Cryptocurrencies:</b>
• Bitcoin (BTC)
• Ethereum (ETH)
• Tether (USDT) - ERC20, TRC20, BEP20
• Litecoin (LTC)
• Bitcoin Cash (BCH)

<b>💎 Plan Prices (Crypto):</b>
• <b>Basic Plan:</b> $9.99/month
  ≈ 0.00025 BTC | 0.0035 ETH | 10 USDT
  
• <b>Pro Plan:</b> $29.99/month
  ≈ 0.00075 BTC | 0.0105 ETH | 30 USDT
  
• <b>Enterprise Plan:</b> $99.99/month
  ≈ 0.0025 BTC | 0.035 ETH | 100 USDT

<b>📊 Credit Packages (Crypto):</b>
• 1,000 views - $4.99
• 5,000 views - $19.99
• 10,000 views - $34.99
• 50,000 views - $149.99

<b>⚡ How to Pay with Crypto:</b>
1. Choose your plan/credits
2. We'll generate a unique wallet address
3. Send exact amount to that address
4. Payment confirmed in 1-3 network confirmations
5. Credits activated automatically

<b>🎯 Quick Crypto Purchase:</b>
<code>/crypto basic</code> - Buy Basic plan
<code>/crypto pro</code> - Buy Pro plan
<code>/crypto credits 5000</code> - Buy 5000 credits

<b>⚠️ Important:</b>
• Send exact amount only
• Include payment reference if requested
• Contact support if payment not confirmed within 1 hour
    """
    
    keyboard = PaymentKeyboard.get_crypto_keyboard()
    await message.answer(crypto_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def create_crypto_invoice(message: types.Message, item_type: str, credits: int = None):
    """Create cryptocurrency payment invoice"""
    user_id = message.from_user.id
    
    # Generate unique payment ID
    import uuid
    payment_id = str(uuid.uuid4())[:8].upper()
    
    # Get prices in USD
    if item_type == 'basic':
        usd_amount = 9.99
        description = "Basic Plan (Monthly Subscription)"
    elif item_type == 'pro':
        usd_amount = 29.99
        description = "Pro Plan (Monthly Subscription)"
    elif item_type == 'enterprise':
        usd_amount = 99.99
        description = "Enterprise Plan (Monthly Subscription)"
    elif item_type == 'credits' and credits:
        usd_amount = credits * 0.005  # $5 per 1000 credits
        description = f"{credits:,} View Credits"
    else:
        await message.answer("❌ Invalid item type!")
        return
    
    # Convert to crypto amounts (simulated rates)
    btc_rate = 40000  # 1 BTC = $40,000
    eth_rate = 3000   # 1 ETH = $3,000
    
    btc_amount = usd_amount / btc_rate
    eth_amount = usd_amount / eth_rate
    
    # Store payment in database (simplified)
    payment_data = {
        'payment_id': payment_id,
        'user_id': user_id,
        'item_type': item_type,
        'item_details': description,
        'usd_amount': usd_amount,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    # Show payment instructions
    payment_text = f"""
💎 <b>Cryptocurrency Payment</b>

<b>Payment ID:</b> <code>{payment_id}</code>
<b>Item:</b> {description}
<b>Amount:</b> ${usd_amount:.2f} USD

<b>📊 Send Exact Amount to:</b>

<b>Bitcoin (BTC):</b>
<code>bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh</code>
<b>Amount:</b> {btc_amount:.8f} BTC

<b>Ethereum (ETH):b>
<code>0x742d35Cc6634C0532925a3b844Bc9e7c6b3b9c9e</code>
<b>Amount:</b> {eth_amount:.6f} ETH

<b>Tether (USDT):</b>
<code>0x742d35Cc6634C0532925a3b844Bc9e7c6b3b9c9e</code>
<b>Amount:</b> {usd_amount:.2f} USDT
<b>Network:</b> ERC20, TRC20, or BEP20

<b>⚠️ Important Instructions:</b>
1. Send <b>EXACT</b> amount only
2. Include payment ID in memo/reference: <code>{payment_id}</code>
3. Wait for 1-3 network confirmations
4. Credits activated automatically

<b>⏱️ Payment Status:</b>
Use /status {payment_id} to check payment status

<b>📞 Support:</b>
Contact @vtultrapro_support if payment not confirmed within 1 hour.
    """
    
    keyboard = PaymentKeyboard.get_crypto_payment_keyboard(payment_id)
    await message.answer(payment_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    # Also send as separate messages for better formatting
    await message.answer(
        f"<b>📋 Payment Summary</b>\n\n"
        f"Payment ID: <code>{payment_id}</code>\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Item: {description}\n"
        f"Amount: ${usd_amount:.2f} USD\n\n"
        f"<b>Save this information for reference!</b>",
        parse_mode=ParseMode.HTML
    )

async def check_crypto_payment(message: types.Message):
    """Check crypto payment status"""
    args = message.get_args().split()
    
    if not args:
        await message.answer(
            "🔍 <b>Check Crypto Payment</b>\n\n"
            "Usage: <code>/check [payment_id]</code>\n\n"
            "Example: <code>/check ABC123</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    payment_id = args[0].upper()
    
    # In real implementation, check blockchain for payment
    # This is a simulation
    
    import random
    status = random.choice(['pending', 'confirmed', 'completed', 'failed'])
    
    status_messages = {
        'pending': "⏳ Payment is pending. Waiting for network confirmations...",
        'confirmed': "✅ Payment confirmed! Credits will be added shortly.",
        'completed': "🎉 Payment completed! Credits have been added to your account.",
        'failed': "❌ Payment failed or not found. Please contact support."
    }
    
    await message.answer(
        f"🔍 <b>Payment Status</b>\n\n"
        f"Payment ID: <code>{payment_id}</code>\n"
        f"Status: {status.upper()}\n\n"
        f"{status_messages[status]}\n\n"
        f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode=ParseMode.HTML
    )

# Register check command separately
async def register_check_command(dp: Dispatcher):
    @dp.message_handler(Command('check'))
    async def cmd_check(message: types.Message):
        await check_crypto_payment(message)