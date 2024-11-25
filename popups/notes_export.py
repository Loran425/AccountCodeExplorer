import os
import tkinter as tk
from tkinter import filedialog, ttk

from tkcalendar import DateEntry

from popups import BasePopup

class ExportPopup(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Export Personal Notes")
        self.geometry("600x120")
        self.resizable(False, False)

        self.grid = ttk.Frame(self)
        self.grid.pack(expand=True, fill=tk.BOTH)

        self.file_label = ttk.Label(self.grid, text="File Name:")
        self.file_label.grid(row=0, column=0, sticky=tk.E)
        self.file_entry = ttk.Entry(self.grid)
        self.file_entry.insert(0, "./personal_notes.csv")
        self.file_entry.grid(row=0, column=1, sticky=tk.EW)
        self.file_button = ttk.Button(self.grid, text="...", command=self.on_file_dialog, width=3)
        self.file_button.grid(row=0, column=2)

        self.author_label = ttk.Label(self.grid, text="Author:")
        self.author_label.grid(row=1, column=0, sticky=tk.E)
        self.author_entry = ttk.Entry(self.grid)
        self.author_entry.insert(0, os.getlogin())
        self.author_entry.grid(row=1, column=1, sticky=tk.EW, columnspan=2)

        self.date_label = ttk.Label(self.grid, text="Date:")
        self.date_label.grid(row=2, column=0, sticky=tk.E)
        self.date_entry = DateEntry(self.grid, borderwidth=2, firstweekday="sunday")
        self.date_entry.grid(row=2, column=1, sticky=tk.EW, columnspan=2)

        self.grid.columnconfigure(0, weight=1)
        self.grid.columnconfigure(1, weight=4)

        self.button_tray = ttk.Frame(self)
        self.button_tray.pack(fill=tk.X)
        self.cancel_button = ttk.Button(self.button_tray, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side=tk.RIGHT, padx=2.5, pady=2.5)
        self.export_button = ttk.Button(self.button_tray, text="Export", command=self.on_export)
        self.export_button.pack(side=tk.RIGHT, padx=2.5, pady=2.5)

        self.center_window(parent)
        self.deiconify() # BasePopup starts withdrawn, so we need to deiconify it

    def on_file_dialog(self):
        file_path = filedialog.asksaveasfilename(
            initialdir=os.getcwd(),
            title="Export Personal Notes",
            filetypes=(("CSV Files", "*.csv"), ("JSON", "*.json")),
            defaultextension=".csv",
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)

        self.focus_set()

    def on_export(self):
        self.result = {
            "file": self.file_entry.get(),
            "author": self.author_entry.get(),
            "date": self.date_entry.get(),
        }
        self.destroy()
