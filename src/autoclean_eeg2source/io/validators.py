"""Validators for input file formats."""

import os
import struct
import logging
from typing import Tuple, Optional, Dict, Any, List, Union
import numpy as np
import mne

from .exceptions import (
    FileFormatError, FileMismatchError, ChannelError, 
    MontageError, CorruptedDataError
)

logger = logging.getLogger(__name__)


class EEGLABValidator:
    """Validates EEGLAB .set/.fdt file pairs for compatibility."""
    
    def validate_file_pair(self, set_file: str, fdt_file: Optional[str] = None, 
                      strict: bool = False) -> Dict[str, Any]:
        """
        Ensure .set and .fdt files are compatible.
        
        Parameters
        ----------
        set_file : str
            Path to .set file
        fdt_file : str, optional
            Path to .fdt file. If None, will look for matching .fdt
        strict : bool
            Whether to apply strict validation
            
        Returns
        -------
        dict
            Validation report with file info
            
        Raises
        ------
        FileNotFoundError
            If required files are not found
        FileFormatError
            If file format is invalid
        FileMismatchError
            If .set and .fdt files don't match
        CorruptedDataError
            If data is corrupted
        """
        # Initialize report
        report = {
            'valid': False,
            'file_path': set_file,
            'warnings': [],
            'errors': []
        }
        
        # Check .set file exists
        if not os.path.exists(set_file):
            error = f"SET file not found: {set_file}"
            report['errors'].append(error)
            raise FileNotFoundError(error)
        
        # Check set file extension
        if not set_file.lower().endswith('.set'):
            warning = f"File does not have .set extension: {set_file}"
            report['warnings'].append(warning)
            logger.warning(warning)
        
        # Determine .fdt file path
        fdt_path = fdt_file if fdt_file else set_file.replace('.set', '.fdt')
        report['fdt_path'] = fdt_path
        
        # Check if .fdt exists
        fdt_exists = os.path.exists(fdt_path)
        report['fdt_exists'] = fdt_exists
        
        if not fdt_exists:
            warning = f"FDT file not found: {fdt_path} - attempting to load from .set only"
            report['warnings'].append(warning)
            logger.warning(warning)
        
        # Try to read directly with MNE
        try:
            import mne
            try:
                # Try without specifying FDT file - MNE will handle it
                epochs = mne.io.read_epochs_eeglab(set_file, verbose=False)
                
                # Get basic info
                n_channels = len(epochs.ch_names)
                n_epochs = len(epochs)
                n_times = len(epochs.times)
                sfreq = epochs.info['sfreq']
                
                # Store in report
                report.update({
                    'n_channels': n_channels,
                    'n_epochs': n_epochs,
                    'n_times': n_times,
                    'sfreq': sfreq,
                    'duration': n_times / sfreq,
                    'ch_names': epochs.ch_names,
                    'file_type': 'epochs'
                })
                
                # Check for invalid values in data
                if strict:
                    data = epochs.get_data()
                    
                    # Check for NaN/Inf
                    invalid_mask = ~np.isfinite(data)
                    invalid_count = np.sum(invalid_mask)
                    
                    if invalid_count > 0:
                        invalid_percent = (invalid_count / data.size) * 100
                        error = (
                            f"Data contains {invalid_count} invalid values "
                            f"({invalid_percent:.2f}% NaN/Inf)"
                        )
                        report['errors'].append(error)
                        raise CorruptedDataError(error)
                
                # Success
                logger.info(
                    f"SET file valid: {n_channels} channels, {n_epochs} epochs, "
                    f"{n_times} samples @ {sfreq}Hz"
                )
                report['valid'] = True
                return report
                
            except FileNotFoundError as e:
                # FDT file is needed but missing
                error = f"Required FDT file not found: {e}"
                report['errors'].append(error)
                raise FileNotFoundError(error)
            
            except Exception as e:
                # Try loading as raw continuous file instead
                logger.info(f"Could not load as epochs, trying as raw continuous file: {str(e)}")
                try:
                    raw = mne.io.read_raw_eeglab(set_file, verbose=False)
                    
                    # Get basic info
                    n_channels = len(raw.ch_names)
                    n_times = raw.n_times
                    sfreq = raw.info['sfreq']
                    duration = raw.times[-1]
                    
                    # Store in report
                    report.update({
                        'n_channels': n_channels,
                        'n_times': n_times,
                        'sfreq': sfreq,
                        'duration': duration,
                        'ch_names': raw.ch_names,
                        'file_type': 'raw'
                    })
                    
                    # Check for invalid values in data
                    if strict:
                        data = raw.get_data()
                        
                        # Check for NaN/Inf
                        invalid_mask = ~np.isfinite(data)
                        invalid_count = np.sum(invalid_mask)
                        
                        if invalid_count > 0:
                            invalid_percent = (invalid_count / data.size) * 100
                            error = (
                                f"Data contains {invalid_count} invalid values "
                                f"({invalid_percent:.2f}% NaN/Inf)"
                            )
                            report['errors'].append(error)
                            raise CorruptedDataError(error)
                    
                    # Success
                    logger.info(
                        f"SET file valid (raw): {n_channels} channels, "
                        f"{n_times} samples @ {sfreq}Hz, duration: {duration:.2f}s"
                    )
                    report['valid'] = True
                    return report
                    
                except Exception as nested_e:
                    # Both epochs and raw loading failed
                    error = f"Failed to load as epochs or raw: {str(e)}; {str(nested_e)}"
                    report['errors'].append(error)
                    raise FileFormatError(error)
                
        except Exception as e:
            # Other validation errors
            error = f"Validation failed: {str(e)}"
            report['errors'].append(error)
            
            if "truncated" in str(e).lower() or "corrupt" in str(e).lower():
                raise FileFormatError(f"Corrupted EEGLAB file: {error}")
            elif "size mismatch" in str(e).lower() or "reshape" in str(e).lower():
                raise FileMismatchError(f"Mismatched SET/FDT files: {error}")
            else:
                raise FileFormatError(f"Invalid EEGLAB file: {error}")
    def validate_montage(self, epochs: mne.Epochs, montage_name: str) -> Dict[str, Any]:
        """
        Validate if montage is compatible with the epochs.
        
        Parameters
        ----------
        epochs : mne.Epochs
            Epochs object to validate
        montage_name : str
            Name of the montage to validate against
            
        Returns
        -------
        dict
            Validation report
            
        Raises
        ------
        MontageError
            If montage is not compatible
        """
        report = {
            'valid': False,
            'montage': montage_name,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Get montage
            montage = mne.channels.make_standard_montage(montage_name)
            
            # Check channel count
            montage_ch_count = len(montage.ch_names)
            epochs_ch_count = len(epochs.ch_names)
            
            report.update({
                'montage_channels': montage_ch_count,
                'epochs_channels': epochs_ch_count
            })
            
            # Check if channel counts match
            if epochs_ch_count != montage_ch_count:
                error = (
                    f"Channel count mismatch: epochs have {epochs_ch_count} channels, "
                    f"but montage '{montage_name}' has {montage_ch_count} channels"
                )
                report['errors'].append(error)
                logger.error(error)
                
                # If too different, raise error
                if abs(epochs_ch_count - montage_ch_count) > 5:  # Allow small differences
                    raise MontageError(error)
                else:
                    report['warnings'].append(
                        f"Minor channel count difference - may be fixable"
                    )
            
            # Try to apply montage (will fail if very incompatible)
            try:
                # Create a copy to avoid modifying original
                epochs_copy = epochs.copy()
                epochs_copy.set_montage(montage, match_case=False)
                report['valid'] = True
                
                logger.info(f"Montage '{montage_name}' is compatible with the data")
                
            except Exception as e:
                error = f"Failed to apply montage: {str(e)}"
                report['errors'].append(error)
                raise MontageError(error)
                
            return report
            
        except Exception as e:
            if not isinstance(e, MontageError):
                error = f"Montage validation failed: {str(e)}"
                report['errors'].append(error)
                raise MontageError(error)
            else:
                raise
    
    def get_file_info(self, set_file: str) -> Dict[str, Any]:
        """
        Get comprehensive information about EEGLAB file.
        
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
            # Run validation to get basic info
            report = self.validate_file_pair(set_file, strict=False)
            
            # If validation succeeded, add more info
            if report['valid']:
                # Add file sizes
                report['set_size_mb'] = os.path.getsize(set_file) / 1e6
                
                if report.get('fdt_exists', False):
                    report['fdt_size_mb'] = os.path.getsize(report['fdt_path']) / 1e6
                else:
                    report['fdt_size_mb'] = None
                
                # Add more readable channel names
                if len(report['ch_names']) > 5:
                    report['channel_preview'] = report['ch_names'][:5] + ['...']
                else:
                    report['channel_preview'] = report['ch_names']
                
                # Format duration
                report['duration_sec'] = report['duration']
                report['duration_str'] = f"{report['duration']:.2f}s"
                
                # Memory estimate
                est_memory_mb = (
                    report['n_channels'] * report['n_epochs'] * 
                    report['n_times'] * 4 / 1e6
                )
                report['estimated_memory_mb'] = est_memory_mb
                
                return report
            else:
                return {
                    'valid': False,
                    'errors': report['errors'],
                    'warnings': report['warnings']
                }
                
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def check_all(self, set_file: str, montage_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform all validation checks on a file.
        
        Parameters
        ----------
        set_file : str
            Path to .set file
        montage_name : str, optional
            Name of montage to check compatibility with
            
        Returns
        -------
        dict
            Comprehensive validation report
        """
        # First validate file format
        try:
            file_report = self.validate_file_pair(set_file, strict=True)
            
            # If file format validation passed and montage specified
            if file_report['valid'] and montage_name:
                # Load the epochs
                import mne
                epochs = mne.io.read_epochs_eeglab(set_file, verbose=False)
                
                # Validate montage
                montage_report = self.validate_montage(epochs, montage_name)
                
                # Combine reports
                report = {
                    'valid': file_report['valid'] and montage_report['valid'],
                    'file_validation': file_report,
                    'montage_validation': montage_report
                }
                
                # Add data quality check
                from .data_quality import QualityAssessor
                quality = QualityAssessor()
                
                try:
                    quality_report = quality.check_epochs(epochs)
                    report['quality_validation'] = quality_report
                    report['valid'] = (
                        report['valid'] and 
                        not quality_report['issues_found']
                    )
                except Exception as e:
                    report['quality_validation'] = {
                        'issues_found': True,
                        'error': str(e)
                    }
                    report['valid'] = False
                
                return report
            else:
                # Just return file validation
                return {
                    'valid': file_report['valid'],
                    'file_validation': file_report
                }
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'valid': False,
                'error': str(e)
            }