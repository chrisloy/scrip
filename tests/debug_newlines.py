"""Debug script to trace newline handling in scrip."""

import os
import tempfile
import shutil
import binascii
from pathlib import Path

from scrip import flatten_directory, restore_directory


def hex_dump(content):
    """Show hex representation of content for debugging."""
    return binascii.hexlify(content.encode('utf-8')).decode('ascii')


def debug_flatten_restore():
    """Debug the flattening and restoration process with explicit content tracing."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as source_dir:
        source_path = Path(source_dir)
        
        # Create test files with known content (no trailing newline)
        (source_path / "dir1").mkdir()
        test_content = "File 1 content"
        
        print(f"Original content: '{test_content}'")
        print(f"Original content (hex): {hex_dump(test_content)}")
        
        with open(source_path / "dir1" / "file1.txt", 'w') as f:
            f.write(test_content)  # No trailing newline
            
        # Create a temporary output file and restoration directory
        with tempfile.NamedTemporaryFile(delete=False) as scrip_file:
            scrip_path = scrip_file.name
        
        try:
            with tempfile.TemporaryDirectory() as dest_dir:
                # Flatten the directory
                flatten_directory(source_dir, scrip_path)
                
                # Check flattened file
                print("\nFlattened file content:")
                with open(scrip_path, 'r') as f:
                    flattened_content = f.read()
                    print(flattened_content)
                
                # Restore the directory
                restore_directory(scrip_path, dest_dir)
                
                # Check restored file content
                dest_path = Path(dest_dir)
                with open(dest_path / "dir1" / "file1.txt", 'r') as f:
                    restored_content = f.read()
                
                print(f"\nRestored content: '{restored_content}'")
                print(f"Restored content (hex): {hex_dump(restored_content)}")
                
                # Compare with original
                print(f"\nOriginal == Restored: {test_content == restored_content}")
                if test_content != restored_content:
                    print("Difference:")
                    for i, (c1, c2) in enumerate(zip(test_content, restored_content)):
                        if c1 != c2:
                            print(f"Pos {i}: '{c1}' ({hex_dump(c1)}) != '{c2}' ({hex_dump(c2)})")
                    
                    # If restored is longer
                    if len(restored_content) > len(test_content):
                        extra = restored_content[len(test_content):]
                        print(f"Extra content in restored: '{extra}' (hex: {hex_dump(extra)})")
                    
        finally:
            # Clean up
            if os.path.exists(scrip_path):
                os.unlink(scrip_path)


if __name__ == "__main__":
    debug_flatten_restore() 