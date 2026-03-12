"""
File upload utilities. 

This module abstracts file storage operations, making it easy to swap
local filesystem uploads with cloud storage (S3, GCP, etc.) later.
"""

import os
from pathlib import Path
from uuid import uuid4
from werkzeug.utils import secure_filename


class LocalFileUploader:
    """Local filesystem upload handler."""

    def __init__(self, upload_folder: str, allowed_extensions: set):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions

    def save(self, file_obj, filename: str = None) -> str:
        """
        Save a file to local storage.

        Args:
            file_obj: File object (from request.files)
            filename: Optional filename; if None, generates one from file

        Returns:
            Relative file path (suitable for database storage)

        Raises:
            ValueError: If file has invalid extension
        """
        if not file_obj or file_obj.filename == "":
            raise ValueError("No file provided")

        # Validate extension
        ext = self._get_extension(file_obj.filename)
        if ext not in self.allowed_extensions:
            raise ValueError(f"File type {ext} not allowed")

        # Generate safe filename
        if not filename:
            filename = f"{uuid4().hex}.{ext}"
        else:
            filename = secure_filename(filename)

        # Ensure upload folder exists
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)

        # Save file
        filepath = os.path.join(self.upload_folder, filename)
        file_obj.save(filepath)

        return f"uploads/{filename}"

    def delete(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Relative file path

        Returns:
            True if successful, False if file not found
        """
        full_path = os.path.join(self.upload_folder, file_path.replace("uploads/", ""))
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    def _get_extension(self, filename: str) -> str:
        """Extract file extension (lowercase, without dot)."""
        if "." not in filename:
            return ""
        return filename.rsplit(".", 1)[1].lower()


def get_uploader(upload_folder: str, allowed_extensions: set):
    """
    Factory function to get the configured uploader.
    
    Currently returns LocalFileUploader.
    Can be extended to return S3Uploader, GCPUploader, etc. based on env config.
    
    Args:
        upload_folder: Path to upload directory
        allowed_extensions: Set of allowed file extensions (without dot)
    
    Returns:
        Uploader instance (LocalFileUploader or cloud equivalent)
    """
    # Future: read from config to decide which uploader to use
    # e.g. STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")
    # if STORAGE_TYPE == "s3":
    #     return S3Uploader(...)
    # if STORAGE_TYPE == "gcp":
    #     return GCPUploader(...)
    # return LocalFileUploader(...)
    
    return LocalFileUploader(upload_folder, allowed_extensions)
