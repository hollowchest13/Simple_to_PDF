import tkinter as tk
from tkinter import ttk

class GUIBuilder:
    def build_gui(self,*, parent: tk.Tk, callbacks: dict[str, callable]) -> dict[str, tk.Widget]:

        """Builds the main GUI layout and returns a dictionary of widgets."""

        # Window settings
        parent.title("Simple to PDF - PDF Merger")
        parent.geometry("700x400")

        # Dictionary to hold references to created widgets
        ui = {}

        list_controller_frame = tk.Frame(parent)
        list_controller_frame.pack(side = "right", fill = "both")
        main_frame = tk.Frame(parent)
        main_frame.pack(side = "left", expand = True, fill = "both")

        ui.update(self._build_right_controls_area(parent = list_controller_frame, callbacks = callbacks))
        ui['listbox'] = self._build_file_batch_area(parent = main_frame)
        ui['progress_bar'], ui['progress_label'] = self._build_progress_bar(parent = main_frame)
        ui['status_text'] = self._build_status_area(parent = main_frame)
        
        return ui
    
    def _build_menu_bar(self,*, parent: tk.Tk, callbacks: dict[str, callable]) -> tk.Menu:
        
        """Builds the menu bar for the application."""

        menu_bar = tk.Menu(parent)
        parent.config(menu = menu_bar)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff = 0)
        file_menu.add_command(label = "Add Files", command = callbacks['add'])
        file_menu.add_command(label = "Merge to PDF", command = callbacks['merge'])
        file_menu.add_command(label = "Extract pages", command = callbacks['extract'])
        file_menu.add_command(label = "Remove file", command = callbacks['remove'])
        file_menu.add_command(label = "Clear status",command = callbacks['clear_status'])
        file_menu.add_separator()
        file_menu.add_command(label = "Exit", command = parent.quit)
        menu_bar.add_cascade(label = "File", menu = file_menu)

        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff = 0)
        help_menu.add_command(label = "License", command = callbacks['license'])
        help_menu.add_command(label = "How to use", command = callbacks['documentation'])
        help_menu.add_command(label = "Check updates", command = callbacks['update'])
        menu_bar.add_cascade(label = "Help", menu = help_menu)

        return menu_bar

    def _build_file_batch_area(self,*, parent: tk.Frame | tk.Tk) -> tk.Listbox:

        """Builds the central Listbox area for displaying files."""

        mid = tk.Frame(parent)
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

    def _build_right_controls_area(self,*, parent: tk.Frame | tk.Tk, callbacks: dict[str, callable]) -> dict[str, tk.Button]:
        right = tk.Frame(parent)
        right.grid(row = 0, column = 0, sticky = "n", padx = 4, pady = 8)
        btns = {}
        btns_width = 4
        btns_height = 2
        btns_padx = 2
        btns_pady = 2
    
        # Create Up and Down buttons with callbacks
        btns_side = "top"

        btns['btn_add'] = tk.Button(right, text = "➕", command = callbacks['add'], width = btns_width, height = btns_height)
        btns['btn_add'].pack(side = btns_side, padx = btns_padx)

        btns['btn_up'] = tk.Button(right, text  = "▲", width = btns_width, height = btns_height, command = lambda: callbacks['move'](direction = "up"))
        btns['btn_up'].pack(side = btns_side, padx = btns_padx, pady = btns_pady)

        btns['btn_down'] = tk.Button(right, text = "▼", width = btns_width, height = btns_height, command = lambda: callbacks['move'](direction = "down"))
        btns['btn_down'].pack(side = btns_side, padx = btns_padx, pady = btns_pady)

        btns['btn_remove'] = tk.Button(right, text = "🗑", command = callbacks['remove'], width = btns_width, height = btns_height)
        btns['btn_remove'].pack(side = btns_side, padx = btns_padx, pady = btns_pady)

        # Return them so they can be accessed in self.ui
        return btns

    def _build_status_area(self,*, parent: tk.Frame | tk.Tk) -> tk.Text:
        status_frame = tk.Frame(parent)
        status_frame.pack(fill = "x", padx = 12, pady = 4)
        
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

    def _build_progress_bar(self,*, parent: tk.Frame | tk.Tk) -> tuple[ttk.Progressbar, tk.Label]:
        progress_frame = tk.Frame(parent)
        progress_frame.pack(side = "top", fill = "x", padx = (12, 22), pady = (2, 16))
        
        label = tk.Label(progress_frame, text = "Progress:")
        label.pack(pady = 4)
        
        bar = ttk.Progressbar(progress_frame, orient = "horizontal", mode = "determinate")
        bar.pack(pady = 8, fill = "x")
        return bar, label