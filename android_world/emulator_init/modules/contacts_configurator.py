"""Contacts configuration for Android emulator."""

from android_world.utils import contacts_utils

from .base_configurator import BaseConfigurator
from ..utils.constants import DEFAULT_VALUES


class ContactsConfigurator(BaseConfigurator):
    """Configurator for contacts management."""
    
    @property
    def module_name(self) -> str:
        return "Contacts"
    
    def configure(self) -> bool:
        """Configure contacts based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring contacts...')
        
        try:
            # Clear contacts if specified
            if self.config.get('clear_contacts', False):
                contacts_utils.clear_contacts(self.env_controller)
                self.log_info('Cleared all contacts.')
            
            # Add contacts if provided
            self._add_contacts()
            
            # Verify contacts
            if self.config.get('verify_contacts', False):
                self._verify_contacts()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure contacts: {e}")
            return False
    
    def _add_contacts(self) -> None:
        """Add contacts from configuration."""
        contacts_to_add = self.config.get('add_contacts', [])
        ui_delay = self.config.get('ui_delay_sec', 1.0)
        
        for contact in contacts_to_add:
            name = contact.get('name', '')
            number = contact.get('number', '')
            
            if name and number:
                try:
                    contacts_utils.add_contact(
                        name, number, self.env_controller, ui_delay_sec=ui_delay
                    )
                    self.log_info(f'Added contact: {name} ({number})')
                except Exception as e:
                    self.log_error(f"Failed to add contact {name}: {e}")
    
    def _verify_contacts(self) -> None:
        """Verify that contacts were added correctly."""
        try:
            contacts_list = contacts_utils.list_contacts(self.env_controller)
            self.log_info(f"Verified contacts: {len(contacts_list)} contacts found")
            for contact in contacts_list:
                self.log_info(f"  - {contact.name}: {contact.number}")
        except Exception as e:
            self.log_error(f"Failed to verify contacts: {e}") 