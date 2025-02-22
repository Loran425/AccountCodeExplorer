import tkinter as tk

from popups import BasePopup
from widgets import SearchView

class AdvancedSearchPopup(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Advanced Search")
        self.geometry("600x800")  # TODO: Check this size
        self.resizable(False, True)

        search_frame = SearchView(self)
        search_frame.pack(expand=True, fill=tk.BOTH)

        self.center_window(parent)
        self.deiconify()
