# Importing necessary libraries
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
import re

# Global variables for setting password and type
new_password = "newsecurepassword123!"  # Pre-selected new password
service_type = "rdp"  # Default service type

# Function to handle forwarded messages
async def handle_forward(update: Update, context: CallbackContext) -> None:
    # Extracting the message text
    message_text = update.message.text

    # Checking for specific RDP giveaway pattern in the forwarded message
    if "RDP GIVEWAY" in message_text or "SSH GIVEWAY" in message_text:
        # Verifying and modifying the message with new password and service type
        if service_type == "rdp":
            updated_message = modify_message(message_text, "worldgaming12345^", new_password)
        else:
            updated_message = modify_message(message_text, "worldgaming12345^", new_password)

        # Sending confirmation message
        await update.message.reply_text(
            f"Password has been updated for {service_type}!\n\nUpdated Details:\n{updated_message}"
        )
    else:
        await update.message.reply_text("No valid RDP or SSH details found in the message.")

# Function to modify the message with new password
def modify_message(message_text: str, old_password: str, new_password: str) -> str:
    # Replace old password with the new password
    return message_text.replace(old_password, new_password)

# Function to set password and type
async def set_password(update: Update, context: CallbackContext) -> None:
    global new_password, service_type

    # Checking if both arguments are provided
    if len(context.args) == 2:
        service_type = context.args[0].lower()  # 'rdp' or 'ssh'
        new_password = context.args[1]  # New password to set

        # Confirming the change of password and service type
        await update.message.reply_text(
            f"Password for {service_type} has been set to {new_password}."
        )
    else:
        await update.message.reply_text(
            "Usage: /setpassword <service_type> <new_password>\nExample: /setpassword rdp mynewpassword"
        )

# Main function to set up the bot
def main():
    # Telegram bot token (replace 'YOUR_BOT_TOKEN' with your actual bot token)
    bot_token = "7880602456:AAFbD_EtlNT1t2NhqFfdJBd6jifftMlIc_A"

    # Setting up the application
    application = Application.builder().token(bot_token).build()

    # Adding handler for forwarded messages
    application.add_handler(MessageHandler(filters.TEXT & filters.FORWARDED, handle_forward))

    # Adding handler for setting password and service type
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^/setpassword'), set_password))

    # Starting the bot
    application.run_polling()

# Running the main function
if __name__ == "__main__":
    main()
