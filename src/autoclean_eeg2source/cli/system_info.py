"""
System information display with retro visual styling.

This module provides real-time system metrics display including CPU usage,
memory statistics, disk space, and project information.
"""

import time
import platform
import sys
import os
from typing import Dict, Any, Optional
from .. import __version__

# Try to import psutil, fall back gracefully if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemMonitor:
    """Efficient system information collection with caching."""
    
    def __init__(self, cache_duration: float = 5.0):
        """
        Initialize system monitor.
        
        Parameters
        ----------
        cache_duration : float
            How long to cache system info in seconds
        """
        self.cache_duration = cache_duration
        self._last_update = 0
        self._cached_info = {}
        self.psutil_available = PSUTIL_AVAILABLE
        
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get cached or fresh system information.
        
        Returns
        -------
        dict
            System information dictionary
        """
        current_time = time.time()
        if current_time - self._last_update > self.cache_duration:
            self._cached_info = self._collect_system_info()
            self._last_update = current_time
        return self._cached_info.copy()
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        info = {
            'platform': platform.platform(),
            'python_version': sys.version.split()[0],
            'cpu_count': None,
            'cpu_usage': None,
            'memory': None,
            'disk': None,
            'uptime': None
        }
        
        if self.psutil_available:
            try:
                # CPU information
                info['cpu_count'] = psutil.cpu_count(logical=True)
                info['cpu_usage'] = psutil.cpu_percent(interval=0.1)
                
                # Memory information
                memory = psutil.virtual_memory()
                info['memory'] = {
                    'total': memory.total,
                    'used': memory.used,
                    'available': memory.available,
                    'percent': memory.percent
                }
                
                # Disk information (for current working directory)
                disk = psutil.disk_usage(os.getcwd())
                info['disk'] = {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
                
                # System uptime
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                info['uptime'] = uptime_seconds
                
            except Exception:
                # If psutil fails, fall back to basic info
                pass
        
        return info
    
    def format_bytes(self, bytes_value: Optional[int]) -> str:
        """
        Format bytes in human-readable format.
        
        Parameters
        ----------
        bytes_value : int or None
            Bytes to format
            
        Returns
        -------
        str
            Formatted string (e.g., "1.2GB")
        """
        if bytes_value is None:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"
    
    def format_duration(self, seconds: Optional[float]) -> str:
        """
        Format duration in human-readable format.
        
        Parameters
        ----------
        seconds : float or None
            Duration in seconds
            
        Returns
        -------
        str
            Formatted duration string
        """
        if seconds is None:
            return "N/A"
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


class SystemInfoDisplay:
    """System information display with retro visual styling."""
    
    def __init__(self, colors=None, ascii_gen=None):
        """
        Initialize system info display.
        
        Parameters
        ----------
        colors : RetroColors, optional
            Color system instance
        ascii_gen : ASCIIArtGenerator, optional
            ASCII art generator instance
        """
        self.colors = colors
        self.ascii_gen = ascii_gen
        self.monitor = SystemMonitor()
        
    def display_system_header(self) -> str:
        """
        Display comprehensive system information header.
        
        Returns
        -------
        str
            Formatted system header
        """
        info = self.monitor.get_system_info()
        
        # Prepare left column content
        left_content = {
            "🧠 AutoClean EEG2Source": f"v{__version__}",
            "💻 CPU": self._format_cpu_info(info),
            "💾 Disk": self._format_disk_info(info)
        }
        
        # Prepare right column content
        right_content = {
            "📂 GitHub": "cincibrainlab/autoclean-eeg2source",
            "🧮 Memory": self._format_memory_info(info),
            "🔗 PyPI": "pypi.org/project/autoclean-eeg2source"
        }
        
        if self.ascii_gen:
            return self.ascii_gen.generate_two_column_box("SYSTEM STATUS", left_content, right_content)
        else:
            # Fallback formatting
            lines = ["=== SYSTEM STATUS ==="]
            for key, value in left_content.items():
                lines.append(f"{key}: {value}")
            for key, value in right_content.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
    
    def display_detailed_system_info(self) -> str:
        """
        Display detailed system information.
        
        Returns
        -------
        str
            Formatted detailed system info
        """
        info = self.monitor.get_system_info()
        
        content = {
            "Platform": info.get('platform', 'Unknown'),
            "Python Version": info.get('python_version', sys.version.split()[0]),
            "CPU Cores": str(info.get('cpu_count', 'N/A')),
            "CPU Usage": f"{info.get('cpu_usage', 0):.1f}%" if info.get('cpu_usage') is not None else "N/A",
            "Memory Total": self.monitor.format_bytes(info.get('memory', {}).get('total')),
            "Memory Used": self.monitor.format_bytes(info.get('memory', {}).get('used')),
            "Memory Available": self.monitor.format_bytes(info.get('memory', {}).get('available')),
            "Disk Total": self.monitor.format_bytes(info.get('disk', {}).get('total')),
            "Disk Free": self.monitor.format_bytes(info.get('disk', {}).get('free')),
            "System Uptime": self.monitor.format_duration(info.get('uptime')),
            "Working Directory": os.getcwd(),
            "AutoClean Version": __version__
        }
        
        if self.ascii_gen:
            return self.ascii_gen.generate_status_box("DETAILED SYSTEM INFORMATION", content)
        else:
            lines = ["=== DETAILED SYSTEM INFORMATION ==="]
            for key, value in content.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
    
    def display_performance_summary(self, start_time: float, end_time: float, 
                                  files_processed: int, errors: int = 0) -> str:
        """
        Display processing performance summary.
        
        Parameters
        ----------
        start_time : float
            Processing start time
        end_time : float
            Processing end time
        files_processed : int
            Number of files processed
        errors : int, optional
            Number of errors encountered
            
        Returns
        -------
        str
            Formatted performance summary
        """
        duration = end_time - start_time
        files_per_second = files_processed / duration if duration > 0 else 0
        success_rate = ((files_processed - errors) / files_processed * 100) if files_processed > 0 else 0
        
        # Get current system state
        info = self.monitor.get_system_info()
        
        content = {
            "⏱️ Total Time": self.monitor.format_duration(duration),
            "📁 Files Processed": str(files_processed),
            "❌ Errors": str(errors),
            "✅ Success Rate": f"{success_rate:.1f}%",
            "🚀 Processing Rate": f"{files_per_second:.2f} files/second",
            "💾 Final Memory Usage": self._format_memory_info(info),
            "💻 Final CPU Usage": self._format_cpu_info(info)
        }
        
        if self.ascii_gen:
            return self.ascii_gen.generate_status_box("PERFORMANCE SUMMARY", content)
        else:
            lines = ["=== PERFORMANCE SUMMARY ==="]
            for key, value in content.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
    
    def _format_cpu_info(self, info: Dict[str, Any]) -> str:
        """Format CPU information."""
        cpu_count = info.get('cpu_count')
        cpu_usage = info.get('cpu_usage')
        
        if cpu_count is None and cpu_usage is None:
            return "N/A"
        elif cpu_count is None:
            return f"{cpu_usage:.1f}% usage"
        elif cpu_usage is None:
            return f"{cpu_count} cores"
        else:
            return f"{cpu_count} cores ({cpu_usage:.1f}% usage)"
    
    def _format_memory_info(self, info: Dict[str, Any]) -> str:
        """Format memory information."""
        memory = info.get('memory')
        if not memory:
            return "N/A"
        
        used = self.monitor.format_bytes(memory.get('used'))
        total = self.monitor.format_bytes(memory.get('total'))
        percent = memory.get('percent', 0)
        
        return f"{used} / {total} ({percent:.1f}%)"
    
    def _format_disk_info(self, info: Dict[str, Any]) -> str:
        """Format disk information."""
        disk = info.get('disk')
        if not disk:
            return "N/A"
        
        free = self.monitor.format_bytes(disk.get('free'))
        total = self.monitor.format_bytes(disk.get('total'))
        
        return f"{free} / {total} available"
    
    def get_memory_status_color(self, info: Dict[str, Any]) -> str:
        """
        Get appropriate color for memory status.
        
        Parameters
        ----------
        info : dict
            System information
            
        Returns
        -------
        str
            Color string or empty if no colors
        """
        if not self.colors:
            return ""
        
        memory = info.get('memory')
        if not memory:
            return ""
        
        percent = memory.get('percent', 0)
        if percent < 50:
            return self.colors.GREEN
        elif percent < 80:
            return self.colors.YELLOW
        else:
            return self.colors.RED
    
    def get_cpu_status_color(self, info: Dict[str, Any]) -> str:
        """
        Get appropriate color for CPU status.
        
        Parameters
        ----------
        info : dict
            System information
            
        Returns
        -------
        str
            Color string or empty if no colors
        """
        if not self.colors:
            return ""
        
        cpu_usage = info.get('cpu_usage')
        if cpu_usage is None:
            return ""
        
        if cpu_usage < 30:
            return self.colors.GREEN
        elif cpu_usage < 70:
            return self.colors.YELLOW
        else:
            return self.colors.RED
    
    def display_startup_info(self) -> str:
        """
        Display startup information banner.
        
        Returns
        -------
        str
            Formatted startup banner
        """
        info = self.monitor.get_system_info()
        
        # Create a simple startup banner
        lines = []
        
        if self.colors:
            lines.extend([
                f"{self.colors.CYAN}{'=' * 60}{self.colors.RESET}",
                f"{self.colors.MAGENTA}🧠 AutoClean EEG2Source v{__version__}{self.colors.RESET}",
                f"{self.colors.WHITE}EEG Source Localization with Desikan-Killiany Atlas{self.colors.RESET}",
                f"{self.colors.CYAN}{'=' * 60}{self.colors.RESET}",
                "",
                f"{self.colors.GREEN}💻 System Ready:{self.colors.RESET} {self._format_cpu_info(info)}",
                f"{self.colors.GREEN}🧮 Memory:{self.colors.RESET} {self._format_memory_info(info)}",
                f"{self.colors.BLUE}📂 Repository:{self.colors.RESET} https://github.com/cincibrainlab/autoclean-eeg2source",
                f"{self.colors.BLUE}📖 Documentation:{self.colors.RESET} Use --help-detailed for comprehensive help",
                ""
            ])
        else:
            lines.extend([
                "=" * 60,
                f"AutoClean EEG2Source v{__version__}",
                "EEG Source Localization with Desikan-Killiany Atlas",
                "=" * 60,
                "",
                f"System Ready: {self._format_cpu_info(info)}",
                f"Memory: {self._format_memory_info(info)}",
                f"Repository: https://github.com/cincibrainlab/autoclean-eeg2source",
                f"Documentation: Use --help-detailed for comprehensive help",
                ""
            ])
        
        return "\n".join(lines)