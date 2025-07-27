"""Base configurator class for emulator initialization modules."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..utils.helpers import ensure_app_ready


class BaseConfigurator(ABC):
    """Base class for all emulator configurators.
    
    This class provides common functionality and interface for all
    specific configurators (SMS, Calendar, etc.).
    """
    
    def __init__(self, env, config: Dict[str, Any]):
        """Initialize the configurator.
        
        Args:
            env: Android environment (AsyncEnv or env_controller depending on context)
            config: Configuration dictionary for this module
        """
        # Handle different types of environment objects
        if hasattr(env, 'base_env'):
            # This is a new AsyncAndroidEnv object
            self.env = env
            self.env_controller = env.base_env
        elif hasattr(env, 'controller'):
            # This is a full AsyncEnv object (old style)
            self.env = env
            self.env_controller = env.controller
        else:
            # This is just an env_controller
            self.env = None
            self.env_controller = env
            
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _ensure_environment(self) -> None:
        """Ensure the environment is properly initialized."""
        if not self.env_controller:
            raise RuntimeError("Environment not initialized. Call setup_environment() first.")
    
    def _ensure_app_ready(self, app_key: str) -> bool:
        """Ensure an app is ready for configuration.
        
        Args:
            app_key: App key from constants
            
        Returns:
            True if app is ready, False otherwise
        """
        return ensure_app_ready(app_key, self.env_controller)
    
    @abstractmethod
    def configure(self) -> bool:
        """Configure the module based on the provided configuration.
        
        Returns:
            True if configuration was successful, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def module_name(self) -> str:
        """Return the name of this configuration module."""
        pass
    
    def log_info(self, message: str) -> None:
        """Log an info message with module prefix."""
        self.logger.info(f"[{self.module_name}] {message}")
    
    def log_warning(self, message: str) -> None:
        """Log a warning message with module prefix."""
        self.logger.warning(f"[{self.module_name}] {message}")
    
    def log_error(self, message: str) -> None:
        """Log an error message with module prefix."""
        self.logger.error(f"[{self.module_name}] {message}")
    
    def log_debug(self, message: str) -> None:
        """Log a debug message with module prefix."""
        self.logger.debug(f"[{self.module_name}] {message}") 