"""System configuration for Android emulator."""

from android_world.env import adb_utils

from .base_configurator import BaseConfigurator


class SystemConfigurator(BaseConfigurator):
    """Configurator for system settings."""
    
    @property
    def module_name(self) -> str:
        return "System"
    
    def configure(self) -> bool:
        """Configure system settings based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring system settings...')
        
        try:
            # Configure screen brightness
            if 'brightness' in self.config:
                self._configure_brightness()
            
            # Configure WiFi state
            if 'wifi' in self.config:
                self._configure_wifi()
            
            # Configure Bluetooth state
            if 'bluetooth' in self.config:
                self._configure_bluetooth()
            
            # Set clipboard content
            if 'clipboard' in self.config:
                self._configure_clipboard()
            
            # Configure airplane mode
            if 'airplane_mode' in self.config:
                self._configure_airplane_mode()
            
            # Close all apps if requested
            if self.config.get('close_all_apps', False):
                self._close_all_apps()
            
            # Open specific app if requested
            if 'open_app' in self.config:
                self._open_app()
            
            # Press home button if close_all_apps was enabled and no specific app to open
            if (self.config.get('close_all_apps', False) and 
                'open_app' not in self.config):
                self._press_home()
            
            self.log_info('System configuration completed.')
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure system: {e}")
            return False
    
    def _configure_brightness(self) -> None:
        """Configure screen brightness."""
        brightness = self.config['brightness']
        if brightness in ['max', 'min']:
            try:
                self.log_info(f'Setting screen brightness to {brightness}')
                adb_utils.set_brightness(brightness, self.env_controller)
                
                # Verify the brightness setting
                res = adb_utils.issue_generic_request(
                    ['shell', 'settings', 'get', 'system', 'screen_brightness'],
                    self.env_controller,
                )
                brightness_level = int(res.generic.output.decode().strip())
                expected_level = 255 if brightness == 'max' else 1
                if brightness_level == expected_level:
                    self.log_info(f'Successfully set brightness to {brightness} ({brightness_level})')
                else:
                    self.log_warning(f'Brightness level ({brightness_level}) does not match expected level ({expected_level})')
            except Exception as e:
                self.log_error(f'Error setting brightness: {e}')
        else:
            self.log_warning(f'Invalid brightness value: {brightness}. Must be "max" or "min".')
    
    def _configure_wifi(self) -> None:
        """Configure WiFi state."""
        wifi_state = self.config['wifi']
        if wifi_state in ['on', 'off']:
            try:
                self.log_info(f'Setting WiFi to {wifi_state}')
                adb_utils.toggle_wifi(self.env_controller, wifi_state)
                
                # Verify the WiFi state
                res = adb_utils.issue_generic_request(
                    ['shell', 'settings', 'get', 'global', 'wifi_on'], 
                    self.env_controller
                )
                current_state = res.generic.output.decode().strip()
                if wifi_state == 'on':
                    if current_state in ['1', '2']:
                        self.log_info('Successfully turned WiFi on')
                    else:
                        self.log_warning(f'Failed to turn WiFi on, current state: {current_state}')
                else:  # wifi_state == 'off'
                    if current_state == '0':
                        self.log_info('Successfully turned WiFi off')
                    else:
                        self.log_warning(f'Failed to turn WiFi off, current state: {current_state}')
            except Exception as e:
                self.log_error(f'Error setting WiFi state: {e}')
        else:
            self.log_warning(f'Invalid WiFi state: {wifi_state}. Must be "on" or "off".')
    
    def _configure_bluetooth(self) -> None:
        """Configure Bluetooth state."""
        bluetooth_state = self.config['bluetooth']
        if bluetooth_state in ['on', 'off']:
            try:
                self.log_info(f'Setting Bluetooth to {bluetooth_state}')
                adb_utils.toggle_bluetooth(self.env_controller, bluetooth_state)
                
                # Verify the Bluetooth state
                res = adb_utils.issue_generic_request(
                    ['shell', 'settings', 'get', 'global', 'bluetooth_on'], 
                    self.env_controller
                )
                current_state = res.generic.output.decode().strip()
                expected_state = '1' if bluetooth_state == 'on' else '0'
                if current_state == expected_state:
                    self.log_info(f'Successfully set Bluetooth to {bluetooth_state}')
                else:
                    self.log_warning(f'Failed to set Bluetooth to {bluetooth_state}, current state: {current_state}')
            except Exception as e:
                self.log_error(f'Error setting Bluetooth state: {e}')
        else:
            self.log_warning(f'Invalid Bluetooth state: {bluetooth_state}. Must be "on" or "off".')
    
    def _configure_clipboard(self) -> None:
        """Configure clipboard content."""
        clipboard_content = self.config['clipboard']
        try:
            self.log_info(f'Setting clipboard content: {clipboard_content}')
            adb_utils.set_clipboard_contents(clipboard_content, self.env_controller)
            
            # Verify the clipboard content
            current_content = adb_utils.get_clipboard_contents(self.env_controller)
            self.log_info(f'Clipboard content set: {current_content}')
        except Exception as e:
            self.log_error(f'Error setting clipboard content: {e}')
    
    def _configure_airplane_mode(self) -> None:
        """Configure airplane mode."""
        airplane_mode = self.config['airplane_mode']
        if airplane_mode in ['on', 'off']:
            try:
                self.log_info(f'Setting airplane mode to {airplane_mode}')
                adb_utils.toggle_airplane_mode(airplane_mode, self.env_controller)
                
                # Verify airplane mode state
                is_enabled = adb_utils.check_airplane_mode(self.env_controller)
                expected_enabled = airplane_mode == 'on'
                if is_enabled == expected_enabled:
                    self.log_info(f'Successfully set airplane mode to {airplane_mode}')
                else:
                    self.log_warning(f'Failed to set airplane mode to {airplane_mode}, current state: {"on" if is_enabled else "off"}')
            except Exception as e:
                self.log_error(f'Error setting airplane mode: {e}')
        else:
            self.log_warning(f'Invalid airplane mode: {airplane_mode}. Must be "on" or "off".')
    
    def _close_all_apps(self) -> None:
        """Close all recent apps."""
        try:
            self.log_info('Closing all recent apps')
            adb_utils.close_recents(self.env_controller)
            self.log_info('Successfully closed all recent apps')
        except Exception as e:
            self.log_error(f'Error closing recent apps: {e}')
    
    def _open_app(self) -> None:
        """Open a specific app."""
        app_name = self.config['open_app']
        try:
            self.log_info(f'Opening app: {app_name}')
            package_name = adb_utils.launch_app(app_name, self.env_controller)
            if package_name:
                self.log_info(f'Successfully opened app: {app_name} (package: {package_name})')
            else:
                self.log_warning(f'Failed to open app: {app_name}')
        except Exception as e:
            self.log_error(f'Error opening app: {e}')
    
    def _press_home(self) -> None:
        """Press home button to return to home screen."""
        try:
            self.log_info('Pressing home button to return to home screen')
            adb_utils.press_home_button(self.env_controller)
            self.log_info('Successfully returned to home screen')
        except Exception as e:
            self.log_error(f'Error pressing home button: {e}') 