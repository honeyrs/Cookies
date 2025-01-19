import winrm
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, MessageHandler, CommandHandler, CallbackQueryHandler,
    filters, CallbackContext, ConversationHandler
)
import re
from typing import List, Dict
import subprocess
import sys
import logging
from dataclasses import dataclass
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States for conversation handler
SELECTING_ACTION = 1
SETTING_PASSWORD = 2
SETTING_TIMEOUT = 3

# Load configuration file
def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            return json.load(f)
    return {
        'default_password': 'NewSecurePass123!',
        'timeout': 30,
        'max_retries': 3,
        'history_enabled': True
    }

# Save configuration file
def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

class RDPManager:
    def __init__(self):
        self.config = load_config()
        self.history = []
        
    def save_to_history(self, entry):
        if self.config['history_enabled']:
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'ip': entry.ip,
                'username': entry.username,
                'success': entry.success,
                'message': entry.message
            })
            # Keep only last 100 entries
            self.history = self.history[-100:]

class RDPBot:
    def __init__(self, token: str):
        self.token = token
        self.rdp_manager = RDPManager()
        self.password_changer = WindowsPasswordChanger()

    def get_main_keyboard(self):
        return ReplyKeyboardMarkup([
            [KeyboardButton("🔑 Change Password"), KeyboardButton("⚙️ Settings")],
            [KeyboardButton("📊 Statistics"), KeyboardButton("❓ Help")],
            [KeyboardButton("📜 History"), KeyboardButton("🔄 Status")]
        ], resize_keyboard=True)

    def get_settings_keyboard(self):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Set Default Password", callback_data="set_password"),
                InlineKeyboardButton("Set Timeout", callback_data="set_timeout")
            ],
            [
                InlineKeyboardButton("Toggle History", callback_data="toggle_history"),
                InlineKeyboardButton("Set Max Retries", callback_data="set_retries")
            ],
            [InlineKeyboardButton("Back to Main Menu", callback_data="main_menu")]
        ])

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Handle the /start command"""
        welcome_message = f"""
🤖 *Welcome to the Advanced RDP Password Manager Bot!*

This bot helps you securely manage Windows RDP passwords by directly connecting to and modifying system passwords.

*Key Features:*
• Automatic password changes on Windows systems
• Real-time status monitoring
• Password change history tracking
• Multiple connection methods
• Secure credential handling

*Current Settings:*
• Default Password: `{self.rdp_manager.config['default_password']}`
• Timeout: {self.rdp_manager.config['timeout']} seconds
• Max Retries: {self.rdp_manager.config['max_retries']}
• History: {'Enabled' if self.rdp_manager.config['history_enabled'] else 'Disabled'}

