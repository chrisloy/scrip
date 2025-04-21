"""Tests for the core scrip/unscrip logic."""

import pytest
import os
import shutil
import base64 # Keep for potential future use, but not used now
from pathlib import Path
from src.scrip import core

# --- Constants for easier assertion ---
BFP = core.BEGIN_FILE_PREFIX
BFS = core.BEGIN_FILE_SUFFIX
EFP = core.END_FILE_PREFIX
EFS = core.END_FILE_SUFFIX
EDP = core.EMPTY_DIR_PREFIX
EDS = core.EMPTY_DIR_SUFFIX
BM = core.BINARY_MARKER

# --- Helper Functions for Tests ---

def create_test_files(base_dir: Path, structure: dict):
    """Recursively creates files and directories based on a dict structure."""
    for name, content in structure.items():
        path = base_dir / name
        if isinstance(content, dict):
            path.mkdir()
            create_test_files(path, content)
        elif isinstance(content, str):
            path.write_text(content, encoding='utf-8')
        elif content is None: # Represents an empty directory
             path.mkdir()
        # Add bytes support later if needed

def verify_restored_files(base_dir: Path, structure: dict):
    """Recursively verifies files and directories match the expected structure."""
    for name, content in structure.items():
        path = base_dir / name
        if isinstance(content, dict):
            assert path.is_dir()
            verify_restored_files(path, content)
        elif isinstance(content, str):
            assert path.is_file()
            # With the new implementation, we preserve file content exactly
            # without adding trailing newlines, so the comparison should be exact
            assert path.read_text('utf-8') == content
        elif content is None:
            assert path.is_dir()
            assert not any(path.iterdir()), f"Directory not empty: {path}"

# --- Fixtures ---

@pytest.fixture
def source_dir(tmp_path):
    """Provides the source directory path for tests."""
    return tmp_path / "source"

@pytest.fixture
def scrip_file(tmp_path):
    """Provides the path for the generated scrip file."""
    return tmp_path / "output.scrip"

@pytest.fixture
def restore_dir(tmp_path):
    """Provides the path for the restore output directory."""
    return tmp_path / "restore_target"


# --- Test Cases: Flattening (Text Only) ---

def test_flatten_empty_directory(source_dir, scrip_file):
    """Flatten an empty directory."""
    source_dir.mkdir()
    core.flatten_directory(str(source_dir), str(scrip_file))
    assert scrip_file.read_text('utf-8') == ""

def test_flatten_single_text_file(source_dir, scrip_file):
    """Flatten a directory with one text file."""
    structure = {"file1.txt": "Hello\nWorld"}
    source_dir.mkdir() # FIX: Create the source directory first
    create_test_files(source_dir, structure)
    core.flatten_directory(str(source_dir), str(scrip_file))
    content = scrip_file.read_text('utf-8')
    # FIX: Ensure expected content ends with newline
    expected = (
        f"{BFP}file1.txt{BFS}\n"
        f"Hello\nWorld\n" # Content from structure, guaranteed newline by flatten
        f"{EFP}file1.txt{EFS}\n"
    )
    assert content == expected

def test_flatten_multiple_text_files(source_dir, scrip_file):
    """Flatten a directory with multiple text files."""
    structure = {
        "file1.txt": "Content 1", # No trailing newline here
        "file2.log": "Log line\nAnother log line" # Ends with newline
    }
    source_dir.mkdir() # FIX: Create the source directory first
    create_test_files(source_dir, structure)
    core.flatten_directory(str(source_dir), str(scrip_file))
    content = scrip_file.read_text('utf-8')
    # FIX: Ensure expected content ends with newline
    expected = (
        f"{BFP}file1.txt{BFS}\n"
        f"Content 1\n" # Flatten adds newline
        f"{EFP}file1.txt{EFS}\n"
        f"{BFP}file2.log{BFS}\n"
        f"Log line\nAnother log line\n" # Flatten keeps existing newline
        f"{EFP}file2.log{EFS}\n"
    )
    assert content == expected

def test_flatten_single_subdir_file(source_dir, scrip_file):
    """Flatten a directory with one file in a subdirectory."""
    structure = {"subdir": {"nested.txt": "Nested content."}}
    source_dir.mkdir() # FIX: Create the source directory first
    create_test_files(source_dir, structure)
    core.flatten_directory(str(source_dir), str(scrip_file))
    content = scrip_file.read_text('utf-8')
    expected_path = Path("subdir") / "nested.txt"
    # FIX: Ensure expected content ends with newline
    expected = (
        f"{BFP}{str(expected_path)}{BFS}\n"
        f"Nested content.\n" # Flatten adds newline
        f"{EFP}{str(expected_path)}{EFS}\n"
    )
    assert content == expected

