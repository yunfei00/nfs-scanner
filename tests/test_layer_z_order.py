"""Tests for commercial realtime layer z-order."""

from __future__ import annotations

import sys
import unittest

from PySide6.QtWidgets import QApplication, QGraphicsScene

try:
    from nfs_scanner.ui.commercial.graphics.layer_manager import LayerManager
    from nfs_scanner.ui.commercial.graphics.layers import LayerKind
except ImportError as import_error:  # pragma: no cover - environment dependent
    LayerManager = None  # type: ignore[assignment,misc]
    LayerKind = None  # type: ignore[assignment,misc]
    _IMPORT_ERROR = import_error
else:
    _IMPORT_ERROR = None


@unittest.skipIf(_IMPORT_ERROR is not None, f"UI dependencies unavailable: {_IMPORT_ERROR}")
class LayerZOrderTestCase(unittest.TestCase):
    """Verify layer items receive stable z-values after mock content is built."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_mock_layers_keep_expected_z_values(self) -> None:
        scene = QGraphicsScene()
        manager = LayerManager(scene)

        manager.ensure_layer(LayerKind.PHOTO).build_mock()
        manager.ensure_layer(LayerKind.HEATMAP).build_mock()
        manager.ensure_layer(LayerKind.PATH).build_mock()
        manager.ensure_layer(LayerKind.MARKER).build_mock()

        self.assertTrue(manager.verify_layer_z_values())


if __name__ == "__main__":
    unittest.main()
