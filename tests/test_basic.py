"""Basic tests for the scrip package."""

import os
import tempfile
import shutil
from pathlib import Path

from scrip import flatten_directory, restore_directory


def test_flatten_and_restore():
    """Test that flattening and then restoring gives the same directory structure."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as source_dir:
        source_path = Path(source_dir)
        
        # Create test files and directories
        (source_path / "dir1").mkdir()
        
        # Create files with explicit content control
        with open(source_path / "dir1" / "file1.txt", 'w') as f:
            f.write("File 1 content")  # No trailing newline
            
        (source_path / "dir2").mkdir()
        with open(source_path / "dir2" / "file2.txt", 'w') as f:
            f.write("File 2 content")  # No trailing newline
            
        (source_path / "emptydir").mkdir()
        
        # Create a temporary output file and restoration directory
        with tempfile.NamedTemporaryFile(delete=False) as scrip_file:
            scrip_path = scrip_file.name
        
        try:
            with tempfile.TemporaryDirectory() as dest_dir:
                # Flatten the directory
                flatten_directory(source_dir, scrip_path)
                
                # Verify scrip file exists
                assert os.path.exists(scrip_path)
                
                # Restore the directory
                restore_directory(scrip_path, dest_dir)
                
                # Verify structure and exact content
                dest_path = Path(dest_dir)
                assert (dest_path / "dir1").is_dir()
                assert (dest_path / "dir1" / "file1.txt").is_file()
                
                with open(dest_path / "dir1" / "file1.txt", 'r') as f:
                    restored_content = f.read()
                assert restored_content == "File 1 content", f"Expected 'File 1 content' but got '{restored_content}'"
                
                assert (dest_path / "dir2").is_dir()
                assert (dest_path / "dir2" / "file2.txt").is_file()
                
                with open(dest_path / "dir2" / "file2.txt", 'r') as f:
                    restored_content = f.read()
                assert restored_content == "File 2 content", f"Expected 'File 2 content' but got '{restored_content}'"
                
                assert (dest_path / "emptydir").is_dir()
                assert not any((dest_path / "emptydir").iterdir())
                
                print("Test completed successfully!")
        finally:
            # Clean up
            if os.path.exists(scrip_path):
                os.unlink(scrip_path)


if __name__ == "__main__":
    test_flatten_and_restore()
