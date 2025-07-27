"""Gallery configuration for Android emulator."""

import os
import time
from typing import Dict, Any, List

from android_world.env import adb_utils
from android_world.utils import file_utils
from PIL import Image, ImageDraw, ImageFont

from .base_configurator import BaseConfigurator


class GalleryConfigurator(BaseConfigurator):
    """Configurator for Gallery images."""
    
    @property
    def module_name(self) -> str:
        return "Gallery"
    
    def configure(self) -> bool:
        """Configure gallery images based on configuration."""
        self._ensure_environment()
        
        self.log_info('Configuring Gallery...')
        
        try:
            # Gallery data path - using DCIM as default path
            gallery_path = "/storage/emulated/0/DCIM"
            
            # Clear existing images if specified
            if self.config.get('clear_images', False):
                self._clear_images(gallery_path)
            
            # Add images
            images = self.config.get('add_images', [])
            if images:
                self._add_images(images, gallery_path)
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to configure Gallery: {e}")
            return False
    
    def _clear_images(self, gallery_path: str) -> None:
        """Clear existing images."""
        try:
            self.log_info("Clearing gallery images...")
            adb_utils.issue_generic_request(['shell', f'rm -rf {gallery_path}/*'], self.env_controller)
            self.log_info("Successfully cleared gallery images")
        except Exception as e:
            self.log_error(f"Failed to clear gallery images: {e}")
    
    def _add_images(self, images: List[Dict[str, Any]], gallery_path: str) -> None:
        """Add images to gallery."""
        self.log_info(f"Preparing to add {len(images)} images to gallery...")
        
        for image_config in images:
            try:
                filename = image_config.get('filename')
                if not filename:
                    self.log_warning("Image configuration missing filename, skipping")
                    continue
                
                # Check image path
                path = image_config.get('path', gallery_path)
                
                # Handle image source
                if 'text' in image_config:
                    # Create image from text
                    self._create_text_image(image_config.get('text', ''), path, filename)
                elif 'src' in image_config:
                    # Copy existing image
                    src_path = image_config.get('src')
                    if os.path.exists(src_path):
                        self._copy_image_to_device(src_path, path, filename)
                    else:
                        self.log_warning(f"Source image does not exist: {src_path}, skipping")
                else:
                    self.log_warning(f"Image {filename} missing text or source path configuration, skipping")
                    
            except Exception as e:
                self.log_error(f"Failed to add image {filename}: {e}")
        
        # Trigger media scan to update gallery
        try:
            self.log_info("Triggering media scan to update gallery...")
            scan_cmd = 'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///storage/emulated/0/DCIM'
            adb_utils.issue_generic_request(['shell', scan_cmd], self.env_controller)
            
            # Also scan Pictures directory
            scan_cmd2 = 'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///storage/emulated/0/Pictures'
            adb_utils.issue_generic_request(['shell', scan_cmd2], self.env_controller)
            
            # Wait for media scan to complete
            time.sleep(1)
            self.log_info("Media scan completed")
        except Exception as e:
            self.log_error(f"Failed to trigger media scan: {e}")
    
    def _get_font_path(self) -> str:
        """Get available font path."""
        font_paths = [
            "arial.ttf",
            "Arial Unicode.ttf",
            "Roboto-Regular.ttf",
            "DejaVuSans-Bold.ttf",
            "LiberationSans-Regular.ttf",
        ]
        
        for font_name in font_paths:
            try:
                font_path = ImageFont.truetype(font_name).path
                return font_path
            except IOError:
                continue
        try:
            return ImageFont.truetype().path
        except IOError as e:
            raise RuntimeError("Cannot find suitable font.") from e
    
    def _create_text_image(self, text: str, path: str, filename: str, font_size: int = 24) -> None:
        """Create text image and save to device."""
        self.log_info(f"Creating text image: {filename}")
        
        # Ensure directory exists
        adb_utils.issue_generic_request(['shell', f'mkdir -p {path}'], self.env_controller)
        
        try:
            # Create text image
            font = ImageFont.truetype(self._get_font_path(), font_size)
            lines = text.split("\n")
            
            # Calculate dimensions
            max_width = 0
            total_height = 0
            for line in lines:
                bbox = font.getbbox(line)
                max_width = max(max_width, bbox[2])
                if line.strip():  # Non-empty line
                    total_height += bbox[3]
                else:  # Empty line (paragraph separator)
                    total_height += font_size // 2
            
            img_width = max_width + 20
            img_height = total_height + 20
            
            # Create image
            img = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Draw text
            y_text = 10
            for line in lines:
                if line.strip():
                    d.text((10, y_text), line, fill=(0, 0, 0), font=font)
                    bbox = font.getbbox(line)
                    y_text += bbox[3]
                else:
                    y_text += font_size // 2
            
            # Save to temporary location
            temp_path = f"/tmp/{filename}"
            img.save(temp_path)
            
            # Copy to device
            full_path = os.path.join(path, filename)
            adb_utils.issue_generic_request(['shell', f'rm -f {full_path}'], self.env_controller)
            file_utils.copy_data_to_device(temp_path, full_path, self.env_controller)
            
            # Delete temporary file
            os.remove(temp_path)
            
            self.log_info(f"Text image {filename} created and saved successfully")
        except Exception as e:
            self.log_error(f"Failed to create text image: {e}")
    
    def _copy_image_to_device(self, src_path: str, dest_path: str, filename: str) -> None:
        """Copy image to device."""
        self.log_info(f"Copying image {src_path} to device")
        
        # Ensure directory exists
        adb_utils.issue_generic_request(['shell', f'mkdir -p {dest_path}'], self.env_controller)
        
        try:
            # Copy to device
            full_path = os.path.join(dest_path, filename)
            adb_utils.issue_generic_request(['shell', f'rm -f {full_path}'], self.env_controller)
            file_utils.copy_data_to_device(src_path, full_path, self.env_controller)
            
            self.log_info(f"Image {filename} copied successfully")
        except Exception as e:
            self.log_error(f"Failed to copy image: {e}") 