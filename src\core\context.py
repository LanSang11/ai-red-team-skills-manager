"""Application context - shared state across all modules (singleton pattern)."""

from typing import Optional

from rich.console import Console

from .config import Config
from .logger import setup_logging, get_logger


class AppContext:
    """Singleton application context holding shared resources.

    Usage:
        ctx = AppContext()           # First call creates the instance
        ctx = AppContext()           # Subsequent calls return the same instance
        ctx.config.get("agents")    # Access config
        ctx.logger.info("...")      # Access logger
        ctx.console.print("...")    # Access rich console

        AppContext.reset()           # Reset singleton (for testing)
    """

    _instance: Optional["AppContext"] = None

    def __new__(cls, config_path: Optional[str] = None) -> "AppContext":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return
        self.config = Config(config_path)
        self.console = Console()
        self.logger = setup_logging(
            log_file=self.config.get("log_file"),
            debug=self.config.get("debug", False),
        )
        self._initialized = True

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (useful for testing)."""
        cls._instance = None

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the context has been initialized."""
        return cls._instance is not None and cls._instance._initialized
