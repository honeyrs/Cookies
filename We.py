# Import necessary modules from the python-telegram-bot library
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import paramiko

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reply with a welcome message and instructions
    await update.message.reply_text(
        "Welcome! Use /login_ssh <host> <username> <password> to log in and change the SSH password."
    )

# Function to log in to SSH and change the password
async def login_ssh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Parse the command arguments
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /login_ssh <host> <username> <password>"
        )
        return

    host = context.args[0]
    username = context.args[1]
    password = context.args[2]

    try:
        # Establish an SSH connection
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=host, username=username, password=password)

        # Notify the user of a successful login
        await update.message.reply_text("SSH login successful! Please send your new password using /set_password <new_password>.")

        # Store the SSH client and username in context for later use
        context.user_data["ssh_client"] = ssh_client
        context.user_data["username"] = username
    except paramiko.AuthenticationException:
        # Notify the user of failed authentication
        await update.message.reply_text("SSH login failed. Please check your credentials.")
    except Exception as e:
        # Catch any other errors and notify the user
        await update.message.reply_text(f"An unexpected error occurred: {str(e)}")

# Function to set a new SSH password
async def set_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user has logged in
    if "ssh_client" not in context.user_data or "username" not in context.user_data:
        await update.message.reply_text("You must log in first using /login_ssh.")
        return

    # Parse the new password
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /set_password <new_password>")
        return

    new_password = context.args[0]
    ssh_client = context.user_data["ssh_client"]
    username = context.user_data["username"]

    try:
        # Change the password on the SSH server
        command = f"echo '{username}:{new_password}' | sudo chpasswd"
        stdin, stdout, stderr = ssh_client.exec_command(command)

        # Check for errors in command execution
        error_output = stderr.read().decode().strip()
        if error_output:
            raise Exception(error_output)

        # Notify the user of a successful password change
        await update.message.reply_text("Password successfully changed!")
    except Exception as e:
        # Notify the user of any errors
        await update.message.reply_text(f"Failed to change password: {str(e)}")
    finally:
        # Close the SSH connection
        ssh_client.close()
        context.user_data.clear()

# Main function to set up the bot
def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    bot_token = "7880602456:AAFbD_EtlNT1t2NhqFfdJBd6jifftMlIc_A"

    # Create an application instance
    application = Application.builder().token(bot_token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login_ssh", login_ssh))
    application.add_handler(CommandHandler("set_password", set_password))

    # Run the bot until manually stopped
    application.run_polling()

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
