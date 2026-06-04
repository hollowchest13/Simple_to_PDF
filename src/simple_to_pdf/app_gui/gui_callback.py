import tkinter as tk
import logging
from typing import Literal
from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin

logger = logging.getLogger(__name__)


class GUICallback(ThemeProviderMixin, LocalizationMixin):
    def __init__(self, main_frame):
        self.main_frame = main_frame

    def safe_callback(
        self, event_type: Literal["status", "progress"], **params
    ) -> None:
        """Thread-safe router for GUI events using .after()."""

        if event_type == "progress":
            progress_params = {
                "stage": params.get("stage", "processing"),
                "mode": params.get("mode", "indeterminate"),
                "current": params.get("current", 0),
                "total": params.get("total", 0),
                "filename": params.get("filename", ""),
            }
            self.main_frame.after(
                20, lambda p=progress_params: self.progress_bar_update(**p)
            )

        elif event_type == "status":
            status_params = params.copy()
            status_key = status_params.pop("key")
            status_type = status_params.pop("status", "info")

            self.main_frame.after(
                20,
                lambda k=status_key, s=status_type, sp=status_params: self.set_status(
                    key=k, status=s, **sp
                ),
            )

    def progress_bar_update(
        self,
        *,
        stage: Literal["processing", "converting", "merging"] = "processing",
        mode: Literal["indeterminate", "determinate"] = "indeterminate",
        current: int = 0,
        total: int = 0,
        filename: str = "",
    ) -> None:
        """Updates the progress bar and label text in the UI."""
        LOC_SECTION: str = "progress"
        pb = self.main_frame.progress_bar
        pl = self.main_frame.progress_label

        idle_color = pb.cget("fg_color")
        active_color = self.get_color(ThemeKeys.PROGRESS_COLOR)
        stage_text = self.get_text(f"stage.{stage}", section=LOC_SECTION)

        if mode == "indeterminate":
            if pb.cget("mode") != "indeterminate":
                pb.configure(mode="indeterminate", progress_color=active_color)
                pb.start()
            progress_text = self.get_text(
                "indeterminate", section=LOC_SECTION, stage=stage_text
            )
        else:
            if pb.cget("mode") == "indeterminate":
                pb.stop()
                pb.configure(mode="determinate")

            progress_float = (current / total) if total > 0 else 0
            pb.configure(
                progress_color=active_color if progress_float > 0 else idle_color
            )
            pb.set(progress_float)

            percent = int(progress_float * 100)
            display_name = (filename[:27] + "...") if len(filename) > 30 else filename

            progress_text = self.get_text(
                "detailed",
                section=LOC_SECTION,
                stage=stage_text,
                filename=display_name,
                current=current,
                total=total,
                percent=percent,
            )

        pl.configure(text=progress_text)

    def set_status(self, key: str, status: str = "info", **kwargs) -> None:
        """Appends a status message with an icon to the text console."""
        icons = {"success": "✔", "error": "✘", "warning": "⚠", "info": "ⓘ"}
        icon = icons.get(status, "ⓘ")

        text = self.get_text(key, section="status", **kwargs)
        message = f"{icon} {text}\n"

        st = self.main_frame.status_text
        st.configure(state="normal")
        st.insert(tk.END, f"- {message}")
        st.see("end")
        st.configure(state="disabled")
