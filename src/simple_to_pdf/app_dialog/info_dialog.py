import logging
from typing import Any, Optional

from simple_to_pdf.widgets import BaseLabel, PrimaryButton
from simple_to_pdf.widgets.base_widgets import BaseTextBox

from .base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class InfoDialog(BaseDialog):
    """
    A versatile dialog for displaying content based on predefined scenarios.
    It automatically links titles, headers, and buttons from the localization JSON.
    """

    def __init__(
        self,
        parent: Any,
        scenario_key: str = "info",
        text_font: str = "Consolas",
        font_size: int = 14,
        with_footer: bool = False,
        with_icon: bool = True,
        size: str = "450x450",
        text: Optional[str] = None,
        **kwargs,
    ):
        group = scenario_key.split(".")[0] if "." in scenario_key else "info"
        super().__init__(
            parent, title_key=f"{group}.__title__", loc_section="notifications"
        )

        self.scenario = scenario_key
        if text is not None:
            msg = self.get_text(text, **kwargs)
        else:
            msg = self.get_text(f"{scenario_key}.message", **kwargs)

        self.raw_text = msg
        self.footer_text = self.get_text(f"{scenario_key}.footer", **kwargs)
        self.current_icon = self._load_icon(with_icon=with_icon, window_type=group)

        if size:
            self.geometry(size)

        self.with_footer = with_footer
        self._setup_dialog_ui(text_font, font_size)
        self.refresh_localization(**kwargs)
        self.update_idletasks()
        self.after(self.FINALIZE_DELAY_MS, self._finalize)

    def _setup_dialog_ui(self, font_name: str, font_size: int) -> None:
        """Constructs the UI layout and registers widgets for the localization engine."""

        self.header.grid_columnconfigure(0, weight=0)
        self.header.grid_columnconfigure(1, weight=2)
        self.header.grid_columnconfigure(2, weight=0)

        if self.current_icon:
            self.icon_label = BaseLabel(self.header, text="", image=self.current_icon)
            self.icon_label.grid(
                row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="w"
            )

        self.ui["header_title"] = BaseLabel(self.header, text="", label_type="title")
        self.ui["header_title"].grid(
            row=0, column=1, sticky="ew", padx=(0, 50), pady=(20, 10)
        )

        self.txt = BaseTextBox(
            self.content, textbox_type="info", font=(font_name, font_size)
        )
        self.txt.insert("1.0", self.raw_text)
        self.txt.configure(state="disabled")
        self.txt.pack(expand=True, fill="both", padx=15, pady=10)

        self.ui["btn_close"] = PrimaryButton(
            self.footer, text="", command=self._on_close, height=40, width=120
        )
        self.ui["btn_close"].pack(side="right", padx=25, pady=15)
        if self.with_footer:
            self.ui["footer_text"] = BaseLabel(
                self.footer, label_type="subtitle", text=""
            )
            self.ui["footer_text"].pack(side="left", padx=25, pady=15)

    def refresh_localization(self, **kwargs) -> None:
        """Synchronizes UI elements with the current language dictionary."""
        super().refresh_localization()  # Updates window title

        if "header_title" in self.ui:
            self.ui["header_title"].configure(
                text=self.get_text(f"{self.scenario}.header")
            )

        if "btn_close" in self.ui:
            btn_text = self.get_text(f"{self.scenario}.btn")
            self.ui["btn_close"].configure(text=btn_text)

        if "footer_text" in self.ui:
            footer_text = self.get_text(f"{self.scenario}.footer_text", **kwargs)
            self.ui["footer_text"].configure(text=footer_text)

    def _on_close(self):
        """Cleanup logic before destroying the widget."""
        if hasattr(self, "remove_from_observers"):
            self.remove_from_observers()
        self.destroy()
