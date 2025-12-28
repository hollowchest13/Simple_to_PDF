import tkinter as tk
from tkinter import filedialog, messagebox
from ..pdf import PdfMerger, PdfSpliter

class PDFMergerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Merger")
        self.geometry("600x350")
        self.build_widgets()
        self.merger = PdfMerger()
        self.spliter = PdfSpliter()
       

    def build_widgets(self):

        # Top button panel

        top = tk.Frame(self)
        top.pack(fill = "x", padx = 8, pady = 8)
        btns_padx = 4

        tk.Button(top, text="Add files",command=self.add_files).pack(side="left", padx = btns_padx)
        tk.Button(top, text="Remove files",command=self.remove_files).pack(side="left", padx = btns_padx)
        tk.Button(top, text="Merge PDFs", command=self.on_merge).pack(side="left", padx = btns_padx)
        tk.Button(top,text="Get pages from pdf", command=self.extract_pages).pack(side="left", padx = btns_padx)

        # Central part:

        mid = tk.Frame(self)
        mid.pack(fill = "both", expand = True, padx = 4, pady = 8)

        self.listbox = tk.Listbox(mid, selectmode = "multiple")
        self.listbox.pack(side = "left", fill = "both", expand = True)

        ctrl = tk.Frame(mid)
        btns_width=3
        ctrl.pack(side = "right", fill = "y", padx = 6)
        tk.Button(ctrl, text = "▲", width = btns_width, command = lambda: self.move_on_listbox(direction="up")).pack(pady = 2)
        tk.Button(ctrl, text = "▼", width = btns_width, command = lambda: self.move_on_listbox(direction="down")).pack(pady = 2)
    
    def load_from_listbox(self) -> list[tuple[int,str]]:
        result:list[tuple[int,str]]=[]
        if self.listbox.size() == 0:
            return result
        for i in range(self.listbox.size()):
            text=self.listbox.get(i)
            result.append((i,text))
        return result
    
    def get_selected_values(self) -> list[str]:
        selection = self.listbox.curselection()
        if not selection:
            return []
        return [(self.listbox.get(i)) for i in self.listbox.curselection()]
    
    def listbox_clear(self) -> None:
        self.listbox.delete(0, tk.END)

   # List Updating
    def list_update(self,*,files: list[str]) -> None:
        self.listbox_clear()
        for pdf in files:
            self.listbox.insert(tk.END, pdf)
    
    # Reselect items after update
    def reselect_items(self,*, all_items, selected_values):
        self.listbox.selection_clear(0, tk.END)
        for idx, val in enumerate(all_items):
            if val in selected_values:
                self.listbox.selection_set(idx)

    def get_files(self, *, filetypes: tuple[str, ...] = ("pdf",), multiple=True):
        """
        Open a file dialog to select files.

        Args:
            filetypes: список або кортеж розширень, наприклад ("pdf", "docx", "xlsx")
            multiple: якщо True — можна вибрати кілька файлів

        Returns:
            str якщо multiple=False і вибрано один файл
            tuple[str] якщо multiple=True
            None якщо користувач натиснув Cancel
        """
        filters = [(f"{ext.upper()} files", f"*.{ext}") for ext in filetypes]
        filters.append(("All files", "*.*"))

        if multiple:
            file_paths = filedialog.askopenfilenames(
                title = "Select files",
                filetypes = filters
            )
            return file_paths or None
        else:
            file_path = filedialog.askopenfilename(
                title = "Select file",
               filetypes = filters
            )
            return file_path or None


    # Add files to the listbox
    def add_files(self):
        filetypes: tuple[str,...] = ("xls","xlsx","doc","docx","jpg","png","pdf")
        files_paths = self.get_files(filetypes = filetypes, multiple = True)
        if files_paths: 
            self.list_update(files = files_paths)
    
    def remove_files(self) -> None:
        all_files = list(self.listbox.get(0,tk.END))
        sel_files = self.get_selected_values()
        if not sel_files:
            answer = messagebox.askyesno(
                "No files.",
                "No files selected. Do you want to remove all files?"
            )
            if answer:
                self.listbox_clear()
                return 
        for file in sel_files:
            if file in all_files:
                all_files.remove(file)
        self.list_update(files = all_files)
       
    # Move selected items in the listbox
    def move_on_listbox(self,*, direction: str):
        sel_idxs = sorted(self.listbox.curselection())
        if not sel_idxs:
            return

        items = self.listbox.get(0, tk.END)
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

        self.list_update(files = items)
        self.reselect_items(all_items = items, selected_values = selected_values)

    # Merge selected PDFs
    def on_merge(self):
        files: list[tuple[int,str]] = []
        files.extend(self.load_from_listbox())
        
        # Warn if no PDFs selected
        if not files:
            messagebox.showwarning("Warning", "No files to merge")
            return
        
        # Ask for output file
        out = filedialog.asksaveasfilename(
            title = "Save Merged PDF", defaultextension = ".pdf",
            filetypes = [("PDF Files","*.pdf")]
        )
        if not out: return

        # Attempt to merge PDFs
        try:
            self.merger.merge_to_pdf(files = files, output_path = out)
            messagebox.showinfo("Success", f"Merged file:\n{out}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_pages(self,*, raw: str) -> list[int] | None:
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
        input_path: str = self.get_files(filetype = ".pdf", multiple = False)
        win = tk.Toplevel(self)
        win.title("Remove PDF")
        win.geometry("300x150")
        win.transient(self)
        win.grab_set()

        # Create a label and entry for page selection
        tk.Label(win, text = "Select pages to remove:").pack(pady=20)
        entry = tk.Entry(win)
        entry.pack(fill = "x", padx=10)
        tk.Button(win, text = "OK", command = lambda: self.on_confirm(raw_input = entry.get(), input_path = input_path, win = win)).pack(pady=12)
        

    def on_confirm(self,*, raw_input: str, input_path: str, win: tk.Toplevel) -> None:

        pages = self.get_pages(raw = raw_input.strip())

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