"""Common helper functions for emulator initialization."""

import datetime
import logging
import os
import platform
import time
from typing import Any, Dict, List, Optional

from android_world.env import adb_utils
from android_world.task_evals.utils import sqlite_schema_utils
from PIL import Image, ImageDraw, ImageFont

from .constants import APP_INFO, DATABASE_PATHS, DEFAULT_VALUES, FONT_PATHS


def get_all_package_names(env_controller) -> list[str]:
    """Get all installed package names from the device.
    
    Args:
        env_controller: Environment controller instance
        
    Returns:
        List of package names
    """
    try:
        cmd = ['shell', 'pm', 'list', 'packages']
        response = adb_utils.issue_generic_request(cmd, env_controller)
        output = response.generic.output.decode('utf-8', errors='ignore')
        
        # Parse the output - each line is in format "package:com.example.app"
        packages = []
        for line in output.strip().split('\n'):
            if line.startswith('package:'):
                package_name = line[8:].strip()  # Remove "package:" prefix
                packages.append(package_name)
        
        return packages
    except Exception as e:
        logging.error(f"Failed to get package names: {e}")
        return []


# Make this function available through adb_utils for backward compatibility
adb_utils.get_all_package_names = get_all_package_names


def set_root_if_needed(env_controller) -> None:
    """Set root permissions if needed.
    
    Args:
        env_controller: Environment controller instance
    """
    try:
        adb_utils.issue_generic_request(["root"], env_controller)
    except Exception as e:
        logging.warning(f"Failed to set root permissions: {e}")


# Make this function available through adb_utils for backward compatibility
adb_utils.set_root_if_needed = set_root_if_needed


def get_default_adb_path() -> str:
    """Get the default ADB path based on the current platform."""
    system = platform.system()
    home_dir = os.path.expanduser("~")
    
    if system == "Darwin":  # macOS
        return os.path.join(home_dir, "Library/Android/sdk/platform-tools/adb")
    elif system == "Linux":
        return os.path.join(home_dir, "Android/Sdk/platform-tools/adb")
    elif system == "Windows":
        return os.path.join(home_dir, "AppData/Local/Android/Sdk/platform-tools/adb.exe")
    else:
        from android_world.env import android_world_controller
        return android_world_controller.DEFAULT_ADB_PATH


def ensure_app_ready(app_key: str, env_controller) -> bool:
    """Ensure an app is installed and ready for configuration.
    
    Args:
        app_key: Key in APP_INFO dictionary
        env_controller: Environment controller instance
        
    Returns:
        True if app is ready, False otherwise
    """
    app_info = APP_INFO.get(app_key, {})
    package_name = app_info.get('package_name')
    app_name = app_info.get('display_name')
    
    if not package_name:
        logging.error(f"Unknown app key: {app_key}")
        return False
    
    # Check if app is installed
    try:
        all_packages = adb_utils.get_all_package_names(env_controller)
        if package_name not in all_packages:
            logging.error(f"App {package_name} is not installed! Please install it first.")
            return False
    except Exception as e:
        logging.error(f"Failed to check if app {package_name} is installed: {e}")
        return False
    
    # Ensure root permissions
    try:
        adb_utils.set_root_if_needed(env_controller)
    except Exception as e:
        logging.error(f"Failed to set root permissions: {e}")
        return False
    
    # Launch app if app_name is available
    if app_name:
        try:
            adb_utils.launch_app(app_name, env_controller)
            time.sleep(2)  # Wait for app to start
            adb_utils.press_home_button(env_controller)
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Failed to launch app {app_name}: {e}")
            logging.warning("Continuing with configuration...")
    
    return True


def check_database_exists(db_path: str, env_controller) -> bool:
    """Check if a database exists on the device.
    
    Args:
        db_path: Path to the database
        env_controller: Environment controller instance
        
    Returns:
        True if database exists, False otherwise
    """
    try:
        db_check_cmd = ['shell', f'ls {db_path}']
        db_check_response = adb_utils.issue_generic_request(db_check_cmd, env_controller)
        output = db_check_response.generic.output.decode('utf-8', errors='ignore')
        logging.info(f"Database check result for {db_path}: {output}")
        return "No such file" not in output
    except Exception as e:
        logging.warning(f"Unable to check if database exists {db_path}: {e}")
        return False


