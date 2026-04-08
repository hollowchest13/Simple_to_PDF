import customtkinter as ctk
from simple_to_pdf.widgets.base_widgets import BaseLabel, PrimaryButton
from .base_dialog import BaseDialog


class PageSelectionDialog(BaseDialog):
    """
    Dialog for inputting specific page ranges to extract from a PDF.
    Fully integrated with the localization system via BaseDialog and Mixins.
    """

    def __init__(self, parent):
        # Pass localization section and window title key to BaseDialog
        super().__init__(
            parent, loc_section="ui.page_selection_dialog", title_key="window_title"
        )

        self.geometry("400x380")
        self.resizable(False, False)
        self.result = None

        # Setup UI and register widgets for automatic translation
        self._setup_dialog_ui()

        # Initial call to populate labels from JSON (BaseDialog handles this,
        # but calling it here ensures UI is ready)
        self.refresh_localization()

    def _setup_dialog_ui(self) -> None:
        """Creates widgets and maps them to self.ui for the LocalizationMixin."""

        # --- Header Section ---
        # Explicitly creating header labels instead of using deleted helper methods
        self.ui["header_title"] = BaseLabel(
            self.header,
            text="",  # Populated via JSON: "header_title"
            label_type="title",
        )
        self.ui["header_title"].pack(pady=(15, 0))

        self.ui["header_subtitle"] = BaseLabel(
            self.header,
            text="",  # Populated via JSON: "header_subtitle"
            label_type="subtitle",
        )
        self.ui["header_subtitle"].pack(pady=(0, 10))

        # --- Content Section ---
        # Main instruction label
        self.ui["instruction_label"] = BaseLabel(
            self.content,
            text="",  # Populated via JSON: "instruction_label"
            label_type="title",
            anchor="center",
        )
        self.ui["instruction_label"].pack(pady=(10, 5), fill="x")

        # Formatting hint label (e.g., "1, 3, 5-10")
        self.ui["hint_label"] = BaseLabel(
            self.content,
            text="",  # Populated via JSON: "hint_label"
            label_type="subtitle",
            anchor="center",
        )
        self.ui["hint_label"].pack(pady=(0, 20), fill="x")

        # Input field (registered for placeholder_text translation)
        self.entry = ctk.CTkEntry(self.content, height=40, font=("Inter", 13))
        self.entry.pack(fill="x", padx=20, pady=(0, 25))
        self.ui["page_entry"] = self.entry

        # Confirm button
        self.btn_ok = PrimaryButton(
            self.content,
            text="",  # Populated via JSON: "btn_ok"
            command=self._on_ok,
            height=45,
        )
        self.btn_ok.pack(fill="x", padx=20)
        self.ui["btn_ok"] = self.btn_ok

        # Accessibility and focus
        self.entry.focus_set()
        # Bind Enter key to the OK action
        self.bind("<Return>", lambda event: self._on_ok())

    def _on_ok(self, event=None):
        """Save input and close the dialog."""
        user_input = self.entry.get().strip()
        if user_input:
            self.result = user_input

        # This calls BaseDialog._on_close which handles cleanup
        self._on_close()

    def get_input(self) -> str | None:
        """
        Display the dialog as modal and wait for user interaction.
        Returns the entered string or None if cancelled.
        """
        self.wait_window(self)
        return self.result
