"""
Inline Keyboards for Special Features
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class PaymentKeyboard:
    """Payment-related keyboards"""
    
    @staticmethod
    def get_buy_keyboard() -> InlineKeyboardMarkup:
        """Get buy options keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("💎 Basic Plan", callback_data="buy_basic"),
            InlineKeyboardButton("🚀 Pro Plan", callback_data="buy_pro"),
            InlineKeyboardButton("🏢 Enterprise", callback_data="buy_enterprise"),
            InlineKeyboardButton("💰 View Packages", callback_data="buy_credits"),
            InlineKeyboardButton("💳 Credit Card", callback_data="pay_card"),
            InlineKeyboardButton("₿ Cryptocurrency", callback_data="pay_crypto"),
            InlineKeyboardButton("🏦 PayPal", callback_data="pay_paypal"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
        )
        
        return keyboard
    
    @staticmethod
    def get_invoice_keyboard(plan: str) -> InlineKeyboardMarkup:
        """Get invoice payment keyboard"""
        keyboard = InlineKeyboardMarkup()
        
        keyboard.add(
            InlineKeyboardButton("💳 Pay with Card", pay=True),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")
        )
        
        return keyboard
    
    @staticmethod
    def get_crypto_keyboard() -> InlineKeyboardMarkup:
        """Get cryptocurrency options keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("₿ Bitcoin", callback_data="crypto_btc"),
            InlineKeyboardButton("Ξ Ethereum", callback_data="crypto_eth"),
            InlineKeyboardButton("💵 USDT", callback_data="crypto_usdt"),
            InlineKeyboardButton("Ł Litecoin", callback_data="crypto_ltc"),
            InlineKeyboardButton("Ƀ Bitcoin Cash", callback_data="crypto_bch"),
            InlineKeyboardButton("📋 How to Pay", callback_data="crypto_help"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_buy")
        )
        
        return keyboard
    
    @staticmethod
    def get_crypto_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
        """Get crypto payment confirmation keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("✅ I've Paid", callback_data=f"crypto_paid:{payment_id}"),
            InlineKeyboardButton("🔍 Check Status", callback_data=f"check_payment:{payment_id}"),
            InlineKeyboardButton("📞 Need Help?", callback_data="crypto_support"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_crypto")
        )
        
        return keyboard
    
    @staticmethod
    def get_credit_packages_keyboard() -> InlineKeyboardMarkup:
        """Get credit packages keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("1,000 views - $4.99", callback_data="buy_1000"),
            InlineKeyboardButton("5,000 views - $19.99", callback_data="buy_5000"),
            InlineKeyboardButton("10,000 views - $34.99", callback_data="buy_10000"),
            InlineKeyboardButton("50,000 views - $149.99", callback_data="buy_50000"),
            InlineKeyboardButton("💳 Credit Card", callback_data="pay_credits_card"),
            InlineKeyboardButton("₿ Cryptocurrency", callback_data="pay_credits_crypto"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_buy")
        )
        
        return keyboard

class ViewMethodsKeyboard:
    """View methods selection keyboards"""
    
    @staticmethod
    def get_method_selection_keyboard() -> InlineKeyboardMarkup:
        """Get method selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("🌐 Browser", callback_data="method_browser"),
            InlineKeyboardButton("⚡ API", callback_data="method_api"),
            InlineKeyboardButton("☁️ Cloud", callback_data="method_cloud"),
            InlineKeyboardButton("🤖 Hybrid AI", callback_data="method_hybrid"),
            InlineKeyboardButton("🔀 Auto Select", callback_data="method_auto"),
            InlineKeyboardButton("📊 Compare", callback_data="method_compare"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_method")
        )
        
        return keyboard
    
    @staticmethod
    def get_method_compare_keyboard() -> InlineKeyboardMarkup:
        """Get method comparison keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("✅ Success Rate", callback_data="compare_success"),
            InlineKeyboardButton("⚡ Speed", callback_data="compare_speed"),
            InlineKeyboardButton("🛡️ Safety", callback_data="compare_safety"),
            InlineKeyboardButton("💰 Cost", callback_data="compare_cost"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_methods")
        )
        
        return keyboard

class ScheduleKeyboard:
    """Scheduling keyboards"""
    
    @staticmethod
    def get_schedule_options_keyboard() -> InlineKeyboardMarkup:
        """Get schedule options keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("⏰ Schedule Views", callback_data="schedule_views"),
            InlineKeyboardButton("📅 View Schedule", callback_data="view_schedule"),
            InlineKeyboardButton("🔄 Edit Schedule", callback_data="edit_schedule"),
            InlineKeyboardButton("❌ Cancel Schedule", callback_data="cancel_schedule"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
        )
        
        return keyboard
    
    @staticmethod
    def get_time_selection_keyboard() -> InlineKeyboardMarkup:
        """Get time selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=4)
        
        # Hours
        hours = []
        for hour in range(0, 24):
            hours.append(InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"hour_{hour}"))
        
        keyboard.row(*hours[:6])
        keyboard.row(*hours[6:12])
        keyboard.row(*hours[12:18])
        keyboard.row(*hours[18:])
        
        keyboard.add(
            InlineKeyboardButton("🔙 Back", callback_data="back_to_schedule"),
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_time")
        )
        
        return keyboard
    
    @staticmethod
    def get_duration_keyboard() -> InlineKeyboardMarkup:
        """Get duration selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        durations = [
            ("1 hour", "1h"),
            ("3 hours", "3h"),
            ("6 hours", "6h"),
            ("12 hours", "12h"),
            ("1 day", "1d"),
            ("3 days", "3d"),
            ("1 week", "7d"),
            ("2 weeks", "14d"),
            ("1 month", "30d")
        ]
        
        buttons = []
        for text, data in durations:
            buttons.append(InlineKeyboardButton(text, callback_data=f"duration_{data}"))
        
        for i in range(0, len(buttons), 3):
            keyboard.row(*buttons[i:i+3])
        
        keyboard.add(
            InlineKeyboardButton("🔙 Back", callback_data="back_to_time"),
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_duration")
        )
        
        return keyboard

