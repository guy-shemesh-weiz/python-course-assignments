"""
bio_unit_converters.py
----------------------
A pure-library module with functions to convert common biology units using Pint.

Supported:
- Volume: L, mL, µL/uL, nL
- Mass: kg, g, mg, µg/ug, ng
- Molarity: M, mM, µM/uM, nM
- Mass concentration: g/L, mg/mL, µg/mL/ug/mL, ng/µL/ng/uL, mg/L, µg/L/ug/L, ng/L, %w/v

Cross-family conversions:
- molarity <-> mass concentration (requires molar mass in g/mol)
"""

from __future__ import annotations
import pint

# Initialize unit registry
ureg = pint.UnitRegistry()

# ------- Public unit lists (canonical, single source-of-truth for frontends) -------
# These are presentation-friendly unit lists (mixed-case) used by the CLIs/GUI.
VOLUME_UNITS = ["L", "mL", "µL", "uL", "nL"]
MASS_UNITS = ["kg", "g", "mg", "µg", "ug", "ng"]
MOLAR_UNITS = ["M", "mM", "µM", "uM", "nM"]
MASSCONC_UNITS = [
    "g/L",
    "mg/mL",
    "µg/mL",
    "ug/mL",
    "ng/µL",
    "ng/uL",
    "mg/L",
    "µg/L",
    "ug/L",
    "ng/L",
    "%w/v",
]

# ASCII-only presentations for places that require typeable ASCII (CLI help/examples)
ASCII_VOLUME = [u.replace("µ", "u") for u in VOLUME_UNITS if u != "µL" or True]
ASCII_MASS = [u.replace("µ", "u") for u in MASS_UNITS]
ASCII_MOLAR = [u.replace("µ", "u") for u in MOLAR_UNITS]
ASCII_MASSCONC = [u.replace("µ", "u") for u in MASSCONC_UNITS]

def _normalize_unit(u: str) -> str:
    """Lowercase, trim, and normalize micro symbol (μ -> µ)."""
    u = u.strip().lower().replace("μ", "µ")
    # Map unicode micro to pint's format (u)
    u = u.replace("µ", "u")
    # Important: handle molar units (m, mm, um, nm) before converting to mL, mm etc.
    # Pint uses 'molar' for molarity, so we need to map properly
    return u


def _unit_to_pint_string(unit: str) -> str:
    """Convert our unit notation to Pint-compatible notation.
    
    This handles special cases like:
    - mM (millimolar) -> millimol/liter (not millimeter)
    - uM (micromolar) -> micromol/liter
    - M (molar) -> mol/liter
    - µM (micromolar using unicode) -> micromol/liter
    - ug/mL -> microgram/milliliter
    """
    unit_lower = unit.strip().lower().replace("μ", "u")
    
    # Map MOLARITY units explicitly first (before checking for other micro units)
    molarity_map = {
        "m": "mol/L",
        "mm": "mmol/L",
        "um": "umol/L",
        "µm": "umol/L",
        "nm": "nmol/L",
    }
    
    if unit_lower in molarity_map:
        return molarity_map[unit_lower]
    
    # For mass concentration and other units, replace only the 'u' that means micro
    # when NOT followed by 'l' (which would be the start of mol)
    # Map common chemistry units
    massconc_map = {
        "g/l": "g/L",
        "mg/ml": "mg/mL",
        "ug/ml": "ug/mL",
        "mg/l": "mg/L",
        "ug/l": "ug/L",
        "ng/l": "ng/L",
        "ng/ul": "ng/uL",
        "mg/ul": "mg/uL",
    }
    
    if unit_lower in massconc_map:
        return massconc_map[unit_lower]
    
    # Return as-is for other units (pint should understand them)
    return unit_lower


def _pint_convert(value: float, from_unit: str, to_unit: str) -> float:
    """Helper function to perform unit conversion using Pint.
    
    Args:
        value: numeric value
        from_unit: source unit string
        to_unit: target unit string
    
    Returns:
        converted numeric value
    
    Raises:
        ValueError: if units are incompatible or unsupported
    """
    try:
        # Normalize units: handle unicode micro and convert to pint format
        from_unit_norm = _unit_to_pint_string(from_unit)
        to_unit_norm = _unit_to_pint_string(to_unit)
        
        # Handle special case: %w/v (percent w/v) -> convert to g/L for pint
        if _normalize_unit(from_unit) == "%w/v":
            from_unit_norm = "g/L"
            value = value * 10  # %w/v is 10 g/L
        if _normalize_unit(to_unit) == "%w/v":
            to_unit_norm = "g/L"
        
        # Create quantities and convert
        q = ureg.Quantity(value, from_unit_norm)
        result = q.to(to_unit_norm)
        
        # If target was %w/v, convert back
        if to_unit_norm == "g/L" and _normalize_unit(to_unit) == "%w/v":
            return result.magnitude / 10
        
        return result.magnitude
    except pint.UndefinedUnitError as e:
        raise ValueError(f"Unsupported unit: {str(e)}")
    except pint.DimensionalityError as e:
        raise ValueError(f"Incompatible units: {str(e)}")
    except Exception as e:
        raise ValueError(f"Conversion error: {str(e)}")

# ---------------- Public API ----------------
def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
    """Convert volume between L, mL, µL/uL, nL."""
    try:
        return _pint_convert(value, from_unit, to_unit)
    except ValueError as e:
        raise ValueError(f"Unsupported volume unit. Supported: {', '.join(VOLUME_UNITS)}. Error: {str(e)}")


