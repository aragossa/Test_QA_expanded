import socket
import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from src.testing.test_framework import AmmeterTestFramework


AMMETER_PORTS = (5001, 5002, 5003)


def run_greenlee_emulator():
    GreenleeAmmeter(5001).start_server()


def run_entes_emulator():
    EntesAmmeter(5002).start_server()


def run_circutor_emulator():
    CircutorAmmeter(5003).start_server()


def wait_for_servers(ports, timeout=5.0):
    pending = set(ports)
    deadline = time.monotonic() + timeout
    while pending:
        for port in tuple(pending):
            try:
                with socket.create_connection(("localhost", port), timeout=0.1):
                    pending.remove(port)
            except OSError:
                pass
        if not pending:
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Emulators did not start on ports: {sorted(pending)}")
        time.sleep(0.05)


def main():
    threading.Thread(target=run_greenlee_emulator, daemon=True).start()
    threading.Thread(target=run_entes_emulator, daemon=True).start()
    threading.Thread(target=run_circutor_emulator, daemon=True).start()
    wait_for_servers(AMMETER_PORTS)

    framework = AmmeterTestFramework()
    for ammeter_type in ("greenlee", "entes", "circutor"):
        result = framework.run_test(ammeter_type)
        print(
            f"{ammeter_type.upper()}: {len(result['measurements'])} measurements, "
            f"mean {result['analysis']['mean']} A, test ID {result['test_id']}"
        )


if __name__ == "__main__":
    main()
