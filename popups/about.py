from tkinter import ttk

from constants import version
from popups import BasePopup


class AboutPopup(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About")
        self.geometry("300x110")
        self.resizable(False, False)

        self.about_label = ttk.Label(self, text=f"Account Code Explorer v{version}")
        self.about_label.pack(pady=5)
        self.contact_label = ttk.Label(self, text="Contact: Loran425@proton.me")
        self.contact_label.pack(anchor="w")
        self.copyright_label = ttk.Label(self, text="Copyright © 2025 Andrew Arneson")
        self.copyright_label.pack(anchor="w")
        self.about_close_button = ttk.Button(self, text="Close", command=self.destroy)
        self.about_close_button.pack(pady=10)

        self.center_window(parent)
        self.deiconify()  # BasePopup starts withdrawn, so we need to deiconify it
