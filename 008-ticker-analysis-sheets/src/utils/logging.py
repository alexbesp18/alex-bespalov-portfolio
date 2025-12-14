import logging
import sys
from typing import Optional

def setup_logger(name: str = "ticker_analysis", level: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a standard logger.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). 
               Defaults to INFO or settings.LOG_LEVEL.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist or force reconfiguration
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Set level
        if level is None:
            # Avoid circular import if possible, or use standard default
            level = "INFO"
            
        logger.setLevel(level.upper())
        
    return logger
