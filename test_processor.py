"""Test the processor with available data."""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autoclean_eeg2source.core.converter import SequentialProcessor
from autoclean_eeg2source.core.memory_manager import MemoryManager
from autoclean_eeg2source.utils.logging import setup_logger


def test_with_embedded_data():
    """Test with file that has embedded data."""
    logger = setup_logger(level="DEBUG")
    
    # Create output directory
    output_dir = "./test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize components
    memory_manager = MemoryManager(max_memory_gb=4)
    processor = SequentialProcessor(
        memory_manager=memory_manager,
        montage="GSN-HydroCel-129",
        resample_freq=250
    )
    
    # Try to read the .set file directly (it might have embedded data)
    set_file = "example_data/3367_SLStructured_PostICA_epoched.set"
    
    logger.info(f"Testing with {set_file}")
    
    try:
        # Let's first check the file size
        file_size = os.path.getsize(set_file) / (1024 * 1024)  # MB
        logger.info(f"File size: {file_size:.1f} MB")
        
        if file_size > 10:
            logger.info("Large .set file - data likely embedded")
        
        # Try to process
        result = processor.process_file(set_file, output_dir)
        
        if result['status'] == 'success':
            logger.info(f"Success! Output: {result['output_file']}")
        else:
            logger.error(f"Failed: {result['error']}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_with_embedded_data()