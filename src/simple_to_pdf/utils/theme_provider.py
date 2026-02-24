
from simple_to_pdf.core.config import ThemeKeys,DEFAULT_COLORS
from typing import Literal
import tkinter as tk

class ThemeProviderMixin:
    
    def get_color(self, key):
        return DEFAULT_COLORS.get(key, "#ffffff")
    
    def set_button_params(self)->dict:

        default_accent = self.get_color(ThemeKeys.ACCENT)
        hover_accent = self.get_color(ThemeKeys.ACCENT_HOVER)
        text_color = self.get_color(ThemeKeys.TEXT_ON_ACCENT)
        theme:dict={
            "text": "Button",
            "fg_color": default_accent,     
            "hover_color": hover_accent,   
            "text_color": text_color,        
            "font": ("Segoe UI", 13, "bold"),
            "corner_radius": 8,              
            "cursor": "hand2",
            "command": None,
        }
        return theme
    
    def set_frame_background(self,*,frame_type:Literal['main','header','content','footer'])->str:
        match frame_type:
            case "main":
                bg_color=self.get_color(ThemeKeys.BG_MAIN)
            case "header":
                bg_color=self.get_color(ThemeKeys.BG_HEADER)
            case "content":
                bg_color=self.get_color(ThemeKeys.BG_MAIN)
            case "footer":
                bg_color=self.get_color(ThemeKeys.BG_FOOTER)
        return bg_color
    
    def set_label_params(self,*,parent:tk.Frame,label_type:Literal['badge','title','content'])->dict:
        bg_color = parent.cget("bg")
        match label_type:
            case "badge":
                fg_color=self.get_color(ThemeKeys.ACCENT)
                params = {
                    "font": ("Consolas", 9, "bold"),
                    "bg": bg_color,
                    "fg": fg_color,
                    "padx": 10,
                    "pady": 4,
                    "relief": "flat"
                } 
            case "title":
                fg_color=self.get_color(ThemeKeys.TEXT_PRIMARY)
                params:dict = {
                    "font": ("Segoe UI", 11, "bold"),
                    "bg": bg_color,
                    "fg": fg_color,
                    "anchor": "w",      
                    "pady": 5
                }
            case "content":
                fg_color=self.get_color(ThemeKeys.TEXT_PRIMARY)
                params:dict = {
                   "font": ("Segoe UI", 10),
                   "bg": bg_color,
                   "fg": fg_color,
                   "justify": "center",
                   "wraplength": 400  
                }

        return params