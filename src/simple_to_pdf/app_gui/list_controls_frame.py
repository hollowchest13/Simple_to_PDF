import logging
import tkinter as tk
import customtkinter as ctk
from typing import Callable
from PIL import Image
from simple_to_pdf.core.config import ICONS_PATH

from simple_to_pdf.widgets import BaseFrame, PrimaryButton, BaseScrollableFrame

logger = logging.getLogger(__name__)


class ListControlsFrame(BaseFrame):
    btns_width = 115
    btns_height = 40
    btns_padx = 2
    btns_pady = 2

    def __init__(self, parent: ctk.CTkFrame):
        super().__init__(parent)

    def init_btns(self, *, callbacks: dict[str, Callable]) -> dict[str, tk.Widget]:
        file_nav_btns: dict[str, tk.Widget] = self._build_file_navigation_panel(
            callbacks=callbacks
        )
        action_btns: dict[str, tk.Widget] = self._build_action_panel(
            callbacks=callbacks
        )
        settings_btn: dict[str, tk.Widget] = self._build_settings_panel(
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

    def _load_icon(self, *, icon_name: str, size=(20, 20)):

        full_path = ICONS_PATH / icon_name

        try:
            pil_img = Image.open(full_path)

            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception as e:
            logger.error(f"❌ Error CTkImage: {e}")
            return None

    def _buttons_pack(self, *, btns_config, parent: tk.Frame):
        btns = {}

        for i, cfg in enumerate(btns_config):
            icon = (
                self._load_icon(icon_name=cfg["icon_name"])
                if "icon_name" in cfg
                else None
            )
            btn = PrimaryButton(
                parent,
                text=cfg["text"],
                command=cfg["cmd"],
                image=icon,
                width=self.btns_width,
                height=self.btns_height,
            )

            is_first = i == 0
            is_last = i == len(btns_config) - 1

            top_pad = 15 if is_first else 4
            bottom_pad = 15 if is_last else 4

            btn.pack(side="top", fill="x", padx=15, pady=(top_pad, bottom_pad))

            btns[cfg["id"]] = btn

        return btns

    def _build_file_navigation_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, tk.Widget]:

        self.nav_frame = BaseFrame(self, frame_type="btns_container")

        button_configs = [
            {
                "id": "btn_add",
                "text": "Add files",
                "cmd": callbacks["add"],
                "icon_name": "add_btn.png",
            },
            {
                "id": "btn_up",
                "text": "Move up",
                "cmd": lambda: callbacks["move"](
                    direction="up",
                ),
                "icon_name": "up_btn.png",
            },
            {
                "id": "btn_down",
                "text": "Move down",
                "cmd": lambda: callbacks["move"](direction="down"),
                "icon_name": "down_btn.png",
            },
            {
                "id": "btn_remove",
                "text": "Remove",
                "cmd": callbacks["remove"],
                "icon_name": "remove_btn.png",
            },
        ]
        return self._buttons_pack(btns_config=button_configs, parent=self.nav_frame)

    def _build_action_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, tk.Widget]:
        self.action_frame = BaseFrame(self, frame_type="btns_container")

        button_configs = [
            {
                "id": "btn_merge",
                "text": "Merge files",
                "cmd": callbacks["merge"],
                "icon_name": "merge_btn.png",
            },
            {
                "id": "btn_extract",
                "text": "Extract pages",
                "cmd": callbacks["extract"],
                "icon_name": "extract_btn.png",
            },
            {
                "id": "btn_status_clear",
                "text": "Clear console",
                "cmd": callbacks["clear_status"],
                "icon_name": "clean_btn.png",
            },
        ]

        return self._buttons_pack(btns_config=button_configs, parent=self.action_frame)

    def _build_settings_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, tk.Widget]:
        self.settings_frame = BaseFrame(self, frame_type="btns_container")
        button_configs = [
            # {"id": "btn_updates",       "text": "Check Updates", "cmd": callbacks["update"]},
            # {"id": "btn_licence",       "text": "License",       "cmd": callbacks["license"]},
            # {"id": "btn_about",         "text": "About",         "cmd": callbacks["documentation"]},
            {
                "id": "btn_help",
                "text": "Help",
                "cmd": callbacks["help"],
                "icon_name": "help_btn.png",
            },
            {
                "id": "btn_settings",
                "text": "Settings",
                "cmd": callbacks["settings"],
                "icon_name": "settings_btn.png",
            },
        ]
        return self._buttons_pack(
            btns_config=button_configs, parent=self.settings_frame
        )
