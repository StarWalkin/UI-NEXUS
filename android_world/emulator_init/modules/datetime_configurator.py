"""DateTime configuration for Android emulator."""

import datetime
import random
from typing import Dict, Any

from android_world.utils import datetime_utils

from .base_configurator import BaseConfigurator


class DateTimeConfigurator(BaseConfigurator):
    """Configurator for datetime settings."""
    
    @property
    def module_name(self) -> str:
        return "DateTime"
    
    def configure(self) -> bool:
        """Configure datetime settings based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring datetime settings...')
        
        try:
            # Disable auto settings if specified (default: True like original)
            if self.config.get('disable_auto_settings', True):
                self._disable_auto_settings()
            
            # Set 24-hour format if specified (default: True like original)
            if self.config.get('use_24_hour_format', True):
                self._enable_24_hour_format()
                self.log_info('Set 24-hour time format.')
            
            # Set timezone if specified
            timezone = self.config.get('timezone')
            if timezone:
                self._set_timezone(timezone)
                self.log_info(f'Set timezone to {timezone}.')
            
            # Set specific datetime if provided
            if 'datetime' in self.config:
                self._set_specific_datetime()
            
            # Set random datetime if configured
            elif self.config.get('use_random_datetime', False):
                self._set_random_datetime()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure datetime: {e}")
            return False
    
    def _disable_auto_settings(self) -> None:
        """Disable automatic date/time/timezone settings."""
        try:
            # Use the existing _disable_auto_settings function from datetime_utils
            from android_env.proto import adb_pb2
            from android_world.env import adb_utils
            
            adb_utils.put_settings(
                adb_pb2.AdbRequest.SettingsRequest.Namespace.GLOBAL, 'auto_time', '0', self.env_controller
            )
            adb_utils.put_settings(
                adb_pb2.AdbRequest.SettingsRequest.Namespace.GLOBAL,
                'auto_time_zone',
                '0',
                self.env_controller,
            )
            self.log_info('Disabled automatic date, time, and timezone settings.')
        except Exception as e:
            self.log_error(f"Failed to disable auto settings: {e}")
    
    def _enable_24_hour_format(self) -> None:
        """Set device to use 24-hour time format."""
        try:
            from android_env.proto import adb_pb2
            from android_world.env import adb_utils
            
            adb_utils.put_settings(
                adb_pb2.AdbRequest.SettingsRequest.Namespace.SYSTEM,
                'time_12_24',
                '24',
                self.env_controller,
            )
        except Exception as e:
            self.log_error(f"Failed to enable 24-hour format: {e}")
    
    def _set_timezone(self, timezone: str) -> None:
        """Set the device timezone.

        Args:
            timezone: Timezone string (e.g., 'UTC', 'America/New_York').
        """
        try:
            from android_world.env import adb_utils
            
            adb_command = ['shell', 'service', 'call', 'alarm', '3', 's16', timezone]
            adb_utils.issue_generic_request(adb_command, self.env_controller)
        except Exception as e:
            self.log_error(f"Failed to set timezone: {e}")
    
    def _set_specific_datetime(self) -> None:
        """Set specific datetime from configuration."""
        datetime_config = self.config['datetime']
        
        try:
            if isinstance(datetime_config, dict):
                # Parse datetime from components
                year = datetime_config.get('year')
                month = datetime_config.get('month')
                day = datetime_config.get('day')
                hour = datetime_config.get('hour', 0)
                minute = datetime_config.get('minute', 0)
                second = datetime_config.get('second', 0)
                
                if all(param is not None for param in [year, month, day]):
                    dt = datetime.datetime(year, month, day, hour, minute, second)
                    self._set_datetime_direct(dt)
                    self.log_info(f'Set datetime to {dt}.')
            elif isinstance(datetime_config, str):
                # Parse datetime from string format
                dt = datetime.datetime.fromisoformat(datetime_config)
                self._set_datetime_direct(dt)
                self.log_info(f'Set datetime to {dt}.')
        except Exception as e:
            self.log_error(f"Failed to set specific datetime: {e}")
    
    def _set_random_datetime(self) -> None:
        """Set random datetime within specified window."""
        try:
            window_size_days = self.config.get('random_window_size_days', 14)
            window_size = datetime.timedelta(days=window_size_days)
            
            if 'random_window_center' in self.config:
                center_str = self.config['random_window_center']
                window_center = datetime.datetime.fromisoformat(center_str)
            else:
                # Use current time as center if not specified
                window_center = datetime.datetime.now()
            
            random_dt = datetime_utils.generate_random_datetime(
                window_size=window_size,
                window_center=window_center
            )
            self._set_datetime_direct(random_dt)
            self.log_info(f'Set random datetime to {random_dt}.')
        except Exception as e:
            self.log_error(f"Failed to set random datetime: {e}")
    
    def _set_datetime_direct(self, dt: datetime.datetime) -> None:
        """Set datetime directly using ADB commands."""
        try:
            from android_world.env import adb_utils
            
            # Format datetime for Android's date command: MMDDhhmm[[CC]YY][.ss]
            formatted_time = dt.strftime('%m%d%H%M%y.%S')
            adb_utils.issue_generic_request(
                ['shell', 'date', formatted_time], self.env_controller
            )
        except Exception as e:
            self.log_error(f"Failed to set datetime directly: {e}") 