import customtkinter as ctk
from typing import Literal
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from simple_to_pdf.core.config import ICONS_PATH
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class PrimaryButton(ctk.CTkButton, ThemeProviderMixin):
    """
    A pre-styled button for main actions.
    Includes a hover effect that changes the background color.
    """

    def __init__(self, parent, **kwargs):
        params = self.set_button_params()
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseFrame(ctk.CTkFrame, ThemeProviderMixin, LocalizationMixin):
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
        params = self.set_frame_params(frame_type=frame_type)
        params.update(kwargs)
        # Call the super constructor with prepared kwargs
        super().__init__(parent, **params)
        self.init_localization()

    def _buttons_pack(
        self,
        *,
        btns_config,
        parent: ctk.CTkFrame,
        btns_width: int = 140,
        btns_height: int = 40,
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
                text=self.get_text(cfg["id"], section="ui.buttons"),
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


class BaseScrollableFrame(ctk.CTkScrollableFrame, ThemeProviderMixin):
    def __init__(
        self,
        parent,
        *,
        scr_frame_type: Literal[
            "file_list", "button_list", "settings", "preview"
        ] = "button_list",
        **kwargs,
    ):
        params = self.set_scrollable_frame_params(scr_frame_type=scr_frame_type)
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseLabel(ctk.CTkLabel, ThemeProviderMixin):
    """
    A label styled as a 'badge' or 'chip'.
    Ideal for displaying versions, engine names, or status tags.
    """

    def __init__(
        self,
        parent,
        *,
        label_type: Literal["badge", "title", "content", "title", "subtitle"] = "badge",
        **kwargs,
    ):
        params = self.set_label_params(label_type=label_type)
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseProgress(ctk.CTkProgressBar, ThemeProviderMixin):
    def __init__(self, parent, *, progress_type: Literal["merge_progress"], **kwargs):
        params = self.set_progress_params(progress_type=progress_type)
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseTextBox(ctk.CTkTextbox, ThemeProviderMixin, LocalizationMixin):
    def __init__(
        self, parent, *, textbox_type: Literal["status_text", "info"] = "info", **kwargs
    ):
        params = self.set_textbox_params(textbox_type=textbox_type)
        params.update(kwargs)
        super().__init__(parent, **params)
