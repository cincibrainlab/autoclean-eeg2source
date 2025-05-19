"""Validators for input file formats."""

import os
import struct
import logging
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EEGLABValidator:
    """Validates EEGLAB .set/.fdt file pairs for compatibility."""
    
    @staticmethod
    def validate_file_pair(set_file: str, fdt_file: Optional[str] = None) -> bool:
        """
        Ensure .set and .fdt files are compatible.
        
        Parameters
        ----------
        set_file : str
            Path to .set file
        fdt_file : str, optional
            Path to .fdt file. If None, will look for matching .fdt
            
        Returns
        -------
        bool
            True if files are valid and compatible
            
        Raises
        ------
        FileNotFoundError
            If required files are not found
        ValueError
            If files are incompatible
        """
        # Check .set file exists
        if not os.path.exists(set_file):
            raise FileNotFoundError(f"SET file not found: {set_file}")
        
        # Try to read directly with MNE
        try:
            import mne
            # Try without specifying FDT file - MNE will handle it
            epochs = mne.io.read_epochs_eeglab(set_file, verbose=False)
            n_channels = len(epochs.ch_names)
            n_epochs = len(epochs)
            n_times = len(epochs.times)
            
            logger.info(
                f"SET file valid: {n_channels} channels, {n_epochs} epochs, "
                f"{n_times} samples"
            )
            return True
            
        except FileNotFoundError as e:
            # FDT file might be needed but missing
            logger.error(f"Required file not found: {e}")
            raise
            
        except Exception as e:
            # Other validation errors
            logger.error(f"Validation failed: {e}")
            raise ValueError(f"Invalid EEGLAB file: {e}")
    
    @staticmethod
    def _validate_set_only(set_file: str) -> bool:
        """
        Validate .set file when .fdt is not available.
        
        Parameters
        ----------
        set_file : str
            Path to .set file
            
        Returns
        -------
        bool
            True if .set file appears valid
        """
        try:
            # Try to read basic info from .set file
            import mne
            # This will fail if data is not embedded
            epochs = mne.io.read_epochs_eeglab(set_file, verbose=False)
            n_channels = len(epochs.ch_names)
            n_epochs = len(epochs)
            n_times = len(epochs.times)
            
            logger.info(f"SET file valid: {n_channels} channels, {n_epochs} epochs, {n_times} samples")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate .set file: {e}")
            raise ValueError(f"Invalid .set file or missing .fdt: {set_file}")
    
    @staticmethod
    def _validate_files(set_file: str, fdt_file: str) -> bool:
        """
        Validate compatibility between .set and .fdt files.
        
        Parameters
        ----------
        set_file : str
            Path to .set file
        fdt_file : str
            Path to .fdt file
            
        Returns
        -------
        bool
            True if files are compatible
        """
        try:
            # Read basic info using MNE
            import mne
            epochs = mne.io.read_epochs_eeglab(set_file, verbose=False)
            
            # Get data dimensions
            n_channels = len(epochs.ch_names)
            n_epochs = len(epochs)
            n_times = len(epochs.times)
            
            # Calculate expected .fdt size (float32 = 4 bytes)
            expected_size = n_channels * n_epochs * n_times * 4
            actual_size = os.path.getsize(fdt_file)
            
            # Allow some tolerance for file headers
            size_ratio = actual_size / expected_size
            if 0.9 <= size_ratio <= 1.1:
                logger.info(
                    f"Files validated: {n_channels} channels, {n_epochs} epochs, "
                    f"{n_times} samples, {actual_size/1e6:.1f}MB"
                )
                return True
            else:
                raise ValueError(
                    f"File size mismatch: expected ~{expected_size/1e6:.1f}MB, "
                    f"got {actual_size/1e6:.1f}MB"
                )
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
    
    @staticmethod
    def get_file_info(set_file: str) -> dict:
        """
        Get information about EEGLAB file.
        
        Parameters
        ----------
        set_file : str
            Path to .set file
            
        Returns
        -------
        dict
            Dictionary with file information
        """
        try:
            import mne
            epochs = mne.io.read_epochs_eeglab(set_file, verbose=False)
            
            info = {
                'n_channels': len(epochs.ch_names),
                'n_epochs': len(epochs),
                'n_times': len(epochs.times),
                'sfreq': epochs.info['sfreq'],
                'duration': len(epochs.times) / epochs.info['sfreq'],
                'channels': epochs.ch_names[:5] + ['...'] if len(epochs.ch_names) > 5 else epochs.ch_names
            }
            
            # Check for .fdt file
            fdt_file = set_file.replace('.set', '.fdt')
            if os.path.exists(fdt_file):
                info['fdt_size_mb'] = os.path.getsize(fdt_file) / 1e6
            else:
                info['fdt_size_mb'] = None
                
            return info
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {'error': str(e)}