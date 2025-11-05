import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bio_unit_converters as conv


def test_ng_per_uL_to_mg_per_L():
    # 1 ng/µL should equal 1 mg/L
    out = conv.convert_concentration(1.0, "ng/µL", "mg/L")
    assert pytest.approx(out, rel=1e-12) == 1.0
    out2 = conv.convert_concentration(1.0, "ng/uL", "mg/L")
    assert pytest.approx(out2, rel=1e-12) == 1.0
