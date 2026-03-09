import customtkinter as ctk
from simple_to_pdf.widgets.base_widgets import BaseLabel, PrimaryButton
from .base_dialog import BaseDialog


class PageSelectionDialog(BaseDialog):
    def __init__(self, parent):
        # Initialize base layout (header, content, footer)
        super().__init__(parent, title="Extract Pages")

        self.geometry("400x380")
        self.resizable(False, False)
        self.result = None

        # Setup header area
        self.set_header_text("Page Selection", "Extract specific pages from PDF")

        # Main instruction label
        BaseLabel(
            self.content,
            text="Enter pages to extract:",
            label_type="title",
            anchor="center",
        ).pack(pady=(0, 5), fill="x")

        # Formatting hint label
        hint_text = "Use commas for single pages (1, 3)\nand dashes for ranges (5-10)."
        BaseLabel(
            self.content, text=hint_text, label_type="subtitle", anchor="center"
        ).pack(pady=(0, 15), fill="x")

        # Input field
        self.entry = ctk.CTkEntry(
            self.content, placeholder_text="e.g. 1, 2, 5-8", height=35
        )
        self.entry.pack(fill="x", pady=(0, 20))

        # Confirm button
        self.btn_ok = PrimaryButton(
            self.content, text="Confirm Extraction", command=self._on_ok, height=40
        )
        self.btn_ok.pack(fill="x")

        # Footer information
        BaseLabel(
            self.footer,
            text="Make sure the page numbers exist in the document.",
            label_type="badge",
        ).pack()

        # Keyboard accessibility
        self.entry.focus_set()
        self.bind("<Return>", lambda event: self._on_ok())

    def _on_ok(self, event=None):
        """Save input and close the dialog."""
        self.result = self.entry.get().strip()
        self.destroy()

    def get_input(self):
        """Display the dialog and wait for user input."""
        self.update_idletasks()
        self.update()
        self.wait_window(self)
        return self.result
