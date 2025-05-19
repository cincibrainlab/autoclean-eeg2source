"""Data quality assessment tools for EEG data."""

import logging
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
import mne
from ..io.exceptions import DataQualityError, CorruptedDataError

logger = logging.getLogger(__name__)


class QualityAssessor:
    """Quality assessment for EEG data."""
    
    def __init__(self, 
                 nan_threshold: float = 0.0,
                 flat_threshold: float = 0.01,
                 noise_threshold: float = 5.0,
                 max_bad_channels_percent: float = 15.0):
        """
        Initialize quality assessor.
        
        Parameters
        ----------
        nan_threshold : float
            Maximum percentage of NaN values allowed
        flat_threshold : float
            Threshold for flat channel detection (μV)
        noise_threshold : float
            Threshold for high noise channel detection (z-score)
        max_bad_channels_percent : float
            Maximum percentage of bad channels allowed
        """
        self.nan_threshold = nan_threshold
        self.flat_threshold = flat_threshold
        self.noise_threshold = noise_threshold
        self.max_bad_channels_percent = max_bad_channels_percent
    
    def check_epochs(self, epochs: mne.Epochs) -> Dict[str, Any]:
        """
        Check epochs data quality.
        
        Parameters
        ----------
        epochs : mne.Epochs
            The epochs to check
            
        Returns
        -------
        report : dict
            Quality report with issues found
            
        Raises
        ------
        CorruptedDataError
            If data has critical corruption issues
        DataQualityError
            If data quality is below threshold
        """
        # Get data
        data = epochs.get_data()
        
        # Initialize report
        report = {
            'n_epochs': len(epochs),
            'n_channels': len(epochs.ch_names),
            'issues_found': False,
            'issues': [],
            'dropped_epochs': [],
            'bad_channels': []
        }
        
        # Check for NaN/Inf values
        nan_report = self._check_nan_values(data)
        if nan_report['issues_found']:
            report['issues'].append('nan_values')
            report['nan_report'] = nan_report
            report['issues_found'] = True
            
            # Critical level of NaNs is unrecoverable
            if nan_report['nan_percent'] > self.nan_threshold:
                raise CorruptedDataError(
                    f"Critical data corruption: {nan_report['nan_percent']:.2f}% NaN values"
                )
        
        # Check for flat channels
        flat_report = self._check_flat_channels(data)
        if flat_report['issues_found']:
            report['issues'].append('flat_channels')
            report['flat_report'] = flat_report
            report['issues_found'] = True
            report['bad_channels'].extend(flat_report['flat_channels'])
        
        # Check for noisy channels
        noise_report = self._check_noise_channels(data)
        if noise_report['issues_found']:
            report['issues'].append('noisy_channels')
            report['noise_report'] = noise_report
            report['issues_found'] = True
            report['bad_channels'].extend(noise_report['noisy_channels'])
        
        # Check overall bad channel percentage
        report['bad_channels'] = list(set(report['bad_channels']))
        report['bad_channel_percent'] = (len(report['bad_channels']) / 
                                        report['n_channels']) * 100
        
        if report['bad_channel_percent'] > self.max_bad_channels_percent:
            report['issues'].append('excessive_bad_channels')
            report['issues_found'] = True
            
            # If too many bad channels, raise error
            raise DataQualityError(
                f"Excessive bad channels: {report['bad_channel_percent']:.1f}% "
                f"({len(report['bad_channels'])}/{report['n_channels']})"
            )
            
        return report
    
    def _check_nan_values(self, data: np.ndarray) -> Dict[str, Any]:
        """Check for NaN/Inf values in the data."""
        nan_mask = ~np.isfinite(data)
        nan_count = np.sum(nan_mask)
        nan_percent = (nan_count / data.size) * 100
        
        # Get affected epochs and channels
        nan_epochs = np.any(nan_mask, axis=(1, 2))
        nan_channels = np.any(nan_mask, axis=(0, 2))
        
        return {
            'issues_found': nan_count > 0,
            'nan_count': int(nan_count),
            'nan_percent': float(nan_percent),
            'nan_epochs': np.where(nan_epochs)[0].tolist(),
            'nan_channels': np.where(nan_channels)[0].tolist()
        }
    
    def _check_flat_channels(self, data: np.ndarray) -> Dict[str, Any]:
        """Check for flat (inactive) channels."""
        # Calculate standard deviation for each channel
        std_per_channel = np.std(data, axis=(0, 2))
        
        # Identify flat channels (std < threshold)
        flat_channels = np.where(std_per_channel < self.flat_threshold)[0].tolist()
        
        return {
            'issues_found': len(flat_channels) > 0,
            'flat_channels': flat_channels,
            'std_values': std_per_channel.tolist()
        }
    
    def _check_noise_channels(self, data: np.ndarray) -> Dict[str, Any]:
        """Check for unusually noisy channels."""
        # Calculate RMS for each channel
        rms_per_channel = np.sqrt(np.mean(data**2, axis=(0, 2)))
        
        # Z-score the RMS values
        z_scores = (rms_per_channel - np.mean(rms_per_channel)) / np.std(rms_per_channel)
        
        # Identify noisy channels (z > threshold)
        noisy_channels = np.where(z_scores > self.noise_threshold)[0].tolist()
        
        return {
            'issues_found': len(noisy_channels) > 0,
            'noisy_channels': noisy_channels,
            'z_scores': z_scores.tolist()
        }
    
    def fix_epochs(self, epochs: mne.Epochs) -> Tuple[mne.Epochs, Dict[str, Any]]:
        """
        Fix epochs data quality issues.
        
        Parameters
        ----------
        epochs : mne.Epochs
            Epochs to fix
            
        Returns
        -------
        fixed_epochs : mne.Epochs
            Fixed epochs
        report : dict
            Report of changes made
        """
        # Initial quality assessment
        report = self.check_epochs(epochs)
        
        if not report['issues_found']:
            logger.info("No quality issues found in epochs")
            return epochs, report
        
        logger.info(f"Found quality issues: {', '.join(report['issues'])}")
        
        # Create a copy to avoid modifying the original
        epochs_fixed = epochs.copy()
        
        # If there are bad channels, mark them
        if report['bad_channels']:
            logger.info(f"Marking {len(report['bad_channels'])} bad channels")
            bad_ch_names = [epochs.ch_names[idx] for idx in report['bad_channels']]
            epochs_fixed.info['bads'] = bad_ch_names
            
            # Interpolate bad channels
            if len(epochs_fixed.info['bads']) < len(epochs_fixed.ch_names) * 0.2:
                logger.info("Interpolating bad channels")
                epochs_fixed = epochs_fixed.interpolate_bads(reset_bads=True)
                report['actions'] = report.get('actions', []) + ['interpolated_bad_channels']
        
        # Return the fixed epochs and report
        return epochs_fixed, report