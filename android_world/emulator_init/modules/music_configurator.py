"""Music configuration for Android emulator."""

import os
import random
import time
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.task_evals.utils import user_data_generation

from .base_configurator import BaseConfigurator


class MusicConfigurator(BaseConfigurator):
    """Configurator for RetroMusic app."""
    
    @property
    def module_name(self) -> str:
        return "Music"
    
    def configure(self) -> bool:
        """Configure music app based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring RetroMusic settings...')
        
        try:
            # Setup music app
            if not self._setup_music_app():
                return False
            
            # Clear existing music if specified
            if self.config.get('clear_music', False):
                self._clear_music()
            
            # Add music files
            music_files = self.config.get('add_music_files', [])
            if music_files:
                added_count = self._add_music_files(music_files)
                self.log_info(f"Successfully added {added_count} music files")
                
                # Scan music directory to update media library
                self._scan_music_directory()
            
            # Create playlists
            playlists = self.config.get('add_playlists', [])
            if playlists:
                self._create_playlists(playlists)
            
            # Set queue
            queue_songs = self.config.get('set_queue', [])
            if queue_songs:
                self._set_queue(queue_songs)
            
            # Restart app to ensure changes take effect
            self._restart_music_app()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure music app: {e}")
            return False
    
    def _setup_music_app(self) -> bool:
        """Setup and verify music app."""
        app_name = 'retro music'
        package_name = 'code.name.monkey.retromusic'
        
        try:
            all_packages = adb_utils.get_all_package_names(self.env_controller)
            if package_name not in all_packages:
                self.log_error("Retro Music app is not installed! Please install it first.")
                return False
            
            # Ensure root permissions
            adb_utils.set_root_if_needed(self.env_controller)
            
            # Launch app
            adb_utils.launch_app(app_name, self.env_controller)
            time.sleep(2)  # Wait for app to start
            
            # Return to home screen
            adb_utils.press_home_button(self.env_controller)
            time.sleep(1)
            
            return True
        except Exception as e:
            self.log_error(f"Error setting up music app: {e}")
            return False
    
    def _clear_music(self) -> None:
        """Clear existing music files and playlists."""
        music_directory = '/storage/emulated/0/Music'
        playlist_db_path = '/data/data/code.name.monkey.retromusic/databases/playlist.db'
        
        try:
            self.log_info("Clearing all existing music files and playlists")
            
            # Clear music directory
            clear_dir_cmd = ['shell', f'rm -rf {music_directory}/*']
            adb_utils.issue_generic_request(clear_dir_cmd, self.env_controller)
            self.log_info("Cleared device music directory")
            
            # Ensure music directory exists
            mkdir_cmd = ['shell', f'mkdir -p {music_directory}']
            adb_utils.issue_generic_request(mkdir_cmd, self.env_controller)
            
            # Clear playlist databases
            self._clear_playlist_dbs(playlist_db_path)
            self.log_info("Cleared playlist databases")
        except Exception as e:
            self.log_error(f"Failed to clear music files and playlists: {e}")
    
    def _add_music_files(self, music_files: List[Dict[str, Any]]) -> int:
        """Add music files to device."""
        music_directory = '/storage/emulated/0/Music'
        added_files = 0
        
        for music_file in music_files:
            try:
                title = music_file.get('title', '')
                artist = music_file.get('artist', 'Unknown Artist')
                duration_ms = music_file.get('duration_ms', random.randint(3 * 60 * 1000, 5 * 60 * 1000))
                file_name = f"{title}.mp3" if title else f"music_{random.randint(1, 1000)}.mp3"
                
                # Write MP3 file to device
                if self.env:
                    # Use full env object if available
                    user_data_generation.write_mp3_file_to_device(
                        os.path.join(music_directory, file_name),
                        self.env,
                        title=title,
                        artist=artist,
                        duration_milliseconds=duration_ms
                    )
                else:
                    # Fallback: if we only have env_controller, we can't use write_mp3_file_to_device
                    self.log_error("Cannot add music files: full env object not available")
                    break
                
                self.log_debug(f"Added music file: {title} - {artist}")
                added_files += 1
            except Exception as e:
                # Only log this as debug if it's due to file name issues with special characters
                if "syntax error" in str(e).lower():
                    self.log_debug(f"Skipped music file '{music_file.get('title', 'Unknown')}' due to special characters in filename")
                else:
                    self.log_error(f"Failed to add music file '{music_file.get('title', 'Unknown')}': {e}")
        
        return added_files
    
    def _scan_music_directory(self) -> None:
        """Scan music directory to update media library."""
        try:
            action = 'android.intent.action.MEDIA_SCANNER_SCAN_FILE'
            data_uri = 'file:///storage/emulated/0/Music'
            
            adb_utils.send_android_intent(
                command='broadcast', 
                action=action, 
                env=self.env_controller, 
                data_uri=data_uri
            )
            
            # Close RetroMusic app
            adb_utils.close_app('retro music', self.env_controller)
            self.log_info("Successfully scanned music directory, media library updated")
            time.sleep(2)  # Wait for scan to complete
        except Exception as e:
            self.log_error(f"Failed to scan music directory: {e}")
    
    def _create_playlists(self, playlists: List[Dict[str, Any]]) -> None:
        """Create playlists."""
        playlist_db_path = '/data/data/code.name.monkey.retromusic/databases/playlist.db'
        added_playlists = 0
        
        # Restart RetroMusic app
        adb_utils.launch_app('retro music', self.env_controller)
        time.sleep(2)
        
        # Get song info map
        try:
            song_info_map = self._get_song_info_map()
            self.log_info(f"Retrieved {len(song_info_map)} songs from media library")
        except Exception as e:
            self.log_error(f"Failed to get media library info: {e}")
            song_info_map = {}
        
        # Global unique song_key counter
        song_key_counter = 10000
        
        for playlist in playlists:
            try:
                playlist_name = playlist.get('name', '')
                songs = playlist.get('songs', [])
                
                if not playlist_name or not songs:
                    continue
                
                self.log_info(f"Creating playlist: {playlist_name} with {len(songs)} songs")
                
                # Create playlist record
                playlist_id = int(time.time() * 1000)  # Use timestamp as playlist ID
                
                # Insert playlist to PlaylistEntity table
                playlist_insert_sql = f"""
                INSERT INTO PlaylistEntity (playlist_id, playlist_name)
                VALUES ({playlist_id}, '{playlist_name}');
                """
                adb_utils.execute_sql_command(playlist_db_path, playlist_insert_sql, self.env_controller)
                
                # Create SongEntity records for each song
                for i, song_name in enumerate(songs):
                    current_song_key = song_key_counter + i
                    
                    # Try to get song info from media library
                    song_info = song_info_map.get(song_name)
                    
                    if song_info:
                        # Use real song info
                        song_id = song_info.get('id', i + 1)
                        track_number = song_info.get('track_number', i + 1)
                        year = song_info.get('year', 2023)
                        duration = song_info.get('duration', 180000)
                        data_path = song_info.get('data', f"/storage/emulated/0/Music/{song_name}.mp3")
                        date_modified = song_info.get('date_modified', int(time.time()))
                        album_id = song_info.get('album_id', 1)
                        album_name = song_info.get('album_name', 'Unknown Album')
                        artist_id = song_info.get('artist_id', 1)
                        artist_name = song_info.get('artist_name', 'Unknown Artist')
                        composer = song_info.get('composer', '')
                        album_artist = song_info.get('album_artist', '')
                    else:
                        # Create default values
                        song_id = current_song_key
                        track_number = i + 1
                        year = 2023
                        duration = 180000
                        data_path = f"/storage/emulated/0/Music/{song_name}.mp3"
                        date_modified = int(time.time())
                        album_id = song_id
                        album_name = 'Unknown Album'
                        artist_id = song_id
                        artist_name = 'Unknown Artist'
                        composer = ''
                        album_artist = ''
                    
                    # Create complete SongEntity record
                    song_insert_sql = f"""
                    INSERT INTO SongEntity (
                        playlist_creator_id, song_key, id, title, track_number, year, 
                        duration, data, date_modified, album_id, album_name, 
                        artist_id, artist_name, composer, album_artist
                    ) VALUES (
                        {playlist_id}, {current_song_key}, {song_id}, '{song_name}', {track_number}, {year}, 
                        {duration}, '{data_path}', {date_modified}, {album_id}, '{album_name}', 
                        {artist_id}, '{artist_name}', '{composer}', '{album_artist}'
                    );
                    """
                    adb_utils.execute_sql_command(playlist_db_path, song_insert_sql, self.env_controller)
                
                # Update song_key_counter
                song_key_counter += len(songs) + 1000
                
                added_playlists += 1
                self.log_info(f"Successfully created playlist: {playlist_name} with {len(songs)} songs")
            except Exception as e:
                self.log_error(f"Failed to create playlist '{playlist.get('name', 'Unknown')}': {e}")
        
        self.log_info(f"Successfully created {added_playlists} playlists")
    
    def _set_queue(self, queue_songs: List[str]) -> None:
        """Set playback queue."""
        playback_db_path = '/data/data/code.name.monkey.retromusic/databases/music_playback_state.db'
        
        try:
            self.log_info(f"Setting playback queue with {len(queue_songs)} songs")
            
            # Clear existing queue
            clear_queue_sql = "DELETE FROM playing_queue;"
            adb_utils.execute_sql_command(playback_db_path, clear_queue_sql, self.env_controller)
            
            # Get song info map
            song_info_map = self._get_song_info_map()
            
            # Add each song to playback queue
            for i, song_name in enumerate(queue_songs):
                song_info = song_info_map.get(song_name)
                
                if song_info:
                    # Use real song info
                    song_id = song_info.get('id', i + 1)
                    track_number = song_info.get('track_number', i + 1)
                    year = song_info.get('year', 2023)
                    duration = song_info.get('duration', 180000)
                    data_path = song_info.get('data', f"/storage/emulated/0/Music/{song_name}.mp3")
                    date_modified = song_info.get('date_modified', int(time.time()))
                    album_id = song_info.get('album_id', 1)
                    album_name = song_info.get('album_name', 'Unknown Album')
                    artist_id = song_info.get('artist_id', 1)
                    artist_name = song_info.get('artist_name', 'Unknown Artist')
                    composer = song_info.get('composer', '')
                    album_artist = song_info.get('album_artist', '')
                else:
                    # Create default values
                    song_id = i + 1000
                    track_number = i + 1
                    year = 2023
                    duration = 180000
                    data_path = f"/storage/emulated/0/Music/{song_name}.mp3"
                    date_modified = int(time.time())
                    album_id = song_id
                    album_name = 'Unknown Album'
                    artist_id = song_id
                    artist_name = 'Unknown Artist'
                    composer = ''
                    album_artist = ''
                
                # Use correct column structure
                queue_insert_sql = f"""
                INSERT INTO playing_queue (
                    _id, title, track, year, duration, 
                    _data, date_modified, album_id, album, 
                    artist_id, artist, composer, album_artist
                ) VALUES (
                    {song_id}, '{song_name}', {track_number}, {year}, {duration}, 
                    '{data_path}', {date_modified}, {album_id}, '{album_name}', 
                    {artist_id}, '{artist_name}', '{composer}', '{album_artist}'
                );
                """
                adb_utils.execute_sql_command(playback_db_path, queue_insert_sql, self.env_controller)
            
            self.log_info(f"Successfully set playback queue with {len(queue_songs)} songs")
        except Exception as e:
            self.log_error(f"Failed to set playback queue: {e}")
    
    def _clear_playlist_dbs(self, playlist_db_path: str) -> None:
        """Clear all playlist-related databases."""
        try:
            adb_utils.execute_sql_command(
                playlist_db_path, 
                "DELETE FROM PlaylistEntity;", 
                self.env_controller
            )
            self.log_info("Cleared PlaylistEntity table")
            
            adb_utils.execute_sql_command(
                playlist_db_path, 
                "DELETE FROM SongEntity;", 
                self.env_controller
            )
            self.log_info("Cleared SongEntity table")
        except Exception as e:
            self.log_error(f"Failed to clear playlist database tables: {e}")
    
    def _get_song_info_map(self) -> dict:
        """Get song info mapping from media library."""
        try:
            song_info_map = {}
            
            # Query media library content provider for song info
            cmd = [
                'shell', 
                'content query --uri content://media/external/audio/media'
            ]
            response = adb_utils.issue_generic_request(cmd, self.env_controller)
            output = response.generic.output.decode('utf-8', errors='ignore')
            
            # Parse output
            current_song = {}
            current_title = None
            
            for line in output.splitlines():
                if line.strip().startswith('Row:'):
                    # New song record
                    if current_title and current_song:
                        song_info_map[current_title] = current_song
                    current_song = {}
                    current_title = None
                elif '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'title':
                        current_title = value
                    
                    current_song[key] = value
            
            # Add last song
            if current_title and current_song:
                song_info_map[current_title] = current_song
                
            return song_info_map
        except Exception as e:
            self.log_error(f"Failed to get song info: {e}")
            return {}
    
    def _restart_music_app(self) -> None:
        """Restart music app to refresh UI."""
        try:
            adb_utils.launch_app('retro music', self.env_controller)
            self.log_info("Restarted RetroMusic app to refresh UI")
        except Exception as e:
            self.log_warning(f"Failed to restart RetroMusic app: {e}") 