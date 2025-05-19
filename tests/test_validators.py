"""Tests for the EEGLAB validator."""

import os
import pytest
import numpy as np
import mne
from mne.epochs import EpochsArray

from autoclean_eeg2source.io.validators import EEGLABValidator
from autoclean_eeg2source.io.exceptions import (
    FileFormatError, FileMismatchError, MontageError, CorruptedDataError
)

# Create a fixtures directory
@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def create_dummy_set_file(temp_dir):
    """Create a dummy .set file for testing."""
    set_file = temp_dir / "test_dummy.set"
    with open(set_file, "w") as f:
        f.write("DUMMY EEGLAB FILE")
    return set_file

@pytest.fixture
def create_epochs():
    """Create synthetic test epochs."""
    # Create random data: 10 epochs, 32 channels, 100 timepoints
    data = np.random.randn(10, 32, 100) * 1e-6
    
    # Channel names matching standard 10-20 system
    ch_names = [
        'Fp1', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8', 'T7', 'C3', 'Cz',
        'C4', 'T8', 'P7', 'P3', 'Pz', 'P4', 'P8', 'O1', 'Oz', 'O2',
        'AF3', 'AF4', 'F5', 'F1', 'F2', 'F6', 'FC5', 'FC1', 'FC2', 'FC6',
        'CP5', 'CP1'
    ]
    
    # Create info
    sfreq = 250.0
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=['eeg'] * len(ch_names))
    
    # Create events
    events = np.array([[i, 0, 1] for i in range(10)])
    
    # Create epochs
    return EpochsArray(data, info, events, tmin=0)

@pytest.fixture
def create_epochs_with_montage(create_epochs):
    """Create epochs with standard montage."""
    epochs = create_epochs
    epochs.set_montage('standard_1020')
    return epochs

@pytest.fixture
def create_corrupt_epochs(create_epochs):
    """Create epochs with corrupted data (NaNs)."""
    epochs = create_epochs.copy()
    # Add NaNs to data
    data = epochs.get_data()
    data[0, 0, 0] = np.nan
    data[1, 1, 1] = np.nan
    return EpochsArray(data, epochs.info, epochs.events, tmin=epochs.tmin)


class TestEEGLABValidator:
    """Test the EEGLAB validator."""
    
    def test_invalid_file_path(self):
        """Test with invalid file path."""
        validator = EEGLABValidator()
        
        with pytest.raises(FileNotFoundError):
            validator.validate_file_pair("/path/to/nonexistent.set")
    
    def test_file_extension_check(self, create_dummy_set_file):
        """Test file extension checking."""
        # Rename file to remove .set extension
        new_file = os.path.splitext(str(create_dummy_set_file))[0]
        os.rename(create_dummy_set_file, new_file)
        
        validator = EEGLABValidator()
        
        # Should warn but not fail
        with pytest.warns(UserWarning):
            report = validator.validate_file_pair(new_file)
        
        assert 'warnings' in report
        assert any('extension' in warning for warning in report['warnings'])
    
    def test_montage_validation_compatible(self, monkeypatch, create_epochs_with_montage):
        """Test montage validation with compatible montage."""
        validator = EEGLABValidator()
        
        # Mock read_epochs_eeglab to return our test epochs
        def mock_read_epochs(*args, **kwargs):
            return create_epochs_with_montage
        
        # Apply the mock
        monkeypatch.setattr(mne.io, 'read_epochs_eeglab', mock_read_epochs)
        
        # Test with compatible montage
        report = validator.validate_montage(create_epochs_with_montage, 'standard_1020')
        
        assert report['valid']
        assert 'errors' in report and len(report['errors']) == 0
    
    def test_montage_validation_incompatible(self, create_epochs):
        """Test montage validation with incompatible montage."""
        validator = EEGLABValidator()
        
        # Test with incompatible montage
        with pytest.raises(MontageError):
            validator.validate_montage(create_epochs, 'GSN-HydroCel-256')
    
    def test_data_quality_check(self, monkeypatch, create_corrupt_epochs):
        """Test data quality checking."""
        validator = EEGLABValidator()
        
        # Mock read_epochs_eeglab to return corrupted epochs
        def mock_read_epochs(*args, **kwargs):
            return create_corrupt_epochs
        
        # Apply the mock
        monkeypatch.setattr(mne.io, 'read_epochs_eeglab', mock_read_epochs)
        
        # Test with strict validation
        with pytest.raises(CorruptedDataError):
            validator.validate_file_pair("dummy.set", strict=True)
    
    def test_get_file_info(self, monkeypatch, create_epochs_with_montage, tmp_path):
        """Test getting file info."""
        validator = EEGLABValidator()
        
        # Create a dummy .set file
        set_file = tmp_path / "test.set"
        with open(set_file, "w") as f:
            f.write("DUMMY")
        
        # Mock read_epochs_eeglab to return our test epochs
        def mock_read_epochs(*args, **kwargs):
            return create_epochs_with_montage
        
        # Mock validate_file_pair to return a valid report
        def mock_validate(*args, **kwargs):
            return {
                'valid': True,
                'n_channels': len(create_epochs_with_montage.ch_names),
                'n_epochs': len(create_epochs_with_montage.events),
                'n_times': len(create_epochs_with_montage.times),
                'sfreq': create_epochs_with_montage.info['sfreq'],
                'duration': len(create_epochs_with_montage.times) / create_epochs_with_montage.info['sfreq'],
                'ch_names': create_epochs_with_montage.ch_names
            }
        
        # Apply the mocks
        monkeypatch.setattr(mne.io, 'read_epochs_eeglab', mock_read_epochs)
        monkeypatch.setattr(validator, 'validate_file_pair', mock_validate)
        
        # Get file info
        info = validator.get_file_info(str(set_file))
        
        assert info['valid']
        assert 'n_channels' in info
        assert 'n_epochs' in info
        assert 'sfreq' in info