"""Test the processor with synthetic data."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autoclean_eeg2source.core.converter import SequentialProcessor
from autoclean_eeg2source.core.memory_manager import MemoryManager
from autoclean_eeg2source.utils.logging import setup_logger


def test_synthetic_data():
    """Test with synthetic EEG data."""
    logger = setup_logger(level="INFO")
    
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
    
    # Use synthetic test file
    set_file = "test_data/test_epochs.set"
    
    logger.info(f"Testing with synthetic data: {set_file}")
    
    try:
        result = processor.process_file(set_file, output_dir)
        
        if result['status'] == 'success':
            logger.info(f"✓ Success! Output: {result['output_file']}")
            
            # Check output file
            if os.path.exists(result['output_file']):
                file_size = os.path.getsize(result['output_file']) / (1024 * 1024)
                logger.info(f"✓ Output file created: {file_size:.1f} MB")
            
        else:
            logger.error(f"Failed: {result['error']}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_synthetic_data()