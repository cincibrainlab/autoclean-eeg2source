"""Custom exceptions for IO operations."""


class EEGLABError(Exception):
    """Base class for EEGLAB-related errors."""
    pass


class FileFormatError(EEGLABError):
    """Raised when file format is invalid."""
    pass


class FileMismatchError(EEGLABError):
    """Raised when .set and .fdt files don't match."""
    pass


class ChannelError(EEGLABError):
    """Raised for channel-related errors."""
    pass


class MontageError(EEGLABError):
    """Raised when montage doesn't match the data."""
    pass


class CorruptedDataError(EEGLABError):
    """Raised when data is corrupted (NaNs, Infs, etc.)."""
    pass


class DataQualityError(EEGLABError):
    """Raised when data quality is poor."""
    pass


class ProcessingError(Exception):
    """Base class for processing errors."""
    pass


class MemoryError(ProcessingError):
    """Raised when memory limits are exceeded."""
    pass


class NumericalError(ProcessingError):
    """Raised for numerical issues during computation."""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass