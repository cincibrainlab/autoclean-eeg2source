"""CLI enhancement modules for AutoClean EEG2Source."""

from .visual import RetroColors

# Import other modules only when they exist
try:
    from .ascii_art import ASCIIArtGenerator
except ImportError:
    ASCIIArtGenerator = None

try:
    from .system_info import SystemInfoDisplay
except ImportError:
    SystemInfoDisplay = None

try:
    from .help_system import EnhancedHelpSystem
except ImportError:
    EnhancedHelpSystem = None

__all__ = [
    'RetroColors',
    'ASCIIArtGenerator', 
    'SystemInfoDisplay',
    'EnhancedHelpSystem'
]