import tkinter as tk
from tkinter import ttk

class GUIBuilder:
    def build_gui(self, parent: tk.Tk, callbacks: dict) -> dict:
        # Window settings
        parent.title("Simple to PDF - PDF Merger")
        parent.geometry("700x400")
        
        # Dictionary to hold references to created widgets
        ui = {}

        # 1. Top panel (Buttons)
        ui.update(self._build_top_controls_area(parent, callbacks))
        
        # 2. Main area (Frame for Listbox + Progress + Status)
        # Create container for the central part
        widgets_area = tk.Frame(parent)
        widgets_area.pack(side = "left", fill = "both", expand = True)
        
        # Fill the central part
        ui['listbox'] = self._build_file_batch_area(widgets_area)
        ui['progress_bar'], ui['progress_label'] = self._build_progress_bar(widgets_area)
        ui['status_text'] = self._build_status_area(widgets_area)
        
        # 3. Right panel (Arrows)
        ui.update(self._build_right_controls_area(parent, callbacks))
        
        return ui

    def _build_top_controls_area(self, parent, callbacks):
        top = tk.Frame(parent)
        top.pack(fill = "x", padx = 4, pady = 8)
        btns = {}
        
        btns_padx = 4
        # Using callbacks instead of self.add_files
        btns['btn_add'] = tk.Button(top, text = "Add files", command = callbacks['add'])
        btns['btn_add'].pack(side = "left", padx = btns_padx)

        btns['btn_merge'] = tk.Button(top, text = "Merge PDFs", command = callbacks['merge'])
        btns['btn_merge'].pack(side = "left", padx = btns_padx)

        btns['btn_extract'] = tk.Button(top, text = "Get pages", command = callbacks['extract'])
        btns['btn_extract'].pack(side = "left", padx = btns_padx)

        btns['btn_remove'] = tk.Button(top, text = "Remove files", command = callbacks['remove'])
        btns['btn_remove'].pack(side = "left", padx = btns_padx)
        
        return btns

    def _build_file_batch_area(self, parent):
        mid = tk.Frame(parent)
        mid.pack(fill = "both", expand = True, padx = 4, pady = 8)
        
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

    def _build_right_controls_area(self, parent, callbacks) -> dict:
        right = tk.Frame(parent)
        right.pack(side = "right", fill = "y", padx = 4, pady = 8)
        btns = {}
        btns_width = 3
    
        # Create Up and Down buttons with callbacks
        btns['btn_up'] = tk.Button(right, text="▲", width = btns_width, command = lambda: callbacks['move'](direction="up"))
        btns['btn_up'].pack(pady=2)

        btns['btn_down'] = tk.Button(right, text="▼", width = btns_width, command = lambda: callbacks['move'](direction="down"))
        btns['btn_down'].pack(pady=2)

        # Return them so they can be accessed in self.ui
        return btns

    def _build_status_area(self, parent):
        status_frame = tk.Frame(parent)
        status_frame.pack(fill="x", padx = 4, pady = 8)
        
        scrollbar = tk.Scrollbar(status_frame)
        scrollbar.pack(side = "right", fill = "y")
        
        text = tk.Text(
            status_frame, height = 5, state = "disabled",
            font=("Consolas", 9), yscrollcommand = scrollbar.set,
            borderwidth = 1, relief = "solid"
        )
        text.pack(side = "bottom", fill = "x", expand = True)
        scrollbar.config(command = text.yview)
        return text

    def _build_progress_bar(self, parent):
        progress_frame = tk.Frame(parent)
        progress_frame.pack(side = "top", fill = "x", padx = (4, 22), pady = (2, 14))
        
        label = tk.Label(progress_frame, text="Progress:")
        label.pack(pady = 4)
        
        bar = ttk.Progressbar(progress_frame, orient = "horizontal", mode = "determinate")
        bar.pack(pady = 8, fill = "x")
        return bar, label