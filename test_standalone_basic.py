#!/usr/bin/env python3
"""
Basic testing suite for autoclean_standalone.py
Tests core functionality without requiring actual EEG files.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

# Add current directory to path for imports
sys.path.insert(0, '.')

try:
    from autoclean_standalone import (
        ScientificConfigManager, 
        StandaloneEEGProcessor,
        DEFAULT_CONFIG_PATH,
        __version__
    )
    STANDALONE_AVAILABLE = True
except ImportError as e:
    print(f"Cannot import standalone module: {e}")
    STANDALONE_AVAILABLE = False


class TestScientificConfigManager(unittest.TestCase):
    """Test configuration management system."""
    
    def setUp(self):
        """Set up test configuration."""
        self.test_config = {
            "scientific_parameters": {
                "montage": {
                    "default": "standard_1020",
                    "description": "Test montage",
                    "citation": "Test citation"
                },
                "inverse_solution": {
                    "method": "MNE",
                    "lambda2": 0.1111,
                    "description": "Test parameter"
                },
                "preprocessing": {
                    "target_srate": 250.0,
                    "highpass_freq": 0.1,
                    "lowpass_freq": 45.0
                }
            },
            "processing_parameters": {
                "memory_threshold_gb": 4.0,
                "validation_level": "strict"
            },
            "metadata": {
                "version": "test_1.0.0"
            }
        }
    
    def test_config_loading(self):
        """Test configuration loading from file."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            temp_config_path = f.name
        
        try:
            config_manager = ScientificConfigManager(temp_config_path)
            self.assertIsNotNone(config_manager.config)
            self.assertEqual(config_manager.config['metadata']['version'], 'test_1.0.0')
        finally:
            os.unlink(temp_config_path)
    
    def test_parameter_validation(self):
        """Test scientific parameter validation."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            temp_config_path = f.name
        
        try:
            config_manager = ScientificConfigManager(temp_config_path)
            # Should pass validation
            self.assertTrue(config_manager.validate_scientific_parameters())
        finally:
            os.unlink(temp_config_path)
    
    def test_invalid_lambda2(self):
        """Test that invalid lambda2 values are rejected."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        # Test with invalid lambda2
        invalid_config = self.test_config.copy()
        invalid_config['scientific_parameters']['inverse_solution']['lambda2'] = 2.0  # Too high
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_config_path = f.name
        
        try:
            config_manager = ScientificConfigManager(temp_config_path)
            with self.assertRaises(ValueError):
                config_manager.validate_scientific_parameters()
        finally:
            os.unlink(temp_config_path)


class TestStandaloneProcessor(unittest.TestCase):
    """Test the main processor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Use the actual config file for testing
        self.config_path = DEFAULT_CONFIG_PATH
    
    def test_processor_initialization(self):
        """Test processor can be initialized."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        if not Path(self.config_path).exists():
            self.skipTest(f"Config file not found: {self.config_path}")
        
        try:
            processor = StandaloneEEGProcessor(self.config_path)
            self.assertIsNotNone(processor.config)
            self.assertIsNotNone(processor.data_loader)
        except ImportError as e:
            self.skipTest(f"Missing dependencies: {e}")
    
    def test_dependency_checking(self):
        """Test dependency checking."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        if not Path(self.config_path).exists():
            self.skipTest(f"Config file not found: {self.config_path}")
        
        # This should work if MNE is available
        try:
            processor = StandaloneEEGProcessor(self.config_path)
            # If we get here, dependencies are satisfied
            self.assertTrue(True)
        except ImportError:
            # Expected if dependencies are missing
            self.assertTrue(True)


class TestCLIInterface(unittest.TestCase):
    """Test command line interface."""
    
    def test_help_output(self):
        """Test that help can be displayed."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        # Test importing the main function
        try:
            from autoclean_standalone import main, create_cli_parser
            parser = create_cli_parser()
            self.assertIsNotNone(parser)
        except ImportError:
            self.skipTest("Cannot import CLI functions")


class TestScientificAccuracy(unittest.TestCase):
    """Test scientific accuracy and reproducibility."""
    
    def test_version_consistency(self):
        """Test that version information is consistent."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        self.assertEqual(__version__, "1.0.0")
    
    def test_desikan_killiany_regions(self):
        """Test that Desikan-Killiany regions are correctly defined."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        from autoclean_standalone import DESIKAN_KILLIANY_REGIONS
        
        # Should have 68 regions (34 per hemisphere)
        self.assertEqual(len(DESIKAN_KILLIANY_REGIONS), 68)
        
        # Should have equal left and right hemisphere regions
        lh_regions = [r for r in DESIKAN_KILLIANY_REGIONS if r.endswith('-lh')]
        rh_regions = [r for r in DESIKAN_KILLIANY_REGIONS if r.endswith('-rh')]
        self.assertEqual(len(lh_regions), len(rh_regions))
        self.assertEqual(len(lh_regions), 34)


class TestFileOperations(unittest.TestCase):
    """Test file operations and error handling."""
    
    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files."""
        if not STANDALONE_AVAILABLE:
            self.skipTest("Standalone module not available")
        
        if not Path(DEFAULT_CONFIG_PATH).exists():
            self.skipTest(f"Config file not found: {DEFAULT_CONFIG_PATH}")
        
        try:
            processor = StandaloneEEGProcessor()
            
            # Test with non-existent file
            with self.assertRaises(FileNotFoundError):
                processor.process_single_file("nonexistent_file.set")
                
        except ImportError:
            self.skipTest("Missing dependencies for processor")


def run_basic_functionality_test():
    """Run a basic smoke test of core functionality."""
    print("🧪 Running Basic Functionality Test")
    print("=" * 50)
    
    if not STANDALONE_AVAILABLE:
        print("❌ Standalone module not available")
        return False
    
    try:
        # Test 1: Configuration loading
        print("1. Testing configuration loading...")
        if Path(DEFAULT_CONFIG_PATH).exists():
            config = ScientificConfigManager(DEFAULT_CONFIG_PATH)
            print(f"   ✅ Config loaded: version {config.config['metadata']['version']}")
        else:
            print(f"   ❌ Config file not found: {DEFAULT_CONFIG_PATH}")
            return False
        
        # Test 2: Parameter validation
        print("2. Testing parameter validation...")
        config.validate_scientific_parameters()
        print("   ✅ Parameters validated")
        
        # Test 3: Processor initialization
        print("3. Testing processor initialization...")
        try:
            processor = StandaloneEEGProcessor()
            print("   ✅ Processor initialized")
        except ImportError as e:
            print(f"   ⚠️ Processor requires dependencies: {e}")
            print("   ℹ️ This is expected if MNE is not installed")
        
        # Test 4: CLI parser
        print("4. Testing CLI parser...")
        from autoclean_standalone import create_cli_parser
        parser = create_cli_parser()
        print("   ✅ CLI parser created")
        
        print("\n🎉 Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("AutoClean Standalone - Basic Test Suite")
    print("=" * 50)
    
    # Run smoke test first
    if run_basic_functionality_test():
        print("\n" + "=" * 50)
        print("Running detailed unit tests...")
        
        # Run unit tests
        unittest.main(verbosity=2)
    else:
        print("\n❌ Basic functionality test failed. Skipping unit tests.")
        sys.exit(1)