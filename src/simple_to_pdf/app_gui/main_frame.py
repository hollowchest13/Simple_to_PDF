import tkinter as tk
from tkinter import ttk,messagebox
from src.simple_to_pdf.app_gui.utils import clear_text_widget,get_files,get_selected_values,list_update,reselect_items,listbox_clear

import logging

logger = logging.getLogger(__name__)

class MainFrame(tk.Frame):


    def __init__(self, parent:tk.Tk):
        super().__init__(parent)

        self.filebox = self._build_file_batch_area()
        self.progress_bar = self._build_progress_bar()
        self.status_text = self._build_status_area()


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
    
    def clear_status_text(self) -> None:
        clear_text_widget(self.status_text)
    
    def load_from_listbox(self) -> list[tuple[int,str]]:
        result: list[tuple[int,str]] = []
        if self.filebox.size() == 0:
            return result
        for i in range(self.filebox.size()):
            text = self.filebox.get(i)
            result.append((i, text))
        return result
    
     # Add files to the listbox
    def add_files(self):

        """Add files of selected types."""

        # Supported list the extensions 
        types = ("xls", "xlsx", "doc", "docx", "jpg", "png", "pdf")

        new_files_paths: list[str] =  list(get_files(filetypes = types, multiple = True))

        if not new_files_paths:
            return

        # Call the method. It will create "All supported" files
        saved_files_paths: list[str] = list(self.filebox.get(0,tk.END))
        
        files_paths: list[str] = saved_files_paths + new_files_paths
        
        if files_paths: 
            list_update(files = files_paths,listbox = self.filebox)
    
    def remove_files(self) -> None:
        all_files = list(self.filebox.get(0,tk.END))
        sel_files = get_selected_values(listbox = self.filebox)
        if not all_files:

            messagebox.showinfo("No files", "The file list is already empty.")
            return
        elif not sel_files:
            answer = messagebox.askyesno(
                "No files.",
                "No files selected. Do you want to remove all files?"
            )
            if answer:
                listbox_clear(listbox = self.filebox)
                return 
            
        for file in sel_files:
            if file in all_files:
                all_files.remove(file)
        list_update(files = all_files,listbox = self.filebox)
       
    # Move selected items in the listbox
    def move_on_listbox(self,*, direction: str):

        """Move selected items up or down in the listbox."""

        sel_idxs = sorted(self.filebox.curselection())
        if not sel_idxs:
            return

        items = list(self.filebox.get(0, tk.END))
        selected_values = [items[i] for i in sel_idxs]

        max_idx = len(items) - 1

        if direction == "down":
            for i in reversed(sel_idxs):
                if i < max_idx and i + 1 not in sel_idxs:
                    items[i], items[i + 1] = items[i + 1], items[i]
                    sel_idxs[sel_idxs.index(i)] += 1

        elif direction == "up":
            for i in sel_idxs:
                if i > 0 and i-1 not in sel_idxs:
                    items[i], items[i - 1] = items[i - 1], items[i]
                    sel_idxs[sel_idxs.index(i)] -= 1

        list_update(files = items,listbox = self.filebox)
        reselect_items(all_items = items, selected_values = selected_values,listbox = self.filebox)
    
    