def test_flatten_nested_files_and_empty_dirs(source_dir, scrip_file):
    """Flatten a directory with nested files and empty directories."""
    structure = {
        "file1.txt": "Root file.",
        "a": {
            "file_a.txt": "File in A.",
            "b": {
                "file_b.txt": "File in B."
            },
            "empty_b": None
        },
        "empty_root": None
    }
    source_dir.mkdir() # FIX: Create the source directory first
    create_test_files(source_dir, structure)
    core.flatten_directory(str(source_dir), str(scrip_file))
    content = scrip_file.read_text('utf-8')

    path_file1 = Path("file1.txt")
    path_file_a = Path("a") / "file_a.txt"
    path_file_b = Path("a") / "b" / "file_b.txt"
    path_empty_b = Path("a") / "empty_b"
    path_empty_root = Path("empty_root")

    # FIX: Ensure expected content ends with newline and matches sorted path order
    expected = (
        f"{BFP}{str(path_file_b)}{BFS}\n" # a/b/file_b.txt
        f"File in B.\n"
        f"{EFP}{str(path_file_b)}{EFS}\n"
        f"{EDP}{str(path_empty_b)}{EDS}\n" # a/empty_b
        f"{BFP}{str(path_file_a)}{BFS}\n" # a/file_a.txt
        f"File in A.\n"
        f"{EFP}{str(path_file_a)}{EFS}\n"
        f"{EDP}{str(path_empty_root)}{EDS}\n" # empty_root
        f"{BFP}{str(path_file1)}{BFS}\n" # file1.txt
        f"Root file.\n"
        f"{EFP}{str(path_file1)}{EFS}\n"
    )
    assert content == expected

def test_flatten_nonexistent_input(scrip_file):
    """Test flattening raises error for non-existent input directory."""
    with pytest.raises(ValueError, match="is not a valid directory"):
        core.flatten_directory("non_existent_dir", str(scrip_file))

# --- Test Cases: Restoration (Text Only) ---

def test_restore_empty_scrip(scrip_file, restore_dir):
    """Restore from an empty scrip file (should create empty target dir)."""
    scrip_file.write_text("", encoding='utf-8')
    core.restore_directory(str(scrip_file), str(restore_dir))
    assert restore_dir.is_dir()
    assert not any(restore_dir.iterdir())

def test_restore_single_text_file(scrip_file, restore_dir):
    """Restore a single text file."""
    # Note: Structure content doesn't need explicit trailing newline here,
    # verify_restored_files handles the comparison correctly.
    structure = {"file1.txt": "Hello\nWorld"}
    scrip_content = (
        f"{BFP}file1.txt{BFS}\n"
        f"Hello\nWorld\n" # Content needs newline matching flatten's output
        f"{EFP}file1.txt{EFS}\n"
    )
    scrip_file.write_text(scrip_content, encoding='utf-8')
    core.restore_directory(str(scrip_file), str(restore_dir))
    verify_restored_files(restore_dir, structure)

def test_restore_multiple_text_files(scrip_file, restore_dir):
    """Restore multiple text files."""
    structure = {
        "file1.txt": "Content 1",
        "file2.log": "Log line\nAnother log line"
    }
    scrip_content = (
        f"{BFP}file1.txt{BFS}\n"
        f"Content 1\n" # Needs newline matching flatten
        f"{EFP}file1.txt{EFS}\n"
        f"{BFP}file2.log{BFS}\n"
        f"Log line\nAnother log line\n" # Needs newline matching flatten
        f"{EFP}file2.log{EFS}\n"
    )
    scrip_file.write_text(scrip_content, encoding='utf-8')
    core.restore_directory(str(scrip_file), str(restore_dir))
    verify_restored_files(restore_dir, structure)

def test_restore_single_subdir_file(scrip_file, restore_dir):
    """Restore a single file in a subdirectory."""
    structure = {"subdir": {"nested.txt": "Nested content."}}
    nested_path = Path("subdir") / "nested.txt"
    scrip_content = (
        f"{BFP}{str(nested_path)}{BFS}\n"
        f"Nested content.\n" # Needs newline matching flatten
        f"{EFP}{str(nested_path)}{EFS}\n"
    )
    scrip_file.write_text(scrip_content, encoding='utf-8')
    core.restore_directory(str(scrip_file), str(restore_dir))
    verify_restored_files(restore_dir, structure)

