import logging
import customtkinter as ctk
from typing import Callable, Dict
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
                "id": "btn_status_clear",
                "cmd": self._trigger("clear_status"),
                "icon_name": "clean_btn.png",
            },
        ]
        return self._buttons_pack(btns_config=button_configs, parent=self.action_frame)

    def _build_settings_panel(self) -> dict[str, ctk.CTkBaseClass]:
        self.settings_frame = BaseFrame(self, frame_type="btns_container")
        button_configs = [
            {
                "id": "btn_help",
                "cmd": self._trigger("help"),  # Standard trigger without arguments
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

        match self.app_mode:
            case App_Mode.COMPRESS:
                key = "btn_compress"
            case App_Mode.MERGE:
                key = "btn_merge"

        # Використовуємо метод міксину для перекладу
        new_text = self.get_text(key, section=self.loc_section)

        # Оновлюємо кнопку
        if "btn_merge" in self.ui:
            self.ui["btn_merge"].configure(text=new_text)
