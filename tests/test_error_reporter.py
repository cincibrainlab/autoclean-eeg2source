"""Tests for the error reporter."""

import os
import json
import pytest
from datetime import datetime

from autoclean_eeg2source.utils.error_reporter import ErrorReporter, ErrorHandler


@pytest.fixture
def error_dir(tmp_path):
    """Create a temporary directory for error reports."""
    error_dir = tmp_path / "errors"
    os.makedirs(error_dir, exist_ok=True)
    return error_dir


@pytest.fixture
def create_reporter(error_dir):
    """Create an error reporter instance."""
    return ErrorReporter(
        error_dir=str(error_dir),
        max_reports=10,
        include_traceback=True,
        include_system_info=True
    )


class TestErrorReporter:
    """Test error reporter functionality."""
    
    def test_save_error(self, create_reporter, error_dir):
        """Test saving an error report."""
        reporter = create_reporter
        
        # Create a test exception
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            exception = e
        
        # Create context
        context = {
            'file_path': '/path/to/file.txt',
            'function_name': 'test_function',
            'user_id': 'test_user'
        }
        
        # Save error
        report_file = reporter.save_error(context, exception)
        
        # Check that file exists
        assert os.path.exists(report_file)
        
        # Load and check contents
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        assert report['error_type'] == 'ValueError'
        assert report['error_message'] == 'Test error message'
        assert 'context' in report
        assert report['context']['file_path'] == '/path/to/file.txt'
        assert 'traceback' in report
        assert 'system_info' in report
    
    def test_get_error_summary(self, create_reporter, error_dir):
        """Test getting error summary."""
        reporter = create_reporter
        
        # Create and save some errors
        exceptions = []
        for i in range(3):
            try:
                if i == 0:
                    raise ValueError(f"Value error {i}")
                elif i == 1:
                    raise TypeError(f"Type error {i}")
                else:
                    raise KeyError(f"Key error {i}")
            except Exception as e:
                exceptions.append(e)
                
                context = {
                    'file_path': f'/path/to/file{i}.txt',
                    'function_name': f'test_function{i}'
                }
                
                reporter.save_error(context, e)
        
        # Get summary
        summary = reporter.get_error_summary()
        
        assert len(summary) == 3
        
        # Get filtered summary
        value_errors = reporter.get_error_summary(error_type='ValueError')
        assert len(value_errors) == 1
        assert value_errors[0]['error_type'] == 'ValueError'
    
    def test_get_error_counts(self, create_reporter, error_dir):
        """Test getting error counts."""
        reporter = create_reporter
        
        # Create and save some errors
        for i in range(5):
            try:
                if i < 3:
                    raise ValueError(f"Value error {i}")
                else:
                    raise TypeError(f"Type error {i}")
            except Exception as e:
                context = {'file_path': f'/path/to/file{i}.txt'}
                reporter.save_error(context, e)
        
        # Get counts
        counts = reporter.get_error_counts()
        
        assert counts['ValueError'] == 3
        assert counts['TypeError'] == 2
    
    def test_get_error_report(self, create_reporter, error_dir):
        """Test getting a specific error report."""
        reporter = create_reporter
        
        # Create and save an error
        try:
            raise ValueError("Specific error")
        except ValueError as e:
            context = {'file_path': '/path/to/specific.txt'}
            reporter.save_error(context, e, error_id='test123')
        
        # Get report
        report = reporter.get_error_report('test123')
        
        assert report is not None
        assert report['error_message'] == 'Specific error'
        assert report['error_type'] == 'ValueError'
    
    def test_cleanup_old_reports(self, error_dir):
        """Test cleanup of old reports when max_reports is exceeded."""
        # Create reporter with small max_reports
        reporter = ErrorReporter(
            error_dir=str(error_dir),
            max_reports=2,  # Only keep 2 most recent
            include_traceback=False,
            include_system_info=False
        )
        
        # Create and save some errors with timestamps spaced apart
        for i in range(4):
            try:
                raise ValueError(f"Error {i}")
            except ValueError as e:
                context = {'file_path': f'/path/to/file{i}.txt'}
                
                # Manually set the error_id for predictable filenames
                error_id = f"error{i}"
                reporter.save_error(context, e, error_id=error_id)
        
        # Check summary count
        summary = reporter._load_summary()
        
        # Should only have 2 errors (the most recent ones)
        assert len(summary.get('errors', [])) == 2
        
        # The most recent errors should be kept
        error_ids = [error.get('error_id') for error in summary.get('errors', [])]
        assert 'error2' in error_ids
        assert 'error3' in error_ids
        
        # The oldest errors should be removed
        assert 'error0' not in error_ids
        assert 'error1' not in error_ids


class TestErrorHandler:
    """Test error handler functionality."""
    
    def test_handle_exception(self, create_reporter):
        """Test handling an exception."""
        handler = ErrorHandler(create_reporter)
        
        # Create an exception
        try:
            raise RuntimeError("Test runtime error")
        except RuntimeError as e:
            context = {
                'function_name': 'test_function',
                'file_path': '/path/to/file.py',
                'line_number': 42
            }
            
            error_id = handler.handle_exception(e, context)
            
            # Should return a valid error ID
            assert error_id is not None
            assert len(error_id) > 0