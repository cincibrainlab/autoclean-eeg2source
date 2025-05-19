"""Error reporting system for detailed, structured error logs."""

import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ErrorReporter:
    """Error reporting system for detailed, structured error logs."""
    
    def __init__(self, 
                 error_dir: str,
                 max_reports: int = 1000,
                 include_traceback: bool = True,
                 include_system_info: bool = True,
                 summary_file: Optional[str] = None):
        """
        Initialize error reporter.
        
        Parameters
        ----------
        error_dir : str
            Directory to save error reports
        max_reports : int
            Maximum number of reports to keep
        include_traceback : bool
            Whether to include traceback in reports
        include_system_info : bool
            Whether to include system info in reports
        summary_file : str, optional
            Path to summary file
        """
        self.error_dir = error_dir
        self.max_reports = max_reports
        self.include_traceback = include_traceback
        self.include_system_info = include_system_info
        self.summary_file = summary_file or os.path.join(error_dir, "error_summary.json")
        
        # Ensure directory exists
        os.makedirs(error_dir, exist_ok=True)
        
        # Initialize summary
        self.summary = self._load_summary()
        
        logger.info(f"Error reporter initialized with output directory: {error_dir}")
    
    def save_error(self, 
                  context: Dict[str, Any],
                  exception: Exception,
                  error_id: Optional[str] = None,
                  extra_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Save error report to file.
        
        Parameters
        ----------
        context : dict
            Context information (e.g., file_path, user_id)
        exception : Exception
            The exception that occurred
        error_id : str, optional
            Unique identifier for the error
        extra_data : dict, optional
            Additional data to include in the report
            
        Returns
        -------
        str
            Path to the error report file
        """
        # Generate a timestamp
        timestamp = datetime.now()
        
        # Generate an error ID if not provided
        if error_id is None:
            error_id = self._generate_error_id(exception, context)
        
        # Create report data
        report = {
            'error_id': error_id,
            'timestamp': timestamp.isoformat(),
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'context': context
        }
        
        # Add traceback if requested
        if self.include_traceback:
            report['traceback'] = traceback.format_exc()
        
        # Add system info if requested
        if self.include_system_info:
            report['system_info'] = self._get_system_info()
        
        # Add extra data if provided
        if extra_data:
            report['extra_data'] = extra_data
        
        # Save report to file
        report_file = self._get_report_filename(error_id, timestamp)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Update summary
        self._update_summary(error_id, report)
        
        # Cleanup old reports if needed
        self._cleanup_old_reports()
        
        logger.info(f"Saved error report to {report_file}")
        return report_file
    
    def get_error_summary(self, 
                         error_type: Optional[str] = None,
                         max_items: int = 100) -> List[Dict[str, Any]]:
        """
        Get summary of recent errors.
        
        Parameters
        ----------
        error_type : str, optional
            Filter by error type
        max_items : int
            Maximum number of items to return
            
        Returns
        -------
        list
            List of error summaries
        """
        # Load latest summary
        summary = self._load_summary()
        
        # Filter by error type if specified
        if error_type:
            filtered = [item for item in summary.get('errors', []) 
                      if item.get('error_type') == error_type]
        else:
            filtered = summary.get('errors', [])
        
        # Sort by timestamp (most recent first)
        sorted_errors = sorted(
            filtered, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )
        
        # Limit number of items
        return sorted_errors[:max_items]
    
    def get_error_counts(self) -> Dict[str, int]:
        """
        Get counts of errors by type.
        
        Returns
        -------
        dict
            Counts of errors by type
        """
        summary = self._load_summary()
        
        # Initialize counts
        counts = {}
        
        # Count by error type
        for error in summary.get('errors', []):
            error_type = error.get('error_type', 'unknown')
            counts[error_type] = counts.get(error_type, 0) + 1
        
        return counts
    
    def get_error_report(self, error_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full error report by ID.
        
        Parameters
        ----------
        error_id : str
            Error ID
            
        Returns
        -------
        dict
            Full error report
        """
        # Look up in summary
        summary = self._load_summary()
        
        # Find entry with matching ID
        matching = [error for error in summary.get('errors', []) 
                   if error.get('error_id') == error_id]
        
        if not matching:
            return None
        
        # Get report file path
        report_file = matching[0].get('report_file')
        
        if not report_file or not os.path.exists(report_file):
            return None
        
        # Load full report
        try:
            with open(report_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load error report {report_file}: {e}")
            return None
    
    def _generate_error_id(self, exception: Exception, context: Dict[str, Any]) -> str:
        """Generate a unique ID for the error."""
        # Create a hash of error type, message, and context
        hasher = hashlib.md5()
        
        # Add error type and message
        hasher.update(type(exception).__name__.encode())
        hasher.update(str(exception).encode())
        
        # Add key context elements if available
        for key in ['file_path', 'function_name', 'line_number', 'user_id']:
            if key in context:
                hasher.update(str(context[key]).encode())
        
        # Use first 12 chars of hexdigest
        return hasher.hexdigest()[:12]
    
    def _get_report_filename(self, error_id: str, timestamp: datetime) -> str:
        """Get the filename for an error report."""
        # Format: YYYYMMDD_HHMMSS_error_id.json
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{error_id}.json"
        return os.path.join(self.error_dir, filename)
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information."""
        import platform
        
        info = {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'system': platform.system(),
            'processor': platform.processor()
        }
        
        # Try to get package versions
        try:
            import mne
            info['mne_version'] = mne.__version__
        except ImportError:
            pass
        
        try:
            import numpy
            info['numpy_version'] = numpy.__version__
        except ImportError:
            pass
        
        return info
    
    def _load_summary(self) -> Dict[str, Any]:
        """Load error summary from file."""
        if os.path.exists(self.summary_file):
            try:
                with open(self.summary_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load error summary: {e}")
        
        # Initialize new summary
        return {
            'last_updated': datetime.now().isoformat(),
            'total_errors': 0,
            'errors': []
        }
    
    def _update_summary(self, error_id: str, report: Dict[str, Any]) -> None:
        """Update error summary with new report."""
        # Load current summary
        summary = self._load_summary()
        
        # Create summary entry
        entry = {
            'error_id': error_id,
            'timestamp': report['timestamp'],
            'error_type': report['error_type'],
            'error_message': report['error_message'],
            'report_file': self._get_report_filename(
                error_id, datetime.fromisoformat(report['timestamp'])
            )
        }
        
        # Add context info if available
        if 'context' in report:
            for key in ['file_path', 'function_name', 'user_id']:
                if key in report['context']:
                    entry[key] = report['context'][key]
        
        # Remove existing entry with same ID
        summary['errors'] = [e for e in summary.get('errors', []) 
                            if e.get('error_id') != error_id]
        
        # Add new entry
        summary['errors'].append(entry)
        
        # Update counts
        summary['total_errors'] = len(summary['errors'])
        summary['last_updated'] = datetime.now().isoformat()
        
        # Save updated summary
        try:
            with open(self.summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save error summary: {e}")
    
    def _cleanup_old_reports(self) -> None:
        """Cleanup old error reports if exceeding max_reports."""
        summary = self._load_summary()
        
        # Check if cleanup needed
        if len(summary.get('errors', [])) <= self.max_reports:
            return
        
        # Sort by timestamp (oldest first)
        sorted_errors = sorted(
            summary.get('errors', []),
            key=lambda x: x.get('timestamp', ''),
            reverse=False
        )
        
        # Get reports to remove
        to_remove = sorted_errors[:len(sorted_errors) - self.max_reports]
        
        # Remove files
        for error in to_remove:
            report_file = error.get('report_file')
            if report_file and os.path.exists(report_file):
                try:
                    os.remove(report_file)
                except Exception as e:
                    logger.error(f"Failed to remove old report {report_file}: {e}")
        
        # Update summary
        summary['errors'] = [e for e in summary.get('errors', []) 
                            if e not in to_remove]
        summary['total_errors'] = len(summary['errors'])
        summary['last_updated'] = datetime.now().isoformat()
        
        # Save updated summary
        try:
            with open(self.summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save error summary after cleanup: {e}")


class ErrorHandler:
    """Global error handler for structured error reporting."""
    
    def __init__(self, error_reporter: ErrorReporter):
        """
        Initialize error handler.
        
        Parameters
        ----------
        error_reporter : ErrorReporter
            Error reporter instance
        """
        self.error_reporter = error_reporter
    
    def handle_exception(self, exception: Exception, context: Dict[str, Any]) -> str:
        """
        Handle exception by logging and saving report.
        
        Parameters
        ----------
        exception : Exception
            The exception to handle
        context : dict
            Context information
            
        Returns
        -------
        str
            Error ID
        """
        # Log error
        logger.error(
            f"Error in {context.get('function_name', 'unknown')}: {exception}"
        )
        
        # Save error report
        report_file = self.error_reporter.save_error(context, exception)
        
        return os.path.basename(report_file).split('.')[0]
    
    def register_global_handler(self) -> None:
        """Register as global exception handler."""
        def global_exception_handler(exctype, value, tb):
            """Handle uncaught exceptions."""
            # Get context from traceback
            context = {}
            if tb:
                frame = traceback.extract_tb(tb)[-1]
                context = {
                    'file_path': frame.filename,
                    'function_name': frame.name,
                    'line_number': frame.lineno,
                    'code_context': frame.line
                }
            
            # Handle exception
            self.handle_exception(value, context)
            
            # Call original handler
            sys.__excepthook__(exctype, value, tb)
        
        # Set as global exception handler
        sys.excepthook = global_exception_handler