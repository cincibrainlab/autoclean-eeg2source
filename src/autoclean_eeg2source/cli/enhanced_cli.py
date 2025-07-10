"""
Enhanced CLI interface with 80s retro styling and comprehensive help.

This module provides the main enhanced CLI interface that integrates all
visual components and interactive features.
"""

import argparse
import sys
import os
from typing import Optional

# Import visual components
try:
    from .visual import RetroColors
    from .ascii_art import ASCIIArtGenerator
    from .system_info import SystemInfoDisplay
    from .help_system import EnhancedHelpSystem
    from .wizard import CommandWizard
    from .progress import VisualProgressTracker
    VISUAL_COMPONENTS_AVAILABLE = True
except ImportError:
    VISUAL_COMPONENTS_AVAILABLE = False

from .. import __version__


class EnhancedCLI:
    """Enhanced CLI interface with visual enhancements."""
    
    def __init__(self):
        """Initialize enhanced CLI."""
        self.visual_components_available = VISUAL_COMPONENTS_AVAILABLE
        
        if self.visual_components_available:
            self.colors = RetroColors()
            self.ascii_gen = ASCIIArtGenerator(self.colors)
            self.system_info = SystemInfoDisplay(self.colors, self.ascii_gen)
            self.help_system = EnhancedHelpSystem(self.colors, self.ascii_gen)
            self.wizard = CommandWizard(self.colors, self.ascii_gen)
            self.progress_tracker = VisualProgressTracker(self.colors, self.ascii_gen)
        else:
            self.colors = None
            self.ascii_gen = None
            self.system_info = None
            self.help_system = None
            self.wizard = None
            self.progress_tracker = None
    
    def create_enhanced_parser(self) -> argparse.ArgumentParser:
        """
        Create argument parser with enhanced help options.
        
        Returns
        -------
        ArgumentParser
            Enhanced argument parser
        """
        # Custom formatter to preserve formatting
        class CustomFormatter(argparse.RawDescriptionHelpFormatter):
            def _format_action_invocation(self, action):
                if not action.option_strings:
                    return super()._format_action_invocation(action)
                default = super()._format_action_invocation(action)
                return default
        
        parser = argparse.ArgumentParser(
            description="AutoClean EEG2Source - EEG source localization with DK atlas regions",
            formatter_class=CustomFormatter,
            epilog=self._get_epilog_text(),
            add_help=False  # We'll handle help ourselves
        )
        
        # Enhanced help options (these take precedence)
        enhanced_group = parser.add_argument_group('Enhanced Help & Tools')
        enhanced_group.add_argument(
            '--help', '-h',
            action='store_true',
            help='Show enhanced quick help'
        )
        enhanced_group.add_argument(
            '--help-detailed',
            action='store_true',
            help='Show comprehensive help with all parameters'
        )
        enhanced_group.add_argument(
            '--examples',
            action='store_true',
            help='Show categorized examples gallery'
        )
        enhanced_group.add_argument(
            '--wizard',
            action='store_true',
            help='Start interactive command builder'
        )
        enhanced_group.add_argument(
            '--system-info',
            action='store_true',
            help='Display detailed system information'
        )
        
        # Version option
        parser.add_argument(
            "--version",
            action="version",
            version=f"autoclean-eeg2source {__version__}"
        )
        
        # Global options
        global_group = parser.add_argument_group('Global Options')
        global_group.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Set logging verbosity level"
        )
        global_group.add_argument(
            "--log-file",
            help="Write logs to specified file"
        )
        global_group.add_argument(
            "--no-color",
            action="store_true",
            help="Disable colored output"
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(
            dest="command",
            help="Available commands",
            metavar="{process,validate,info,quality,recover,benchmark}",
            title="Commands"
        )
        
        # Process command
        self._add_process_parser(subparsers)
        
        # Validate command
        self._add_validate_parser(subparsers)
        
        # Info command
        self._add_info_parser(subparsers)
        
        # Quality command
        self._add_quality_parser(subparsers)
        
        # Recover command
        self._add_recover_parser(subparsers)
        
        # Benchmark command
        self._add_benchmark_parser(subparsers)
        
        return parser
    
    def _get_epilog_text(self) -> str:
        """Get epilog text for help."""
        if self.colors:
            return f"""
{self.colors.YELLOW}🚀 Quick Start Examples:{self.colors.RESET}
  {self.colors.WHITE}Single file:{self.colors.RESET}     autoclean-eeg2source process data.set
  {self.colors.WHITE}Directory:{self.colors.RESET}      autoclean-eeg2source process ./eeg_data
  {self.colors.WHITE}Parallel:{self.colors.RESET}       autoclean-eeg2source process ./data --parallel --n-jobs 8
  {self.colors.WHITE}Validation:{self.colors.RESET}     autoclean-eeg2source validate data.set

{self.colors.YELLOW}📚 More Help:{self.colors.RESET}
  {self.colors.GREEN}--help-detailed{self.colors.RESET}  Show comprehensive parameter reference
  {self.colors.GREEN}--examples{self.colors.RESET}       Browse 15+ categorized examples
  {self.colors.GREEN}--wizard{self.colors.RESET}         Interactive command builder
  {self.colors.GREEN}--system-info{self.colors.RESET}    Display system information

{self.colors.BLUE}🔗 Links:{self.colors.RESET}
  GitHub: {self.colors.UNDERLINE}https://github.com/cincibrainlab/autoclean-eeg2source{self.colors.RESET}
  PyPI: {self.colors.UNDERLINE}https://pypi.org/project/autoclean-eeg2source{self.colors.RESET}
"""
        else:
            return """
Quick Start Examples:
  Single file:     autoclean-eeg2source process data.set
  Directory:       autoclean-eeg2source process ./eeg_data
  Parallel:        autoclean-eeg2source process ./data --parallel --n-jobs 8
  Validation:      autoclean-eeg2source validate data.set

More Help:
  --help-detailed  Show comprehensive parameter reference
  --examples       Browse 15+ categorized examples
  --wizard         Interactive command builder
  --system-info    Display system information

Links:
  GitHub: https://github.com/cincibrainlab/autoclean-eeg2source
  PyPI: https://pypi.org/project/autoclean-eeg2source
"""
    
    def _add_process_parser(self, subparsers):
        """Add process command parser."""
        process_parser = subparsers.add_parser(
            "process",
            help="Process EEG files to source localization",
            description="Convert EEG data to source-localized signals using Desikan-Killiany atlas"
        )
        
        # Input/Output
        io_group = process_parser.add_argument_group('Input/Output')
        io_group.add_argument(
            "input_path",
            help="Input .set file or directory containing .set files"
        )
        io_group.add_argument(
            "--output-dir",
            default="./output",
            help="Output directory for processed files (default: ./output)"
        )
        io_group.add_argument(
            "--recursive",
            action="store_true",
            help="Search subdirectories recursively for .set files"
        )
        
        # Processing options
        processing_group = process_parser.add_argument_group('Processing Options')
        processing_group.add_argument(
            "--montage",
            default="standard_1020",
            choices=["standard_1020", "standard_1005", "GSN-HydroCel-32", "GSN-HydroCel-64", 
                    "GSN-HydroCel-128", "GSN-HydroCel-256", "biosemi64", "biosemi128"],
            help="EEG montage/channel layout (default: standard_1020)"
        )
        processing_group.add_argument(
            "--resample-freq",
            type=float,
            default=250.0,
            help="Target sampling frequency in Hz (default: 250)"
        )
        processing_group.add_argument(
            "--lambda2",
            type=float,
            default=1.0/9.0,
            help="Regularization parameter for inverse solution (default: 1/9)"
        )
        
        # Processing modes
        mode_group = process_parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            "--parallel",
            action="store_true",
            help="Enable parallel processing for batch operations"
        )
        mode_group.add_argument(
            "--robust",
            action="store_true",
            help="Use robust processing with enhanced error recovery"
        )
        mode_group.add_argument(
            "--gpu",
            action="store_true",
            help="Enable GPU acceleration (requires CUDA)"
        )
        
        # Parallel processing options
        parallel_group = process_parser.add_argument_group('Parallel Processing')
        parallel_group.add_argument(
            "--n-jobs",
            type=int,
            default=4,
            help="Number of parallel jobs (default: 4)"
        )
        parallel_group.add_argument(
            "--batch-processing",
            action="store_true",
            help="Enable optimized batch processing mode"
        )
        parallel_group.add_argument(
            "--enable-cache",
            action="store_true",
            help="Enable result caching for similar files"
        )
        
        # Memory and performance
        perf_group = process_parser.add_argument_group('Performance & Memory')
        perf_group.add_argument(
            "--memory-limit",
            help="Memory usage limit (e.g., 4GB, 2048MB)"
        )
        perf_group.add_argument(
            "--chunk-size",
            type=int,
            help="Processing chunk size for large files"
        )
        
        # Error handling
        error_group = process_parser.add_argument_group('Error Handling')
        error_group.add_argument(
            "--error-dir",
            help="Directory to save error reports and problematic files"
        )
        error_group.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Continue processing other files if some fail"
        )
    
    def _add_validate_parser(self, subparsers):
        """Add validate command parser."""
        validate_parser = subparsers.add_parser(
            "validate",
            help="Validate EEG files without processing",
            description="Check file format, montage compatibility, and data quality"
        )
        
        validate_parser.add_argument(
            "input_path",
            help="Input .set file or directory to validate"
        )
        validate_parser.add_argument(
            "--recursive",
            action="store_true",
            help="Validate files in subdirectories recursively"
        )
        validate_parser.add_argument(
            "--montage",
            help="Check compatibility with specific montage"
        )
        validate_parser.add_argument(
            "--check-quality",
            action="store_true",
            help="Perform detailed data quality assessment"
        )
        validate_parser.add_argument(
            "--save-validation",
            action="store_true",
            help="Save detailed validation report to file"
        )
    
    def _add_info_parser(self, subparsers):
        """Add info command parser."""
        info_parser = subparsers.add_parser(
            "info",
            help="Display detailed file information",
            description="Show comprehensive metadata about EEG files"
        )
        
        info_parser.add_argument(
            "input_path",
            help="Input .set file to analyze"
        )
        info_parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed technical information"
        )
        info_parser.add_argument(
            "--channels",
            action="store_true",
            help="List all channel names and types"
        )
    
    def _add_quality_parser(self, subparsers):
        """Add quality command parser."""
        quality_parser = subparsers.add_parser(
            "quality",
            help="Assess data quality metrics",
            description="Analyze EEG data quality and identify potential issues"
        )
        
        quality_parser.add_argument(
            "input_path",
            help="Input .set file or directory to assess"
        )
        quality_parser.add_argument(
            "--recursive",
            action="store_true",
            help="Assess files in subdirectories recursively"
        )
        quality_parser.add_argument(
            "--save-report",
            action="store_true",
            help="Save quality assessment report"
        )
    
    def _add_recover_parser(self, subparsers):
        """Add recover command parser."""
        recover_parser = subparsers.add_parser(
            "recover",
            help="Attempt to recover problematic files",
            description="Try to fix and reprocess files that previously failed"
        )
        
        recover_parser.add_argument(
            "input_path",
            help="Directory containing failed files or error reports"
        )
        recover_parser.add_argument(
            "--output-dir",
            default="./recovered",
            help="Output directory for recovered files"
        )
        recover_parser.add_argument(
            "--conservative",
            action="store_true",
            help="Use conservative recovery settings"
        )
    
    def _add_benchmark_parser(self, subparsers):
        """Add benchmark command parser."""
        benchmark_parser = subparsers.add_parser(
            "benchmark",
            help="Run performance benchmarks",
            description="Test processing performance with different configurations"
        )
        
        benchmark_parser.add_argument(
            "input_path",
            help="Test file or directory for benchmarking"
        )
        benchmark_parser.add_argument(
            "--modes",
            nargs="+",
            choices=["sequential", "parallel", "robust", "gpu"],
            default=["sequential", "parallel"],
            help="Processing modes to benchmark"
        )
        benchmark_parser.add_argument(
            "--iterations",
            type=int,
            default=3,
            help="Number of benchmark iterations"
        )
    
    def handle_enhanced_options(self, args) -> bool:
        """
        Handle enhanced CLI options.
        
        Parameters
        ----------
        args : Namespace
            Parsed arguments
            
        Returns
        -------
        bool
            True if an enhanced option was handled (should exit)
        """
        if args.no_color and self.colors:
            self.colors = RetroColors(force_colors=False)
            if self.ascii_gen:
                self.ascii_gen.colors = self.colors
            if self.system_info:
                self.system_info.colors = self.colors
            if self.help_system:
                self.help_system.colors = self.colors
            if self.wizard:
                self.wizard.colors = self.colors
            if self.progress_tracker:
                self.progress_tracker.colors = self.colors
        
        # Handle enhanced help options
        if args.help:
            if self.help_system:
                print(self.help_system.show_quick_help())
            else:
                print("Help system not available. Use standard --help.")
            return True
        
        if args.help_detailed:
            if self.help_system:
                print(self.help_system.show_detailed_help())
            else:
                print("Detailed help not available.")
            return True
        
        if args.examples:
            if self.help_system:
                print(self.help_system.show_examples_gallery())
            else:
                print("Examples gallery not available.")
            return True
        
        if args.wizard:
            if self.wizard:
                command = self.wizard.run_wizard()
                if command:
                    if self.colors:
                        print(f"\n{self.colors.GREEN}Wizard completed successfully!{self.colors.RESET}")
                        print(f"{self.colors.CYAN}Run the generated command to start processing.{self.colors.RESET}")
                    else:
                        print("\nWizard completed successfully!")
                        print("Run the generated command to start processing.")
            else:
                print("Interactive wizard not available.")
            return True
        
        if args.system_info:
            if self.system_info:
                print(self.system_info.display_detailed_system_info())
            else:
                print("System information not available.")
            return True
        
        return False
    
    def should_display_header(self, args) -> bool:
        """
        Determine if header should be displayed.
        
        Parameters
        ----------
        args : Namespace
            Parsed arguments
            
        Returns
        -------
        bool
            True if header should be shown
        """
        # Show header for interactive use or specific commands
        if len(sys.argv) == 1:  # No arguments
            return True
        
        # Show for enhanced help options
        enhanced_options = ['help', 'help_detailed', 'examples', 'wizard', 'system_info']
        if any(getattr(args, opt, False) for opt in enhanced_options):
            return True
        
        # Show for main commands if not in batch mode
        if hasattr(args, 'command') and args.command:
            return not getattr(args, 'batch_processing', False)
        
        return False
    
    def display_startup_banner(self):
        """Display startup banner."""
        if self.system_info:
            print(self.system_info.display_startup_info())
        else:
            print("AutoClean EEG2Source")
            print("EEG Source Localization with Desikan-Killiany Atlas")
            print("=" * 60)
    
    def get_progress_tracker(self):
        """Get progress tracker instance."""
        return self.progress_tracker


def create_enhanced_cli() -> EnhancedCLI:
    """
    Create enhanced CLI instance.
    
    Returns
    -------
    EnhancedCLI
        Enhanced CLI instance
    """
    return EnhancedCLI()