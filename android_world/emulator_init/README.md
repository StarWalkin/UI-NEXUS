# Android Emulator Initialization System

This directory contains a Android emulator initialization system that allows you to configure various apps and system settings through JSON configuration files.

## Overview

The emulator initialization system provides a way to set up Android emulator environments with predefined states including contacts, SMS messages, calendar events, music files, notes, and system settings. This is particularly useful for creating consistent testing environments or preparing specific scenarios for application testing.

## Quick Start

### Prerequisites

1. Android emulator running with gRPC enabled
2. ADB (Android Debug Bridge) installed and accessible
3. Python environment with required dependencies

### Basic Usage

```bash
# Start your Android emulator with gRPC support
~/Library/Android/sdk/emulator/emulator -avd YOUR_AVD_NAME -no-snapshot -grpc 8554

# Change the current directory to UI-NEXUS/android_world 

# Run the initialization script
python emulator_init/emulator_init.py --config_path=task_config/Simple_Concatenation/10_contacts_markor.json
```

### Command Line Options

- `--config_path`: Path to configuration JSON file (required)
- `--console_port`: Console port of the Android emulator (default: 5554)
- `--adb_path`: Path to the ADB binary (auto-detected by default)
- `--grpc_port`: Port for gRPC communication with the emulator (default: 8554)
- `--emulator_setup`: Perform first-time app setup on the environment (default: False)
- `--device_serial`: Serial number of target Android device (optional, for physical devices)

## Configuration File Format

Configuration files are written in JSON format. Each top-level key corresponds to a specific app or system component that can be configured.

### Basic Structure

```json
{
  "datetime": { ... },
  "system": { ... },
  "contacts": { ... },
  "sms": { ... },
  "calendar": { ... },
  "music": { ... },
  "files": { ... },
  "markor": { ... }
}
```

## Supported Configurators

### 1. DateTime Configuration

Controls date, time, timezone, and time format settings.

```json
{
  "datetime": {
    "disable_auto_settings": true,
    "use_24_hour_format": true,
    "timezone": "Asia/Shanghai",
    "datetime": {
      "year": 2024,
      "month": 4,
      "day": 15,
      "hour": 14,
      "minute": 30,
      "second": 0
    }
  }
}
```

**Options:**
- `disable_auto_settings`: Disable automatic date/time from network
- `use_24_hour_format`: Use 24-hour time format
- `timezone`: Timezone string (e.g., "Asia/Shanghai", "America/New_York")
- `datetime`: Specific date and time to set

### 2. System Configuration

Controls system-level settings like WiFi, Bluetooth, brightness, and app management.

```json
{
  "system": {
    "wifi": "off",
    "bluetooth": "on",
    "brightness": "max",
    "airplane_mode": "off",
    "close_all_apps": true,
    "open_app": "com.android.settings",
    "clipboard": "Some text content"
  }
}
```

**Options:**
- `wifi`: "on" or "off"
- `bluetooth`: "on" or "off"
- `brightness`: "min", "max", or percentage value
- `airplane_mode`: "on" or "off"
- `close_all_apps`: Close all running applications
- `open_app`: Package name of app to open after configuration
- `clipboard`: Text content to set in clipboard

### 3. Contacts Configuration

Manages device contacts.

```json
{
  "contacts": {
    "clear_contacts": true,
    "add_contacts": [
      {
        "name": "Jane Smith",
        "number": "999888777"
      },
      {
        "name": "Michael Johnson",
        "number": "444555666"
      }
    ]
  }
}
```

**Options:**
- `clear_contacts`: Remove all existing contacts
- `add_contacts`: Array of contacts to add
  - `name`: Contact name
  - `number`: Phone number


### 4. SMS Configuration

Manages SMS messages.

```json
{
  "sms": {
    "clear_messages": true,
    "add_messages": [
      {
        "number": "123456789",
        "text": "When is our call scheduled for today?",
        "is_received": true
      }
    ]
  }
}
```

**Options:**
- `clear_messages`: Remove all existing SMS messages
- `add_messages`: Array of messages to add
  - `number`: Phone number
  - `text`: Message content
  - `is_received`: true for received messages, false for sent

### 5. Calendar Configuration

Manages calendar events.

