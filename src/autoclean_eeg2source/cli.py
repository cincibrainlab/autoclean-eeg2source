"""Command-line interface for AutoClean EEG2Source."""

import os
import sys
import argparse
import glob
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .core.converter import SequentialProcessor
from .core.robust_processor import RobustProcessor
from .core.memory_manager import MemoryManager
from .io.validators import EEGLABValidator
from .io.data_quality import QualityAssessor
from .utils.logging import setup_logger
from .utils.error_reporter import ErrorReporter, ErrorHandler


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
    
    # Setup error reporting if enabled
    error_reporter = None
    if args.error_dir:
        error_dir = os.path.abspath(args.error_dir)
        os.makedirs(error_dir, exist_ok=True)
        error_reporter = ErrorReporter(
            error_dir=error_dir,
            include_traceback=True,
            include_system_info=True
        )
        
        # Register global error handler
        if args.global_error_handler:
            ErrorHandler(error_reporter).register_global_handler()
    
    # Find input files
    set_files = find_set_files(args.input_path, args.recursive)
    
    if not set_files:
        logger.error(f"No .set files found in {args.input_path}")
        return 1
    
    logger.info(f"Found {len(set_files)} .set files to process")
    
    # Create output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize memory manager
    memory_manager = MemoryManager(max_memory_gb=args.max_memory)
    
    # Choose processor based on robustness mode
    if args.robust:
        logger.info("Using robust processor with recovery strategies")
        processor = RobustProcessor(
            memory_manager=memory_manager,
            montage=args.montage,
            resample_freq=args.resample_freq,
            lambda2=args.lambda2,
            recovery_mode=True,
            error_dir=args.error_dir
        )
        
        # Process files with recovery
        results = []
        for i, set_file in enumerate(set_files, 1):
            logger.info(f"Processing file {i}/{len(set_files)}: {os.path.basename(set_file)}")
            
            try:
                result = processor.process_with_recovery(set_file, output_dir)
                results.append(result)
                
                if result['status'] == 'success':
                    if result.get('recovery_successful', False):
                        logger.info(f"✓ Completed with recovery: {result['output_file']}")
                        if 'warnings' in result and result['warnings']:
                            for warning in result['warnings']:
                                logger.warning(f"  - {warning}")
                    else:
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
        
        # Recovery statistics
        recovery_stats = processor.get_recovery_stats()
        if recovery_stats['attempted'] > 0:
            logger.info("=" * 50)
            logger.info("Recovery Statistics:")
            logger.info(f"  - Attempted recoveries: {recovery_stats['attempted']}")
            logger.info(f"  - Successful recoveries: {recovery_stats['successful']}")
            logger.info(f"  - Failed recoveries: {recovery_stats['failed']}")
            logger.info(f"  - Success rate: {recovery_stats['success_rate']:.1f}%")
            
            if recovery_stats['strategies_used']:
                logger.info("Recovery strategies used:")
                for strategy, count in recovery_stats['strategies_used'].items():
                    logger.info(f"  - {strategy}: {count}")
            
    else:
        logger.info("Using standard sequential processor")
        processor = SequentialProcessor(
            memory_manager=memory_manager,
            montage=args.montage,
            resample_freq=args.resample_freq,
            lambda2=args.lambda2
        )
        
        # Process files without recovery
        results = []
        for i, set_file in enumerate(set_files, 1):
            logger.info(f"Processing file {i}/{len(set_files)}: {os.path.basename(set_file)}")
            
            try:
                result = processor.process_file(set_file, output_dir)
                results.append(result)
                
                if result['status'] == 'success':
                    logger.info(f"✓ Completed: {result['output_file']}")
                else:
                    logger.error(f"Failed: {result['error']}")
                    
            except Exception as e:
                error_message = str(e)
                logger.error(f"Unhandled error processing {set_file}: {error_message}")
                
                # Save error report if enabled
                if error_reporter:
                    context = {
                        'file_path': set_file,
                        'function_name': 'process_command',
                        'command': 'process',
                        'args': vars(args)
                    }
                    error_reporter.save_error(context, e)
                
                results.append({
                    'input_file': set_file,
                    'status': 'failed',
                    'error': error_message
                })
    
    # Save results summary if requested
    if args.save_summary:
        summary_file = os.path.join(output_dir, f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'args': vars(args),
                'results': results
            }, f, indent=2)
        logger.info(f"Saved processing summary to {summary_file}")
    
    # Print summary
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - successful
    
    logger.info("="*50)
    logger.info(f"Processing complete: {successful} successful, {failed} failed")
    
    if failed > 0:
        logger.error("Failed files:")
        for result in results:
            if result['status'] == 'failed':
                logger.error(f"  - {os.path.basename(result['input_file'])}: {result['error']}")
    
    return 0 if failed == 0 else 1


