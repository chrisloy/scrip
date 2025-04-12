"""Core logic for scrip (flattening) and unscrip (restoring)."""

import base64
import os
import stat
from pathlib import Path
from typing import Optional

# --- Constants for Delimiters ---
BEGIN_FILE_PREFIX = "--- BEGIN FILE: "
BEGIN_FILE_SUFFIX = " ---"
END_FILE_PREFIX = "--- END FILE: "
END_FILE_SUFFIX = " ---"
EMPTY_DIR_PREFIX = "--- EMPTY DIR: "
EMPTY_DIR_SUFFIX = " ---"
BINARY_MARKER = " (BINARY - BASE64 ENCODED)"


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

def flatten_directory(directory_path: str, output_file: str):
    """Flattens the directory structure into a single text file."""
    root_path = Path(directory_path).resolve()
    if not root_path.is_dir():
        raise ValueError(f"Error: {directory_path} is not a valid directory.")

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for item in sorted(root_path.rglob('*')):
            relative_path = item.relative_to(root_path)
            if item.is_dir():
                # Check if directory is empty
                if not any(item.iterdir()):
                    outfile.write(EMPTY_DIR_PREFIX + str(relative_path) + EMPTY_DIR_SUFFIX + '\n')
            elif item.is_file():
                is_bin = is_binary(item)
                marker = BINARY_MARKER if is_bin else ""
                outfile.write(BEGIN_FILE_PREFIX + str(relative_path) + marker + BEGIN_FILE_SUFFIX + '\n')
                try:
                    if is_bin:
                        with open(item, 'rb') as infile:
                            encoded_content = base64.b64encode(infile.read()).decode('ascii')
                            outfile.write(encoded_content + '\n')
                    else:
                        with open(item, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read()) # Write content without adding extra newline
                            # Check if file ends with newline, add one if not to separate content from end marker
                            if infile.tell() > 0: # Check if file was not empty
                                infile.seek(infile.tell() - 1)
                                if infile.read(1) != '\n':
                                     outfile.write('\n')
                except Exception as e:
                    print(f"Warning: Could not read file {item}. Skipping. Error: {e}")
                    outfile.write(f"Error reading file content: {e}\n") # Indicate error in output

                outfile.write(END_FILE_PREFIX + str(relative_path) + marker + END_FILE_SUFFIX + '\n')

    print(f"Successfully flattened '{directory_path}' to '{output_file}'")

def _parse_begin_file_line(line: str) -> tuple[Optional[str], bool]:
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

def _parse_empty_dir_line(line: str) -> Optional[str]:
    """Parses an EMPTY DIR line. Returns path_str or None."""
    if line.startswith(EMPTY_DIR_PREFIX) and line.endswith(EMPTY_DIR_SUFFIX):
        path_str = line[len(EMPTY_DIR_PREFIX):-len(EMPTY_DIR_SUFFIX)]
        return path_str
    return None

def _parse_end_file_line(line: str) -> tuple[Optional[str], bool]:
    """Parses an END FILE line. Returns (path_str, is_binary) or (None, False)."""
    # Similar logic to begin, checking the END prefix/suffix
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

