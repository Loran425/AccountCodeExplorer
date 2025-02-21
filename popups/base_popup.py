import tkinter as tk


class BasePopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.iconbitmap("AccountCodeExplorer.ico")
        self.result = None
        self.withdraw()

    def center_window(self, parent):
        parent.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (window_width // 2)
        y = parent_y + (parent_height // 2) - (window_height // 2)
        self.geometry(f"+{x}+{y}")

    def on_cancel(self):
        self.result = None
        self.destroy()
