import tkinter as tk
from tkinter import ttk

import logging

logger = logging.getLogger(__name__)

class ListControlsFrame(tk.Frame):

    def __init__(self,*, parent: tk.Tk):
        super().__init__(parent)

              
    def init_btns(self,*,callbacks: dict[str,callable]) -> None:
        self.ui: dict[str,tk.Widget] = self._build_right_controls_area(callbacks = callbacks)
        for key, value in self.ui.items():
            setattr(self, key, value)
   
    def _build_right_controls_area(self,*, callbacks: dict[str, callable]) -> dict[str, tk.Button]:
        controls_frame: tk.Frame = tk.Frame(self)
        controls_frame.grid(row = 0, column = 0, sticky = "n", padx = 4, pady = 8)
        btns = {}
        btns_width = 4
        btns_height = 2
        btns_padx = 2
        btns_pady = 2
    
        # Create Up and Down buttons with callbacks
        btns_side = "top"

        btns['btn_add'] = tk.Button(controls_frame, text = "➕", command = callbacks['add'], width = btns_width, height = btns_height)
        btns['btn_add'].pack(side = btns_side, padx = btns_padx)

        btns['btn_up'] = tk.Button(controls_frame, text  = "▲", width = btns_width, height = btns_height, command = lambda: callbacks['move'](direction = "up"))
        btns['btn_up'].pack(side = btns_side, padx = btns_padx, pady = btns_pady)

        btns['btn_down'] = tk.Button(controls_frame, text = "▼", width = btns_width, height = btns_height, command = lambda: callbacks['move'](direction = "down"))
        btns['btn_down'].pack(side = btns_side, padx = btns_padx, pady = btns_pady)

        btns['btn_remove'] = tk.Button(controls_frame, text = "🗑", command = callbacks['remove'], width = btns_width, height = btns_height)
        btns['btn_remove'].pack(side = btns_side, padx = btns_padx, pady = btns_pady)

        # Return them so they can be accessed in self.ui
        return btns