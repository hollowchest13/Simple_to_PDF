from typing import Any, Callable, Dict

import customtkinter as ctk

from simple_to_pdf.widgets import BaseLabel, ToogleFrame
from simple_to_pdf.widgets.base_widgets import BaseOptionMenu, BaseSwitcher


class SettingsFrame(ToogleFrame):
    def __init__(
        self,
        parent: Any,
        *,
        open_width: int = 200,
        closed_width: int = 0,
        handlers: Dict[str, Callable],
        **kwargs: Any,
    ) -> None:
        super().__init__(
            parent, open_width=open_width, closed_width=closed_width, **kwargs
        )
        self.language_selector: BaseOptionMenu
        self.compress_selector: BaseSwitcher

        # Path to settings section in translation JSON
        self.loc_section = "ui.settings_panel"
        self.handlers = handlers

        # Centralized storage for all translatable widgets
        self.ui: Dict[str, Any] = {}

        # Build the interface
        self._setup_ui()

        # Register for localization updates
        self.init_localization()

    def _setup_ui(self) -> None:
        """
        Creates all UI components and organizes them into the self.ui dictionary.
        """

        # 1. Create and pack Title
        title = BaseLabel(self, label_type="title", text="Settings")
        title.pack(side="top", fill="x", padx=10, pady=(10, 0))
        self.ui["title_label"] = title

        # 2. Setup specific setting controls (Language selector, etc.)
        settings_widgets = self._setup_settings_controls()
        self.ui.update(settings_widgets)

        # Map dictionary items to object attributes for easy 'self.widget_name' access
        for key, widget in self.ui.items():
            setattr(self, key, widget)

    def _setup_settings_controls(self) -> Dict[str, Any]:
        """
        Configures individual setting rows and returns a dict of widgets.
        """
        widgets: Dict[str, Any] = {}

        # Language Selection Row
        # Returns both the label and the option menu to be stored in self.ui
        lang_widgets = self._create_setting_row(
            parent=self,
            row_id="language",  # Used to generate keys: 'language_label' and 'language_selector'
            label_text=self.get_text("settings_panel.language_label", section="ui"),
            widget_class=BaseOptionMenu,
            values=sorted(self._LANG_MAP.keys()),
            width=120,
            command=self._trigger("change_language"),
        )
        compress_widgets: Any = self._create_setting_row(
            parent=self,
            row_id="compress",
            label_text=self.get_text("settings_panel.compress_label", section="ui"),
            widget_class=BaseSwitcher,  # Передаємо клас світча
            value=False,
        )
        widgets.update(**lang_widgets, **compress_widgets)
        return widgets

    def _create_setting_row(
        self,
        *,
        parent: ctk.CTkFrame,
        row_id: str,
        label_text: str,
        widget_class: Any,
        **widget_kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Creates a row with a Label on the left and a functional Widget on the right.
        Returns a dict with both components for localization purposes.
        """
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=8)

        # Create label
        label = BaseLabel(container, text=label_text, label_type="content")
        label.pack(side="left", padx=(5, 10))

        # Create the control widget (OptionMenu, Entry, etc.)
        widget = widget_class(container, **widget_kwargs)
        widget.pack(side="right", padx=5)

        # Return both so they can be added to self.ui for translation
        return {f"{row_id}_label": label, f"{row_id}_selector": widget}

    def collect_data(self) -> Dict[str, str]:
        data = {}
        # Check for language selector
        if hasattr(self, "language_selector"):
            data["language"] = self.language_selector.get()
        return data
