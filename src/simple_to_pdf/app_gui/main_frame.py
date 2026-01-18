import tkinter as tk
from tkinter import ttk,messagebox
from src.simple_to_pdf.app_gui.utils import clear_text_widget,get_files,get_selected_values,list_update,reselect_items,listbox_clear
from src.simple_to_pdf.pdf.pdf_merger import PdfMerger
import logging

logger = logging.getLogger(__name__)

class MainFrame(tk.Frame):


    def __init__(self, parent:tk.Tk, merger: PdfMerger):
        super().__init__(parent)
        self.ui: dict[str, tk.Widget] = {}
        
        # 2. set attributes and register in self.ui
        self._register_components(self._setup_layout())
        self.merger = merger
        

    def _setup_layout(self):
        raw_components = {}

        status_area = tk.Frame(self)
        status_area.pack(side = "bottom", fill = "x", padx = 12, pady = 4)

        file_batch_area = tk.Frame(self)
        file_batch_area.pack(fill = "both", expand = True, padx = 12, pady = 8)

        progress_area = tk.Frame(self)
        progress_area.pack(side = "top", fill = "x", padx = (12, 22), pady = (2, 16))

        # Create and register all components
        raw_components = {
            'filebox': self._setup_file_batch_area(mid = file_batch_area),
            'status_text': self._setup_status_area(status_frame = status_area)
        }
    
        # Then build progress bar and label because it returns two widgets
        p_bar, p_label = self._setup_progress_bar_area(progress_frame = progress_area)
        raw_components['progress_bar'] = p_bar
        raw_components['progress_label'] = p_label
        return raw_components

    def _register_components(self, components: dict[str, tk.Widget]):

        """Adds components to self and self.ui for easy access."""
        
        for key, widget in components.items():
            setattr(self, key, widget)  
            self.ui[key] = widget       

    def _setup_file_batch_area(self,mid:tk.Frame) -> tk.Listbox:

        """Builds the central Listbox area for displaying files."""
        
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


    def _setup_status_area(self,status_frame: tk.Frame) -> tk.Text:
        
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
    
    def _setup_progress_bar_area(self, progress_frame: tk.Frame) -> tuple[ttk.Progressbar, tk.Label]:
        
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
    

    def _get_formatted_filetypes(self) -> list[tuple[str, str]]:

        """Converts a dictionary of formats into a list of tuples for the dialog window."""

        supported_dict = self.merger.converter.get_supported_formats()
        formatted_types = []

        # 1.Get all extensions for the general filter
        all_exts = []
        for exts in supported_dict.values():
            all_exts.extend(exts)

        # Create a string like "*.pdf *.docx *.png"
        all_pattern = " ".join([f"*{e}" for e in all_exts])
        formatted_types.append(("All supported files", all_pattern))

        # 2. Add each category separately
        # Sort keys so PDF is always at the top or logically first
        for category in sorted(supported_dict.keys()):
            exts = supported_dict[category]
            label = f"{category.capitalize()} files"
            pattern = " ".join([f"*{e}" for e in exts])
            formatted_types.append((label, pattern))
        return formatted_types
    
     # Add files to the listbox
    def add_files(self):

        """Add files of selected types."""
        
        # Supported list the extensions 
        types = self._get_formatted_filetypes()
        new_files_paths: list[str] =  list(get_files(filetypes = types, multiple = True))

        if not new_files_paths:
            return

        # Call the method. It will create "All supported" files
        saved_files_paths: list[str] = list(self.filebox.get(0,tk.END))
        
        files_paths: list[str] = saved_files_paths + new_files_paths
        
        if files_paths: 
            self.progress_bar_reset()
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
        self.progress_bar_reset()
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

        self.progress_bar_reset()
        list_update(files = items,listbox = self.filebox)
        reselect_items(all_items = items, selected_values = selected_values,listbox = self.filebox)

    def progress_bar_reset(self):
        pb: ttk.Progressbar = self.progress_bar
        pl: tk.Label = self.progress_label
        pb.stop()
        pb.config(mode='determinate', value = 0, maximum = 100)
        pl.config(text = "Progress: Ready")
        self.update_idletasks()

    def set_progress_determinate(self, max_value=100):
        """
        Safely switches the progress bar to determinate mode.
        This method should be called via .after() if triggered from a worker thread.
        """
        if self.progress_bar.winfo_exists():
            self.progress_bar.stop()  # Stop indeterminate animation
            self.progress_bar.config(
            mode = 'determinate',
            value = 0,
            maximum = max_value
            )
            self.update_idletasks() # Refresh the UI immediately
    
    