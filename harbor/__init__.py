"""Development import shim for Harbor's src/ package layout.

It allows commands such as `python -m harbor.main` and
`python -m unittest discover -s tests` to run from the repository root
before installing the package in editable mode.
"""

from pathlib import Path

_SRC_PACKAGE_PATH = Path(__file__).resolve().parent.parent / "src" / "harbor"

if _SRC_PACKAGE_PATH.exists():
    __path__.append(str(_SRC_PACKAGE_PATH))
