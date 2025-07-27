"""Calendar configuration for Android emulator."""

import datetime
import time
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.task_evals.single.calendar import calendar_utils
from android_world.task_evals.utils import sqlite_schema_utils, sqlite_utils

from .base_configurator import BaseConfigurator


class CalendarConfigurator(BaseConfigurator):
    """Configurator for calendar events and scheduling."""
    
    @property
    def module_name(self) -> str:
        return "Calendar"
    
    def configure(self) -> bool:
        """Configure calendar events based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring calendar events...')
        
        try:
            # Ensure calendar app is installed and ready
            if not self._setup_calendar_app():
                return False
            
            # Clear existing events if specified
            if self.config.get('clear_events', False):
                self._clear_calendar_events()
            
            # Add specific events
            events_to_add = self.config.get('add_events', [])
            if events_to_add:
                self._add_specific_events(events_to_add)
            
            # Add random events if specified
            if self.config.get('add_random_events', False):
                self._add_random_events()
            
            # Restart calendar app to refresh UI
            self._restart_calendar_app()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure calendar: {e}")
            return False
    
    def _setup_calendar_app(self) -> bool:
        """Ensure calendar app is installed and properly configured."""
        try:
            calendar_package = "com.simplemobiletools.calendar.pro"
            self.log_info(f"Ensure calendar app {calendar_package} is running...")
            
            # Check if calendar app is installed
            all_packages = adb_utils.get_all_package_names(self.env_controller)
            if calendar_package not in all_packages:
                self.log_error(f"Calendar app {calendar_package} is not installed! Please install the app first.")
                return False
            
            # Launch calendar app
            adb_utils.launch_app("simple calendar pro", self.env_controller)
            time.sleep(2)  # Wait for app to start
            
            # Ensure root permissions
            adb_utils.set_root_if_needed(self.env_controller)
            
            # Grant calendar permissions
            adb_utils.grant_permissions(calendar_package, "android.permission.READ_CALENDAR", self.env_controller)
            adb_utils.grant_permissions(calendar_package, "android.permission.WRITE_CALENDAR", self.env_controller)
            
            # Return to home screen
            adb_utils.press_home_button(self.env_controller)
            time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log_error(f"Error starting calendar app or setting permissions: {e}")
            return True  # Continue anyway
    
    def _clear_calendar_events(self) -> None:
        """Clear all existing calendar events."""
        try:
            db_path = calendar_utils.DB_PATH
            self.log_info(f"Attempting to clear calendar database: {db_path}")
            
            calendar_utils.clear_calendar_db(self.env_controller)  # Use env_controller
            self.log_info('Successfully cleared all calendar events')
            
            # Verify clearing was successful
            try:
                events = sqlite_utils.get_rows_from_remote_device(
                    calendar_utils.EVENTS_TABLE,
                    db_path,
                    sqlite_schema_utils.CalendarEvent,
                    self.env_controller  # Use env_controller
                )
                self.log_info(f"Remaining events after clearing: {len(events)}")
            except Exception as e:
                self.log_warning(f"Unable to verify clearing result: {e}")
                
        except Exception as e:
            self.log_error(f"Failed to clear calendar events: {e}")
            
            try:
                # Try alternative method: direct SQL command
                adb_utils.execute_sql_command(calendar_utils.DB_PATH, "DELETE FROM events;", self.env_controller)
                self.log_info("Cleared calendar events using direct SQL command")
            except Exception as e2:
                self.log_error(f"Alternative clearing method also failed: {e2}")
    
    def _add_specific_events(self, events_to_add: List[Dict[str, Any]]) -> None:
        """Add specific calendar events from configuration."""
        calendar_events = []
        
        for i, event in enumerate(events_to_add):
            title = event.get('title', '')
            description = event.get('description', '')
            location = event.get('location', '')
            
            # Parse start and end times
            start_time = event.get('start_time', None)
            end_time = event.get('end_time', None)
            
            # Duration in minutes - used if end_time not provided
            duration_mins = event.get('duration_mins', 30)
            
            # Repeat settings
            repeat_interval = event.get('repeat_interval', 0)
            day_of_week = event.get('day_of_week', 0)
            repeat_rule = 0
            
            if repeat_interval == 'weekly' and 1 <= day_of_week <= 7:
                repeat_interval = 60 * 60 * 24 * 7  # Weekly (seconds)
                repeat_rule = calendar_utils.generate_simple_calendar_weekly_repeat_rule(day_of_week)
                self.log_info(f"Set weekly repeat, weekday {day_of_week}, rule value: {repeat_rule}")
            elif repeat_interval == 'daily':
                repeat_interval = 60 * 60 * 24  # Daily (seconds)
                self.log_info("Set daily repeat")
            else:
                repeat_interval = 0  # No repeat
            
            if title and start_time:
                try:
                    # Parse start time to Unix timestamp
                    if isinstance(start_time, str):
                        start_dt = datetime.datetime.fromisoformat(start_time)
                        start_ts = int(start_dt.timestamp())
                        self.log_info(f"Event[{i+1}] '{title}' start time: {start_dt}")
                    else:
                        # Assume already Unix timestamp
                        start_ts = start_time
                        self.log_info(f"Event[{i+1}] '{title}' start timestamp: {start_ts}")
                    
                    # Calculate end time
                    if end_time:
                        if isinstance(end_time, str):
                            end_dt = datetime.datetime.fromisoformat(end_time)
                            end_ts = int(end_dt.timestamp())
                            self.log_info(f"Event[{i+1}] '{title}' end time: {end_dt}")
                        else:
                            end_ts = end_time
                            self.log_info(f"Event[{i+1}] '{title}' end timestamp: {end_ts}")
                    else:
                        end_ts = start_ts + (duration_mins * 60)
                        self.log_info(f"Event[{i+1}] '{title}' duration: {duration_mins} minutes, end timestamp: {end_ts}")
                    
                    # Create calendar event object
                    calendar_event = sqlite_schema_utils.CalendarEvent(
                        start_ts=start_ts,
                        end_ts=end_ts,
                        title=title,
                        description=description,
                        location=location,
                        repeat_interval=repeat_interval,
                        repeat_rule=repeat_rule
                    )
                    
                    calendar_events.append(calendar_event)
                    self.log_info(f"Prepared calendar event[{i+1}]: '{title}' at {datetime.datetime.fromtimestamp(start_ts)}")
                except Exception as e:
                    self.log_error(f"Failed to create calendar event '{title}': {e}")
        
        # Add events to calendar database
        if calendar_events:
            try:
                self.log_info(f"Attempting to add {len(calendar_events)} events to calendar database...")
                calendar_utils.add_events(calendar_events, self.env_controller)  # Use env_controller
                self.log_info(f"Successfully added {len(calendar_events)} events to calendar database")
                
                # Verify addition was successful
                try:
                    db_path = calendar_utils.DB_PATH
                    events = sqlite_utils.get_rows_from_remote_device(
                        calendar_utils.EVENTS_TABLE,
                        db_path,
                        sqlite_schema_utils.CalendarEvent,
                        self.env_controller  # Use env_controller
                    )
                    self.log_info(f"Total events after addition: {len(events)}")
                    for i, event in enumerate(events[:min(5, len(events))]):
                        self.log_info(f"  - Event[{i+1}]: {event.title} ({datetime.datetime.fromtimestamp(event.start_ts)})")
                    if len(events) > 5:
                        self.log_info(f"  - {len(events) - 5} more events...")
                except Exception as e:
                    self.log_warning(f"Unable to verify addition result: {e}")
                    
            except Exception as e:
                self.log_error(f"Failed to add events to calendar database: {e}")
                
                try:
                    # Try adding events one by one
                    self.log_info("Attempting to add events one by one...")
                    for i, event in enumerate(calendar_events):
                        try:
                            calendar_utils.add_events([event], self.env_controller)  # Use env_controller
                            self.log_info(f"Successfully added event[{i+1}]: {event.title}")
                        except Exception as e_inner:
                            self.log_error(f"Failed to add single event[{i+1}] '{event.title}': {e_inner}")
                except Exception as e2:
                    self.log_error(f"Adding events one by one also failed: {e2}")
    
    def _add_random_events(self) -> None:
        """Add random calendar events if specified."""
        num_random_events = self.config.get('random_event_count', 10)
        if num_random_events > 0:
            try:
                self.log_info(f"Attempting to add {num_random_events} random events to calendar...")
                calendar_utils.add_random_events(self.env_controller, num_random_events)  # Use env_controller
                self.log_info(f"Successfully added {num_random_events} random events to calendar")
            except Exception as e:
                self.log_error(f"Failed to add random events: {e}")
    
    def _restart_calendar_app(self) -> None:
        """Restart calendar app to refresh UI."""
        try:
            adb_utils.launch_app("simple calendar pro", self.env_controller)
            self.log_info("Restarted calendar app to refresh UI")
        except Exception as e:
            self.log_warning(f"Failed to restart calendar app: {e}")
