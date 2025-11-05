#!/usr/bin/env python3
"""
Tkinter GUI for Bio Unit Converters
-----------------------------------
Requires: bio_unit_converters.py (same folder or on PYTHONPATH)

Features:
- Volume conversion (L, mL, µL/uL, nL)
- Mass conversion (kg, g, mg, µg/ug, ng)
- Concentration conversion within family:
    * Molarity: M, mM, µM/uM, nM
    * Mass concentration: g/L, mg/mL, µg/mL/ug/mL, ng/µL/ng/uL, mg/L, µg/L/ug/L, ng/L, %w/v
- Cross-family conversions with molar mass:
    * Molarity -> Mass concentration
    * Mass concentration -> Molarity
"""

import tkinter as tk
from tkinter import ttk, messagebox

# Try to import the converter library
import bio_unit_converters as conv


# ------- Helpers -------
def normalize_unit(u: str) -> str:
    """Normalize common micro symbol inputs."""
    return u.replace("μ", "µ")


def parse_float(entry: tk.Entry, field_name: str) -> float:
    try:
        return float(entry.get())
    except ValueError:
        raise ValueError(f"{field_name} must be a number.")


def set_result(label: ttk.Label, value: float):
    label.config(text=f"{value:.10g}")


# ------- GUI -------
class ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Biology Unit Converter")
        self.geometry("620x420")
        self.minsize(600, 400)

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_volume_tab(nb)
        self._build_mass_tab(nb)
        self._build_conc_tab(nb)
        self._build_cross_tab(nb)

        footer = ttk.Label(self, text="Tip: Use 'µ' or 'u' for micro (e.g., µL or uL). %w/v = g per 100 mL.", anchor="center")
        footer.pack(side="bottom", fill="x", pady=(0,6))

    # ---- Volume ----
    def _build_volume_tab(self, nb: ttk.Notebook):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Volume")

        units = conv.VOLUME_UNITS

        ttk.Label(frame, text="Value").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        val_entry = ttk.Entry(frame, width=18)
        val_entry.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="From").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        from_cb = ttk.Combobox(frame, values=units, width=10, state="readonly")
        from_cb.set("mL")
        from_cb.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="To").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        to_cb = ttk.Combobox(frame, values=units, width=10, state="readonly")
        to_cb.set("µL")
        to_cb.grid(row=2, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="Result").grid(row=3, column=0, padx=6, pady=12, sticky="e")
        res = ttk.Label(frame, text="-", foreground="#1b5e20", font=("TkDefaultFont", 10, "bold"))
        res.grid(row=3, column=1, padx=6, pady=12, sticky="w")

        def run():
            try:
                v = parse_float(val_entry, "Value")
                out = conv.convert_volume(v, normalize_unit(from_cb.get()), normalize_unit(to_cb.get()))
                set_result(res, out)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(frame, text="Convert", command=run).grid(row=4, column=0, columnspan=2, pady=8)

        for i in range(2):
            frame.columnconfigure(i, weight=1)

    # ---- Mass ----
    def _build_mass_tab(self, nb: ttk.Notebook):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Mass")

        units = conv.MASS_UNITS

        ttk.Label(frame, text="Value").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        val_entry = ttk.Entry(frame, width=18)
        val_entry.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="From").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        from_cb = ttk.Combobox(frame, values=units, width=10, state="readonly")
        from_cb.set("mg")
        from_cb.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="To").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        to_cb = ttk.Combobox(frame, values=units, width=10, state="readonly")
        to_cb.set("µg")
        to_cb.grid(row=2, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="Result").grid(row=3, column=0, padx=6, pady=12, sticky="e")
        res = ttk.Label(frame, text="-", foreground="#1b5e20", font=("TkDefaultFont", 10, "bold"))
        res.grid(row=3, column=1, padx=6, pady=12, sticky="w")

        def run():
            try:
                v = parse_float(val_entry, "Value")
                out = conv.convert_mass(v, normalize_unit(from_cb.get()), normalize_unit(to_cb.get()))
                set_result(res, out)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(frame, text="Convert", command=run).grid(row=4, column=0, columnspan=2, pady=8)
        for i in range(2):
            frame.columnconfigure(i, weight=1)

    # ---- Concentration (within family) ----
    def _build_conc_tab(self, nb: ttk.Notebook):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Concentration")

        molarity_units = conv.MOLAR_UNITS
        massc_units = conv.MASSCONC_UNITS

        ttk.Label(frame, text="Value").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        val_entry = ttk.Entry(frame, width=18)
        val_entry.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="From").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        from_cb = ttk.Combobox(frame, values=molarity_units + massc_units, width=12, state="readonly")
        from_cb.set("mM")
        from_cb.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="To").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        to_cb = ttk.Combobox(frame, values=molarity_units + massc_units, width=12, state="readonly")
        to_cb.set("µM")
        to_cb.grid(row=2, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="Result").grid(row=3, column=0, padx=6, pady=12, sticky="e")
        res = ttk.Label(frame, text="-", foreground="#1b5e20", font=("TkDefaultFont", 10, "bold"))
        res.grid(row=3, column=1, padx=6, pady=12, sticky="w")

        def run():
            try:
                v = parse_float(val_entry, "Value")
                out = conv.convert_concentration(v, normalize_unit(from_cb.get()), normalize_unit(to_cb.get()))
                set_result(res, out)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(frame, text="Convert", command=run).grid(row=4, column=0, columnspan=2, pady=8)
        for i in range(2):
            frame.columnconfigure(i, weight=1)

    # ---- Cross-family (needs MW) ----
    def _build_cross_tab(self, nb: ttk.Notebook):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Cross (MW)")

        molarity_units = conv.MOLAR_UNITS
        massc_units = conv.MASSCONC_UNITS

        # Left column: Molarity -> Mass concentration
        left = ttk.LabelFrame(frame, text="Molarity → Mass Concentration")
        left.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        ttk.Label(left, text="Value").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        val1 = ttk.Entry(left, width=14)
        val1.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(left, text="From").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        from1 = ttk.Combobox(left, values=molarity_units, width=10, state="readonly")
        from1.set("µM")
        from1.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(left, text="To").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        to1 = ttk.Combobox(left, values=massc_units, width=10, state="readonly")
        to1.set("mg/L")
        to1.grid(row=2, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(left, text="Molar mass (g/mol)").grid(row=3, column=0, padx=6, pady=6, sticky="e")
        mw1 = ttk.Entry(left, width=14)
        mw1.grid(row=3, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(left, text="Result").grid(row=4, column=0, padx=6, pady=12, sticky="e")
        res1 = ttk.Label(left, text="-", foreground="#1b5e20", font=("TkDefaultFont", 10, "bold"))
        res1.grid(row=4, column=1, padx=6, pady=12, sticky="w")

        def run1():
            try:
                v = parse_float(val1, "Value")
                mw = parse_float(mw1, "Molar mass")
                out = conv.molarity_to_mass_conc(v, normalize_unit(from1.get()), normalize_unit(to1.get()), mw)
                set_result(res1, out)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(left, text="Convert", command=run1).grid(row=5, column=0, columnspan=2, pady=8)

        # Right column: Mass concentration -> Molarity
        right = ttk.LabelFrame(frame, text="Mass Concentration → Molarity")
        right.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        ttk.Label(right, text="Value").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        val2 = ttk.Entry(right, width=14)
        val2.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(right, text="From").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        from2 = ttk.Combobox(right, values=massc_units, width=10, state="readonly")
        from2.set("%w/v")
        from2.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(right, text="To").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        to2 = ttk.Combobox(right, values=molarity_units, width=10, state="readonly")
        to2.set("mM")
        to2.grid(row=2, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(right, text="Molar mass (g/mol)").grid(row=3, column=0, padx=6, pady=6, sticky="e")
        mw2 = ttk.Entry(right, width=14)
        mw2.grid(row=3, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(right, text="Result").grid(row=4, column=0, padx=6, pady=12, sticky="e")
        res2 = ttk.Label(right, text="-", foreground="#1b5e20", font=("TkDefaultFont", 10, "bold"))
        res2.grid(row=4, column=1, padx=6, pady=12, sticky="w")

        def run2():
            try:
                v = parse_float(val2, "Value")
                mw = parse_float(mw2, "Molar mass")
                out = conv.mass_conc_to_molarity(v, normalize_unit(from2.get()), normalize_unit(to2.get()), mw)
                set_result(res2, out)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(right, text="Convert", command=run2).grid(row=5, column=0, columnspan=2, pady=8)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        for section in (left, right):
            for i in range(2):
                section.columnconfigure(i, weight=1)


if __name__ == "__main__":
    app = ConverterGUI()
    app.mainloop()
