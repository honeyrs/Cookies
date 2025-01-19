from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackContext, ConversationHandler
import re

# Global variables
new_password = "newsecurepassword123!"  # Pre-selected new password
service_type = "rdp"  # Default service type

# Keyboard layouts
def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📝 Set Password"), KeyboardButton("ℹ️ Help")],
        [KeyboardButton("🔄 Current Settings"), KeyboardButton("📋 Commands List")]
    ], resize_keyboard=True)

async def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command"""
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
    """Handle the /help command"""
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
    """Show current bot settings"""
    settings_text = f"""
*Current Settings:*

Service Type: {service_type.upper()}
Current Password: {new_password}
Auto-Update: Enabled
    """
    await update.message.reply_text(settings_text, parse_mode='Markdown')

async def handle_forward(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text

    if "RDP GIVEWAY" in message_text or "SSH GIVEWAY" in message_text:
        updated_message = modify_message(message_text, "worldgaming12345^", new_password)
        await update.message.reply_text(
            f"✅ Password has been updated for {service_type}!\n\n*Updated Details:*\n{updated_message}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ No valid RDP or SSH details found in the message.")

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

def modify_message(message_text: str, old_password: str, new_password: str) -> str:
    return message_text.replace(old_password, new_password)

async def handle_button(update: Update, context: CallbackContext) -> None:
    """Handle keyboard button presses"""
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
