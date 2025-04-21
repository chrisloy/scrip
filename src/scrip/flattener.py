"""Directory flattening functionality for scrip."""

import base64
from pathlib import Path

from .constants import (
    BEGIN_FILE_PREFIX, BEGIN_FILE_SUFFIX,
    END_FILE_PREFIX, END_FILE_SUFFIX,
    EMPTY_DIR_PREFIX, EMPTY_DIR_SUFFIX,
    BINARY_MARKER
)
from .file_utils import is_binary


class ScripFlattener:
    """Class for flattening directories into scrip format files."""
    
    def __init__(self):
        """Initialize the flattener."""
        pass
    
    def flatten(self, directory_path: str, output_file: str):
        """Flattens the directory structure into a single text file."""
        root_path = Path(directory_path).resolve()
        if not root_path.is_dir():
            raise ValueError(f"Error: {directory_path} is not a valid directory.")

        with open(output_file, 'w', encoding='utf-8') as outfile:
            self._process_directory(root_path, outfile)
            
        print(f"Successfully flattened '{directory_path}' to '{output_file}'")
    
    def _process_directory(self, root_path: Path, outfile):
        """Process all files and directories within the given root."""
        for item in sorted(root_path.rglob('*')):
            relative_path = item.relative_to(root_path)
            
            if item.is_dir():
                self._process_empty_directory(item, relative_path, outfile)
            elif item.is_file():
                self._process_file(item, relative_path, outfile)
    
    def _process_empty_directory(self, dir_path: Path, relative_path: Path, outfile):
        """Process an empty directory."""
        if not any(dir_path.iterdir()):
            outfile.write(EMPTY_DIR_PREFIX + str(relative_path) + EMPTY_DIR_SUFFIX + '\n')
    
    def _process_file(self, file_path: Path, relative_path: Path, outfile):
        """Process a single file."""
        is_bin = is_binary(file_path)
        marker = BINARY_MARKER if is_bin else ""
        
        # Write begin marker
        outfile.write(BEGIN_FILE_PREFIX + str(relative_path) + marker + BEGIN_FILE_SUFFIX + '\n')
        
        try:
            if is_bin:
                self._write_binary_file(file_path, outfile)
            else:
                self._write_text_file(file_path, outfile)
        except Exception as e:
            print(f"Warning: Could not read file {file_path}. Skipping. Error: {e}")
            outfile.write(f"Error reading file content: {e}\n")
        
        # Write end marker - always on its own line without extra newlines
        outfile.write(END_FILE_PREFIX + str(relative_path) + marker + END_FILE_SUFFIX + '\n')
    
    def _write_binary_file(self, file_path: Path, outfile):
        """Write binary file content as base64 encoded."""
        with open(file_path, 'rb') as infile:
            encoded_content = base64.b64encode(infile.read()).decode('ascii')
            outfile.write(encoded_content + '\n')  # Add newline after binary content
    
    def _write_text_file(self, file_path: Path, outfile):
        """Write text file content, preserving exact content."""
        with open(file_path, 'rb') as infile:  # Open in binary mode to preserve exact bytes
            content = infile.read()
            outfile.write(content.decode('utf-8', errors='ignore'))
            # Always ensure a newline after content, so END marker appears on a new line
            if not content.endswith(b'\n'):
                outfile.write('\n')


def flatten_directory(directory_path: str, output_file: str):
    """Flattens the directory structure into a single text file.
    
    This function maintains backward compatibility with the original API.
    """
    flattener = ScripFlattener()
    flattener.flatten(directory_path, output_file)
