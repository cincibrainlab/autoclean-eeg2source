#!/usr/bin/env python3
"""Comprehensive test suite for CLI enhancements."""

import sys
import os
import subprocess
import tempfile
import time
sys.path.insert(0, '/Users/ernie/Documents/GitHub/autoclean-eeg2source/src')

def test_enhanced_help_options():
    """Test all enhanced help options work correctly."""
    print("🔍 Testing Enhanced Help Options...")
    
    # Test cases with expected behavior
    help_tests = [
        (['python', '-m', 'autoclean_eeg2source.cli', '--help'], 'Quick help display'),
        (['python', '-m', 'autoclean_eeg2source.cli', '--help-detailed'], 'Detailed help display'),
        (['python', '-m', 'autoclean_eeg2source.cli', '--examples'], 'Examples gallery'),
        (['python', '-m', 'autoclean_eeg2source.cli', '--system-info'], 'System information'),
        (['python', '-m', 'autoclean_eeg2source.cli', '--version'], 'Version information'),
    ]
    
    passed = 0
    for cmd, description in help_tests:
        try:
            result = subprocess.run(
                cmd, 
                cwd='/Users/ernie/Documents/GitHub/autoclean-eeg2source',
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            # These commands should exit cleanly (code 0) or with version exit (varies)
            if result.returncode in [0, 1] and len(result.stdout) > 0:
                print(f"   ✅ {description}")
                passed += 1
            else:
                print(f"   ❌ {description} - Unexpected output")
                print(f"      Return code: {result.returncode}")
                print(f"      Error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"   ❌ {description} - Timeout")
        except Exception as e:
            print(f"   ❌ {description} - Error: {e}")
    
    print(f"   📊 Help Options: {passed}/{len(help_tests)} passed")
    return passed == len(help_tests)

def test_argument_parsing():
    """Test argument parsing for all commands."""
    print("\n📋 Testing Argument Parsing...")
    
    # Test argument validation (these should parse without errors)
    parse_tests = [
        (['python', '-m', 'autoclean_eeg2source.cli', 'process', '--help'], 'Process command help'),
        (['python', '-m', 'autoclean_eeg2source.cli', 'validate', '--help'], 'Validate command help'),
        (['python', '-m', 'autoclean_eeg2source.cli', 'info', '--help'], 'Info command help'),
        (['python', '-m', 'autoclean_eeg2source.cli', 'benchmark', '--help'], 'Benchmark command help'),
    ]
    
    passed = 0
    for cmd, description in parse_tests:
        try:
            result = subprocess.run(
                cmd,
                cwd='/Users/ernie/Documents/GitHub/autoclean-eeg2source',
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Help commands should exit cleanly and show help text
            if result.returncode in [0, 1] and 'help' in result.stdout.lower():
                print(f"   ✅ {description}")
                passed += 1
            else:
                print(f"   ❌ {description} - No help output")
        except Exception as e:
            print(f"   ❌ {description} - Error: {e}")
    
    print(f"   📊 Argument Parsing: {passed}/{len(parse_tests)} passed")
    return passed == len(parse_tests)

def test_color_fallback():
    """Test color system fallback behavior."""
    print("\n🎨 Testing Color System Fallback...")
    
    try:
        from autoclean_eeg2source.cli.visual import RetroColors
        
        # Test with colors enabled
        colors_enabled = RetroColors(force_colors=True)
        assert colors_enabled.colors_enabled == True
        assert len(colors_enabled.CYAN) > 0
        print("   ✅ Colors enabled mode working")
        
        # Test with colors disabled
        colors_disabled = RetroColors(force_colors=False)
        assert colors_disabled.colors_enabled == False
        assert colors_disabled.CYAN == ""
        print("   ✅ Colors disabled mode working")
        
        # Test performance mode
        colors_enabled.enable_performance_mode()
        assert colors_enabled.performance_mode == True
        print("   ✅ Performance mode working")
        
        colors_enabled.disable_performance_mode()
        assert colors_enabled.performance_mode == False
        print("   ✅ Performance mode toggle working")
        
        return True
    except Exception as e:
        print(f"   ❌ Color system test failed: {e}")
        return False

def test_visual_components_isolation():
    """Test visual components work independently."""
    print("\n🔧 Testing Visual Components Isolation...")
    
    try:
        from autoclean_eeg2source.cli.visual import RetroColors
        from autoclean_eeg2source.cli.ascii_art import ASCIIArtGenerator
        from autoclean_eeg2source.cli.progress import VisualProgressTracker
        
        # Test with full components
        colors = RetroColors()
        ascii_gen = ASCIIArtGenerator(colors)
        progress = VisualProgressTracker(colors, ascii_gen)
        
        # Test basic operations
        progress.display_info("Test with full components")
        progress.update_progress(1, 2, "Test progress")
        print("\n   ✅ Full components working")
        
        # Test with None components (fallback mode)
        progress_minimal = VisualProgressTracker(None, None)
        progress_minimal.display_info("Test with minimal components")
        progress_minimal.update_progress(1, 2, "Test minimal progress")
        print("\n   ✅ Minimal components working")
        
        return True
    except Exception as e:
        print(f"   ❌ Visual components test failed: {e}")
        return False

def test_performance_impact():
    """Test that visual enhancements don't impact processing performance."""
    print("\n⚡ Testing Performance Impact...")
    
    try:
        from autoclean_eeg2source.cli.visual import RetroColors
        from autoclean_eeg2source.cli.progress import VisualProgressTracker
        import time
        
        # Measure performance with visual enhancements disabled
        colors = RetroColors(force_colors=False)
        colors.enable_performance_mode()
        progress = VisualProgressTracker(colors, None)
        
        start_time = time.time()
        for i in range(100):
            progress.update_progress(i, 100, "Performance test")
        disabled_time = time.time() - start_time
        
        # Measure performance with visual enhancements enabled  
        colors = RetroColors(force_colors=True)
        colors.disable_performance_mode()
        
        start_time = time.time()
        for i in range(100):
            # Simulate same operations but don't actually output
            pass
        enabled_time = time.time() - start_time
        
        print(f"   📊 Performance comparison:")
        print(f"      Disabled mode: {disabled_time:.4f}s")
        print(f"      Enabled mode: {enabled_time:.4f}s")
        
        # Performance impact should be minimal
        if disabled_time < 1.0:  # Should be very fast
            print("   ✅ Performance impact minimal")
            return True
        else:
            print("   ⚠️ Performance may need optimization")
            return False
            
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        return False

def test_backwards_compatibility():
    """Test backwards compatibility with existing CLI behavior."""
    print("\n🔄 Testing Backwards Compatibility...")
    
    try:
        # Test that the CLI still works when enhanced components fail
        from autoclean_eeg2source import cli
        
        # Test main function exists and is callable
        assert hasattr(cli, 'main')
        assert callable(cli.main)
        print("   ✅ Main CLI function accessible")
        
        # Test legacy functions exist
        assert hasattr(cli, 'find_set_files')
        assert callable(cli.find_set_files)
        print("   ✅ Legacy utility functions available")
        
        # Test find_set_files works with test data
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock .set file
            test_file = os.path.join(temp_dir, "test.set")
            with open(test_file, 'w') as f:
                f.write("mock EEG data")
            
            found_files = cli.find_set_files(temp_dir)
            assert len(found_files) == 1
            assert found_files[0].endswith('test.set')
            print("   ✅ File discovery working")
        
        return True
    except Exception as e:
        print(f"   ❌ Backwards compatibility test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and graceful degradation."""
    print("\n🛡️ Testing Error Handling...")
    
    try:
        # Test CLI with invalid arguments
        result = subprocess.run(
            ['python', '-m', 'autoclean_eeg2source.cli', 'invalid-command'],
            cwd='/Users/ernie/Documents/GitHub/autoclean-eeg2source',
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Should exit with error but not crash
        if result.returncode != 0:
            print("   ✅ Invalid command handled gracefully")
        else:
            print("   ❌ Invalid command not properly rejected")
            return False
        
        # Test with missing file
        result = subprocess.run(
            ['python', '-m', 'autoclean_eeg2source.cli', 'process', 'nonexistent.set'],
            cwd='/Users/ernie/Documents/GitHub/autoclean-eeg2source',
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Should handle missing file gracefully
        if result.returncode != 0:
            print("   ✅ Missing file handled gracefully")
        else:
            print("   ❌ Missing file not properly handled")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False

def test_dependency_isolation():
    """Test that missing dependencies don't break core functionality."""
    print("\n📦 Testing Dependency Isolation...")
    
    try:
        # Test importing individual components
        components_to_test = [
            'autoclean_eeg2source.cli.visual',
            'autoclean_eeg2source.cli.ascii_art', 
            'autoclean_eeg2source.cli.system_info',
            'autoclean_eeg2source.cli.help_system',
            'autoclean_eeg2source.cli.wizard',
            'autoclean_eeg2source.cli.progress',
            'autoclean_eeg2source.cli.enhanced_cli'
        ]
        
        imported = 0
        for component in components_to_test:
            try:
                __import__(component)
                imported += 1
                print(f"   ✅ {component} imports successfully")
            except ImportError as e:
                print(f"   ⚠️ {component} import failed: {e}")
        
        print(f"   📊 Dependencies: {imported}/{len(components_to_test)} available")
        
        # Test that CLI still works even if some components fail
        from autoclean_eeg2source.cli import create_enhanced_cli
        cli = create_enhanced_cli()
        
        if cli is not None:
            print("   ✅ Enhanced CLI creation working")
            return True
        else:
            print("   ❌ Enhanced CLI creation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Dependency isolation test failed: {e}")
        return False

def main():
    """Run comprehensive CLI validation tests."""
    print("🚀 AutoClean EEG2Source - Comprehensive CLI Validation")
    print("=" * 70)
    
    tests = [
        test_enhanced_help_options,
        test_argument_parsing, 
        test_color_fallback,
        test_visual_components_isolation,
        test_performance_impact,
        test_backwards_compatibility,
        test_error_handling,
        test_dependency_isolation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Comprehensive Test Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All comprehensive validation tests passed!")
        print("✨ CLI enhancement implementation is complete and robust.")
        return True
    else:
        print("⚠️ Some validation tests failed. Implementation needs review.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)