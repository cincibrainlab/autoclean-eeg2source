"""Command-line interface for AutoClean EEG2Source."""

import os
import sys
import argparse
import glob
from pathlib import Path
from typing import List

from .core.converter import SequentialProcessor
from .core.memory_manager import MemoryManager
from .io.validators import EEGLABValidator
from .utils.logging import setup_logger


def find_set_files(input_path: str, recursive: bool = False) -> List[str]:
    """Find all .set files in the given path."""
    if os.path.isfile(input_path):
        return [input_path] if input_path.endswith('.set') else []
    
    if recursive:
        pattern = os.path.join(input_path, "**", "*.set")
        files = glob.glob(pattern, recursive=True)
    else:
        pattern = os.path.join(input_path, "*.set")
        files = glob.glob(pattern)
    
    return sorted(files)


def process_command(args):
    """Process EEG files to source localization."""
    # Setup logger
    logger = setup_logger(level=args.log_level, log_file=args.log_file)
    
    # Find input files
    set_files = find_set_files(args.input_path, args.recursive)
    
    if not set_files:
        logger.error(f"No .set files found in {args.input_path}")
        return 1
    
    logger.info(f"Found {len(set_files)} .set files to process")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize processor
    memory_manager = MemoryManager(max_memory_gb=args.max_memory)
    processor = SequentialProcessor(
        memory_manager=memory_manager,
        montage=args.montage,
        resample_freq=args.resample_freq,
        lambda2=args.lambda2
    )
    
    # Process files
    results = []
    for i, set_file in enumerate(set_files, 1):
        logger.info(f"Processing file {i}/{len(set_files)}: {os.path.basename(set_file)}")
        
        try:
            result = processor.process_file(set_file, args.output_dir)
            results.append(result)
            
            if result['status'] == 'success':
                logger.info(f"✓ Completed: {result['output_file']}")
            else:
                logger.error(f"Failed: {result['error']}")
                
        except Exception as e:
            logger.error(f"Unhandled error processing {set_file}: {e}")
            results.append({
                'input_file': set_file,
                'status': 'failed',
                'error': str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - successful
    
    logger.info("="*50)
    logger.info(f"Processing complete: {successful} successful, {failed} failed")
    
    if failed > 0:
        logger.error("Failed files:")
        for result in results:
            if result['status'] == 'failed':
                logger.error(f"  - {result['input_file']}: {result['error']}")
    
    return 0 if failed == 0 else 1


def validate_command(args):
    """Validate EEG files without processing."""
    logger = setup_logger(level=args.log_level)
    
    set_files = find_set_files(args.input_path, args.recursive)
    
    if not set_files:
        logger.error(f"No .set files found in {args.input_path}")
        return 1
    
    validator = EEGLABValidator()
    valid_count = 0
    
    for set_file in set_files:
        try:
            validator.validate_file_pair(set_file)
            info = validator.get_file_info(set_file)
            logger.info(f"Valid: {set_file}")
            logger.info(f"  - Channels: {info.get('n_channels', 'N/A')}")
            logger.info(f"  - Epochs: {info.get('n_epochs', 'N/A')}")
            logger.info(f"  - Sampling rate: {info.get('sfreq', 'N/A')}Hz")
            valid_count += 1
        except Exception as e:
            logger.error(f"Invalid: {set_file} - {e}")
    
    logger.info(f"Validation complete: {valid_count}/{len(set_files)} files valid")
    return 0 if valid_count == len(set_files) else 1


def info_command(args):
    """Display information about EEG files."""
    logger = setup_logger(level=args.log_level)
    
    if not os.path.exists(args.input_file):
        logger.error(f"File not found: {args.input_file}")
        return 1
    
    validator = EEGLABValidator()
    
    try:
        info = validator.get_file_info(args.input_file)
        
        logger.info(f"File: {args.input_file}")
        logger.info(f"Channels: {info.get('n_channels', 'N/A')}")
        logger.info(f"Epochs: {info.get('n_epochs', 'N/A')}")
        logger.info(f"Samples per epoch: {info.get('n_times', 'N/A')}")
        logger.info(f"Sampling rate: {info.get('sfreq', 'N/A')}Hz")
        logger.info(f"Duration per epoch: {info.get('duration', 'N/A')}s")
        
        if 'channels' in info:
            logger.info(f"Channel names: {info['channels']}")
        
        if info.get('fdt_size_mb'):
            logger.info(f"FDT file size: {info['fdt_size_mb']:.1f}MB")
            
        return 0
        
    except Exception as e:
        logger.error(f"Failed to read file info: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AutoClean EEG2Source - EEG source localization with DK atlas regions"
    )
    
    # Global options
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
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process EEG files")
    process_parser.add_argument(
        "input_path",
        help="Input .set file or directory"
    )
    process_parser.add_argument(
        "--output-dir",
        default="./output",
        help="Output directory"
    )
    process_parser.add_argument(
        "--montage",
        default="GSN-HydroCel-129",
        help="EEG montage"
    )
    process_parser.add_argument(
        "--resample-freq",
        type=float,
        default=250,
        help="Resampling frequency (Hz)"
    )
    process_parser.add_argument(
        "--lambda2",
        type=float,
        default=1.0/9.0,
        help="Regularization parameter"
    )
    process_parser.add_argument(
        "--max-memory",
        type=float,
        default=4.0,
        help="Maximum memory usage (GB)"
    )
    process_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search recursively for .set files"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate EEG files")
    validate_parser.add_argument(
        "input_path",
        help="Input .set file or directory"
    )
    validate_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search recursively for .set files"
    )
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Display file information")
    info_parser.add_argument(
        "input_file",
        help="Input .set file"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    # Route to appropriate command
    if args.command == "process":
        return process_command(args)
    elif args.command == "validate":
        return validate_command(args)
    elif args.command == "info":
        return info_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())