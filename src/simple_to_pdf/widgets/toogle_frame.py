from simple_to_pdf.widgets import BaseFrame


class ToogleFrame(BaseFrame):
    def __init__(self, parent, *, width: int = 150, **kwargs) -> None:
        """
        Initialize the sliding panel.
        :param open_width: Width in pixels when expanded.
        :param closed_width: Width in pixels when collapsed.
        """
        super().__init__(parent, frame_type="btns_container", width=width, **kwargs)
        self.width = width
        self.is_open: bool = False
        if self.winfo_viewable():
            self.is_open: bool = True
        self.pack_propagate(False)

    def toggle(self) -> None:
        """Toggle the panel visibility using pack_forget."""
        if self.is_open:
            self.pack_forget()
            self.is_open = False
        else:
            self.pack(side="right", fill="y", pady=10, padx=10)
            self.is_open = True
