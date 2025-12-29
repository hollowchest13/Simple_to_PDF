from importlib.metadata import files
import tkinter as tk
from tkinter import ttk
import threading
from tkinter import filedialog, messagebox
from src.simple_to_pdf.pdf import PdfMerger, PdfSpliter

class PDFMergerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.build_gui()

         # PDF Merger instance
        self.merger = PdfMerger()
        self.spliter = PdfSpliter()

    def build_gui(self):
        win_size = "600x400"
        win_title = "Simple to PDF - PDF Merger"
        self.title(win_title)
        self.geometry(win_size)
        self._build_top_controls_area()
        self._build_right_controls_area()
        self._build_widgets_area()
       
        
    def _build_widgets_area(self):
        self.widgets_area = tk.Frame(self)
        self.widgets_area.pack(side = "left",fill = "both", expand = True)
        self._build_file_batch_area(parent = self.widgets_area)
        self._build_status_area(parent = self.widgets_area)
        self._build_progress_bar(parent = self.widgets_area)

    def _build_file_batch_area(self,*, parent: tk.Frame):
         # File_batch_area:

        mid = tk.Frame(parent)
        mid.pack(fill = "both", expand = True, padx = 4, pady = 8)

        self.listbox = tk.Listbox(mid, selectmode = "multiple")
        self.listbox.pack(side = "left", fill = "both", expand = True)

    def _build_top_controls_area(self):
        # Top button panel

        top = tk.Frame(self)
        top.pack(fill = "x", padx = 4, pady = 8)
        btns_padx = 4

        tk.Button(top, text = "Add files", command = self.add_files).pack(side = "left", padx = btns_padx)
        tk.Button(top, text = "Remove files", command = self.remove_files).pack(side = "left", padx = btns_padx)
        tk.Button(top, text = "Merge PDFs", command = self.on_merge).pack(side = "left", padx = btns_padx)
        tk.Button(top,text = "Get pages from pdf", command = self.extract_pages).pack(side = "left", padx = btns_padx)

    def _build_status_area(self,*, parent: tk.Frame):

        """Creates a text field for logs between mid and the progress bar"""

        self.status_frame = tk.Frame(parent)
        self.status_frame.pack(fill = "x", padx = 4, pady = 8)
        self.status_text = tk.Text(
            self.status_frame,
            height = 5,
            state = "disabled",
            font = ("Consolas",9),
            bg = "#f0f0f0"
        )
        self.status_text.pack(side = "left", fill = "x", expand = True)

        scrollbar = tk.Scrollbar(self.status_frame, command = self.status_text.yview)
        scrollbar.pack(side = "right", fill = "y")
        self.status_text.config(yscrollcommand=scrollbar.set)

    def _build_progress_bar(self,*, parent: tk.Frame):
        
        """Method to initialize progress elements"""

        self.progress_frame = tk.Frame(parent)
        self.progress_frame.pack(side = "bottom", fill="x", padx = 4, pady = 4)
        self.progress_label = tk.Label(self.progress_frame, text = "Progress:")
        self.progress_label.pack(pady = 4)
        self.progress_bar= ttk.Progressbar(self.progress_frame, 
            orient = "horizontal",
            mode = "determinate",
            length = 400
        )
        self.progress_bar.pack(pady = 8, fill="x")

    def progress_bar_update(self, *, current: int, total: int, filename: str = ""):
       
       """Update progress bar and status text"""

       # division by zero protection
       if total <= 0:
           percent = 0
       else:
           percent = (current / total) * 100

       # Update the widget
       self.progress_bar['value'] = percent

       # Form the status text
       # Filename[:30]... — truncate long names to avoid GUI overflow
       display_name = (filename[:27] + '...') if len(filename) > 30 else filename
       status_text = f"Processing: {display_name} ({current}/{total}) — {percent:.1f}%"
    
       self.progress_label.config(text=status_text)

       # Add log entry to the new log field (if it exists)
       if filename:
           self.log_message(f"Processed: {filename}")

        # Force window update (to prevent "hanging")
       self.update_idletasks()

    def _build_right_controls_area(self):

        # Right button panel
        frame_padx = 4
        frame_pady = 8
        right_controls = tk.Frame(self)
        right_controls.pack(side = "right", fill = "y", padx = frame_padx, pady = frame_pady)
        btns_width = 3
        btns_pady = 2
        tk.Button(right_controls, text = "▲", width = btns_width, command = lambda: self.move_on_listbox(direction = "up")).pack(pady = btns_pady)
        tk.Button(right_controls, text = "▼", width = btns_width, command = lambda: self.move_on_listbox(direction = "down")).pack(pady = btns_pady)
    
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
            return filedialog.askopenfilenames(filetypes=filters)
        return filedialog.askopenfilename(filetypes=filters)


    # Add files to the listbox
    def add_files(self):
        """Add files of selected types."""
        # Just list the extensions we need
        types = ("xls", "xlsx", "doc", "docx", "jpg", "png", "pdf")

        # Call the method. It will create both "All supported" and "All files"
        files_paths = self._get_files(filetypes=types, multiple=True)
        
        if files_paths: 
            self._list_update(files=files_paths)
    
    def remove_files(self) -> None:
        all_files = list(self.listbox.get(0,tk.END))
        sel_files = self._get_selected_values()
        if not sel_files:
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

    # Merge selected PDFs
    def on_merge(self):

        """Handler for Merge button click"""

        # 1. Preparing data (quick operation, doing in main thread)
        files = self._load_from_listbox()
    
        if not files:
            messagebox.showwarning("Warning", "No files to merge")
            return
    
        out = filedialog.asksaveasfilename(
        title = "Save Merged PDF", 
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not out: 
            return

        # 2. Block the button, so user doesn't click twice
        # Assume your button is stored in self.btn_merge
        # self.btn_merge.config(state="disabled") 

        # 3. START THREAD
        # Pass data (files and out) via args
        thread = threading.Thread(
            target = self._run_merge_worker, 
            args = (files, out), 
            daemon = True
        )
        thread.start()
        
    def _run_merge_worker(self,*, files, output_path):

        """Method for working in background thread"""

        try:
            total = len(files)
        
            # Make a special wrapper function for progress, 
            # which we will pass to your merger object
            def update_callback(current, filename):
                self.progress_bar_update(current = current, total = total, filename = filename)

            # Call your merge logic
            # Make sure the merge_to_pdf method can call the callback!
            self.merger.merge_to_pdf(
                files = files, 
                output_path = output_path,
                callback = update_callback # give my function to update progress
            )

            # When all is ready — show success (via main thread)
            self.after(0, lambda: messagebox.showinfo("Success", f"Merged file:\n{output_path}"))
        
        except Exception as e:
            # Show error
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        finally:
            # Unblock the interface in any case
            # self.after(0, lambda: self.btn_merge.config(state = "normal"))
            # Reset the progress bar to 0
            self.after(0, lambda: self.progress_bar_update(current = 0, total=100, filename = "Ready"))

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
        input_path: str = self._get_files(filetype = ".pdf", multiple = False)
        win = tk.Toplevel(self)
        win.title("Remove PDF")
        win.geometry("300x150")
        win.transient(self)
        win.grab_set()

        # Create a label and entry for page selection
        tk.Label(win, text = "Select pages to remove:").pack(pady=20)
        entry = tk.Entry(win)
        entry.pack(fill = "x", padx=10)
        tk.Button(win, text = "OK", command = lambda: self.on_confirm(raw_input = entry.get(), input_path = input_path, win = win)).pack(pady = 12)
        

    def on_confirm(self,*, raw_input: str, input_path: str, win: tk.Toplevel) -> None:

        pages = self._get_pages(raw = raw_input.strip())

        if pages is None:
            messagebox.showerror("Error", "Invalid page range format")
            return

        # If no input path is selected, show a warning
        if not input_path:
            messagebox.showwarning("No file", "Please select a PDF to extract pages from.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension = ".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="removed_pages.pdf",
            title="Save PDF")
        
        if not output_path:
            return
        try:
            self.spliter.extract_pages(input_path = input_path, pages_to_extract = pages, output_path = output_path)
            messagebox.showinfo("Success", f"Saved to:\n{output_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            
        finally:
            win.destroy()
    
def run_gui():
    app = PDFMergerGUI()
    app.mainloop()