def convert_mass(value: float, from_unit: str, to_unit: str) -> float:
    """Convert mass between kg, g, mg, µg/ug, ng."""
    try:
        return _pint_convert(value, from_unit, to_unit)
    except ValueError as e:
        raise ValueError(f"Unsupported mass unit. Supported: {', '.join(MASS_UNITS)}. Error: {str(e)}")


def convert_concentration(value: float, from_unit: str, to_unit: str) -> float:
    """Convert concentration within the same family (molarity or mass-concentration).
    
    - Molarity family: M, mM, µM/uM, nM
    - Mass concentration family: g/L, mg/mL, µg/mL/ug/mL, ng/µL/ng/uL, mg/L, µg/L/ug/L, ng/L, %w/v
    
    To convert between families, use:
      - molarity_to_mass_conc(..., mw_g_per_mol)
      - mass_conc_to_molarity(..., mw_g_per_mol)
    """
    from_unit_norm = _normalize_unit(from_unit)
    to_unit_norm = _normalize_unit(to_unit)
    
    # Check if both are in the same family
    molarity_units = [_normalize_unit(u) for u in MOLAR_UNITS]
    massconc_units = [_normalize_unit(u) for u in MASSCONC_UNITS]
    
    in_molar = from_unit_norm in molarity_units and to_unit_norm in molarity_units
    in_massc = from_unit_norm in massconc_units and to_unit_norm in massconc_units
    
    if not (in_molar or in_massc):
        raise ValueError("Cross-family conversion requested; use molarity_to_mass_conc or mass_conc_to_molarity with molar mass.")
    
    try:
        return _pint_convert(value, from_unit, to_unit)
    except ValueError as e:
        raise ValueError(f"Concentration conversion error: {str(e)}")


def molarity_to_mass_conc(value: float, from_unit: str, to_unit: str, mw_g_per_mol: float) -> float:
    """Convert molarity (M family) -> mass concentration (g/L family).
    
    Args:
        value: numeric value
        from_unit: 'M', 'mM', 'µM'/'uM', 'nM'
        to_unit: e.g., 'g/L', 'mg/mL', 'mg/L', '%w/v'
        mw_g_per_mol: molar mass in g/mol
    """
    try:
        from_unit_pint = _unit_to_pint_string(from_unit)
        to_unit_norm = _normalize_unit(to_unit)
        
        # Step 1: Convert the molarity value to mol/L
        molarity_value = ureg.Quantity(value, from_unit_pint)
        mol_per_l = molarity_value.to("mol/L").magnitude
        
        # Step 2: Convert mol/L to g/L using the molar mass
        g_per_l_value = mol_per_l * mw_g_per_mol
        
        # Step 3: Handle special case: %w/v
        if to_unit_norm == "%w/v":
            # %w/v is g/100mL = 10 g/L
            return g_per_l_value / 10.0
        
        # Step 4: Convert from g/L to target mass concentration unit
        g_per_l_quantity = ureg.Quantity(g_per_l_value, "g/L")
        to_unit_pint = _unit_to_pint_string(to_unit)
        result = g_per_l_quantity.to(to_unit_pint)
        return result.magnitude
    except pint.UndefinedUnitError as e:
        raise ValueError(f"Unsupported unit: {str(e)}")
    except pint.DimensionalityError as e:
        raise ValueError(f"Incompatible units: {str(e)}")
    except Exception as e:
        raise ValueError(f"Conversion error: {str(e)}")


def mass_conc_to_molarity(value: float, from_unit: str, to_unit: str, mw_g_per_mol: float) -> float:
    """Convert mass concentration (g/L family) -> molarity (M family)."""
    try:
        from_unit_norm = _normalize_unit(from_unit)
        to_unit_pint = _unit_to_pint_string(to_unit)
        
        # Handle special case: %w/v
        if from_unit_norm == "%w/v":
            # %w/v is g/100mL = 10 g/L
            g_per_l_value = value * 10
        else:
            # Convert to g/L first using pint
            from_unit_pint = _unit_to_pint_string(from_unit)
            mass_conc = ureg.Quantity(value, from_unit_pint)
            g_per_l_value = mass_conc.to(ureg.g / ureg.L).magnitude
        
        # Convert g/L to molarity using molar mass
        mol_per_l = g_per_l_value / mw_g_per_mol
        molarity = ureg.Quantity(mol_per_l, "mol/L")
        
        # Convert to target unit
        result = molarity.to(to_unit_pint)
        return result.magnitude
    except pint.UndefinedUnitError as e:
        raise ValueError(f"Unsupported unit: {str(e)}")
    except pint.DimensionalityError as e:
        raise ValueError(f"Incompatible units: {str(e)}")
    except Exception as e:
        raise ValueError(f"Conversion error: {str(e)}")

__all__ = [
    "convert_volume",
    "convert_mass",
    "convert_concentration",
    "molarity_to_mass_conc",
    "mass_conc_to_molarity",
    "VOLUME_UNITS",
    "MASS_UNITS",
    "MOLAR_UNITS",
    "MASSCONC_UNITS",
    "ASCII_VOLUME",
    "ASCII_MASS",
    "ASCII_MOLAR",
    "ASCII_MASSCONC",
]
