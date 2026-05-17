from abc import ABC, abstractmethod
from typing import Literal, Dict, Any
from simple_to_pdf.core.config import ThemeKeys, DEFAULT_COLORS


class ThemeProviderMixin:
    def get_color(self, key):
        return DEFAULT_COLORS.get(key, "#ffffff")


class WidgetThemeProviderMixin(ThemeProviderMixin, ABC):
    @abstractmethod
    def set_params(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        pass


class ButtonThemeMixin(WidgetThemeProviderMixin):
    def set_params(self) -> Dict[str, Any]:

        default_accent = self.get_color(ThemeKeys.ACCENT)
        hover_accent = self.get_color(ThemeKeys.ACCENT_HOVER)
        text_color = self.get_color(ThemeKeys.TEXT_ON_ACCENT)
        params: Dict[str, Any] = {
            "fg_color": default_accent,
            "hover_color": hover_accent,
            "text_color": text_color,
            "font": ("Segoe UI", 13, "bold"),
            "corner_radius": 8,
            "cursor": "hand2",
            "command": None,
        }
        return params


class FrameThemeMixin(WidgetThemeProviderMixin):
    def set_params(
        self,
        *,
        frame_type: Literal[
            "main",
            "header",
            "content",
            "footer",
            "btns_container",
            "scr_frame_container",
            "list_item",
        ],
    ) -> Dict[str, Any]:

        match frame_type:
            case "main":
                return {"fg_color": self.get_color(ThemeKeys.BG_MAIN)}
            case "header":
                return {"fg_color": self.get_color(ThemeKeys.BG_HEADER)}
            case "content":
                return {"fg_color": self.get_color(ThemeKeys.BG_MAIN)}
            case "footer":
                return {
                    "fg_color": self.get_color(ThemeKeys.BG_MAIN),
                }
            case "btns_container":
                return {
                    "fg_color": self.get_color(ThemeKeys.BG_MAIN),
                }
            case "scr_frame_container":
                return {
                    "fg_color": self.get_color(ThemeKeys.BG_MAIN),
                    "border_width": 1,
                    "corner_radius": 8,
                }
            case "list_item":
                return {"fg_color": "transparent"}


class LabelThemeMixit(WidgetThemeProviderMixin):
    def set_params(self, label_type: str) -> Dict[str, Any]:
        bg_color = "transparent"

        match label_type:
            case "badge":
                return {
                    "font": ("Segoe UI", 12, "bold"),
                    "text_color": self.get_color(ThemeKeys.TEXT_PRIMARY),
                    "fg_color": bg_color,
                    "corner_radius": 6,
                }
            case "subtitle":
                return {
                    "font": ("Segoe UI", 14, "italic"),
                    "text_color": self.get_color(ThemeKeys.TEXT_SECONDARY),
                    "fg_color": bg_color,
                    "corner_radius": 6,
                    "anchor": "center",
                }

            case "title":
                return {
                    "font": ("Segoe UI", 16, "bold"),
                    "text_color": self.get_color(ThemeKeys.TEXT_TITLE),
                    "fg_color": bg_color,
                    "anchor": "center",
                }

            case "content":
                return {
                    "font": ("Segoe UI", 14),
                    "text_color": self.get_color(ThemeKeys.TEXT_CONTENT),
                    "fg_color": bg_color,
                    "justify": "left",
                }
        return {}


class ScrolableFrameThemeMixin(WidgetThemeProviderMixin):
    def set_params(
        self,
        *,
        scr_frame_type: Literal["file_list", "button_list", "settings", "preview"],
    ) -> Dict[str, Any]:
        """
        Generates configuration parameters for different types of CTkScrollableFrames.
        Ensures consistent UI across the application using the theme's color palette.
        """
        # Base parameters shared by all scrollable frames
        params = {
            "corner_radius": 8,
            "scrollbar_button_color": self.get_color(
                ThemeKeys.ACCENT_DIM
            ),  # Subtle color for the scroll thumb
            "scrollbar_button_hover_color": self.get_color(
                ThemeKeys.ACCENT
            ),  # Vibrant color when interacting
        }
        match scr_frame_type:
            case "file_list":
                params.update(
                    {
                        "fg_color": "transparent",  # Matches the main content area
                        "label_font": (
                            "Segoe UI",
                            13,
                            "bold",
                        ),  # Clear header for the file queue
                        "label_anchor": "w",  # Left-aligned header text
                    }
                )
            case "settings":
                params.update(
                    {
                        "fg_color": self.get_color(
                            ThemeKeys.BG_HEADER
                        ),  # Blends with the sidebar/navigation background
                        "orientation": "vertical",  # Fixed vertical layout for configuration options
                    }
                )
            case "preview":
                params.update(
                    {
                        "fg_color": self.get_color(
                            ThemeKeys.BG_PREVIEW
                        ),  # Fixed dark neutral background for document preview
                        "border_width": 1,
                        "border_color": self.get_color(
                            ThemeKeys.BORDER
                        ),  # Visual separation from the main surface
                    }
                )
            case "button_list":
                params.update(
                    {
                        "fg_color": "transparent",  # Seamless integration with the parent frame
                        "corner_radius": 0,
                    }
                )
        return params


class TextboxThemeMixin(WidgetThemeProviderMixin):
    def set_params(
        self, *, textbox_type: Literal["status_text", "info"]
    ) -> Dict[str, Any]:
        match textbox_type:
            case "status_text":
                params = {
                    "fg_color": self.get_color(ThemeKeys.BG_MAIN),
                    "state": "disabled",
                    "corner_radius": 10,
                    "height": 100,
                    "border_width": 1,
                }
            case "info":
                params = {
                    "wrap": "word",
                    "font": ("Segoe UI", 14),
                    "fg_color": self.get_color(ThemeKeys.BG_MAIN),
                    "text_color": self.get_color(ThemeKeys.TEXT_CONTENT),
                    "scrollbar_button_color": self.get_color(ThemeKeys.ACCENT),
                    "corner_radius": 10,
                    "border_width": 0,
                }
        return params


class ProgressThemeMixin(WidgetThemeProviderMixin):
    def set_params(self, *, progress_type: Literal["merge_progress"]) -> Dict[str, Any]:
        match progress_type:
            case "merge_progress":
                params = {
                    "height": 12,
                    "progress_color": self.get_color(ThemeKeys.PROGRESS_COLOR),
                    "corner_radius": 6,
                    "orientation": "horizontal",
                }
        return params


class OptionMenuThemeMixin(WidgetThemeProviderMixin):
    def set_params(self, menu_type: str = "standard") -> Dict[str, Any]:
        accent = self.get_color(ThemeKeys.ACCENT)
        accent_hover = self.get_color(ThemeKeys.ACCENT_HOVER)

        # Base parameters for CTkOptionMenu
        params = {
            "fg_color": accent,
            "button_color": accent_hover,
            "button_hover_color": accent,
            "text_color": self.get_color(ThemeKeys.TEXT_ON_ACCENT),
            "dropdown_fg_color": self.get_color(ThemeKeys.BG_MAIN),
            "dropdown_hover_color": accent,
            "dropdown_text_color": self.get_color(ThemeKeys.TEXT_CONTENT),
            "font": ("Segoe UI", 13),
            "dropdown_font": ("Segoe UI", 13),
            "corner_radius": 8,
            "anchor": "center",
        }

        # Specific adjustments for settings rows
        if menu_type == "settings":
            params.update({"width": 140, "dynamic_resizing": False})

        return params


class SwitcherThemeMixin(WidgetThemeProviderMixin):
    def set_params(self, variable: Any, text: str = "", **kwargs) -> Dict[str, Any]:
        "Return style parameters for CTKSwitch."
        accent_color = self.get_color(ThemeKeys.ACCENT)
        text_color = self.get_color(ThemeKeys.TEXT_CONTENT)
        button_color = self.get_color(ThemeKeys.TEXT_PRIMARY)

        params: Dict[str, Any] = {
            "variable": variable,
            "text": text,  # Зазвичай "" (якщо підпис робимо через Label)
            "progress_color": accent_color,  # Колір лінії, коли світчер ON
            "button_color": button_color,  # Колір кульки у вимкненому стані
            "button_hover_color": accent_color,  # Колір кульки при наведенні
            "text_color": text_color,
            "font": ("Segoe UI", 13),
            "cursor": "hand2",
        }
        params.update(**kwargs)
        return params
