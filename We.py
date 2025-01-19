import winrm
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackContext
import re
from typing import List, Dict
import subprocess
import sys
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RDPCredentials:
    ip: str
    username: str
    current_password: str
    new_password: str
    ram: str
    core: str
    location: str

class WindowsPasswordChanger:
    def __init__(self):
        self.timeout = 30  # Connection timeout in seconds

    async def change_password(self, creds: RDPCredentials) -> tuple[bool, str]:
        """
        Attempt to change Windows password using different methods
        Returns: (success: bool, message: str)
        """
        try:
            # First try WinRM
            session = winrm.Session(
                f'http://{creds.ip}:5985/wsman',
                auth=(creds.username, creds.current_password),
                transport='ntlm',
                server_cert_validation='ignore'
            )

            # PowerShell command to change password
            ps_script = f"""
            $securePassword = ConvertTo-SecureString "{creds.new_password}" -AsPlainText -Force
            $UserAccount = Get-LocalUser -Name "{creds.username}"
            $UserAccount | Set-LocalUser -Password $securePassword
            """
            
            result = session.run_ps(ps_script)

            if result.status_code == 0:
                return True, "Password changed successfully via WinRM"
            
            error_msg = result.std_err.decode('utf-8') if result.std_err else "Unknown WinRM error"
            raise Exception(error_msg)

        except Exception as winrm_error:
            logger.error(f"WinRM failed: {str(winrm_error)}")
            
            try:
                # Fallback to cmdkey/net use method
                return await self._change_password_via_cmdkey(creds)
            except Exception as cmdkey_error:
                logger.error(f"Cmdkey method failed: {str(cmdkey_error)}")
                return False, f"Failed to change password: {str(cmdkey_error)}"

    async def _change_password_via_cmdkey(self, creds: RDPCredentials) -> tuple[bool, str]:
        """Fallback method using cmdkey and net use commands"""
        
        # Clear existing credentials
        subprocess.run(['cmdkey', '/delete:TERMSRV/' + creds.ip])
        
        # Add new credentials
        subprocess.run([
            'cmdkey', '/generic:TERMSRV/' + creds.ip,
            '/user:' + creds.username,
            '/pass:' + creds.current_password
        ])
        
        # Connect to remote share to verify credentials
        net_use = subprocess.run([
            'net', 'use', f'\\\\{creds.ip}\\IPC$',
            '/user:' + creds.username,
            creds.current_password
        ], capture_output=True)
        
        if net_use.returncode != 0:
            raise Exception("Failed to verify credentials")

        # Use PowerShell to change password
        ps_command = f"""
        $password = ConvertTo-SecureString "{creds.new_password}" -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential("{creds.username}", $password)
        Invoke-Command -ComputerName {creds.ip} -Credential $credential -ScriptBlock {{
            Net User $env:USERNAME "{creds.new_password}"
        }}
        """
        
        ps_result = subprocess.run(['powershell', '-Command', ps_command], capture_output=True)
        
        # Cleanup
        subprocess.run(['net', 'use', f'\\\\{creds.ip}\\IPC$', '/delete'])
        subprocess.run(['cmdkey', '/delete:TERMSRV/' + creds.ip])
        
        if ps_result.returncode == 0:
            return True, "Password changed successfully via cmdkey method"
        else:
            raise Exception(ps_result.stderr.decode('utf-8'))

class RDPBot:
    def __init__(self, token: str):
        self.password_changer = WindowsPasswordChanger()
        self.token = token
        self.new_password = "NewSecurePass123!"  # Default new password

    async def handle_forward(self, update: Update, context: CallbackContext) -> None:
        message_text = update.message.text
        rdp_entries = self._parse_rdp_entries(message_text)
        
        if not rdp_entries:
            await update.message.reply_text(
                "❌ No valid RDP entries found in the message.",
                parse_mode='Markdown'
            )
            return

        status_message = await update.message.reply_text(
            "⏳ *Processing RDP entries...*\n\n"
            "Attempting to connect and change passwords. This may take a few minutes.",
            parse_mode='Markdown'
        )

        results = []
        for entry in rdp_entries:
            try:
                success, message = await self.password_changer.change_password(entry)
                
                status = "✅" if success else "❌"
                result = f"{status} RDP: {entry.ip}\n"
                result += f"User: {entry.username}\n"
                result += f"Status: {message}\n"
                if success:
                    result += f"New Password: {entry.new_password}\n"
                results.append(result)
                
                # Update status message
                await status_message.edit_text(
                    "*RDP Password Change Progress:*\n\n" + "\n\n".join(results),
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                results.append(f"❌ Error with {entry.ip}: {str(e)}")
                await status_message.edit_text(
                    "*RDP Password Change Progress:*\n\n" + "\n\n".join(results),
                    parse_mode='Markdown'
                )

        # Final summary
        success_count = sum(1 for r in results if "✅" in r)
        await update.message.reply_text(
            f"*Password Change Complete*\n\n"
            f"✅ Successful: {success_count}\n"
            f"❌ Failed: {len(rdp_entries) - success_count}\n\n"
            "Use /settings to view current configuration.",
            parse_mode='Markdown'
        )

    def _parse_rdp_entries(self, text: str) -> List[RDPCredentials]:
        pattern = re.compile(
            r'IP:\s*(\d+\.\d+\.\d+\.\d+)\s*'
            r'USER:\s*(\w+)\s*'
            r'PAS:\s*([\w\^\$\#\@\!]+)\s*'
            r'RAM:\s*(\d+)\s*'
            r'CORE:\s*(\d+)\s*'
            r'LOCATION:\s*(\w+)',
            re.IGNORECASE
        )
        
        entries = []
        for match in pattern.finditer(text):
            ip, user, password, ram, core, location = match.groups()
            entries.append(RDPCredentials(
                ip=ip,
                username=user,
                current_password=password,
                new_password=self.new_password,
                ram=ram,
                core=core,
                location=location
            ))
        return entries

    async def set_password(self, update: Update, context: CallbackContext) -> None:
        if len(context.args) != 1:
            await update.message.reply_text(
                "❌ *Usage:* /setpassword <new_password>\n"
                "Example: `/setpassword NewSecure123!`",
                parse_mode='Markdown'
            )
            return

        self.new_password = context.args[0]
        await update.message.reply_text(
            f"✅ New password template set to: `{self.new_password}`",
            parse_mode='Markdown'
        )

def main():
    # Replace with your bot token
    bot_token = "8152265435:AAH9ex75KOmXl6lb_M79EAQgUvnPjbfkYUA"
    
    # Initialize bot
    rdp_bot = RDPBot(bot_token)
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("setpassword", rdp_bot.set_password))
    application.add_handler(MessageHandler(filters.TEXT & filters.FORWARDED, rdp_bot.handle_forward))
    
    # Start bot
    application.run_polling()

if __name__ == "__main__":
    main()
