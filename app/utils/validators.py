"""
Input validation utilities for DocGenius application.
"""

import os
import re
from typing import Dict, Any
from werkzeug.datastructures import FileStorage

from app.utils.exceptions import ValidationException


def validate_file(file: FileStorage) -> Dict[str, Any]:
    """
    Validate uploaded file.

    Args:
        file: Uploaded file object

    Returns:
        Dictionary with validation result
    """
    # Check if file is provided
    if not file or not file.filename:
        return {
            'valid': False,
            'error': 'No file provided'
        }

    # Check file extension
    filename = file.filename.lower()
    allowed_extensions = {'.pdf', '.txt', '.docx', '.pptx'}
    file_extension = os.path.splitext(filename)[1]

    if file_extension not in allowed_extensions:
        return {
            'valid': False,
            'error': f'Unsupported file type. Allowed types: {", ".join(allowed_extensions)}'
        }

    # Check file size (approximate check before reading)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    max_size = 16 * 1024 * 1024  # 16MB
    if file_size > max_size:
        return {
            'valid': False,
            'error': f'File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (16MB)'
        }

    # Check filename for security
    if not is_safe_filename(filename):
        return {
            'valid': False,
            'error': 'Invalid filename. Please use only letters, numbers, spaces, hyphens, and underscores.'
        }

    return {
        'valid': True,
        'file_size': file_size,
        'file_extension': file_extension
    }


def validate_question(question: str) -> Dict[str, Any]:
    """
    Validate user question.

    Args:
        question: User's question string

    Returns:
        Dictionary with validation result
    """
    if not question:
        return {
            'valid': False,
            'error': 'Question cannot be empty'
        }

    # Remove extra whitespace
    question = question.strip()

    if len(question) < 3:
        return {
            'valid': False,
            'error': 'Question must be at least 3 characters long'
        }

    if len(question) > 1000:
        return {
            'valid': False,
            'error': 'Question cannot exceed 1000 characters'
        }

    # Check for potentially harmful content
    if contains_harmful_content(question):
        return {
            'valid': False,
            'error': 'Question contains inappropriate content'
        }

    return {
        'valid': True,
        'cleaned_question': question
    }


def validate_user_id(user_id: str) -> bool:
    """
    Validate user ID format.

    Args:
        user_id: User session ID

    Returns:
        True if valid, False otherwise
    """
    if not user_id:
        return False

    # Check if it's a valid UUID format
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )

    return bool(uuid_pattern.match(user_id))


def validate_file_id(file_id: str) -> bool:
    """
    Validate file ID format.

    Args:
        file_id: File identifier

    Returns:
        True if valid, False otherwise
    """
    return validate_user_id(file_id)  # Same UUID format


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe and doesn't contain harmful characters.

    Args:
        filename: Filename to validate

    Returns:
        True if safe, False otherwise
    """
    if not filename:
        return False

    # Remove the path and keep only the filename
    filename = os.path.basename(filename)

    # Check for empty filename after removing path
    if not filename:
        return False

    # Check for dangerous patterns
    dangerous_patterns = [
        r'\.\.', r'/', r'\\', r':', r'\*', r'\?', r'"', r'<', r'>', r'\|'
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            return False

    # Check if filename is too long
    if len(filename) > 255:
        return False

    # Check if filename starts with dot (hidden files)
    if filename.startswith('.'):
        return False

    return True


def contains_harmful_content(text: str) -> bool:
    """
    Basic check for potentially harmful content in user input.

    Args:
        text: Text to check

    Returns:
        True if potentially harmful content is detected
    """
    if not text:
        return False

    text_lower = text.lower()

    # Basic patterns to detect harmful content
    harmful_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'eval\s*\(',  # eval() calls
        r'document\.',  # DOM manipulation
        r'window\.',  # Window object access
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
            return True

    return False


def sanitize_input(text: str, max_length: int = None) -> str:
    """
    Sanitize user input by removing potentially harmful content.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = text.strip()

    # Remove potential HTML/script content
    text = re.sub(r'<[^>]+>', '', text)

    # Remove potential JavaScript
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)

    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def validate_pagination_params(page: int, per_page: int) -> Dict[str, Any]:
    """
    Validate pagination parameters.

    Args:
        page: Page number (1-based)
        per_page: Items per page

    Returns:
        Dictionary with validation result and cleaned values
    """
    errors = []

    # Validate page number
    if page < 1:
        page = 1
    elif page > 1000:  # Reasonable upper limit
        errors.append("Page number too high")
        page = 1000

    # Validate per_page
    if per_page < 1:
        per_page = 10
    elif per_page > 100:  # Reasonable upper limit
        errors.append("Items per page too high (max 100)")
        per_page = 100

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'page': page,
        'per_page': per_page
    }
