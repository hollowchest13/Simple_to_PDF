import logging
import tkinter as tk
import customtkinter as ctk
from typing import Callable

from simple_to_pdf.widgets import BaseScrollableFrame,PrimaryButton

logger = logging.getLogger(__name__)


class ActionControlsFrame(BaseScrollableFrame):
    
    def __init__(self,*, parent: tk.Frame):
        super().__init__(parent=parent)
        self.ui: dict[str, tk.Widget] = {}

    def init_btns(self, *, callbacks: dict[str, Callable]) -> dict[str, tk.Widget]:
        action_btns:dict[str, ctk.CTkButton]=self._action_panel(
            callbacks=callbacks
        )
        self.ui.update(action_btns)
        for key, value in self.ui.items():
            setattr(self, key, value)
        return self.ui

    def _action_panel(
        self, *, callbacks: dict[str, Callable]
    ) -> dict[str, ctk.CTkButton]:
        controls_frame: ctk.CTkScrollableFrame= BaseScrollableFrame(self,scr_frame_type='button_list')
        controls_frame.grid(row=0, column=0, sticky="n", padx=4, pady=8)

        btns = {}
        btns_width = 60
        btns_height = 40
        btns_padx = 2
        btns_pady = 2

        btns_side = "top"

        btns["btn_merge"] = PrimaryButton(
            controls_frame,
            text="merge",
            command=callbacks["merge"],
            width=btns_width,
            height=btns_height,
        )
        btns["btn_merge"].pack(side=btns_side, padx=btns_padx, pady=btns_pady)

        btns["btn_extract"] = PrimaryButton(
            controls_frame,
            text="extract",
            width=btns_width,
            height=btns_height,
            command=lambda: callbacks["extract"],
        )
        btns["btn_extract"].pack(side=btns_side, padx=btns_padx, pady=btns_pady)

        btns["btn_status_clear"] = PrimaryButton(
            controls_frame,
            text="clear status",
            width=btns_width,
            height=btns_height,
            command=lambda: callbacks["clear"],
        )
        btns["btn_down"].pack(side=btns_side, padx=btns_padx, pady=btns_pady)

        btns["btn_status_clear"] = PrimaryButton(
            controls_frame,
            text="clear status",
            command=callbacks["remove"],
            width=btns_width,
            height=btns_height,
        )
        btns["btn_remove"].pack(side=btns_side, padx=btns_padx, pady=btns_pady)

        # Return them so they can be accessed in self.ui
        return btns
