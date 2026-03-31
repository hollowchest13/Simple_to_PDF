import customtkinter as ctk
from simple_to_pdf.widgets import BaseLabel, SlidingFrame
from typing import Callable, Dict, Any


class SettingsFrame(SlidingFrame):
    def __init__(
        self,
        parent: Any,
        *,
        open_width: int = 200,
        closed_width: int = 0,
        callbacks: Dict[str, Callable],
        **kwargs: Any,
    ) -> None:
        super().__init__(
            parent, open_width=open_width, closed_width=closed_width, **kwargs
        )
        # Initialize UI title immediately
        self.title_label = BaseLabel(self, label_type="title", text="Settings")
        self.title_label.pack(side="top", fill="x", padx=10, pady=(10, 0))

        # Placeholder for widgets dictionary
        self.ui: Dict[str, ctk.CTkBaseClass] = {}
        self.loc_section = "ui.settings_panel"
        self.callbacks = callbacks
        self.init_controls()
        self.init_localization()

    def init_controls(self) -> Dict[str, ctk.CTkBaseClass]:
        """
        Public method to initialize settings controls, similar to init_btns in HelpFrame.
        """
        # Build the settings panel
        settings_widgets: Dict[str, ctk.CTkBaseClass] = self._build_settings_panel()

        # Store in self.ui and set as attributes for direct access (self.language_selector, etc.)
        self.ui = settings_widgets
        for key, value in self.ui.items():
            setattr(self, key, value)

        return self.ui

    def _build_settings_panel(self) -> Dict[str, ctk.CTkBaseClass]:
        """
        Internal method to construct specific setting rows.
        Now uses the centralized _trigger mechanism.
        """
        widgets: Dict[str, ctk.CTkBaseClass] = {}
        widgets["language_selector"] = self._create_setting_row(
            parent=self,
            text="Language:",
            widget_class=ctk.CTkOptionMenu,
            values=["English", "Ukrainian"],
            width=120,
            command=self._trigger("change_language"),
        )
        return widgets

    def _create_setting_row(
        self,
        *,
        parent: ctk.CTkFrame,
        text: str,
        widget_class: Any,
        **widget_kwargs: Any,
    ) -> Any:
        """
        Standardized row creator: Label on the left, Widget on the right.
        """
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=8)

        label = ctk.CTkLabel(container, text=text, font=("Arial", 12))
        label.pack(side="left", padx=(5, 10))

        widget = widget_class(container, **widget_kwargs)
        widget.pack(side="right", expand=True, fill="x", padx=5)

        return widget
