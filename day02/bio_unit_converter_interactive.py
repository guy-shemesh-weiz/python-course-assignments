#!/usr/bin/env python3
"""
Interactive Biology Unit Converter
----------------------------------
Uses bio_unit_converters.py and prompts the user for inputs.
Run:
  python bio_unit_converter_interactive.py
"""

import sys

try:
    import bio_unit_converters as conv
except Exception as e:
    sys.stderr.write("Could not import bio_unit_converters.py. "
                     "Place it in the same folder or on PYTHONPATH.\n")
    raise

# Use canonical lists from the conversion library to avoid duplication
VOLUME_UNITS = conv.VOLUME_UNITS
MASS_UNITS = conv.MASS_UNITS
MOLAR_UNITS = conv.MOLAR_UNITS
MASSC_UNITS = conv.MASSCONC_UNITS

def norm(u: str) -> str:
    return u.strip().replace("μ", "µ")

def pick(prompt: str, options):
    """Simple numeric picker for options list."""
    while True:
        print(prompt)
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
        sel = input("> ").strip()
        if sel.isdigit():
            idx = int(sel)
            if 1 <= idx <= len(options):
                return options[idx-1]
        print("Please enter a valid number.\n")

def ask_float(prompt: str):
    while True:
        s = input(prompt).strip()
        try:
            return float(s)
        except ValueError:
            print("Please enter a numeric value.\n")

def main():
    print("=== Biology Unit Converter (Interactive) ===")
    print("Tip: You can use 'u' or 'µ' for micro (e.g., uL or µL). %w/v = g per 100 mL.\n")

    while True:
        mode = pick("Choose a conversion type:", [
            "Volume",
            "Mass",
            "Concentration (within family)",
            "Molarity → Mass concentration (requires molar mass)",
            "Mass concentration → Molarity (requires molar mass)",
            "Quit",
        ])

        if mode == "Quit":
            print("Goodbye!")
            break

        try:
            if mode == "Volume":
                value = ask_float("Enter value: ")
                from_u = pick("From unit:", VOLUME_UNITS)
                to_u = pick("To unit:", VOLUME_UNITS)
                result = conv.convert_volume(value, norm(from_u), norm(to_u))
                print(f"Result: {result:.10g}\n")

            elif mode == "Mass":
                value = ask_float("Enter value: ")
                from_u = pick("From unit:", MASS_UNITS)
                to_u = pick("To unit:", MASS_UNITS)
                result = conv.convert_mass(value, norm(from_u), norm(to_u))
                print(f"Result: {result:.10g}\n")

            elif mode == "Concentration (within family)":
                value = ask_float("Enter value: ")
                from_u = pick("From unit:", MOLAR_UNITS + MASSC_UNITS)
                to_u = pick("To unit:", MOLAR_UNITS + MASSC_UNITS)
                result = conv.convert_concentration(value, norm(from_u), norm(to_u))
                print(f"Result: {result:.10g}\n")

            elif mode == "Molarity → Mass concentration (requires molar mass)":
                value = ask_float("Enter value: ")
                from_u = pick("From unit (molarity):", MOLAR_UNITS)
                to_u = pick("To unit (mass conc):", MASSC_UNITS)
                mw = ask_float("Enter molar mass (g/mol): ")
                result = conv.molarity_to_mass_conc(value, norm(from_u), norm(to_u), mw)
                print(f"Result: {result:.10g}\n")

            elif mode == "Mass concentration → Molarity (requires molar mass)":
                value = ask_float("Enter value: ")
                from_u = pick("From unit (mass conc):", MASSC_UNITS)
                to_u = pick("To unit (molarity):", MOLAR_UNITS)
                mw = ask_float("Enter molar mass (g/mol): ")
                result = conv.mass_conc_to_molarity(value, norm(from_u), norm(to_u), mw)
                print(f"Result: {result:.10g}\n")

        except Exception as e:
            print(f"Error: {e}\n")

        # Continue?
        again = input("Do another conversion? [Y/n]: ").strip().lower()
        if again.startswith("n"):
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()
