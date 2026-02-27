import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal
from simple_to_pdf.app_gui.main_frame import MainFrame
from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from simple_to_pdf.widgets.base_widgets import BaseLabel, BaseProgress


class GUICallback(ThemeProviderMixin):
    def __init__(self, main_frame: MainFrame):
        # Saving link to main window (PDFGUIMerger)
        self.main_frame = main_frame

    def safe_callback(self, **kwargs) -> None:
        """Using self.app.after, because after belongs to the main window."""

        data = kwargs.copy()
        status_message = data.pop("status_message", None)

        # Pass updates to the GUI thread queue

        self.main_frame.after(0, lambda: self.progress_bar_update(**data))
        if status_message:
            self.main_frame.after(
                0, lambda: self.show_status_message(status_message=status_message)
            )

    def progress_bar_update(
        self,
        *,
        stage: str = "Processing",
        progress_bar_mode: str = "indeterminate",
        current: int = 0,
        total: int = 0,
        filename: str = "",
    ) -> None:
        pb: BaseProgress = self.main_frame.progress_bar
        pl: BaseLabel = self.main_frame.progress_label
        
        idle_color = pb.cget("fg_color")
        active_color = self.get_color(ThemeKeys.PROGRESS_COLOR)

        if progress_bar_mode == "indeterminate":
            pb.configure(mode="indeterminate", progress_color=active_color)
            pb.start()
            status_text = f"{stage} documents..."
        else:
            pb.stop()
            pb.configure(mode="determinate")
            
            progress_float = (current / total) if total > 0 else 0
            
            current_color = active_color if progress_float > 0 else idle_color
            pb.configure(progress_color=current_color)
            
            pb.set(progress_float)

            percent = progress_float * 100
            display_name = (filename[:27] + "...") if len(filename) > 30 else filename
            status_text = f"{stage}: {display_name} ({current}/{total}) — {percent:.1f}%"

        pl.configure(text=status_text)
        self.main_frame.update_idletasks()
    def show_status_message(self, status_message: str):
        st = self.main_frame.status_text
        st.configure(state="normal")
        st.insert(tk.END, f"- {status_message}\n")
        st.see("end")
        st.configure(state="disabled")
