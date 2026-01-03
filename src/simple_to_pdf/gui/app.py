from importlib.metadata import files
import tkinter as tk
from tkinter import ttk
import threading
from tkinter import filedialog, messagebox
from src.simple_to_pdf.pdf import PdfMerger, PdfSpliter
from src.simple_to_pdf.gui.gui_builder import GUIBuilder
from src.simple_to_pdf.gui.gui_callback import GUICallback

class PDFMergerGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        handlers = {
            'add': self.add_files,
            'merge': self.on_merge,
            'extract': self.extract_pages,
            'remove': self.remove_files,
            'move': self.move_on_listbox  # Твій метод для ▲/▼
        }
        builder = GUIBuilder()
        self.ui = builder.build_gui(self, handlers)
        self.listbox: tk.Listbox = self.ui['listbox']
        self.progress_bar: ttk.Progressbar = self.ui['progress_bar']
        self.status_text: tk.Text = self.ui['status_text']
        self.btn_merge: tk.Button = self.ui['btn_merge']
        self.btn_split: tk.Button = self.ui['btn_extract']
        self.btn_remove: tk.Button = self.ui['btn_remove']
        self.btn_add: tk.Button = self.ui['btn_add']
        self.btn_up: tk.Button = self.ui['btn_up']
        self.btn_down: tk.Button = self.ui['btn_down']
        self.callback = GUICallback(main_app = self)
        self.merger = PdfMerger()
        self.spliter = PdfSpliter()
    
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

    def _get_files(self, *, filetypes: tuple[str, ...] = ("pdf",), multiple = True):

        """
        Open dialog window to select files.

        """
        # Create mask for all extensions together: "*.pdf *.docx *.xlsx"
        all_supported_mask = " ".join([f"*.{ext}" for ext in filetypes])
        
        # Form the list of filters
        # 1. First item — all supported types together
        filters = [("All supported types", all_supported_mask)]
        
        # 2. Then each type separately (for convenience)
        for ext in filetypes:
            filters.append((f"{ext.upper()} files", f"*.{ext}"))
            
        # 3. Finally — all files
        filters.append(("All files", "*.*"))

        if multiple:
            return filedialog.askopenfilenames(filetypes = filters)
        return filedialog.askopenfilename(filetypes = filters)


    # Add files to the listbox
    def add_files(self):

        """Add files of selected types."""

        # Supported list the extensions 
        types = ("xls", "xlsx", "doc", "docx", "jpg", "png", "pdf")

        # Call the method. It will create both "All supported" and "All files"
        files_paths = self._get_files(filetypes = types, multiple = True)
        
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

        # 2. Block the button, so user doesn't click twice
        # Assume button is stored in self.btn_merge
        self.btn_merge.config(state = "disabled") 

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

            #In the end, we can show a final message
            self.after(0, lambda: self.callback.show_status_message("✅ All files merged successfully!"))
        except Exception as e:
            self.after(0, lambda: self.callback.show_status_message(f"❌ Error: Could not merge files:\n{e}"))
        
        finally:
            self.after(0, lambda: self.btn_merge.config(state = "normal"))

    def _get_pages(self,*, raw: str) -> list[int] | None:
        pages:list[int] = []
        try:
            for part in raw.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.extend(range(start - 1, end))  # Convert to 0-based index
                else:
                    pages.append(int(part) - 1)  # Convert to 0-based index
            return pages
        except ValueError:
            return None
        
    def extract_pages(self):
        input_path: str = self._get_files(filetypes = ".pdf", multiple = False)

        if not input_path:
            return
        
        win = tk.Toplevel(self)
        win.title("Remove PDF")
        win.geometry("300x150")
        win.transient(self)
        win.grab_set()

        # Create a label and entry for page selection
        tk.Label(win, text = "Select pages to remove:").pack(pady = 20)
        entry = tk.Entry(win)
        entry.pack(fill = "x", padx = 10)
        tk.Button(win, text = "OK", command = lambda: self.on_confirm(raw_input = entry.get(), input_path = input_path, win = win)).pack(pady = 12)
        

    def on_confirm(self,*, raw_input: str, input_path: str, win: tk.Toplevel) -> None:

        pages = self._get_pages(raw = raw_input.strip())

        if pages is None:
            messagebox.showwarning(
                "Invalid Input", 
                 "Please use the correct format for page ranges (e.g., 1-5, 8, 10-12)."
            )
            return

        # If no input path is selected, show a warning
        if not input_path:
            messagebox.showwarning(
               "No file", 
               "Please select a PDF to extract pages from."
            )
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension = ".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile ="removed_pages.pdf",
            title = "Save PDF")
        
        if not output_path:
            return
        try:
            self.spliter.extract_pages(input_path = input_path, pages_to_extract = pages, output_path = output_path)
            self.callback.show_status_message("Success", f"Saved to:\n{output_path}")
            win.destroy()

        except Exception as e:
            self.callback.show_status_message("Error", f"Failed to extract pages: {e}")
            
def run_gui():
    app = PDFMergerGUI()
    app.mainloop()