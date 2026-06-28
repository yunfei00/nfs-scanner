"""Central action registry for Commercial V1 — all buttons must register here."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

ActionCategory = Literal[
    "project",
    "device",
    "scan",
    "camera",
    "region",
    "view",
    "data",
    "report",
    "settings",
    "help",
    "demo",
]


@dataclass
class CommercialActionDefinition:
    """One registered UI action with handler and state rules."""

    action_id: str
    text: str
    tooltip: str = ""
    shortcut: str = ""
    category: ActionCategory = "demo"
    handler: Callable[[], None] | None = None
    enabled_rule: Callable[[], bool] | None = None
    checked_rule: Callable[[], bool] | None = None
    ui_bindings: list[str] = field(default_factory=list)

    def has_handler(self) -> bool:
        return self.handler is not None and callable(self.handler)

    def is_enabled(self) -> bool:
        if self.enabled_rule is None:
            return self.has_handler()
        return bool(self.enabled_rule())

    def is_checked(self) -> bool:
        if self.checked_rule is None:
            return False
        return bool(self.checked_rule())

    def trigger(self) -> bool:
        if not self.has_handler():
            return False
        self.handler()  # type: ignore[misc]
        return True


class CommercialActionRegistry:
    """Registry enumerating every commercial UI action for QA and wiring."""

    REQUIRED_ACTION_IDS: tuple[str, ...] = (
        "project.new",
        "project.open",
        "project.save",
        "project.save_as",
        "project.recent",
        "project.close",
        "device.connect_all",
        "device.disconnect_all",
        "device.refresh_all",
        "device.open_center",
        "device.configure",
        "device.test_connection",
        "scan.start",
        "scan.pause",
        "scan.resume",
        "scan.stop",
        "scan.reset",
        "scan.apply_config",
        "scan.preview_path",
        "camera.capture",
        "region.align",
        "region.clear",
        "region.select",
        "region.box_select",
        "region.polygon_select",
        "view.fit",
        "view.reset",
        "view.pan",
        "view.zoom",
        "view.select",
        "view.undo",
        "view.redo",
        "view.annotate",
        "view.grid_toggle",
        "view.path_toggle",
        "view.measure",
        "view.lut_change",
        "view.opacity_change",
        "data.open_view",
        "data.export_json",
        "data.export_csv",
        "data.export_table",
        "data.clear_history",
        "report.open_center",
        "report.preview",
        "report.export_md",
        "report.export_html",
        "report.export_png",
        "report.export_pdf_placeholder",
        "settings.display",
        "settings.instrument",
        "settings.apply_template",
        "settings.save_device_config",
        "help.open",
        "help.shortcuts",
        "help.self_check",
        "help.about",
        "demo.reset",
    )

    def __init__(self) -> None:
        self._actions: dict[str, CommercialActionDefinition] = {}

    def register(self, definition: CommercialActionDefinition) -> None:
        self._actions[definition.action_id] = definition

    def register_simple(
        self,
        action_id: str,
        text: str,
        handler: Callable[[], None],
        *,
        tooltip: str = "",
        shortcut: str = "",
        category: ActionCategory = "demo",
        enabled_rule: Callable[[], bool] | None = None,
        checked_rule: Callable[[], bool] | None = None,
    ) -> None:
        self.register(
            CommercialActionDefinition(
                action_id=action_id,
                text=text,
                tooltip=tooltip or text,
                shortcut=shortcut,
                category=category,
                handler=handler,
                enabled_rule=enabled_rule,
                checked_rule=checked_rule,
            )
        )

    def get(self, action_id: str) -> CommercialActionDefinition | None:
        return self._actions.get(action_id)

    def trigger(self, action_id: str) -> bool:
        action = self._actions.get(action_id)
        if action is None:
            return False
        return action.trigger()

    def all_actions(self) -> list[CommercialActionDefinition]:
        return list(self._actions.values())

    def all_action_ids(self) -> list[str]:
        return sorted(self._actions.keys())

    def missing_required_actions(self) -> list[str]:
        return [aid for aid in self.REQUIRED_ACTION_IDS if aid not in self._actions]

    def actions_without_handlers(self) -> list[str]:
        return [aid for aid, action in self._actions.items() if not action.has_handler()]

    def validate(self) -> dict[str, Any]:
        missing = self.missing_required_actions()
        no_handler = self.actions_without_handlers()
        return {
            "registered_count": len(self._actions),
            "required_count": len(self.REQUIRED_ACTION_IDS),
            "missing_required": missing,
            "actions_without_handlers": no_handler,
            "all_actions_have_handlers": not no_handler and not missing,
        }

    def by_category(self, category: ActionCategory) -> list[CommercialActionDefinition]:
        return [a for a in self._actions.values() if a.category == category]
