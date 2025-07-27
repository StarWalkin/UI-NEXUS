"""Core emulator initialization logic."""

import json
import logging
import os
import subprocess
import time
from typing import Any, Dict, Optional

from android_world.env import env_launcher, adb_utils

from .modules import (
    DateTimeConfigurator, ContactsConfigurator, SMSConfigurator, SystemConfigurator,
    CalendarConfigurator, RecipeConfigurator, TasksConfigurator, ExpenseConfigurator,
    MusicConfigurator, JoplinConfigurator, OsmAndConfigurator, AudioRecorderConfigurator,
    MarkorConfigurator, FilesConfigurator, OpenTracksConfigurator, GalleryConfigurator
)
from .utils.helpers import get_default_adb_path


class EmulatorInitializer:
    """Main class for initializing Android emulator based on configuration."""

    def __init__(
        self,
        config_path: str,
        console_port: int = 5554,
        adb_path: Optional[str] = None,
        grpc_port: int = 8554,
        emulator_setup: bool = False,
        device_serial: Optional[str] = None,
    ):
        """Initialize the emulator initializer.

        Args:
            config_path: Path to the configuration JSON file.
            console_port: Console port of the Android emulator.
            adb_path: Path to the ADB binary. If None, will use platform-specific default.
            grpc_port: Port for gRPC communication with the emulator.
            emulator_setup: Whether to perform first-time app setup.
        """
        self.config_path = config_path
        self.console_port = console_port
        self.adb_path = adb_path or get_default_adb_path()
        self.grpc_port = grpc_port
        self.emulator_setup = emulator_setup
        # Serial number of the target Android device. If provided and the
        # serial does not start with "emulator-", we will treat it as a
        # physical device.
        self.device_serial = device_serial
        self.config = self._load_config()
        self.env = None
        
        # Verify ADB path exists
        if not os.path.exists(self.adb_path):
            logging.warning(f"ADB path does not exist: {self.adb_path}")
            logging.warning("Please provide the correct path using --adb_path")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file.

        Returns:
            Dict containing configuration settings.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            json.JSONDecodeError: If the configuration file is not valid JSON.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def setup_environment(self) -> None:
        """Set up the Android environment."""
        logging.info('Setting up Android environment...')
        try:
            # Check if emulator is running via ADB
            adb_cmd = [self.adb_path, 'devices']
            try:
                result = subprocess.run(adb_cmd, capture_output=True, text=True, check=True)
                devices = result.stdout.strip()
                logging.info(f"Available devices: {devices}")
                
                # If we are targeting a physical device (device_serial is provided and
                # does not start with "emulator-"), skip the emulator presence check.
                if (not self.device_serial or self.device_serial.startswith("emulator-")) and "emulator" not in devices:
                    logging.error("No emulator found! Please start the emulator before running this script or provide a physical device serial via 'device_serial'.")
                    logging.error("Command: ~/Library/Android/sdk/emulator/emulator -avd EMULATOR_NAME -no-snapshot -grpc 8554")
                    raise RuntimeError("Emulator not running")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to run adb devices: {e}")
            
            # Try connecting to the environment
            try:
                self.env = env_launcher.load_and_setup_env(
                    console_port=self.console_port,
                    emulator_setup=self.emulator_setup,
                    freeze_datetime=False,  # We'll handle datetime setup ourselves
                    adb_path=self.adb_path,
                    grpc_port=self.grpc_port,
                    device_serial=self.device_serial,
                )
                logging.info('Android environment set up successfully.')
            except Exception as e:
                logging.error(f"Failed to connect to the Android environment: {e}")
                logging.error("\nPOSSIBLE SOLUTIONS:")
                logging.error("1. Make sure the emulator is running")
                logging.error("2. Ensure the emulator was started with: -grpc 8554")
                logging.error("3. Check if port 8554 is already in use (try: lsof -i :8554)")
                logging.error("4. Try temporarily disabling proxy settings (unset https_proxy http_proxy all_proxy)")
                logging.error("\nTo restart the emulator correctly:")
                logging.error("~/Library/Android/sdk/platform-tools/adb emu kill")
                logging.error("~/Library/Android/sdk/emulator/emulator -avd YOUR_AVD_NAME -no-snapshot -grpc 8554\n")
                raise
                
        except Exception as e:
            logging.error(f"Error setting up environment: {e}")
            raise

    def initialize(self) -> bool:
        """Initialize the emulator with all configured modules.

        Returns:
            True if initialization was successful, False otherwise.
        """
        logging.info("Beginning emulator initialization with config: %s", self.config_path)
        
        try:
            self.setup_environment()
            
            configuration_order = [
                ('datetime', DateTimeConfigurator),
                ('contacts', ContactsConfigurator),
                ('sms', SMSConfigurator),
                ('calendar', CalendarConfigurator),
                ('recipe', RecipeConfigurator),
                ('tasks', TasksConfigurator),
                ('expense', ExpenseConfigurator),
                ('music', MusicConfigurator),
                ('joplin', JoplinConfigurator),
                ('osmand', OsmAndConfigurator),
                ('audio_recorder', AudioRecorderConfigurator),
                ('markor', MarkorConfigurator),
                ('files', FilesConfigurator),
                ('opentracks', OpenTracksConfigurator),
                ('gallery', GalleryConfigurator),
                ('system', SystemConfigurator), 
            ]
            
            success_count = 0
            total_count = 0
            
            for config_key, configurator_class in configuration_order:
                if config_key in self.config:
                    total_count += 1
                    try:
                        logging.info(f"Configuring {config_key}...")
                        configurator = configurator_class(
                            self.env,  # Pass full env object instead of just controller
                            self.config[config_key]
                        )
                        if configurator.configure():
                            success_count += 1
                            logging.info(f"Successfully configured {config_key}")
                        else:
                            logging.error(f"Failed to configure {config_key}")
                    except Exception as e:
                        logging.error(f"Error configuring {config_key}: {e}")
            
            # Handle remaining configurations that might not be in the order list
            remaining_configs = set(self.config.keys()) - {item[0] for item in configuration_order}
            for config_key in remaining_configs:
                total_count += 1
                logging.warning(f"Configuration for '{config_key}' not found in configuration order")
                success_count += 1
            
            if success_count == total_count:
                logging.info("Emulator initialization completed successfully.")
                return True
            else:
                logging.warning(f"Emulator initialization completed with {total_count - success_count} failures.")
                return False
                
        except Exception as e:
            logging.error(f"Critical error during initialization: {e}")
            return False

    # Backward compatibility methods
    def configure_datetime(self) -> None:
        """Configure datetime settings (backward compatibility)."""
        if 'datetime' in self.config:
            configurator = DateTimeConfigurator(self.env, self.config['datetime'])
            configurator.configure()

    def configure_contacts(self) -> None:
        """Configure contacts (backward compatibility)."""
        if 'contacts' in self.config:
            configurator = ContactsConfigurator(self.env, self.config['contacts'])
            configurator.configure()

    def configure_sms(self) -> None:
        """Configure SMS messages (backward compatibility)."""
        if 'sms' in self.config:
            configurator = SMSConfigurator(self.env, self.config['sms'])
            configurator.configure()

    def configure_calendar(self) -> None:
        """Configure calendar events (backward compatibility)."""
        if 'calendar' in self.config:
            configurator = CalendarConfigurator(self.env, self.config['calendar'])
            configurator.configure()

    def configure_recipe(self) -> None:
        """Configure recipe app (backward compatibility)."""
        if 'recipe' in self.config:
            configurator = RecipeConfigurator(self.env, self.config['recipe'])
            configurator.configure()

    def configure_tasks(self) -> None:
        """Configure tasks app (backward compatibility)."""
        if 'tasks' in self.config:
            configurator = TasksConfigurator(self.env, self.config['tasks'])
            configurator.configure()

    def configure_expense(self) -> None:
        """Configure expense app (backward compatibility)."""
        if 'expense' in self.config:
            configurator = ExpenseConfigurator(self.env, self.config['expense'])
            configurator.configure()

    def configure_music(self) -> None:
        """Configure music app (backward compatibility)."""
        if 'music' in self.config:
            configurator = MusicConfigurator(self.env, self.config['music'])
            configurator.configure()

    def configure_joplin(self) -> None:
        """Configure Joplin app (backward compatibility)."""
        if 'joplin' in self.config:
            configurator = JoplinConfigurator(self.env, self.config['joplin'])
            configurator.configure()

    def configure_osmand(self) -> None:
        """Configure OsmAnd app (backward compatibility)."""
        if 'osmand' in self.config:
            configurator = OsmAndConfigurator(self.env, self.config['osmand'])
            configurator.configure()

    def configure_audio_recorder(self) -> None:
        """Configure audio recorder app (backward compatibility)."""
        if 'audio_recorder' in self.config:
            configurator = AudioRecorderConfigurator(self.env, self.config['audio_recorder'])
            configurator.configure()

    def configure_markor(self) -> None:
        """Configure Markor app (backward compatibility)."""
        if 'markor' in self.config:
            configurator = MarkorConfigurator(self.env, self.config['markor'])
            configurator.configure()

    def configure_files(self) -> None:
        """Configure files app (backward compatibility)."""
        if 'files' in self.config:
            configurator = FilesConfigurator(self.env, self.config['files'])
            configurator.configure()

    def configure_opentracks(self) -> None:
        """Configure OpenTracks app (backward compatibility)."""
        if 'opentracks' in self.config:
            configurator = OpenTracksConfigurator(self.env, self.config['opentracks'])
            configurator.configure()

    def configure_gallery(self) -> None:
        """Configure gallery app (backward compatibility)."""
        if 'gallery' in self.config:
            configurator = GalleryConfigurator(self.env, self.config['gallery'])
            configurator.configure()

    def configure_system(self) -> None:
        """Configure system settings (backward compatibility)."""
        if 'system' in self.config:
            configurator = SystemConfigurator(self.env, self.config['system'])
            configurator.configure() 