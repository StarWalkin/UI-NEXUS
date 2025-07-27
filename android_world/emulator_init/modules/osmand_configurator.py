"""OsmAnd configuration for Android emulator."""

import os
import time
from typing import Dict, Any, List
from xml.etree import ElementTree

from android_world.env import adb_utils
from android_world.utils import file_utils

from .base_configurator import BaseConfigurator


class OsmAndConfigurator(BaseConfigurator):
    """Configurator for OsmAnd map app."""
    
    # Constants from osmand.py
    _DEVICE_FILES = '/data/media/0/Android/data/net.osmand/files'
    _LEGACY_FILES = '/data/data/net.osmand/files'
    _FAVORITES_PATH = os.path.join(_DEVICE_FILES, 'favorites/favorites.gpx')
    _LEGACY_FAVORITES_PATH = os.path.join(_LEGACY_FILES, 'favourites_bak.gpx')
    _BACKUP_DIR_PATH = os.path.join(_LEGACY_FILES, 'backup')
    
    _FAVORITES_XML_NAMESPACES = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    # Predefined locations (Liechtenstein locations from osmand.py)
    _PRELOADED_MAP_LOCATIONS = {
        'Balzers, Liechtenstein': (47.0688832, 9.5061564),
        'Bendern, Liechtenstein': (47.2122151, 9.5062101),
        'Malbun, Liechtenstein': (47.1026191, 9.6083057),
        'Nendeln, Liechtenstein': (47.1973857, 9.5430636),
        'Oberplanken, Liechtenstein': (47.1784977, 9.5450163),
        'Planken, Liechtenstein': (47.1858882, 9.5452201),
        'Rotenboden, Liechtenstein': (47.1275785, 9.5387131),
        'Ruggell, Liechtenstein': (47.23976, 9.5262837),
        'Schaan, Liechtenstein': (47.1663432, 9.5103085),
        'Schaanwald, Liechtenstein': (47.2165476, 9.5699984),
        'Schönberg, Liechtenstein': (47.1303814, 9.5930117),
        'Triesen, Liechtenstein': (47.106997, 9.5274854),
    }
    
    @property
    def module_name(self) -> str:
        return "OsmAnd"
    
    def configure(self) -> bool:
        """Configure OsmAnd app based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring OsmAnd map app...')
        
        try:
            # Setup OsmAnd app
            if not self._setup_osmand_app():
                return False
            
            # Initialize the app to create necessary files
            self._initialize_app()
            
            # Clear data if specified
            if self.config.get('clear_favorites', False):
                self._clear_favorites()
            
            # Add favorites
            favorites = self.config.get('add_favorites', [])
            if favorites:
                self._add_favorites(favorites)
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure OsmAnd app: {e}")
            return False
    
    def _setup_osmand_app(self) -> bool:
        """Setup and verify OsmAnd app."""
        package_name = 'net.osmand'  # Correct package name
        
        try:
            # Check if app is installed
            all_packages = adb_utils.get_all_package_names(self.env_controller)
            if package_name not in all_packages:
                self.log_warning("OsmAnd app is not installed! Skipping configuration.")
                return False
            
            return True
        except Exception as e:
            self.log_error(f"Error setting up OsmAnd app: {e}")
            return False
    
    def _initialize_app(self) -> None:
        """Initialize OsmAnd app to create necessary directories and files."""
        self.log_info("Initializing OsmAnd app...")
        adb_utils.launch_app("OsmAnd", self.env_controller)
        time.sleep(3)  # Wait for app to initialize
        adb_utils.close_app("OsmAnd", self.env_controller)
        time.sleep(1)
    
    def _clear_favorites(self) -> None:
        """Clear existing favorite locations using the same method as osmand.py."""
        self.log_info("Clearing OsmAnd favorite locations...")
        
        try:
            # Clear backup directory
            file_utils.clear_directory(self._BACKUP_DIR_PATH, self.env_controller)
            
            # Clear favorites files
            for path in [self._FAVORITES_PATH, self._LEGACY_FAVORITES_PATH]:
                if file_utils.check_file_exists(path, self.env_controller):
                    with file_utils.tmp_file_from_device(path, self.env_controller) as favorites_file:
                        tree = ElementTree.parse(favorites_file)
                        for waypoint in tree.findall('gpx:wpt', self._FAVORITES_XML_NAMESPACES):
                            tree.getroot().remove(waypoint)
                        tree.write(favorites_file)
                        file_utils.copy_data_to_device(favorites_file, path, self.env_controller)
                    self.log_info(f"Cleared favorites from {path}")
                else:
                    self.log_info(f"Favorites file {path} not found, creating new one")
                    
            self.log_info("Successfully cleared OsmAnd favorite locations")
        except Exception as e:
            self.log_error(f"Failed to clear OsmAnd favorite locations: {e}")
    
    def _add_favorites(self, favorites: List[Dict[str, Any]]) -> None:
        """Add favorite locations using GPX XML format."""
        self.log_info(f"Adding {len(favorites)} favorite locations to OsmAnd...")
        
        for favorite in favorites:
            name = favorite.get('name', 'Unnamed Location')
            
            # Check if it's a predefined location
            if name in self._PRELOADED_MAP_LOCATIONS and 'lat' not in favorite and 'lon' not in favorite:
                lat, lon = self._PRELOADED_MAP_LOCATIONS[name]
            else:
                # Use custom coordinates
                lat = favorite.get('lat')
                lon = favorite.get('lon')
                
                if lat is None or lon is None:
                    self.log_error(f"Failed to add favorite location '{name}': missing coordinates")
                    continue
            
            try:
                self._add_single_favorite(name, lat, lon)
                self.log_info(f"Successfully added favorite location: {name} ({lat}, {lon})")
            except Exception as e:
                self.log_error(f"Failed to add favorite location '{name}': {e}")
    
    def _add_single_favorite(self, name: str, lat: float, lon: float) -> None:
        """Add a single favorite location to the GPX file."""
        # Try to add to the main favorites path first
        favorites_path = self._FAVORITES_PATH
        
        # Ensure the favorites directory exists
        favorites_dir = os.path.dirname(favorites_path)
        self._ensure_directory_exists(favorites_dir)
        
        # Check if favorites file exists, if not create it
        if not file_utils.check_file_exists(favorites_path, self.env_controller):
            self._create_empty_favorites_file(favorites_path)
        
        # Add the waypoint to the GPX file
        with file_utils.tmp_file_from_device(favorites_path, self.env_controller) as favorites_file:
            try:
                tree = ElementTree.parse(favorites_file)
                root = tree.getroot()
            except ElementTree.ParseError:
                # Create new GPX structure if file is corrupted
                root = self._create_gpx_root()
                tree = ElementTree.ElementTree(root)
            
            # Create waypoint element
            waypoint = ElementTree.SubElement(root, 'wpt', {
                'lat': str(lat),
                'lon': str(lon)
            })
            
            # Add name element
            name_elem = ElementTree.SubElement(waypoint, 'name')
            name_elem.text = name
            
            # Add description element (optional)
            desc_elem = ElementTree.SubElement(waypoint, 'desc')
            desc_elem.text = f'Favorite location: {name}'
            
            # Write back to file
            tree.write(favorites_file, encoding='utf-8', xml_declaration=True)
            file_utils.copy_data_to_device(favorites_file, favorites_path, self.env_controller)
    
    def _ensure_directory_exists(self, directory_path: str) -> None:
        """Ensure a directory exists on the device."""
        try:
            adb_utils.issue_generic_request(
                ['shell', 'mkdir', '-p', directory_path], 
                self.env_controller
            )
        except Exception as e:
            self.log_error(f"Failed to create directory {directory_path}: {e}")
    
    def _create_empty_favorites_file(self, file_path: str) -> None:
        """Create an empty GPX favorites file."""
        self.log_info(f"Creating new favorites file: {file_path}")
        
        # Create GPX content
        root = self._create_gpx_root()
        tree = ElementTree.ElementTree(root)
        
        # Write to temporary file and copy to device
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_file:
            tree.write(temp_file.name, encoding='utf-8', xml_declaration=True)
            file_utils.copy_data_to_device(temp_file.name, file_path, self.env_controller)
        
        # Clean up temporary file
        os.unlink(temp_file.name)
    
    def _create_gpx_root(self) -> ElementTree.Element:
        """Create a GPX root element with proper namespace."""
        root = ElementTree.Element('gpx', {
            'version': '1.1',
            'creator': 'OsmAnd',
            'xmlns': 'http://www.topografix.com/GPX/1/1'
        })
        return root 