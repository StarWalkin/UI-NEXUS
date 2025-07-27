"""Markor configuration for Android emulator."""

import datetime
import os
import random
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.utils import file_utils

from .base_configurator import BaseConfigurator


class MarkorConfigurator(BaseConfigurator):
    """Configurator for Markor note-taking app."""
    
    @property
    def module_name(self) -> str:
        return "Markor"
    
    def configure(self) -> bool:
        """Configure Markor app based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring Markor app...')
        
        try:
            # Setup Markor app
            if not self._setup_markor_app():
                return False
            
            # Clear existing notes if specified
            if self.config.get('clear_notes', False):
                self._clear_notes()
            
            # Add folders
            if self.config.get('add_folders'):
                self._add_folders()
            
            # Add notes
            notes_to_add = self.config.get('add_notes', [])
            if notes_to_add:
                self._add_notes(notes_to_add)
            
            # Add random notes if specified
            if self.config.get('add_random_notes', False):
                self._add_random_notes()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure Markor app: {e}")
            return False
    
    def _setup_markor_app(self) -> bool:
        """Setup and verify Markor app."""
        package_name = 'net.gsantner.markor'
        
        try:
            # Check if app is installed
            all_packages = adb_utils.get_all_package_names(self.env_controller)
            if package_name not in all_packages:
                self.log_warning("Markor app is not installed! Skipping configuration.")
                return False
            
            # Ensure Markor directory exists
            markor_data_path = '/storage/emulated/0/Documents/Markor'
            if not file_utils.check_directory_exists(markor_data_path, self.env_controller):
                self.log_info(f'Creating Markor directory: {markor_data_path}')
                try:
                    file_utils.mkdir(markor_data_path, self.env_controller)
                    if not file_utils.check_directory_exists(markor_data_path, self.env_controller):
                        self.log_error('Failed to create Markor directory.')
                        return False
                except Exception as e:
                    self.log_error(f'Error creating Markor directory: {e}')
                    return False
            
            return True
        except Exception as e:
            self.log_error(f"Error setting up Markor app: {e}")
            return False
    
    def _clear_notes(self) -> None:
        """Clear existing notes and folders."""
        markor_data_path = '/storage/emulated/0/Documents/Markor'
        
        try:
            self.log_info('Clearing existing notes and folders from Markor...')
            file_utils.clear_directory(markor_data_path, self.env_controller)
            self.log_info('Successfully cleared Markor notes and folders.')
        except Exception as e:
            self.log_error(f'Error clearing Markor notes: {e}')
    
    def _add_folders(self) -> None:
        """Add folders."""
        markor_data_path = '/storage/emulated/0/Documents/Markor'
        
        for folder_info in self.config.get('add_folders', []):
            folder_name = folder_info.get('title')  # Changed from 'name' to 'title'
            if folder_name:
                folder_path = os.path.join(markor_data_path, folder_name)
                try:
                    self.log_info(f'Creating folder: {folder_name}')
                    file_utils.mkdir(folder_path, self.env_controller)
                except Exception as e:
                    self.log_error(f'Error creating folder {folder_name}: {e}')
    
    def _add_notes(self, notes_to_add: List[Dict[str, Any]]) -> None:
        """Add notes."""
        markor_data_path = '/storage/emulated/0/Documents/Markor'
        
        for note_info in notes_to_add:
            title = note_info.get('title')
            content = note_info.get('content', '')
            folder = note_info.get('folder', '')
            
            if not title:
                continue
                
            # Add default extension if none provided
            if not title.endswith('.md') and not title.endswith('.txt'):
                title += '.md'
                
            if folder:
                folder_path = os.path.join(markor_data_path, folder)
                # Check if folder exists
                if not file_utils.check_directory_exists(folder_path, self.env_controller):
                    try:
                        file_utils.mkdir(folder_path, self.env_controller)
                    except Exception as e:
                        self.log_error(f'Error creating folder {folder}: {e}')
                        folder_path = markor_data_path
                note_path = os.path.join(folder_path, title)
            else:
                note_path = os.path.join(markor_data_path, title)
                
            try:
                self.log_info(f'Creating note: {title}')
                file_utils.create_file(title, os.path.dirname(note_path), self.env_controller, content)
            except Exception as e:
                self.log_error(f'Error creating note {title}: {e}')
    
    def _add_random_notes(self) -> None:
        """Add random notes."""
        markor_data_path = '/storage/emulated/0/Documents/Markor'
        note_count = self.config.get('random_note_count', 5)
        
        self.log_info(f'Adding {note_count} random notes...')
        
        for i in range(note_count):
            # Random content for notes
            template_titles = [
                "Meeting Notes", "Project Ideas", "Shopping List", 
                "Travel Plans", "Books to Read", "Recipes", "Daily Journal"
            ]
            
            title = f"{random.choice(template_titles)} {i+1}.md"
            content = f"# {title[:-3]}\n\nThis is a sample note created on {datetime.datetime.now().strftime('%Y-%m-%d')}.\n\n"
            content += "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec auctor, nisl eget ultricies lacinia, nisl nisl aliquam nisl, eget aliquam nisi nisl eget nisl."
            
            try:
                self.log_info(f'Creating random note: {title}')
                file_utils.create_file(title, markor_data_path, self.env_controller, content)
            except Exception as e:
                self.log_error(f'Error creating random note {title}: {e}') 