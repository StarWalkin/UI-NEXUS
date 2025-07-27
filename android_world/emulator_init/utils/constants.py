"""Constants for emulator initialization."""

# Font paths for image generation
FONT_PATHS = [
    "arial.ttf",
    "Arial Unicode.ttf", 
    "Roboto-Regular.ttf",
    "DejaVuSans-Bold.ttf",
    "LiberationSans-Regular.ttf",
]

# Application package names and display names
APP_INFO = {
    'datetime': {
        'package_name': 'com.android.settings',
        'display_name': 'Settings'
    },
    'contacts': {
        'package_name': 'com.android.contacts',
        'display_name': 'Contacts'
    },
    'sms': {
        'package_name': 'com.android.messaging',
        'display_name': 'Messages'
    },
    'calendar': {
        'package_name': 'com.android.calendar',
        'display_name': 'Calendar'
    },
    'recipe': {
        'package_name': 'com.foodsquare.broccoli',
        'display_name': 'Broccoli',
        'db_path': '/data/data/com.foodsquare.broccoli/databases/broccoli.sqlite',
        'table_name': 'recipe'
    },
    'tasks': {
        'package_name': 'org.tasks',
        'display_name': 'Tasks',
        'db_path': '/data/data/org.tasks/databases/database',
        'table_name': 'tasks'
    },
    'expense': {
        'package_name': 'com.arduia.expense',
        'display_name': 'Pro Expense',
        'db_path': '/data/data/com.arduia.expense/databases/accounting.db',
        'table_name': 'expense'
    },
    'music': {
        'package_name': 'code.name.monkey.retromusic',
        'display_name': 'Retro Music',
        'playlist_db_path': '/data/data/code.name.monkey.retromusic/databases/playlist.db',
        'playback_db_path': '/data/data/code.name.monkey.retromusic/databases/music_playback_state.db'
    },
    'joplin': {
        'package_name': 'net.cozic.joplin',
        'display_name': 'Joplin',
        'db_path': '/data/data/net.cozic.joplin/databases/joplin.sqlite'
    },
    'osmand': {
        'package_name': 'net.osmand.plus',
        'display_name': 'OsmAnd',
        'favorites_path': '/data/data/net.osmand.plus/files/favourites.gpx'
    },
    'audio_recorder': {
        'package_name': 'com.dimowner.audiorecorder',
        'display_name': 'Audio Recorder',
        'data_path': '/storage/emulated/0/Android/data/com.dimowner.audiorecorder/files/Music/records'
    },
    'markor': {
        'package_name': 'net.gsantner.markor',
        'display_name': 'Markor',
        'data_path': '/storage/emulated/0/Documents/Markor'
    },
    'opentracks': {
        'package_name': 'de.dennisguse.opentracks',
        'display_name': 'Activity Tracker',
        'db_path': '/data/data/de.dennisguse.opentracks/databases/database.db',
        'table_name': 'tracks'
    },
    'gallery': {
        'data_path': '/storage/emulated/0/DCIM'
    },
    'files': {
        'base_path': '/storage/emulated/0'
    }
}

# Database table names and common paths
DATABASE_PATHS = {
    'sms': 'content://sms',
    'contacts': 'content://contacts',
    'music_directory': '/storage/emulated/0/Music',
    'documents_directory': '/storage/emulated/0/Documents',
    'downloads_directory': '/storage/emulated/0/Download',
    'pictures_directory': '/storage/emulated/0/Pictures'
}

# Default values for various configurations
DEFAULT_VALUES = {
    'random_expense_count': 5,
    'random_note_count': 10,
    'random_conversation_count': 3,
    'random_activity_count': 5,
    'random_file_count': 5,
    'font_size': 24,
    'ui_delay_sec': 1.0
} 