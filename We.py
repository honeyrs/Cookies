# Import necessary modules from the python-telegram-bot library
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import subprocess

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reply with a welcome message and instructions
    await update.message.reply_text("Welcome! Use /change_ssh <username> <new_password> to change the SSH password.")

# Function to change SSH password
async def change_ssh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Parse the command arguments
    if len(context.args) < 2:
        # If not enough arguments are provided, send usage instructions
        await update.message.reply_text("Usage: /change_ssh <username> <new_password>")
        return

    # Extract username and new_password from the arguments
    username = context.args[0]
    new_password = context.args[1]

    try:
        # Construct the shell command to change the password
        command = f"echo '{username}:{new_password}' | sudo chpasswd"

        # Run the command securely
        subprocess.run(command, shell=True, check=True)

        # Notify the user of success
        await update.message.reply_text("Password successfully changed!")
    except subprocess.CalledProcessError:
        # If the command fails, notify the user
        await update.message.reply_text("Failed to change password. Ensure the username exists and you have sufficient permissions.")
    except Exception as e:
        # Catch any other unexpected errors and notify the user
        await update.message.reply_text(f"An unexpected error occurred: {str(e)}")

# Main function to set up the bot
def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    bot_token = "7880602456:AAGajxDcV8BxyJHw0aGFmOurPbbkuM2OoHI"

    # Create an application instance
    application = Application.builder().token(bot_token).build()

    # Add command handlers for /start and /change_ssh
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change_ssh", change_ssh))

    # Run the bot until manually stopped
    application.run_polling()

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
