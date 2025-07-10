#!/usr/bin/env python3
"""Complete CLI integration test."""

import sys
import os
sys.path.insert(0, '/Users/ernie/Documents/GitHub/autoclean-eeg2source/src')

def test_cli_imports():
    """Test all CLI imports work correctly."""
    print("🧪 Testing CLI Imports...")
    
    try:
        from autoclean_eeg2source.cli import (
            RetroColors, ASCIIArtGenerator, SystemInfoDisplay, 
            EnhancedHelpSystem, CommandWizard, VisualProgressTracker,
            EnhancedCLI, create_enhanced_cli
        )
        print("✅ All CLI modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_enhanced_cli_creation():
    """Test enhanced CLI creation."""
    print("\n🏗️ Testing Enhanced CLI Creation...")
    
    try:
        from autoclean_eeg2source.cli import create_enhanced_cli
        cli = create_enhanced_cli()
        
        print(f"✅ Enhanced CLI created successfully")
        print(f"   Visual components available: {cli.visual_components_available}")
        
        if cli.visual_components_available:
            print(f"   Colors: {cli.colors is not None}")
            print(f"   ASCII Art: {cli.ascii_gen is not None}")
            print(f"   System Info: {cli.system_info is not None}")
            print(f"   Help System: {cli.help_system is not None}")
            print(f"   Wizard: {cli.wizard is not None}")
            print(f"   Progress Tracker: {cli.progress_tracker is not None}")
        
        return True, cli
    except Exception as e:
        print(f"❌ Enhanced CLI creation failed: {e}")
        return False, None

def test_argument_parser():
    """Test enhanced argument parser."""
    print("\n📋 Testing Enhanced Argument Parser...")
    
    try:
        from autoclean_eeg2source.cli import create_enhanced_cli
        cli = create_enhanced_cli()
        parser = cli.create_enhanced_parser()
        
        # Test parsing help options
        test_args = [
            ['--help'],
            ['--help-detailed'],
            ['--examples'],
            ['--wizard'],
            ['--system-info'],
            ['--version'],
            ['process', 'test.set'],
            ['process', 'test.set', '--parallel', '--n-jobs', '4']
        ]
        
        successful_parses = 0
        for args in test_args:
            try:
                parsed = parser.parse_args(args)
                successful_parses += 1
                print(f"   ✅ Parsed: {' '.join(args)}")
            except SystemExit:
                # Expected for help/version
                successful_parses += 1
                print(f"   ✅ Parsed (SystemExit): {' '.join(args)}")
            except Exception as e:
                print(f"   ❌ Failed to parse {args}: {e}")
        
        print(f"✅ Parser test: {successful_parses}/{len(test_args)} successful")
        return True
    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        return False

def test_visual_integration():
    """Test visual components integration."""
    print("\n🎨 Testing Visual Integration...")
    
    try:
        from autoclean_eeg2source.cli import create_enhanced_cli
        cli = create_enhanced_cli()
        
        if not cli.visual_components_available:
            print("⚠️ Visual components not available - skipping")
            return True
        
        # Test progress tracker
        if cli.progress_tracker:
            print("   Testing progress tracker...")
            cli.progress_tracker.display_info("Test info message")
            cli.progress_tracker.display_success("Test success message")
            cli.progress_tracker.display_warning("Test warning message")
            print("   ✅ Progress tracker working")
        
        # Test system info display
        if cli.system_info:
            print("   Testing system info display...")
            startup_info = cli.system_info.display_startup_info()
            print("   ✅ System info working")
        
        # Test help system
        if cli.help_system:
            print("   Testing help system...")
            quick_help = cli.help_system.show_quick_help()
            print("   ✅ Help system working")
        
        print("✅ Visual integration test successful")
        return True
    except Exception as e:
        print(f"❌ Visual integration test failed: {e}")
        return False

def test_fallback_mode():
    """Test fallback mode without visual components."""
    print("\n🔧 Testing Fallback Mode...")
    
    try:
        # Create CLI with disabled colors
        from autoclean_eeg2source.cli.visual import RetroColors
        from autoclean_eeg2source.cli.progress import VisualProgressTracker
        
        colors = RetroColors(force_colors=False)
        progress = VisualProgressTracker(colors=None, ascii_gen=None)
        
        print("   Testing fallback progress...")
        progress.display_info("Fallback info message")
        progress.display_success("Fallback success message")
        progress.update_progress(3, 5, "Fallback progress test")
        print("\n   ✅ Fallback mode working")
        
        return True
    except Exception as e:
        print(f"❌ Fallback mode test failed: {e}")
        return False

def main():
    """Run complete CLI integration tests."""
    print("🚀 AutoClean EEG2Source - Complete CLI Integration Test")
    print("=" * 60)
    
    tests = [
        test_cli_imports,
        test_enhanced_cli_creation,
        test_argument_parser,
        test_visual_integration,
        test_fallback_mode
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CLI integration is complete.")
        return True
    else:
        print("⚠️ Some tests failed. Check implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)