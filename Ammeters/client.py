import math
from socket import AF_INET, SOCK_STREAM, socket


def request_current_from_ammeter(port: int, command: bytes, timeout: float = 2.0) -> float:
    with socket(AF_INET, SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(('localhost', port))
        s.sendall(command)
        data = s.recv(1024)
        if not data:
            raise ValueError(f"Ammeter on port {port} returned an empty response")

        try:
            current = float(data.decode('utf-8'))
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError(f"Ammeter on port {port} returned a malformed response") from error

        if not math.isfinite(current):
            raise ValueError(f"Ammeter on port {port} returned a non-finite measurement")

        return current