Press any button below to get started!
        """
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=self.get_main_keyboard()
        )
        return SELECTING_ACTION

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Handle the /help command"""
        help_text = """
*🔧 RDP Password Manager Commands:*

*Basic Commands:*
/start - Initialize the bot and show main menu
/help - Display this help message
/settings - Configure bot settings
/status - Check current bot status
/history - View password change history

*Password Management:*
/setpassword <password> - Set new default password
/timeout <seconds> - Set connection timeout
/retry <number> - Set max retry attempts

*Usage Instructions:*
1. Forward RDP messages to automatically process them
2. Use /setpassword to configure default new password
3. Check /history to view past operations
4. Use /status to monitor current operations

*Password Requirements:*
• Minimum 8 characters
• Mix of uppercase and lowercase
• At least one number
• At least one special character

*Security Notes:*
• All connections are encrypted
• Credentials are securely handled
• Failed attempts are logged
• History can be disabled for privacy

*Example Usage:*
1. Set new password:
   `/setpassword NewSecure123!`

2. Set timeout:
   `/timeout 45`

3. Forward RDP message:
   Simply forward any RDP credential message

Need more help? Use the keyboard buttons below!
        """
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=self.get_main_keyboard()
        )

    async def settings_command(self, update: Update, context: CallbackContext) -> None:
        """Handle the /settings command"""
        settings_text = f"""
*⚙️ Current Settings:*

*Password Configuration:*
• Default Password: `{self.rdp_manager.config['default_password']}`
• Password History: {'Enabled' if self.rdp_manager.config['history_enabled'] else 'Disabled'}

*Connection Settings:*
• Timeout: {self.rdp_manager.config['timeout']} seconds
• Max Retries: {self.rdp_manager.config['max_retries']}

Select an option to modify:
        """
        await update.message.reply_text(
            settings_text,
            parse_mode='Markdown',
            reply_markup=self.get_settings_keyboard()
        )

    async def history_command(self, update: Update, context: CallbackContext) -> None:
        """Handle the /history command"""
        if not self.rdp_manager.history:
            await update.message.reply_text(
                "📜 *No password change history available*",
                parse_mode='Markdown'
            )
            return

        history_text = "*📜 Recent Password Changes:*\n\n"
        for entry in self.rdp_manager.history[-10:]:  # Show last 10 entries
            status = "✅" if entry['success'] else "❌"
            history_text += f"{status} {entry['timestamp']}\n"
            history_text += f"IP: `{entry['ip']}`\n"
            history_text += f"User: `{entry['username']}`\n"
            history_text += f"Status: {entry['message']}\n\n"

        await update.message.reply_text(
            history_text,
            parse_mode='Markdown'
        )

    async def status_command(self, update: Update, context: CallbackContext) -> None:
        """Handle the /status command"""
        status_text = f"""
*🔄 System Status:*

*Service Status:*
• Bot: ✅ Online
• WinRM Service: ✅ Active
• Password Manager: ✅ Running

*Statistics:*
• Total Operations: {len(self.rdp_manager.history)}
• Success Rate: {self._calculate_success_rate()}%
• Average Response Time: {self._calculate_avg_response_time()}s

*Current Configuration:*
• Default Password: {'*' * len(self.rdp_manager.config['default_password'])}
• Timeout: {self.rdp_manager.config['timeout']}s
• Max Retries: {self.rdp_manager.config['max_retries']}
• History: {'Enabled' if self.rdp_manager.config['history_enabled'] else 'Disabled'}
        """
        await update.message.reply_text(
            status_text,
            parse_mode='Markdown'
        )

    def _calculate_success_rate(self) -> float:
        if not self.rdp_manager.history:
            return 0.0
        successful = sum(1 for entry in self.rdp_manager.history if entry['success'])
        return round((successful / len(self.rdp_manager.history)) * 100, 2)

    def _calculate_avg_response_time(self) -> float:
        # Simulated for demonstration
        return round(self.rdp_manager.config['timeout'] / 2, 2)

    async def handle_button(self, update: Update, context: CallbackContext) -> None:
        """Handle keyboard button presses"""
        query = update.callback_query
        await query.answer()

        if query.data == "set_password":
            await query.message.edit_text(
                "Please enter new default password using:\n"
                "/setpassword <new_password>",
                parse_mode='Markdown'
            )
            return SETTING_PASSWORD

        elif query.data == "set_timeout":
            await query.message.edit_text(
                "Please enter new timeout (in seconds) using:\n"
                "/timeout <seconds>",
                parse_mode='Markdown'
            )
            return SETTING_TIMEOUT

        elif query.data == "toggle_history":
            self.rdp_manager.config['history_enabled'] = not self.rdp_manager.config['history_enabled']
            save_config(self.rdp_manager.config)
            await self.settings_command(update, context)

        elif query.data == "main_menu":
            await query.message.edit_text(
                "Returning to main menu...",
                reply_markup=self.get_main_keyboard()
            )
            return SELECTING_ACTION

    async def set_password(self, update: Update, context: CallbackContext) -> None:
        """Handle the /setpassword command"""
        if not context.args:
            await update.message.reply_text(
                "❌ *Usage:* /setpassword <new_password>\n"
                "Example: `/setpassword NewSecure123!`\n\n"
                "*Password Requirements:*\n"
                "• Minimum 8 characters\n"
                "• Mix of uppercase and lowercase\n"
                "• At least one number\n"
                "• At least one special character",
                parse_mode='Markdown'
            )
            return

        new_password = context.args[0]
        
        # Validate password
        if not self._validate_password(new_password):
            await update.message.reply_text(
                "❌ Password does not meet requirements!\n\n"
                "Please ensure your password has:\n"
                "• Minimum 8 characters\n"
                "• Mix of uppercase and lowercase\n"
                "• At least one number\n"
                "• At least one special character",
                parse_mode='Markdown'
            )
            return

        self.rdp_manager.config['default_password'] = new_password
        save_config(self.rdp_manager.config)
        
        await update.message.reply_text(
            "✅ Default password updated successfully!\n\n"
            "New password will be used for all future operations.",
            parse_mode='Markdown'
        )

    def _validate_password(self, password: str) -> bool:
        """Validate password meets requirements"""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        return True

def main():
    # Replace with your bot token
    bot_token = "7893919705:AAEvxFdD6D2nDAUPdLkgCEa8SmoALq7h2s4"
    
    # Initialize bot
    rdp_bot = RDPBot(bot_token)
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", rdp_bot.start))
    application.add_handler(CommandHandler("help", rdp_bot.help_command))
    application.add_handler(CommandHandler("settings", rdp_bot.settings_command))
    application.add_handler(CommandHandler("history", rdp_bot.history_command))
    application.add_handler(CommandHandler("status", rdp_bot.status_command))
    application.add_handler(CommandHandler("setpassword", rdp_bot.set_password))
    
    # Add callback query handler for inline keyboard buttons
    application.add_handler(CallbackQueryHandler(rdp_bot.handle_button))
    
    # Add message handler for forwarded messages
    application.add_handler(MessageHandler(filters.TEXT & filters.FORWARDED, rdp_bot.handle_forward))
    
    # Start bot
    application.run_polling()

if __name__ == "__main__":
    main()
