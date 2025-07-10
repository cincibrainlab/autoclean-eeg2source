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

__all__ = [
    'RetroColors',
    'ASCIIArtGenerator',
    'SystemInfoDisplay',
    'EnhancedHelpSystem',
    'CommandWizard',
    'VisualProgressTracker',
    'EnhancedCLI',
    'create_enhanced_cli'
]