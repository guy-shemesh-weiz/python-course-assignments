import sys
from pathlib import Path
import pytest

# Ensure the project root (parent of tests/) is on sys.path so tests can import local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bio_unit_converters as conv


def test_volume_round_trip():
    # 2 mL -> uL -> mL should return original value
    v = 2.0
    ul = conv.convert_volume(v, "mL", "µL")
    back = conv.convert_volume(ul, "µL", "mL")
    assert pytest.approx(back, rel=1e-12) == v


def test_molarity_to_mass_conc_known_mw():
    # 1 mM of a compound with MW=100 g/mol -> 0.1 g/L
    out = conv.molarity_to_mass_conc(1.0, "mM", "g/L", 100.0)
    assert pytest.approx(out, rel=1e-12) == 0.1


def test_normalize_u_vs_micro():
    # library should accept ASCII 'u' and micro 'µ' equivalently
    a = conv.convert_mass(1.0, "mg", "ug")
    b = conv.convert_mass(1.0, "mg", "µg")
    assert pytest.approx(a, rel=1e-12) == b
