import tkinter as tk
from tkinter import ttk

import logging

logger = logging.getLogger(__name__)

class MainFrame(tk.Frame):


    def __init__(self, parent:tk.Tk):
        super().__init__(parent)

        self.filebox = self._build_file_batch_area()
        self.progress_bar = self._build_progress_bar()
        self.status_bar = self._build_status_area()



    def _build_file_batch_area(self) -> tk.Listbox:

        """Builds the central Listbox area for displaying files."""

        mid = tk.Frame(self)
        mid.pack(fill = "both", expand = True, padx = 12, pady = 8)
        
        scrollbar = tk.Scrollbar(mid)
        scrollbar.pack(side = "right", fill = "y")
        
        listbox = tk.Listbox(
            mid, 
            selectmode = "multiple",
            yscrollcommand = scrollbar.set,
            borderwidth = 1,
            relief = "solid"
        )
        listbox.pack(side = "left", fill = "both", expand = True)
        scrollbar.config(command = listbox.yview)
        return listbox


    def _build_status_area(self) -> tk.Text:
        status_frame = tk.Frame(self)
        status_frame.pack(fill = "x", padx = 12, pady = 4)
        
        scrollbar = tk.Scrollbar(status_frame)
        scrollbar.pack(side = "right", fill = "y")
        
        text = tk.Text(
            status_frame, height = 5, state = "disabled",
            font = ("Consolas", 9), yscrollcommand = scrollbar.set,
            borderwidth = 1, relief = "solid"
        )
        text.pack(side = "bottom", fill = "x", expand = True)
        scrollbar.config(command = text.yview)
        return text
    
    def _build_progress_bar(self) -> tuple[ttk.Progressbar, tk.Label]:
        progress_frame = tk.Frame(self)
        progress_frame.pack(side = "top", fill = "x", padx = (12, 22), pady = (2, 16))
        
        label = tk.Label(progress_frame, text = "Progress:")
        label.pack(pady = 4)
        
        bar = ttk.Progressbar(progress_frame, orient = "horizontal", mode = "determinate")
        bar.pack(pady = 8, fill = "x")
        return bar, label