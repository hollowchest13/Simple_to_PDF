from typing import Dict
import webbrowser
import customtkinter as ctk

from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton, BaseLabel
from simple_to_pdf.core.config import GITHUB_REPO_URL


class AboutDialog(BaseDialog):
    """Displays information about the app and engine."""

    def __init__(self, parent, version: str, engine_name: str, size: str = "400x450"):
        # Initialize BaseDialog with specific translation section
        # BaseDialog calls init_localization() and sets up self.ui internally
        super().__init__(parent, title="window_title", loc_section="ui.about_dialog")

        self.version = version
        self.engine_name = engine_name

        if size:
            self.geometry(size)

        # Create UI components and register them in self.ui
        self._setup_dialog_ui()

        # Initial refresh to populate dynamic variables like {version} and {engine}
        self.refresh_localization()

    def _setup_dialog_ui(self) -> None:
        """Creates widgets and registers them in the self.ui dictionary for auto-translation."""

        # --- Header Section ---
        # Using BaseDialog helper to create title and subtitle labels
        self.set_header_text("Simple to PDF", f"Version {self.version}")

        # Map header labels to self.ui to enable automatic text updates
        header_children = self.header.winfo_children()
        if len(header_children) >= 2:
            self.ui["header_title"] = header_children[0]
            self.ui["header_subtitle"] = header_children[1]

        # --- Content Section ---
        # Engine badge (text will be set in refresh_localization)
        self.ui["engine_badge"] = BaseLabel(self.content, text="", label_type="badge")
        self.ui["engine_badge"].pack(pady=(0, 20))

        # Main description
        self.ui["description_label"] = BaseLabel(
            self.content,
            text="",
            label_type="subtitle",
        )
        self.ui["description_label"].pack(pady=10)

        # GitHub action button
        self.ui["github_btn"] = PrimaryButton(
            self.content,
            text="",
            command=lambda: webbrowser.open(GITHUB_REPO_URL),
            height=40,
            width=200,
        )
        self.ui["github_btn"].pack(pady=(70, 20))

    def refresh_localization(self) -> None:
        """
        Overrides the mixin method to handle dynamic keys with placeholders.
        This is called automatically by the LocalizationManager.
        """
        # Step 1: Standard translation for simple keys (description, button, etc.)
        super().refresh_localization()

        # Step 2: Manually update labels that require dynamic formatting (kwargs)
        if "header_subtitle" in self.ui:
            self.ui["header_subtitle"].configure(
                text=self.get_text("header_subtitle", version=self.version)
            )

        if "engine_badge" in self.ui:
            self.ui["engine_badge"].configure(
                text=self.get_text("engine_badge", engine=self.engine_name)
            )
