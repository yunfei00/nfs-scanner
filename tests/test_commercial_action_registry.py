"""Tests for Commercial V1 action registry."""

from __future__ import annotations

import os
import unittest

from nfs_scanner.ui.commercial.actions import CommercialActionRegistry


class CommercialActionRegistryTestCase(unittest.TestCase):
    def test_required_action_ids_defined(self) -> None:
        self.assertGreaterEqual(len(CommercialActionRegistry.REQUIRED_ACTION_IDS), 50)

    def test_registry_validate_empty(self) -> None:
        registry = CommercialActionRegistry()
        result = registry.validate()
        self.assertFalse(result["all_actions_have_handlers"])
        self.assertEqual(len(result["missing_required"]), len(CommercialActionRegistry.REQUIRED_ACTION_IDS))

    def test_register_and_trigger(self) -> None:
        registry = CommercialActionRegistry()
        triggered: list[str] = []

        def handler() -> None:
            triggered.append("ok")

        registry.register_simple("demo.test", "Test", handler)
        self.assertTrue(registry.trigger("demo.test"))
        self.assertEqual(triggered, ["ok"])

    def test_actions_without_handlers(self) -> None:
        from nfs_scanner.ui.commercial.actions import CommercialActionDefinition

        registry = CommercialActionRegistry()
        registry.register(
            CommercialActionDefinition(action_id="demo.b", text="B", handler=None)
        )
        self.assertIn("demo.b", registry.actions_without_handlers())


@unittest.skipIf(os.getenv("NFS_SCANNER_SKIP_GUI_TESTS") == "1", "GUI tests skipped")
class CommercialActionRegistryIntegrationTestCase(unittest.TestCase):
    def test_shell_registry_complete(self) -> None:
        from PySide6.QtWidgets import QApplication

        from nfs_scanner.ui.commercial.entry import create_commercial_shell

        app = QApplication.instance() or QApplication([])
        shell = create_commercial_shell()
        try:
            registry = shell.action_registry
            self.assertIsNotNone(registry)
            result = registry.validate()  # type: ignore[union-attr]
            self.assertTrue(
                result["all_actions_have_handlers"],
                f"missing={result['missing_required']} no_handler={result['actions_without_handlers']}",
            )
        finally:
            shell.close()
            app.processEvents()


if __name__ == "__main__":
    unittest.main()
