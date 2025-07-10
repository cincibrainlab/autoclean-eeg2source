"""
80s-inspired color system with cross-platform support.

This module provides a retro color scheme with graceful degradation
for terminals that don't support colors.
"""

import sys
import os


class RetroColors:
    """80s-inspired color system with fallback support."""
    
    def __init__(self, force_colors=None):
        """
        Initialize color system.
        
        Parameters
        ----------
        force_colors : bool, optional
            Force enable/disable colors regardless of terminal support
        """
        self.colorama_available = self._init_colorama()
        self.colors_enabled = self._should_use_colors(force_colors)
        self.performance_mode = False
        
    def _init_colorama(self):
        """Initialize colorama if available."""
        try:
            import colorama
            colorama.init(autoreset=True)
            return True
        except ImportError:
            return False
    
    def _should_use_colors(self, force_colors):
        """Determine if colors should be used."""
        if force_colors is not None:
            return force_colors
            
        # Check if running in a terminal that supports colors
        if not sys.stdout.isatty():
            return False
            
        # Check environment variables
        if os.environ.get('NO_COLOR'):
            return False
            
        if os.environ.get('FORCE_COLOR'):
            return True
            
        # Check for common terminals that support colors
        term = os.environ.get('TERM', '').lower()
        if any(t in term for t in ['color', 'xterm', 'screen', 'tmux']):
            return True
            
        return self.colorama_available
    
    def enable_performance_mode(self):
        """Disable colors during processing for performance."""
        self.performance_mode = True
    
    def disable_performance_mode(self):
        """Re-enable colors after processing."""
        self.performance_mode = False
    
    def _color(self, code):
        """Return color code if colors are enabled."""
        if self.colors_enabled and not self.performance_mode:
            return code
        return ''
    
    # Primary 80s colors
    @property
    def CYAN(self):
        """Bright cyan - headers, success messages, highlights."""
        return self._color('\033[96m')
    
    @property
    def MAGENTA(self):
        """Bright magenta - version info, important warnings."""
        return self._color('\033[95m')
    
    @property
    def YELLOW(self):
        """Bright yellow - file paths, progress indicators."""
        return self._color('\033[93m')
    
    @property
    def GREEN(self):
        """Bright green - success states, system info."""
        return self._color('\033[92m')
    
    @property
    def RED(self):
        """Bright red - error messages, critical warnings."""
        return self._color('\033[91m')
    
    @property
    def BLUE(self):
        """Bright blue - links, secondary information."""
        return self._color('\033[94m')
    
    @property
    def WHITE(self):
        """Bright white - primary text content."""
        return self._color('\033[97m')
    
    @property
    def RESET(self):
        """Reset to default color."""
        return self._color('\033[0m')
    
    # Text styles
    @property
    def BOLD(self):
        """Bold text."""
        return self._color('\033[1m')
    
    @property
    def DIM(self):
        """Dim text."""
        return self._color('\033[2m')
    
    @property
    def UNDERLINE(self):
        """Underlined text."""
        return self._color('\033[4m')
    
    @property
    def BLINK(self):
        """Blinking text (use sparingly)."""
        return self._color('\033[5m')
    
    # Background colors (for special effects)
    @property
    def BG_BLACK(self):
        """Black background."""
        return self._color('\033[40m')
    
    @property
    def BG_CYAN(self):
        """Cyan background."""
        return self._color('\033[46m')
    
    @property
    def BG_MAGENTA(self):
        """Magenta background."""
        return self._color('\033[45m')
    
    # Convenience methods
    def success(self, text):
        """Format text as success message."""
        return f"{self.GREEN}{text}{self.RESET}"
    
    def error(self, text):
        """Format text as error message."""
        return f"{self.RED}{text}{self.RESET}"
    
    def warning(self, text):
        """Format text as warning message."""
        return f"{self.YELLOW}{text}{self.RESET}"
    
    def info(self, text):
        """Format text as info message."""
        return f"{self.CYAN}{text}{self.RESET}"
    
    def highlight(self, text):
        """Format text as highlighted."""
        return f"{self.MAGENTA}{self.BOLD}{text}{self.RESET}"
    
    def link(self, text):
        """Format text as a link."""
        return f"{self.BLUE}{self.UNDERLINE}{text}{self.RESET}"
    
    def header(self, text):
        """Format text as a header."""
        return f"{self.CYAN}{self.BOLD}{text}{self.RESET}"
    
    def filename(self, text):
        """Format text as a filename."""
        return f"{self.YELLOW}{text}{self.RESET}"


# Global instance for easy access
colors = RetroColors()