```json
{
  "calendar": {
    "clear_events": true,
    "add_events": [
      {
        "title": "Team Meeting",
        "description": "Weekly team sync meeting",
        "location": "Conference Room A",
        "start_time": "2024-04-15T09:00:00",
        "duration_mins": 60
      }
    ]
  }
}
```

**Options:**
- `clear_events`: Remove all existing calendar events
- `add_events`: Array of events to add
  - `title`: Event title
  - `description`: Event description
  - `location`: Event location
  - `start_time`: ISO format datetime string
  - `duration_mins`: Duration in minutes

### 6. Music Configuration

Manages music library.

```json
{
  "music": {
    "clear_music": true,
    "add_music_files": [
      {
        "title": "Blinding Lights",
        "artist": "The Weeknd",
        "duration_ms": 200000
      }
    ]
  }
}
```

**Options:**
- `clear_music`: Remove all existing music files
- `add_music_files`: Array of music tracks to add
  - `title`: Song title
  - `artist`: Artist name
  - `duration_ms`: Duration in milliseconds

### 7. Files Configuration

Manages file system content.

```json
{
  "files": {
    "create_folders": [
      "Documents/Reference",
      "Download/Temp"
    ],
    "add_files": [
      {
        "name": "meeting_agenda.txt",
        "folder": "Documents/Reference",
        "content": "Meeting Agenda:\n1. Project updates\n2. Budget review"
      }
    ]
  }
}
```

**Options:**
- `create_folders`: Array of folder paths to create
- `add_files`: Array of files to create
  - `name`: File name
  - `folder`: Target folder path
  - `content`: File content

### 8. Markor Configuration

Manages Markor note-taking app content.

```json
{
  "markor": {
    "clear_notes": true,
    "add_folders": [
      {
        "title": "Templates"
      }
    ],
    "add_notes": [
      {
        "title": "important_reminder.md",
        "content": "# Important Reminder\n\nDon't forget...",
        "folder": "Templates"
      }
    ]
  }
}
```

**Options:**
- `clear_notes`: Remove all existing notes
- `add_folders`: Array of folders to create
  - `title`: Folder name
- `add_notes`: Array of notes to create
  - `title`: Note title (include .md extension)
  - `content`: Note content in Markdown format
  - `folder`: Target folder (empty string for root)

### 9. Recipe Configuration

Manages recipe app (Broccoli) content.

```json
{
  "recipe": {
    "clear_recipes": true,
    "add_recipes": [
      {
        "title": "Scrambled Eggs",
        "description": "Simple scrambled eggs",
        "servings": "1 serving",
        "preparationTime": "5 mins",
        "ingredients": "2 eggs\nMilk\nSalt\nButter",
        "directions": "Whisk eggs, milk, salt. Cook in butter.",
        "favorite": 0
      }
    ],
    "add_random_recipes": false
  }
}
```

**Options:**
- `clear_recipes`: Remove all existing recipes
- `add_recipes`: Array of recipes to add
  - `title`: Recipe title
  - `description`: Recipe description
  - `servings`: Number of servings
  - `preparationTime`: Preparation time
  - `ingredients`: Ingredients list (use \n for line breaks)
  - `directions`: Cooking directions
  - `favorite`: 1 for favorite, 0 for normal
- `add_random_recipes`: Add random sample recipes

### 10. Tasks Configuration

Manages Tasks app content for task management.

```json
{
  "tasks": {
    "clear_tasks": true,
    "add_tasks": [
      {
        "title": "Schedule dentist appointment",
        "importance": 2,
        "notes": "Call Dr. Smith's office for a checkup.",
        "due_date": "2024-04-18"
      }
    ],
    "add_random_tasks": false
  }
}
```

**Options:**
- `clear_tasks`: Remove all existing tasks
- `add_tasks`: Array of tasks to add
  - `title`: Task title
  - `importance`: Priority level (1-3, where 3 is highest)
  - `notes`: Task notes/description (optional)
  - `due_date`: Due date in YYYY-MM-DD format (optional)
- `add_random_tasks`: Add random sample tasks

### 11. Expense Configuration

Manages Pro Expense app for expense tracking.

```json
{
  "expense": {
    "clear_expenses": true,
    "add_expenses": [
      {
        "title": "Coffee",
        "amount": 4.50,
        "category": "Food",
        "date": "2024-04-15",
        "note": "Morning coffee at cafe"
      }
    ],
    "add_random_expenses": false,
    "random_expense_count": 5
  }
}
```

