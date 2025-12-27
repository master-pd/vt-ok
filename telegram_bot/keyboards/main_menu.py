"""
Main Menu Keyboards for Telegram Bot
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

class MainKeyboard:
    """Main menu keyboard generator"""
    
    @staticmethod
    def get_start_keyboard() -> InlineKeyboardMarkup:
        """Get start menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("🚀 Send Views", callback_data="quick_send"),
            InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
            InlineKeyboardButton("💎 Upgrade", callback_data="upgrade"),
            InlineKeyboardButton("🆘 Help", callback_data="help"),
            InlineKeyboardButton("⚙️ Settings", callback_data="setting_menu"),
            InlineKeyboardButton("📞 Support", callback_data="contact_support")
        )
        
        return keyboard
    
    @staticmethod
    def get_balance_keyboard() -> InlineKeyboardMarkup:
        """Get balance menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("💎 Upgrade Plan", callback_data="upgrade"),
            InlineKeyboardButton("📤 Send Views", callback_data="quick_send"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_balance"),
            InlineKeyboardButton("📊 View Stats", callback_data="my_stats")
        )
        
        return keyboard
    
    @staticmethod
    def get_stats_keyboard() -> InlineKeyboardMarkup:
        """Get stats menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📤 Send More", callback_data="quick_send"),
            InlineKeyboardButton("📋 Order History", callback_data="view_history"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
            InlineKeyboardButton("💎 Upgrade", callback_data="upgrade")
        )
        
        return keyboard
    
    @staticmethod
    def get_history_keyboard() -> InlineKeyboardMarkup:
        """Get history menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📤 New Order", callback_data="quick_send"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_history"),
            InlineKeyboardButton("📄 Export", callback_data="export_history"),
            InlineKeyboardButton("📊 Stats", callback_data="my_stats")
        )
        
        return keyboard
    
    @staticmethod
    def get_status_keyboard(order_id: str = None) -> InlineKeyboardMarkup:
        """Get status menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        if order_id:
            keyboard.add(
                InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_status:{order_id}"),
                InlineKeyboardButton("📋 All Orders", callback_data="view_history")
            )
        else:
            keyboard.add(
                InlineKeyboardButton("🔄 Refresh All", callback_data="refresh_all_status"),
                InlineKeyboardButton("📤 New Order", callback_data="quick_send")
            )
        
        keyboard.add(
            InlineKeyboardButton("📊 Stats", callback_data="my_stats"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        
        return keyboard
    
    @staticmethod
    def get_subscribe_keyboard(current_plan: str) -> InlineKeyboardMarkup:
        """Get subscribe menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Only show upgrade buttons for plans lower than current
        plans = ['basic', 'pro', 'enterprise']
        current_index = plans.index(current_plan) if current_plan in plans else -1
        
        for i, plan in enumerate(plans):
            if i > current_index:
                plan_name = plan.title()
                price = {
                    'basic': '$9.99',
                    'pro': '$29.99',
                    'enterprise': '$99.99'
                }.get(plan, '')
                
                keyboard.insert(
                    InlineKeyboardButton(
                        f"{plan_name} - {price}",
                        callback_data=f"upgrade_to:{plan}"
                    )
                )
        
        keyboard.add(
            InlineKeyboardButton("📞 Contact Support", callback_data="contact_support"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_subscribe"),
            InlineKeyboardButton("💰 Check Balance", callback_data="refresh_balance")
        )
        
        return keyboard
    
    @staticmethod
    def get_methods_keyboard() -> InlineKeyboardMarkup:
        """Get methods menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("🚀 Send Views", callback_data="quick_send"),
            InlineKeyboardButton("💎 Upgrade Plan", callback_data="upgrade"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_methods"),
            InlineKeyboardButton("📊 View Stats", callback_data="my_stats")
        )
        
        return keyboard
    
    @staticmethod
    def get_settings_keyboard() -> InlineKeyboardMarkup:
        """Get settings menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("🌐 Language", callback_data="setting_language"),
            InlineKeyboardButton("🔔 Notifications", callback_data="setting_notifications"),
            InlineKeyboardButton("🔄 Auto-Update", callback_data="setting_autoupdate"),
            InlineKeyboardButton("👤 Privacy", callback_data="setting_privacy"),
            InlineKeyboardButton("📊 Reports", callback_data="setting_reports"),
            InlineKeyboardButton("⚡ Performance", callback_data="setting_performance"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"),
            InlineKeyboardButton("💾 Save", callback_data="setting_save")
        )
        
        return keyboard
    
    @staticmethod
    def get_support_keyboard() -> InlineKeyboardMarkup:
        """Get support menu keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📞 Contact Now", url="https://t.me/vtultrapro_support"),
            InlineKeyboardButton("🌐 Visit Website", url="https://vtultrapro.com"),
            InlineKeyboardButton("📚 Documentation", callback_data="docs"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        
        return keyboard
    
    @staticmethod
    def get_send_views_keyboard() -> InlineKeyboardMarkup:
        """Get send views selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        keyboard.add(
            InlineKeyboardButton("100 views", callback_data="send_100"),
            InlineKeyboardButton("500 views", callback_data="send_500"),
            InlineKeyboardButton("1000 views", callback_data="send_1000"),
            InlineKeyboardButton("Custom", callback_data="send_custom"),
            InlineKeyboardButton("Cancel", callback_data="send_cancel")
        )
        
        return keyboard
    
    @staticmethod
    def get_quick_send_keyboard() -> InlineKeyboardMarkup:
        """Get quick send keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("100", callback_data="confirm_views:100"),
            InlineKeyboardButton("500", callback_data="confirm_views:500"),
            InlineKeyboardButton("1000", callback_data="confirm_views:1000"),
            InlineKeyboardButton("Custom", callback_data="custom_views"),
            InlineKeyboardButton("Cancel", callback_data="cancel_send"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        )
        
        return keyboard
    
    @staticmethod
    def get_main_menu_reply() -> ReplyKeyboardMarkup:
        """Get main menu reply keyboard"""
        keyboard = ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=False,
            row_width=2
        )
        
        keyboard.add(
            KeyboardButton("🚀 Send Views"),
            KeyboardButton("💰 Balance"),
            KeyboardButton("📊 Stats"),
            KeyboardButton("📋 History"),
            KeyboardButton("⚙️ Settings"),
            KeyboardButton("🆘 Help")
        )
        
        return keyboard
    
    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """Get cancel keyboard"""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
        return keyboard
    
    @staticmethod
    def get_back_keyboard() -> InlineKeyboardMarkup:
        """Get back keyboard"""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="go_back"))
        return keyboard
    
    @staticmethod
    def get_confirmation_keyboard() -> InlineKeyboardMarkup:
        """Get confirmation keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_action"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")
        )
        return keyboard