import os
import tkinter as tk
from tkinter import filedialog, ttk

from popups import BasePopup


class ImportPopup(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Import Personal Notes")
        self.wm_minsize(400, 100)
        self.resizable(False, False)

        self.file_group = ttk.Frame(self)
        self.file_label = ttk.Label(self.file_group, text="File Name:")
        self.file_label.pack(side=tk.LEFT)
        self.file_entry = ttk.Entry(self.file_group)
        self.file_entry.insert(0, "./personal_notes.csv")
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.file_button = ttk.Button(self.file_group, text="...", command=self.on_file_dialog, width=3)
        self.file_button.pack(side=tk.LEFT)
        self.file_group.pack(fill=tk.X, pady=2.5)

        self.options_group = ttk.Frame(self)
        self.notes_frame = ttk.Frame(self.options_group, borderwidth=2, relief=tk.SUNKEN)
        self.note_tracking_label = ttk.Label(self.notes_frame, text="Note Annotation:")
        self.note_tracking_label.pack()
        self.note_tracking = tk.IntVar()
        self.text_only_radio = tk.Radiobutton(self.notes_frame, text="Text Only", variable=self.note_tracking, value=1)
        self.text_only_radio.pack()
        self.annotated_radio = tk.Radiobutton(self.notes_frame, text="Annotated", variable=self.note_tracking, value=2)
        self.annotated_radio.pack()
        self.notes_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2.5, pady=2.5)

        self.overwrite_frame = ttk.Frame(self.options_group, borderwidth=2, relief=tk.SUNKEN)
        self.overwrite_label = ttk.Label(self.overwrite_frame, text="Overwrite Behavior:")
        self.overwrite_label.pack()
        self.overwrite_behavior = tk.IntVar()
        self.amend_radio = tk.Radiobutton(self.overwrite_frame, text="Ammend", variable=self.overwrite_behavior, value=1)
        self.amend_radio.pack()
        self.overwrite_radio = tk.Radiobutton(self.overwrite_frame, text="Overwrite", variable=self.overwrite_behavior, value=2)
        self.overwrite_radio.pack()
        self.overwrite_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2.5, pady=2.5)
        self.options_group.pack(fill=tk.X)

        self.button_tray = ttk.Frame(self)
        self.button_tray.pack(fill=tk.X)
        self.cancel_button = ttk.Button(self.button_tray, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side=tk.RIGHT, padx=2.5, pady=2.5)
        self.export_button = ttk.Button(self.button_tray, text="Import", command=self.on_import)
        self.export_button.pack(side=tk.RIGHT, padx=2.5, pady=2.5)

        self.center_window(parent)
        self.deiconify() # BasePopup starts withdrawn, so we need to deiconify it

    def on_file_dialog(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Import Personal Notes",
            filetypes=(("CSV Files", "*.csv"), ("JSON", "*.json")),
            defaultextension=".csv",
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            self.file_entry.xview_moveto(1)

        self.focus_set()

    def on_import(self):
        self.result = {
            "file": self.file_entry.get(),
            "overwrite": self.overwrite_behavior.get() == 2,
            "annotate": self.note_tracking.get() == 2,
        }
        self.destroy()