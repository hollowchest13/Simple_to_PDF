import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfReader, PdfWriter
from src.converter import merge_pdfs, export_to_pdf
from src.converter.pages_remover import remove_from_pdf
from pathlib import Path

class PDFMergerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Merger")
        self.geometry("600x350")
        self.build_widgets()

    def build_widgets(self):

        # Top button panel

        top = tk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        tk.Button(top, text="Add PDFs",   command=self.add_pdfs).pack(side="left", padx=4)
        tk.Button(top, text="Remove PDF", command=self.remove_from_list).pack(side="left", padx=4)
        tk.Button(top, text="Merge PDFs", command=self.on_merge).pack(side="left", padx=4)
        tk.Button(top, text="Export",     command=self.on_export).pack(side="left", padx=4)
        tk.Button(top,text="Remove pages",command=self.open_remove_dialog).pack(side="left", padx=4)
        
        # Central part:

        mid = tk.Frame(self)
        mid.pack(fill="both", expand=True, padx=4, pady=8)

        self.listbox = tk.Listbox(mid, selectmode="multiple")
        self.listbox.pack(side="left", fill="both", expand=True)

        ctrl = tk.Frame(mid)
        ctrl.pack(side="right", fill="y", padx=6)
        tk.Button(ctrl, text="▲", width=3, command=self.move_up).pack(pady=2)
        tk.Button(ctrl, text="▼", width=3, command=self.move_down).pack(pady=2)
    
    def add_pdfs(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF files", filetypes=[("PDF Files","*.pdf")]
        )
        for p in paths:
            if p not in self.listbox.get(0, tk.END):
                self.listbox.insert(tk.END, p)

    def remove_from_list(self):
        sel = self.listbox.curselection()
        if not sel:
            answer=messagebox.askyesno(
                "No PDF selected.",
                "No PDF selected. Do you want to remove all PDFs?"
            )
            if answer:
                self.listbox.delete(0, tk.END)
                return
        for idx_str in reversed(sel):
            self.listbox.delete(int(idx_str))
        return

    def move_up(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0:
            return
        
        # Deselect all

        self.listbox.selection_clear(0, tk.END)
        for idx in sel:
            if idx == 0:
                continue
            val = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(idx - 1, val)

        # Reselect moved items

        for idx in [i - 1 for i in sel if i != 0]:
            self.listbox.select_set(idx)

    def move_down(self):
        sel = self.listbox.curselection()
        last = self.listbox.size() - 1
        if not sel or sel[-1] == last:
            return
        
        # Deselect all

        self.listbox.selection_clear(0, tk.END)
        for idx in reversed(sel):
            if idx == last:
                continue
            val = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(idx + 1, val)

        # Reselect moved items
        
        for idx in [i + 1 for i in sel if i != last]:
            self.listbox.select_set(idx)

    def on_merge(self):
        pdfs = list(self.listbox.get(0, tk.END))
        if not pdfs:
            messagebox.showwarning("Warning", "No PDFs to merge")
            return

        out = filedialog.asksaveasfilename(
            title="Save Merged PDF", defaultextension=".pdf",
            filetypes=[("PDF Files","*.pdf")]
        )
        if not out: return

        try:
            merge_pdfs(pdfs, out)
            messagebox.showinfo("Success", f"Merged file:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def remove_from_pdf(input_path: str, pages_to_remove: list[int], output_path: str) -> None:

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
        output_path.parent.mkdir(parents=True, exist_ok=True)

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
        
    def open_remove_dialog(self):
        win= tk.Toplevel(self)
        win.title("Remove PDF")
        win.geometry("300x150")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Select pages to remove:").pack(pady=8)
        entry = tk.Entry(win)
        entry.pack(fill="x", padx=10)

        def on_confirm():
            raw = entry.get().strip()
            pages = self.parse_pages(raw)
            if pages is None:
                messagebox.showerror("Error", "Invalid page range format")
                return

            input_path = self.manager.get_selected()  # або будь-який спосіб вибрати PDF
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
            export_to_pdf(files, save_to)
            messagebox.showinfo("Success", f"Exported to:\n{save_to}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

def run_gui():
    app = PDFMergerGUI()
    app.mainloop()

if __name__ == "__main__":
    run_gui()