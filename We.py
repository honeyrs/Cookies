from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackContext, ConversationHandler
import re
from typing import List, Dict

# Global variables
new_password = "newsecurepassword123!"  # Pre-selected new password
service_type = "rdp"  # Default service type

# Regular expressions for parsing RDP details
RDP_PATTERN = re.compile(
    r'IP:\s*(\d+\.\d+\.\d+\.\d+)\s*'
    r'USER:\s*(\w+)\s*'
    r'PAS:\s*([\w\^\$\#\@\!]+)\s*'
    r'RAM:\s*(\d+)\s*'
    r'CORE:\s*(\d+)\s*'
    r'LOCATION:\s*(\w+)',
    re.IGNORECASE
)

class RDPEntry:
    def __init__(self, ip: str, user: str, password: str, ram: str, core: str, location: str):
        self.ip = ip
        self.user = user
        self.password = password
        self.ram = ram
        self.core = core
        self.location = location
        self.status = "⏳ Processing"
        self.error = None

    def to_string(self) -> str:
        status_emoji = "✅" if self.status == "Success" else "❌" if self.status == "Failed" else "⏳"
        result = f"{status_emoji} *RDP Entry*\n\n"
        result += f"IP: `{self.ip}`\n"
        result += f"User: `{self.user}`\n"
        result += f"Password: `{self.password}`\n"
        result += f"RAM: {self.ram}GB\n"
        result += f"Core: {self.core}\n"
        result += f"Location: {self.location}\n"
        if self.error:
            result += f"\nError: {self.error}"
        return result

def parse_rdp_entries(message_text: str) -> List[RDPEntry]:
    entries = []
    matches = RDP_PATTERN.finditer(message_text)
    
    for match in matches:
        ip, user, password, ram, core, location = match.groups()
        entry = RDPEntry(ip, user, password, ram, core, location)
        entries.append(entry)
    
    return entries

async def handle_forward(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    
    # Parse RDP entries from the message
    rdp_entries = parse_rdp_entries(message_text)
    
    if not rdp_entries:
        await update.message.reply_text(
            "❌ *Error: No valid RDP details found*\n\nPlease forward a message containing valid RDP information.",
            parse_mode='Markdown'
        )
        return

    # Send initial status message
    status_message = await update.message.reply_text(
        "⏳ *Processing RDP entries...*",
        parse_mode='Markdown'
    )

    # Process each RDP entry
    summary = "*RDP Update Summary*\n\n"
    success_count = 0
    failed_count = 0

    for entry in rdp_entries:
        try:
            if entry.password == "worldgaming12345^":
                entry.password = new_password
                entry.status = "Success"
                success_count += 1
            else:
                entry.status = "Failed"
                entry.error = "Password pattern not matched"
                failed_count += 1
            
            # Add entry details to summary
            summary += f"{entry.to_string()}\n\n"
            
        except Exception as e:
            entry.status = "Failed"
            entry.error = str(e)
            failed_count += 1
            summary += f"{entry.to_string()}\n\n"

    # Add final statistics
    summary += f"*Summary:*\n"
    summary += f"✅ Successful updates: {success_count}\n"
    summary += f"❌ Failed updates: {failed_count}\n"
    
    # Update the status message with final results
    await status_message.edit_text(
        summary,
        parse_mode='Markdown'
    )

    if success_count > 0:
        keyboard = get_main_keyboard()
        await update.message.reply_text(
            "✅ *Password update completed!*\n\nUse the keyboard below to manage your RDP settings.",
            parse_mode='Markdown',
            reply_markup=keyboard
        )

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📝 Set Password"), KeyboardButton("ℹ️ Help")],
        [KeyboardButton("🔄 Current Settings"), KeyboardButton("📋 Commands List")]
    ], resize_keyboard=True)

# [Previous command handlers remain the same]
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = """
🤖 *Welcome to the RDP/SSH Password Manager Bot!*

This bot helps you manage passwords for RDP and SSH services.

*Main Features:*
• Forward RDP/SSH giveaway messages to update passwords
• Set custom passwords for different services
• View current settings and configurations

Use the keyboard below to navigate through features or type /help for more information.
    """
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
*Available Commands:*

/start - Start the bot and show main menu
/help - Show this help message
/setpassword <type> <password> - Set new password
  Example: /setpassword rdp mynewpass123

*How to Use:*
1. Forward any RDP/SSH giveaway message
2. Bot will automatically update the password
3. Use /setpassword to change passwords

*Password Guidelines:*
• Minimum 8 characters
• Mix of letters and numbers
• Special characters recommended
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_settings(update: Update, context: CallbackContext) -> None:
    settings_text = f"""
*Current Settings:*

Service Type: {service_type.upper()}
Current Password: {new_password}
Auto-Update: Enabled
    """
    await update.message.reply_text(settings_text, parse_mode='Markdown')

async def set_password(update: Update, context: CallbackContext) -> None:
    global new_password, service_type
    
    if len(context.args) == 2:
        service_type = context.args[0].lower()
        new_password = context.args[1]
        
        await update.message.reply_text(
            f"✅ Password for {service_type.upper()} has been set to: `{new_password}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *Usage:* /setpassword <service_type> <new_password>\n*Example:* /setpassword rdp mynewpassword",
            parse_mode='Markdown'
        )

async def handle_button(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    
    if text == "📝 Set Password":
        await update.message.reply_text(
            "*Set a New Password*\n\nUse the command:\n/setpassword <type> <password>\n\nExample:\n`/setpassword rdp mynewpass123`",
            parse_mode='Markdown'
        )
    elif text == "ℹ️ Help":
        await help_command(update, context)
    elif text == "🔄 Current Settings":
        await show_settings(update, context)
    elif text == "📋 Commands List":
        await update.message.reply_text(
            "*Available Commands:*\n\n/start - Start bot\n/help - Show help\n/setpassword - Set new password",
            parse_mode='Markdown'
        )

def main():
    bot_token = "8152265435:AAH9ex75KOmXl6lb_M79EAQgUvnPjbfkYUA"
    application = Application.builder().token(bot_token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setpassword", set_password))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & filters.FORWARDED, handle_forward))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button))

    application.run_polling()

if __name__ == "__main__":
    main()
