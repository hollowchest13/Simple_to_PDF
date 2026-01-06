from pathlib import Path
import os
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog, messagebox,scrolledtext
import threading
from src.simple_to_pdf.pdf import PdfMerger, PageExtractor
from src.simple_to_pdf.app_gui.gui_builder import GUIBuilder
from src.simple_to_pdf.app_gui.gui_callback import GUICallback
from src.simple_to_pdf.app_gui.utils import get_text, get_files, get_pages

import logging

logger = logging.getLogger(__name__)

class PDFMergerGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        handlers = self._setup_handlers()
        builder = GUIBuilder()
        self.menu_bar = builder._build_menu_bar(parent = self, callbacks = handlers)
        self.ui = builder.build_gui(parent = self, callbacks = handlers)
        self._init_controls()
        self._init_services()

    def _setup_handlers(self) -> dict:

        """Create a dictionary of commands to pass to the Builder."""

        handlers: dict[str, callable] = {
            'add': self.add_files,
            'merge': self.on_merge,
            'extract': self.prompt_pages_to_remove,
            'remove': self.remove_files,
            'move': self.move_on_listbox,
            'license':self.show_license,
            'documentation':self.show_documentation,
            'update':self.check_updates,
            'about':self.show_about,
            'clear_status':self.clear_status_text
            }
        return handlers
    
    def clear_status_text(self) -> None:
        self.status_text.config(state ="normal")     
        self.status_text.delete("1.0", "end")        
        self.status_text.config(state = "disabled")

    def check_updates(self) -> None:
        pass

    def show_about(self) -> None:
        pass

    def show_license(self) -> None:
        license_file_name: str = "LICENSE"
        license_path: Path = os.path.join(os.path.dirname(__file__),license_file_name)
        license_text: str = get_text(file_name = license_file_name,file_path = license_path)
        if not license_text:
            return
        self._create_text_window(title = "LICENSE",text = license_text)

    def _create_text_window(self,*,text: str,title: str,size: str = "700x400",text_font: str = "Consolas",font_size: int = 10) -> None:
        top = tk.Toplevel(self)
        top.title(title)
        top.geometry(size)
        top.resizable(False,False)
        txt:scrolledtext.ScrolledText = scrolledtext.ScrolledText(top, wrap = tk.WORD,font = (text_font,font_size))
        txt.insert(tk.END,text)
        txt.config(state = tk.DISABLED)
        txt.pack(expand = True,fill = "both", padx = 10,pady = 10)
        btn_close:tk.Button = tk.Button(top, text = "Got it!", command = top.destroy)
        btn_close.pack(pady = 5)

    def show_documentation(self) -> None:
        pass

    def _init_controls(self) -> None:

        """Create  references to widgets from self.ui."""

        # Display elements
        self.listbox: tk.Listbox = self.ui['listbox']
        self.progress_bar: ttk.Progressbar = self.ui['progress_bar']
        self.status_text: tk.Text = self.ui['status_text']

        # Buttons
        self.btn_add: tk.Button = self.ui['btn_add']
        self.btn_remove: tk.Button = self.ui['btn_remove']
        self.btn_up: tk.Button = self.ui['btn_up']
        self.btn_down: tk.Button = self.ui['btn_down']

    def _init_services(self) -> None:

        """Initialize internal logic and services."""

        self.callback = GUICallback(main_app = self)
        self.merger = PdfMerger()
        self.page_extractor = PageExtractor()

    def _load_from_listbox(self) -> list[tuple[int,str]]:
        result: list[tuple[int,str]] = []
        if self.listbox.size() == 0:
            return result
        for i in range(self.listbox.size()):
            text = self.listbox.get(i)
            result.append((i,text))
        return result
    
    def _get_selected_values(self) -> list[str]:
        selection = self.listbox.curselection()
        if not selection:
            return []
        return [(self.listbox.get(i)) for i in self.listbox.curselection()]
    
    def _listbox_clear(self) -> None:
        self.listbox.delete(0, tk.END)

   # List Updating
    def _list_update(self,*,files: list[str]) -> None:
        self._listbox_clear()
        for pdf in files:
            self.listbox.insert(tk.END, pdf)
    
    # Reselect items after update
    def _reselect_items(self,*, all_items, selected_values):
        self.listbox.selection_clear(0, tk.END)
        for idx, val in enumerate(all_items):
            if val in selected_values:
                self.listbox.selection_set(idx)

    # Add files to the listbox
    def add_files(self):

        """Add files of selected types."""

        # Supported list the extensions 
        types = ("xls", "xlsx", "doc", "docx", "jpg", "png", "pdf")

        new_files_paths: list[str] =  list(get_files(filetypes = types, multiple = True))

        if not new_files_paths:
            return

        # Call the method. It will create "All supported" files
        saved_files_paths: list[str] = list(self.listbox.get(0,tk.END))
        
        files_paths: list[str] = saved_files_paths + new_files_paths
        
        if files_paths: 
            self._list_update(files = files_paths)
    
    def remove_files(self) -> None:
        all_files = list(self.listbox.get(0,tk.END))
        sel_files = self._get_selected_values()
        if not all_files:

            messagebox.showinfo("No files", "The file list is already empty.")
            return
        elif not sel_files:
            answer = messagebox.askyesno(
                "No files.",
                "No files selected. Do you want to remove all files?"
            )
            if answer:
                self._listbox_clear()
                return 
            
        for file in sel_files:
            if file in all_files:
                all_files.remove(file)
        self._list_update(files = all_files)
       
    # Move selected items in the listbox
    def move_on_listbox(self,*, direction: str):

        """Move selected items up or down in the listbox."""

        sel_idxs = sorted(self.listbox.curselection())
        if not sel_idxs:
            return

        items = list(self.listbox.get(0, tk.END))
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

        self._list_update(files = items)
        self._reselect_items(all_items = items, selected_values = selected_values)

    def on_merge(self):

        """Handler for Merge button click"""

        # 1. Preparing data (quick operation, doing in main thread)
        files = self._load_from_listbox()
        self.callback.progress_bar_reset()

        if not files:
            messagebox.showwarning("Warning", "No files to merge")
            return

        out = filedialog.asksaveasfilename(
            title = "Save Merged PDF", 
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile = "merged.pdf"
        )
        if not out: 
            return

        # 3. START THREAD
        # Pass data (files and out) via args
        thread = threading.Thread(
            target = self._run_merge_worker, 
            kwargs={"files": files, "output_path": out},
            daemon = True
        )
        thread.start()

    def _run_merge_worker(self, files, output_path):
        try:
            
            # Give this safe wrapper to the engine
            self.merger.merge_to_pdf(
                files = files, 
                output_path = output_path, 
                callback = self.callback.safe_callback # Use the wrapper
            )
            self.after(0, lambda: self.callback.show_status_message(f"Merged PDF saved to:\n{output_path}"))
        except Exception as e:
            self.after(0, lambda: self.callback.show_status_message(f"❌ Error: Could not merge files: \n{e}"))
        
        
    def prompt_pages_to_remove(self):
        input_path: str = get_files(filetypes = "*.pdf", multiple = False)

        if not input_path:
            return
        
        win = tk.Toplevel(self)
        win.title("Pages to extract")
        win.geometry("350x170")
        win.transient(self)
        win.grab_set()

        # Create a label and entry for page selection
        # Main instruction
        tk.Label(win, text = "Select pages to extract:", font = ("TkDefaultFont", 10, "bold")).pack(pady=(20, 0))

        # Format description (hint)
        hint_text = "Format: 1, 3, 5-10\n(use commas for single pages and dashes for ranges)"
        tk.Label(win, text = hint_text, fg = "gray", font = ("TkDefaultFont", 9)).pack(pady = (0, 10))
        entry = tk.Entry(win)
        entry.pack(fill = "x", padx = 10)
        tk.Button(
            win, 
            text = "OK", 
            width = 10,    # Width in characters
            height = 1,    # Height in text lines
            command = lambda: self.on_confirm(
                raw_input = entry.get(), 
                input_path = input_path, 
                win = win
            )
        ).pack(pady = 12)
        

    def on_confirm(self, *, raw_input: str, input_path: str, win: tk.Toplevel) -> None:
        # Parse string input into a list of page indices
        pages = get_pages(raw = raw_input.strip())

        if pages is None:
            messagebox.showwarning(
                "Invalid Input", 
                "Please use the correct format (e.g., 1-5, 8, 10-12).",
                parent = win
            )
            return

        # Validate page numbers against the actual PDF file
        try:
            self.page_extractor.validate_pages(input_path = input_path, pages_to_extract = pages)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent = win)
            return
        except Exception as e:
            messagebox.showerror("File Error", f"Could not read PDF: {e}", parent = win)
            return

        # Ask user for the output destination
        output_path = filedialog.asksaveasfilename(
            defaultextension = ".pdf",
            filetypes = [("PDF files", "*.pdf")],
            initialfile = f"extracted_{Path(input_path).stem}.pdf",
            title = "Save PDF"
        )

        if not output_path:
            return

        # Close input window and start the background worker thread
        win.destroy()

        threading.Thread(
            target=self._run_page_extractor_worker,
            kwargs={
                "input_path": input_path, 
                "pages": pages, 
                "output_path": output_path
            },
            daemon=True
        ).start()

    def _run_page_extractor_worker(self, input_path, pages, output_path):
        try:
            self.page_extractor.extract_pages(input_path = input_path, pages_to_extract = pages, output_path = output_path, callback = self.callback.safe_callback)
            self.callback.show_status_message(f"✅ Extraction completed successfully! Extracted pages saved to:\n{output_path}")

        except Exception as e:
            error_msg = f" Error during page extraction: {e}"
            if isinstance(e, ValueError):
                self.after(0, lambda: messagebox.showerror("Extraction Error", error_msg))
            else:   
                self.callback.show_status_message(f"❌ {error_msg}")
            
def run_gui():
    app = PDFMergerGUI()
    app.mainloop()