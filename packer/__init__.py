"""Compatibility package for the legacy root-level module layout.

The original application imports modules as ``packer.<module>`` while the
source files are kept in the repository root. Extending the package search
path lets Python resolve those modules without moving data files or changing
the legacy source layout.
"""

from pathlib import Path

_repository_root = str(Path(__file__).resolve().parent.parent)
if _repository_root not in __path__:
    __path__.append(_repository_root)
