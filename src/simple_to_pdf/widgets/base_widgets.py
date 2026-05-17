from tkinter import BooleanVar
import customtkinter as ctk
from typing import Literal, Any, Callable, Dict, List
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.utils.theme_provider import (
    LabelThemeMixit,
    ProgressThemeMixin,
    TextboxThemeMixin,
    OptionMenuThemeMixin,
    ButtonThemeMixin,
    FrameThemeMixin,
    ScrolableFrameThemeMixin,
    SwitcherThemeMixin,
)
from simple_to_pdf.core.config import ICONS_PATH
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class PrimaryButton(ctk.CTkButton, ButtonThemeMixin):
    """
    A pre-styled button for main actions.
    Includes a hover effect that changes the background color.
    """

    def __init__(self, parent, **kwargs):
        params = self.set_params()
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseFrame(ctk.CTkFrame, FrameThemeMixin, LocalizationMixin):
    def __init__(
        self,
        parent,
        *,
        frame_type: Literal[
            "main",
            "header",
            "content",
            "footer",
            "btns_container",
            "scr_frame_container",
            "list_item",
        ] = "main",
        **kwargs,
    ):
        """
        A themed frame component that applies styles from ThemeProviderMixin.

        Args:
            parent: The parent widget.
            frame_type (str): The functional role ("main", "header", "content", "footer").
            **kwargs: Any valid tkinter.Frame arguments.
                - 'bg' (str): Overrides the automatic theme color if provided.
                - Other common arguments: 'width', 'height', 'padx', 'pady', 'relief'.

        Note:
            If 'bg' is not explicitly passed in **kwargs, it will be
            automatically assigned based on the provided frame_type.
        """
        params = self.set_params(frame_type=frame_type)
        params.update(kwargs)
        # Call the super constructor with prepared kwargs
        super().__init__(parent, **params)
        self.callbacks: Dict[str, Callable] = {}
        self.ui: dict[str, Any] = {}
        self.loc_section: str = ""
        self.init_localization()

    def _buttons_pack(
        self,
        *,
        btns_config,
        parent: ctk.CTkFrame,
        btns_width: int = 180,
        btns_height: int = 50,
    ):
        btns = {}

        for i, cfg in enumerate(btns_config):
            icon = (
                self._load_icon(icon_name=cfg["icon_name"])
                if "icon_name" in cfg
                else None
            )
            btn = PrimaryButton(
                parent,
                text=self.get_text(cfg["id"], section=self.loc_section),
                command=cfg["cmd"],
                image=icon,
                width=btns_width,
                height=btns_height,
            )

            is_first = i == 0
            is_last = i == len(btns_config) - 1

            top_pad = 15 if is_first else 4
            bottom_pad = 15 if is_last else 4

            btn.pack(side="top", padx=15, pady=(top_pad, bottom_pad))

            btns[cfg["id"]] = btn

        return btns

    def _load_icon(self, *, icon_name: str, size=(20, 20)):

        full_path = ICONS_PATH / icon_name

        try:
            pil_img = Image.open(full_path)

            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception as e:
            logger.error(f"❌ Error CTkImage: {e}")
            return None

    def set_actions_state(self, enabled: bool) -> None:
        """Lock or unlock all active ui in object"""
        new_state = "normal" if enabled else "disabled"
        for widget in self.ui.values():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(state=new_state)

    def _trigger(self, command: str | Callable) -> Callable:
        """
        A universal wrapper for UI commands.
        Allows creating widgets in __init__ before all dependencies are fully initialized.
        """

        # TODO Add logging
        def wrapper(*args, **kwargs):
            # Case 1: Command is a string key (Look up in callbacks dictionary)
            if isinstance(command, str):
                # The dictionary self.callbacks will be populated later by the MainWindow
                callback = self.callbacks.get(command)
                if callback:
                    return callback(*args, **kwargs)

                # Debug warning if the button is pressed but the handler isn't linked yet
                print(
                    f"Warning: Command '{command}' is not registered in {self.__class__.__name__}"
                )
                return None

            # Case 2: Command is a direct reference to a method (e.g., self.some_internal_method)
            elif callable(command):
                return command(*args, **kwargs)

        return wrapper


class BaseScrollableFrame(ctk.CTkScrollableFrame, ScrolableFrameThemeMixin):
    def __init__(
        self,
        parent,
        *,
        scr_frame_type: Literal[
            "file_list", "button_list", "settings", "preview"
        ] = "button_list",
        **kwargs,
    ):
        params = self.set_params(scr_frame_type=scr_frame_type)
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseLabel(ctk.CTkLabel, LabelThemeMixit):
    """
    A label styled as a 'badge' or 'chip'.
    Ideal for displaying versions, engine names, or status tags.
    """

    def __init__(
        self,
        parent,
        *,
        label_type: Literal["badge", "title", "content", "subtitle"] = "badge",
        **kwargs,
    ):
        params = self.set_params(label_type=label_type)
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseProgress(ctk.CTkProgressBar, ProgressThemeMixin):
    def __init__(self, parent, *, progress_type: Literal["merge_progress"], **kwargs):
        params = self.set_params(progress_type=progress_type)
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseTextBox(ctk.CTkTextbox, TextboxThemeMixin):
    def __init__(
        self, parent, *, textbox_type: Literal["status_text", "info"] = "info", **kwargs
    ):
        params = self.set_params(textbox_type=textbox_type)
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseOptionMenu(ctk.CTkOptionMenu, OptionMenuThemeMixin):
    def __init__(
        self,
        parent,
        menu_type: Literal["settings"] = "settings",
        values: List[str] | None = None,
        **kwargs,
    ):
        params = self.set_params(menu_type=menu_type)
        params["values"] = values or ["None"]
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseSwitcher(ctk.CTkSwitch, SwitcherThemeMixin):
    def __init__(self, parent,*,value:bool,**kwargs):
        self.var = ctk.BooleanVar(value=value)
        theme_params = self.set_params(variable=self.var, text="")
        super().__init__(parent, **theme_params,**kwargs)

    def is_on(self) -> bool:
        return self.var.get()
