import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from src.testing.test_framework import AmmeterTestFramework


def run_greenlee_emulator():
    greenlee = GreenleeAmmeter(5001)
    greenlee.start_server()

def run_entes_emulator():
    entes = EntesAmmeter(5002)
    entes.start_server()

def run_circutor_emulator():
    circutor = CircutorAmmeter(5003)
    circutor.start_server()

if __name__ == "__main__":
    # Start each ammeter in a separate thread
    threading.Thread(target=run_greenlee_emulator, daemon=True).start()
    threading.Thread(target=run_entes_emulator, daemon=True).start()
    threading.Thread(target=run_circutor_emulator, daemon=True).start()

    # Give the background servers a moment to bind their sockets.
    time.sleep(5)

    framework = AmmeterTestFramework()
    for ammeter_type in ("greenlee", "entes", "circutor"):
        result = framework.run_test(ammeter_type)
        print(
            f"{ammeter_type.upper()}: {len(result['measurements'])} measurements, "
            f"mean {result['analysis']['mean']} A, test ID {result['test_id']}"
        )
