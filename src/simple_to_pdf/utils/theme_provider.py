
from simple_to_pdf.core.config import ThemeKeys,DEFAULT_COLORS
from typing import Literal

class ThemeProviderMixin:
    
    def get_color(self, key):
        return DEFAULT_COLORS.get(key, "#ffffff")
    
    def set_button_params(self)->dict:

        default_accent = self.get_color(ThemeKeys.ACCENT)
        hover_accent = self.get_color(ThemeKeys.ACCENT_HOVER)
        text_color = self.get_color(ThemeKeys.TEXT_ON_ACCENT)
        theme:dict={
            "fg_color": default_accent,     
            "hover_color": hover_accent,   
            "text_color": text_color,        
            "font": ("Segoe UI", 13, "bold"),
            "corner_radius": 8,              
            "cursor": "hand2",
            "command": None,
        }
        return theme
    
    def set_frame_params(self,*,frame_type:Literal['main','header','content','footer','btns_container','scr_frame_container'])->dict:

        match frame_type:
            case "main":
                 return {
                    "fg_color":self.get_color(ThemeKeys.BG_MAIN)
                 }
            case "header":
               return {
                    "fg_color":self.get_color(ThemeKeys.BG_HEADER)
                }
            case "content":
               return {
                    "fg_color":self.get_color(ThemeKeys.BG_MAIN)
                }
            case "footer":
                return {
                    "fg_color":self.get_color(ThemeKeys.BG_MAIN),
                }
            case "btns_container":
                return {
                    "fg_color":self.get_color(ThemeKeys.BG_MAIN),
                }
            case "scr_frame_container":
                return {
                    "fg_color":self.get_color(ThemeKeys.BG_MAIN),
                    "border_width":1,
                    "corner_radius":8
                }

    
    def set_label_params(self, label_type: str) -> dict:
        bg_color = "transparent"
        
        match label_type:
            case "badge":
                return {
                    "font": ("Consolas", 10, "bold"),
                    "text_color": self.get_color(ThemeKeys.TEXT_PRIMARY),                              
                    "fg_color": bg_color, 
                    "corner_radius": 6,                
                    "padx": 8,
                    "pady": 2
                }
            
            case "title":
                return {
                    "font": ("Segoe UI", 14, "bold"),
                    "text_color": self.get_color(ThemeKeys.TEXT_PRIMARY),
                    "fg_color": bg_color,
                    "anchor": "w"
                }
            
            case "content":
                return {
                    "font": ("Segoe UI", 12),
                    "text_color": self.get_color(ThemeKeys.TEXT_PRIMARY),
                    "fg_color": bg_color,
                    "justify": "left"
                }
        return {}

    def set_scrollable_frame_params(self, *, scr_frame_type: Literal[
        "file_list",
        "button_list",   
        "settings",     
        "preview"
    ]) -> dict:
        """
        Generates configuration parameters for different types of CTkScrollableFrames.
        Ensures consistent UI across the application using the theme's color palette.
        """
        # Base parameters shared by all scrollable frames
        params = {
            "corner_radius": 8,
            "scrollbar_button_color": self.get_color(ThemeKeys.ACCENT_DIM), # Subtle color for the scroll thumb
            "scrollbar_button_hover_color": self.get_color(ThemeKeys.ACCENT), # Vibrant color when interacting
        }
        match scr_frame_type:
            case "file_list":
                params.update({
                    "fg_color": "transparent", # Matches the main content area
                    "label_font": ("Segoe UI", 13, "bold"),        # Clear header for the file queue
                    "label_anchor": "w",                           # Left-aligned header text
                    
                })
            case "settings":
                params.update({
                    "fg_color": self.get_color(ThemeKeys.BG_HEADER), # Blends with the sidebar/navigation background
                    "orientation": "vertical",                     # Fixed vertical layout for configuration options
                })
            case "preview":
                params.update({
                    "fg_color":self.get_color(ThemeKeys.BG_PREVIEW),                 # Fixed dark neutral background for document preview
                    "border_width": 1,
                    "border_color": self.get_color(ThemeKeys.BORDER) # Visual separation from the main surface
                })
            case "button_list":
                params.update({
                    "fg_color": "transparent",                      # Seamless integration with the parent frame
                    "corner_radius": 0,
                })
        return params
    
    def set_textbox_params(self,*, textbox_type:Literal['status_text'])->dict:
        match textbox_type:
            case "status_text":
                params={
                    "fg_color":self.get_color(ThemeKeys.BG_MAIN),
                    "state":"disabled",
                    "corner_radius":10,
                    "height":100,
                    "border_width":1
                }
        return params
    
    def set_progress_params(self,*,progress_type:Literal['merge_progress'])->dict:
        match progress_type:
            case "merge_progress":
                params={
                    "height":12,
                    "progress_color":self.get_color(ThemeKeys.PROGRESS_COLOR),
                    "corner_radius":6,
                    "orientation":"horizontal"
                }
        return params


