import logging
import tkinter as tk
import customtkinter as ctk
from typing import Callable

from simple_to_pdf.widgets import BaseFrame,PrimaryButton,BaseScrollableFrame

logger = logging.getLogger(__name__)


class ListControlsFrame(BaseFrame):
        
    btns_width = 100
    btns_height = 40
    btns_padx = 2
    btns_pady = 2
    
    def __init__(self, parent: tk.Frame):
        super().__init__(parent)

    def init_btns(self, *, callbacks: dict[str, Callable]) -> dict[str, tk.Widget]:
        ui: dict[str, tk.Widget] = {}
        file_nav_btns:dict[str, tk.Widget]=self._build_file_navigation_panel(callbacks=callbacks)
        action_btns:dict[str, tk.Widget]=self._build_action_panel(callbacks=callbacks)
        self.ui=file_nav_btns | action_btns
        for key, value in self.ui.items():
            setattr(self, key, value)
        return ui

    def _build_file_navigation_panel(
        self,*, callbacks: dict[str, Callable]
    ) -> dict[str, tk.Widget]:
        controls_frame: tk.Frame = BaseFrame(self)
        controls_frame.grid(row=0, column=0, sticky="n", padx=4, pady=8)

        btns = {}
        
        # Create Up and Down buttons with callbacks
        btns_side = "top"

        btns["btn_add"] = PrimaryButton(
            controls_frame,
            text="📄+",
            command=callbacks["add"],
            width=self.btns_width,
            height=self.btns_height,
        )
        btns["btn_add"].pack(side=btns_side, padx=self.btns_padx, pady=self.btns_pady)

        btns["btn_up"] = PrimaryButton(
            controls_frame,
            text="▲",
            width=self.btns_width,
            height=self.btns_height,
            command=lambda: callbacks["move"](direction="up"),
        )
        btns["btn_up"].pack(side=btns_side, padx=self.btns_padx, pady=self.btns_pady)

        btns["btn_down"] = PrimaryButton(
            controls_frame,
            text="▼",
            width=self.btns_width,
            height=self.btns_height,
            command=lambda: callbacks["move"](direction="down"),
        )
        btns["btn_down"].pack(side=btns_side, padx=self.btns_padx, pady=self.btns_pady)

        btns["btn_remove"] = PrimaryButton(
            controls_frame,
            text="🗑",
            command=callbacks["remove"],
            width=self.btns_width,
            height=self.btns_height,
        )
        btns["btn_remove"].pack(side=btns_side, padx=self.btns_padx, pady=self.btns_pady)

        # Return them so they can be accessed in self.ui
        return btns
    
    def _build_action_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, tk.Widget]:
        controls_frame: tk.Frame= BaseFrame(self,frame_type='content')
        controls_frame.grid(row=1, column=0, sticky="n", padx=4, pady=8)

        btns = {}
        btns_side = "top"

        btns["btn_merge"] = PrimaryButton(
            controls_frame,
            text="merge",
            command=callbacks["merge"],
            width=self.btns_width,
            height=self.btns_height,
        )
        btns["btn_merge"].pack(side=btns_side, padx=self.btns_padx, pady=self.btns_pady)

        btns["btn_extract"] = PrimaryButton(
            controls_frame,
            text="extract",
            width=self.btns_width,
            height=self.btns_height,
            command=callbacks["extract"],
        )
        btns["btn_extract"].pack(side=btns_side, padx=self.btns_padx, pady=self.btns_pady)

        btns["btn_status_clear"] = PrimaryButton(
            controls_frame,
            text="clear status",
            width=self.btns_width,
            height=self.btns_height,
            command=callbacks["clear_status"],
        )
        btns["btn_status_clear"].pack(side=btns_side, padx=self.btns_padx, pady=self.btns_pady)

        # Return them so they can be accessed in self.ui
        return btns
