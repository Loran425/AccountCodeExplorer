import configparser
import os
import re
import threading
import tkinter as tk
from csv import DictReader, excel
from pathlib import Path
from tkinter import filedialog, ttk, BooleanVar, messagebox
from tkinter.ttk import Style

import peewee

version = "1.0.1"

db = peewee.SqliteDatabase(None)


class AccountCode(peewee.Model):
    account_code = peewee.TextField()
    level = peewee.IntegerField()
    description = peewee.TextField()
    uom = peewee.TextField()
    uom2 = peewee.TextField()
    metric_uom = peewee.TextField()
    metric_uom2 = peewee.TextField()
    notes = peewee.TextField()
    personal_notes = peewee.TextField(null=True)
    _flags = peewee.BitField()
    has_labor_cost = _flags.flag(1)
    has_const_eqp_cost = _flags.flag(2)
    has_fom_rented_eqp_cost = _flags.flag(4)
    has_supplies_cost = _flags.flag(8)
    has_materials_cost = _flags.flag(16)
    has_subcontract_cost = _flags.flag(32)
    has_fixed_fees_and_services_cost = _flags.flag(64)
    has_contingency_allowances_cost = _flags.flag(128)
    has_ga_cost = _flags.flag(256)
    uom_to_sup_uom = _flags.flag(512)
    uom_to_sup_uom2 = _flags.flag(1024)
    uom2_to_sup_uom2 = _flags.flag(2048)
    auto_quantity_uom = _flags.flag(4096)
    auto_quantity_uom2 = _flags.flag(8192)

    class Meta:
        database = db


AccountCodeFields = [
    "account_code",
    "uom",
    "uom2",
    "metric_uom",
    "metric_uom2",
]
AccountCodeFlags = [
    "has_labor_cost",
    "has_const_eqp_cost",
    "has_fom_rented_eqp_cost",
    "has_supplies_cost",
    "has_materials_cost",
    "has_subcontract_cost",
    "has_fixed_fees_and_services_cost",
    "has_contingency_allowances_cost",
    "has_ga_cost",
    "uom_to_sup_uom",
    "uom_to_sup_uom2",
    "uom2_to_sup_uom2",
    "auto_quantity_uom",
    "auto_quantity_uom2",
]
AccountCodeLevelColoring = {
    "level1": "#e88b8b",
    "level2": "#a7d1ba",
    "level3": "#8ec6e2",
    "level4": "#ba8ba3",
    "level5": "#e0c296",
    "level6": "#9aa1e0",
    "level7": "#c7d38d",
    "level8": "#d1d1d1",
    "level9": "#c5a18b",
    "level10": "#ce9de0",
    "level11": "#a3e4aa",
}


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


