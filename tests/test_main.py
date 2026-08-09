import pytest

import main


class Connection:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


def test_wait_for_servers_retries_until_every_port_is_ready(monkeypatch):
    attempts = {5001: 0, 5002: 0}

    def connect(address, timeout):
        port = address[1]
        attempts[port] += 1
        if port == 5002 and attempts[port] == 1:
            raise ConnectionRefusedError
        return Connection()

    monkeypatch.setattr(main.socket, "create_connection", connect)
    monkeypatch.setattr(main.time, "sleep", lambda _: None)

    main.wait_for_servers((5001, 5002), timeout=1)

    assert attempts == {5001: 1, 5002: 2}


def test_wait_for_servers_reports_ports_that_never_start(monkeypatch):
    times = iter((0.0, 0.0, 1.0))
    monkeypatch.setattr(main.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(
        main.socket,
        "create_connection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ConnectionRefusedError()),
    )

    with pytest.raises(TimeoutError, match=r"\[5003\]"):
        main.wait_for_servers((5003,), timeout=0.5)


def test_example_uses_the_working_main_entry_point():
    from examples.run_tests import main as example_main

    assert example_main is main.main
