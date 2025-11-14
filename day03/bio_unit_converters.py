"""
bio_unit_converters.py
----------------------
A pure-library module with functions to convert common biology units.

Supported:
- Volume: L, mL, µL/uL, nL
- Mass: kg, g, mg, µg/ug, ng
- Molarity: M, mM, µM/uM, nM
- Mass concentration: g/L, mg/mL, µg/mL/ug/mL, ng/µL/ng/uL, mg/L, µg/L/ug/L, ng/L, %w/v

Cross-family conversions:
- molarity <-> mass concentration (requires molar mass in g/mol)
"""

from __future__ import annotations

# -------- Volume --------
_VOLUME_TO_L = {
    "l": 1.0,
    "ml": 1e-3,
    "µl": 1e-6, "ul": 1e-6,
    "nl": 1e-9,
}

# -------- Mass --------
_MASS_TO_G = {
    "kg": 1e3,
    "g": 1.0,
    "mg": 1e-3,
    "µg": 1e-6, "ug": 1e-6,
    "ng": 1e-9,
}

# -------- Concentration (within type) --------
# Molarity base: mol/L
_MOLARITY_TO_M = {
    "m": 1.0,
    "mm": 1e-3,
    "µm": 1e-6, "um": 1e-6,
    "nm": 1e-9,
}

# Mass concentration base: g/L
_MASSCONC_TO_G_PER_L = {
    "g/l": 1.0,
    "mg/ml": 1e0,     # 1 mg/mL = 1 g/L
    "µg/ml": 1e-3, "ug/ml": 1e-3,
    "ng/µl": 1e-3, "ng/ul": 1e-3,  # 1 ng/µL = 1 mg/L = 0.001 g/L
    "mg/l": 1e-3,
    "µg/l": 1e-6, "ug/l": 1e-6,
    "ng/l": 1e-9,
    "mg/µl": 1e3, "mg/ul": 1e3,  # rare but defined
    # Include percent w/v (% w/v) as g/100 mL = 10 g/L
    "%w/v": 10.0,
}

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
    return u

# ---------------- Public API ----------------
def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
    """Convert volume between L, mL, µL/uL, nL."""
    fu = _normalize_unit(from_unit)
    tu = _normalize_unit(to_unit)
    if fu not in _VOLUME_TO_L or tu not in _VOLUME_TO_L:
        raise ValueError(f"Unsupported volume unit. Supported: {sorted(_VOLUME_TO_L.keys())}")
    liters = value * _VOLUME_TO_L[fu]
    return liters / _VOLUME_TO_L[tu]

def convert_mass(value: float, from_unit: str, to_unit: str) -> float:
    """Convert mass between kg, g, mg, µg/ug, ng."""
    fu = _normalize_unit(from_unit)
    tu = _normalize_unit(to_unit)
    if fu not in _MASS_TO_G or tu not in _MASS_TO_G:
        raise ValueError(f"Unsupported mass unit. Supported: {sorted(_MASS_TO_G.keys())}")
    grams = value * _MASS_TO_G[fu]
    return grams / _MASS_TO_G[tu]

def convert_concentration(value: float, from_unit: str, to_unit: str) -> float:
    """Convert concentration within the same family (molarity or mass-concentration).
    
    - Molarity family: M, mM, µM/uM, nM
    - Mass concentration family: g/L, mg/mL, µg/mL/ug/mL, ng/µL/ng/uL, mg/L, µg/L/ug/L, ng/L, %w/v
    
    To convert between families, use:
      - molarity_to_mass_conc(..., mw_g_per_mol)
      - mass_conc_to_molarity(..., mw_g_per_mol)
    """
    fu = _normalize_unit(from_unit)
    tu = _normalize_unit(to_unit)
    in_molar = fu in _MOLARITY_TO_M and tu in _MOLARITY_TO_M
    in_massc = fu in _MASSCONC_TO_G_PER_L and tu in _MASSCONC_TO_G_PER_L
    if in_molar:
        molar = value * _MOLARITY_TO_M[fu]
        return molar / _MOLARITY_TO_M[tu]
    if in_massc:
        g_per_l = value * _MASSCONC_TO_G_PER_L[fu]
        return g_per_l / _MASSCONC_TO_G_PER_L[tu]
    raise ValueError("Cross-family conversion requested; use molarity_to_mass_conc or mass_conc_to_molarity with molar mass.")

def molarity_to_mass_conc(value: float, from_unit: str, to_unit: str, mw_g_per_mol: float) -> float:
    """Convert molarity (M family) -> mass concentration (g/L family).
    
    Args:
        value: numeric value
        from_unit: 'M', 'mM', 'µM'/'uM', 'nM'
        to_unit: e.g., 'g/L', 'mg/mL', 'mg/L', '%w/v'
        mw_g_per_mol: molar mass in g/mol
    """
    fu = _normalize_unit(from_unit)
    tu = _normalize_unit(to_unit)
    if fu not in _MOLARITY_TO_M:
        raise ValueError("from_unit must be a molarity unit like M, mM, µM/uM, nM")
    if tu not in _MASSCONC_TO_G_PER_L:
        raise ValueError("to_unit must be a mass concentration unit like g/L, mg/mL, mg/L, %w/v")
    mol_per_l = value * _MOLARITY_TO_M[fu]
    g_per_l = mol_per_l * mw_g_per_mol
    return g_per_l / _MASSCONC_TO_G_PER_L[tu]

def mass_conc_to_molarity(value: float, from_unit: str, to_unit: str, mw_g_per_mol: float) -> float:
    """Convert mass concentration (g/L family) -> molarity (M family)."""
    fu = _normalize_unit(from_unit)
    tu = _normalize_unit(to_unit)
    if fu not in _MASSCONC_TO_G_PER_L:
        raise ValueError("from_unit must be a mass concentration unit like g/L, mg/mL, mg/L, %w/v")
    if tu not in _MOLARITY_TO_M:
        raise ValueError("to_unit must be a molarity unit like M, mM, µM/uM, nM")
    g_per_l = value * _MASSCONC_TO_G_PER_L[fu]
    mol_per_l = g_per_l / mw_g_per_mol
    return mol_per_l / _MOLARITY_TO_M[tu]

__all__ = [
    "convert_volume",
    "convert_mass",
    "convert_concentration",
    "molarity_to_mass_conc",
    "mass_conc_to_molarity",
]
