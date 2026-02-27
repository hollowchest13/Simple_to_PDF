import tkinter as tk
import customtkinter as ctk
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from typing import Literal

class BaseFrame(ctk.CTkFrame,ThemeProviderMixin):
    def __init__(self,parent,*,frame_type:Literal["main", "header", "content", "footer","btns_container"] ="main", **kwargs):
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
        params=self.set_frame_params(frame_type=frame_type)
        params.update(kwargs)
        # Call the super constructor with prepared kwargs
        super().__init__(parent, **params)
    
class BaseScrollableFrame(ctk.CTkScrollableFrame,ThemeProviderMixin):
    def __init__(self,parent,*,scr_frame_type:Literal[
        "file_list",
        "button_list",   
        "settings",     
        "preview"
    ] ="button_list", **kwargs):
        params=self.set_scrollable_frame_params(scr_frame_type=scr_frame_type)
        params.update(kwargs)
        super().__init__(parent,**params)