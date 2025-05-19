"""AutoClean EEG2Source: EEG source localization with DK atlas regions."""

__version__ = "0.2.0"
__author__ = "AutoClean Team"

from .core.converter import SequentialProcessor
from .core.memory_manager import MemoryManager
from .core.robust_processor import RobustProcessor
from .io.eeglab_reader import EEGLABReader
from .io.validators import EEGLABValidator
from .io.data_quality import QualityAssessor
from .utils.error_reporter import ErrorReporter, ErrorHandler
from .utils.logging import setup_logger

__all__ = [
    # Core processing
    "SequentialProcessor",
    "RobustProcessor",
    "MemoryManager",
    
    # IO and validation
    "EEGLABReader",
    "EEGLABValidator",
    "QualityAssessor",
    
    # Utilities
    "ErrorReporter",
    "ErrorHandler",
    "setup_logger",
]