class ReportKeyboard:
    """Report generation keyboards"""
    
    @staticmethod
    def get_report_type_keyboard() -> InlineKeyboardMarkup:
        """Get report type selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📅 Daily", callback_data="report_daily"),
            InlineKeyboardButton("📆 Weekly", callback_data="report_weekly"),
            InlineKeyboardButton("📊 Monthly", callback_data="report_monthly"),
            InlineKeyboardButton("📈 Custom", callback_data="report_custom"),
            InlineKeyboardButton("📋 Order Report", callback_data="report_orders"),
            InlineKeyboardButton("📊 Performance", callback_data="report_performance"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
        )
        
        return keyboard
    
    @staticmethod
    def get_report_format_keyboard() -> InlineKeyboardMarkup:
        """Get report format selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📄 HTML", callback_data="format_html"),
            InlineKeyboardButton("📊 PDF", callback_data="format_pdf"),
            InlineKeyboardButton("📋 CSV", callback_data="format_csv"),
            InlineKeyboardButton("📝 JSON", callback_data="format_json"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_report_type"),
            InlineKeyboardButton("✅ Generate", callback_data="generate_report")
        )
        
        return keyboard
    
    @staticmethod
    def get_custom_period_keyboard() -> InlineKeyboardMarkup:
        """Get custom period selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("Last 24 hours", callback_data="period_24h"),
            InlineKeyboardButton("Last 48 hours", callback_data="period_48h"),
            InlineKeyboardButton("Last 7 days", callback_data="period_7d"),
            InlineKeyboardButton("Last 30 days", callback_data="period_30d"),
            InlineKeyboardButton("Last 90 days", callback_data="period_90d"),
            InlineKeyboardButton("Custom Range", callback_data="period_custom"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_report_type")
        )
        
        return keyboard

class SettingsKeyboard:
    """Settings keyboards"""
    
    @staticmethod
    def get_language_keyboard() -> InlineKeyboardMarkup:
        """Get language selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        languages = [
            ("🇺🇸 English", "en"),
            ("🇪🇸 Spanish", "es"),
            ("🇷🇺 Russian", "ru"),
            ("🇫🇷 French", "fr"),
            ("🇩🇪 German", "de"),
            ("🇮🇹 Italian", "it"),
            ("🇵🇹 Portuguese", "pt"),
            ("🇸🇦 Arabic", "ar"),
            ("🇨🇳 Chinese", "zh")
        ]
        
        buttons = []
        for flag, code in languages:
            buttons.append(InlineKeyboardButton(flag, callback_data=f"lang_{code}"))
        
        for i in range(0, len(buttons), 3):
            keyboard.row(*buttons[i:i+3])
        
        keyboard.add(
            InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")
        )
        
        return keyboard
    
    @staticmethod
    def get_notification_keyboard() -> InlineKeyboardMarkup:
        """Get notification settings keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("🔔 All Notifications", callback_data="notify_all"),
            InlineKeyboardButton("📊 Order Updates", callback_data="notify_orders"),
            InlineKeyboardButton("💎 Promotions", callback_data="notify_promos"),
            InlineKeyboardButton("📈 System Alerts", callback_data="notify_system"),
            InlineKeyboardButton("❌ Disable All", callback_data="notify_none"),
            InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")
        )
        
        return keyboard
    
    @staticmethod
    def get_privacy_keyboard() -> InlineKeyboardMarkup:
        """Get privacy settings keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("👤 Public", callback_data="privacy_public"),
            InlineKeyboardButton("🔒 Private", callback_data="privacy_private"),
            InlineKeyboardButton("🛡️ Anonymous", callback_data="privacy_anon"),
            InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")
        )
        
        return keyboard

