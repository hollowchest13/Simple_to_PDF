import tkinter as tk
import customtkinter as ctk
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.widgets import BaseFrame
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin


class BaseWindow(ctk.CTk, ThemeProviderMixin, LocalizationMixin):
    """
    Base class for the main application window.
    Focuses on layout structure and consistent theming.
    """

    def __init__(self, **kwargs):
        window_title = kwargs.pop("title", "Window")
        window_size = kwargs.pop("size", "1000x600")

        super().__init__(**kwargs)

        self.title(window_title)
        self.geometry(window_size)

        self._init_base_layout()
        self.init_localization()

    def _init_base_layout(self):
        """Creates top-level structural containers for the main window."""

        self.root_container = BaseFrame(self)
        self.root_container.pack(fill="both", expand=True)
