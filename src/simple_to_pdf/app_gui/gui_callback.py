from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from simple_to_pdf.app_gui.main_frame import MainFrame
import logging
import tkinter as tk
from collections.abc import Callable
from typing import Literal

from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin

logger = logging.getLogger(__name__)


class GUICallback(ThemeProviderMixin, LocalizationMixin):
    def __init__(self, main_frame: MainFrame, schedule: Callable[..., Any]):
        self.main_frame = main_frame
        self._schedule_task = schedule

    def safe_callback(
        self, event_type: Literal["status", "progress"], **params
    ) -> None:
        """Can be called from any thread; hands the event over to the UI thread."""
        self._schedule_task(self._handle_event, event_type, **params)

    def _handle_event(
        self, event_type: Literal["status", "progress"], **params
    ) -> None:
        """Routes GUI events. Always runs in the main (UI) thread."""
        match event_type:
            case "progress":
                self._progress_bar_update(
                    stage=params.get("stage", "processing"),
                    mode=params.get("mode", "indeterminate"),
                    current=params.get("current", 0),
                    total=params.get("total", 0),
                    filename=params.get("filename", ""),
                )

            case "status":
                status_params = params.copy()
                status_key = status_params.pop("key")
                status_type = status_params.pop("status", "info")
                self._set_status(key=status_key, status=status_type, **status_params)

            case _:
                logger.warning("Unknown GUI event type: %s", event_type)

    def _progress_bar_update(
        self,
        *,
        stage: Literal["processing", "converting", "merging", "ready"] = "processing",
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

        match mode:
            case "indeterminate":
                if pb.cget("mode") != "indeterminate":
                    pb.configure(mode="indeterminate", progress_color=active_color)
                    pb.start()
                progress_text = self.get_text(
                    "indeterminate", section=LOC_SECTION, stage=stage_text
                )
            case _:
                if pb.cget("mode") == "indeterminate":
                    pb.stop()
                    pb.configure(mode="determinate")

        progress_float = (current / total) if total > 0 else 0
        pb.configure(progress_color=active_color if progress_float > 0 else idle_color)
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

    def _set_status(self, key: str, status: str = "info", **kwargs) -> None:
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
