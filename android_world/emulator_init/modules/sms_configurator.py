"""SMS configuration for Android emulator."""

import random
import time
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.task_evals.utils import user_data_generation

from .base_configurator import BaseConfigurator


class SMSConfigurator(BaseConfigurator):
    """Configurator for SMS messages."""
    
    @property
    def module_name(self) -> str:
        return "SMS"
    
    def configure(self) -> bool:
        """Configure SMS messages based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring SMS messages...')
        
        try:
            # Disable notifications during setup if requested
            disable_notifications = self.config.get('disable_notifications_during_setup', True)
            if disable_notifications:
                self._toggle_sms_notifications(False)
            
            # Disable auto reply if requested
            disable_auto_reply = self.config.get('disable_auto_reply', True)
            
            # Clear existing SMS if specified - use clear_messages to match config file
            if self.config.get('clear_messages', False):
                self._clear_all_sms()
            
            # Add specific messages
            messages_to_add = self.config.get('add_messages', [])
            if messages_to_add:
                self._add_specific_messages(messages_to_add, disable_auto_reply)
            
            # Add random conversations if specified
            if self.config.get('add_random_conversations', False):
                conversation_count = self.config.get('random_conversation_count', 3)
                self._add_random_conversations(conversation_count)
            
            # Re-enable notifications if they were disabled
            if disable_notifications:
                self._toggle_sms_notifications(True)
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure SMS: {e}")
            return False
    
    def _toggle_sms_notifications(self, enable: bool) -> None:
        """Toggle SMS notifications."""
        try:
            if enable:
                self.log_info("Re-enabling SMS notifications")
            else:
                self.log_info("Temporarily disabling SMS notifications during setup")
            
            # Implementation would depend on specific notification settings
            # This is a placeholder for the notification toggle logic
            
        except Exception as e:
            self.log_error(f"Failed to toggle SMS notifications: {e}")
    
    def _clear_all_sms(self) -> None:
        """Clear all SMS messages from the device."""
        self.log_info('Clearing all SMS messages using database approach...')
        
        # Direct database deletion approach - more reliable
        try:
            # Path to the SMS database
            db_path = "/data/data/com.android.providers.telephony/databases/mmssms.db"
            
            # Delete messages from SMS, MMS, and threads tables
            adb_utils.execute_sql_command(db_path, "DELETE FROM sms;", self.env_controller)
            adb_utils.execute_sql_command(db_path, "DELETE FROM threads;", self.env_controller)
            adb_utils.execute_sql_command(db_path, "DELETE FROM mms;", self.env_controller)
            adb_utils.execute_sql_command(db_path, "DELETE FROM canonical_addresses;", self.env_controller)
            
            # Also try to clear using content provider
            clear_commands = [
                ['shell', 'content delete --uri content://sms'],
                ['shell', 'content delete --uri content://sms/inbox'],
                ['shell', 'content delete --uri content://sms/sent'],
                ['shell', 'content delete --uri content://sms/draft'],
                ['shell', 'content delete --uri content://sms/conversations'],
                ['shell', 'content delete --uri content://mms'],
                ['shell', 'content delete --uri content://mms-sms/conversations'],
            ]
            
            for cmd in clear_commands:
                try:
                    adb_utils.issue_generic_request(cmd, self.env_controller)
                except Exception as e:
                    self.log_warning(f"Command {cmd} failed: {e}")
            
            self.log_info('Successfully cleared SMS and threads tables.')
            
            # Force messaging app to refresh
            refresh_cmd = ['shell', 'am broadcast -a android.provider.Telephony.SMS_RECEIVED']
            adb_utils.issue_generic_request(refresh_cmd, self.env_controller)
            
        except Exception as e:
            self.log_error(f"Error clearing SMS database: {e}")
            self.log_info('Falling back to app data clearing method...')
            
            # Fallback to the app data clearing method if database approach fails
            sms_packages = [
                "com.simplemobiletools.smsmessenger",  # Simple SMS Messenger
                "com.google.android.apps.messaging",   # Google Messages
                "com.android.mms",                     # Default SMS app
            ]
            
            for pkg in sms_packages:
                try:
                    adb_utils.clear_app_data(pkg, self.env_controller)
                except Exception as pkg_e:
                    self.log_warning(f"Could not clear data for {pkg}: {pkg_e}")
        
        # Wait a moment for the operation to complete
        time.sleep(2.0)
    
    def _add_specific_messages(self, messages: List[Dict[str, Any]], disable_auto_reply: bool) -> None:
        """Add specific SMS messages."""
        added_count = 0
        
        for message_data in messages:
            try:
                number = message_data.get('number', '')
                text = message_data.get('text', '')
                is_received = message_data.get('is_received', True)
                
                if not number or not text:
                    self.log_warning("Skipping message with missing number or text")
                    continue
                
                self._add_sms_message(number, text, is_received, disable_auto_reply)
                added_count += 1
                
            except Exception as e:
                self.log_error(f"Failed to add SMS message: {e}")
        
        self.log_info(f"Successfully added {added_count} SMS messages")
    
    def _add_sms_message(self, number: str, text: str, is_received: bool = True, disable_auto_reply: bool = False) -> None:
        """Add a single SMS message."""
        direction = "received from" if is_received else "sent to"  # Define direction first
        
        try:
            import re
            import time
            from android_world.env import adb_utils
            
            # Clean the phone number
            clean_number = re.sub(r'[^0-9+]', '', number)
            timestamp = int(time.time() * 1000)  # Current time in milliseconds
            
            if disable_auto_reply:
                try:
                    # Need to escape single quotes for shell command
                    escaped_text = text.replace("'", "''").replace('"', '\\"')
                    
                    if is_received:
                        # For incoming messages, use emu sms send command (more reliable than content provider)
                        adb_args = [
                            'emu', 'sms', 'send', clean_number, escaped_text
                        ]
                        adb_utils.issue_generic_request(adb_args, self.env_controller)
                    else:
                        # For outgoing messages, we have to use sqlite directly
                        db_path = "/data/data/com.android.providers.telephony/databases/mmssms.db"
                        insert_stmt = f"INSERT INTO sms(address, date, body, read, type) VALUES('{clean_number}', {timestamp}, '{escaped_text}', 1, 2);"
                        adb_utils.execute_sql_command(db_path, insert_stmt, self.env_controller)
                    
                    # Force messaging app to refresh its view
                    time.sleep(0.5)
                    refresh_cmd = ['shell', 'am broadcast -a android.provider.Telephony.SMS_RECEIVED']
                    adb_utils.issue_generic_request(refresh_cmd, self.env_controller)
                except Exception as e:
                    self.log_error(f"Error using direct database method: {e}")
                    # Fall back to the original approach if the direct method fails
                    if is_received:
                        # For incoming messages, use text_emulator
                        adb_utils.text_emulator(self.env_controller, number, text)
                    else:
                        # For outgoing messages, use UI interaction
                        from android_world.env import tools
                        controller = tools.AndroidToolController(self.env_controller)
                        controller.send_sms(number, text)
            else:
                # Original approach
                if is_received:
                    # For incoming messages, use text_emulator
                    adb_utils.text_emulator(self.env_controller, number, text)
                else:
                    # For outgoing messages, use UI interaction
                    from android_world.env import tools
                    controller = tools.AndroidToolController(self.env_controller)
                    controller.send_sms(number, text)
                    
            # Add a delay after adding each message
            time.sleep(0.5)
            
            self.log_info(f"Added SMS {direction} {number}: {text[:50]}...")
            
        except Exception as e:
            self.log_error(f"Failed to add SMS message {direction} {number}: {e}")
    
    def _add_random_conversations(self, num_conversations: int = 3, max_messages_per_conversation: int = 5) -> None:
        """Add random SMS conversations."""
        try:
            self.log_info(f"Adding {num_conversations} random SMS conversations...")
            
            # Sample contact names and numbers
            contacts = [
                {"name": "Alice Johnson", "number": "+1234567890"},
                {"name": "Bob Smith", "number": "+1234567891"},
                {"name": "Carol Davis", "number": "+1234567892"},
                {"name": "David Wilson", "number": "+1234567893"},
                {"name": "Emma Brown", "number": "+1234567894"},
                {"name": "Frank Miller", "number": "+1234567895"},
                {"name": "Grace Lee", "number": "+1234567896"},
                {"name": "Henry Taylor", "number": "+1234567897"},
            ]
            
            # Sample message templates
            message_templates = [
                "Hey, how are you doing?",
                "Are you free for lunch today?",
                "Thanks for your help yesterday!",
                "Can you call me when you get this?",
                "See you at the meeting tomorrow",
                "Happy birthday! Hope you have a great day!",
                "Don't forget about dinner tonight",
                "The weather is beautiful today",
                "Did you see the news?",
                "Let me know if you need anything",
                "Running a bit late, will be there soon",
                "Great job on the presentation!",
                "What time works best for you?",
                "Hope everything is going well",
                "Thanks for the reminder!"
            ]
            
            responses = [
                "Great, thanks for asking!",
                "Yes, that sounds good",
                "You're welcome!",
                "Sure, I'll call you in a few minutes",
                "Looking forward to it",
                "Thank you so much!",
                "Sounds perfect",
                "I agree, it's lovely",
                "Yes, quite surprising!",
                "Will do, thanks",
                "No worries, take your time",
                "Thank you!",
                "How about 2 PM?",
                "Thanks, you too!",
                "No problem at all"
            ]
            
            # Generate conversations
            for i in range(min(num_conversations, len(contacts))):
                contact = contacts[i]
                num_messages = random.randint(1, max_messages_per_conversation)
                
                for j in range(num_messages):
                    # Alternate between received and sent messages
                    is_received = j % 2 == 0
                    
                    if is_received:
                        message_text = random.choice(message_templates)
                    else:
                        message_text = random.choice(responses)
                    
                    # Add some delay between messages to make timestamps realistic
                    time.sleep(0.1)
                    
                    self._add_sms_message(
                        number=contact["number"],
                        text=message_text,
                        is_received=is_received,
                        disable_auto_reply=True
                    )
                
                self.log_info(f"Created conversation with {contact['name']} ({num_messages} messages)")
            
            self.log_info(f"Successfully created {num_conversations} random conversations")
            
        except Exception as e:
            self.log_error(f"Failed to add random SMS conversations: {e}") 