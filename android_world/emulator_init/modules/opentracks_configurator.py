"""OpenTracks configuration for Android emulator."""

import datetime
import random
import uuid
from typing import Dict, Any, List

import pytz
from android_world.env import adb_utils

from .base_configurator import BaseConfigurator


class OpenTracksConfigurator(BaseConfigurator):
    """Configurator for OpenTracks activity tracker app."""
    
    @property
    def module_name(self) -> str:
        return "OpenTracks"
    
    def configure(self) -> bool:
        """Configure OpenTracks app based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring OpenTracks activity tracker app...')
        
        try:
            # Setup OpenTracks app
            if not self._setup_opentracks_app():
                return False
            
            # Clear existing activities if specified
            if self.config.get('clear_activities', False):
                self._clear_activities()
            
            # Add custom activities
            activities = self.config.get('add_activities', [])
            if activities:
                self._add_activities(activities)
            
            # Add random activities if specified
            if self.config.get('add_random_activities', False):
                random_count = self.config.get('random_activity_count', 5)
                self._add_random_activities(random_count)
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure OpenTracks app: {e}")
            return False
    
    def _get_device_timezone(self) -> str:
        """Get the current timezone from the device."""
        try:
            response = adb_utils.issue_generic_request(
                ['shell', 'getprop', 'persist.sys.timezone'],
                self.env_controller
            )
            if response.status == adb_utils.adb_pb2.AdbResponse.Status.OK:
                timezone_str = response.generic.output.decode('utf-8').strip()
                if timezone_str:
                    return timezone_str
        except Exception as e:
            self.log_warning(f"Could not get device timezone: {e}. Defaulting to UTC.")
        return "UTC"

    def _setup_opentracks_app(self) -> bool:
        """Setup and verify OpenTracks app."""
        package_name = 'de.dennisguse.opentracks'
        
        try:
            # Check if app is installed
            all_packages = adb_utils.get_all_package_names(self.env_controller)
            if package_name not in all_packages:
                self.log_warning(f"OpenTracks app is not installed (package: {package_name}), skipping configuration")
                return False
            
            return True
        except Exception as e:
            self.log_error(f"Error setting up OpenTracks app: {e}")
            return False
    
    def _clear_activities(self) -> None:
        """Clear existing activity records."""
        db_path = "/data/data/de.dennisguse.opentracks/databases/database.db"
        tracks_table = "tracks"
        
        try:
            self.log_info("Clearing existing OpenTracks activity records...")
            adb_utils.execute_sql_command(
                db_path, 
                f"DELETE FROM {tracks_table};", 
                self.env_controller
            )
            self.log_info("Successfully cleared OpenTracks activity records")
        except Exception as e:
            self.log_error(f"Failed to clear OpenTracks activity records: {e}")
    
    def _add_activities(self, activities: List[Dict[str, Any]]) -> None:
        """Add custom activity records."""
        db_path = "/data/data/de.dennisguse.opentracks/databases/database.db"
        tracks_table = "tracks"
        device_timezone_str = self._get_device_timezone()
        device_tz = pytz.timezone(device_timezone_str)

        self.log_info(f"Preparing to add {len(activities)} activity records using timezone: {device_timezone_str}...")
        
        for activity in activities:
            try:
                # Required fields
                name = activity.get('name', '')
                category = activity.get('category', 'running')  # Default to 'running' if not provided
                description = activity.get('description', f'{name} activity')  # Provide a default description
                activity_type = category  # Keep activity_type same as category, as per original logic for now
                icon = f'activity_{category}'  # Set a default icon based on category

                # Time related
                start_date_str = activity.get('start_date', '')
                start_time_str = activity.get('start_time', '00:00')
                duration_mins = float(activity.get('duration_mins', 30))
                
                # Parse date and time
                if start_date_str:
                    try:
                        date_formats = ["%Y-%m-%d", "%B %d %Y", "%m/%d/%Y"]
                        parsed_date = None
                        
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.datetime.strptime(start_date_str, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if parsed_date is None:
                            raise ValueError(f"Cannot parse date format: {start_date_str}")
                            
                        start_date_str = parsed_date.strftime("%Y-%m-%d")
                    except Exception as e:
                        self.log_error(f"Date format conversion failed: {e}")
                        continue
                else:
                    # Use current date if not specified
                    start_date_str = datetime.datetime.now(device_tz).strftime("%Y-%m-%d")
                
                # Parse time
                try:
                    parsed_time = datetime.datetime.strptime(start_time_str, "%H:%M")
                    start_time_str = parsed_time.strftime("%H:%M")
                except ValueError:
                    self.log_error(f"Cannot parse time format: {start_time_str}")
                    start_time_str = "00:00"
                
                # Convert to unix timestamp (milliseconds)
                dt_str = f"{start_date_str} {start_time_str}"
                naive_dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                
                # Make datetime object timezone-aware
                aware_dt = device_tz.localize(naive_dt)
                starttime = int(aware_dt.timestamp() * 1000)
                
                # Get timezone offset in seconds (not milliseconds)
                starttime_offset = int(aware_dt.utcoffset().total_seconds())

                # Calculate end time (milliseconds)
                stoptime = starttime + int(duration_mins * 60 * 1000)
                totaltime = stoptime - starttime
                movingtime = totaltime  # Moving time usually close to total time
                
                # Distance and speed related
                total_distance = float(activity.get('distance', 0.0))  # Unit: meters
                
                # Prevent division by zero
                avg_speed = 0.0
                if totaltime > 0:
                    avg_speed = total_distance / (totaltime / 1000)
                
                # Elevation related
                elevation_gain = float(activity.get('elevation_gain', 0.0))
                elevation_loss = float(activity.get('elevation_loss', 0.0))
                
                # Generate UUID
                uuid_str = str(uuid.uuid4())
                
                # Build SQL insert command
                sql_command = f"""
                INSERT INTO {tracks_table} (
                    name, description, category, activity_type, 
                    starttime, stoptime, totaldistance, 
                    totaltime, movingtime, 
                    avgspeed, avgmovingspeed, 
                    elevationgain, elevationloss,
                    uuid, starttime_offset, icon
                ) VALUES (
                    '{name}', '{description}', '{category}', '{activity_type}',
                    {starttime}, {stoptime}, {total_distance},
                    {totaltime}, {movingtime},
                    {avg_speed}, {avg_speed},
                    {elevation_gain}, {elevation_loss},
                    '{uuid_str}', {starttime_offset}, '{icon}'
                );
                """
                
                # Execute SQL command
                adb_utils.execute_sql_command(
                    db_path, 
                    sql_command, 
                    self.env_controller
                )
                
                self.log_info(f"Successfully added activity record: {name} ({category})")
            except Exception as e:
                self.log_error(f"Failed to add activity record: {e}")
        
        self.log_info("Completed adding OpenTracks activity records")
    
    def _add_random_activities(self, random_count: int) -> None:
        """Add random activity records."""
        db_path = "/data/data/de.dennisguse.opentracks/databases/database.db"
        tracks_table = "tracks"
        device_timezone_str = self._get_device_timezone()
        device_tz = pytz.timezone(device_timezone_str)

        self.log_info(f"Preparing to add {random_count} random activity records using timezone: {device_timezone_str}...")
        
        # Activity type and name mapping
        category_to_names = {
            "Running": ["Morning Run", "Night Run", "Marathon Training", "Interval Run", "Long-distance Run"],
            "Cycling": ["Bike Commute", "Mountain Biking", "Road Cycling", "Leisure Cycling"],
            "Walking": ["Stroll", "Brisk Walking", "Hiking", "City Walk"],
            "Swimming": ["Freestyle", "Breaststroke", "Backstroke", "Butterfly", "Medley"],
            "Skiing": ["Alpine Skiing", "Cross-country Skiing", "Freestyle Skiing"],
            "Fitness": ["Strength Training", "HIIT Workout", "Cardio", "Yoga"],
            "Ball Sports": ["Basketball", "Soccer", "Tennis", "Volleyball"]
        }
        
        for i in range(random_count):
            try:
                # Randomly select activity type and name
                category = random.choice(list(category_to_names.keys()))
                name = random.choice(category_to_names[category])
                description = f"Random {name} activity"  # Default description for random activities
                activity_type = category
                icon = f'activity_{category}'

                # Generate random time (past 30 days)
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                
                now = datetime.datetime.now(device_tz)
                random_dt = now - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

                starttime = int(random_dt.timestamp() * 1000)
                starttime_offset = int(random_dt.utcoffset().total_seconds())

                # Random duration (15 minutes to 3 hours)
                duration_mins = random.randint(15, 180)
                stoptime = starttime + (duration_mins * 60 * 1000)
                totaltime = stoptime - starttime
                movingtime = totaltime
                
                # Random distance (based on different activity types)
                if category == "Running":
                    distance = random.uniform(1000, 15000)  # 1-15km
                elif category == "Cycling":
                    distance = random.uniform(5000, 50000)  # 5-50km
                elif category == "Walking":
                    distance = random.uniform(500, 8000)    # 0.5-8km
                elif category == "Swimming":
                    distance = random.uniform(100, 3000)    # 100-3000m
                else:
                    distance = random.uniform(1000, 10000)  # 1-10km
                
                # Calculate average speed
                avg_speed = distance / (totaltime / 1000) if totaltime > 0 else 0
                
                # Random elevation change
                elevation_gain = random.uniform(0, 500)
                elevation_loss = random.uniform(0, 500)
                
                # Generate UUID string
                uuid_str = str(uuid.uuid4())
                
                # Build SQL insert command
                sql_command = f"""
                INSERT INTO {tracks_table} (
                    name, description, category, activity_type, 
                    starttime, stoptime, totaldistance, 
                    totaltime, movingtime, 
                    avgspeed, avgmovingspeed, 
                    elevationgain, elevationloss,
                    uuid, starttime_offset, icon
                ) VALUES (
                    '{name}', '{description}', '{category}', '{activity_type}',
                    {starttime}, {stoptime}, {distance},
                    {totaltime}, {movingtime},
                    {avg_speed}, {avg_speed},
                    {elevation_gain}, {elevation_loss},
                    '{uuid_str}', {starttime_offset}, '{icon}'
                );
                """
                
                # Execute SQL command
                adb_utils.execute_sql_command(
                    db_path, 
                    sql_command, 
                    self.env_controller
                )
                
                self.log_info(f"Successfully added random activity record #{i+1}: {name} ({category})")
            except Exception as e:
                self.log_error(f"Failed to add random activity record: {e}")
        
        self.log_info("Completed adding OpenTracks random activity records")
