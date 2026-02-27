import customtkinter as ctk
from typing import Literal
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin


class PrimaryButton(ctk.CTkButton, ThemeProviderMixin):
    """
    A pre-styled button for main actions.
    Includes a hover effect that changes the background color.
    """

    def __init__(self, parent, **kwargs):
        params = self.set_button_params()
        params.update(kwargs)
        super().__init__(parent, **params)


class BaseFrame(ctk.CTkFrame, ThemeProviderMixin):
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
        label_type: Literal["badge", "title", "content"] = "badge",
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


class BaseTextBox(ctk.CTkTextbox, ThemeProviderMixin):
    def __init__(self, parent, *, textbox_type: Literal["status_text"], **kwargs):
        params = self.set_textbox_params(textbox_type=textbox_type)
        params.update(kwargs)
        super().__init__(parent, **params)
