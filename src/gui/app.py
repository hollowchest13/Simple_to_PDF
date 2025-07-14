import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfMerger
from src.converter.merger import merge_pdfs

class PDFMergerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Merger")
        self.geometry("600x350")
        self.build_widgets()

    def build_widgets(self):
        # Верхня панель з кнопками
        top = tk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)
        tk.Button(top, text="Add PDFs",   command=self.add_pdfs).pack(side="left", padx=4)
        tk.Button(top, text="Remove PDF", command=self.remove_pdf).pack(side="left", padx=4)
        tk.Button(top, text="Merge PDFs", command=self.merge_pdfs).pack(side="left", padx=4)

        # Центральна частина: список + кнопки переміщення
        mid = tk.Frame(self)
        mid.pack(fill="both", expand=True, padx=4, pady=8)

        self.listbox = tk.Listbox(mid, selectmode="single")
        self.listbox.pack(side="left", fill="both", expand=True)

        ctrl = tk.Frame(mid)
        ctrl.pack(side="right", fill="y", padx=6)
        tk.Button(ctrl, text="▲", width=3, command=self.move_up).pack(pady=2)
        tk.Button(ctrl, text="▼", width=3, command=self.move_down).pack(pady=2)

    def add_pdfs(self):
        files = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF Files", "*.pdf")]
        )
        for f in files:
            if f not in self.listbox.get(0, tk.END):
                self.listbox.insert(tk.END, f)

    def remove_pdf(self):
        idx = self.listbox.curselection()
        if not idx:
            messagebox.showwarning("Warning", "No file selected")
            return
        self.listbox.delete(idx)

    def move_up(self):
        idx = self.listbox.curselection()
        if not idx or idx[0] == 0:
            return
        i = idx[0]
        val = self.listbox.get(i)
        self.listbox.delete(i)
        self.listbox.insert(i-1, val)
        self.listbox.select_set(i-1)

    def move_down(self):
        idx = self.listbox.curselection()
        last = self.listbox.size() - 1
        if not idx or idx[0] == last:
            return
        i = idx[0]
        val = self.listbox.get(i)
        self.listbox.delete(i)
        self.listbox.insert(i+1, val)
        self.listbox.select_set(i+1)

    def merge_pdfs(self):
        pdf_list = list(self.listbox.get(0, tk.END))
        if not pdf_list:
            messagebox.showwarning("Warning", "No files to merge")
            return

        output_file = filedialog.asksaveasfilename(
            title="Save Merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not output_file:
            return

        try:
            merge_pdfs(pdf_list, output_file)
            messagebox.showinfo("Success", "PDFs merged successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to merge PDFs: {e}")

if __name__ == "__main__":
    app = PDFMergerGUI()
    app.mainloop()