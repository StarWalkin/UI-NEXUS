"""Audio Recorder configuration for Android emulator."""

from android_world.env import adb_utils

from .base_configurator import BaseConfigurator


class AudioRecorderConfigurator(BaseConfigurator):
    """Configurator for AudioRecorder app."""
    
    @property
    def module_name(self) -> str:
        return "AudioRecorder"
    
    def configure(self) -> bool:
        """Configure audio recorder app based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring AudioRecorder app...')
        
        try:
            # Setup audio recorder app
            if not self._setup_audio_recorder_app():
                return False
            
            # Clear existing recordings if specified
            if self.config.get('clear_recordings', False):
                self._clear_recordings()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure audio recorder app: {e}")
            return False
    
    def _setup_audio_recorder_app(self) -> bool:
        """Setup and verify audio recorder app."""
        package_name = 'com.dimowner.audiorecorder'
        
        try:
            # Check if app is installed
            all_packages = adb_utils.get_all_package_names(self.env_controller)
            if package_name not in all_packages:
                self.log_warning("AudioRecorder app is not installed! Skipping configuration.")
                return False
            
            # Set root permissions
            adb_utils.set_root_if_needed(self.env_controller)
            return True
        except Exception as e:
            self.log_error(f"Error setting up AudioRecorder app: {e}")
            return False
    
    def _clear_recordings(self) -> None:
        """Clear existing recordings."""
        audiorecorder_data = "/storage/emulated/0/Android/data/com.dimowner.audiorecorder/files/Music/records"
        
        try:
            self.log_info("Clearing AudioRecorder existing recordings...")
            
            # Check if directory exists
            check_dir_cmd = ['shell', f'ls -la {audiorecorder_data} 2>/dev/null || echo "not_found"']
            check_dir_response = adb_utils.issue_generic_request(check_dir_cmd, self.env_controller)
            check_result = check_dir_response.generic.output.decode('utf-8', errors='ignore').strip()
            
            if "not_found" in check_result:
                self.log_info(f"AudioRecorder directory does not exist, creating: {audiorecorder_data}")
                create_dir_cmd = ['shell', f'mkdir -p {audiorecorder_data}']
                adb_utils.issue_generic_request(create_dir_cmd, self.env_controller)
            else:
                # Clear recording files
                clear_cmd = ['shell', f'rm -f {audiorecorder_data}/*.m4a {audiorecorder_data}/*.wav {audiorecorder_data}/*.3gp']
                adb_utils.issue_generic_request(clear_cmd, self.env_controller)
                self.log_info("Successfully cleared AudioRecorder recordings")
            
        except Exception as e:
            self.log_error(f"Failed to clear AudioRecorder recordings: {e}") 