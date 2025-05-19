"""Tests for the memory manager."""

import os
import gc
import pytest
from unittest.mock import patch, MagicMock

from autoclean_eeg2source.core.memory_manager import MemoryManager
from autoclean_eeg2source.io.exceptions import MemoryError


class TestMemoryManager:
    """Test memory manager functionality."""
    
    def test_initialization(self):
        """Test memory manager initialization."""
        manager = MemoryManager(max_memory_gb=4)
        assert manager.max_memory == 4 * 1e9
    
    @patch('psutil.virtual_memory')
    def test_check_available_sufficient(self, mock_virtual_memory):
        """Test check_available with sufficient memory."""
        # Mock 8GB total with 6GB available
        mock_mem = MagicMock()
        mock_mem.total = 8 * 1e9
        mock_mem.available = 6 * 1e9
        mock_mem.percent = 25.0  # 25% used, 75% free
        mock_virtual_memory.return_value = mock_mem
        
        manager = MemoryManager(max_memory_gb=4)
        
        # Should not raise error
        result = manager.check_available()
        assert result
    
    @patch('psutil.virtual_memory')
    def test_check_available_insufficient(self, mock_virtual_memory):
        """Test check_available with insufficient memory."""
        # Mock 8GB total with 0.5GB available
        mock_mem = MagicMock()
        mock_mem.total = 8 * 1e9
        mock_mem.available = 0.5 * 1e9
        mock_mem.percent = 93.75  # 93.75% used, 6.25% free
        mock_virtual_memory.return_value = mock_mem
        
        manager = MemoryManager(max_memory_gb=4)
        
        # Should raise MemoryError
        with pytest.raises(MemoryError):
            manager.check_available()
    
    @patch('psutil.virtual_memory')
    @patch('gc.collect')
    def test_cleanup(self, mock_gc_collect, mock_virtual_memory):
        """Test cleanup functionality."""
        # Mock memory before and after cleanup
        # First call during cleanup
        mock_mem1 = MagicMock()
        mock_mem1.available = 2 * 1e9
        
        # Second call after cleanup
        mock_mem2 = MagicMock()
        mock_mem2.available = 3 * 1e9
        
        mock_virtual_memory.side_effect = [mock_mem1, mock_mem2]
        
        manager = MemoryManager(max_memory_gb=4)
        
        # Cleanup should return available memory
        result = manager.cleanup()
        
        # Check that gc.collect was called
        mock_gc_collect.assert_called_once()
        
        # Should return available memory after cleanup
        assert result == 3 * 1e9
    
    @patch('psutil.virtual_memory')
    def test_get_memory_usage(self, mock_virtual_memory):
        """Test get_memory_usage."""
        # Mock memory stats
        mock_mem = MagicMock()
        mock_mem.total = 8 * 1e9
        mock_mem.available = 4 * 1e9
        mock_mem.used = 4 * 1e9
        mock_mem.percent = 50.0
        mock_virtual_memory.return_value = mock_mem
        
        manager = MemoryManager(max_memory_gb=4)
        
        # Get memory usage
        stats = manager.get_memory_usage()
        
        # Check values
        assert stats['total_gb'] == 8.0
        assert stats['available_gb'] == 4.0
        assert stats['used_gb'] == 4.0
        assert stats['percent_used'] == 50.0
        assert stats['percent_free'] == 50.0
    
    @patch('psutil.virtual_memory')
    def test_log_memory_status(self, mock_virtual_memory, caplog):
        """Test log_memory_status."""
        # Mock memory stats
        mock_mem = MagicMock()
        mock_mem.total = 8 * 1e9
        mock_mem.available = 4 * 1e9
        mock_mem.used = 4 * 1e9
        mock_mem.percent = 50.0
        mock_virtual_memory.return_value = mock_mem
        
        manager = MemoryManager(max_memory_gb=4)
        
        # Log memory status
        manager.log_memory_status("Test context")
        
        # Check log message
        assert "Test context" in caplog.text
        assert "Memory: 4.0/8.0GB used (50.0%)" in caplog.text