**Options:**
- `clear_expenses`: Remove all existing expenses
- `add_expenses`: Array of expenses to add
  - `title`: Expense title/description
  - `amount`: Expense amount (numeric)
  - `category`: Expense category
  - `date`: Date in YYYY-MM-DD format
  - `note`: Additional notes (optional)
- `add_random_expenses`: Add random sample expenses
- `random_expense_count`: Number of random expenses to add (default: 5)

### 12. Joplin Configuration

Manages Joplin note-taking app content.

```json
{
  "joplin": {
    "clear_notes": true,
    "add_folders": [
      {
        "title": "Work"
      },
      {
        "title": "Personal"
      }
    ],
    "add_notes": [
      {
        "title": "Meeting Notes",
        "body": "# Team Meeting Summary\n\nDiscussion points...",
        "folder": "Work",
        "is_todo": false,
        "todo_completed": false
      }
    ],
    "add_random_notes": false
  }
}
```

**Options:**
- `clear_notes`: Remove all existing notes and folders
- `add_folders`: Array of folders to create
  - `title`: Folder name
- `add_notes`: Array of notes to create
  - `title`: Note title
  - `body`: Note content in Markdown format
  - `folder`: Target folder name
  - `is_todo`: Whether this note is a todo item
  - `todo_completed`: Whether todo is completed (if is_todo is true)
- `add_random_notes`: Add random sample notes

### 13. OsmAnd Configuration

Manages OsmAnd navigation app favorites and locations.

```json
{
  "osmand": {
    "clear_favorites": true,
    "add_favorites": [
      {
        "name": "Home",
        "lat": 47.1663432,
        "lon": 9.5103085,
        "description": "My home location"
      }
    ],
    "add_random_favorites": false,
    "random_favorite_count": 3
  }
}
```

**Options:**
- `clear_favorites`: Remove all existing favorites
- `add_favorites`: Array of favorite locations to add
  - `name`: Location name
  - `lat`: Latitude coordinate
  - `lon`: Longitude coordinate  
  - `description`: Location description (optional)
- `add_random_favorites`: Add random sample locations from Liechtenstein
- `random_favorite_count`: Number of random favorites to add (default: 3)

### 14. Audio Recorder Configuration

Manages AudioRecorder app settings and recordings.

```json
{
  "audio_recorder": {
    "clear_recordings": true
  }
}
```

**Options:**
- `clear_recordings`: Remove all existing audio recordings

### 15. OpenTracks Configuration

Manages OpenTracks fitness tracking app activities.

```json
{
  "opentracks": {
    "clear_activities": true,
    "add_activities": [
      {
        "name": "Morning Run",
        "category": "running",
        "description": "Morning jog in the park",
        "start_date": "2024-04-14",
        "start_time": "07:30",
        "duration_mins": 35,
        "distance": 4500,
        "elevation_gain": 45,
        "elevation_loss": 45
      }
    ],
    "add_random_activities": false,
    "random_activity_count": 5
  }
}
```

**Options:**
- `clear_activities`: Remove all existing activities
- `add_activities`: Array of activities to add
  - `name`: Activity name
  - `category`: Activity type (e.g., "running", "cycling", "walking")
  - `description`: Activity description
  - `start_date`: Start date in YYYY-MM-DD format
  - `start_time`: Start time in HH:MM format
  - `duration_mins`: Duration in minutes
  - `distance`: Distance in meters
  - `elevation_gain`: Elevation gain in meters
  - `elevation_loss`: Elevation loss in meters
- `add_random_activities`: Add random sample activities
- `random_activity_count`: Number of random activities to add (default: 5)

### 16. Gallery Configuration

Manages Gallery app images.

```json
{
  "gallery": {
    "clear_images": true,
    "add_images": [
      {
        "filename": "expenses.jpg",
        "text": "Name, Amount, Category\nLunch, $35.80, Food\nMovie, $89.90, Entertainment"
      },
      {
        "filename": "photo.jpg",
        "src": "/path/to/existing/image.jpg",
        "path": "/storage/emulated/0/Pictures"
      }
    ]
  }
}
```

**Options:**
- `clear_images`: Remove all existing images from gallery
- `add_images`: Array of images to create and add
  - `filename`: Image filename (required, include extension)
  - `text`: Text content to generate as image (mutually exclusive with `src`)
  - `src`: Path to existing image file to copy (mutually exclusive with `text`) 