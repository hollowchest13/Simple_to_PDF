from typing import Callable, Dict

import customtkinter as ctk

from simple_to_pdf.widgets import BaseLabel, ToogleFrame


class HelpFrame(ToogleFrame):
    def __init__(
        self,
        parent,
        *,
        width: int = 200,
        handlers: Dict[str, Callable],
        **kwargs,
    ):
        super().__init__(parent, width=width, **kwargs)

        # Localization section path in JSON
        self.loc_section = "ui.help_panel"
        self.handlers: Dict[str, Callable] = handlers

        # Centralized UI storage for localization updates
        self.ui: Dict[str, ctk.CTkBaseClass] = {}

        # Initialize all visual components
        self._setup_ui()

        # Register for language change notifications
        self.init_localization()

    def _setup_ui(self) -> None:
        """
        Creates and arranges all UI elements, then stores them in self.ui.
        """
        # 1. Create Title Label
        title = BaseLabel(self, label_type="title", text="Help")
        title.pack(side="top", fill="x", padx=(10, 10), pady=(10, 0))

        # Add to UI dict under 'title_label' key
        self.ui["title_label"] = title

        # 2. Create and pack Buttons
        buttons = self._setup_help_buttons()
        self.ui.update(buttons)

        # Allow the last row to expand (pushes everything to the top)
        self.grid_rowconfigure(len(self.ui) + 1, weight=1)

        # Map UI dictionary keys to object attributes for direct access
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
                "icon_name": "license_btn.png",
            },
            {
                "id": "documentation_btn",
                "cmd": self._trigger("documentation"),
                "icon_name": "documentation_btn.png",
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
        ]

        # Internal helper from BaseFrame that handles ctk.CTkButton creation and packing
        return self._buttons_pack(btns_config=button_configs, parent=self)
