import tkinter as tk
from typing import Dict
import webbrowser
from simple_to_pdf.core import config
from simple_to_pdf.app_dialog.base_dialog import BaseDialog
from simple_to_pdf.widgets import BaseFrame, PrimaryButton, BaseLabel


class UpdateDialog(BaseDialog):
    """
    Dialog to notify the user about a new software version.
    Integrated with the centralized localization and observer system.
    """

    def __init__(self, parent, new_version: str, changelog: str):
        # Pass localization section to the base class
        # This registers the dialog as an observer and sets up self.ui
        super().__init__(parent, loc_section="ui.update_dialog", title="window_title")

        self.new_version = new_version
        self.changelog = changelog

        # Create UI and register widgets
        self._setup_dialog_ui()

        # Initial refresh to inject dynamic version and changelog data
        self.refresh_localization()

    def _setup_dialog_ui(self) -> None:
        """Constructs the UI and maps elements to self.ui for auto-updates."""

        # --- Header Section ---
        # Placeholder text, will be formatted in refresh_localization
        self.set_header_text("New Update!", f"Version {self.new_version}")
        header_children = self.header.winfo_children()
        if len(header_children) >= 2:
            self.ui["header_title"] = header_children[0]
            self.ui["header_subtitle"] = header_children[1]

        # --- Content Area ---
        # "What's New" static label
        self.ui["whats_new_title"] = BaseLabel(self.content, text="")
        self.ui["whats_new_title"].pack(anchor="w", pady=(0, 5))

        # Dynamic changelog display
        self.ui["changelog_box"] = BaseLabel(self.content, text="", label_type="badge")
        self.ui["changelog_box"].pack(fill="x", pady=(0, 20))

        # Action buttons layout
        self.btn_frame = BaseFrame(self.content)
        self.btn_frame.pack(fill="x", pady=10)

        # Download Button
        self.ui["btn_download"] = PrimaryButton(
            self.btn_frame, text="", command=self._on_update_click
        )
        self.ui["btn_download"].pack(side="right", padx=5)

        # Later / Close Button
        self.ui["btn_later"] = PrimaryButton(
            self.btn_frame,
            text="",
            command=self._on_close,  # Use base method for clean observer removal
        )
        self.ui["btn_later"].pack(side="right", padx=5)

    def _on_update_click(self):
        """Open the releases page and close the dialog safely."""
        webbrowser.open_new_tab(config.RELEASES_URL)
        self._on_close()

    def refresh_localization(self) -> None:
        """
        Handles translation for static keys and formats dynamic placeholders.
        """
        # Step 1: Translate all standard widgets mapped in self.ui
        super().refresh_localization()

        # Step 2: Inject dynamic data into specific labels
        if "header_subtitle" in self.ui:
            self.ui["header_subtitle"].configure(
                text=self.get_text("header_subtitle", version=self.new_version)
            )

        # We treat the changelog as a dynamic variable passed to the log key
        if "changelog_box" in self.ui:
            self.ui["changelog_box"].configure(
                text=self.get_text("changelog_text", logs=self.changelog)
            )
