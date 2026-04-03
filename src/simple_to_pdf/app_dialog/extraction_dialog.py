import customtkinter as ctk
from typing import Dict
from simple_to_pdf.widgets.base_widgets import BaseLabel, PrimaryButton
from .base_dialog import BaseDialog

class PageSelectionDialog(BaseDialog):
    """
    Dialog for inputting specific page ranges to extract from a PDF.
    Fully integrated with the localization system.
    """

    def __init__(self, parent):
        # Pass localization section to BaseDialog
        # BaseDialog will handle init_localization and observer registration
        super().__init__(
            parent, 
            loc_section="ui.page_selection_dialog", 
            title="window_title"
        )

        self.geometry("400x380")
        self.resizable(False, False)
        self.result = None

        # Setup UI and register widgets for automatic translation
        self._setup_dialog_ui()
        
        # Initial call to populate labels from JSON
        self.refresh_localization()

    def _setup_dialog_ui(self) -> None:
        """Creates widgets and maps them to self.ui for the LocalizationMixin."""
        
        # --- Header Section ---
        # BaseDialog helper creates the title and subtitle in self.header
        self.set_header_text("Page Selection", "Extract specific pages from PDF")
        header_children = self.header.winfo_children()
        if len(header_children) >= 2:
            self.ui["header_title"] = header_children[0]
            self.ui["header_subtitle"] = header_children[1]

        # --- Content Section ---
        # Main instruction label
        self.ui["instruction_label"] = BaseLabel(
            self.content,
            text="", # Populated via JSON
            label_type="title",
            anchor="center",
        )
        self.ui["instruction_label"].pack(pady=(0, 5), fill="x")

        # Formatting hint label
        self.ui["hint_label"] = BaseLabel(
            self.content, 
            text="", 
            label_type="subtitle", 
            anchor="center"
        )
        self.ui["hint_label"].pack(pady=(0, 15), fill="x")

        # Input field (registered in self.ui for placeholder_text translation)
        self.entry = ctk.CTkEntry(self.content, height=35)
        self.entry.pack(fill="x", pady=(0, 20))
        self.ui["page_entry"] = self.entry

        # Confirm button
        self.btn_ok = PrimaryButton(
            self.content, 
            text="", 
            command=self._on_ok, 
            height=40
        )
        self.btn_ok.pack(fill="x")
        self.ui["btn_ok"] = self.btn_ok

        # --- Footer Section ---
        self.ui["footer_note"] = BaseLabel(
            self.footer,
            text="",
            label_type="badge",
        )
        self.ui["footer_note"].pack()

        # Keyboard accessibility
        self.entry.focus_set()
        self.bind("<Return>", lambda event: self._on_ok())

    def _on_ok(self, event=None):
        """Save input and clean up before closing."""
        self.result = self.entry.get().strip()
        # Important: BaseDialog._on_close handles remove_from_observers()
        self._on_close()

    def get_input(self):
        """Display the dialog as modal and wait for user input."""
        self.wait_window(self)
        return self.result