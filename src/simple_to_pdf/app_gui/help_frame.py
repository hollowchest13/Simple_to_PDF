import customtkinter as ctk
from simple_to_pdf.widgets import BaseLabel, BaseFrame, SlidingFrame
from typing import Callable


class HelpFrame(SlidingFrame):
    def __init__(
        self,
        parent,
        *,
        open_width=210,
        closed_width=0,
        callbacks: dict[str, Callable],
        **kwargs,
    ):
        super().__init__(
            parent, open_width=open_width, closed_width=closed_width, **kwargs
        )

        self.title_label = BaseLabel(self, label_type="title", text="Help").pack(
            side="top", fill="x", padx=(10, 10), pady=(10, 0)
        )
        self.loc_section = "ui.help_panel"
        self.callbacks: dict[str, Callable] = callbacks
        self.init_btns()
        self.init_localization()

    def init_btns(self) -> dict[str, ctk.CTkBaseClass]:
        help_widgets: dict[str, ctk.CTkBaseClass] = self._build_help_panel()
        self.grid_rowconfigure(3, weight=1)
        self.ui = help_widgets
        for key, value in self.ui.items():
            setattr(self, key, value)
        return self.ui

    def _build_help_panel(self) -> dict[str, ctk.CTkBaseClass]:
        """
        Builds the help panel buttons using the internal _trigger mechanism.
        No external callbacks injection needed at this stage.
        """
        button_configs = [
            {
                "id": "license_btn",
                "cmd": self._trigger("license"),  # Using string key
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
        # Return the dictionary of created buttons for localization mapping
        return self._buttons_pack(btns_config=button_configs, parent=self)
