import tkinter as tk
import tkinter.ttk as ttk

from src.simple_to_pdf.app_gui.main_frame import MainFrame


class GUICallback:
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
        pb: ttk.Progressbar = self.main_frame.progress_bar
        pl: tk.Label = self.main_frame.progress_label

        if pb["mode"] != progress_bar_mode:
            pb.stop()
            pb.config(mode=progress_bar_mode)

        if progress_bar_mode == "indeterminate":
            pb.start(10)
            status_text = f"{stage} documents..."
        else:
            pb.stop()
            percent = (current / total * 100) if total > 0 else 0
            pb["value"] = percent

            display_name = (filename[:27] + "...") if len(filename) > 30 else filename
            status_text = (
                f"{stage}: {display_name} ({current}/{total}) — {percent:.1f}%"
            )

        pl.config(text=status_text)

        if filename and progress_bar_mode == "determinate":
            self.show_status_message(f"✅ {stage} successfully: {filename}")
        self.main_frame.update_idletasks()

    def show_status_message(self, status_message: str):
        st: tk.Text = self.main_frame.status_text
        st.config(state="normal")
        st.insert(tk.END, f"- {status_message}\n")
        st.see(tk.END)
        st.config(state="disabled")