def restore_directory(input_file: str, output_directory: str):
    """Restores the directory structure from a scrip file."""
    input_path = Path(input_file).resolve()
    output_root = Path(output_directory).resolve()

    if not input_path.is_file():
        raise ValueError(f"Error: {input_file} is not a valid file.")

    # --- Phase 1: Pre-check for conflicts ---
    conflicts = []
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            for line in infile:
                line_rstrip = line.rstrip('\n')

                path_str, _ = _parse_begin_file_line(line_rstrip)
                if path_str is not None:
                    target_path = output_root / path_str
                    if target_path.exists():
                        conflicts.append(target_path)
                    continue # Move to next line

                path_str = _parse_empty_dir_line(line_rstrip)
                if path_str is not None:
                    target_path = output_root / path_str
                    if target_path.exists():
                        conflicts.append(target_path)
                    continue # Move to next line

                # END FILE lines and content lines ignored in phase 1

    except Exception as e:
        raise IOError(f"Error reading or parsing input file {input_path}: {e}") from e

    if conflicts:
        conflict_list_str = "\n".join([str(p.relative_to(output_root)) for p in conflicts])
        raise FileExistsError(f"Error: The following paths already exist in {output_root}. Please remove them or choose a different output directory:\n{conflict_list_str}")

    # --- Phase 2: Create directories and files ---
    output_root.mkdir(parents=True, exist_ok=True) # Create root if needed

    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            current_file_handle = None
            current_file_path = None
            current_file_is_binary = False
            expected_end_path = None # Store the path expected by the END marker

            for line_num, line in enumerate(infile, 1):
                line_rstrip = line.rstrip('\n')

                # Try parsing delimiters first
                begin_path, is_binary_next = _parse_begin_file_line(line_rstrip)
                if begin_path is not None:
                    if current_file_handle:
                        print(f"Warning (L{line_num}): Found new BEGIN FILE marker before END FILE for {current_file_path}. Closing previous.")
                        current_file_handle.close()

                    current_file_is_binary = is_binary_next
                    current_file_path = output_root / begin_path
                    expected_end_path = begin_path # Store for matching END marker
                    mode = 'wb' if current_file_is_binary else 'w'

                    # Ensure parent dir exists
                    try:
                        current_file_path.parent.mkdir(parents=True, exist_ok=True)
                        current_file_handle = open(current_file_path, mode, encoding=(None if current_file_is_binary else 'utf-8'))
                    except IOError as e:
                        print(f"Error (L{line_num}): Could not open file for writing: {current_file_path}. Error: {e}")
                        raise # Abort on file open error
                    continue # Move to next line

                empty_dir_path = _parse_empty_dir_line(line_rstrip)
                if empty_dir_path is not None:
                    if current_file_handle:
                        print(f"Warning (L{line_num}): Found EMPTY DIR marker while processing file {current_file_path}. Closing file.")
                        current_file_handle.close()
                        # Reset file state
                        current_file_handle = None
                        current_file_is_binary = False
                        current_file_path = None
                        expected_end_path = None

                    target_path = output_root / empty_dir_path
                    target_path.mkdir(parents=True, exist_ok=True) # Create the empty directory
                    continue # Move to next line

                end_path, end_is_binary = _parse_end_file_line(line_rstrip)
                if end_path is not None:
                    if current_file_handle:
                         # Optional: Verify end marker details match begin marker details
                         if end_path != expected_end_path or end_is_binary != current_file_is_binary:
                             print(f"Warning (L{line_num}): END FILE marker mismatch for {current_file_path}. Expected path='{expected_end_path}', binary={current_file_is_binary}. Got path='{end_path}', binary={end_is_binary}.")
                         current_file_handle.close()
                         # Reset file state
                         current_file_handle = None
                         current_file_is_binary = False
                         current_file_path = None
                         expected_end_path = None
                    else:
                         print(f"Warning (L{line_num}): Found END FILE marker but no file is currently open: {line_rstrip}")
                    continue # Move to next line

                # --- Process Content Line --- #
                if current_file_handle:
                    try:
                        if current_file_is_binary:
                            # Base64 content line - decode and write
                            decoded_bytes = base64.b64decode(line_rstrip)
                            current_file_handle.write(decoded_bytes)
                        else:
                            # Text content line - write preserving original line ending
                            current_file_handle.write(line)
                    except base64.binascii.Error as decode_error:
                        print(f"Warning (L{line_num}): Could not decode base64 content for {current_file_path}. Line: '{line_rstrip[:50]}...'. Error: {decode_error}")
                        # Decide: skip line, write placeholder, or raise error? Skipping line for now.
                    except IOError as e:
                        print(f"Error (L{line_num}): Could not write to file {current_file_path}. Error: {e}")
                        current_file_handle.close() # Close on error
                        raise # Abort on write error
                    except Exception as e:
                         print(f"Error (L{line_num}): Unexpected error writing content for {current_file_path}. Error: {e}")
                         current_file_handle.close()
                         raise
                # else: Line is not a delimiter and no file is open - ignore (e.g., blank lines between files)

            # End of file processing
            if current_file_handle:
                print(f"Warning: Input file ended unexpectedly while processing file {current_file_path}. Closing file.")
                current_file_handle.close()

    except Exception as e:
        # Consider cleanup of partially created files/dirs?
        raise IOError(f"Error writing files during restoration to {output_root}: {e}") from e

    print(f"Successfully restored '{input_path.name}' to '{output_directory}'") 