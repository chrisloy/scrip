"""Directory restoration functionality for scrip."""

import base64
from pathlib import Path

from .parser import parse_begin_file_line, parse_empty_dir_line, parse_end_file_line


class ScripRestorer:
    """Class for restoring directories from scrip format files."""
    
    def __init__(self):
        """Initialize the restorer."""
        pass
    
    def restore(self, input_file: str, output_directory: str):
        """Restores the directory structure from a scrip file."""
        input_path = Path(input_file).resolve()
        output_root = Path(output_directory).resolve()

        if not input_path.is_file():
            raise ValueError(f"Error: {input_file} is not a valid file.")

        # First check for conflicts
        conflicts = self._check_conflicts(input_path, output_root)
        if conflicts:
            self._handle_conflicts(conflicts, output_root)
            
        # Then perform the actual restoration
        self._perform_restoration(input_path, output_root)
            
        print(f"Successfully restored '{input_path.name}' to '{output_directory}'")
    
    def _check_conflicts(self, input_path: Path, output_root: Path):
        """Check for any conflicts with existing files or directories."""
        conflicts = []
        
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                for line in infile:
                    line_rstrip = line.rstrip('\n')

                    path_str, _ = parse_begin_file_line(line_rstrip)
                    if path_str is not None:
                        target_path = output_root / path_str
                        if target_path.exists():
                            conflicts.append(target_path)
                        continue  # Move to next line

                    path_str = parse_empty_dir_line(line_rstrip)
                    if path_str is not None:
                        target_path = output_root / path_str
                        if target_path.exists():
                            conflicts.append(target_path)
                        continue  # Move to next line
        except Exception as e:
            raise IOError(f"Error reading or parsing input file {input_path}: {e}") from e
            
        return conflicts
    
    def _handle_conflicts(self, conflicts, output_root: Path):
        """Handle any conflicts found during conflict checking."""
        conflict_list_str = "\n".join([str(p.relative_to(output_root)) for p in conflicts])
        raise FileExistsError(
            f"Error: The following paths already exist in {output_root}. "
            f"Please remove them or choose a different output directory:\n{conflict_list_str}"
        )
    
    def _perform_restoration(self, input_path: Path, output_root: Path):
        """Perform the actual restoration process."""
        output_root.mkdir(parents=True, exist_ok=True)  # Create root if needed
        
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                self._process_file_contents(infile, output_root)
        except Exception as e:
            # Consider cleanup of partially created files/dirs?
            raise IOError(f"Error writing files during restoration to {output_root}: {e}") from e
    
    def _process_file_contents(self, infile, output_root: Path):
        """Process the contents of the input file."""
        current_file_handle = None
        current_file_path = None
        current_file_is_binary = False
        expected_end_path = None  # Store the path expected by the END marker
        content_buffer = []  # Buffer for collecting content lines
        
        for line_num, line in enumerate(infile, 1):
            line_rstrip = line.rstrip('\n')
            
            # Try parsing delimiters first
            begin_path, is_binary_next = parse_begin_file_line(line_rstrip)
            if begin_path is not None:
                # Handle any previously open file
                if current_file_handle:
                    self._write_buffered_content(current_file_handle, content_buffer, current_file_is_binary)
                    current_file_handle.close()
                
                # Start a new file
                current_file_handle = self._handle_begin_file(
                    begin_path, is_binary_next, None, None, output_root, line_num
                )
                current_file_is_binary = is_binary_next
                current_file_path = output_root / begin_path
                expected_end_path = begin_path  # Store for matching END marker
                content_buffer = []  # Clear the buffer
                continue  # Move to next line
                
            empty_dir_path = parse_empty_dir_line(line_rstrip)
            if empty_dir_path is not None:
                # Handle any previously open file
                if current_file_handle:
                    self._write_buffered_content(current_file_handle, content_buffer, current_file_is_binary)
                    current_file_handle.close()
                
                # Process empty directory
                self._handle_empty_dir(empty_dir_path, None, None, output_root, line_num)
                
                # Reset file state
                current_file_handle = None
                current_file_is_binary = False
                current_file_path = None
                expected_end_path = None
                content_buffer = []  # Clear the buffer
                continue  # Move to next line
                
            end_path, end_is_binary = parse_end_file_line(line_rstrip)
            if end_path is not None:
                # Handle end of file - write any buffered content
                if current_file_handle:
                    self._write_buffered_content(current_file_handle, content_buffer, current_file_is_binary)
                    
                    # Close file and verify end marker
                    self._handle_end_file(
                        end_path, end_is_binary, current_file_handle, 
                        current_file_path, expected_end_path, 
                        current_file_is_binary, line_num
                    )
                else:
                    print(f"Warning (L{line_num}): Found END FILE marker but no file is currently open: {line_rstrip}")
                
                # Reset file state
                current_file_handle = None
                current_file_is_binary = False
                current_file_path = None
                expected_end_path = None
                content_buffer = []  # Clear the buffer
                continue  # Move to next line
                
            # Process content line - add to buffer
            if current_file_handle:
                content_buffer.append(line)
        
        # End of file processing
        if current_file_handle:
            # Write any remaining buffered content
            self._write_buffered_content(current_file_handle, content_buffer, current_file_is_binary)
            print(f"Warning: Input file ended unexpectedly while processing file {current_file_path}. Closing file.")
            current_file_handle.close()
    
    def _write_buffered_content(self, file_handle, content_buffer, is_binary):
        """Write buffered content to the file."""
        if not content_buffer:
            return
            
        if is_binary:
            # For binary content, decode the base64 string
            try:
                # Remove the ending newline that was added during flattening
                encoded_content = content_buffer[0].rstrip('\n')
                decoded_bytes = base64.b64decode(encoded_content)
                file_handle.write(decoded_bytes)
            except base64.binascii.Error as e:
                print(f"Warning: Could not decode base64 content. Error: {e}")
        else:
            # For text content, we need to handle the newline that might have been
            # added by the flattener to ensure the END marker appears on its own line
            
            # Join all the content lines
            file_content = ''.join(content_buffer)
            
            # If content ends with a newline and original content didn't have one,
            # we need to remove it
            if file_content.endswith('\n'):
                # Check if there's a newline after content - this is likely added by flattener
                # We look at the second-to-last character - if it's also a newline, then the file
                # probably originally ended with a newline
                if len(file_content) >= 2 and file_content[-2] == '\n':
                    # File likely had a trailing newline, keep as is
                    pass
                else:
                    # File likely didn't have a trailing newline, remove the one added by flattener
                    file_content = file_content[:-1]
            
            file_handle.write(file_content)
    
    def _handle_begin_file(self, path_str, is_binary, current_handle, current_path, output_root, line_num):
        """Handle a BEGIN FILE marker."""
        if current_handle:
            print(f"Warning (L{line_num}): Found new BEGIN FILE marker before END FILE for {current_path}. Closing previous.")
            current_handle.close()
            
        target_path = output_root / path_str
        mode = 'wb' if is_binary else 'w'
        
        # Ensure parent dir exists
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            return open(target_path, mode, encoding=(None if is_binary else 'utf-8'))
        except IOError as e:
            print(f"Error (L{line_num}): Could not open file for writing: {target_path}. Error: {e}")
            raise  # Abort on file open error
    
    def _handle_empty_dir(self, path_str, current_handle, current_path, output_root, line_num):
        """Handle an EMPTY DIR marker."""
        if current_handle:
            print(f"Warning (L{line_num}): Found EMPTY DIR marker while processing file {current_path}. Closing file.")
            current_handle.close()
            
        target_path = output_root / path_str
        target_path.mkdir(parents=True, exist_ok=True)  # Create the empty directory
        return None
    
    def _handle_end_file(self, path_str, is_binary, current_handle, current_path, 
                         expected_path, current_is_binary, line_num):
        """Handle an END FILE marker."""
        if current_handle:
            # Optional: Verify end marker details match begin marker details
            if path_str != expected_path or is_binary != current_is_binary:
                print(
                    f"Warning (L{line_num}): END FILE marker mismatch for {current_path}. "
                    f"Expected path='{expected_path}', binary={current_is_binary}. "
                    f"Got path='{path_str}', binary={is_binary}."
                )
            current_handle.close()
            return None
        else:
            print(f"Warning (L{line_num}): Found END FILE marker but no file is currently open: {path_str}")
            return None
    
    def _process_content_line(self, line, line_rstrip, file_handle, is_binary, file_path, line_num):
        """Process a content line (legacy method, no longer used)."""
        try:
            if is_binary:
                # Base64 content line - decode and write
                decoded_bytes = base64.b64decode(line_rstrip)
                file_handle.write(decoded_bytes)
            else:
                # Text content line - write preserving original line ending
                file_handle.write(line)
        except base64.binascii.Error as decode_error:
            print(
                f"Warning (L{line_num}): Could not decode base64 content for {file_path}. "
                f"Line: '{line_rstrip[:50]}...'. Error: {decode_error}"
            )
            # Decide: skip line, write placeholder, or raise error? Skipping line for now.
        except IOError as e:
            print(f"Error (L{line_num}): Could not write to file {file_path}. Error: {e}")
            file_handle.close()  # Close on error
            raise  # Abort on write error
        except Exception as e:
            print(f"Error (L{line_num}): Unexpected error writing content for {file_path}. Error: {e}")
            file_handle.close()
            raise


def restore_directory(input_file: str, output_directory: str):
    """Restores the directory structure from a scrip file.
    
    This function maintains backward compatibility with the original API.
    """
    restorer = ScripRestorer()
    restorer.restore(input_file, output_directory)
