import logging
import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext
from typing import Callable

from simple_to_pdf.app_gui.gui_callback import GUICallback
from simple_to_pdf.app_gui.list_controls_frame import ListControlsFrame
from simple_to_pdf.app_gui.main_frame import MainFrame
from simple_to_pdf.cli.logger import get_log_dir
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.pdf import PageExtractor, PdfMerger
from simple_to_pdf.utils.file_tools import get_files
from simple_to_pdf.utils.logic import get_pages
from simple_to_pdf.utils.ui_tools import change_state, ui_locker
from simple_to_pdf.app_gui.about_dialog import AboutDialog
from simple_to_pdf.app_gui.update_dialog import UpdateDialog
from simple_to_pdf.app_gui.info_dialog import InfoDialog
from simple_to_pdf.core import config

logger = logging.getLogger(__name__)

class PDFMergerGUI(tk.Tk):
    APP_NAME: str = "Simple_to_PDF"

    def __init__(self, *, merger: PdfMerger, page_extractor: PageExtractor,version_controller:VersionController):
        super().__init__()
        self.merger = merger
        self.page_extractor = page_extractor
        self.version_controller=version_controller
        self.init_panels()
        self.init_connections()
        handlers = self._setup_handlers()
        self.list_controls: dict[str, tk.Widget] = self.btns_panel.init_btns(callbacks=handlers)
        self.build_gui(parent=self, callbacks=handlers)

    def init_panels(self) -> None:
        self.main_panel: MainFrame = MainFrame(parent=self, merger=self.merger)
        self.btns_panel: ListControlsFrame = ListControlsFrame(parent=self)

    def init_connections(self) -> None:
        self.callback = GUICallback(main_frame=self.main_panel)

    def _toggle_menu_items(self, *, menu_obj: tk.Menu, active: bool):
        state = tk.NORMAL if active else tk.DISABLED
        # index_count gets the index of the last menu item
        last_item = menu_obj.index("end")

        if last_item is not None:
            for i in range(last_item + 1):
                try:
                    menu_obj.entryconfig(i, state=state)
                except:  # noqa: E722
                    continue  # Skip separators

    def toggle_ui(self, *, active: bool) -> None:
        """Enable or disable the entire UI."""

        if active:
            btns_state = tk.NORMAL
            menu_active = True
        else:
            btns_state = tk.DISABLED
            menu_active = False

        # Disable all buttons and menu items
        change_state(widgets_dict=self.btns_panel.ui, state=btns_state)

        # You can also disabled specific panels if needed
        self._toggle_menu_items(menu_obj=self.menu, active=menu_active)

    def build_gui(
        self, *, parent: tk.Tk, callbacks: dict[str, Callable]
    ) -> None:
        """Builds the main GUI layout"""

        # Window settings
        parent.title(f"{self.APP_NAME} - PDF Merger")
        parent.geometry("700x400")
        self.menu = self._build_menu_bar(parent=parent, callbacks=callbacks)
        self.main_panel.pack(side="left", fill="both", expand=True)
        self.btns_panel.pack(side="right", fill="both")

    def _build_menu_bar(
        self, *, parent: tk.Tk, callbacks: dict[str, Callable]
    ) -> tk.Menu:
        """Builds the menu bar for the application."""

        menu_bar = tk.Menu(parent)
        parent.config(menu=menu_bar)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Add Files", command=callbacks["add"])
        file_menu.add_command(label="Merge to PDF", command=callbacks["merge"])
        file_menu.add_command(label="Extract pages", command=callbacks["extract"])
        file_menu.add_command(label="Remove file", command=callbacks["remove"])
        file_menu.add_command(label="Clear status", command=callbacks["clear_status"])
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=parent.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="License", command=callbacks["license"])
        help_menu.add_command(label="How to use", command=callbacks["documentation"])
        help_menu.add_command(label="About", command=callbacks["about"])
        help_menu.add_command(label="Check updates", command=callbacks["update"])
        help_menu.add_command(label="Show logs", command=callbacks["logs"])
        menu_bar.add_cascade(label="Help", menu=help_menu)

        return menu_bar

    def open_log_folder(self):
        """Handles the OS-specific logic to open the file explorer."""

        # Primary path in the user's home directory
        log_dir = get_log_dir()

        # Get the absolute path as a string
        path_str = str(log_dir.absolute())

        if sys.platform == "win32":
            # On Windows, os.startfile handles the explorer process correctly
            try:
                os.startfile(path_str)
            except Exception as e:
                logger.error(f"Could not open folder on Windows: {e}")

        elif sys.platform == "linux":
            # Create a clean environment copy to avoid library conflicts
            # PyInstaller sets LD_LIBRARY_PATH which can break system apps like xdg-open
            clean_env = os.environ.copy()

            # Remove variables that might point to the bundled PyInstaller libraries
            vars_to_remove = ["LD_LIBRARY_PATH", "PYTHONPATH", "PYTHONHOME"]
            for var in vars_to_remove:
                clean_env.pop(var, None)

            try:
                # Use xdg-open with the cleaned environment
                subprocess.Popen(
                    ["xdg-open", path_str],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=clean_env,  # Critical for bundled Linux applications
                )
            except Exception as e:
                logger.error(f"Could not open folder on Linux: {e}", exc_info=True)

    def _setup_handlers(self) -> dict:
        """Create a dictionary of commands to pass to the Builder."""

        handlers: dict[str, Callable] = {
            "add": self.main_panel.add_files,
            "merge": self.on_merge,
            "extract": self.prompt_pages_to_remove,
            "remove": self.main_panel.remove_files,
            "move": self.main_panel.move_on_listbox,
            "license": self.show_license,
            "documentation": self.show_documentation,
            "update": self.on_check_updates_click,
            "about": self.show_about,
            "clear_status": self.main_panel.clear_status_text,
            "logs": self.open_log_folder,
        }
        return handlers

    def on_check_updates_click(self):
        """
        Handles the update check event from the UI.
        """
        # 1. Fetch data from controller
        result = self.version_controller.check_for_updates()

        # 2. Handle errors
        if result.error_message:
            messagebox.showerror(
                "Update Error", 
                f"Unable to check for updates:\n{result.error_message}"
            )
            return

        # 3. If update found, show the beautiful dialog
        if result.is_available and result.release:
            UpdateDialog(self, result.release)
    
        # 4. If no update found
        else:
            current_v = self.version_controller._get_current_version()
            messagebox.showinfo(
                "Software Update", 
                f"You're all set! Version {current_v} is the latest available."
            )

    def show_about(self):
        """Gathers data and displays the About Dialog."""
        # 1. Get version from controller
        current_version = self.version_controller._get_current_version()
    
        # 2. Get engine name
        engine_class = getattr(self.merger.converter, "__class__", None)
        engine_name = engine_class.__name__ if engine_class else "Unknown"

        # 3. Open the dialog
        AboutDialog(self, current_version, engine_name)

    def show_license(self) -> None:
        """Displays the license file in a styled TextWindow."""
        license_path = config.LICENCE_PATH

        # 1. Check if file exists
        if not license_path.exists():
            logger.warning(f"⚠️ License file not found at path: {license_path}")
            messagebox.showwarning(
                "File Not Found", 
                f"License file could not be found at:\n{license_path}"
            )
            return

        try:
            # 2. Reading file (UTF-8 is essential for cross-platform compatibility)
            text = license_path.read_text(encoding="utf-8")

             # 3. Call the new class instead of the old method
            InfoDialog(
                self, 
                text=text, 
                title="License Agreement", 
                header_title="MIT License - Simple to PDF", # Заголовок всередині вікна
                text_font="Consolas",  # Моноширинний шрифт для офіційних документів
                font_size=10,
                size="700x600"
            )
        
        except Exception as e:
            logger.error(f"❌ Error reading license file: {e}")
            messagebox.showerror(
                "Read Error", 
                f"An error occurred while reading the license:\n{str(e)}"
            )
    def show_documentation(self) -> None:
        webbrowser.open(config.README_URL)

    def on_merge(self):
        """Handler for Merge button click"""

        # Preparing data (quick operation, doing in main thread)
        files = self.main_panel.load_from_listbox()

        if not files:
            messagebox.showwarning("Warning", "No files to merge")
            return

        out = filedialog.asksaveasfilename(
            title="Save Merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="merged.pdf",
        )
        if not out:
            return

        self._run_merge_worker(files=files, output_path=out)

    @ui_locker
    def _run_merge_worker(self, files, output_path):
        try:
            # Reset progress bar
            self.main_panel.progress_bar_reset()

            # Give this safe wrapper to the engine
            self.merger.merge_to_pdf(
                files=files,
                output_path=output_path,
                callback=self.callback.safe_callback,  # Use the wrapper
            )
            self.main_panel.after(
                0,
                lambda: self.callback.show_status_message(
                    f"Merged PDF saved to:\n{output_path}"
                ),
            )
        except Exception as e:
            err_msg = f"❌ Error: Could not merge files: \n{e}"
            logger.error(err_msg, exc_info=True)
            self.after(0, lambda: self.callback.show_status_message(err_msg))
            if self.main_panel.progress_bar["mode"] == "indeterminate":
                self.after(0, lambda: self.main_panel.set_progress_determinate())

    def prompt_pages_to_remove(self):
        input_path = get_files(filetypes=[("PDF files", "*.pdf")], multiple=False)

        if not input_path:
            return

        win = tk.Toplevel(self)
        win.title("Pages to extract")
        win.geometry("350x170")
        win.transient(self)
        win.grab_set()

        # Create a label and entry for page selection
        # Main instruction
        tk.Label(
            win, text="Select pages to extract:", font=("TkDefaultFont", 10, "bold")
        ).pack(pady=(20, 0))

        # Format description (hint)
        hint_text = (
            "Format: 1, 3, 5-10\n(use commas for single pages and dashes for ranges)"
        )
        tk.Label(win, text=hint_text, fg="gray", font=("TkDefaultFont", 9)).pack(
            pady=(0, 10)
        )
        entry = tk.Entry(win)
        entry.pack(fill="x", padx=10)
        tk.Button(
            win,
            text="OK",
            width=10,  # Width in characters
            height=1,  # Height in text lines
            command=lambda: self.on_confirm(
                raw_input=entry.get(), input_path=input_path, win=win
            ),
        ).pack(pady=12)

    def on_confirm(self, *, raw_input: str, input_path: str, win: tk.Toplevel) -> None:
        # Parse string input into a list of page indices
        pages = get_pages(raw=raw_input.strip())

        if pages is None:
            messagebox.showwarning(
                "Invalid Input",
                "Please use the correct format (e.g., 1-5, 8, 10-12).",
                parent=win,
            )
            return

        # Validate page numbers against the actual PDF file
        try:
            self.page_extractor.validate_pages(
                input_path=Path(input_path), pages_to_extract=pages
            )
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=win)
            return
        except Exception as e:
            messagebox.showerror("File Error", f"Could not read PDF: {e}", parent=win)
            return

        # Ask user for the output destination
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"extracted_{Path(input_path).stem}.pdf",
            title="Save PDF",
        )

        if not output_path:
            return

        # Close input window and start the background worker thread
        win.destroy()

        self._run_page_extractor_worker(
            input_path=input_path, pages=pages, output_path=output_path
        )

    @ui_locker
    def _run_page_extractor_worker(self, input_path, pages, output_path):
        try:
            # Reset progress bar
            self.main_panel.progress_bar_reset()
            self.page_extractor.extract_pages(
                input_path=input_path,
                pages_to_extract=pages,
                output_path=output_path,
                callback=self.callback.safe_callback,
            )
            self.callback.show_status_message(
                f"✅ Extraction completed successfully! Extracted pages saved to:\n{output_path}"
            )

        except Exception as e:
            error_msg = f"❌ Error during page extraction: {e}"
            if isinstance(e, ValueError):
                self.after(
                    0, lambda: messagebox.showerror("Extraction Error", error_msg)
                )
            else:
                self.callback.show_status_message(status_message=error_msg)
                logger.error(error_msg, exc_info=True)
                self.after(0, lambda: self.main_panel.progress_bar_reset())
