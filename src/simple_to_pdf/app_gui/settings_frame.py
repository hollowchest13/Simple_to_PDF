from typing import Any, Callable, Dict

import customtkinter as ctk
from simple_to_pdf.core import config
from simple_to_pdf.settings.settings_manager import SettingsManager
from simple_to_pdf.widgets import BaseLabel, ToogleFrame
from simple_to_pdf.widgets.base_widgets import BaseOptionMenu, BaseSwitcher


class SettingsFrame(ToogleFrame):
    def __init__(
        self,
        parent: Any,
        *,
        is_open: bool = False,
        width: int = 230,
        handlers: Dict[str, Callable],
        settings_manager: SettingsManager,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, width=width, is_open=is_open, **kwargs)
        self.language_selector: BaseOptionMenu
        self.compress_selector: BaseSwitcher
        self.settings_manager: SettingsManager = settings_manager
        self._callback = lambda *args, **kwargs: None

        self.loc_section = "ui.settings_panel"
        self.handlers = handlers

        self.ui: Dict[str, Any] = {}

        self._setup_ui()

        self.init_localization()

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    def _setup_ui(self) -> None:
        """
        Creates all UI components and organizes them into the self.ui dictionary.
        """

        title = BaseLabel(self, label_type="title", text="Settings")
        title.pack(side="top", fill="x", padx=10, pady=(10, 0))
        self.ui["title_label"] = title

        settings_widgets = self._setup_settings_controls()
        self.ui.update(settings_widgets)

        for key, widget in self.ui.items():
            setattr(self, key, widget)

    def _setup_settings_controls(self) -> Dict[str, Any]:
        """
        Configures individual setting rows and returns a dict of widgets.
        """
        widgets: Dict[str, Any] = {}

        option_width = 120
        lang_widgets = self._create_setting_row(
            parent=self,
            row_id="language",
            label_text=self.get_text("settings_panel.language_label", section="ui"),
            widget_class=BaseOptionMenu,
            values=sorted(self._LANG_MAP.keys()),
            width=option_width,
            command=self._trigger("change_language"),
        )
        format_widgets = self._create_setting_row(
            parent=self,
            row_id="format",
            label_text=self.get_text("settings_panel.format_label", section="ui"),
            widget_class=BaseOptionMenu,
            values=list(config.PAGE_FORMATS.keys()),
            width=option_width,
        )
        compress_widgets: Any = self._create_setting_row(
            parent=self,
            row_id="compress",
            label_text=self.get_text("settings_panel.compress_label", section="ui"),
            widget_class=BaseSwitcher,
            value=False,
            command=lambda: self.callback(),
        )
        widgets.update(**lang_widgets, **compress_widgets, **format_widgets)
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
        Create a setting row with a label and a control widget.
        Returns: Dict containing label and widget instances.
        """
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=8)
        container.columnconfigure(1, weight=1)

        label = BaseLabel(container, text=label_text, label_type="content")
        label.grid(row=0, column=0, padx=5, sticky="w")

        widget = widget_class(container, **widget_kwargs)
        widget.grid(row=0, column=1, padx=5, sticky="e")

        return {f"{row_id}_label": label, f"{row_id}_selector": widget}

    def collect_data(self) -> Dict[str, str]:
        """
        Collect configuration data from settings widgets.

        Iterates through the UI dictionary, extracts values from widgets with
        a '_selector' suffix, and returns a dictionary where the keys are
        cleaned by removing that suffix.

        Returns:
            Dict[str, str]: A dictionary of configuration keys and their string-converted values.
        """
        data = {}
        for key, widget in self.ui.items():
            if "_selector" in key and hasattr(widget, "get"):
                clean_key = key.replace("_selector", "")
                data[clean_key] = str(widget.get())
        return data

    def get_widget_value(self, *, widget_id: str) -> str:
        """Retrieve and return the string value of a specified UI widget."""
        value = self.ui[widget_id].get()
        return str(value)

    def setup(self) -> None:
        """Load and apply all settings dynamically."""
        settings = self.settings_manager.get_settings()

        for ui_key, widget in self.ui.items():
            if ui_key.endswith("_selector") and hasattr(widget, "set"):
                setting_key = ui_key.replace("_selector", "")
                if setting_key in settings:
                    value = settings[setting_key]
                    widget.set(value)
