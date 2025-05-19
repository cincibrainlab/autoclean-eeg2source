"""AutoClean EEG2Source: EEG source localization with DK atlas regions."""

__version__ = "0.1.0"
__author__ = "AutoClean Team"

from .core.converter import SequentialProcessor
from .core.memory_manager import MemoryManager
from .io.eeglab_reader import EEGLABReader
from .io.validators import EEGLABValidator

__all__ = [
    "SequentialProcessor",
    "MemoryManager",
    "EEGLABReader",
    "EEGLABValidator",
]
