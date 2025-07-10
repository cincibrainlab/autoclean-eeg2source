"""
Visual progress tracking with retro styling.

This module provides progress bars, status updates, and processing feedback
with 80s-inspired visual design.
"""

import time
import sys
from typing import Optional, Dict, Any, List


class VisualProgressTracker:
    """Visual progress tracking with retro styling."""
    
    def __init__(self, colors=None, ascii_gen=None):
        """
        Initialize progress tracker.
        
        Parameters
        ----------
        colors : RetroColors, optional
            Color system instance
        ascii_gen : ASCIIArtGenerator, optional
            ASCII art generator instance
        """
        self.colors = colors
        self.ascii_gen = ascii_gen
        self.start_time = time.time()
        self.current_file_start = None
        self.files_processed = 0
        self.total_files = 0
        self.errors = 0
        
    def start_processing(self, files: List[str], processor_type: str):
        """
        Display processing start information.
        
        Parameters
        ----------
        files : list
            List of files to process
        processor_type : str
            Type of processor being used
        """
        self.total_files = len(files)
        self.start_time = time.time()
        
        if self.colors:
            print(f"\n{self.colors.CYAN}{'═' * 60}{self.colors.RESET}")
            print(f"{self.colors.MAGENTA}🚀 Starting EEG Source Localization{self.colors.RESET}")
            print(f"{self.colors.CYAN}{'═' * 60}{self.colors.RESET}")
            print(f"{self.colors.WHITE}Processor: {self.colors.YELLOW}{processor_type}{self.colors.RESET}")
            print(f"{self.colors.WHITE}Files to process: {self.colors.GREEN}{self.total_files}{self.colors.RESET}")
            print(f"{self.colors.WHITE}Started: {self.colors.BLUE}{time.strftime('%Y-%m-%d %H:%M:%S')}{self.colors.RESET}")
            print(f"{self.colors.CYAN}{'─' * 60}{self.colors.RESET}\n")
        else:
            print(f"\n{'=' * 60}")
            print("Starting EEG Source Localization")
            print(f"{'=' * 60}")
            print(f"Processor: {processor_type}")
            print(f"Files to process: {self.total_files}")
            print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'─' * 60}\n")
    
    def start_file(self, file_path: str):
        """
        Start processing a file.
        
        Parameters
        ----------
        file_path : str
            Path to file being processed
        """
        self.current_file_start = time.time()
        filename = file_path.split('/')[-1]  # Get just the filename
        
        if self.colors:
            print(f"{self.colors.YELLOW}📁 Processing: {self.colors.WHITE}{filename}{self.colors.RESET}")
        else:
            print(f"Processing: {filename}")
    
    def update_progress(self, current: int, total: int, description: str = ""):
        """
        Update progress bar.
        
        Parameters
        ----------
        current : int
            Current progress
        total : int
            Total items
        description : str, optional
            Progress description
        """
        if self.ascii_gen:
            progress_bar = self.ascii_gen.generate_progress_bar(current, total, description)
            # Use carriage return to overwrite previous progress
            print(f"\r{progress_bar}", end="", flush=True)
        else:
            percentage = (current / total * 100) if total > 0 else 0
            bar_length = 40
            filled_length = int(bar_length * current // total) if total > 0 else 0
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            print(f"\r[{bar}] {percentage:.1f}% {description}", end="", flush=True)
    
    def finish_file(self, file_path: str, success: bool, error_msg: str = ""):
        """
        Finish processing a file.
        
        Parameters
        ----------
        file_path : str
            Path to processed file
        success : bool
            Whether processing was successful
        error_msg : str, optional
            Error message if failed
        """
        if self.current_file_start:
            duration = time.time() - self.current_file_start
        else:
            duration = 0
        
        filename = file_path.split('/')[-1]
        
        if success:
            self.files_processed += 1
            if self.colors:
                print(f"\r{self.colors.GREEN}✅ Completed: {self.colors.WHITE}{filename}{self.colors.RESET} {self.colors.DIM}({duration:.1f}s){self.colors.RESET}")
            else:
                print(f"\r✅ Completed: {filename} ({duration:.1f}s)")
        else:
            self.errors += 1
            if self.colors:
                print(f"\r{self.colors.RED}❌ Failed: {self.colors.WHITE}{filename}{self.colors.RESET}")
                if error_msg:
                    print(f"   {self.colors.RED}Error: {self.colors.WHITE}{error_msg}{self.colors.RESET}")
            else:
                print(f"\r❌ Failed: {filename}")
                if error_msg:
                    print(f"   Error: {error_msg}")
    
    def display_batch_progress(self, completed: int, total: int, current_file: str = ""):
        """
        Display overall batch progress.
        
        Parameters
        ----------
        completed : int
            Number of completed files
        total : int
            Total number of files
        current_file : str, optional
            Currently processing file
        """
        if self.ascii_gen:
            if current_file:
                description = f"File {completed + 1}/{total}: {current_file.split('/')[-1]}"
            else:
                description = f"Completed {completed}/{total} files"
            
            progress_bar = self.ascii_gen.generate_progress_bar(completed, total, description)
            print(f"\r{progress_bar}", end="", flush=True)
        else:
            percentage = (completed / total * 100) if total > 0 else 0
            bar_length = 50
            filled_length = int(bar_length * completed // total) if total > 0 else 0
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            if current_file:
                desc = f"File {completed + 1}/{total}: {current_file.split('/')[-1]}"
            else:
                desc = f"Completed {completed}/{total} files"
            
            print(f"\r[{bar}] {percentage:.1f}% {desc}", end="", flush=True)
    
    def display_final_summary(self, results: List[Dict[str, Any]]):
        """
        Display comprehensive processing summary.
        
        Parameters
        ----------
        results : list
            List of processing results
        """
        end_time = time.time()
        total_duration = end_time - self.start_time
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = len(results) - successful
        
        print("\n")  # New line after progress
        
        if self.ascii_gen:
            summary_content = {
                '⏱️ Total Time': self._format_duration(total_duration),
                '📁 Files Processed': f"{len(results)}",
                '✅ Successful': f"{successful}",
                '❌ Failed': f"{failed}",
                '📊 Success Rate': f"{(successful/len(results)*100):.1f}%" if results else "0%",
                '🚀 Average Rate': f"{len(results)/total_duration:.2f} files/second" if total_duration > 0 else "N/A"
            }
            
            print(self.ascii_gen.generate_status_box("PROCESSING COMPLETE", summary_content))
        else:
            print("=" * 60)
            print("PROCESSING COMPLETE")
            print("=" * 60)
            print(f"Total Time: {self._format_duration(total_duration)}")
            print(f"Files Processed: {len(results)}")
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")
            print(f"Success Rate: {(successful/len(results)*100):.1f}%" if results else "0%")
            print(f"Average Rate: {len(results)/total_duration:.2f} files/second" if total_duration > 0 else "N/A")
            print("=" * 60)
        
        # Display failed files if any
        if failed > 0:
            print()
            if self.colors:
                print(f"{self.colors.RED}❌ Failed Files:{self.colors.RESET}")
            else:
                print("❌ Failed Files:")
            
            for result in results:
                if result.get('status') != 'success':
                    filename = result.get('input_file', 'Unknown').split('/')[-1]
                    error = result.get('error', 'Unknown error')
                    
                    if self.colors:
                        print(f"   {self.colors.WHITE}{filename}{self.colors.RESET}: {self.colors.RED}{error}{self.colors.RESET}")
                    else:
                        print(f"   {filename}: {error}")
        
        print()
    
    def display_step_progress(self, step_name: str, current: int, total: int):
        """
        Display progress for individual processing steps.
        
        Parameters
        ----------
        step_name : str
            Name of the processing step
        current : int
            Current step number
        total : int
            Total number of steps
        """
        if self.colors:
            print(f"{self.colors.CYAN}[{current}/{total}]{self.colors.RESET} {self.colors.WHITE}{step_name}...{self.colors.RESET}")
        else:
            print(f"[{current}/{total}] {step_name}...")
    
    def display_warning(self, message: str):
        """
        Display a warning message.
        
        Parameters
        ----------
        message : str
            Warning message
        """
        if self.colors:
            print(f"{self.colors.YELLOW}⚠️ Warning: {self.colors.WHITE}{message}{self.colors.RESET}")
        else:
            print(f"⚠️ Warning: {message}")
    
    def display_info(self, message: str):
        """
        Display an info message.
        
        Parameters
        ----------
        message : str
            Info message
        """
        if self.colors:
            print(f"{self.colors.CYAN}ℹ️ {self.colors.WHITE}{message}{self.colors.RESET}")
        else:
            print(f"ℹ️ {message}")
    
    def display_success(self, message: str):
        """
        Display a success message.
        
        Parameters
        ----------
        message : str
            Success message
        """
        if self.colors:
            print(f"{self.colors.GREEN}✅ {self.colors.WHITE}{message}{self.colors.RESET}")
        else:
            print(f"✅ {message}")
    
    def display_error(self, message: str):
        """
        Display an error message.
        
        Parameters
        ----------
        message : str
            Error message
        """
        if self.colors:
            print(f"{self.colors.RED}❌ Error: {self.colors.WHITE}{message}{self.colors.RESET}")
        else:
            print(f"❌ Error: {message}")
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def create_spinner_animation(self, message: str = "Processing..."):
        """
        Create a simple spinner animation.
        
        Parameters
        ----------
        message : str
            Message to display with spinner
            
        Returns
        -------
        function
            Spinner update function
        """
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        counter = 0
        
        def update_spinner():
            nonlocal counter
            char = spinner_chars[counter % len(spinner_chars)]
            if self.colors:
                print(f"\r{self.colors.CYAN}{char} {self.colors.WHITE}{message}{self.colors.RESET}", end="", flush=True)
            else:
                print(f"\r{char} {message}", end="", flush=True)
            counter += 1
        
        return update_spinner