import tkinter as tk
import tkinter.ttk as ttk

class GUICallback:
    def __init__(self,*, main_app: tk.Tk):

        # Saving link to main window (PDFGUIMerger)
        self.app = main_app

    def safe_callback(self, **kwargs) -> None:
        """
        Using self.app.after, because after belongs to the main window.
        """
        data = kwargs.copy()
        status_message = data.pop('status_message', None)

        # Pass updates to the GUI thread queue

        self.app.after(0, lambda: self.progress_bar_update(**data))
        if status_message:
            self.app.after(0, lambda: self.show_status_message(status_message = status_message))

    def progress_bar_update(self,*, stage: str = "Processing", progress_bar_mode: str = "indeterminate", current: int = 0, total: int = 0, filename: str = "") -> None:
        ui: dict[str, tk.Widget] = self.app.ui

        # 2. Check types for specific widgets (now pb.start() methods will be highlighted)
        # Using ttk.Progressbar, because it has start/stop methods
        pb: ttk.Progressbar = ui['progress_bar'] 
        pl: tk.Label = ui['progress_label']

        if pb['mode'] != progress_bar_mode:
            pb.stop()
            pb.config(mode = progress_bar_mode)
    
        if progress_bar_mode == "indeterminate":
            pb.start(10)
            status_text = f"{stage} documents..."
        else:
            pb.stop()
            percent = (current / total * 100) if total > 0 else 0
            pb['value'] = percent
        
            display_name = (filename[:27] + '...') if len(filename) > 30 else filename
            status_text = f"{stage}: {display_name} ({current}/{total}) — {percent:.1f}%"

        pl.config(text = status_text)

        if filename and progress_bar_mode == "determinate":
            self.show_status_message(f"✅ {stage} successfully: {filename}")

        self.app.update_idletasks()

    def show_status_message(self, status_message: str):
        ui: dict[str, tk.Text] = self.app.ui
        if 'status_text' in ui:
            st: tk.Text = ui['status_text']
            st.config(state="normal")
            st.insert(tk.END, f"- {status_message}\n")
            st.see(tk.END)
            st.config(state = "disabled")

    def progress_bar_reset(self):
        ui: dict[str, ttk.Progressbar] = self.app.ui
        ui['progress_bar'].stop()
        ui['progress_bar'].config(mode = 'determinate', value = 0)
        ui['progress_label'].config(text = "Progress: Ready")
        self.app.update_idletasks()