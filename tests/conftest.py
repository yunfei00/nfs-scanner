"""Keep automated tests out of operator configuration and measurement folders."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


_runtime_directory = tempfile.TemporaryDirectory(prefix="nfs-scanner-tests-")
_runtime_root = Path(_runtime_directory.name)
for _environment_name, _relative_path in {
    "NFS_SCANNER_CONFIG_DIR": "config",
    "NFS_SCANNER_STATE_DIR": "state",
    "NFS_SCANNER_LOG_DIR": "logs",
    "NFS_SCANNER_DATA_DIR": "data",
}.items():
    os.environ.setdefault(_environment_name, str(_runtime_root / _relative_path))


def pytest_sessionfinish(session: object, exitstatus: int) -> None:
    """Release the isolated runtime directory after all tests finish."""

    del session, exitstatus
    _runtime_directory.cleanup()
