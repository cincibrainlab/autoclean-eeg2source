"""Logging configuration utilities."""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logger(
    name: str = "autoclean_eeg2source",
    level: str = "INFO",
    log_file: Optional[str] = None,
    colorize: bool = True
) -> logging.Logger:
    """
    Setup logger with colorful console output.
    
    Parameters
    ----------
    name : str
        Logger name
    level : str
        Logging level (DEBUG, INFO, WARNING, ERROR)
    log_file : str, optional
        Path to log file
    colorize : bool
        Whether to colorize console output
        
    Returns
    -------
    logger : logging.Logger
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    
    if colorize:
        try:
            from loguru import logger as loguru_logger
            # Use loguru for colorful output
            class ColoredFormatter(logging.Formatter):
                colors = {
                    'DEBUG': '\033[36m',  # Cyan
                    'INFO': '\033[32m',   # Green
                    'WARNING': '\033[33m',  # Yellow
                    'ERROR': '\033[31m',  # Red
                    'CRITICAL': '\033[35m',  # Magenta
                }
                reset = '\033[0m'
                
                def format(self, record):
                    levelname = record.levelname
                    if levelname in self.colors:
                        levelname_color = f"{self.colors[levelname]}{levelname}{self.reset}"
                        record.levelname = levelname_color
                    return super().format(record)
            
            console_formatter = ColoredFormatter(
                '%(levelname)s | %(asctime)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        except ImportError:
            # Fallback to standard formatter
            console_formatter = logging.Formatter(
                '%(levelname)-8s | %(asctime)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    else:
        console_formatter = logging.Formatter(
            '%(levelname)-8s | %(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Add custom success level
    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, f"✓ {message}", args, **kwargs)
    
    # Bind the method to the logger
    logger.success = success.__get__(logger, logger.__class__)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the module name.
    
    Parameters
    ----------
    name : str
        Module name (usually __name__)
        
    Returns
    -------
    logger : logging.Logger
        Logger instance
    """
    return logging.getLogger(name)