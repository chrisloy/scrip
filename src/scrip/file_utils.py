"""File utility functions for scrip."""

from pathlib import Path


def is_binary(file_path: Path) -> bool:
    """Check if a file is likely binary based on reading a chunk."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)  # Read the first 1KB
            # Simple heuristic: If it contains a null byte, treat as binary
            # More sophisticated checks could be added (e.g., checking proportion of non-printable chars)
            return b'\x00' in chunk
    except Exception:
        # If we can't read it, maybe treat it as binary or error out?
        # For now, let's assume it's not binary if we can't read it, might be permissions.
        return False
