from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox,scrolledtext
import webbrowser
import platform
import requests
import subprocess
import os
from src.simple_to_pdf.pdf import PdfMerger, PageExtractor
from src.simple_to_pdf.app_gui.main_frame import MainFrame
from src.simple_to_pdf.app_gui.list_controls_frame import ListControlsFrame
from src.simple_to_pdf.app_gui.gui_callback import GUICallback
from src.simple_to_pdf.app_gui.utils import get_text, get_files, get_pages, change_state,ui_locker

import logging

logger = logging.getLogger(__name__)

# --- App constants ---
APP_VERSION = "0.9.8"
GITHUB_USER = "hollowchest13"
GITHUB_REPO = "Simple_to_PDF"

# Dynamically constructing URLs for easier modification.
GITHUB_REPO_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"

# Path to the version.json file in the cli directory
VERSION_JSON_URL = f"{GITHUB_REPO_URL}/main/cli/version.json"
README_URL = f"{GITHUB_REPO_URL}#readme"
RELEASES_URL = f"{GITHUB_REPO_URL}/releases"

class PDFMergerGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self._init_services()
        self.init_panels()
        self.init_connections()
        self.build_gui
        handlers = self._setup_handlers()
        self.list_controls: dict[str,tk.Widget] = self.btns_panel.init_btns(callbacks = handlers)
        self.build_gui(parent = self,callbacks = handlers)
    
    def init_panels(self) -> None:
        self.main_panel: MainFrame = MainFrame(parent = self, merger = self.merger)
        self.btns_panel: ListControlsFrame = ListControlsFrame (parent = self)

    def init_connections(self) -> None:
        self.callback = GUICallback(main_frame = self.main_panel)
    
    def _init_services(self) -> None:

        """Initialize internal logic and services."""

        self.merger = PdfMerger()
        self.page_extractor = PageExtractor()

    def _toggle_menu_items(self,*,menu_obj: tk.Menu, active: bool):
        state = tk.NORMAL if active else tk.DISABLED
        # index_count gets the index of the last menu item
        last_item = menu_obj.index("end") 
    
        if last_item is not None:
            for i in range(last_item + 1):
                try:
                    menu_obj.entryconfig(i, state=state)
                except:
                    continue # Skip separators

    def toggle_ui(self,*, active: bool) -> None:

        """Enable or disable the entire UI."""

        if active:
           btns_state = tk.NORMAL
           menu_active = True
        else:
            btns_state = tk.DISABLED
            menu_active = False
        
        # Disable all buttons and menu items
        change_state(widgets_dict = self.btns_panel.ui, state = btns_state)
        # You can also disabled specific panels if needed
        self._toggle_menu_items(menu_obj = self.menu, active = menu_active)

    def build_gui(self,*, parent: tk.Tk, callbacks: dict[str, callable]) -> dict[str, tk.Widget]:

        """Builds the main GUI layout and returns a dictionary of widgets."""

        # Window settings
        parent.title("Simple to PDF - PDF Merger")
        parent.geometry("700x400")
        self.menu = self._build_menu_bar(parent = parent, callbacks = callbacks)
        self.main_panel.pack(side = "left", fill = "both", expand = True)
        self.btns_panel.pack(side = "right", fill = "both")

    def _build_menu_bar(self,*, parent: tk.Tk, callbacks: dict[str, callable]) -> tk.Menu:
        
        """Builds the menu bar for the application."""

        menu_bar = tk.Menu(parent)
        parent.config(menu = menu_bar)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff = 0)
        file_menu.add_command(label = "Add Files", command = callbacks['add'])
        file_menu.add_command(label = "Merge to PDF", command = callbacks['merge'])
        file_menu.add_command(label = "Extract pages", command = callbacks['extract'])
        file_menu.add_command(label = "Remove file", command = callbacks['remove'])
        file_menu.add_command(label = "Clear status",command = callbacks['clear_status'])
        file_menu.add_separator()
        file_menu.add_command(label = "Exit", command = parent.quit)
        menu_bar.add_cascade(label = "File", menu = file_menu)

        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff = 0)
        help_menu.add_command(label = "License", command = callbacks['license'])
        help_menu.add_command(label = "How to use", command = callbacks['documentation'])
        help_menu.add_command(label = "About", command = callbacks['about'])
        help_menu.add_command(label = "Check updates", command = callbacks['update'])
        help_menu.add_command(label= "Show logs", command = callbacks['logs'])
        menu_bar.add_cascade(label = "Help", menu = help_menu)

        return menu_bar
    
    def open_log_folder(self):
        # "The path must match the one in setup_logger
        log_dir = Path.home() / ".simple_to_pdf" / "logs"
    
        # "If the folder in home doesn't exist, checking the local folde
        if not log_dir.exists():
            log_dir = Path("logs")
    
        # If the folder still doesn't exist (the program hasn't written anything yet)
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

        path_str = str(log_dir.absolute())

        if platform.system() == "Windows":
            # "Opening Windows Explorer" (або "Opens Windows Explorer")
            os.startfile(path_str)
        elif platform.system() == "Linux":
            # for Linux
            clean_env = os.environ.copy()
             # Removing variables related to my Python
            clean_env.pop("PYTHONPATH", None)
            clean_env.pop("PYTHONHOME", None)
            try:
                subprocess.Popen(
                    ["xdg-open",path_str],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
                )
            except Exception as e:
                logger.error(f":Could not open folder: {e}")
            

    def _setup_handlers(self) -> dict:

        """Create a dictionary of commands to pass to the Builder."""

        handlers: dict[str, callable] = {
            'add': self.main_panel.add_files,
            'merge': self.on_merge,
            'extract': self.prompt_pages_to_remove,
            'remove': self.main_panel.remove_files,
            'move': self.main_panel.move_on_listbox,
            'license': self.show_license,
            'documentation':self.show_documentation,
            'update': self.check_updates,
            'about': self.show_about,
            'clear_status': self.main_panel.clear_status_text,
            'logs': self.open_log_folder
            }
        return handlers
    
    def check_updates(self):

        """Fetches the latest version info from GitHub and prompts for update."""

        try:
            # Requesting the version file
            response = requests.get(VERSION_JSON_URL, timeout = 5)
            response.raise_for_status()
        
            data = response.json()
            latest_version = data.get("version")
            release_notes = data.get("notes", "No release notes provided.")

            if latest_version == APP_VERSION:
                messagebox.showinfo("Update Check", f"You are up to date!\nVersion {APP_VERSION} is the latest.")
            else:
                # New version found
                message = (
                    f"A new version is available: {latest_version}\n\n"
                    f"What's new:\n{release_notes}\n\n"
                    "Would you like to visit the download page?"
                )
                if messagebox.askyesno("Update Available", message):
                   webbrowser.open(RELEASES_URL)
        except requests.exceptions.RequestException as e:
            logger.error(f"Update check failed (Network error): {e}")
            messagebox.showerror("Update Error", "Could not connect to the update server.\nPlease check your internet connection.")
        except Exception as e:
            logger.error(f"Update check failed (Parse error): {e}")
            messagebox.showerror("Update Error", f"An unexpected error occurred:\n{e}")

    def show_about(self):

        """Displays a modal window with application information."""

        about_window = tk.Toplevel(self)
        about_window.title("About")
        about_window.geometry("380x280")
        about_window.resizable(False, False)
        about_window.transient(self)
        about_window.grab_set()

        # App Title & Version
        tk.Label(about_window, text = GITHUB_REPO, font=("Arial", 12, "bold")).pack(pady=15)
        tk.Label(about_window, text=f"Application Version: {APP_VERSION}").pack()
    
        # Engine Info (Dynamic check)
        engine_class = getattr(self.merger.converter, '__class__', None)
        engine_name = engine_class.__name__ if engine_class else "Unknown"
        tk.Label(about_window, text=f"Conversion Engine: {engine_name}", fg = "gray").pack(pady=5)

        # Description
        desc = "A professional tool for batch converting\nand merging documents into PDF."
        tk.Label(about_window, text = desc, justify = "center", pady = 10).pack()

        # Footer
        tk.Label(about_window, text = "© 2026 All Rights Reserved", font = ("Arial", 8)).pack(side = "bottom", pady = 10)
    
        tk.Button(about_window, text = "Project GitHub", width = 20, command = lambda: webbrowser.open(GITHUB_REPO_URL)).pack(pady=5)

    def show_license(self) -> None:
        license_file_name: str = "LICENSE"
        license_path = Path(__file__).parent.parent / "LICENSE"
        license_text: str = get_text(file_name = license_file_name,file_path = license_path)
        if not license_text:
            return
        self._create_text_window(title = "LICENSE",text = license_text)

    def _create_text_window(self,*,text: str,title: str,size: str = "700x400",text_font: str = "Consolas",font_size: int = 10) -> None:
        top = tk.Toplevel(self)
        top.title(title)
        top.geometry(size)
        top.resizable(False,False)
        txt:scrolledtext.ScrolledText = scrolledtext.ScrolledText(top, wrap = tk.WORD,font = (text_font,font_size))
        txt.insert(tk.END,text)
        txt.config(state = tk.DISABLED)
        txt.pack(expand = True, fill = "both", padx = 10, pady = 10)
        btn_close:tk.Button = tk.Button(top, text = "Got it!", command = top.destroy)
        btn_close.pack(pady = 5)

    def show_documentation(self) -> None:
        webbrowser.open(README_URL)

    def on_merge(self):

        """Handler for Merge button click"""
       
        # Preparing data (quick operation, doing in main thread)
        files = self.main_panel.load_from_listbox()

        if not files:
            messagebox.showwarning("Warning", "No files to merge")
            return

        out = filedialog.asksaveasfilename(
            title = "Save Merged PDF", 
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile = "merged.pdf"
        )
        if not out: 
            return

        self._run_merge_worker(files = files, output_path=out)

    @ui_locker
    def _run_merge_worker(self, files, output_path):
        try:
            # Reset progress bar
            self.main_panel.progress_bar_reset()

            # Give this safe wrapper to the engine
            self.merger.merge_to_pdf(
                files = files, 
                output_path = output_path, 
                callback = self.callback.safe_callback # Use the wrapper
            )
            self.main_panel.after(0, lambda: self.callback.show_status_message(f"Merged PDF saved to:\n{output_path}"))
        except Exception as e:
            err_msg = f"❌ Error: Could not merge files: \n{e}"
            logger.error(err_msg, exc_info = True)
            self.after(0, lambda: self.callback.show_status_message(err_msg))
            if self.main_panel.progress_bar['mode'] == "indeterminate":
                self.after(0,lambda: self.main_panel.set_progress_determinate())
        
    def prompt_pages_to_remove(self):
        input_path: str = get_files(filetypes = "*.pdf", multiple = False)

        if not input_path:
            return
        
        win = tk.Toplevel(self)
        win.title("Pages to extract")
        win.geometry("350x170")
        win.transient(self)
        win.grab_set()

        # Create a label and entry for page selection
        # Main instruction
        tk.Label(win, text = "Select pages to extract:", font = ("TkDefaultFont", 10, "bold")).pack(pady=(20, 0))

        # Format description (hint)
        hint_text = "Format: 1, 3, 5-10\n(use commas for single pages and dashes for ranges)"
        tk.Label(win, text = hint_text, fg = "gray", font = ("TkDefaultFont", 9)).pack(pady = (0, 10))
        entry = tk.Entry(win)
        entry.pack(fill = "x", padx = 10)
        tk.Button(
            win, 
            text = "OK", 
            width = 10,    # Width in characters
            height = 1,    # Height in text lines
            command = lambda: self.on_confirm(
                raw_input = entry.get(), 
                input_path = input_path, 
                win = win
            )
        ).pack(pady = 12)

    def on_confirm(self, *, raw_input: str, input_path: str, win: tk.Toplevel) -> None:

        # Parse string input into a list of page indices
        pages = get_pages(raw = raw_input.strip())

        if pages is None:
            messagebox.showwarning(
                "Invalid Input", 
                "Please use the correct format (e.g., 1-5, 8, 10-12).",
                parent = win
            )
            return

        # Validate page numbers against the actual PDF file
        try:
            self.page_extractor.validate_pages(input_path = input_path, pages_to_extract = pages)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent = win)
            return
        except Exception as e:
            messagebox.showerror("File Error", f"Could not read PDF: {e}", parent = win)
            return

        # Ask user for the output destination
        output_path = filedialog.asksaveasfilename(
            defaultextension = ".pdf",
            filetypes = [("PDF files", "*.pdf")],
            initialfile = f"extracted_{Path(input_path).stem}.pdf",
            title = "Save PDF"
        )

        if not output_path:
            return

        # Close input window and start the background worker thread
        win.destroy()

        self._run_page_extractor_worker(
            input_path=input_path,
            pages=pages,
            output_path=output_path
        )
     
    @ui_locker
    def _run_page_extractor_worker(self, input_path, pages, output_path):
        try:
             # Reset progress bar
            self.main_panel.progress_bar_reset()
            self.page_extractor.extract_pages(input_path = input_path, pages_to_extract = pages, output_path = output_path, callback = self.callback.safe_callback)
            self.callback.show_status_message(f"✅ Extraction completed successfully! Extracted pages saved to:\n{output_path}")

        except Exception as e:
            error_msg = f"❌ Error during page extraction: {e}"
            if isinstance(e, ValueError):
                self.after(0, lambda: messagebox.showerror("Extraction Error", error_msg))
            else:   
                self.callback.show_status_message(status_message = error_msg)
                logger.error(error_msg, exc_info = True)
                self.after(0,lambda: self.main_panel.progress_bar_reset())
            
def run_gui():
    app = PDFMergerGUI()
    app.mainloop()