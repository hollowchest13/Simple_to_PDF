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
        # Top button panel
        top = tk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        tk.Button(top, text="Add PDFs",   command=self.add_pdfs).pack(side="left", padx=4)
        tk.Button(top, text="Remove PDF", command=self.remove_from_list).pack(side="left", padx=4)
        tk.Button(top, text="Merge PDFs", command=self.on_merge).pack(side="left", padx=4)
        tk.Button(top, text="Export",     command=self.on_export).pack(side="left", padx=4)

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

if __name__ == "__main__":
    main()