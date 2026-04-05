from typing import Dict
import webbrowser
import customtkinter as ctk

from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton, BaseLabel
from simple_to_pdf.core.config import GITHUB_REPO_URL


class AboutDialog(BaseDialog):
    """
    Displays information about the app and engine.
    Fully integrated with the centralized localization system.
    """

    def __init__(self, parent, version: str, engine_name: str, size: str = "400x450"):
        # Initialize BaseDialog with translation section 'ui.about_dialog'
        super().__init__(parent, loc_section="ui.about_dialog")

        self.version = version
        self.engine_name = engine_name

        if size:
            self.geometry(size)

        # Build UI structure and register widgets in self.ui
        self._setup_dialog_ui()

        # Initial call to populate labels with localized text and dynamic data
        self.refresh_localization()

    def _setup_dialog_ui(self) -> None:
        """
        Creates widgets and registers them in self.ui for automatic translation updates.
        Since set_header_text was removed, we create header labels manually.
        """


        # --- Header Section ---
        # Main Title (Brand name)
        self.ui["header_title"] = BaseLabel(self.header, text="", label_type="title")
        self.ui["header_title"].pack(pady=(25, 2))

        # Subtitle (Version info placeholder)
        self.ui["header_subtitle"] = BaseLabel(
            self.header, text="", label_type="subtitle"
        )
        self.ui["header_subtitle"].pack(pady=(0, 20))

        # --- Content Section ---
        # Engine badge (e.g., PyMuPDF)
        self.ui["engine_badge"] = BaseLabel(self.content, text="", label_type="badge")
        self.ui["engine_badge"].pack(pady=(0, 20))

        # Main description text from JSON
        self.ui["description_label"] = BaseLabel(
            self.content,
            text="",
            label_type="subtitle",
        )
        self.ui["description_label"].pack(pady=10)

        # Action button to open GitHub repository
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
        Updates UI text. Combines super() automatic mapping for static keys
        with manual formatting for dynamic version/engine strings.
        """
        # Step 1: Спочатку даємо базі заповнити статичні ключі (description, buttons)
        super().refresh_localization()

        # Step 2: Тепер ПЕРЕЗАПИСУЄМО динамічні поля, щоб вставити версію та двигун

        if "header_title" in self.ui:
            self.ui["header_title"].configure(text="Simple to PDF")

        if "header_subtitle" in self.ui:
            # Використовуємо str(), щоб Pyright не сварився на "None"
            text = str(self.get_text("header_subtitle", version=self.version))
            self.ui["header_subtitle"].configure(text=text)

        if "engine_badge" in self.ui:
            text = str(self.get_text("engine_badge", engine=self.engine_name))
            self.ui["engine_badge"].configure(text=text)
