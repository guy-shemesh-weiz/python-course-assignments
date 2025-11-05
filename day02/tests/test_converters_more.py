import sys
from pathlib import Path
import pytest

# Ensure local package is importable when pytest runs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bio_unit_converters as conv


def test_molarity_within_family():
    # 1000 µM -> 1 mM
    out = conv.convert_concentration(1000.0, "µM", "mM")
    assert pytest.approx(out, rel=1e-12) == 1.0


def test_percent_wv_to_g_per_l():
    # 1 %w/v should be 10 g/L (implementation uses 10.0 in mapping)
    out = conv.convert_concentration(1.0, "%w/v", "g/L")
    assert pytest.approx(out, rel=1e-12) == 10.0


def test_mass_conc_to_molarity_known():
    # 0.1 g/L of MW=100 g/mol -> 1 mM
    out = conv.mass_conc_to_molarity(0.1, "g/L", "mM", 100.0)
    assert pytest.approx(out, rel=1e-12) == 1.0


def test_convert_concentration_cross_family_raises():
    # convert_concentration should not accept cross-family conversions
    with pytest.raises(ValueError):
        conv.convert_concentration(1.0, "M", "g/L")


def test_unsupported_volume_unit_raises():
    with pytest.raises(ValueError):
        conv.convert_volume(1.0, "foo", "mL")