class SupportKeyboard:
    """Support keyboards"""
    
    @staticmethod
    def get_support_topics_keyboard() -> InlineKeyboardMarkup:
        """Get support topics keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("❓ General Help", callback_data="help_general"),
            InlineKeyboardButton("💰 Payments", callback_data="help_payments"),
            InlineKeyboardButton("📊 Orders", callback_data="help_orders"),
            InlineKeyboardButton("⚙️ Technical", callback_data="help_technical"),
            InlineKeyboardButton("🔄 Refunds", callback_data="help_refunds"),
            InlineKeyboardButton("📞 Contact", callback_data="help_contact"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
        )
        
        return keyboard
    
    @staticmethod
    def get_faq_keyboard() -> InlineKeyboardMarkup:
        """Get FAQ keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("🤔 How to use?", callback_data="faq_usage"),
            InlineKeyboardButton("💰 Pricing", callback_data="faq_pricing"),
            InlineKeyboardButton("⏱️ Delivery Time", callback_data="faq_delivery"),
            InlineKeyboardButton("🛡️ Safety", callback_data="faq_safety"),
            InlineKeyboardButton("📊 Success Rate", callback_data="faq_success"),
            InlineKeyboardButton("🔙 Back to Support", callback_data="back_to_support")
        )
        
        return keyboard

class AnalyticsKeyboard:
    """Analytics keyboards"""
    
    @staticmethod
    def get_analytics_dashboard_keyboard() -> InlineKeyboardMarkup:
        """Get analytics dashboard keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📈 Overview", callback_data="analytics_overview"),
            InlineKeyboardButton("📊 Performance", callback_data="analytics_performance"),
            InlineKeyboardButton("🎯 Success Rate", callback_data="analytics_success"),
            InlineKeyboardButton("⏱️ Speed", callback_data="analytics_speed"),
            InlineKeyboardButton("💰 Cost Analysis", callback_data="analytics_cost"),
            InlineKeyboardButton("📋 Export Data", callback_data="analytics_export"),
            InlineKeyboardButton("🔄 Refresh", callback_data="analytics_refresh"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
        )
        
        return keyboard
    
    @staticmethod
    def get_timeframe_keyboard() -> InlineKeyboardMarkup:
        """Get timeframe selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        timeframes = [
            ("Today", "today"),
            ("Yesterday", "yesterday"),
            ("Week", "week"),
            ("Month", "month"),
            ("Quarter", "quarter"),
            ("Year", "year"),
            ("All Time", "all"),
            ("Custom", "custom")
        ]
        
        buttons = []
        for text, data in timeframes:
            buttons.append(InlineKeyboardButton(text, callback_data=f"timeframe_{data}"))
        
        for i in range(0, len(buttons), 3):
            keyboard.row(*buttons[i:i+3])
        
        keyboard.add(
            InlineKeyboardButton("🔙 Back to Analytics", callback_data="back_to_analytics")
        )
        
        return keyboard

class QuickActionsKeyboard:
    """Quick action keyboards"""
    
    @staticmethod
    def get_quick_actions_keyboard() -> InlineKeyboardMarkup:
        """Get quick actions keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("🚀 Send 100 Views", callback_data="quick_100"),
            InlineKeyboardButton("📈 Send 500 Views", callback_data="quick_500"),
            InlineKeyboardButton("🏆 Send 1000 Views", callback_data="quick_1000"),
            InlineKeyboardButton("💰 Check Balance", callback_data="quick_balance"),
            InlineKeyboardButton("📊 View Stats", callback_data="quick_stats"),
            InlineKeyboardButton("📋 Recent Orders", callback_data="quick_orders"),
            InlineKeyboardButton("⚙️ Settings", callback_data="quick_settings"),
            InlineKeyboardButton("🆘 Help", callback_data="quick_help")
        )
        
        return keyboard
    
    @staticmethod
    def get_dashboard_keyboard() -> InlineKeyboardMarkup:
        """Get dashboard keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        keyboard.add(
            InlineKeyboardButton("📤 Send", callback_data="dashboard_send"),
            InlineKeyboardButton("💰 Balance", callback_data="dashboard_balance"),
            InlineKeyboardButton("📊 Stats", callback_data="dashboard_stats"),
            InlineKeyboardButton("📋 Orders", callback_data="dashboard_orders"),
            InlineKeyboardButton("⚙️ Settings", callback_data="dashboard_settings"),
            InlineKeyboardButton("🆘 Help", callback_data="dashboard_help"),
            InlineKeyboardButton("💎 Upgrade", callback_data="dashboard_upgrade"),
            InlineKeyboardButton("📈 Analytics", callback_data="dashboard_analytics"),
            InlineKeyboardButton("🔔 Notifications", callback_data="dashboard_notify")
        )
        
        return keyboard