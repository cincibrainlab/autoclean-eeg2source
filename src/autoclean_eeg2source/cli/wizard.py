"""
Interactive command builder wizard.

This module provides a step-by-step wizard for building AutoClean EEG2Source
commands with validation and helpful guidance.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple


class CommandWizard:
    """Interactive command builder with visual guidance."""
    
    def __init__(self, colors=None, ascii_gen=None):
        """
        Initialize command wizard.
        
        Parameters
        ----------
        colors : RetroColors, optional
            Color system instance for styling
        ascii_gen : ASCIIArtGenerator, optional
            ASCII art generator instance
        """
        self.colors = colors
        self.ascii_gen = ascii_gen
        self.command_parts = {}
        self.processing_modes = {
            '1': ('sequential', 'Sequential Processing', '🚀', 'Memory efficient, single-file processing'),
            '2': ('parallel', 'Parallel Processing', '⚡', 'High-speed batch processing'),
            '3': ('robust', 'Robust Processing', '🛡️', 'Maximum error recovery'),
            '4': ('gpu', 'GPU Accelerated', '🎮', 'CUDA-powered processing'),
            '5': ('cached', 'Cached Processing', '💾', 'Optimized for similar files')
        }
    
    def run_wizard(self) -> str:
        """
        Start interactive command building session.
        
        Returns
        -------
        str
            Generated command string
        """
        # Display header
        if self.ascii_gen:
            print(self.ascii_gen.generate_header())
        else:
            print("=" * 60)
            print("AutoClean EEG2Source Command Wizard")
            print("=" * 60)
        
        print()
        if self.colors:
            print(f"{self.colors.CYAN}🧙‍♂️ Welcome to the AutoClean EEG2Source Command Wizard!{self.colors.RESET}")
            print(f"{self.colors.WHITE}This wizard will help you build the perfect command for your EEG processing needs.{self.colors.RESET}")
        else:
            print("Welcome to the AutoClean EEG2Source Command Wizard!")
            print("This wizard will help you build the perfect command for your EEG processing needs.")
        print()
        
        # Step-by-step command building
        try:
            self._get_input_path()
            self._get_processing_mode()
            self._get_output_options()
            self._get_advanced_options()
            
            # Generate and display final command
            final_command = self._build_command()
            self._display_final_command(final_command)
            
            return final_command
            
        except KeyboardInterrupt:
            if self.colors:
                print(f"\n{self.colors.YELLOW}Wizard cancelled by user.{self.colors.RESET}")
            else:
                print("\nWizard cancelled by user.")
            return ""
        except Exception as e:
            if self.colors:
                print(f"\n{self.colors.RED}Error in wizard: {e}{self.colors.RESET}")
            else:
                print(f"\nError in wizard: {e}")
            return ""
    
    def _get_input_path(self):
        """Get and validate input path with visual feedback."""
        if self.colors:
            print(f"{self.colors.YELLOW}Step 1: Input Selection{self.colors.RESET}")
            print(f"{self.colors.CYAN}{'─' * 30}{self.colors.RESET}")
        else:
            print("Step 1: Input Selection")
            print("─" * 30)
        
        while True:
            if self.colors:
                prompt = f"{self.colors.GREEN}Enter path to .set file or directory:{self.colors.RESET} "
            else:
                prompt = "Enter path to .set file or directory: "
            
            input_path = input(prompt).strip()
            
            if not input_path:
                if self.colors:
                    print(f"{self.colors.RED}Please enter a path.{self.colors.RESET}")
                else:
                    print("Please enter a path.")
                continue
            
            # Validate path
            if os.path.exists(input_path):
                if os.path.isfile(input_path):
                    if input_path.endswith('.set'):
                        self.command_parts['input_path'] = input_path
                        if self.colors:
                            print(f"{self.colors.GREEN}✅ Valid .set file: {input_path}{self.colors.RESET}")
                        else:
                            print(f"✅ Valid .set file: {input_path}")
                        break
                    else:
                        if self.colors:
                            print(f"{self.colors.RED}File must be a .set file.{self.colors.RESET}")
                        else:
                            print("File must be a .set file.")
                        continue
                elif os.path.isdir(input_path):
                    # Check for .set files in directory
                    set_files = []
                    for root, dirs, files in os.walk(input_path):
                        set_files.extend([f for f in files if f.endswith('.set')])
                    
                    if set_files:
                        self.command_parts['input_path'] = input_path
                        if self.colors:
                            print(f"{self.colors.GREEN}✅ Valid directory: {len(set_files)} .set files found{self.colors.RESET}")
                        else:
                            print(f"✅ Valid directory: {len(set_files)} .set files found")
                        
                        # Ask about recursive processing
                        if self.colors:
                            recursive_prompt = f"{self.colors.CYAN}Search subdirectories recursively? [y/N]:{self.colors.RESET} "
                        else:
                            recursive_prompt = "Search subdirectories recursively? [y/N]: "
                        
                        recursive = input(recursive_prompt).strip().lower()
                        if recursive in ['y', 'yes']:
                            self.command_parts['recursive'] = True
                            if self.colors:
                                print(f"{self.colors.GREEN}✅ Recursive search enabled{self.colors.RESET}")
                            else:
                                print("✅ Recursive search enabled")
                        break
                    else:
                        if self.colors:
                            print(f"{self.colors.RED}No .set files found in directory.{self.colors.RESET}")
                        else:
                            print("No .set files found in directory.")
                        continue
            else:
                if self.colors:
                    print(f"{self.colors.RED}Path does not exist: {input_path}{self.colors.RESET}")
                else:
                    print(f"Path does not exist: {input_path}")
                continue
        
        print()
    
    def _get_processing_mode(self):
        """Interactive processing mode selection."""
        if self.colors:
            print(f"{self.colors.YELLOW}Step 2: Processing Mode Selection{self.colors.RESET}")
            print(f"{self.colors.CYAN}{'─' * 40}{self.colors.RESET}")
        else:
            print("Step 2: Processing Mode Selection")
            print("─" * 40)
        
        # Display processing mode options
        processing_options = [
            (key, details[2], details[1], details[3]) 
            for key, details in self.processing_modes.items()
        ]
        
        if self.ascii_gen:
            menu = self.ascii_gen.generate_menu_box("PROCESSING MODE SELECTION", processing_options)
            print(menu)
        else:
            print("Choose your processing strategy:")
            print()
            for key, emoji, name, description in processing_options:
                print(f"[{key}] {emoji} {name} - {description}")
            print()
        
        while True:
            if self.colors:
                prompt = f"{self.colors.GREEN}Enter selection [1-5]:{self.colors.RESET} "
            else:
                prompt = "Enter selection [1-5]: "
            
            choice = input(prompt).strip()
            
            if choice in self.processing_modes:
                mode_key, mode_name, emoji, description = self.processing_modes[choice]
                self.command_parts['processing_mode'] = mode_key
                
                if self.colors:
                    print(f"{self.colors.GREEN}✅ Selected: {emoji} {mode_name}{self.colors.RESET}")
                else:
                    print(f"✅ Selected: {emoji} {mode_name}")
                
                # Additional options based on mode
                if mode_key == 'parallel':
                    self._get_parallel_options()
                elif mode_key == 'robust':
                    self._get_robust_options()
                elif mode_key == 'gpu':
                    self._get_gpu_options()
                
                break
            else:
                if self.colors:
                    print(f"{self.colors.RED}Please enter a number between 1 and 5.{self.colors.RESET}")
                else:
                    print("Please enter a number between 1 and 5.")
        
        print()
    
    def _get_parallel_options(self):
        """Get parallel processing specific options."""
        if self.colors:
            prompt = f"{self.colors.CYAN}Number of parallel jobs (default: 4):{self.colors.RESET} "
        else:
            prompt = "Number of parallel jobs (default: 4): "
        
        n_jobs = input(prompt).strip()
        if n_jobs:
            try:
                n_jobs_int = int(n_jobs)
                if n_jobs_int > 0:
                    self.command_parts['n_jobs'] = n_jobs_int
                else:
                    if self.colors:
                        print(f"{self.colors.YELLOW}Invalid number, using default (4){self.colors.RESET}")
                    else:
                        print("Invalid number, using default (4)")
            except ValueError:
                if self.colors:
                    print(f"{self.colors.YELLOW}Invalid number, using default (4){self.colors.RESET}")
                else:
                    print("Invalid number, using default (4)")
        
        # Batch processing option
        if self.colors:
            batch_prompt = f"{self.colors.CYAN}Enable batch processing optimization? [Y/n]:{self.colors.RESET} "
        else:
            batch_prompt = "Enable batch processing optimization? [Y/n]: "
        
        batch = input(batch_prompt).strip().lower()
        if batch not in ['n', 'no']:
            self.command_parts['batch_processing'] = True
    
    def _get_robust_options(self):
        """Get robust processing specific options."""
        if self.colors:
            prompt = f"{self.colors.CYAN}Error reporting directory (optional):{self.colors.RESET} "
        else:
            prompt = "Error reporting directory (optional): "
        
        error_dir = input(prompt).strip()
        if error_dir:
            self.command_parts['error_dir'] = error_dir
    
    def _get_gpu_options(self):
        """Get GPU processing specific options."""
        if self.colors:
            print(f"{self.colors.CYAN}GPU processing requires CUDA-compatible hardware.{self.colors.RESET}")
            prompt = f"{self.colors.CYAN}Number of parallel jobs (default: 4):{self.colors.RESET} "
        else:
            print("GPU processing requires CUDA-compatible hardware.")
            prompt = "Number of parallel jobs (default: 4): "
        
        n_jobs = input(prompt).strip()
        if n_jobs:
            try:
                n_jobs_int = int(n_jobs)
                if n_jobs_int > 0:
                    self.command_parts['n_jobs'] = n_jobs_int
            except ValueError:
                pass
    
    def _get_output_options(self):
        """Get output configuration."""
        if self.colors:
            print(f"{self.colors.YELLOW}Step 3: Output Configuration{self.colors.RESET}")
            print(f"{self.colors.CYAN}{'─' * 35}{self.colors.RESET}")
        else:
            print("Step 3: Output Configuration")
            print("─" * 35)
        
        # Output directory
        if self.colors:
            prompt = f"{self.colors.GREEN}Output directory (default: ./output):{self.colors.RESET} "
        else:
            prompt = "Output directory (default: ./output): "
        
        output_dir = input(prompt).strip()
        if output_dir:
            self.command_parts['output_dir'] = output_dir
        else:
            self.command_parts['output_dir'] = './output'
        
        if self.colors:
            print(f"{self.colors.GREEN}✅ Output directory: {self.command_parts['output_dir']}{self.colors.RESET}")
        else:
            print(f"✅ Output directory: {self.command_parts['output_dir']}")
        
        print()
    
    def _get_advanced_options(self):
        """Get advanced processing options."""
        if self.colors:
            print(f"{self.colors.YELLOW}Step 4: Advanced Options (Optional){self.colors.RESET}")
            print(f"{self.colors.CYAN}{'─' * 40}{self.colors.RESET}")
        else:
            print("Step 4: Advanced Options (Optional)")
            print("─" * 40)
        
        # Montage selection
        montages = [
            'standard_1020', 'standard_1005', 'GSN-HydroCel-32', 'GSN-HydroCel-64',
            'GSN-HydroCel-128', 'GSN-HydroCel-256', 'biosemi64', 'biosemi128'
        ]
        
        if self.colors:
            print(f"{self.colors.WHITE}Available montages: {', '.join(montages)}{self.colors.RESET}")
            prompt = f"{self.colors.GREEN}EEG montage (default: standard_1020):{self.colors.RESET} "
        else:
            print(f"Available montages: {', '.join(montages)}")
            prompt = "EEG montage (default: standard_1020): "
        
        montage = input(prompt).strip()
        if montage and montage in montages:
            self.command_parts['montage'] = montage
            if self.colors:
                print(f"{self.colors.GREEN}✅ Montage: {montage}{self.colors.RESET}")
            else:
                print(f"✅ Montage: {montage}")
        elif montage and montage not in montages:
            if self.colors:
                print(f"{self.colors.YELLOW}Unknown montage, using default (standard_1020){self.colors.RESET}")
            else:
                print("Unknown montage, using default (standard_1020)")
        
        # Resampling frequency
        if self.colors:
            prompt = f"{self.colors.GREEN}Resampling frequency in Hz (default: 250):{self.colors.RESET} "
        else:
            prompt = "Resampling frequency in Hz (default: 250): "
        
        resample_freq = input(prompt).strip()
        if resample_freq:
            try:
                freq = float(resample_freq)
                if freq > 0:
                    self.command_parts['resample_freq'] = freq
                    if self.colors:
                        print(f"{self.colors.GREEN}✅ Resampling: {freq}Hz{self.colors.RESET}")
                    else:
                        print(f"✅ Resampling: {freq}Hz")
            except ValueError:
                if self.colors:
                    print(f"{self.colors.YELLOW}Invalid frequency, using default (250Hz){self.colors.RESET}")
                else:
                    print("Invalid frequency, using default (250Hz)")
        
        # Logging level
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if self.colors:
            print(f"{self.colors.WHITE}Log levels: {', '.join(log_levels)}{self.colors.RESET}")
            prompt = f"{self.colors.GREEN}Logging level (default: INFO):{self.colors.RESET} "
        else:
            print(f"Log levels: {', '.join(log_levels)}")
            prompt = "Logging level (default: INFO): "
        
        log_level = input(prompt).strip().upper()
        if log_level and log_level in log_levels:
            self.command_parts['log_level'] = log_level
            if self.colors:
                print(f"{self.colors.GREEN}✅ Log level: {log_level}{self.colors.RESET}")
            else:
                print(f"✅ Log level: {log_level}")
        
        print()
    
    def _build_command(self) -> str:
        """Generate final command string."""
        cmd_parts = ['autoclean-eeg2source']
        
        # Determine command based on processing mode
        processing_mode = self.command_parts.get('processing_mode', 'sequential')
        
        if processing_mode == 'sequential':
            cmd_parts.append('process')
        elif processing_mode == 'parallel':
            cmd_parts.extend(['process', '--parallel'])
            if self.command_parts.get('batch_processing'):
                cmd_parts.append('--batch-processing')
        elif processing_mode == 'robust':
            cmd_parts.extend(['process', '--robust'])
        elif processing_mode == 'gpu':
            cmd_parts.extend(['process', '--gpu'])
        elif processing_mode == 'cached':
            cmd_parts.extend(['process', '--parallel', '--enable-cache'])
        else:
            cmd_parts.append('process')
        
        # Add input path
        input_path = self.command_parts.get('input_path', '')
        if ' ' in input_path:
            cmd_parts.append(f'"{input_path}"')
        else:
            cmd_parts.append(input_path)
        
        # Add options
        if self.command_parts.get('output_dir'):
            cmd_parts.extend(['--output-dir', self.command_parts['output_dir']])
        
        if self.command_parts.get('recursive'):
            cmd_parts.append('--recursive')
        
        if self.command_parts.get('n_jobs'):
            cmd_parts.extend(['--n-jobs', str(self.command_parts['n_jobs'])])
        
        if self.command_parts.get('montage'):
            cmd_parts.extend(['--montage', self.command_parts['montage']])
        
        if self.command_parts.get('resample_freq'):
            cmd_parts.extend(['--resample-freq', str(self.command_parts['resample_freq'])])
        
        if self.command_parts.get('log_level'):
            cmd_parts.extend(['--log-level', self.command_parts['log_level']])
        
        if self.command_parts.get('error_dir'):
            cmd_parts.extend(['--error-dir', self.command_parts['error_dir']])
        
        return ' '.join(cmd_parts)
    
    def _display_final_command(self, command: str):
        """Display the generated command with copy instructions."""
        if self.ascii_gen:
            content = {
                'Generated Command': command,
                'Ready to Execute': 'Copy the command below and run it in your terminal',
                'Tip': 'You can modify any parameters as needed'
            }
            print(self.ascii_gen.generate_status_box("COMMAND GENERATED", content))
        else:
            print("=" * 60)
            print("COMMAND GENERATED")
            print("=" * 60)
            print(f"Generated Command: {command}")
            print("Ready to Execute: Copy the command below and run it in your terminal")
            print("Tip: You can modify any parameters as needed")
            print("=" * 60)
        
        print()
        if self.colors:
            print(f"{self.colors.GREEN}📋 Copy this command:{self.colors.RESET}")
            print(f"{self.colors.YELLOW}{command}{self.colors.RESET}")
        else:
            print("📋 Copy this command:")
            print(command)
        print()
        
        if self.colors:
            print(f"{self.colors.CYAN}💡 Next steps:{self.colors.RESET}")
            print(f"{self.colors.WHITE}1. Copy the command above{self.colors.RESET}")
            print(f"{self.colors.WHITE}2. Paste it in your terminal{self.colors.RESET}")
            print(f"{self.colors.WHITE}3. Press Enter to start processing{self.colors.RESET}")
        else:
            print("💡 Next steps:")
            print("1. Copy the command above")
            print("2. Paste it in your terminal")
            print("3. Press Enter to start processing")
        print()