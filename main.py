import configparser
import json
import os
import re
import threading
import tkinter as tk
from csv import DictReader, DictWriter, excel
from pathlib import Path
from tkinter import filedialog, ttk, BooleanVar, IntVar, messagebox

import screeninfo

from constants import LeftPanelMode
from models import AccountCode, AccountCodeIndex, db
from popups import ExportPopup, ImportPopup, AboutPopup
from widgets import TreePanel, DetailView, SearchView


class ExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()
        self.root.title("Account Code Explorer")

        self.root.geometry("1440x814")

        # Set the icon
        self.root.iconbitmap("AccountCodeExplorer.ico")

        # Create a PanedWindow
        self.paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)

        # Create the search panel frame
        self.search_view = SearchView(self.paned_window, padding=5)
        self.search_view.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(self.search_view)

        # Create the side drawer frame
        self.tree_panel = TreePanel(self.paned_window, padding=5)

        # Create the detail view frame
        self.detail_view = DetailView(self.paned_window, padding=5)
        self.detail_view.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(self.detail_view)

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
        self.file_menu.add_command(label="Import Account Codes", command=self.import_account_codes)
        self.file_menu.add_command(label="Export Account Codes", command=self.export_account_codes)
        self.file_menu.entryconfig("Export Account Codes", state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Import Personal Notes", command=self.import_notes)
        self.file_menu.add_command(label="Export Personal Notes", command=self.export_notes)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Update Index", command=self.on_update_index)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_close, accelerator="Ctrl+Q")

        self.view_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="View", menu=self.view_menu)
        self.color_hierarchy = BooleanVar(value=False)
        self.color_hierarchy.trace_add("write", self.on_color_hierarchy_change)
        self.left_panel_mode = IntVar(value=1)
        self.view_menu.add_radiobutton(
            label="Browse Mode", value=LeftPanelMode.BROWSE.value, variable=self.left_panel_mode
        )
        self.view_menu.add_radiobutton(
            label="Search Mode", value=LeftPanelMode.SEARCH.value, variable=self.left_panel_mode
        )
        self.view_menu.add_separator()
        self.left_panel_mode.trace_add("write", self.on_mode_change)
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
        self.root.bind("<<TreeviewSelect>>", self.on_tree_selection)
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Button-1>", self.on_click)
        self.update_bindings()

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
        # If no database has been selected abort startup
        db_path = self.app_config["database"].get("path", "")
        if not db_path or not Path(db_path).exists():
            return
        self.database_init()
        self.tree_panel.populate_tree()

        # Show the window
        self.root.deiconify()

    #########################################################################
    # Configuration and Database Management
    #########################################################################
    # TODO: Test with old configs

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
        if "panel" not in self.app_config:
            print("No panel section found in config file. Creating empty section.")
            self.app_config["panel"] = {}
        if "window" not in self.app_config:
            print("No window section found in config file. Creating empty section.")
            self.app_config["window"] = {}
        if "database" not in self.app_config:
            print("No database section found in config file. Creating empty section.")
            self.app_config["database"] = {}

        # Validate color hierarchy
        self.color_hierarchy.set(self.app_config["panel"].get("color_hierarchy", "") == "True")

        # Validate left panel mode
        left_panel_mode = self.app_config["panel"].get("left_panel_mode", "")
        try:
            left_panel_mode = int(left_panel_mode)
        except ValueError:
            print("Invalid left panel mode. Using default left panel mode.")
            left_panel_mode = 1
        self.left_panel_mode.set(left_panel_mode)

        # Validate sort mode
        sort_mode = self.app_config["panel"].get("sort_mode", "")
        try:
            sort_mode = int(sort_mode)
        except ValueError:
            print("Invalid sort mode. Using default sort mode.")
            sort_mode = 1
        self.search_view.sort_mode_combo.current(sort_mode)

        # Validate window size and position
        size = self.app_config["window"].get("size", "")
        position = self.app_config["window"].get("position", "")
        if not re.match(r"^\d+x\d+$", size):
            print("Invalid window size format. Using default size.")
            size = "1440x814"
        if not re.match(r"^\+\d+\+\d+$", position):
            print("Invalid window position format. Using default position.")
            position = "+50+50"

        # TODO: consider moving this to a separate method
        x, y = map(int, position.split("+")[1:])

        monitors = screeninfo.get_monitors()
        active_monitor = None
        for m in monitors:
            if m.x <= x <= m.x + m.width and m.y <= y <= m.y + m.height:
                active_monitor = m
                break

        if active_monitor:
            if (x - active_monitor.x) > active_monitor.width - 50:
                x = active_monitor.x + active_monitor.width - 50
            if (y - active_monitor.y) < 0:
                y = active_monitor.y
            elif (y - active_monitor.y) > active_monitor.height - 50:
                y = active_monitor.y + active_monitor.height - 50
            position = f"+{x}+{y}"
        else:
            print("Invalid window position. Using default position.")
            position = "+50+50"

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
                    self.on_close()

        # If we still don't have a valid database path something has gone wrong, exit the program
        db_path = self.app_config["database"].get("path", "")
        if not db_path or not Path(db_path).exists():
            messagebox.showerror("Database Error", "No database file selected. Exiting")

    def config_create_default(self):
        config = configparser.ConfigParser()
        config["panel"] = {
            "color_hierarchy": "False",
            "left_panel_mode": "1",
            "sort_mode": "Account Code",
        }
        config["window"] = {
            "size": "1440x814",
            "position": "+50+50",
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
        db.create_tables([AccountCode, AccountCodeIndex], safe=True)
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

    def on_click(self, event=None):
        x, y = self.root.winfo_pointerxy()
        widget = self.root.winfo_containing(x, y)
        active_widget = self.root.focus_get()
        if widget != active_widget:
            self.root.focus()  # focus on root

    def on_close(self):
        self.detail_view.save_personal_notes(None)

        # Remove old config sections, remove in v1.1.0
        if "tree" in self.app_config:
            self.app_config.remove_section("tree")

        self.app_config.set("panel", "color_hierarchy", str(self.color_hierarchy.get()))
        self.app_config.set("panel", "left_panel_mode", str(self.left_panel_mode.get()))
        self.app_config.set("panel", "sort_mode", str(self.search_view.sort_mode_combo.current()))
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        width = self.root.winfo_width()
        height = self.root.winfo_height() + 20  # Add 20 for the status bar TODO: Find a better way to do this
        self.app_config.set("window", "size", f"{width}x{height}")
        self.app_config.set("window", "position", f"+{x}+{y}")
        if db.database:
            self.app_config.set("database", "path", db.database)
            db.commit()
            db.close()
        self.app_config.write(open(self.app_config_path, "w"))
        self.root.destroy()

    def on_color_hierarchy_change(self, *args):
        self.tree_panel.configure_tree_backgrounds(self.color_hierarchy.get())
        self.search_view.configure_tree_backgrounds(self.color_hierarchy.get())

    def on_mode_change(self, *args):
        mode = LeftPanelMode(self.left_panel_mode.get())
        self.paned_window.forget(1)
        self.paned_window.forget(0)
        if mode == LeftPanelMode.BROWSE:
            self.paned_window.add(self.tree_panel)
            self.paned_window.add(self.detail_view)
        elif mode == LeftPanelMode.SEARCH:
            self.paned_window.add(self.search_view)
            self.paned_window.add(self.detail_view)
        self.update_bindings()

    def on_resize(self, event=None):
        win_width = self.paned_window.winfo_width()
        self.paned_window.sashpos(0, win_width - 738)

    def on_tree_selection(self, event=None):
        mode = LeftPanelMode(self.left_panel_mode.get())
        if mode == LeftPanelMode.BROWSE:
            if not self.tree_panel.tree.selection():
                return
            selection = self.tree_panel.tree.selection()
            acct_code = AccountCode.get(AccountCode.account_code == selection[0])
            if selection:
                self.detail_view.update_details(acct_code)
        elif mode == LeftPanelMode.SEARCH:
            if not self.search_view.results_list.selection():
                return
            selection = self.search_view.results_list.selection()
            acct_code = AccountCode.get(AccountCode.account_code == selection[0])
            if selection:
                self.detail_view.update_details(acct_code)

    @staticmethod
    def on_update_index():
        AccountCodeIndex.rebuild()
        AccountCodeIndex.optimize()

    def select_search(self, event=None):
        self.tree_panel.search_combobox.focus_set()
        self.tree_panel.search_combobox.selection_range(0, tk.END)

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

    def export_account_codes(self):
        pass

    def export_notes(self):
        # TODO: Add option to exclude notes not written by the current user
        export_config = ExportPopup(self.root)
        self.root.wait_window(export_config)

        if not export_config.result:
            return

        notes = {
            "author": export_config.result.get("author", None),
            "date": export_config.result.get("date", None),
            "file": Path(export_config.result.get("file", None)),
            "notes": dict(),
        }

        for code in AccountCode.select():
            if code.personal_notes:
                notes["notes"][code.account_code] = code.personal_notes

        if not notes["notes"]:
            messagebox.showinfo("Export Notes", "No notes to export.")
            return

        if notes["file"].suffix == ".csv":
            with open(notes["file"], "w", newline="") as f:
                writer = DictWriter(f, fieldnames=["Account Code", "Personal Notes", "Author", "Date"])
                writer.writeheader()
                for acct_code, note in notes["notes"].items():
                    writer.writerow(
                        {
                            "Account Code": acct_code,
                            "Personal Notes": note,
                            "Author": notes["author"],
                            "Date": notes["date"],
                        }
                    )

        elif notes["file"].suffix == ".json":
            with open(notes["file"], "w") as f:
                del notes["file"]
                json.dump(notes, f, indent=4)

        else:
            messagebox.showerror(
                "Export Notes", f"Invalid file type returned [{notes["file"].suffix}]\nExport canceled"
            )
            return

    def import_notes(self):
        import_config = ImportPopup(self.root)
        self.root.wait_window(import_config)

        if not import_config.result:
            return

        file_path = import_config.result.get("file", None)
        overwrite = import_config.result.get("overwrite", False)
        annotate = import_config.result.get("annotate", False)

        if not file_path:
            return

        if file_path.endswith(".csv"):
            with open(file_path, "r") as f:
                reader = DictReader(f)
                for row in reader:
                    if annotate:
                        notes = f"{row['Author'] or 'Unknown'} {row['Date'] or 'Unknown'}: {row['Personal Notes']}"
                    else:
                        notes = row["Personal Notes"]
                    acct_code = AccountCode.get(AccountCode.account_code == row["Account Code"])

                    if overwrite:
                        acct_code.personal_notes = notes
                    else:
                        acct_code.personal_notes = f"{acct_code.personal_notes}\n{notes}"

                    acct_code.save()

        elif file_path.endswith(".json"):
            with open(file_path, "r") as f:
                notes = json.load(f)
                for acct_code, note in notes["notes"].items():
                    acct_code = AccountCode.get(AccountCode.account_code == acct_code)
                    if annotate:
                        note = f"{notes['author'] or 'Unknown'} {notes['date'] or 'Unknown'}: {note}"

                    if overwrite:
                        acct_code.personal_notes = note
                    else:
                        acct_code.personal_notes = f"{acct_code.personal_notes}\n{note}"
                    acct_code.save()

        # TODO: Add method to prevent duplicate notes
        pass

    def show_about(self):
        about = AboutPopup(self.root)
        self.root.wait_window(about)

    def update_bindings(self):
        self.root.unbind("<F6>")
        mode = LeftPanelMode(self.left_panel_mode.get())
        if mode == LeftPanelMode.BROWSE:
            self.root.bind("<F6>", self.select_search)
        elif mode == LeftPanelMode.SEARCH:
            self.root.bind("<F6>", lambda e: self.search_view.search_term.focus_set())


if __name__ == "__main__":
    root = tk.Tk()
    app = ExplorerApp(root)
    root.mainloop()
