"""Architecture checks for the unified application baseline."""

from __future__ import annotations

import ast
from pathlib import Path
import tomllib

from nfs_scanner import __version__
from nfs_scanner.application import ApplicationContext, create_application_context
from nfs_scanner.core import DeviceManager, ScanManager
from nfs_scanner.version import APP_VERSION


def test_application_layer_does_not_import_ui_modules() -> None:
    application_dir = Path(__file__).parents[1] / "nfs_scanner" / "application"
    imported_modules: list[str] = []

    for source_path in application_dir.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)

    assert not [name for name in imported_modules if name.startswith("nfs_scanner.ui")]


def test_application_context_uses_proven_manager_interfaces() -> None:
    context = create_application_context()

    assert isinstance(context, ApplicationContext)
    assert isinstance(context.device_manager, DeviceManager)
    assert isinstance(context.scan_manager, ScanManager)


def test_only_one_ui_implementation_exists() -> None:
    project_root = Path(__file__).parents[1]
    app_source = (project_root / "nfs_scanner" / "app.py").read_text(encoding="utf-8")

    assert not (project_root / "nfs_scanner" / "ui" / "commercial").exists()
    assert "MainWindow()" in app_source
    assert "NFS_SCANNER_UI" not in app_source
    assert "create_commercial_shell" not in app_source


def test_package_metadata_uses_runtime_version_as_single_source() -> None:
    project_root = Path(__file__).parents[1]
    pyproject = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))

    assert __version__ == APP_VERSION
    assert "version" in pyproject["project"]["dynamic"]
    assert pyproject["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "nfs_scanner.version.APP_VERSION"
    }


def test_requirements_match_project_runtime_dependencies() -> None:
    project_root = Path(__file__).parents[1]
    pyproject = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    requirement_lines = {
        line.strip()
        for line in (project_root / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert requirement_lines == set(pyproject["project"]["dependencies"])
