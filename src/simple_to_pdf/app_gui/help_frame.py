import customtkinter as ctk
from simple_to_pdf.widgets import BaseLabel, BaseFrame, SlidingFrame
from typing import Callable


class HelpFrame(SlidingFrame):
    def __init__(self, parent, *, open_width=170, closed_width=0, **kwargs):
        super().__init__(
            parent, open_width=open_width, closed_width=closed_width, **kwargs
        )
        self.title_label = BaseLabel(self, label_type="title", text="Help").pack(
            side="top", fill="x", padx=(10, 10), pady=(10, 0)
        )

    def init_btns(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, ctk.CTkBaseClass]:
        help_widgets: dict[str, ctk.CTkBaseClass] = self._build_help_panel(
            callbacks=callbacks
        )
        self.grid_rowconfigure(3, weight=1)
        self.ui = help_widgets
        for key, value in self.ui.items():
            setattr(self, key, value)
        return self.ui

    def _build_help_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, ctk.CTkBaseClass]:

        button_configs = [
            {
                "id": "license_btn",
                "cmd": callbacks["license"],
                "icon_name": "license_btn.png",
            },
            {
                "id": "documentation_btn",
                "cmd": callbacks["documentation"],
                "icon_name": "documentation_btn.png",
            },
            {
                "id": "about_btn",
                "cmd": callbacks["about"],
                "icon_name": "about_btn.png",
            },
            {
                "id": "check_updates_btn",
                "cmd": callbacks["update"],
                "icon_name": "update_btn.png",
            },
            {
                "id": "logs_btn",
                "cmd": callbacks["logs"],
                "icon_name": "logs.png",
            },
        ]
        return self._buttons_pack(btns_config=button_configs, parent=self)
