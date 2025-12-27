"""
Admin Panel Keyboards for Telegram Bot
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class AdminKeyboard:
    """Admin panel keyboard generator"""
    
    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get admin main menu keyboard"""
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
        
        return keyboard
    
    @staticmethod
    def get_broadcast_keyboard() -> InlineKeyboardMarkup:
        """Get broadcast confirmation keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("✅ Send to All Users", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel"),
            InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")
        )
        
        return keyboard
    
    @staticmethod
    def get_users_keyboard() -> InlineKeyboardMarkup:
        """Get users management keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📋 Recent Users", callback_data="users_recent:10"),
            InlineKeyboardButton("⚡ Active Users", callback_data="users_active"),
            InlineKeyboardButton("💎 Premium Users", callback_data="users_premium"),
            InlineKeyboardButton("📊 Statistics", callback_data="users_stats"),
            InlineKeyboardButton("📄 Export CSV", callback_data="users_export"),
            InlineKeyboardButton("🔄 Refresh", callback_data="users_refresh"),
            InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")
        )
        
        return keyboard
    
    @staticmethod
    def get_inactive_users_keyboard(days: int) -> InlineKeyboardMarkup:
        """Get inactive users keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton(f"📧 Send Reminder ({days} days)", callback_data=f"inactive_reminder:{days}"),
            InlineKeyboardButton(f"🗑️ Cleanup ({days} days)", callback_data=f"inactive_cleanup:{days}"),
            InlineKeyboardButton("🔙 Back to Users", callback_data="admin_users")
        )
        
        return keyboard
    
    @staticmethod
    def get_system_keyboard() -> InlineKeyboardMarkup:
        """Get system management keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📊 Detailed Metrics", callback_data="system_metrics"),
            InlineKeyboardButton("🔍 Health Check", callback_data="system_health"),
            InlineKeyboardButton("💾 Backup Now", callback_data="system_backup"),
            InlineKeyboardButton("🔄 Restart Bot", callback_data="system_restart"),
            InlineKeyboardButton("🗑️ Clean Cache", callback_data="system_clean"),
            InlineKeyboardButton("📋 Logs", callback_data="system_logs"),
            InlineKeyboardButton("🔄 Refresh", callback_data="system_refresh"),
            InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")
        )
        
        return keyboard
    
    @staticmethod
    def get_logs_keyboard(limit: int = 100) -> InlineKeyboardMarkup:
        """Get logs management keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📄 Full Logs", callback_data=f"logs_full:{limit}"),
            InlineKeyboardButton("🚨 Errors Only", callback_data=f"logs_errors:{limit}"),
            InlineKeyboardButton("💾 Export", callback_data=f"logs_export:{limit}"),
            InlineKeyboardButton("🗑️ Clear Logs", callback_data="logs_clear"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"logs_refresh:{limit}"),
            InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")
        )
        
        return keyboard
    
    @staticmethod
    def get_user_actions_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """Get user actions keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📨 Message User", callback_data=f"user_message:{user_id}"),
            InlineKeyboardButton("💎 Change Plan", callback_data=f"user_plan:{user_id}"),
            InlineKeyboardButton("➕ Add Credits", callback_data=f"user_add:{user_id}"),
            InlineKeyboardButton("➖ Remove Credits", callback_data=f"user_remove:{user_id}"),
            InlineKeyboardButton("✅ Activate", callback_data=f"user_activate:{user_id}"),
            InlineKeyboardButton("❌ Deactivate", callback_data=f"user_deactivate:{user_id}"),
            InlineKeyboardButton("🔙 Back to Users", callback_data="admin_users")
        )
        
        return keyboard
    
    @staticmethod
    def get_plan_selection_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """Get plan selection keyboard for user"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("Free", callback_data=f"set_plan:{user_id}:free"),
            InlineKeyboardButton("Basic", callback_data=f"set_plan:{user_id}:basic"),
            InlineKeyboardButton("Pro", callback_data=f"set_plan:{user_id}:pro"),
            InlineKeyboardButton("Enterprise", callback_data=f"set_plan:{user_id}:enterprise"),
            InlineKeyboardButton("🔙 Back", callback_data=f"user_actions:{user_id}")
        )
        
        return keyboard
    
    @staticmethod
    def get_credit_amount_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """Get credit amount selection keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        keyboard.add(
            InlineKeyboardButton("+100", callback_data=f"add_credits:{user_id}:100"),
            InlineKeyboardButton("+500", callback_data=f"add_credits:{user_id}:500"),
            InlineKeyboardButton("+1000", callback_data=f"add_credits:{user_id}:1000"),
            InlineKeyboardButton("+5000", callback_data=f"add_credits:{user_id}:5000"),
            InlineKeyboardButton("+10000", callback_data=f"add_credits:{user_id}:10000"),
            InlineKeyboardButton("Custom", callback_data=f"add_credits_custom:{user_id}"),
            InlineKeyboardButton("🔙 Back", callback_data=f"user_actions:{user_id}")
        )
        
        return keyboard
    
    @staticmethod
    def get_backup_keyboard() -> InlineKeyboardMarkup:
        """Get backup options keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("💾 Database", callback_data="backup_db"),
            InlineKeyboardButton("📁 Logs", callback_data="backup_logs"),
            InlineKeyboardButton("📄 Config", callback_data="backup_config"),
            InlineKeyboardButton("📦 Full Backup", callback_data="backup_full"),
            InlineKeyboardButton("🔙 Back to System", callback_data="admin_system")
        )
        
        return keyboard
    
    @staticmethod
    def get_restart_confirmation_keyboard() -> InlineKeyboardMarkup:
        """Get restart confirmation keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("✅ Confirm Restart", callback_data="restart_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="restart_cancel"),
            InlineKeyboardButton("🔙 Back to System", callback_data="admin_system")
        )
        
        return keyboard
    
    @staticmethod
    def get_cleanup_keyboard() -> InlineKeyboardMarkup:
        """Get cleanup options keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("🗑️ Old Logs", callback_data="clean_logs"),
            InlineKeyboardButton("🧹 Temp Files", callback_data="clean_temp"),
            InlineKeyboardButton("🗄️ Cache", callback_data="clean_cache"),
            InlineKeyboardButton("📊 Old Stats", callback_data="clean_stats"),
            InlineKeyboardButton("🧽 Full Cleanup", callback_data="clean_full"),
            InlineKeyboardButton("🔙 Back to System", callback_data="admin_system")
        )
        
        return keyboard
    
    @staticmethod
    def get_stats_filter_keyboard() -> InlineKeyboardMarkup:
        """Get stats filter keyboard"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton("📅 Today", callback_data="stats_today"),
            InlineKeyboardButton("📆 Yesterday", callback_data="stats_yesterday"),
            InlineKeyboardButton("📈 Last 7 Days", callback_data="stats_week"),
            InlineKeyboardButton("📊 Last 30 Days", callback_data="stats_month"),
            InlineKeyboardButton("📋 All Time", callback_data="stats_all"),
            InlineKeyboardButton("📄 Export", callback_data="stats_export"),
            InlineKeyboardButton("🔄 Refresh", callback_data="stats_refresh"),
            InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")
        )
        
        return keyboard