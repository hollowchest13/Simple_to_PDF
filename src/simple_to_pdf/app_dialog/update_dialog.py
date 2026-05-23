import webbrowser

from simple_to_pdf.core import config
from .base_dialog import BaseDialog
from simple_to_pdf.widgets import BaseFrame, PrimaryButton, BaseLabel


class UpdateDialog(BaseDialog):
    """
    Dialog to notify the user about a new software version.
    Integrated with the centralized localization and observer system.
    """

    def __init__(self, parent, new_version: str, changelog: str):
        # Initialize BaseDialog with specific translation section and window title key
        super().__init__(parent, loc_section="dialogs.update_dialog")

        self.new_version = new_version
        self.changelog = changelog

        # Build UI and register widgets in self.ui for automatic updates
        self._setup_dialog_ui()

        # Initial refresh to sync labels with JSON and inject dynamic data
        self.refresh_localization()

    def _setup_dialog_ui(self) -> None:
        """
        Constructs the UI manually and maps elements to self.ui.
        Replaces the old set_header_text with explicit widget creation.
        """

        # --- Header Section ---
        # Main Title (e.g., "New Update!")
        self.ui["header_title"] = BaseLabel(self.header, text="", label_type="title")
        self.ui["header_title"].pack(pady=(25, 2))

        # Subtitle (Version info placeholder)
        self.ui["header_subtitle"] = BaseLabel(
            self.header, text="", label_type="subtitle"
        )
        self.ui["header_subtitle"].pack(pady=(0, 20))

        # --- Content Area ---
        # Static label for the "What's New" section
        self.ui["whats_new_title"] = BaseLabel(
            self.content, text="", label_type="subtitle"
        )
        self.ui["whats_new_title"].pack(anchor="w", pady=(0, 5))

        # Box to display the changelog content
        self.ui["changelog_box"] = BaseLabel(self.content, text="", label_type="badge")
        self.ui["changelog_box"].pack(fill="x", pady=(0, 20))

        # Frame for action buttons
        self.btn_frame = BaseFrame(self.content)
        self.btn_frame.pack(fill="x", pady=10)

        # Button to trigger the update/download process
        self.ui["btn_download"] = PrimaryButton(
            self.btn_frame, text="", command=self._on_update_click
        )
        self.ui["btn_download"].pack(side="right", padx=5)

        # Button to dismiss the dialog
        self.ui["btn_later"] = PrimaryButton(
            self.btn_frame,
            text="",
            command=self._on_close,
        )
        self.ui["btn_later"].pack(side="right", padx=5)

    def _on_update_click(self):
        """Open the releases page in a browser and close the dialog safely."""
        webbrowser.open_new_tab(config.RELEASES_URL)
        self._on_close()

    def refresh_localization(self) -> None:
        """
        Updates UI text. Combines automatic JSON mapping for static keys
        with manual formatting for dynamic version and changelog strings.
        """
        # Step 1: Standard translation for keys registered in self.ui
        super().refresh_localization()

        # Step 2: Inject dynamic variables using get_text with kwargs
        if "header_subtitle" in self.ui:
            # Replaces {version} placeholder in the JSON string
            self.ui["header_subtitle"].configure(
                text=self.get_text("header_subtitle", version=self.new_version)
            )

        if "changelog_box" in self.ui:
            # Replaces {logs} placeholder in the JSON string
            self.ui["changelog_box"].configure(
                text=self.get_text("changelog_text", logs=self.changelog)
            )
