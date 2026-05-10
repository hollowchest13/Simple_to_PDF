from simple_to_pdf.widgets import BaseFrame, BaseScrollableFrame


class SlidingFrame(BaseFrame):
    def __init__(
        self, parent, *, open_width: int = 150, closed_width: int = 0, **kwargs
    ) -> None:
        """
        Initialize the sliding panel.
        :param open_width: Width in pixels when expanded.
        :param closed_width: Width in pixels when collapsed.
        """
        super().__init__(
            parent, frame_type="scr_frame_container", width=closed_width, **kwargs
        )
        self.open_width = open_width
        self.closed_width = closed_width
        self.is_open = False
        self.pack_propagate(False)

    def toggle(self) -> None:
        """Toggle the panel visibility with a sliding animation."""
        target = self.closed_width if self.is_open else self.open_width
        self._animate_width(target=target)
        self.is_open = not self.is_open

    def _animate_width(self, *, target: int) -> None:
        """Incrementally adjust frame width to create a smooth transition."""
        current_width = int(self.cget("width"))
        step = 100

        if abs(current_width - target) > step:
            # Using ternary for concise textbook examples
            new_width = (
                current_width + step if current_width < target else current_width - step
            )
            self.configure(width=new_width)
            self.after(10, lambda: self._animate_width(target=target))
        else:
            self.configure(width=target)
