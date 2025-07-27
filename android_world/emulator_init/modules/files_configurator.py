"""Files configuration for Android emulator."""

import os
import random
import string
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.utils import file_utils

from .base_configurator import BaseConfigurator


class FilesConfigurator(BaseConfigurator):
    """Configurator for Files app with predefined file structure."""
    
    @property
    def module_name(self) -> str:
        return "Files"
    
    def configure(self) -> bool:
        """Configure Files app based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring Files app...')
        
        try:
            # Set root for file operations
            adb_utils.set_root_if_needed(self.env_controller)
            
            # Base storage path for Android emulator
            base_path = '/storage/emulated/0'
            
            # Clear folders if requested
            if self.config.get('clear_folders'):
                self._clear_folders(base_path)
            
            # Create folders
            if self.config.get('create_folders'):
                self._create_folders(base_path)
            
            # Add files
            if self.config.get('add_files'):
                self._add_files(base_path)
            
            # Copy files if requested
            if self.config.get('copy_files'):
                self._copy_files(base_path)
            
            # Add random files if requested
            if self.config.get('add_random_files', False):
                self._add_random_files(base_path)
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure Files app: {e}")
            return False
    
    def _clear_folders(self, base_path: str) -> None:
        """Clear specified folders."""
        for folder_path in self.config.get('clear_folders', []):
            full_path = os.path.join(base_path, folder_path)
            self.log_info(f'Clearing folder: {full_path}')
            try:
                if file_utils.check_directory_exists(full_path, self.env_controller):
                    file_utils.clear_directory(full_path, self.env_controller)
                    self.log_info(f'Successfully cleared folder: {full_path}')
                else:
                    self.log_warning(f'Folder does not exist, creating it: {full_path}')
                    file_utils.mkdir(full_path, self.env_controller)
            except Exception as e:
                self.log_error(f'Error clearing folder {full_path}: {e}')
    
    def _create_folders(self, base_path: str) -> None:
        """Create folders."""
        for folder_path in self.config.get('create_folders', []):
            full_path = os.path.join(base_path, folder_path)
            self.log_info(f'Creating folder: {full_path}')
            try:
                file_utils.mkdir(full_path, self.env_controller)
                self.log_info(f'Successfully created folder: {full_path}')
            except Exception as e:
                self.log_error(f'Error creating folder {full_path}: {e}')
    
    def _add_files(self, base_path: str) -> None:
        """Add files."""
        for file_info in self.config.get('add_files', []):
            file_name = file_info.get('name')
            folder_path = file_info.get('folder', '')
            content = file_info.get('content', '')
            
            if not file_name:
                continue
                
            full_folder_path = os.path.join(base_path, folder_path)
            
            try:
                self.log_info(f'Creating file: {file_name} in {full_folder_path}')
                if not file_utils.check_directory_exists(full_folder_path, self.env_controller):
                    self.log_info(f'Folder does not exist, creating it: {full_folder_path}')
                    file_utils.mkdir(full_folder_path, self.env_controller)
                file_utils.create_file(file_name, full_folder_path, self.env_controller, content)
                self.log_info(f'Successfully created file: {file_name}')
            except Exception as e:
                self.log_error(f'Error creating file {file_name}: {e}')
    
    def _copy_files(self, base_path: str) -> None:
        """Copy files."""
        for copy_info in self.config.get('copy_files', []):
            source_path = copy_info.get('source')
            destination_path = copy_info.get('destination')
            
            if not source_path or not destination_path:
                continue
                
            full_source_path = os.path.join(base_path, source_path)
            full_destination_path = os.path.join(base_path, destination_path)
            
            try:
                self.log_info(f'Copying file from {full_source_path} to {full_destination_path}')
                # First make sure the destination directory exists
                dest_dir = os.path.dirname(full_destination_path)
                if not file_utils.check_directory_exists(dest_dir, self.env_controller):
                    file_utils.mkdir(dest_dir, self.env_controller)
                
                # Execute the copy command using adb
                adb_utils.issue_generic_request(
                    ["shell", "cp", full_source_path, full_destination_path], 
                    self.env_controller
                )
                self.log_info('Successfully copied file')
            except Exception as e:
                self.log_error(f'Error copying file: {e}')
    
    def _add_random_files(self, base_path: str) -> None:
        """Add random files."""
        file_count = self.config.get('random_file_count', 5)
        folders = self.config.get('random_file_folders', ['Download', 'Documents', 'Pictures'])
        
        self.log_info(f'Adding {file_count} random files...')
        
        for i in range(file_count):
            folder = random.choice(folders)
            full_folder_path = os.path.join(base_path, folder)
            
            # Ensure folder exists
            if not file_utils.check_directory_exists(full_folder_path, self.env_controller):
                try:
                    file_utils.mkdir(full_folder_path, self.env_controller)
                except Exception as e:
                    self.log_error(f'Error creating folder {full_folder_path}: {e}')
                    continue
            
            # Generate random file with random extension
            extensions = ['.txt', '.md', '.log', '.csv', '.json']
            file_name = f"random_file_{i+1}{random.choice(extensions)}"
            content = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(100))
            
            try:
                self.log_info(f'Creating random file: {file_name} in {full_folder_path}')
                file_utils.create_file(file_name, full_folder_path, self.env_controller, content)
            except Exception as e:
                self.log_error(f'Error creating random file {file_name}: {e}') 