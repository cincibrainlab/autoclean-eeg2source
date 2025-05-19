"""Memory optimization strategies for EEG processing."""

import gc
import os
import logging
import threading
import numpy as np
import psutil
import tempfile
from typing import Optional, Dict, Any, List, Union, Tuple
import mne
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class OptimizedMemoryManager(MemoryManager):
    """Enhanced memory manager with optimization strategies."""
    
    def __init__(self, 
                 max_memory_gb: float = 4,
                 enable_disk_offload: bool = False,
                 enable_auto_cleanup: bool = True,
                 cleanup_threshold: float = 0.7):
        """
        Initialize optimized memory manager.
        
        Parameters
        ----------
        max_memory_gb : float
            Maximum memory usage allowed in gigabytes
        enable_disk_offload : bool
            Whether to enable disk offloading for large arrays
        enable_auto_cleanup : bool
            Whether to enable automatic garbage collection
        cleanup_threshold : float
            Memory usage threshold (0-1) for automatic cleanup
        """
        super().__init__(max_memory_gb=max_memory_gb)
        
        self.enable_disk_offload = enable_disk_offload
        self.enable_auto_cleanup = enable_auto_cleanup
        self.cleanup_threshold = cleanup_threshold
        
        # Temporary directory for disk offloading
        self.temp_dir = None
        if enable_disk_offload:
            self.temp_dir = tempfile.mkdtemp(prefix="eeg2source_")
            logger.info(f"Disk offloading enabled with temp directory: {self.temp_dir}")
        
        # List of memory-mapped arrays to manage
        self.memmaps = []
        
        # Auto-cleanup daemon
        self.auto_cleanup_thread = None
        self.stop_auto_cleanup = threading.Event()
        if enable_auto_cleanup:
            self._start_auto_cleanup()
            
        logger.info(
            f"Optimized memory manager initialized with {max_memory_gb}GB limit, "
            f"disk_offload={enable_disk_offload}, auto_cleanup={enable_auto_cleanup}"
        )
    
    def _start_auto_cleanup(self):
        """Start automatic memory cleanup thread."""
        def auto_cleanup_worker():
            logger.debug("Auto-cleanup thread started")
            while not self.stop_auto_cleanup.is_set():
                # Check current memory usage
                mem = psutil.virtual_memory()
                if mem.percent > self.cleanup_threshold * 100:
                    logger.debug(f"Auto-cleanup triggered at {mem.percent:.1f}% memory usage")
                    self.cleanup()
                
                # Sleep for a short period
                self.stop_auto_cleanup.wait(timeout=5)
                
            logger.debug("Auto-cleanup thread stopped")
        
        # Start as daemon thread
        self.auto_cleanup_thread = threading.Thread(target=auto_cleanup_worker, daemon=True)
        self.auto_cleanup_thread.start()
        logger.debug("Auto-cleanup thread started")
    
    def stop(self):
        """Stop auto-cleanup thread and clean up temporary files."""
        if self.auto_cleanup_thread:
            self.stop_auto_cleanup.set()
            self.auto_cleanup_thread.join(timeout=1)
        
        # Close memory-mapped arrays
        for mm in self.memmaps:
            if hasattr(mm, 'close'):
                try:
                    mm.close()
                except Exception:
                    pass
                
        # Remove temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Removed temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary directory: {e}")
    
    def __del__(self):
        """Cleanup on garbage collection."""
        self.stop()
    
    def check_available(self, required_gb: Optional[float] = None) -> bool:
        """
        Check if processing can continue based on available memory.
        
        Parameters
        ----------
        required_gb : float, optional
            Required memory in GB for next operation
            
        Returns
        -------
        bool
            True if sufficient memory is available
            
        Raises
        ------
        MemoryError
            If available memory is below threshold
        """
        mem = psutil.virtual_memory()
        available_gb = mem.available / 1e9
        percent_available = 100 - mem.percent
        
        # Calculate required memory
        if required_gb is None:
            required_gb = self.max_memory / 1e9 * 0.2
        
        logger.debug(
            f"Memory status: {available_gb:.2f}GB available ({percent_available:.1f}% free), "
            f"need {required_gb:.2f}GB"
        )
        
        if available_gb < required_gb:
            # Try cleanup first
            self.cleanup()
            
            # Check again
            mem = psutil.virtual_memory()
            available_gb = mem.available / 1e9
            
            if available_gb < required_gb:
                raise MemoryError(
                    f"Insufficient memory: {available_gb:.2f}GB available, "
                    f"need at least {required_gb:.2f}GB"
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
    
    def offload_array(self, array: np.ndarray, name: str = None) -> np.memmap:
        """
        Offload NumPy array to disk using memory mapping.
        
        Parameters
        ----------
        array : np.ndarray
            Array to offload
        name : str, optional
            Name for the memory-mapped file
            
        Returns
        -------
        np.memmap
            Memory-mapped array
        """
        if not self.enable_disk_offload or self.temp_dir is None:
            return array
        
        # Generate filename
        prefix = name or "array"
        filename = os.path.join(self.temp_dir, f"{prefix}_{len(self.memmaps)}.dat")
        
        try:
            # Create memory-mapped array
            mmap = np.memmap(filename, dtype=array.dtype, mode='w+', shape=array.shape)
            
            # Copy data to memory map
            mmap[:] = array[:]
            mmap.flush()
            
            # Add to managed list
            self.memmaps.append(mmap)
            
            # Log offloading
            size_mb = array.nbytes / 1e6
            logger.debug(f"Offloaded array '{prefix}' ({size_mb:.1f}MB) to disk: {filename}")
            
            return mmap
            
        except Exception as e:
            logger.warning(f"Failed to offload array to disk: {e}")
            return array
    
    def optimize_epochs(self, epochs: mne.Epochs) -> mne.Epochs:
        """
        Optimize memory usage for epochs object.
        
        Parameters
        ----------
        epochs : mne.Epochs
            Epochs to optimize
            
        Returns
        -------
        mne.Epochs
            Optimized epochs
        """
        # Check if epochs are already loaded
        if epochs._data is None:
            logger.debug("Epochs already using memory-optimization (data not loaded)")
            return epochs
        
        if not self.enable_disk_offload:
            return epochs
        
        try:
            # Get data
            data = epochs.get_data()
            
            # Offload to disk
            mmap_data = self.offload_array(data, name="epochs")
            
            # Create new epochs with offloaded data
            events = epochs.events.copy()
            info = epochs.info.copy()
            event_id = epochs.event_id.copy()
            tmin = epochs.tmin
            
            # Create new epochs object with memory-mapped data
            new_epochs = mne.EpochsArray(
                mmap_data, info, events=events, 
                event_id=event_id, tmin=tmin
            )
            
            # Copy metadata
            if hasattr(epochs, 'metadata') and epochs.metadata is not None:
                new_epochs.metadata = epochs.metadata.copy()
            
            logger.debug(f"Optimized epochs: {len(epochs)} epochs, {len(epochs.ch_names)} channels")
            return new_epochs
            
        except Exception as e:
            logger.warning(f"Failed to optimize epochs: {e}")
            return epochs
    
    def get_memory_usage(self) -> dict:
        """
        Get current memory usage statistics with optimization info.
        
        Returns
        -------
        dict
            Dictionary with memory statistics
        """
        mem = psutil.virtual_memory()
        stats = {
            'total_gb': mem.total / 1e9,
            'available_gb': mem.available / 1e9,
            'used_gb': mem.used / 1e9,
            'percent_used': mem.percent,
            'percent_free': 100 - mem.percent,
            'offloaded_arrays': len(self.memmaps),
            'disk_offload_enabled': self.enable_disk_offload,
            'auto_cleanup_enabled': self.enable_auto_cleanup
        }
        
        # Add disk usage if offloading is enabled
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                total_size = 0
                for path, dirs, files in os.walk(self.temp_dir):
                    for f in files:
                        fp = os.path.join(path, f)
                        total_size += os.path.getsize(fp)
                
                stats['offload_size_gb'] = total_size / 1e9
            except Exception:
                stats['offload_size_gb'] = 0
        
        return stats


class MemoryOptimizer:
    """Utility class for optimizing memory usage during processing."""
    
    @staticmethod
    def optimize_epochs_data(epochs: mne.Epochs, 
                           memory_manager: Optional[OptimizedMemoryManager] = None) -> mne.Epochs:
        """
        Optimize memory usage for epochs object.
        
        Parameters
        ----------
        epochs : mne.Epochs
            Epochs to optimize
        memory_manager : OptimizedMemoryManager, optional
            Memory manager instance
            
        Returns
        -------
        mne.Epochs
            Optimized epochs
        """
        if memory_manager and isinstance(memory_manager, OptimizedMemoryManager):
            return memory_manager.optimize_epochs(epochs)
            
        # Default implementation without memory manager
        if epochs._data is not None:
            # If data is already loaded, nothing we can do easily
            # without a proper memory manager
            return epochs
        
        return epochs
    
    @staticmethod
    def optimize_array(array: np.ndarray, max_size_mb: float = 100) -> np.ndarray:
        """
        Optimize memory usage for a NumPy array.
        
        Parameters
        ----------
        array : np.ndarray
            Array to optimize
        max_size_mb : float
            Maximum size in MB before downgrading precision
            
        Returns
        -------
        np.ndarray
            Optimized array
        """
        # Check if array needs optimization
        size_mb = array.nbytes / 1e6
        if size_mb <= max_size_mb:
            return array
        
        # Downgrade precision if needed
        if array.dtype == np.float64:
            logger.debug(f"Downgrading array precision from float64 to float32 ({size_mb:.1f}MB)")
            return array.astype(np.float32)
        elif array.dtype == np.float32 and size_mb > max_size_mb * 2:
            logger.debug(f"Downgrading array precision from float32 to float16 ({size_mb:.1f}MB)")
            return array.astype(np.float16)
        
        return array
    
    @staticmethod
    def clear_mne_cache():
        """Clear MNE's internal caches to free memory."""
        # Clear source space cache
        if hasattr(mne.source_space, '_cache'):
            mne.source_space._cache.clear()
        
        # Clear forward solution cache
        if hasattr(mne.forward, '_cache'):
            mne.forward._cache.clear()
        
        # Clear source estimate cache
        if hasattr(mne.source_estimate, '_cache'):
            mne.source_estimate._cache.clear()
        
        # Force garbage collection
        gc.collect()
        
        logger.debug("Cleared MNE internal caches")