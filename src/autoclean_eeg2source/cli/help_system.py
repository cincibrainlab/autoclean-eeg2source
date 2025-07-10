"""
Enhanced help system with comprehensive examples and interactive features.

This module provides multi-level help including quick help, detailed documentation,
examples gallery, and interactive command building.
"""

import textwrap
from typing import Dict, List, Tuple, Optional


class EnhancedHelpSystem:
    """Comprehensive help system with visual enhancements."""
    
    def __init__(self, colors=None, ascii_gen=None):
        """
        Initialize enhanced help system.
        
        Parameters
        ----------
        colors : RetroColors, optional
            Color system instance for styling
        ascii_gen : ASCIIArtGenerator, optional
            ASCII art generator instance
        """
        self.colors = colors
        self.ascii_gen = ascii_gen
        self.examples = self._load_examples()
        self.detailed_help = self._load_detailed_help()
    
    def show_quick_help(self) -> str:
        """
        Enhanced version of standard --help.
        
        Returns
        -------
        str
            Formatted quick help text
        """
        help_text = []
        
        if self.colors:
            help_text.extend([
                f"{self.colors.CYAN}{'=' * 60}{self.colors.RESET}",
                f"{self.colors.MAGENTA}🧠 AutoClean EEG2Source - Quick Help{self.colors.RESET}",
                f"{self.colors.CYAN}{'=' * 60}{self.colors.RESET}",
                "",
                f"{self.colors.WHITE}EEG Source Localization with Desikan-Killiany Atlas Regions{self.colors.RESET}",
                "",
                f"{self.colors.YELLOW}📖 BASIC USAGE:{self.colors.RESET}",
                f"  {self.colors.GREEN}autoclean-eeg2source process <file_or_directory>{self.colors.RESET}",
                "",
                f"{self.colors.YELLOW}🚀 QUICK START EXAMPLES:{self.colors.RESET}",
                f"  {self.colors.WHITE}Single file:{self.colors.RESET}     autoclean-eeg2source process data.set",
                f"  {self.colors.WHITE}Directory:{self.colors.RESET}      autoclean-eeg2source process ./eeg_data",
                f"  {self.colors.WHITE}Parallel:{self.colors.RESET}       autoclean-eeg2source process ./data --parallel --n-jobs 8",
                f"  {self.colors.WHITE}Validation:{self.colors.RESET}     autoclean-eeg2source validate data.set",
                "",
                f"{self.colors.YELLOW}🔧 MAIN COMMANDS:{self.colors.RESET}",
                f"  {self.colors.CYAN}process{self.colors.RESET}         Process EEG files to source localization",
                f"  {self.colors.CYAN}validate{self.colors.RESET}        Validate EEG files without processing",
                f"  {self.colors.CYAN}info{self.colors.RESET}            Display file information",
                f"  {self.colors.CYAN}quality{self.colors.RESET}         Assess data quality",
                "",
                f"{self.colors.YELLOW}📚 MORE HELP:{self.colors.RESET}",
                f"  {self.colors.GREEN}--help-detailed{self.colors.RESET}  Show comprehensive help with all parameters",
                f"  {self.colors.GREEN}--examples{self.colors.RESET}       Show categorized examples gallery",
                f"  {self.colors.GREEN}--wizard{self.colors.RESET}         Start interactive command builder",
                f"  {self.colors.GREEN}--system-info{self.colors.RESET}    Display system information",
                "",
                f"{self.colors.BLUE}🔗 Links:{self.colors.RESET}",
                f"  GitHub: {self.colors.UNDERLINE}https://github.com/cincibrainlab/autoclean-eeg2source{self.colors.RESET}",
                f"  PyPI: {self.colors.UNDERLINE}https://pypi.org/project/autoclean-eeg2source{self.colors.RESET}",
                ""
            ])
        else:
            help_text.extend([
                "=" * 60,
                "AutoClean EEG2Source - Quick Help",
                "=" * 60,
                "",
                "EEG Source Localization with Desikan-Killiany Atlas Regions",
                "",
                "BASIC USAGE:",
                "  autoclean-eeg2source process <file_or_directory>",
                "",
                "QUICK START EXAMPLES:",
                "  Single file:     autoclean-eeg2source process data.set",
                "  Directory:       autoclean-eeg2source process ./eeg_data",
                "  Parallel:        autoclean-eeg2source process ./data --parallel --n-jobs 8",
                "  Validation:      autoclean-eeg2source validate data.set",
                "",
                "MAIN COMMANDS:",
                "  process         Process EEG files to source localization",
                "  validate        Validate EEG files without processing",
                "  info            Display file information",
                "  quality         Assess data quality",
                "",
                "MORE HELP:",
                "  --help-detailed  Show comprehensive help with all parameters",
                "  --examples       Show categorized examples gallery",
                "  --wizard         Start interactive command builder",
                "  --system-info    Display system information",
                "",
                "Links:",
                "  GitHub: https://github.com/cincibrainlab/autoclean-eeg2source",
                "  PyPI: https://pypi.org/project/autoclean-eeg2source",
                ""
            ])
        
        return "\n".join(help_text)
    
    def show_detailed_help(self) -> str:
        """
        Comprehensive help with all parameters and explanations.
        
        Returns
        -------
        str
            Formatted detailed help text
        """
        help_sections = []
        
        if self.ascii_gen:
            help_sections.append(self.ascii_gen.generate_header())
            help_sections.append("")
        
        for section_name, section_content in self.detailed_help.items():
            if self.ascii_gen:
                help_sections.append(
                    self.ascii_gen.generate_status_box(section_name.upper(), section_content)
                )
            else:
                help_sections.append(f"=== {section_name.upper()} ===")
                for key, value in section_content.items():
                    help_sections.append(f"{key}: {value}")
            help_sections.append("")
        
        return "\n".join(help_sections)
    
    def show_examples_gallery(self) -> str:
        """
        Categorized examples with copy-paste commands.
        
        Returns
        -------
        str
            Formatted examples gallery
        """
        gallery_text = []
        
        if self.ascii_gen:
            gallery_text.append(self.ascii_gen.generate_header())
            gallery_text.append("")
        
        if self.colors:
            gallery_text.extend([
                f"{self.colors.CYAN}{'=' * 70}{self.colors.RESET}",
                f"{self.colors.MAGENTA}📚 AutoClean EEG2Source Examples Gallery{self.colors.RESET}",
                f"{self.colors.CYAN}{'=' * 70}{self.colors.RESET}",
                ""
            ])
        else:
            gallery_text.extend([
                "=" * 70,
                "AutoClean EEG2Source Examples Gallery", 
                "=" * 70,
                ""
            ])
        
        for category_name, examples in self.examples.items():
            # Category header
            if self.colors:
                gallery_text.extend([
                    f"{self.colors.YELLOW}🎯 {category_name.upper().replace('_', ' ')} EXAMPLES{self.colors.RESET}",
                    f"{self.colors.CYAN}{'-' * 50}{self.colors.RESET}",
                    ""
                ])
            else:
                gallery_text.extend([
                    f"{category_name.upper().replace('_', ' ')} EXAMPLES",
                    "-" * 50,
                    ""
                ])
            
            # Examples in category
            for i, example in enumerate(examples, 1):
                if self.colors:
                    gallery_text.extend([
                        f"{self.colors.GREEN}{i}. {example['title']}{self.colors.RESET}",
                        f"   {self.colors.WHITE}{example['description']}{self.colors.RESET}",
                        "",
                        f"   {self.colors.CYAN}Command:{self.colors.RESET}",
                        f"   {self.colors.YELLOW}{example['command']}{self.colors.RESET}",
                        "",
                        f"   {self.colors.BLUE}Explanation:{self.colors.RESET}",
                        f"   {self._wrap_text(example['explanation'], 67, '   ')}",
                        ""
                    ])
                else:
                    gallery_text.extend([
                        f"{i}. {example['title']}",
                        f"   {example['description']}",
                        "",
                        f"   Command:",
                        f"   {example['command']}",
                        "",
                        f"   Explanation:",
                        f"   {self._wrap_text(example['explanation'], 67, '   ')}",
                        ""
                    ])
            
            gallery_text.append("")
        
        return "\n".join(gallery_text)
    
    def show_interactive_builder(self) -> str:
        """
        Interactive command builder interface.
        
        Returns
        -------
        str
            Command builder interface
        """
        if self.ascii_gen:
            header = self.ascii_gen.generate_header()
        else:
            header = "=== AutoClean EEG2Source Command Builder ==="
        
        # Processing mode options
        processing_options = [
            ("1", "🚀", "Sequential Processing - Memory efficient, single-file processing"),
            ("2", "⚡", "Parallel Processing - High-speed batch processing"),
            ("3", "🛡️", "Robust Processing - Maximum error recovery"),
            ("4", "🎮", "GPU Accelerated - CUDA-powered processing"),
            ("5", "💾", "Cached Processing - Optimized for similar files")
        ]
        
        if self.ascii_gen:
            menu = self.ascii_gen.generate_menu_box("PROCESSING MODE SELECTION", processing_options)
        else:
            menu_lines = ["=== PROCESSING MODE SELECTION ===", "Choose your processing strategy:", ""]
            for key, emoji, description in processing_options:
                menu_lines.append(f"[{key}] {emoji} {description}")
            menu_lines.extend(["", f"Enter selection [1-5]: _"])
            menu = "\n".join(menu_lines)
        
        instructions = []
        if self.colors:
            instructions.extend([
                "",
                f"{self.colors.CYAN}🧙‍♂️ Interactive Command Builder{self.colors.RESET}",
                f"{self.colors.WHITE}This wizard will help you build the perfect command for your needs.{self.colors.RESET}",
                "",
                f"{self.colors.YELLOW}Step 1:{self.colors.RESET} Choose your processing strategy from the menu above",
                f"{self.colors.YELLOW}Step 2:{self.colors.RESET} Specify your input file or directory",
                f"{self.colors.YELLOW}Step 3:{self.colors.RESET} Configure output and advanced options",
                "",
                f"{self.colors.GREEN}💡 Tip:{self.colors.RESET} Use {self.colors.CYAN}--examples{self.colors.RESET} to see ready-made commands for common scenarios!",
                ""
            ])
        else:
            instructions.extend([
                "",
                "Interactive Command Builder",
                "This wizard will help you build the perfect command for your needs.",
                "",
                "Step 1: Choose your processing strategy from the menu above",
                "Step 2: Specify your input file or directory", 
                "Step 3: Configure output and advanced options",
                "",
                "Tip: Use --examples to see ready-made commands for common scenarios!",
                ""
            ])
        
        return "\n".join([header, "", menu] + instructions)
    
    def _load_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """Load categorized examples."""
        return {
            'basic': [
                {
                    'title': '🎯 Process Single File',
                    'description': 'Basic EEG to source localization',
                    'command': 'autoclean-eeg2source process data.set --output-dir results',
                    'explanation': 'Processes a single .set file with default settings (sequential processing, standard_1020 montage, 250Hz resampling). Creates source localization data in the results directory.'
                },
                {
                    'title': '🔍 Validate File Before Processing',
                    'description': 'Check file compatibility and quality',
                    'command': 'autoclean-eeg2source validate data.set --montage standard_1020',
                    'explanation': 'Validates file format, checks montage compatibility, and assesses data quality without processing. Useful for troubleshooting before running full analysis.'
                },
                {
                    'title': '📊 Display File Information',
                    'description': 'Get detailed file metadata',
                    'command': 'autoclean-eeg2source info data.set',
                    'explanation': 'Shows comprehensive information about the EEG file including channels, epochs, sampling rate, and data quality metrics.'
                }
            ],
            'batch': [
                {
                    'title': '📁 Process Directory (Sequential)',
                    'description': 'Process all .set files in directory',
                    'command': 'autoclean-eeg2source process ./eeg_data --output-dir ./results',
                    'explanation': 'Finds all .set files in the eeg_data directory and processes them sequentially. Safe for systems with limited memory or when maximum reliability is needed.'
                },
                {
                    'title': '🔄 Recursive Directory Processing',
                    'description': 'Process files in subdirectories too',
                    'command': 'autoclean-eeg2source process ./study_data --recursive --output-dir ./results',
                    'explanation': 'Searches through subdirectories recursively for .set files. Perfect for processing entire study datasets with organized folder structures.'
                },
                {
                    'title': '⚡ Parallel Batch Processing',
                    'description': 'High-speed parallel processing',
                    'command': 'autoclean-eeg2source process ./data --parallel --batch-processing --n-jobs 8',
                    'explanation': 'Processes multiple files simultaneously using 8 CPU cores. Significantly faster for large datasets but requires sufficient memory (8GB+ recommended).'
                },
                {
                    'title': '🔍 Batch Validation',
                    'description': 'Validate multiple files quickly',
                    'command': 'autoclean-eeg2source validate ./data --recursive --save-validation',
                    'explanation': 'Validates all .set files in directory tree and saves detailed validation report. Useful for quality control before processing large datasets.'
                }
            ],
            'advanced': [
                {
                    'title': '🚀 Maximum Performance Setup',
                    'description': 'GPU + caching + parallel processing',
                    'command': 'autoclean-eeg2source process ./data --parallel --batch-processing --n-jobs 8 --gpu --enable-cache',
                    'explanation': 'Ultimate performance configuration combining GPU acceleration, result caching, and parallel processing. Requires CUDA-compatible GPU and 16GB+ RAM for optimal performance.'
                },
                {
                    'title': '🛡️ Robust Processing with Error Recovery',
                    'description': 'Maximum reliability for problematic files',
                    'command': 'autoclean-eeg2source process ./data --robust --error-dir ./error_reports',
                    'explanation': 'Uses robust processor with comprehensive error recovery strategies. Automatically attempts to fix common issues and generates detailed error reports for files that cannot be processed.'
                },
                {
                    'title': '🎛️ Custom Processing Parameters',
                    'description': 'Fine-tune processing settings',
                    'command': 'autoclean-eeg2source process data.set --montage biosemi64 --resample-freq 500 --lambda2 0.05',
                    'explanation': 'Custom configuration with BioSemi 64-channel montage, 500Hz sampling rate, and modified regularization parameter (lambda2=0.05) for higher spatial resolution.'
                },
                {
                    'title': '🔧 Memory-Optimized Processing',
                    'description': 'Process large files with limited RAM',
                    'command': 'autoclean-eeg2source process data.set --robust --memory-limit 2GB --resample-freq 125',
                    'explanation': 'Memory-efficient processing with 2GB limit and reduced sampling rate. Ideal for processing high-density recordings on systems with limited RAM.'
                }
            ],
            'troubleshooting': [
                {
                    'title': '🔧 Fix HEOG/VEOG Channel Errors',
                    'description': 'Resolve montage compatibility issues',
                    'command': 'autoclean-eeg2source process data.set --montage standard_1020',
                    'explanation': 'Version 0.3.2+ automatically handles HEOG/VEOG channels by setting their type to EOG before montage application. Use standard montages for best compatibility.'
                },
                {
                    'title': '📊 Handle High-Density Recordings',
                    'description': 'Process 128+ channel systems',
                    'command': 'autoclean-eeg2source process data.set --montage GSN-HydroCel-128 --robust',
                    'explanation': 'For high-density EEG systems like EGI HydroCel. Robust processing helps handle the increased complexity and potential channel naming variations.'
                },
                {
                    'title': '💾 Recover from Processing Errors',
                    'description': 'Resume failed batch processing',
                    'command': 'autoclean-eeg2source recover ./failed_batch --output-dir ./results',
                    'explanation': 'Attempts to recover and reprocess files that failed in previous batch runs. Uses conservative settings and detailed error reporting.'
                },
                {
                    'title': '🔍 Debug Processing Issues',
                    'description': 'Verbose output for troubleshooting',
                    'command': 'autoclean-eeg2source process data.set --log-level DEBUG --log-file debug.log',
                    'explanation': 'Enables detailed logging to help diagnose processing issues. Creates a debug.log file with comprehensive information about each processing step.'
                }
            ]
        }
    
    def _load_detailed_help(self) -> Dict[str, Dict[str, str]]:
        """Load detailed help content."""
        return {
            'overview': {
                'Purpose': 'AutoClean EEG2Source performs source localization using Desikan-Killiany atlas regions',
                'Input': 'EEGLAB .set files (epoched or continuous EEG data)',
                'Output': 'Source-localized EEG data in EEGLAB format with 68 Desikan-Killiany regions',
                'Method': 'Minimum norm estimation (MNE) with FreeSurfer fsaverage brain model',
                'Requirements': 'Python 3.9+, MNE-Python, EEGLAB files with standard channel names'
            },
            'processing_modes': {
                'Sequential': 'Single-threaded processing, memory efficient, most reliable',
                'Parallel': 'Multi-threaded batch processing, faster but memory intensive',
                'Robust': 'Enhanced error recovery, automatic problem fixing, detailed reporting',
                'GPU': 'CUDA acceleration for compatible systems, fastest for large datasets',
                'Cached': 'Optimized for repeated processing of similar files'
            },
            'supported_montages': {
                'standard_1020': '10-20 system with 19-21 channels',
                'standard_1005': '10-05 system with extended coverage',
                'GSN-HydroCel-32': 'EGI HydroCel 32-channel system',
                'GSN-HydroCel-64': 'EGI HydroCel 64-channel system',
                'GSN-HydroCel-128': 'EGI HydroCel 128-channel system',
                'GSN-HydroCel-256': 'EGI HydroCel 256-channel system',
                'biosemi64': 'BioSemi 64-channel system',
                'biosemi128': 'BioSemi 128-channel system'
            },
            'common_parameters': {
                '--output-dir': 'Specify output directory for results',
                '--montage': 'Set EEG montage/channel layout (default: standard_1020)',
                '--resample-freq': 'Target sampling frequency in Hz (default: 250)',
                '--lambda2': 'Regularization parameter for inverse solution (default: 1/9)',
                '--n-jobs': 'Number of parallel jobs for batch processing',
                '--recursive': 'Search subdirectories for .set files',
                '--log-level': 'Set logging verbosity (DEBUG, INFO, WARNING, ERROR)',
                '--memory-limit': 'Set memory usage limit (e.g., 4GB)'
            },
            'troubleshooting': {
                'Channel Errors': 'Update to v0.3.2+ for automatic HEOG/VEOG handling',
                'Memory Issues': 'Use --robust mode or reduce --n-jobs for parallel processing',
                'Montage Problems': 'Verify channel names match selected montage, try standard_1020',
                'File Format': 'Ensure .set files are valid EEGLAB format with accompanying .fdt if needed',
                'Performance': 'Use --gpu for CUDA systems, --enable-cache for repeated processing'
            }
        }
    
    def _wrap_text(self, text: str, width: int, indent: str = "") -> str:
        """Wrap text to specified width with optional indentation."""
        wrapper = textwrap.TextWrapper(
            width=width,
            initial_indent=indent,
            subsequent_indent=indent,
            break_long_words=False,
            break_on_hyphens=False
        )
        return wrapper.fill(text)