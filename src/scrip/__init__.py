# src/scrip/__init__.py

"""Scrip - a tool for flattening and restoring directory structures."""

from .flattener import flatten_directory, ScripFlattener
from .restorer import restore_directory, ScripRestorer

__all__ = [
    'flatten_directory',
    'restore_directory',
    'ScripFlattener',
    'ScripRestorer',
]
