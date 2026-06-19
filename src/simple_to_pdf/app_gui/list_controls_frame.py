import logging
from typing import Callable, Dict

import customtkinter as ctk

from simple_to_pdf.core.models import App_Mode
from simple_to_pdf.widgets import BaseFrame

logger = logging.getLogger(__name__)


class ListControlsFrame(BaseFrame):
    def __init__(
        self,
        parent: ctk.CTkFrame,
        *,
        width: int = 150,
        handlers: Dict[str, Callable],
        **kwargs,
    ):
        super().__init__(parent, width=width, **kwargs)
        self.loc_section: str = "ui.list_controls_panel"
        self.handlers = handlers
        self.init_btns()
        self._app_mode: App_Mode = App_Mode.MERGE

    @property
    def app_mode(self) -> App_Mode:
        return self._app_mode

    @app_mode.setter
    def app_mode(self, value):
        self._app_mode: App_Mode = value

    def init_btns(
        self,
    ) -> dict[str, ctk.CTkBaseClass]:
        """
        Build, configure, and layout all button panels within the interface.

        Constructs navigation, action, and settings panels, arranges them
        using the grid layout manager, and registers all created UI elements
        into the main UI dictionary and as instance attributes for easy access.

        Returns:
            dict[str, ctk.CTkBaseClass]: A dictionary mapping button identifiers
            to their corresponding CustomTkinter widget instances.
        """

        file_nav_btns: dict[str, ctk.CTkBaseClass] = self._build_file_navigation_panel()
        action_btns: dict[str, ctk.CTkBaseClass] = self._build_action_panel()
        settings_btn: dict[str, ctk.CTkBaseClass] = self._build_settings_panel()

        self.grid_rowconfigure(3, weight=1)

        self.nav_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=8)
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=4, pady=8)
        self.settings_frame.grid(row=4, column=0, sticky="ew", padx=4, pady=8)

        self.ui = file_nav_btns | action_btns | settings_btn
        for key, value in self.ui.items():
            setattr(self, key, value)
        return self.ui

    def _build_file_navigation_panel(self) -> dict[str, ctk.CTkBaseClass]:
        """
        Builds the file navigation panel using late-binding triggers.
        No need to pass callbacks as an argument anymore.
        """
        self.nav_frame = BaseFrame(self, frame_type="btns_container")

        # TODO: Add enum for buttons id
        button_configs = [
            {
                "id": "btn_add",
                "cmd": self._trigger("add"),
                "icon_name": "add_btn.png",
            },
            {
                "id": "btn_up",
                "cmd": lambda: self._trigger("move")(direction="up"),
                "icon_name": "up_btn.png",
            },
            {
                "id": "btn_down",
                "cmd": lambda: self._trigger("move")(direction="down"),
                "icon_name": "down_btn.png",
            },
            {
                "id": "btn_remove",
                "cmd": self._trigger("remove"),
                "icon_name": "remove_btn.png",
            },
        ]
        return self._buttons_pack(btns_config=button_configs, parent=self.nav_frame)

    def _build_action_panel(self) -> dict[str, ctk.CTkBaseClass]:
        self.action_frame = BaseFrame(self, frame_type="btns_container")

        button_configs = [
            {
                "id": "btn_merge",
                "cmd": self._trigger("merge"),
                "icon_name": "merge_btn.png",
            },
            {
                "id": "btn_extract",
                "cmd": self._trigger("extract"),
                "icon_name": "extract_btn.png",
            },
            {
                "id": "btn_stop",
                "cmd": self._trigger("stop"),
                "icon_name": "stop_btn.png",
                "state": "disabled",
            },
        ]
        return self._buttons_pack(btns_config=button_configs, parent=self.action_frame)

    def _build_settings_panel(self) -> dict[str, ctk.CTkBaseClass]:
        """
        Construct and configure the settings panel container and its buttons.

        Initializes the settings frame and defines button configurations for
        help and settings actions. Packs these buttons into the frame using
        the base button packing utility.

        Returns:
            dict[str, ctk.CTkBaseClass]: A dictionary containing the created
            button widgets mapped by their identifier keys.
        """
        self.settings_frame = BaseFrame(self, frame_type="btns_container")
        button_configs = [
            {
                "id": "btn_help",
                "cmd": self._trigger("help"),
                "icon_name": "help_btn.png",
            },
            {
                "id": "btn_settings",
                "cmd": self._trigger("settings"),
                "icon_name": "settings_btn.png",
            },
        ]
        return self._buttons_pack(
            btns_config=button_configs, parent=self.settings_frame
        )

    def refresh_localization(self) -> None:
        super().refresh_localization()
        self.update_conditional_button()

    def update_conditional_button(self):
        """
        Update the primary action button text based on the current application mode.

        Determines the appropriate translation key corresponding to the active
        app mode (COMPRESS, MERGE, or CONVERT), retrieves the localized text,
        and applies it to the button widget if it exists in the UI dictionary.
        """

        match self.app_mode:
            case App_Mode.COMPRESS:
                key = "btn_compress"
            case App_Mode.MERGE:
                key = "btn_merge"
            case App_Mode.CONVERT:
                key = "btn_convert"

        new_text = self.get_text(key, section=self.loc_section)

        if "btn_merge" in self.ui:
            self.ui["btn_merge"].configure(text=new_text)
