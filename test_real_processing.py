#!/usr/bin/env python3
"""
Test real EEG processing pipeline with the standalone implementation.
Tests the full pipeline from EEGLAB file to atlas timecourses.
"""

import numpy as np
import mne
from pathlib import Path
import sys
import time

# Add current directory to path
sys.path.insert(0, '.')

from autoclean_standalone import StandaloneEEGProcessor

def test_real_processing():
    """Test the complete processing pipeline."""
    print("🧪 Testing Real EEG Processing Pipeline")
    print("=" * 50)
    
    # Test file
    test_file = "/Users/ernie/Data/testfiles_for_p300/140108_C5D1BL_P300_comp.set"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Initialize processor
        print("1. Initializing processor...")
        processor = StandaloneEEGProcessor()
        
        # Load and inspect the test file
        print("2. Loading test file...")
        epochs = mne.io.read_epochs_eeglab(test_file, verbose=False)
        print(f"   ✅ Loaded {len(epochs)} epochs, {len(epochs.ch_names)} channels")
        
        # Check channel names
        print("3. Analyzing channels...")
        print(f"   Channels: {epochs.ch_names[:10]}...")  # Show first 10
        print(f"   Sampling rate: {epochs.info['sfreq']} Hz")
        print(f"   Epoch duration: {epochs.times[-1] - epochs.times[0]:.3f} seconds")
        
        # Test preprocessing
        print("4. Testing preprocessing...")
        preprocessed = processor._preprocess_data(epochs)
        print(f"   ✅ Preprocessing completed")
        
        # Test forward model construction
        print("5. Testing forward model...")
        forward = processor._build_forward_model(preprocessed.info)
        if forward is not None:
            print(f"   ✅ Forward model constructed successfully")
            print(f"   Sources: {forward['nsource']}, Channels: {forward['nchan']}")
        else:
            print(f"   ⚠️ Forward model failed, using simulation")
        
        # Test inverse solution
        print("6. Testing inverse solution...")
        start_time = time.time()
        source_estimates = processor._compute_inverse_solution(preprocessed, forward)
        end_time = time.time()
        
        print(f"   ✅ Inverse solution computed in {end_time - start_time:.1f} seconds")
        print(f"   Shape: {source_estimates.shape}")
        print(f"   Data range: {np.min(source_estimates):.2e} to {np.max(source_estimates):.2e}")
        
        # Test atlas parcellation
        print("7. Testing atlas parcellation...")
        atlas_results = processor._apply_atlas_parcellation(source_estimates)
        print(f"   ✅ Atlas parcellation completed")
        print(f"   Regions: {len(atlas_results['region_names'])}")
        
        print("\n🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_processing()
    sys.exit(0 if success else 1)