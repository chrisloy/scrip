"""Command-line interface for scrip and unscrip."""

import argparse
import os
import sys
from pathlib import Path
from . import core # Use relative import

def scrip_cli():
    """Handles the 'scrip' command-line invocation."""
    parser = argparse.ArgumentParser(description="Flatten a directory structure into a single text file.")
    parser.add_argument("directory", help="The directory to flatten.")
    parser.add_argument("-o", "--output", help="Optional output file name (defaults to <directory_name>.scrip).", default=None)
    # Add other options later (e.g., --exclude, --binary-handling)

    args = parser.parse_args()

    input_dir = args.directory
    output_file = args.output

    if not Path(input_dir).is_dir():
        print(f"Error: Input path '{input_dir}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    if output_file is None:
        dir_name = Path(input_dir).resolve().name
        output_file = f"{dir_name}.scrip"
    else:
        # Ensure output file has .scrip extension?
        # For now, allow any extension, but maybe enforce later.
        pass

    try:
        core.flatten_directory(input_dir, output_file)
    except Exception as e:
        print(f"Error during flattening: {e}", file=sys.stderr)
        sys.exit(1)

def unscrip_cli():
    """Handles the 'unscrip' command-line invocation."""
    parser = argparse.ArgumentParser(description="Restore a directory structure from a scrip file.")
    parser.add_argument("file", help="The .scrip file to restore.")
    parser.add_argument("-o", "--output", help="Optional output directory name (defaults to <filename_without_extension>).", default=None)
    # Add other options later (e.g., --overwrite)

    args = parser.parse_args()

    input_file = args.file
    output_dir = args.output

    if not Path(input_file).is_file():
        print(f"Error: Input file '{input_file}' is not a valid file.", file=sys.stderr)
        sys.exit(1)

    if output_dir is None:
        file_stem = Path(input_file).stem # Name without extension
        output_dir = file_stem

    # Note: core.restore_directory needs to create the output_dir if it doesn't exist
    # It also needs to handle the conflict checking we discussed.
    try:
        # We will pass the target directory directly to the core function
        core.restore_directory(input_file, output_dir)
    except FileExistsError as e: # Catch the specific conflict error
        print(f"Error: {e}", file=sys.stderr)
        print("Restoration aborted due to existing files/directories.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during restoration: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    # This allows running the module directly, but entry points are preferred
    # Figure out which command was intended based on how it was run?
    # This part might not be strictly necessary if using entry points.
    print("Please run using the 'scrip' or 'unscrip' commands.")
    sys.exit(1) 