def validate_command(args):
    """Validate EEG files without processing."""
    logger = setup_logger(level=args.log_level, log_file=args.log_file)
    
    set_files = find_set_files(args.input_path, args.recursive)
    
    if not set_files:
        logger.error(f"No .set files found in {args.input_path}")
        return 1
    
    validator = EEGLABValidator()
    valid_count = 0
    validation_results = []
    
    for set_file in set_files:
        try:
            # Perform comprehensive validation
            report = validator.check_all(
                set_file, 
                montage_name=args.montage if args.check_montage else None
            )
            
            # Store result
            report['file_path'] = set_file
            validation_results.append(report)
            
            if report['valid']:
                logger.info(f"✓ Valid: {os.path.basename(set_file)}")
                
                # Get details from file validation
                file_validation = report.get('file_validation', {})
                if file_validation:
                    logger.info(f"  - Channels: {file_validation.get('n_channels', 'N/A')}")
                    logger.info(f"  - Epochs: {file_validation.get('n_epochs', 'N/A')}")
                    logger.info(f"  - Sampling rate: {file_validation.get('sfreq', 'N/A')}Hz")
                    
                    # Show warnings if any
                    if 'warnings' in file_validation and file_validation['warnings']:
                        for warning in file_validation['warnings']:
                            logger.warning(f"  - Warning: {warning}")
                
                # Show montage validation if performed
                if 'montage_validation' in report:
                    if report['montage_validation'].get('valid', False):
                        logger.info(f"  - Montage '{args.montage}' compatible")
                    else:
                        logger.warning(f"  - Montage '{args.montage}' has issues")
                        for error in report['montage_validation'].get('errors', []):
                            logger.warning(f"    - {error}")
                
                # Show quality issues if checked
                if 'quality_validation' in report:
                    if report['quality_validation'].get('issues_found', False):
                        logger.warning("  - Data quality issues found:")
                        for issue in report['quality_validation'].get('issues', []):
                            logger.warning(f"    - {issue}")
                    else:
                        logger.info("  - No data quality issues")
                
                valid_count += 1
            else:
                logger.error(f"✗ Invalid: {os.path.basename(set_file)}")
                
                # Show errors
                if 'file_validation' in report and not report['file_validation'].get('valid', False):
                    for error in report['file_validation'].get('errors', []):
                        logger.error(f"  - {error}")
                        
                if 'montage_validation' in report and not report['montage_validation'].get('valid', False):
                    for error in report['montage_validation'].get('errors', []):
                        logger.error(f"  - {error}")
                
                if 'error' in report:
                    logger.error(f"  - {report['error']}")
                
        except Exception as e:
            logger.error(f"Error validating {os.path.basename(set_file)}: {e}")
            validation_results.append({
                'file_path': set_file,
                'valid': False,
                'error': str(e)
            })
    
    # Save validation results if requested
    if args.save_validation:
        validation_file = os.path.join(
            args.output_dir or ".", 
            f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs(os.path.dirname(validation_file), exist_ok=True)
        
        with open(validation_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'args': vars(args),
                'results': validation_results
            }, f, indent=2)
        logger.info(f"Saved validation results to {validation_file}")
    
    logger.info(f"Validation complete: {valid_count}/{len(set_files)} files valid")
    return 0 if valid_count == len(set_files) else 1


