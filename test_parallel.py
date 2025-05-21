"""Test the parallel processor with batch processing."""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autoclean_eeg2source.core.parallel_processor import ParallelProcessor
from autoclean_eeg2source.core.memory_manager import MemoryManager
from autoclean_eeg2source.utils.logging import setup_logger


def test_parallel_processor():
    """Test parallel processor with batch processing."""
    logger = setup_logger(level="INFO")
    
    # Create output directory
    output_dir = "./test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize components
    memory_manager = MemoryManager(max_memory_gb=4)
    processor = ParallelProcessor(
        memory_manager=memory_manager,
        montage="GSN-HydroCel-129",
        resample_freq=250,
        n_jobs=2,  # Use 2 workers
        batch_size=4,
        parallel_method='threads'  # Use threads for testing to avoid pickling issues
    )
    
    # Define test file
    set_file = "example_data/3367_SLStructured_PostICA_epoched.set"
    
    logger.info(f"Testing parallel processor with {set_file}")
    
    try:
        # Process the file directly first
        logger.info("Processing file directly...")
        result = processor.process_file(set_file, output_dir)
        
        if result['status'] == 'success':
            logger.info(f"Direct processing succeeded! Output: {result['output_file']}")
        else:
            logger.error(f"Direct processing failed: {result['error']}")
        
        # Now try batch processing
        file_list = [set_file]
        logger.info(f"Processing in batch mode with {len(file_list)} files...")
        
        # Test the batch processing
        results = processor.process_batch(file_list, output_dir, max_workers=2)
        
        # Check results
        for i, result in enumerate(results):
            if result['status'] == 'success':
                logger.info(f"Batch item {i} succeeded! Output: {result['output_file']}")
            else:
                logger.error(f"Batch item {i} failed: {result['error']}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_parallel_processor()