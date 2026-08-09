import math
import socket

import pytest

from Ammeters.client import request_current_from_ammeter
from conftest import AMMETERS, fake_server, unused_tcp_port


@pytest.mark.parametrize("emulator_class,minimum,maximum", AMMETERS)
def test_correct_command_returns_finite_measurement_in_expected_range(
    real_emulator, emulator_class, minimum, maximum
):
    port = real_emulator(emulator_class)

    result = request_current_from_ammeter(
        port, emulator_class(port).get_current_command, timeout=0.5
    )

    assert isinstance(result, float)
    assert math.isfinite(result)
    assert minimum <= result <= maximum


@pytest.mark.parametrize("emulator_class,minimum,maximum", AMMETERS)
def test_wrong_command_is_rejected(real_emulator, emulator_class, minimum, maximum):
    port = real_emulator(emulator_class)

    with pytest.raises(ValueError, match="empty response"):
        request_current_from_ammeter(port, b"NOT_A_REAL_COMMAND", timeout=0.5)


def test_connection_error_is_propagated():
    with pytest.raises(ConnectionRefusedError):
        request_current_from_ammeter(unused_tcp_port(), b"MEASURE", timeout=0.1)


def test_silent_server_triggers_timeout():
    with fake_server(response_delay=0.3) as port:
        with pytest.raises(socket.timeout):
            request_current_from_ammeter(port, b"MEASURE", timeout=0.05)


@pytest.mark.parametrize("response", [b"", b"not-a-number"])
def test_empty_or_malformed_response_is_rejected(response):
    with fake_server(response=response) as port:
        with pytest.raises(ValueError):
            request_current_from_ammeter(port, b"MEASURE", timeout=0.5)


@pytest.mark.parametrize("response", [b"nan", b"inf", b"-inf"])
def test_non_finite_measurement_is_rejected(response):
    with fake_server(response=response) as port:
        with pytest.raises(ValueError, match="finite"):
            request_current_from_ammeter(port, b"MEASURE", timeout=0.5)


@pytest.mark.parametrize("emulator_class,minimum,maximum", AMMETERS)
def test_repeated_measurements_continue_after_rejected_command(
    real_emulator, emulator_class, minimum, maximum
):
    port = real_emulator(emulator_class)
    command = emulator_class(port).get_current_command

    first = request_current_from_ammeter(port, command, timeout=0.5)
    with pytest.raises(ValueError):
        request_current_from_ammeter(port, b"NOT_A_REAL_COMMAND", timeout=0.5)
    second = request_current_from_ammeter(port, command, timeout=0.5)

    assert minimum <= first <= maximum
    assert minimum <= second <= maximum