def clear_database_table(db_path: str, table_name: str, env_controller) -> bool:
    """Clear all records from a database table.
    
    Args:
        db_path: Path to the database
        table_name: Name of the table to clear
        env_controller: Environment controller instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info(f"Clearing database table: {table_name}")
        adb_utils.execute_sql_command(db_path, f"DELETE FROM {table_name};", env_controller)
        logging.info(f"Successfully cleared table {table_name}")
        return True
    except Exception as e:
        logging.error(f"Failed to clear table {table_name}: {e}")
        return False


def verify_table_count(db_path: str, table_name: str, env_controller) -> Optional[int]:
    """Verify the number of records in a table.
    
    Args:
        db_path: Path to the database
        table_name: Name of the table
        env_controller: Environment controller instance
        
    Returns:
        Number of records, or None if failed
    """
    try:
        count_cmd = ['shell', f'sqlite3 {db_path} "SELECT COUNT(*) FROM {table_name};"']
        count_response = adb_utils.issue_generic_request(count_cmd, env_controller)
        count_result = count_response.generic.output.decode('utf-8', errors='ignore').strip()
        return int(count_result) if count_result.isdigit() else None
    except Exception as e:
        logging.warning(f"Unable to verify table count for {table_name}: {e}")
        return None


def safe_sql_insert(db_path: str, table_name: str, data_obj, exclude_key: str, env_controller) -> bool:
    """Safely insert data into a database table.
    
    Args:
        db_path: Path to the database
        table_name: Name of the table
        data_obj: Data object to insert
        exclude_key: Key to exclude from insertion
        env_controller: Environment controller instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Generate SQL insert statement and values
        insert_sql, values = sqlite_schema_utils.insert_into_db(data_obj, table_name, exclude_key)
        
        # Get field names
        field_names = [field.name for field in data_obj.__dataclass_fields__.values() if field.name != exclude_key]
        
        # Handle special cases for reserved keywords
        columns_list = []
        for field_name in field_names:
            if field_name == 'order':
                columns_list.append('"[order]"')
            else:
                columns_list.append(f'"{field_name}"')
        
        columns = ','.join(columns_list)
        
        # Build SQL insert statement with proper escaping
        bind_values = []
        for value in values:
            if value is None or value == 'None':
                bind_values.append('NULL')
            elif isinstance(value, str):
                # Properly escape single quotes
                escaped_value = value.replace("'", "''")
                bind_values.append(f"'{escaped_value}'")
            else:
                bind_values.append(str(value))
        
        values_str = ','.join(bind_values)
        full_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values_str});"
        
        # Execute SQL command
        adb_utils.execute_sql_command(db_path, full_sql, env_controller)
        return True
        
    except Exception as e:
        logging.error(f"Failed to insert data into {table_name}: {e}")
        return False


def parse_datetime_string(date_str: str, time_str: str = "00:00") -> Optional[datetime.datetime]:
    """Parse date and time strings into datetime object.
    
    Args:
        date_str: Date string in various formats
        time_str: Time string in HH:MM format
        
    Returns:
        datetime object or None if parsing failed
    """
    date_formats = ["%Y-%m-%d", "%B %d %Y", "%m/%d/%Y"]
    
    for fmt in date_formats:
        try:
            dt_str = f"{date_str} {time_str}"
            combined_fmt = f"{fmt} %H:%M"
            return datetime.datetime.strptime(dt_str, combined_fmt)
        except ValueError:
            continue
    
    logging.error(f"Unable to parse date: {date_str}")
    return None


def get_font_path() -> str:
    """Get available font path for image generation.
    
    Returns:
        Path to usable font file
        
    Raises:
        RuntimeError: If no suitable font is found
    """
    for font_name in FONT_PATHS:
        try:
            font_path = ImageFont.truetype(font_name).path
            return font_path
        except (IOError, OSError):
            continue
    
    # Try default font
    try:
        return ImageFont.truetype().path
    except (IOError, OSError) as e:
        raise RuntimeError("No suitable font found for image generation") from e


def create_text_image(text: str, width: int = None, height: int = None, 
                      font_size: int = None) -> Image.Image:
    """Create an image with text content.
    
    Args:
        text: Text to render
        width: Image width (auto-calculated if None)
        height: Image height (auto-calculated if None)
        font_size: Font size (uses default if None)
        
    Returns:
        PIL Image object
    """
    if font_size is None:
        font_size = DEFAULT_VALUES['font_size']
    
    try:
        font = ImageFont.truetype(get_font_path(), font_size)
    except RuntimeError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    lines = text.split("\n")
    
    # Calculate dimensions if not provided
    if width is None or height is None:
        max_width = 0
        total_height = 0
        for line in lines:
            bbox = font.getbbox(line)
            max_width = max(max_width, bbox[2])
            if line.strip():  # Non-empty line
                total_height += bbox[3]
            else:  # Empty line (paragraph separator)
                total_height += font_size // 2
        
        if width is None:
            width = max_width + 20
        if height is None:
            height = total_height + 20
    
    # Create image
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw text
    y_text = 10
    for line in lines:
        if line.strip():
            draw.text((10, y_text), line, fill=(0, 0, 0), font=font)
            bbox = font.getbbox(line)
            y_text += bbox[3]
        else:
            y_text += font_size // 2
    
    return img


def ensure_directory_exists(path: str, env_controller) -> bool:
    """Ensure a directory exists on the device.
    
    Args:
        path: Directory path
        env_controller: Environment controller instance
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        mkdir_cmd = ['shell', f'mkdir -p {path}']
        adb_utils.issue_generic_request(mkdir_cmd, env_controller)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False


def trigger_media_scan(path: str, env_controller) -> None:
    """Trigger media scan for a specific path.
    
    Args:
        path: Path to scan
        env_controller: Environment controller instance
    """
    try:
        scan_cmd = f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{path}'
        adb_utils.issue_generic_request(['shell', scan_cmd], env_controller)
        time.sleep(1)  # Wait for scan to complete
    except Exception as e:
        logging.warning(f"Failed to trigger media scan for {path}: {e}")


def cleanup_temp_file(file_path: str) -> None:
    """Safely delete a temporary file.
    
    Args:
        file_path: Path to the temporary file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logging.warning(f"Failed to clean up temporary file {file_path}: {e}") 