import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Style

from constants import AccountCodeLevelColoring
from models import AccountCode


class TreePanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.level_button_row = ttk.Frame(self.frame)
        self.level_button_row.pack(fill=tk.X)
        self.collapse_all_button = ttk.Button(self.level_button_row, text="Collapse All", command=self.collapse_all)
        self.collapse_all_button.pack(side="left")
        self.expand_all_button = ttk.Button(self.level_button_row, text="Expand All", command=self.expand_all)
        self.expand_all_button.pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_combobox = ttk.Combobox(self.frame, textvariable=self.search_var)
        self.search_combobox.pack(fill=tk.X, padx=5, pady=5)
        self.search_combobox.bind("<FocusIn>", self.add_keyrelease_binding)
        self.search_combobox.bind("<FocusOut>", self.remove_keyrelease_binding)
        self.search_combobox.bind("<<ComboboxSelected>>", self.search)

        style = Style()
        style.layout("Treeview.Heading", [])
        self.tree = ttk.Treeview(self.frame, selectmode="browse")
        self.tree_items = []
        self.tree.pack(fill=tk.BOTH, expand=True)

    def add_keyrelease_binding(self, event):
        self.search_combobox.bind("<KeyRelease>", self.search)

    def remove_keyrelease_binding(self, event):
        self.search_combobox.unbind("<KeyRelease>")

    def search(self, event):
        if event == "<KeyPress>":
            if event.keysym == "BackSpace":
                return
            cursor_index = self.search_combobox.index("insert")
            self.search_var.set(self.search_var.get()[: cursor_index + 1])
            return
        query = self.search_var.get().lower()
        filtered_items = [item for item in self.tree_items if query in item.lower()]
        self.search_combobox["values"] = filtered_items

        if filtered_items:
            first_acct_code = filtered_items[0].split(" - ")[0]
            self.tree.selection_set(first_acct_code)
            self.tree.see(first_acct_code)
            self.tree.focus(first_acct_code)

    def populate_tree(self):
        # Clear the treeview in case there are existing items
        self.tree.delete(*self.tree.get_children())
        self.tree_items = []

        # Query the database and insert data into the treeview
        for code in AccountCode.select():
            acct_code = code.account_code.split(".")
            if len(acct_code) > 1:
                parent = ".".join(acct_code[:-1])
            else:
                parent = ""

            self.tree.insert(
                parent,
                "end",
                iid=code.account_code,
                text=f"{code.account_code} - {code.description}",
                tags=(f"level{code.level}",),
            )
            self.tree_items.append(f"{code.account_code} - {code.description}")

    def configure_tree_backgrounds(self, value=None):
        for level, color in AccountCodeLevelColoring.items():
            self.tree.tag_configure(level, background=color if value else "")

    def collapse_all(self, item=None):
        for item in self.tree_items:
            item_code = item.split(" - ")[0]
            self.tree.item(item_code, open=False)

    def expand_all(self):
        for item in self.tree_items:
            item_code = item.split(" - ")[0]
            self.tree.item(item_code, open=True)
