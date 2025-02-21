from tkinter import ttk


class PlaceholderEntry(ttk.Entry):
    def __init__(self, parent, placeholder, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.placeholder = placeholder
        # TODO: Placeholder style needed, standard with grey text
        self.field_style = kwargs.pop("style", "TEntry")
        self.placeholder_style = kwargs.pop("placeholder_style", self.field_style)
        self["style"] = self.placeholder_style
        self.insert("0", self.placeholder)
        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

    def _clear_placeholder(self, e):
        if self["style"] == self.placeholder_style:
            self.delete("0", "end")
            self["style"] = self.field_style

    def _add_placeholder(self, e):
        if not self.get():
            self.insert("0", self.placeholder)
            self["style"] = self.placeholder_style
