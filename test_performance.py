#!/usr/bin/env python
"""
Performance benchmark script for AutoClean EEG2Source.

This script runs performance tests comparing different processing strategies.
"""

import os
import sys
import argparse
import logging
import glob
from typing import List

from src.autoclean_eeg2source.core.converter import SequentialProcessor
from src.autoclean_eeg2source.core.parallel_processor import ParallelProcessor, CachedProcessor
from src.autoclean_eeg2source.core.optimized_memory import OptimizedMemoryManager
from src.autoclean_eeg2source.utils.benchmarking import (
    PerformanceBenchmark, run_standard_benchmark
)


def find_test_files(input_path: str, pattern: str = "*.set", max_files: int = 5) -> List[str]:
    """Find test files for benchmarking."""
    if os.path.isfile(input_path) and input_path.endswith('.set'):
        return [input_path]
    
    # Find files matching pattern
    files = glob.glob(os.path.join(input_path, pattern))
    
    # Limit number of files
    return sorted(files)[:max_files]


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure logging
    log_config = {
        'level': numeric_level,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
    
    if log_file:
        log_config['filename'] = log_file
        log_config['filemode'] = 'w'
    
    logging.basicConfig(**log_config)


def main():
    """Main benchmark entry point."""
    parser = argparse.ArgumentParser(
        description="Performance benchmark for AutoClean EEG2Source"
    )
    
    # Input and output options
    parser.add_argument(
        "--input-path",
        required=True,
        help="Path to input .set file or directory with .set files"
    )
    parser.add_argument(
        "--output-dir",
        default="./benchmark_output",
        help="Output directory for benchmark results"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5,
        help="Maximum number of files to process"
    )
    
    # Benchmark options
    parser.add_argument(
        "--benchmark-type",
        choices=["all", "sequential", "parallel", "cached", "gpu"],
        default="all",
        help="Type of benchmark to run"
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=-1,
        help="Number of parallel jobs (-1 for all cores)"
    )
    parser.add_argument(
        "--memory",
        type=float,
        default=4.0,
        help="Maximum memory usage in GB"
    )
    parser.add_argument(
        "--enable-cache",
        action="store_true",
        help="Enable caching benchmark"
    )
    parser.add_argument(
        "--enable-gpu",
        action="store_true",
        help="Enable GPU benchmark"
    )
    
    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    parser.add_argument(
        "--log-file",
        help="Log file path"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Find test files
    input_files = find_test_files(args.input_path, max_files=args.max_files)
    
    if not input_files:
        logging.error(f"No .set files found in {args.input_path}")
        return 1
    
    logging.info(f"Found {len(input_files)} files for benchmarking")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run benchmark based on type
    if args.benchmark_type == "all":
        # Run standard benchmark comparing all processor types
        results = run_standard_benchmark(
            input_files=input_files,
            output_dir=args.output_dir,
            n_jobs=args.n_jobs,
            enable_cache=args.enable_cache,
            enable_gpu=args.enable_gpu,
            max_memory_gb=args.memory
        )
        
        # Log summary
        logging.info("Benchmark completed")
        if 'speedups' in results:
            logging.info("Relative speedups:")
            for processor, speedup in results['speedups'].items():
                logging.info(f"  - {processor}: {speedup:.2f}x")
    
    elif args.benchmark_type == "sequential":
        # Benchmark sequential processor only
        benchmark = PerformanceBenchmark(
            output_dir=os.path.join(args.output_dir, "benchmark_results")
        )
        
        processor = SequentialProcessor(
            memory_manager=OptimizedMemoryManager(max_memory_gb=args.memory)
        )
        
        results = benchmark.benchmark_processor(
            processor=processor,
            input_files=input_files,
            output_dir=args.output_dir,
            test_name="sequential_benchmark"
        )
        
        logging.info("Sequential benchmark completed")
    
    elif args.benchmark_type == "parallel":
        # Benchmark parallel processor only
        benchmark = PerformanceBenchmark(
            output_dir=os.path.join(args.output_dir, "benchmark_results")
        )
        
        processor = ParallelProcessor(
            n_jobs=args.n_jobs,
            memory_manager=OptimizedMemoryManager(max_memory_gb=args.memory)
        )
        
        results = benchmark.benchmark_processor(
            processor=processor,
            input_files=input_files,
            output_dir=args.output_dir,
            test_name="parallel_benchmark"
        )
        
        logging.info("Parallel benchmark completed")
    
    elif args.benchmark_type == "cached":
        # Benchmark cached processor only
        cache_dir = os.path.join(args.output_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        benchmark = PerformanceBenchmark(
            output_dir=os.path.join(args.output_dir, "benchmark_results")
        )
        
        processor = CachedProcessor(
            n_jobs=args.n_jobs,
            memory_manager=OptimizedMemoryManager(max_memory_gb=args.memory),
            cache_dir=cache_dir
        )
        
        results = benchmark.benchmark_processor(
            processor=processor,
            input_files=input_files,
            output_dir=args.output_dir,
            test_name="cached_benchmark"
        )
        
        logging.info("Cached benchmark completed")
    
    elif args.benchmark_type == "gpu":
        # Benchmark GPU processor only
        try:
            from src.autoclean_eeg2source.core.gpu_processor import GPUProcessor, check_gpu_availability
            
            gpu_info = check_gpu_availability()
            
            if gpu_info['gpu_count'] == 0:
                logging.error("No GPU available for benchmarking")
                return 1
            
            benchmark = PerformanceBenchmark(
                output_dir=os.path.join(args.output_dir, "benchmark_results")
            )
            
            processor = GPUProcessor(
                n_jobs=args.n_jobs,
                memory_manager=OptimizedMemoryManager(max_memory_gb=args.memory),
                gpu_backend='auto'
            )
            
            results = benchmark.benchmark_processor(
                processor=processor,
                input_files=input_files,
                output_dir=args.output_dir,
                test_name="gpu_benchmark"
            )
            
            logging.info("GPU benchmark completed")
            
        except ImportError as e:
            logging.error(f"Failed to import GPU processor: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())