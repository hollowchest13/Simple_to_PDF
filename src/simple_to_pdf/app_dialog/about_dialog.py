from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton, BaseLabel
from simple_to_pdf.core.config import GITHUB_REPO_URL
import webbrowser


class AboutDialog(BaseDialog):
    """Displays information about the app and engine."""

    def __init__(self, parent, version, engine_name, size="400x400"):
        # We call the parent constructor with title and size
        super().__init__(parent, title="About")
        if size:
            self.geometry(size)

        # Use our helper from BaseDialog to set the header
        self.set_header_text("Simple to PDF", f"Version {version}")

        # Add a badge for the engine name
        BaseLabel(self.content, text=f"Engine: {engine_name}", label_type="badge").pack(
            pady=(0, 20)
        )

        # Main description
        BaseLabel(
            self.content,
            text="Professional utility for batch PDF processing.\nBuilt for efficiency and speed.",
            label_type="subtitle",
        ).pack(pady=10)

        # Primary action button
        PrimaryButton(
            self.content,
            text="View Source on GitHub",
            command=lambda: webbrowser.open(GITHUB_REPO_URL),
            height=40,
            width=70,
        ).pack(pady=(70, 20))
