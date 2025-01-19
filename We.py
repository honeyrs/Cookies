# Import necessary modules
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

import subprocess

# Function to handle the /start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /change_ssh <username> <new_password> to change the SSH password.")

# Function to change SSH password
def change_ssh(update: Update, context: CallbackContext):
    # Parse the command arguments
    try:
        username = context.args[0]
        new_password = context.args[1]
    except IndexError:
        update.message.reply_text("Usage: /change_ssh <username> <new_password>")
        return

    try:
        # Execute the password change command
        command = f"echo '{username}:{new_password}' | sudo chpasswd"
        subprocess.run(command, shell=True, check=True)

        # Notify success
        update.message.reply_text("Password successfully changed!")
    except subprocess.CalledProcessError:
        # Notify error
        update.message.reply_text("Failed to change password. Ensure the username exists and you have sufficient permissions.")

# Main function to set up the bot
def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    bot_token = "7880602456:AAGajxDcV8BxyJHw0aGFmOurPbbkuM2OoHI"

    # Initialize the bot and updater
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("change_ssh", change_ssh))

    # Start the bot
    updater.start_polling()
    updater.idle()

# Run the main function
if __name__ == "__main__":
    main()
