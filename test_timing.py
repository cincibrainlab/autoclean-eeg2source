#!/usr/bin/env python3
"""
Quick timing test for the standalone processor.
"""

import sys
sys.path.insert(0, '.')

from autoclean_standalone import StandaloneEEGProcessor

def test_timing():
    """Test processing times for different modes."""
    test_file = "/Users/ernie/Data/testfiles_for_p300/140108_C5D1BL_P300_comp.set"
    
    print("🚀 Testing Standalone Processor Timing")
    print("=" * 40)
    
    # Test 1: Simulation mode (should be fast)
    print("\n📊 Test 1: Simulation Mode")
    print("-" * 30)
    processor_sim = StandaloneEEGProcessor(use_simulation=True)
    results_sim = processor_sim.process_single_file(test_file, "test_sim_output")
    
    # Test 2: Real mode (should show where the bottleneck is)
    print("\n📊 Test 2: Real Processing Mode")
    print("-" * 30)
    processor_real = StandaloneEEGProcessor(use_simulation=False)
    results_real = processor_real.process_single_file(test_file, "test_real_output")

if __name__ == "__main__":
    test_timing()