def test_restore_nested_files_and_empty_dirs(scrip_file, restore_dir):
    """Restore nested files and empty directories."""
    structure = {
        "file1.txt": "Root file.",
        "a": {
            "file_a.txt": "File in A.",
            "b": {
                "file_b.txt": "File in B."
            },
            "empty_b": None
        },
        "empty_root": None
    }
    path_file1 = Path("file1.txt")
    path_file_a = Path("a") / "file_a.txt"
    path_file_b = Path("a") / "b" / "file_b.txt"
    path_empty_b = Path("a") / "empty_b"
    path_empty_root = Path("empty_root")
    scrip_content = (
        f"{BFP}{str(path_file_b)}{BFS}\n"
        f"File in B.\n"
        f"{EFP}{str(path_file_b)}{EFS}\n"
        f"{EDP}{str(path_empty_b)}{EDS}\n"
        f"{BFP}{str(path_file_a)}{BFS}\n"
        f"File in A.\n"
        f"{EFP}{str(path_file_a)}{EFS}\n"
        f"{EDP}{str(path_empty_root)}{EDS}\n"
        f"{BFP}{str(path_file1)}{BFS}\n"
        f"Root file.\n"
        f"{EFP}{str(path_file1)}{EFS}\n"
    )
    scrip_file.write_text(scrip_content, encoding='utf-8')
    core.restore_directory(str(scrip_file), str(restore_dir))
    verify_restored_files(restore_dir, structure)

def test_restore_nonexistent_input(restore_dir):
    """Test restoration raises error for non-existent input file."""
    with pytest.raises(ValueError, match="is not a valid file"):
        core.restore_directory("non_existent.scrip", str(restore_dir))

def test_restore_conflict_error(scrip_file, restore_dir):
    """Test restoration raises FileExistsError if text file conflicts exist."""
    # Define structure and create scrip file
    structure = {"file1.txt": "Content"}
    scrip_content = f"{BFP}file1.txt{BFS}\nContent\n{EFP}file1.txt{EFS}\n"
    scrip_file.write_text(scrip_content, encoding='utf-8')

    # Create conflicting file
    restore_dir.mkdir()
    (restore_dir / "file1.txt").write_text("pre-existing")

    with pytest.raises(FileExistsError, match="already exist"):
        core.restore_directory(str(scrip_file), str(restore_dir))
    # Verify pre-existing file was not touched
    assert (restore_dir / "file1.txt").read_text() == "pre-existing"

def test_restore_conflict_error_message(scrip_file, restore_dir):
    """Test the conflict error message lists the correct conflicting text files."""
    structure = {
        "file1.txt": "",
        "a": {"b": {"file2.txt": ""}}, # Nested conflict
        "a": {"c": None} # Empty dir conflict
    }
    path1 = Path("file1.txt")
    path2 = Path("a") / "b" / "file2.txt"
    path3 = Path("a") / "c"
    scrip_content = (
        f"{BFP}{str(path1)}{BFS}\n\n{EFP}{str(path1)}{EFS}\n"
        f"{BFP}{str(path2)}{BFS}\n\n{EFP}{str(path2)}{EFS}\n"
        f"{EDP}{str(path3)}{EDS}\n"
    )
    scrip_file.write_text(scrip_content, encoding='utf-8')

    # Create conflicts
    restore_dir.mkdir()
    (restore_dir / path1).touch()
    (restore_dir / path2).parent.mkdir(parents=True, exist_ok=True)
    (restore_dir / path2).touch()
    (restore_dir / path3).mkdir(parents=True, exist_ok=True)

    with pytest.raises(FileExistsError) as excinfo:
        core.restore_directory(str(scrip_file), str(restore_dir))

    error_msg = str(excinfo.value)
    print(f"Conflict Error: {error_msg}") # Print for debugging
    assert str(path1) in error_msg
    assert str(path2) in error_msg
    assert str(path3) in error_msg

# TODO:
# - Add back binary file tests later.
# - Add tests for file content exactly matching (e.g., handling of final newlines).
# - Add tests for files/dirs with unusual names.
# - Add tests for large files.
# - Add tests for corrupted scrip files.
# - Add tests for permissions (if implemented).

# TODO: Add tests for edge cases:
# - Files/dirs with unusual names (spaces, symbols)? (Pathlib should handle)
# - Very large files?
# - Corrupted scrip file (missing delimiters, bad base64)?
# - Handling of file permissions? (Not currently preserved) 