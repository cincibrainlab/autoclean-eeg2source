"""Memory management utilities for processing large EEG datasets."""

import gc
import logging
from typing import Optional
import psutil

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages memory usage during EEG processing to prevent exhaustion."""
    
    def __init__(self, max_memory_gb: float = 4):
        """
        Initialize memory manager.
        
        Parameters
        ----------
        max_memory_gb : float
            Maximum memory usage allowed in gigabytes
        """
        self.max_memory = max_memory_gb * 1e9  # Convert to bytes
        self.initial_memory = psutil.virtual_memory().available
        logger.info(f"Memory manager initialized with {max_memory_gb}GB limit")
        
    def check_available(self) -> bool:
        """
        Check if processing can continue based on available memory.
        
        Returns
        -------
        bool
            True if sufficient memory is available
            
        Raises
        ------
        MemoryError
            If available memory is below 20% of max limit
        """
        mem = psutil.virtual_memory()
        available_gb = mem.available / 1e9
        percent_available = mem.percent
        
        logger.debug(f"Memory status: {available_gb:.2f}GB available ({100-percent_available:.1f}% free)")
        
        if mem.available < self.max_memory * 0.2:
            raise MemoryError(
                f"Insufficient memory: {available_gb:.2f}GB available, "
                f"need at least {self.max_memory * 0.2 / 1e9:.2f}GB"
            )
        
        return True
    
    def cleanup(self) -> float:
        """
        Force garbage collection and return available memory.
        
        Returns
        -------
        float
            Available memory in bytes after cleanup
        """
        # Log memory before cleanup
        before = psutil.virtual_memory().available
        
        # Force garbage collection
        gc.collect()
        
        # Log memory after cleanup
        after = psutil.virtual_memory().available
        freed = (after - before) / 1e6  # Convert to MB
        
        if freed > 0:
            logger.debug(f"Memory cleanup freed {freed:.1f}MB")
        
        return after
    
    def get_memory_usage(self) -> dict:
        """
        Get current memory usage statistics.
        
        Returns
        -------
        dict
            Dictionary with memory statistics
        """
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / 1e9,
            'available_gb': mem.available / 1e9,
            'used_gb': mem.used / 1e9,
            'percent_used': mem.percent,
            'percent_free': 100 - mem.percent
        }
    
    def log_memory_status(self, context: str = ""):
        """
        Log current memory status with optional context.
        
        Parameters
        ----------
        context : str
            Context message for the log entry
        """
        stats = self.get_memory_usage()
        msg = f"Memory: {stats['used_gb']:.1f}/{stats['total_gb']:.1f}GB used ({stats['percent_used']:.1f}%)"
        if context:
            msg = f"{context} - {msg}"
        logger.info(msg)