"""Core logic for scrip (flattening) and unscrip (restoring).

This module now re-exports functionality from dedicated modules for improved modularity.
"""

# Re-export the public API for backward compatibility
from .constants import (
    BEGIN_FILE_PREFIX, BEGIN_FILE_SUFFIX,
    END_FILE_PREFIX, END_FILE_SUFFIX,
    EMPTY_DIR_PREFIX, EMPTY_DIR_SUFFIX,
    BINARY_MARKER
)
from .file_utils import is_binary
from .flattener import flatten_directory, ScripFlattener
from .parser import parse_begin_file_line as _parse_begin_file_line
from .parser import parse_empty_dir_line as _parse_empty_dir_line
from .parser import parse_end_file_line as _parse_end_file_line
from .restorer import restore_directory, ScripRestorer

# Re-export these with their previous names for backward compatibility
def _parse_begin_file_line(line):
    return _parse_begin_file_line(line)

def _parse_empty_dir_line(line):
    return _parse_empty_dir_line(line)

def _parse_end_file_line(line):
    return _parse_end_file_line(line) 