import tkinter as tk
from tkinter import BooleanVar, ttk

from constants import AccountCodeFields, AccountCodeFlags
from models import AccountCode


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
            checkbox = ttk.Checkbutton(self.frame, variable=var, state="disabled")
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
            notes = self.pnotes_text.get("1.0", tk.END)
            if notes.isspace():
                notes = None
            else:
                notes = notes.rstrip()
            self.current_account_code.personal_notes = notes
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
