"""Parser utilities for scrip file format."""

from typing import Tuple, Optional
from .constants import (
    BEGIN_FILE_PREFIX, BEGIN_FILE_SUFFIX,
    END_FILE_PREFIX, END_FILE_SUFFIX,
    EMPTY_DIR_PREFIX, EMPTY_DIR_SUFFIX,
    BINARY_MARKER
)


def parse_begin_file_line(line: str) -> Tuple[Optional[str], bool]:
    """Parses a BEGIN FILE line. Returns (path_str, is_binary) or (None, False)."""
    if line.startswith(BEGIN_FILE_PREFIX) and line.endswith(BEGIN_FILE_SUFFIX):
        path_part = line[len(BEGIN_FILE_PREFIX):-len(BEGIN_FILE_SUFFIX)]
        is_binary = path_part.endswith(BINARY_MARKER)
        if is_binary:
            path_str = path_part[:-len(BINARY_MARKER)]
            return path_str, True
        else:
            path_str = path_part
            return path_str, False
    return None, False


def parse_empty_dir_line(line: str) -> Optional[str]:
    """Parses an EMPTY DIR line. Returns path_str or None."""
    if line.startswith(EMPTY_DIR_PREFIX) and line.endswith(EMPTY_DIR_SUFFIX):
        path_str = line[len(EMPTY_DIR_PREFIX):-len(EMPTY_DIR_SUFFIX)]
        return path_str
    return None


def parse_end_file_line(line: str) -> Tuple[Optional[str], bool]:
    """Parses an END FILE line. Returns (path_str, is_binary) or (None, False)."""
    if line.startswith(END_FILE_PREFIX) and line.endswith(END_FILE_SUFFIX):
        path_part = line[len(END_FILE_PREFIX):-len(END_FILE_SUFFIX)]
        is_binary = path_part.endswith(BINARY_MARKER)
        if is_binary:
            path_str = path_part[:-len(BINARY_MARKER)]
            return path_str, True
        else:
            path_str = path_part
            return path_str, False
    return None, False
