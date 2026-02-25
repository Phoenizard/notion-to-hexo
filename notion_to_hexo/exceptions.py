"""
Custom exceptions for Notion to Hexo.

Provides specific exception types for better error handling
and user-friendly diagnostic messages.
"""


class NotionToHexoError(Exception):
    """Base exception for notion-to-hexo."""
    pass


class NotionAPIError(NotionToHexoError):
    """Notion API request failed.

    Common causes:
    - Page not shared with Integration (object_not_found)
    - Invalid token (unauthorized)
    - Rate limiting (rate_limited)
    """
    def __init__(self, message, status_code=None):
        self.status_code = status_code
        super().__init__(message)


class OSSUploadError(NotionToHexoError):
    """Failed to upload image to Aliyun OSS.

    Common causes:
    - Invalid credentials (403)
    - Bucket not found
    - Network issues
    """
    pass


class HexoCommandError(NotionToHexoError):
    """Hexo CLI command failed.

    Common causes:
    - hexo-cli not installed
    - Invalid hexo_root path
    - hexo generate errors
    """
    pass


class ConfigurationError(NotionToHexoError):
    """Configuration is missing or invalid.

    Common causes:
    - config.json not found
    - Missing required fields (notion token, OSS credentials)
    - Invalid file paths
    """
    pass
