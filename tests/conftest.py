import multiprocessing
import socket
import threading
import time
from contextlib import contextmanager

import pytest

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter


AMMETERS = (
    pytest.param(GreenleeAmmeter, 0.01, 100.0, id="greenlee"),
    pytest.param(EntesAmmeter, 5.0, 200.0, id="entes"),
    pytest.param(CircutorAmmeter, 0.001, 0.1, id="circutor"),
)


def unused_tcp_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("localhost", 0))
        return server.getsockname()[1]


def _serve(emulator_class, port):
    emulator_class(port).start_server()


@pytest.fixture
def real_emulator():
    processes = []

    def start(emulator_class):
        port = unused_tcp_port()
        process = multiprocessing.Process(target=_serve, args=(emulator_class, port))
        process.start()
        processes.append(process)

        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(("localhost", port), timeout=0.05):
                    return port
            except OSError:
                time.sleep(0.01)
        pytest.fail(f"{emulator_class.__name__} did not start")

    yield start

    for process in processes:
        process.terminate()
        process.join(timeout=1)


@contextmanager
def fake_server(response=None, response_delay=0):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("localhost", 0))
        server.listen()
        port = server.getsockname()[1]

        def handle_request():
            connection, _ = server.accept()
            with connection:
                connection.recv(1024)
                if response_delay:
                    time.sleep(response_delay)
                if response is not None:
                    connection.sendall(response)

        thread = threading.Thread(target=handle_request, daemon=True)
        thread.start()
        yield port
        thread.join(timeout=1)