class DetailView:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Populate the detail view with labels, values, and checkboxes
        self.detail_widgets = {}
        self.current_account_code = None

        for i, field in enumerate(AccountCodeFields):
            # Create a gap for the description field
            if field != "account_code":
                i += 4
            label = ttk.Label(
                self.frame,
                text=f"{field.replace('_', ' ').title()}:",
                justify="right",
            )
            label.grid(row=i, column=0, sticky="e")
            value = tk.Text(self.frame, state="disabled", height=1, width=60)
            value.grid(row=i, column=1, sticky="w")
            self.detail_widgets[field] = value

        for i, flag in enumerate(AccountCodeFlags):
            flag_label_text = flag
            if flag_label_text.startswith("has_"):
                flag_label_text = flag[4:]
            if flag_label_text.endswith("_cost"):
                flag_label_text = flag_label_text[:-5]
            flag_label_text = flag_label_text.replace("_", " ").title()

            label = ttk.Label(self.frame, text=f"{flag_label_text}:")
            label.grid(row=i, column=2, sticky="w")
            var = BooleanVar(value=False)
            checkbox = ttk.Checkbutton(self.frame, variable=var)
            checkbox.grid(row=i, column=3, sticky="w")
            self.detail_widgets[flag] = var

        # Add a read-only multi-line text box for description
        description_label = ttk.Label(self.frame, text="Description:", anchor="e")
        description_label.grid(row=1, column=0, sticky="ne")
        self.description_text = tk.Text(self.frame, height=4.75, wrap="word", state="disabled", width=60)
        self.description_text.grid(row=1, column=1, rowspan=4, sticky="nwe")
        self.detail_widgets["description"] = self.description_text

        # Add a wrapping text box for notes
        notes_label = ttk.Label(self.frame, text="District Notes:")
        notes_label.grid(row=len(AccountCodeFlags) - 1, column=0, columnspan=4, sticky="w")
        self.notes_text = tk.Text(self.frame, height=10, wrap="word", state="disabled")
        self.notes_text.grid(row=len(AccountCodeFlags) + 1, column=0, columnspan=4, sticky="we")

        # Add a wrapping text box for personal notes
        pnotes_label = ttk.Label(self.frame, text="Personal Notes:")
        pnotes_label.grid(row=len(AccountCodeFlags) + 10, column=0, columnspan=4, sticky="w")
        self.pnotes_text = tk.Text(self.frame, height=10, wrap="word")
        self.pnotes_text.grid(row=len(AccountCodeFlags) + 11, column=0, columnspan=4, sticky="we")

        # Bindings for saving personal notes, probably should just save notes on quit
        self.pnotes_text.bind("<<FocusOut>>", self.save_personal_notes)

    def save_personal_notes(self, event=None):
        if self.current_account_code:
            self.current_account_code.personal_notes = self.pnotes_text.get("1.0", tk.END)
            self.current_account_code.save()

    def update(self, acct_code: AccountCode):
        self.save_personal_notes(None)

        self.current_account_code = acct_code
        for field, widget in self.detail_widgets.items():
            if isinstance(widget, BooleanVar):
                widget.set(getattr(self.current_account_code, field))
            else:
                widget.config(state="normal")
                widget.delete("1.0", tk.END)
                widget.insert(tk.END, str(getattr(self.current_account_code, field)))
                widget.config(state="disabled")

        self.notes_text.config(state="normal")
        self.notes_text.delete("1.0", tk.END)
        if self.current_account_code.notes:
            self.notes_text.insert(tk.END, str(self.current_account_code.notes))
        else:
            self.notes_text.insert(tk.END, "No notes available")
        self.notes_text.config(state="disabled")

        self.pnotes_text.delete("1.0", tk.END)
        if self.current_account_code.personal_notes:
            self.pnotes_text.insert(tk.END, str(self.current_account_code.personal_notes))


class ExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Account Code Explorer")

        self.root.geometry("1440x814")

        # Set the icon
        self.root.iconbitmap("AccountCodeExplorer.ico")

        # Create a PanedWindow
        self.paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)

        # Create the side drawer frame
        self.tree_panel = TreePanel(self.paned_window)
        self.paned_window.add(self.tree_panel.frame)

        # Create the detail view frame
        self.detail_view = DetailView(self.paned_window)
        self.paned_window.add(self.detail_view.frame)

        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Create a menu
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        # Add a File menu
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New Database", command=self.database_create, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open Database", command=self.database_open, accelerator="Ctrl+O")
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Import Account Codes", command=self.import_account_codes, accelerator="Ctrl+I"
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_close, accelerator="Ctrl+Q")

        self.view_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="View", menu=self.view_menu)
        self.color_hierarchy = BooleanVar(value=False)
        self.color_hierarchy.trace_add("write", self.on_color_hierarchy_change)
        self.view_menu.add_checkbutton(label="Color Hierarchy", variable=self.color_hierarchy, accelerator="Ctrl+H")

        self.about_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="About", menu=self.about_menu)
        self.about_menu.add_command(label="About", command=self.show_about)

        # Add bindings, including accelerators
        # For accelerators, we need to use lambda functions to strip the event and only call the function
        self.root.bind("<Control-n>", lambda e: self.database_create())
        self.root.bind("<Control-o>", lambda e: self.database_open())
        self.root.bind("<Control-i>", lambda e: self.import_account_codes())
        self.root.bind("<Control-q>", lambda e: self.on_close())
        self.root.bind("<Control-h>", lambda e: self.color_hierarchy.set(not self.color_hierarchy.get()))
        self.root.bind("<F6>", lambda e: self.tree_panel.search_combobox.focus_set())
        self.root.bind("<<TreeviewSelect>>", self.on_tree_selection)
        self.root.bind("<Configure>", self.on_resize)

        # Bind the close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create status bar frame
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        self.status_bar.config(relief=tk.SUNKEN)

        # Add label to status bar frame
        self.status_label = ttk.Label(self.status_bar, text="Ready", font=("Consolas", 8))
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)

        # placeholders for the progress popup
        self.progress_popup = None
        self.progress_label = None
        self.progress_bar = None

        # Load Config file
        self.app_config = configparser.ConfigParser()
        self.app_config_path: Path | None = None
        self.config_load()
        self.database_init()
        self.tree_panel.populate_tree()

    #########################################################################
    # Configuration and Database Management
    #########################################################################

    def config_load(self):
        appdata = Path(os.getenv("APPDATA") + "/Account Code Explorer")
        if Path("./config.ini").exists():
            self.app_config.read("config.ini")
            self.app_config_path = Path("./config.ini")
        elif (appdata / "config.ini").exists():
            self.app_config.read(appdata / "config.ini")
            self.app_config_path = appdata / "config.ini"
        elif (appdata / "default_config.ini").exists():
            self.app_config.read(appdata / "default_config.ini")
            self.app_config_path = appdata / "config.ini"  # Don't overwrite the default config file
        else:
            self.config_create_default()
            self.app_config_path = Path("./config.ini")

        self.config_validate()

    def config_validate(self):
        # Validate color hierarchy
        self.color_hierarchy.set(self.app_config["tree"].get("color_hierarchy", "") == "True")

        # Validate window size and position
        size = self.app_config["window"].get("size", "")
        position = self.app_config["window"].get("position", "")
        if not re.match(r"^\d+x\d+$", size):
            print("Invalid window size format. Using default size.")
            size = "1440x814"
        if not re.match(r"^\+\d+\+\d+$", position) and position != "":
            print("Invalid window position format. Using default position.")
            position = ""

        self.root.geometry(size + position)

        # Validate database path
        db_path = self.app_config["database"].get("path", "")
        if db_path == "" or not Path(db_path).exists():
            response = messagebox.askyesno(
                "Database Not Found",
                "The selected database file does not exist. Would you like to open an existing database file?",
            )
            if response:
                self.database_open()
            else:
                response = messagebox.askyesno(
                    "Create New Database",
                    "Would you like to create a new database file?",
                )
                if response:
                    self.database_create()
                else:
                    exit()

    def config_create_default(self):
        config = configparser.ConfigParser()
        config["tree"] = {
            "color_hierarchy": "False",
        }
        config["window"] = {
            "size": "1440x814",
            "position": "",
        }
        config["database"] = {
            "path": "account_code_viewer.sqlite",
        }
        with open("config.ini", "w") as configfile:
            config.write(configfile)
        self.app_config = config

    def update_status(self, message):
        self.status_label.config(text=message)

    def database_init(self):
        if not db.is_closed():
            db.commit()
            db.close()
        db_path = self.app_config["database"]["path"]
        db.init(db_path, pragmas={"journal_mode": "wal"})
        db.connect()
        db.create_tables([AccountCode], safe=True)
        self.update_status(f"Connected to database: {Path(db_path).absolute()}")

    def database_open(self):
        db_path = filedialog.askopenfilename(
            initialdir=self.app_config_path.parent,
            title="Open Database",
            filetypes=(("SQLite Files", "*.sqlite"),),
        )
        if db_path:
            self.app_config["database"]["path"] = db_path
            self.database_init()
            self.tree_panel.populate_tree()

    def database_create(self):
        db_path = filedialog.asksaveasfilename(
            initialdir=self.app_config_path.parent,
            title="Create Database",
            filetypes=(("SQLite Files", "*.sqlite"),),
            defaultextension=".sqlite",
        )
        if db_path:
            self.app_config["database"]["path"] = db_path
            self.database_init()
            self.tree_panel.populate_tree()

    #########################################################################
    # event handlers
    #########################################################################

    def on_resize(self, event=None):
        win_width = self.paned_window.winfo_width()
        self.paned_window.sashpos(0, win_width - 738)

    def on_tree_selection(self, event=None):
        if not self.tree_panel.tree.selection():
            return
        selection = self.tree_panel.tree.selection()
        acct_code = AccountCode.get(AccountCode.account_code == selection[0])
        if selection:
            self.detail_view.update(acct_code)

    def on_close(self):
        self.detail_view.save_personal_notes(None)
        self.app_config.set("tree", "color_hierarchy", str(self.color_hierarchy.get()))
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        width = self.root.winfo_width()
        height = self.root.winfo_height() + 20  # Add 20 for the status bar TODO: Find a better way to do this
        self.app_config.set("window", "size", f"{width}x{height}")
        self.app_config.set("window", "position", f"+{x}+{y}")
        self.app_config.set("database", "path", db.database)
        self.app_config.write(open(self.app_config_path, "w"))
        db.commit()
        db.close()
        self.root.destroy()

    def on_color_hierarchy_change(self, *args):
        self.tree_panel.configure_tree_backgrounds(self.color_hierarchy.get())

    #########################################################################
    # Import Processes
    #########################################################################

    def show_progress_popup(self):
        self.progress_popup = tk.Toplevel(self.root)
        self.progress_popup.title("Import Progress")

        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()

        popup_width = 300
        popup_height = 100

        x = parent_x + (parent_width // 2) - (popup_width // 2)
        y = parent_y + (parent_height // 2) - (popup_height // 2)

        self.progress_popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        self.progress_popup.geometry("300x100")
        self.progress_label = ttk.Label(self.progress_popup, text="Importing account codes...")
        self.progress_label.pack(pady=10)
        self.progress_bar = ttk.Progressbar(self.progress_popup, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=20, pady=10)
        self.progress_bar["value"] = 0

    def import_account_codes(self):
        account_codes_csv = filedialog.askopenfilename(
            initialdir=self.app_config_path.parent,
            title="Select Account Codes CSV",
            filetypes=(("CSV Files", "*.csv"),),
        )

        if not account_codes_csv:
            print("No file selected")
            return

        self.show_progress_popup()

        def import_process():
            # recreate the account code table
            AccountCode().drop_table()
            AccountCode().create_table()

            with open(account_codes_csv, mode="r") as f:
                csvreader = DictReader(f, dialect=excel)
                total_rows = sum(1 for _ in csvreader)
                f.seek(0)
                next(csvreader)  # Skip header row, only needed because we did a seek(0) above

                for i, row in enumerate(csvreader):
                    code = AccountCode()
                    acct_code = row["Account Code"].split(".")
                    if len(acct_code) > 1 and len(acct_code[1]) == 1:
                        acct_code[1] = acct_code[1] + "0"
                    code.account_code = ".".join(acct_code)
                    code.level = 1 + row["Account Code"].count(".")
                    code.description = row["Description"]
                    code.uom = row["Primary UOM"]
                    code.uom2 = row["2nd UOM"]
                    code.metric_uom = row["Metric Primary"]
                    code.metric_uom2 = row["Metric 2nd"]
                    code.notes = row["Notes"]
                    code.has_labor_cost = row["Labor"] == "Yes"
                    code.has_const_eqp_cost = row["Const. EQP"] == "Yes"
                    code.has_fom_rented_eqp_cost = row["FOM Rented EQP"] == "Yes"
                    code.has_supplies_cost = row["Supplies"] == "Yes"
                    code.has_materials_cost = row["Materials"] == "Yes"
                    code.has_subcontract_cost = row["Subcontract"] == "Yes"
                    code.has_fixed_fees_and_services_cost = row["Fixed Fees and Services"] == "Yes"
                    code.has_contingency_allowances_cost = row["Contingency (Allowances)"] == "Yes"
                    code.has_ga_cost = row["G & A"] == "Yes"
                    code.uom_to_sup_uom = row["Primary to Sup Primary"] == "TRUE"
                    code.uom_to_sup_uom2 = row["Primary to Sup 2nd"] == "TRUE"
                    code.uom2_to_sup_uom2 = row["2nd to Sup 2nd"] == "TRUE"
                    code.auto_quantity_uom = row["Auto Quantity Primary"] == "TRUE"
                    code.auto_quantity_uom2 = row["Auto Quantity 2nd"] == "TRUE"
                    code.save()

                    self.progress_label["text"] = f"Importing account codes... {i + 1}/{total_rows}"
                    self.progress_bar["value"] = (i + 1) / total_rows * 100
                    self.progress_popup.update_idletasks()

            self.progress_popup.destroy()
            self.tree_panel.populate_tree()

        threading.Thread(target=import_process).start()

    def show_about(self):
        about_popup = tk.Toplevel(self.root)
        about_popup.title("About")
        about_popup.resizable(False, False)

        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()

        popup_width = 300
        popup_height = 110

        x = parent_x + (parent_width // 2) - (popup_width // 2)
        y = parent_y + (parent_height // 2) - (popup_height // 2)

        about_popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        about_label = ttk.Label(about_popup, text=f"Account Code Explorer v{version}")
        about_label.pack(pady=5)
        contact_label = ttk.Label(about_popup, text="Contact: Loran425@gmail.com")
        contact_label.pack(anchor="w")
        copyright_label = ttk.Label(about_popup, text="Copyright © 2024 Andrew Arneson")
        copyright_label.pack(anchor="w")
        about_close_button = ttk.Button(about_popup, text="Close", command=about_popup.destroy)
        about_close_button.pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = ExplorerApp(root)
    root.mainloop()
