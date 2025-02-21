import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Style

from models import AccountCode
from widgets import PlaceholderEntry

from bitarray import bitarray
from popups import BasePopup


class AdvancedSearchPopup(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Advanced Search")
        self.geometry("600x800")  # TODO: Check this size
        self.resizable(False, True)

        self.grid = ttk.Frame(self, padding=5)
        self.grid.pack(expand=True, fill=tk.BOTH)

        self.search_frame = ttk.Frame(self.grid, relief=tk.SUNKEN, padding=5)
        self.search_frame.pack(side=tk.TOP, fill=tk.X)

        self.search_term = PlaceholderEntry(self.search_frame, "Search Term")
        self.search_term.pack(fill=tk.X)

        self.search_desc_var = tk.BooleanVar()
        self.search_desc = tk.Checkbutton(
            self.search_frame, text="Description", anchor=tk.W, variable=self.search_desc_var
        )
        self.search_district_var = tk.BooleanVar()
        self.search_district = tk.Checkbutton(
            self.search_frame, text="District Notes", anchor=tk.W, variable=self.search_district_var
        )
        self.search_personal_var = tk.BooleanVar()
        self.search_personal = tk.Checkbutton(
            self.search_frame, text="Personal Notes", anchor=tk.W, variable=self.search_personal_var
        )
        self.search_desc.select()
        self.search_district.select()

        self.search_desc.pack(fill=tk.X)
        self.search_district.pack(fill=tk.X)
        self.search_personal.pack(fill=tk.X)

        self.cost_frame = ttk.Frame(self.grid, relief=tk.SUNKEN, padding=5)
        self.cost_frame.pack(fill=tk.X)
        self.cost_label = ttk.Label(self.cost_frame, text="Cost Categories")
        self.cost_div = ttk.Separator(self.cost_frame, orient=tk.HORIZONTAL)
        self.cost_labor_var = tk.BooleanVar()
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
        self.cost_contingency = tk.Checkbutton(
            self.cost_frame, text="Contingency & Allowances", variable=self.cost_contingency_var
        )
        self.cost_g_and_a_var = tk.BooleanVar()
        self.cost_g_and_a = tk.Checkbutton(self.cost_frame, text="G&A", variable=self.cost_g_and_a_var)

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
        self.cost_g_and_a.grid(row=4, column=2, sticky=tk.W)

        for i in range(3):
            self.cost_frame.columnconfigure(i, weight=1)

        self.results_frame = ttk.Frame(self.grid, relief=tk.SUNKEN, padding=5)
        self.results_frame.pack(expand=True, fill=tk.BOTH)
        self.results_label = ttk.Label(self.results_frame, text="Search Results", anchor=tk.W)
        self.results_label.pack(fill=tk.X)
        style = Style()
        style.layout("Treeview.Heading", [])
        self.results_list = ttk.Treeview(self.results_frame, selectmode="browse")
        self.results_list.pack(expand=True, fill=tk.BOTH)

        self.search_button = ttk.Button(self.grid, text="Search", command=self._search)
        self.search_button.pack(side=tk.RIGHT, pady=5)

        self.center_window(parent)
        self.deiconify()

    def _search(self):
        search_terms = self.search_term.get().split(" ")
        search_locations = {
            "Description": self.search_desc_var.get(),
            "District_Notes": self.search_district_var.get(),
            "Personal_Notes": self.search_personal_var.get(),
        }
        search_costs = bitarray(
            [
                self.cost_labor_var.get(),
                self.cost_equip_var.get(),
                self.cost_fom_equip_var.get(),
                self.cost_supplies_var.get(),
                self.cost_materials_var.get(),
                self.cost_subcontract_var.get(),
                self.cost_fixed_var.get(),
                self.cost_contingency_var.get(),
                self.cost_g_and_a_var.get(),
            ]
        )
        print(search_terms, search_locations, search_costs, "", sep="\n")
