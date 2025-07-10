"""
ASCII art generator for retro-style CLI elements.

This module provides functions to generate ASCII art headers, progress bars,
status boxes, and other visual elements with 80s retro styling.
"""

import shutil
import math
from typing import Dict, List, Optional, Tuple


class ASCIIArtGenerator:
    """Generate retro-style ASCII art elements."""
    
    def __init__(self, colors=None):
        """
        Initialize ASCII art generator.
        
        Parameters
        ----------
        colors : RetroColors, optional
            Color system instance for styling
        """
        self.colors = colors
        self.terminal_width = shutil.get_terminal_size().columns
        self.min_width = 80  # Minimum width for proper display
        
    def generate_header(self):
        """Generate main application header with ASCII art."""
        width = max(self.terminal_width, self.min_width)
        
        # Main ASCII art title
        title_art = [
            "┌─┐┬ ┬┌┬┐┌─┐┌─┐┬  ┌─┐┌─┐┌┐┌  ┌─┐┌─┐┌─┐ ┌─ ┌─┐┌─┐┬ ┬┬─┐┌─┐┌─┐",
            "├─┤│ │ │ │ │├─┤│  ├┤ ├─┤│││  ├┤ ├┤ │ ┬ └─┐ └─┐│ ││ │├┬┘│  ├┤ ",
            "┴ ┴└─┘ ┴ └─┘┴ ┴┴─┘└─┘┴ ┴┘└┘  └─┘└─┘└─┘ └─┘ └─┘└─┘└─┘┴└─└─┘└─┘"
        ]
        
        # Create bordered header
        border_char = "═"
        corner_tl = "╔"
        corner_tr = "╗"
        corner_bl = "╚"
        corner_br = "╝"
        vertical = "║"
        
        # Calculate padding for centering
        max_title_width = max(len(line) for line in title_art)
        content_width = max(max_title_width + 4, 70)
        
        if self.colors:
            header_lines = [
                f"{self.colors.CYAN}{corner_tl}{border_char * (content_width - 2)}{corner_tr}{self.colors.RESET}"
            ]
            
            # Add title lines
            for line in title_art:
                padding = (content_width - len(line) - 2) // 2
                header_lines.append(
                    f"{self.colors.CYAN}{vertical}{self.colors.MAGENTA}{' ' * padding}{line}{' ' * (content_width - len(line) - padding - 2)}{self.colors.CYAN}{vertical}{self.colors.RESET}"
                )
            
            # Add subtitle
            subtitle = "🧠 EEG Source Localization with Desikan-Killiany Atlas Regions"
            padding = (content_width - len(subtitle) - 2) // 2
            header_lines.extend([
                f"{self.colors.CYAN}{vertical}{' ' * (content_width - 2)}{vertical}{self.colors.RESET}",
                f"{self.colors.CYAN}{vertical}{self.colors.WHITE}{' ' * padding}{subtitle}{' ' * (content_width - len(subtitle) - padding - 2)}{self.colors.CYAN}{vertical}{self.colors.RESET}",
                f"{self.colors.CYAN}{corner_bl}{border_char * (content_width - 2)}{corner_br}{self.colors.RESET}"
            ])
        else:
            # Fallback without colors
            header_lines = [
                f"{corner_tl}{border_char * (content_width - 2)}{corner_tr}"
            ]
            
            for line in title_art:
                padding = (content_width - len(line) - 2) // 2
                header_lines.append(
                    f"{vertical}{' ' * padding}{line}{' ' * (content_width - len(line) - padding - 2)}{vertical}"
                )
            
            subtitle = "EEG Source Localization with Desikan-Killiany Atlas Regions"
            padding = (content_width - len(subtitle) - 2) // 2
            header_lines.extend([
                f"{vertical}{' ' * (content_width - 2)}{vertical}",
                f"{vertical}{' ' * padding}{subtitle}{' ' * (content_width - len(subtitle) - padding - 2)}{vertical}",
                f"{corner_bl}{border_char * (content_width - 2)}{corner_br}"
            ])
        
        return "\n".join(header_lines)
    
    def generate_progress_bar(self, current: int, total: int, description: str = "", width: int = 50):
        """
        Generate animated progress bar with retro styling.
        
        Parameters
        ----------
        current : int
            Current progress value
        total : int
            Total value
        description : str, optional
            Description text to display
        width : int, optional
            Width of progress bar in characters
        
        Returns
        -------
        str
            Formatted progress bar string
        """
        if total == 0:
            percentage = 0
        else:
            percentage = min(100, (current / total) * 100)
        
        filled_width = int((percentage / 100) * width)
        empty_width = width - filled_width
        
        # Use different characters for retro feel
        filled_char = "█"
        empty_char = "░"
        
        if self.colors:
            progress_bar = (
                f"{self.colors.CYAN}[{self.colors.GREEN}{filled_char * filled_width}"
                f"{self.colors.DIM}{empty_char * empty_width}{self.colors.CYAN}] "
                f"{self.colors.YELLOW}{percentage:6.1f}%{self.colors.RESET}"
            )
            
            if description:
                progress_bar += f" {self.colors.CYAN}│{self.colors.RESET} {self.colors.WHITE}{description}{self.colors.RESET}"
        else:
            progress_bar = f"[{filled_char * filled_width}{empty_char * empty_width}] {percentage:6.1f}%"
            if description:
                progress_bar += f" | {description}"
        
        return progress_bar
    
    def generate_status_box(self, title: str, content: Dict[str, str], width: Optional[int] = None):
        """
        Generate bordered information box.
        
        Parameters
        ----------
        title : str
            Box title
        content : dict
            Dictionary of key-value pairs to display
        width : int, optional
            Box width (auto-calculated if not provided)
        
        Returns
        -------
        str
            Formatted status box
        """
        if width is None:
            # Calculate width based on content
            max_content_width = max(
                len(f"{key}: {value}") for key, value in content.items()
            )
            width = max(len(title) + 6, max_content_width + 4, 60)
        
        # Box drawing characters
        horizontal = "─"
        vertical = "│"
        top_left = "┌"
        top_right = "┐"
        bottom_left = "└"
        bottom_right = "┘"
        title_left = "─ "
        title_right = " "
        
        lines = []
        
        # Calculate title positioning
        title_text = f"{title_left}{title.upper()}{title_right}"
        title_padding = width - len(title_text) - 2
        
        if self.colors:
            # Top border with title
            lines.append(
                f"{self.colors.CYAN}{top_left}{title_text}{horizontal * title_padding}{top_right}{self.colors.RESET}"
            )
            
            # Content lines
            for key, value in content.items():
                content_line = f"{key}: {value}"
                padding = width - len(content_line) - 2
                lines.append(
                    f"{self.colors.CYAN}{vertical}{self.colors.RESET} {self.colors.WHITE}{content_line}{self.colors.RESET}{' ' * padding}{self.colors.CYAN}{vertical}{self.colors.RESET}"
                )
            
            # Bottom border
            lines.append(
                f"{self.colors.CYAN}{bottom_left}{horizontal * (width - 2)}{bottom_right}{self.colors.RESET}"
            )
        else:
            # Top border with title
            lines.append(f"{top_left}{title_text}{horizontal * title_padding}{top_right}")
            
            # Content lines
            for key, value in content.items():
                content_line = f"{key}: {value}"
                padding = width - len(content_line) - 2
                lines.append(f"{vertical} {content_line}{' ' * padding}{vertical}")
            
            # Bottom border
            lines.append(f"{bottom_left}{horizontal * (width - 2)}{bottom_right}")
        
        return "\n".join(lines)
    
    def generate_two_column_box(self, title: str, left_content: Dict[str, str], right_content: Dict[str, str]):
        """
        Generate a two-column status box.
        
        Parameters
        ----------
        title : str
            Box title
        left_content : dict
            Left column content
        right_content : dict
            Right column content
        
        Returns
        -------
        str
            Formatted two-column box
        """
        # Calculate column widths
        left_width = max(len(f"{k}: {v}") for k, v in left_content.items()) + 2
        right_width = max(len(f"{k}: {v}") for k, v in right_content.items()) + 2
        total_width = left_width + right_width + 5  # 5 for borders and separator
        
        # Ensure all content arrays are the same length
        max_rows = max(len(left_content), len(right_content))
        left_items = list(left_content.items()) + [("", "")] * (max_rows - len(left_content))
        right_items = list(right_content.items()) + [("", "")] * (max_rows - len(right_content))
        
        lines = []
        
        # Box drawing characters
        horizontal = "─"
        vertical = "│"
        top_left = "┌"
        top_right = "┐"
        bottom_left = "└"
        bottom_right = "┘"
        
        # Title
        title_text = f"─ {title.upper()} "
        title_padding = total_width - len(title_text) - 2
        
        if self.colors:
            lines.append(
                f"{self.colors.CYAN}{top_left}{title_text}{horizontal * title_padding}{top_right}{self.colors.RESET}"
            )
            
            # Content rows
            for (l_key, l_val), (r_key, r_val) in zip(left_items, right_items):
                left_text = f"{l_key}: {l_val}" if l_key else ""
                right_text = f"{r_key}: {r_val}" if r_key else ""
                
                left_padded = left_text.ljust(left_width)
                right_padded = right_text.ljust(right_width)
                
                lines.append(
                    f"{self.colors.CYAN}{vertical}{self.colors.RESET} {self.colors.WHITE}{left_padded}{self.colors.CYAN}{vertical}{self.colors.RESET} {self.colors.WHITE}{right_padded}{self.colors.CYAN}{vertical}{self.colors.RESET}"
                )
            
            lines.append(
                f"{self.colors.CYAN}{bottom_left}{horizontal * (total_width - 2)}{bottom_right}{self.colors.RESET}"
            )
        else:
            lines.append(f"{top_left}{title_text}{horizontal * title_padding}{top_right}")
            
            for (l_key, l_val), (r_key, r_val) in zip(left_items, right_items):
                left_text = f"{l_key}: {l_val}" if l_key else ""
                right_text = f"{r_key}: {r_val}" if r_key else ""
                
                left_padded = left_text.ljust(left_width)
                right_padded = right_text.ljust(right_width)
                
                lines.append(f"{vertical} {left_padded}{vertical} {right_padded}{vertical}")
            
            lines.append(f"{bottom_left}{horizontal * (total_width - 2)}{bottom_right}")
        
        return "\n".join(lines)
    
    def generate_separator(self, style: str = 'double', width: Optional[int] = None):
        """
        Generate decorative separators.
        
        Parameters
        ----------
        style : str
            Style of separator ('single', 'double', 'thick', 'dotted')
        width : int, optional
            Width of separator (uses terminal width if not provided)
        
        Returns
        -------
        str
            Separator line
        """
        if width is None:
            width = min(self.terminal_width, 100)
        
        separators = {
            'single': '─',
            'double': '═',
            'thick': '━',
            'dotted': '┈',
            'dashed': '┄'
        }
        
        char = separators.get(style, '─')
        
        if self.colors:
            return f"{self.colors.CYAN}{char * width}{self.colors.RESET}"
        else:
            return char * width
    
    def generate_menu_box(self, title: str, options: List[Tuple[str, str, str]]):
        """
        Generate a menu selection box.
        
        Parameters
        ----------
        title : str
            Menu title
        options : list
            List of (key, emoji, description) tuples
        
        Returns
        -------
        str
            Formatted menu box
        """
        # Calculate width based on longest option
        max_width = max(len(f"[{key}] {emoji} {desc}") for key, emoji, desc in options)
        width = max(len(title) + 6, max_width + 4, 60)
        
        lines = []
        
        # Box drawing characters
        horizontal = "─"
        vertical = "│"
        top_left = "┌"
        top_right = "┐"
        bottom_left = "└"
        bottom_right = "┘"
        
        # Title
        title_text = f"─ {title.upper()} "
        title_padding = width - len(title_text) - 2
        
        if self.colors:
            lines.append(
                f"{self.colors.CYAN}{top_left}{title_text}{horizontal * title_padding}{top_right}{self.colors.RESET}"
            )
            
            # Add description if this is a selection menu
            if title.endswith("SELECTION"):
                desc_text = "Choose your processing strategy:"
                desc_padding = width - len(desc_text) - 2
                lines.extend([
                    f"{self.colors.CYAN}{vertical}{self.colors.RESET} {self.colors.WHITE}{desc_text}{' ' * desc_padding}{self.colors.CYAN}{vertical}{self.colors.RESET}",
                    f"{self.colors.CYAN}{vertical}{' ' * (width - 2)}{vertical}{self.colors.RESET}"
                ])
            
            # Options
            for key, emoji, description in options:
                option_text = f"[{key}] {emoji} {description}"
                padding = width - len(option_text) - 2
                lines.append(
                    f"{self.colors.CYAN}{vertical}{self.colors.RESET} {self.colors.YELLOW}[{self.colors.MAGENTA}{key}{self.colors.YELLOW}]{self.colors.RESET} {emoji} {self.colors.WHITE}{description}{' ' * padding}{self.colors.CYAN}{vertical}{self.colors.RESET}"
                )
            
            # Input prompt
            lines.extend([
                f"{self.colors.CYAN}{vertical}{' ' * (width - 2)}{vertical}{self.colors.RESET}",
                f"{self.colors.CYAN}{vertical}{self.colors.RESET} {self.colors.GREEN}Enter selection [{'-'.join(opt[0] for opt in options)}]: {self.colors.YELLOW}_{' ' * (width - len('Enter selection [' + '-'.join(opt[0] for opt in options) + ']: _') - 2)}{self.colors.CYAN}{vertical}{self.colors.RESET}",
                f"{self.colors.CYAN}{bottom_left}{horizontal * (width - 2)}{bottom_right}{self.colors.RESET}"
            ])
        else:
            lines.append(f"{top_left}{title_text}{horizontal * title_padding}{top_right}")
            
            if title.endswith("SELECTION"):
                desc_text = "Choose your processing strategy:"
                desc_padding = width - len(desc_text) - 2
                lines.extend([
                    f"{vertical} {desc_text}{' ' * desc_padding}{vertical}",
                    f"{vertical}{' ' * (width - 2)}{vertical}"
                ])
            
            for key, emoji, description in options:
                option_text = f"[{key}] {emoji} {description}"
                padding = width - len(option_text) - 2
                lines.append(f"{vertical} {option_text}{' ' * padding}{vertical}")
            
            lines.extend([
                f"{vertical}{' ' * (width - 2)}{vertical}",
                f"{vertical} Enter selection [{'-'.join(opt[0] for opt in options)}]: _{' ' * (width - len('Enter selection [' + '-'.join(opt[0] for opt in options) + ']: _') - 2)}{vertical}",
                f"{bottom_left}{horizontal * (width - 2)}{bottom_right}"
            ])
        
        return "\n".join(lines)