def info_command(args):
    """Display information about EEG files."""
    logger = setup_logger(level=args.log_level, log_file=args.log_file)
    
    if not os.path.exists(args.input_file):
        logger.error(f"File not found: {args.input_file}")
        return 1
    
    validator = EEGLABValidator()
    
    try:
        info = validator.get_file_info(args.input_file)
        
        # Basic info header
        logger.info("=" * 50)
        logger.info(f"File Information: {os.path.basename(args.input_file)}")
        logger.info("=" * 50)
        
        if info.get('valid', False):
            # File details
            logger.info("File Details:")
            logger.info(f"  - Path: {args.input_file}")
            logger.info(f"  - SET file size: {info.get('set_size_mb', 'N/A'):.1f} MB")
            if info.get('fdt_exists'):
                logger.info(f"  - FDT file: Present ({info.get('fdt_size_mb', 'N/A'):.1f} MB)")
            else:
                logger.info("  - FDT file: Not found or not needed")
            
            # Data structure
            logger.info("\nData Structure:")
            logger.info(f"  - Channels: {info.get('n_channels', 'N/A')}")
            logger.info(f"  - Epochs: {info.get('n_epochs', 'N/A')}")
            logger.info(f"  - Samples per epoch: {info.get('n_times', 'N/A')}")
            logger.info(f"  - Sampling rate: {info.get('sfreq', 'N/A')} Hz")
            logger.info(f"  - Duration: {info.get('duration_str', 'N/A')}")
            
            # Channel preview
            if 'channel_preview' in info:
                logger.info("\nChannel Names:")
                logger.info(f"  - {', '.join(info['channel_preview'])}")
            
            # Memory estimate
            if 'estimated_memory_mb' in info:
                memory_mb = info['estimated_memory_mb']
                logger.info("\nProcessing Information:")
                logger.info(f"  - Estimated memory usage: {memory_mb:.1f} MB "
                            f"({memory_mb/1024:.2f} GB)")
            
            # Any warnings
            if 'warnings' in info and info['warnings']:
                logger.warning("\nWarnings:")
                for warning in info['warnings']:
                    logger.warning(f"  - {warning}")
        else:
            # Show errors
            logger.error("File validation failed:")
            if 'errors' in info:
                for error in info['errors']:
                    logger.error(f"  - {error}")
            if 'error' in info:
                logger.error(f"  - {info['error']}")
        
        # Option to save report
        if args.save_info:
            info_file = os.path.join(
                args.output_dir or ".",
                f"file_info_{os.path.basename(args.input_file).split('.')[0]}.json"
            )
            os.makedirs(os.path.dirname(info_file), exist_ok=True)
            
            with open(info_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'info': info
                }, f, indent=2)
            logger.info(f"\nSaved detailed info to {info_file}")
            
        return 0 if info.get('valid', False) else 1
        
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
    # New robust options
    process_parser.add_argument(
        "--robust",
        action="store_true",
        help="Use robust processing with error recovery"
    )
    process_parser.add_argument(
        "--error-dir",
        help="Directory to save error reports"
    )
    process_parser.add_argument(
        "--global-error-handler",
        action="store_true",
        help="Register global error handler"
    )
    process_parser.add_argument(
        "--save-summary",
        action="store_true",
        help="Save processing summary to JSON file"
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
    # Enhanced validate options
    validate_parser.add_argument(
        "--check-montage",
        action="store_true",
        help="Check montage compatibility"
    )
    validate_parser.add_argument(
        "--montage",
        default="GSN-HydroCel-129",
        help="Montage to check (if --check-montage is used)"
    )
    validate_parser.add_argument(
        "--save-validation",
        action="store_true",
        help="Save validation results to file"
    )
    validate_parser.add_argument(
        "--output-dir",
        help="Output directory for validation results"
    )
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Display file information")
    info_parser.add_argument(
        "input_file",
        help="Input .set file"
    )
    # Enhanced info options
    info_parser.add_argument(
        "--save-info",
        action="store_true",
        help="Save detailed info to file"
    )
    info_parser.add_argument(
        "--output-dir",
        help="Output directory for info file"
    )
    
    # Quality command (new)
    quality_parser = subparsers.add_parser("quality", help="Assess data quality")
    quality_parser.add_argument(
        "input_file",
        help="Input .set file"
    )
    quality_parser.add_argument(
        "--fix",
        action="store_true",
        help="Try to fix quality issues"
    )
    quality_parser.add_argument(
        "--output-dir",
        help="Output directory for fixed file"
    )
    
    # Recover command (new)
    recover_parser = subparsers.add_parser("recover", help="Attempt to recover a problematic file")
    recover_parser.add_argument(
        "input_file",
        help="Input .set file to recover"
    )
    recover_parser.add_argument(
        "output_dir",
        help="Output directory for recovered file"
    )
    recover_parser.add_argument(
        "--strategy",
        choices=["auto", "file", "montage", "quality", "memory", "generic"],
        default="auto",
        help="Recovery strategy to attempt"
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
    elif args.command == "quality":
        # TODO: Implement quality command in next version
        print("Quality command not yet implemented")
        return 1
    elif args.command == "recover":
        # TODO: Implement recover command in next version
        print("Recovery command not yet implemented")
        return 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())