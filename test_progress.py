#!/usr/bin/env python3
"""Test script for visual progress tracking."""

import sys
import time
import os
sys.path.insert(0, '/Users/ernie/Documents/GitHub/autoclean-eeg2source/src')

from autoclean_eeg2source.cli.visual import RetroColors
from autoclean_eeg2source.cli.ascii_art import ASCIIArtGenerator
from autoclean_eeg2source.cli.progress import VisualProgressTracker

def test_progress_tracking():
    """Test the visual progress tracking."""
    colors = RetroColors(force_colors=True)
    ascii_gen = ASCIIArtGenerator(colors)
    progress = VisualProgressTracker(colors, ascii_gen)
    
    print("🎮 Testing AutoClean EEG2Source Visual Progress Tracking\n")
    
    # Test basic progress tracking
    print("📊 Testing Basic Progress Tracking:")
    test_files = ['file1.set', 'file2.set', 'file3.set', 'file4.set', 'file5.set']
    
    # Start processing
    progress.start_processing(test_files, "Parallel Processor")
    time.sleep(0.5)
    
    # Simulate file processing
    for i, file_path in enumerate(test_files):
        progress.start_file(file_path)
        
        # Simulate processing steps
        for step in range(5):
            progress.update_progress(step + 1, 5, f"Step {step + 1}/5")
            time.sleep(0.1)
        
        # Finish file (simulate success/failure)
        success = i != 2  # Make file3 fail for testing
        error_msg = "Montage compatibility error" if not success else ""
        progress.finish_file(file_path, success, error_msg)
        
        # Show batch progress
        progress.display_batch_progress(i + 1, len(test_files))
        time.sleep(0.2)
    
    print("\n")
    
    # Test final summary
    print("📋 Testing Final Summary:")
    mock_results = [
        {'status': 'success', 'input_file': 'file1.set'},
        {'status': 'success', 'input_file': 'file2.set'},
        {'status': 'failed', 'input_file': 'file3.set', 'error': 'Montage compatibility error'},
        {'status': 'success', 'input_file': 'file4.set'},
        {'status': 'success', 'input_file': 'file5.set'},
    ]
    progress.display_final_summary(mock_results)
    print()
    
    # Test different message types
    print("💬 Testing Message Types:")
    progress.display_info("Loading EEG data...")
    progress.display_warning("HEOG/VEOG channels detected")
    progress.display_success("Montage set successfully")
    progress.display_error("Failed to read .fdt file")
    print()
    
    # Test step progress
    print("📈 Testing Step Progress:")
    steps = ["Loading data", "Setting montage", "Computing forward solution", "Applying inverse", "Saving results"]
    for i, step in enumerate(steps):
        progress.display_step_progress(step, i + 1, len(steps))
        time.sleep(0.3)
    print()
    
    # Test duration formatting
    print("⏱️ Testing Duration Formatting:")
    test_durations = [30.5, 125.3, 3665.7, 7265.2]
    for duration in test_durations:
        formatted = progress._format_duration(duration)
        print(f"   {duration:.1f}s = {formatted}")
    print()
    
    # Test spinner animation
    print("🌀 Testing Spinner Animation:")
    spinner = progress.create_spinner_animation("Computing inverse solution")
    for i in range(20):
        spinner()
        time.sleep(0.1)
    print("  Done!")
    print()
    
    # Test fallback mode
    print("🔧 Testing Fallback Mode:")
    progress_fallback = VisualProgressTracker(colors=None, ascii_gen=None)
    
    print("   Progress without colors:")
    for i in range(6):
        progress_fallback.update_progress(i, 5, f"Step {i}/5")
        time.sleep(0.1)
    print("  ✅ Completed")
    
    print("   Messages without colors:")
    progress_fallback.display_success("Processing completed successfully")
    progress_fallback.display_error("Sample error message")
    progress_fallback.display_warning("Sample warning message")
    print()
    
    print("✅ All progress tracking tests completed successfully!")
    print()
    print("🎨 Visual Features Demonstrated:")
    print("   - Real-time progress bars with retro styling")
    print("   - Comprehensive processing summaries")
    print("   - Color-coded status messages")
    print("   - Batch processing visualization")
    print("   - Spinner animations for long operations")
    print("   - Proper fallback for terminals without color support")

if __name__ == "__main__":
    test_progress_tracking()