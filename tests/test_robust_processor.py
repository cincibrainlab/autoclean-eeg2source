"""Tests for the robust processor."""

import os
import pytest
import numpy as np
import mne
from mne.epochs import EpochsArray
from unittest.mock import patch, MagicMock

from autoclean_eeg2source.core.robust_processor import RobustProcessor
from autoclean_eeg2source.core.memory_manager import MemoryManager
from autoclean_eeg2source.io.exceptions import (
    FileFormatError, MontageError, DataQualityError, MemoryError
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def create_memory_manager():
    """Create a mock memory manager."""
    memory_manager = MagicMock(spec=MemoryManager)
    memory_manager.check_available.return_value = True
    memory_manager.cleanup.return_value = 1e9
    memory_manager.log_memory_status.return_value = None
    return memory_manager


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
def create_robust_processor(create_memory_manager, temp_dir):
    """Create a robust processor with mocked components."""
    error_dir = os.path.join(temp_dir, "errors")
    os.makedirs(error_dir, exist_ok=True)
    
    return RobustProcessor(
        memory_manager=create_memory_manager,
        montage="standard_1020",
        resample_freq=250,
        recovery_mode=True,
        error_dir=error_dir
    )


class TestRobustProcessor:
    """Test the robust processor."""
    
    def test_initialization(self, create_robust_processor):
        """Test initialization."""
        processor = create_robust_processor
        
        assert processor.recovery_mode
        assert processor.error_dir is not None
        assert processor.validator is not None
        assert processor.quality_assessor is not None
    
    def test_normal_processing(self, create_robust_processor, monkeypatch, create_epochs, temp_dir):
        """Test normal processing path."""
        processor = create_robust_processor
        
        # Create test files
        input_file = os.path.join(temp_dir, "test.set")
        with open(input_file, "w") as f:
            f.write("DUMMY")
        
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Mock validator
        validation_report = {'valid': True, 'file_validation': {'valid': True}}
        processor.validator.check_all = MagicMock(return_value=validation_report)
        
        # Mock parent class method
        parent_result = {'status': 'success', 'output_file': os.path.join(output_dir, "test_dk_regions.set")}
        with patch('autoclean_eeg2source.core.converter.SequentialProcessor.process_file', 
                  return_value=parent_result):
            
            # Process file
            result = processor.process_with_recovery(input_file, output_dir)
            
            assert result['status'] == 'success'
            assert not result['recovery_attempted']
            assert result['output_file'] == parent_result['output_file']
    
    def test_file_format_recovery(self, create_robust_processor, monkeypatch, create_epochs, temp_dir):
        """Test recovery from file format error."""
        processor = create_robust_processor
        
        # Create test files
        input_file = os.path.join(temp_dir, "test.set")
        with open(input_file, "w") as f:
            f.write("DUMMY")
        
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Mock validator to raise file error
        def mock_check_all(*args, **kwargs):
            raise FileFormatError("Invalid file format")
        
        processor.validator.check_all = MagicMock(side_effect=mock_check_all)
        
        # Mock direct epoch reading
        def mock_read_epochs(*args, **kwargs):
            return create_epochs
        
        monkeypatch.setattr(mne.io, 'read_epochs_eeglab', mock_read_epochs)
        
        # Mock _process_with_epochs
        processor._process_with_epochs = MagicMock(return_value={
            'status': 'success',
            'output_file': os.path.join(output_dir, "test_dk_regions.set")
        })
        
        # Process file
        result = processor.process_with_recovery(input_file, output_dir)
        
        assert result['status'] == 'success'
        assert result['recovery_attempted']
        assert result['recovery_successful']
        assert result['recovery_strategy'] == 'file_recovery'
    
    def test_montage_recovery(self, create_robust_processor, monkeypatch, create_epochs, temp_dir):
        """Test recovery from montage error."""
        processor = create_robust_processor
        
        # Create test files
        input_file = os.path.join(temp_dir, "test.set")
        with open(input_file, "w") as f:
            f.write("DUMMY")
        
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Mock validator to raise montage error
        def mock_check_all(*args, **kwargs):
            raise MontageError("Incompatible montage")
        
        processor.validator.check_all = MagicMock(side_effect=mock_check_all)
        
        # Mock direct epoch reading
        def mock_read_epochs(*args, **kwargs):
            return create_epochs
        
        monkeypatch.setattr(mne.io, 'read_epochs_eeglab', mock_read_epochs)
        
        # Mock process_file to succeed with alternative montage
        def mock_process_file(self, input_file, output_dir):
            return {
                'status': 'success',
                'output_file': os.path.join(output_dir, "test_dk_regions.set")
            }
        
        monkeypatch.setattr('autoclean_eeg2source.core.converter.SequentialProcessor.process_file', 
                           mock_process_file)
        
        # Process file
        result = processor.process_with_recovery(input_file, output_dir)
        
        assert result['status'] == 'success'
        assert result['recovery_attempted']
        assert result['recovery_successful']
        assert result['recovery_strategy'] == 'montage_recovery'
    
    def test_get_recovery_stats(self, create_robust_processor):
        """Test getting recovery statistics."""
        processor = create_robust_processor
        
        # Set some stats
        processor.recovery_stats = {
            'attempted': 10,
            'successful': 7,
            'failed': 3,
            'strategies_used': {
                'file_recovery': 3,
                'montage_recovery': 4,
                'quality_recovery': 2,
                'memory_recovery': 1
            }
        }
        
        stats = processor.get_recovery_stats()
        
        assert stats['attempted'] == 10
        assert stats['successful'] == 7
        assert stats['failed'] == 3
        assert 'success_rate' in stats
        assert stats['success_rate'] == 70.0