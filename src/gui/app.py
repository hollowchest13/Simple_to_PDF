import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfReader, PdfWriter
from src.converter import PdfManager
from pathlib import Path

class PDFMergerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Merger")
        self.geometry("600x350")
        self.build_widgets()
        self.merger = PdfManager()

    def build_widgets(self):

        # Top button panel

        top = tk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        tk.Button(top, text="Add PDFs",   command=self.add_pdf).pack(side="left", padx=4)
        tk.Button(top, text="Remove PDF", command=self.remove_pdf).pack(side="left", padx=4)
        tk.Button(top, text="Merge PDFs", command=self.on_merge).pack(side="left", padx=4)
        tk.Button(top, text="Export",     command=self.on_export).pack(side="left", padx=4)
        tk.Button(top,text="Get pages",   command=self.open_dialog).pack(side="left", padx=4)

        # Central part:

        mid = tk.Frame(self)
        mid.pack(fill="both", expand=True, padx=4, pady=8)

        self.listbox = tk.Listbox(mid, selectmode="multiple")
        self.listbox.pack(side="left", fill="both", expand=True)

        ctrl = tk.Frame(mid)
        ctrl.pack(side="right", fill="y", padx=6)
        tk.Button(ctrl, text="▲", width=3, command=lambda: self.move_on_listbox(direction="up")).pack(pady=2)
        tk.Button(ctrl, text="▼", width=3, command=lambda: self.move_on_listbox(direction="down")).pack(pady=2)
    
    def load_from_listbox(self) -> list[str]:
        if not self.listbox.size():
            return []
        return list(self.listbox.get(0, tk.END))
    
    def get_list_selected(self) -> list[str]:
        selection = self.listbox.curselection()
        if not selection:
            return []
        return [(self.listbox.get(i)) for i in self.listbox.curselection()]
    
    def listbox_clear(self) -> None:
        self.listbox.delete(0, tk.END)

    def list_update(self,*,files: list[str]) -> None:
        self.listbox_clear()
        self.merger.add_pdf(files)
        for pdf in files:
            self.listbox.insert(tk.END, pdf)
  
    def reselect_items(self, selected_values:list[str], updated_list:list[str])->None:
        self.listbox.selection_clear(0, tk.END)
        for i,value in enumerate(updated_list):
            if value in selected_values:
                self.listbox.select_set(i)

    def add_pdf(self):
        files_paths = filedialog.askopenfilenames(
            title="Select PDF files", filetypes=[("PDF Files","*.pdf")]
        )
        self.list_update(files=files_paths)
    
    def remove_pdf(self):
        sel = self.get_list_selected()
        if not sel:
            answer=messagebox.askyesno(
                "No PDF selected.",
                "No PDF selected. Do you want to remove all PDFs?"
            )
            if answer:
                self.listbox_clear()
                return
        new_file_list= self.merger.remove_from_list(selected_list=sel, files_list=self.load_from_listbox())
        self.list_update(files=new_file_list)

    def move_on_listbox(self,*,direction: str = "up"):
        sel_indexes = self.listbox.curselection()
        selected_values = self.get_list_selected()

        # Deselect all
        self.listbox.selection_clear(0, tk.END)
        new_files=self.merger.move_on_list(files=self.load_from_listbox(),selected_idx=sel_indexes, direction=direction)
        self.list_update(files=new_files)

        # Reselect moved items
        self.reselect_items(selected_values = selected_values, updated_list=new_files)

    def on_merge(self):
        pdfs = list(self.listbox.get(0, tk.END))

        # Warn if no PDFs selected
        if not pdfs:
            messagebox.showwarning("Warning", "No PDFs to merge")
            return
        
        # Ask for output file
        out = filedialog.asksaveasfilename(
            title="Save Merged PDF", defaultextension=".pdf",
            filetypes=[("PDF Files","*.pdf")]
        )
        if not out: return

        # Attempt to merge PDFs
        try:
            self.merger.merge_pdfs(pdfs, out)
            messagebox.showinfo("Success", f"Merged file:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def remove_from_pdf(self,input_path: str, pages_to_remove: list[int], output_path: str) -> None:

       # Load the PDF file for reading
        reader = PdfReader(input_path)
        writer = PdfWriter()
        total_pages = len(reader.pages)

        # Normalize page numbers to 0-based index and filter invalid entries
        pages_to_remove = {p - 1 for p in pages_to_remove if 1 <= p <= total_pages}

        # Raise an error if all pages are being removed
        if len(pages_to_remove) == total_pages:
            raise ValueError("Cannot remove all pages from a PDF")

        # Add only pages that are not marked for removal
        for i, page in enumerate(reader.pages):
            if i not in pages_to_remove:
                writer.add_page(page)

        # Ensure the output directory exists
        output_path = Path(output_path)
        
        # Write the new PDF file
        with open(output_path, "wb") as f:
            writer.write(f)

    def parse_pages(self, raw: str) -> list[int] | None:
        pages = []
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
        
    def open_dialog(self):
        sel = self.listbox.curselection()

        # If no item is selected, show a warning
        if not sel:
            messagebox.showwarning("No PDF selected", "Please select a PDF to remove pages from.")
            return
        win= tk.Toplevel(self)
        win.title("Remove PDF")
        win.geometry("300x150")
        win.transient(self)
        win.grab_set()

        # Create a label and entry for page selection
        tk.Label(win, text="Select pages to remove:").pack(pady=8)
        entry = tk.Entry(win)
        entry.pack(fill="x", padx=10)

        def on_confirm():
            raw = entry.get().strip()
            pages = self.parse_pages(raw)
            if pages is None:
                messagebox.showerror("Error", "Invalid page range format")
                return

            input_path = self.listbox.get(sel[0])

            # або будь-який спосіб вибрати PDF

            if not input_path:
                messagebox.showwarning("No file", "Please select a PDF to remove pages from.")
                return

            output_path = filedialog.asksaveasfilename(defaultextension=".pdf")
            if not output_path:
                return

            try:
                self.remove_from_pdf(input_path, pages, output_path)
                messagebox.showinfo("Success", f"Saved to:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                win.destroy()

        tk.Button(win, text="OK", command=on_confirm).pack(pady=12)
        
    def on_export(self):
        files = filedialog.askopenfilenames(
            title="Select files to export", filetypes=[("All files","*.*")]
        )
        if not files:
            return

        save_to = filedialog.asksaveasfilename(
            title="Save Export", defaultextension=".pdf",
            filetypes=[("PDF Files","*.pdf")]
        )
        if not save_to:
            return

        try:
            self.merger.export_to_pdf(files, save_to)
            messagebox.showinfo("Success", f"Exported to:\n{save_to}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

def run_gui():
    app = PDFMergerGUI()
    app.mainloop()

if __name__ == "__main__":
    run_gui()