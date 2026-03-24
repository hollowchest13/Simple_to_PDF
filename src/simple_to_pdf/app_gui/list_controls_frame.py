import logging
import customtkinter as ctk
from typing import Callable


from simple_to_pdf.widgets import BaseFrame

logger = logging.getLogger(__name__)


class ListControlsFrame(BaseFrame):
    def __init__(self, parent: ctk.CTkFrame, *, width: int = 150, **kwargs):
        super().__init__(parent, width=width, **kwargs)

    def init_btns(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, ctk.CTkBaseClass]:
        file_nav_btns: dict[str, ctk.CTkBaseClass] = self._build_file_navigation_panel(
            callbacks=callbacks
        )
        action_btns: dict[str, ctk.CTkBaseClass] = self._build_action_panel(
            callbacks=callbacks
        )
        settings_btn: dict[str, ctk.CTkBaseClass] = self._build_settings_panel(
            callbacks=callbacks
        )

        self.grid_rowconfigure(3, weight=1)

        self.nav_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=8)
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=4, pady=8)
        self.settings_frame.grid(row=4, column=0, sticky="ew", padx=4, pady=8)

        self.ui = file_nav_btns | action_btns | settings_btn
        for key, value in self.ui.items():
            setattr(self, key, value)
        return self.ui

    def _build_file_navigation_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, ctk.CTkBaseClass]:

        self.nav_frame = BaseFrame(self, frame_type="btns_container")

        # TODO Add enum for buttons id
        button_configs = [
            {
                "id": "btn_add",
                "cmd": callbacks["add"],
                "icon_name": "add_btn.png",
            },
            {
                "id": "btn_up",
                "cmd": lambda: callbacks["move"](
                    direction="up",
                ),
                "icon_name": "up_btn.png",
            },
            {
                "id": "btn_down",
                "cmd": lambda: callbacks["move"](direction="down"),
                "icon_name": "down_btn.png",
            },
            {
                "id": "btn_remove",
                "cmd": callbacks["remove"],
                "icon_name": "remove_btn.png",
            },
        ]
        return self._buttons_pack(btns_config=button_configs, parent=self.nav_frame)

    def _build_action_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, ctk.CTkBaseClass]:
        self.action_frame = BaseFrame(self, frame_type="btns_container")

        button_configs = [
            {
                "id": "btn_merge",
                "cmd": callbacks["merge"],
                "icon_name": "merge_btn.png",
            },
            {
                "id": "btn_extract",
                "cmd": callbacks["extract"],
                "icon_name": "extract_btn.png",
            },
            {
                "id": "btn_status_clear",
                "cmd": callbacks["clear_status"],
                "icon_name": "clean_btn.png",
            },
        ]

        return self._buttons_pack(btns_config=button_configs, parent=self.action_frame)

    def _build_settings_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, ctk.CTkBaseClass]:
        self.settings_frame = BaseFrame(self, frame_type="btns_container")
        button_configs = [
            {
                "id": "btn_help",
                "cmd": callbacks["help"],
                "icon_name": "help_btn.png",
            },
            {
                "id": "btn_settings",
                "cmd": callbacks["settings"],
                "icon_name": "settings_btn.png",
            },
        ]
        return self._buttons_pack(
            btns_config=button_configs, parent=self.settings_frame
        )
