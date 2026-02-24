import tkinter as tk
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from typing import Literal

class BaseFrame(tk.Frame,ThemeProviderMixin):
    def __init__(self, parent,frame_type:Literal["main", "header", "content", "footer"] ="main", **kwargs):
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
        kwargs.setdefault("bg",self.set_frame_background(frame_type=frame_type))
        
        # Call the super constructor with prepared kwargs
        super().__init__(parent, **kwargs)