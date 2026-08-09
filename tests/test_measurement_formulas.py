import pytest

import Ammeters.Circutor_Ammeter as circutor_module
import Ammeters.Entes_Ammeter as entes_module
import Ammeters.Greenlee_Ammeter as greenlee_module
from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter


@pytest.mark.parametrize(
    ("voltage", "resistance", "expected"),
    [(1.0, 100.0, 0.01), (10.0, 0.1, 100.0)],
)
def test_greenlee_uses_ohms_law(monkeypatch, voltage, resistance, expected):
    values = iter((voltage, resistance))
    monkeypatch.setattr(greenlee_module, "generate_random_float", lambda *_: next(values))

    assert GreenleeAmmeter(0).measure_current() == pytest.approx(expected)


@pytest.mark.parametrize(
    ("magnetic_field", "calibration_factor", "expected"),
    [(0.01, 500.0, 5.0), (0.1, 2000.0, 200.0)],
)
def test_entes_uses_hall_effect_formula(
    monkeypatch, magnetic_field, calibration_factor, expected
):
    values = iter((magnetic_field, calibration_factor))
    monkeypatch.setattr(entes_module, "generate_random_float", lambda *_: next(values))

    assert EntesAmmeter(0).measure_current() == pytest.approx(expected)


@pytest.mark.parametrize(
    ("time_step", "voltage", "expected"),
    [(0.001, 0.1, 0.001), (0.01, 1.0, 0.1)],
)
def test_circutor_integrates_ten_voltage_samples(
    monkeypatch, time_step, voltage, expected
):
    values = iter((time_step, *([voltage] * 10)))
    monkeypatch.setattr(circutor_module, "generate_random_float", lambda *_: next(values))

    assert CircutorAmmeter(0).measure_current() == pytest.approx(expected)

