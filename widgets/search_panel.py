import tkinter as tk
from tkinter import ttk

from bitarray import bitarray
from bitarray.util import ba2int

from constants import AccountCodeLevelColoring, SortMode
from models import AccountCode, AccountCodeIndex
from .placeholder_entry import PlaceholderEntry


class SearchView(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.search_frame = ttk.Frame(self, relief=tk.SUNKEN, padding=5)
        self.search_frame.pack(side=tk.TOP, fill=tk.X)

        self.search_term = PlaceholderEntry(self.search_frame, "Search Term")
        self.search_term.bind("<Return>", self._search)
        self.search_term.pack(fill=tk.X)

        self.search_desc_var = tk.BooleanVar()
        self.search_desc = tk.Checkbutton(self.search_frame, text="Description", anchor=tk.W,
                                          variable=self.search_desc_var)
        self.search_district_var = tk.BooleanVar()
        self.search_district = tk.Checkbutton(self.search_frame, text="District Notes", anchor=tk.W,
                                              variable=self.search_district_var)
        self.search_personal_var = tk.BooleanVar()
        self.search_personal = tk.Checkbutton(self.search_frame, text="Personal Notes", anchor=tk.W,
                                              variable=self.search_personal_var)
        self.search_desc.select()
        self.search_district.select()

        self.search_desc.pack(fill=tk.X)
        self.search_district.pack(fill=tk.X)
        self.search_personal.pack(fill=tk.X)

        self.cost_frame = ttk.Frame(self, relief=tk.SUNKEN, padding=5)
        self.cost_frame.pack(fill=tk.X)
        self.cost_label = ttk.Label(self.cost_frame, text="Cost Categories")
        self.cost_div = ttk.Separator(self.cost_frame, orient=tk.HORIZONTAL)
        self.cost_labor_var = tk.BooleanVar(value=True)
        self.cost_labor = tk.Checkbutton(self.cost_frame, text="Labor", variable=self.cost_labor_var)
        self.cost_equip_var = tk.BooleanVar()
        self.cost_equip = tk.Checkbutton(self.cost_frame, text="Equipment", variable=self.cost_equip_var)
        self.cost_fom_equip_var = tk.BooleanVar()
        self.cost_fom_equip = tk.Checkbutton(self.cost_frame, text="FOM Equipment", variable=self.cost_fom_equip_var)
        self.cost_supplies_var = tk.BooleanVar()
        self.cost_supplies = tk.Checkbutton(self.cost_frame, text="Supplies", variable=self.cost_supplies_var)
        self.cost_materials_var = tk.BooleanVar()
        self.cost_materials = tk.Checkbutton(self.cost_frame, text="Materials", variable=self.cost_materials_var)
        self.cost_subcontract_var = tk.BooleanVar()
        self.cost_subcontract = tk.Checkbutton(self.cost_frame, text="Subcontract", variable=self.cost_subcontract_var)
        self.cost_fixed_var = tk.BooleanVar()
        self.cost_fixed = tk.Checkbutton(self.cost_frame, text="Fixed Fees & Services", variable=self.cost_fixed_var)
        self.cost_contingency_var = tk.BooleanVar()
        self.cost_contingency = tk.Checkbutton(self.cost_frame, text="Contingency & Allowances",
                                               variable=self.cost_contingency_var)
        self.cost_ga_var = tk.BooleanVar()
        self.cost_ga = tk.Checkbutton(self.cost_frame, text="G&A", variable=self.cost_ga_var)

        self.cost_label.grid(row=0, column=0, columnspan=3, sticky=tk.W)
        self.cost_div.grid(row=1, column=0, columnspan=3, sticky=tk.EW)
        self.cost_labor.grid(row=2, column=0, sticky=tk.W)
        self.cost_equip.grid(row=3, column=0, sticky=tk.W)
        self.cost_fom_equip.grid(row=4, column=0, sticky=tk.W)
        self.cost_supplies.grid(row=2, column=1, sticky=tk.W)
        self.cost_materials.grid(row=3, column=1, sticky=tk.W)
        self.cost_subcontract.grid(row=4, column=1, sticky=tk.W)
        self.cost_fixed.grid(row=2, column=2, sticky=tk.W)
        self.cost_contingency.grid(row=3, column=2, sticky=tk.W)
        self.cost_ga.grid(row=4, column=2, sticky=tk.W)

        for i in range(3):
            self.cost_frame.columnconfigure(i, weight=1)

        self.search_frame = ttk.Frame(self, padding=5)
        self.search_button = ttk.Button(self.search_frame, text="Search", command=self._search)
        self.search_button.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.sort_label = ttk.Label(self.search_frame, text="Sort by")
        self.sort_label.pack(side=tk.LEFT, padx=5)
        self.sort_mode = tk.StringVar()
        self.sort_mode_combo = ttk.Combobox(self.search_frame,
                                            state="readonly",
                                            textvariable=self.sort_mode,
                                            values=["Relevance", "Account Code"])
        self.sort_mode_combo.current(1)
        self.sort_mode_combo.pack(side=tk.LEFT, padx=5)
        self.search_frame.pack(fill=tk.X)
        self.sort_mode_combo.bind("<<ComboboxSelected>>", self._search)

        self.results_frame = ttk.Frame(self, relief=tk.SUNKEN, padding=5)
        self.results_label = ttk.Label(self.results_frame, text="Search Results", anchor=tk.W)
        self.results_label.pack(fill=tk.X)
        style = ttk.Style()
        style.layout("Treeview.Heading", [])
        self.results_list = ttk.Treeview(self.results_frame, selectmode="browse")

        self.scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.results_list.yview)
        self.results_list.configure(yscrollcommand=self.scrollbar.set)

        self.results_list.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_frame.pack(expand=True, fill=tk.BOTH)



    def _search(self, event=None):
        # TODO: find a better way to call this (event?)
        AccountCodeIndex.rebuild()
        AccountCodeIndex.optimize()
        search_terms = self.search_term.get()
        search_locations = {
            "Description": self.search_desc_var.get(),
            "Notes": self.search_district_var.get(),
            "Personal_Notes": self.search_personal_var.get(),
        }
        search_costs = bitarray(
            [
                self.cost_ga_var.get(), # 256
                self.cost_contingency_var.get(), # 128
                self.cost_fixed_var.get(), # 64
                self.cost_subcontract_var.get(), # 32
                self.cost_materials_var.get(), # 16
                self.cost_supplies_var.get(), # 8
                self.cost_fom_equip_var.get(), # 4
                self.cost_equip_var.get(), # 2
                self.cost_labor_var.get(), # 1
            ]
        )

        search_phrase = f"{{ {" ".join([key for key, value in search_locations.items() if value])} }}: {search_terms}"

        search_costs = ba2int(search_costs)

        # search_terms: list of strings to search for in the account code, search for ANY word in ANY selected field
        # search_costs: bitarray of cost types to search for, & the bit array with the _flags and return if > 0
        search_mode = SortMode(self.sort_mode_combo.current())
        if search_mode == SortMode.RELEVANCE:
            values = (AccountCode
                      .select(AccountCode.account_code, AccountCode.description, AccountCode.level)
                      .join(AccountCodeIndex,
                            on=(AccountCode.id == AccountCodeIndex.rowid))
                      .where(
                          (AccountCodeIndex.match(search_phrase)) &
                          (AccountCode._flags.bin_and(search_costs))
                      )
                      .order_by(AccountCodeIndex.bm25())
            )
        elif search_mode == SortMode.ACCOUNT_CODE:
            values = (AccountCode
                .select(AccountCode.account_code, AccountCode.description, AccountCode.level)
                .join(AccountCodeIndex,
                      on=(AccountCode.id == AccountCodeIndex.rowid))
                .where(
                    (AccountCodeIndex.match(search_phrase)) &
                    (AccountCode._flags.bin_and(search_costs))
                )
                .order_by(AccountCode.account_code)
            )

        self.results_list.delete(*self.results_list.get_children())

        for value in values:
            self.results_list.insert("",
                                     "end",
                                     iid=value.account_code,
                                     text=f"{value.account_code} - {value.description}",
                                     tags=(f"level{value.level}",),
                                     )

    def configure_tree_backgrounds(self, value=None):
        for level, color in AccountCodeLevelColoring.items():
            self.results_list.tag_configure(level, background=color if value else "")