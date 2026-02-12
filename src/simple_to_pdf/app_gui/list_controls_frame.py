import logging
import tkinter as tk
from typing import Callable

from simple_to_pdf.widgets.widgets import BaseFrame,PrimaryButton

logger = logging.getLogger(__name__)


class ListControlsFrame(BaseFrame):
    
    def __init__(self, *, parent: tk.Frame):
        super().__init__(parent)
        self.ui: dict[str, tk.Widget] = {}

    def init_btns(self, *, callbacks: dict[str, Callable]) -> dict[str, tk.Widget]:
        file_nav_btns:dict[str, tk.Button]=self._build_file_navigation_panel(
            callbacks=callbacks
        )
        self.ui.update(file_nav_btns)
        for key, value in self.ui.items():
            setattr(self, key, value)
        return self.ui

    def _build_file_navigation_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, tk.Button]:
        controls_frame: tk.Frame = BaseFrame(self)
        controls_frame.grid(row=0, column=0, sticky="n", padx=4, pady=8)

        btns = {}
        btns_width = 4
        btns_height = 2
        btns_padx = 2
        btns_pady = 2

        # Create Up and Down buttons with callbacks
        btns_side = "top"

        btns["btn_add"] = PrimaryButton(
            controls_frame,
            text="📄+",
            command=callbacks["add"],
            width=btns_width,
            height=btns_height,
        )
        btns["btn_add"].pack(side=btns_side, padx=btns_padx)

        btns["btn_up"] = PrimaryButton(
            controls_frame,
            text="▲",
            width=btns_width,
            height=btns_height,
            command=lambda: callbacks["move"](direction="up"),
        )
        btns["btn_up"].pack(side=btns_side, padx=btns_padx, pady=btns_pady)

        btns["btn_down"] = PrimaryButton(
            controls_frame,
            text="▼",
            width=btns_width,
            height=btns_height,
            command=lambda: callbacks["move"](direction="down"),
        )
        btns["btn_down"].pack(side=btns_side, padx=btns_padx, pady=btns_pady)

        btns["btn_remove"] = PrimaryButton(
            controls_frame,
            text="🗑",
            command=callbacks["remove"],
            width=btns_width,
            height=btns_height,
        )
        btns["btn_remove"].pack(side=btns_side, padx=btns_padx, pady=btns_pady)

        # Return them so they can be accessed in self.ui
        return btns
