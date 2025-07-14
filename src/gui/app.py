import tkinter as tk
from tkinter import filedialog, messagebox
from src.converter import merge_pdfs, export_to_pdf

class PDFMergerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Merger")
        self.geometry("600x350")
        self.build_widgets()

    def build_widgets(self):
        # ── Верхня панель кнопок ────────────────────
        top = tk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        tk.Button(top, text="Add PDFs",   command=self.add_pdfs).pack(side="left", padx=4)
        tk.Button(top, text="Remove PDF", command=self.remove_pdf).pack(side="left", padx=4)
        tk.Button(top, text="Merge PDFs", command=self.on_merge).pack(side="left", padx=4)
        tk.Button(top, text="Export",     command=self.on_export).pack(side="left", padx=4)

        # ── Центральна частина: список + керування ───
        mid = tk.Frame(self)
        mid.pack(fill="both", expand=True, padx=4, pady=8)

        self.listbox = tk.Listbox(mid, selectmode="single")
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

    def remove_pdf(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "No file selected")
            return
        self.listbox.delete(sel)

    def move_up(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0: return
        i = sel[0]
        val = self.listbox.get(i)
        self.listbox.delete(i)
        self.listbox.insert(i-1, val)
        self.listbox.select_set(i-1)

    def move_down(self):
        sel = self.listbox.curselection()
        last = self.listbox.size() - 1
        if not sel or sel[0] == last: return
        i = sel[0]
        val = self.listbox.get(i)
        self.listbox.delete(i)
        self.listbox.insert(i+1, val)
        self.listbox.select_set(i+1)

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

def main():
    app = PDFMergerGUI()
    app.mainloop()