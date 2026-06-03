from typing import Callable, Dict

import customtkinter as ctk

from simple_to_pdf.widgets import BaseLabel, ToogleFrame


class HelpFrame(ToogleFrame):
    def __init__(
        self,
        parent,
        *,
        is_open: bool = False,
        width: int = 230,
        handlers: Dict[str, Callable],
        **kwargs,
    ):
        super().__init__(parent, width=width, is_open=is_open, **kwargs)

        self.loc_section = "ui.help_panel"
        self.handlers: Dict[str, Callable] = handlers
        self.ui: Dict[str, ctk.CTkBaseClass] = {}
        self._setup_ui()
        self.init_localization()

    def _setup_ui(self) -> None:
        """
        Creates and arranges all UI elements, then stores them in self.ui.
        """
        title = BaseLabel(self, label_type="title", text="Help")
        title.pack(side="top", fill="x", padx=(10, 10), pady=(10, 0))

        self.ui["title_label"] = title

        buttons = self._setup_help_buttons()
        self.ui.update(buttons)

        self.grid_rowconfigure(len(self.ui) + 1, weight=1)

        for key, widget in self.ui.items():
            setattr(self, key, widget)

    def _setup_help_buttons(self) -> Dict[str, ctk.CTkBaseClass]:
        """
        Defines button configurations and generates them via _buttons_pack.
        Returns a dictionary of created button objects.
        """
        button_configs = [
            {
                "id": "license_btn",
                "cmd": self._trigger("license"),
            },
            {
                "id": "documentation_btn",
                "cmd": self._trigger("documentation"),
            },
            {
                "id": "about_btn",
                "cmd": self._trigger("about"),
            },
            {
                "id": "check_updates_btn",
                "cmd": self._trigger("update"),
            },
            {
                "id": "logs_btn",
                "cmd": self._trigger("logs"),
            },
            {
                "id": "dep_btn",
                "cmd": self._trigger("dependencies"),
            },
        ]

        return self._buttons_pack(btns_config=button_configs, parent=self)
