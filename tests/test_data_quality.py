"""Tests for the data quality assessor."""

import pytest
import numpy as np
import mne
from mne.epochs import EpochsArray

from autoclean_eeg2source.io.data_quality import QualityAssessor
from autoclean_eeg2source.io.exceptions import DataQualityError, CorruptedDataError


@pytest.fixture
def create_clean_epochs():
    """Create clean synthetic test epochs."""
    # Create random data: 10 epochs, 32 channels, 100 timepoints
    data = np.random.randn(10, 32, 100) * 1e-6
    
    # Channel names
    ch_names = [f'CH{i+1}' for i in range(32)]
    
    # Create info
    sfreq = 250.0
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=['eeg'] * len(ch_names))
    
    # Create events
    events = np.array([[i, 0, 1] for i in range(10)])
    
    # Create epochs
    return EpochsArray(data, info, events, tmin=0)


@pytest.fixture
def create_epochs_with_nans():
    """Create epochs with NaN values."""
    # Create random data with some NaNs
    data = np.random.randn(10, 32, 100) * 1e-6
    data[0, 0, 0] = np.nan  # Add a NaN value
    data[1, 1, 1] = np.nan  # Add another NaN value
    
    # Channel names
    ch_names = [f'CH{i+1}' for i in range(32)]
    
    # Create info
    sfreq = 250.0
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=['eeg'] * len(ch_names))
    
    # Create events
    events = np.array([[i, 0, 1] for i in range(10)])
    
    # Create epochs
    return EpochsArray(data, info, events, tmin=0)


@pytest.fixture
def create_epochs_with_flat_channels():
    """Create epochs with flat channels."""
    # Create random data
    data = np.random.randn(10, 32, 100) * 1e-6
    
    # Make some channels flat (zero std)
    data[:, 0, :] = 1e-8  # Flat channel
    data[:, 5, :] = 2e-8  # Another flat channel
    
    # Channel names
    ch_names = [f'CH{i+1}' for i in range(32)]
    
    # Create info
    sfreq = 250.0
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=['eeg'] * len(ch_names))
    
    # Create events
    events = np.array([[i, 0, 1] for i in range(10)])
    
    # Create epochs
    return EpochsArray(data, info, events, tmin=0)


@pytest.fixture
def create_epochs_with_noisy_channels():
    """Create epochs with noisy channels."""
    # Create random data
    data = np.random.randn(10, 32, 100) * 1e-6
    
    # Make some channels noisy (high std)
    data[:, 2, :] = np.random.randn(10, 100) * 1e-4  # Noisy channel
    data[:, 7, :] = np.random.randn(10, 100) * 1e-4  # Another noisy channel
    
    # Channel names
    ch_names = [f'CH{i+1}' for i in range(32)]
    
    # Create info
    sfreq = 250.0
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=['eeg'] * len(ch_names))
    
    # Create events
    events = np.array([[i, 0, 1] for i in range(10)])
    
    # Create epochs
    return EpochsArray(data, info, events, tmin=0)


class TestQualityAssessor:
    """Test the quality assessor."""
    
    def test_check_clean_epochs(self, create_clean_epochs):
        """Test checking clean epochs."""
        quality = QualityAssessor()
        report = quality.check_epochs(create_clean_epochs)
        
        assert not report['issues_found']
        assert len(report['bad_channels']) == 0
    
    def test_check_epochs_with_nans(self, create_epochs_with_nans):
        """Test checking epochs with NaNs."""
        quality = QualityAssessor(nan_threshold=0.01)  # Allow small percentage of NaNs
        
        with pytest.raises(CorruptedDataError):
            quality.check_epochs(create_epochs_with_nans)
    
    def test_check_flat_channels(self, create_epochs_with_flat_channels):
        """Test checking epochs with flat channels."""
        quality = QualityAssessor(flat_threshold=1e-7)
        report = quality.check_epochs(create_epochs_with_flat_channels)
        
        assert report['issues_found']
        assert 'flat_channels' in report['issues']
        assert len(report['flat_report']['flat_channels']) == 2
    
    def test_check_noisy_channels(self, create_epochs_with_noisy_channels):
        """Test checking epochs with noisy channels."""
        quality = QualityAssessor(noise_threshold=3.0)  # Z-score threshold
        report = quality.check_epochs(create_epochs_with_noisy_channels)
        
        assert report['issues_found']
        assert 'noisy_channels' in report['issues']
        assert len(report['noise_report']['noisy_channels']) == 2
    
    def test_fix_epochs(self, create_epochs_with_flat_channels):
        """Test fixing epochs."""
        quality = QualityAssessor(flat_threshold=1e-7)
        fixed_epochs, report = quality.fix_epochs(create_epochs_with_flat_channels)
        
        assert report['issues_found']
        assert 'actions' in report
        
        # Check that bad channels were marked
        assert len(fixed_epochs.info['bads']) > 0
        
        # Original epochs should be unchanged
        assert len(create_epochs_with_flat_channels.info['bads']) == 0
    
    def test_excessive_bad_channels(self, create_epochs_with_flat_channels):
        """Test with excessive bad channels."""
        # Set a low threshold to trigger the error
        quality = QualityAssessor(
            flat_threshold=1e-7,
            max_bad_channels_percent=5.0  # 5% of 32 channels = ~1.6 channels
        )
        
        with pytest.raises(DataQualityError):
            quality.check_epochs(create_epochs_with_flat_channels)