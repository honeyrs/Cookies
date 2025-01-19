# Importing necessary libraries
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext

# Function to handle forwarded messages
async def handle_forward(update: Update, context: CallbackContext) -> None:
    # Extracting the message text
    message_text = update.message.text

    # Checking for specific RDP giveaway pattern in the forwarded message
    if "RDP GIVEWAY" in message_text:
        # Parsing and modifying the message with new password
        new_password = "newsecurepassword123!"  # Pre-selected new password
        updated_message = message_text.replace("worldgaming12345^", new_password)

        # Sending confirmation message
        await update.message.reply_text(
            f"Password has been updated!\n\nUpdated Details:\n{updated_message}"
        )
    else:
        await update.message.reply_text("No RDP details found in the message.")

# Main function to set up the bot
def main():
    # Telegram bot token (replace 'YOUR_BOT_TOKEN' with your actual bot token)
    bot_token = "7880602456:AAFbD_EtlNT1t2NhqFfdJBd6jifftMlIc_A"

    # Setting up the application
    application = Application.builder().token(bot_token).build()

    # Adding handler for forwarded messages
    application.add_handler(MessageHandler(filters.TEXT & filters.FORWARDED, handle_forward))

    # Starting the bot
    application.run_polling()

# Running the main function
if __name__ == "__main__":
    main()
