"""
Custom exception classes for DocGenius application.
"""


class DocGeniusException(Exception):
    """Base exception class for DocGenius application."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class FileProcessingException(DocGeniusException):
    """Exception raised when file processing fails."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)


class AIServiceException(DocGeniusException):
    """Exception raised when AI service encounters an error."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)


class ValidationException(DocGeniusException):
    """Exception raised when input validation fails."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)


class ConversationException(DocGeniusException):
    """Exception raised when conversation operations fail."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)
