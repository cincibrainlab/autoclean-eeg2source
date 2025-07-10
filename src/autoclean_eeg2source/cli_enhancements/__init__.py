"""
CLI enhancement package for AutoClean EEG2Source.

Provides 80s retro-styled visual enhancements including:
- Color system with graceful fallbacks
- ASCII art headers and progress bars
- System information display
- Enhanced help system with examples
- Interactive command wizard
- Visual progress tracking with animations
"""

from .visual import RetroColors

try:
    from .ascii_art import ASCIIArtGenerator
    from .system_info import SystemInfoDisplay
    from .help_system import EnhancedHelpSystem
    from .wizard import CommandWizard
    from .progress import VisualProgressTracker
    from .enhanced_cli import EnhancedCLI, create_enhanced_cli
except ImportError:
    # Graceful fallback if dependencies are missing
    ASCIIArtGenerator = None
    SystemInfoDisplay = None
    EnhancedHelpSystem = None
    CommandWizard = None
    VisualProgressTracker = None
    EnhancedCLI = None
    create_enhanced_cli = None

# Import main function from the CLI module
def main():
    """Entry point for the CLI."""
    import sys
    import os
    
    # Add src directory to path so that autoclean_eeg2source can be imported
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Import the CLI module properly
    try:
        # Import the actual CLI module which contains the main function
        import autoclean_eeg2source.cli as cli_module
        # Access the main function directly from the module
        main_func = getattr(cli_module, 'main')
        return main_func()
    except ImportError as e:
        print(f"Error importing CLI module: {e}")
        print("AutoClean EEG2Source CLI")
        print("Enhanced CLI not available. Please check installation.")
        return 1

__all__ = [
    'RetroColors',
    'ASCIIArtGenerator',
    'SystemInfoDisplay',
    'EnhancedHelpSystem',
    'CommandWizard',
    'VisualProgressTracker',
    'EnhancedCLI',
    'create_enhanced_cli',
    'main'
]