#!/usr/bin/env python3
"""run_receiver.py — lance capture_receiver.py en service (pas le selftest), imprime
l'IP d'ecoute et un point de sante toutes les 10 s."""
import sys
import time

sys.path.insert(0, "/home/younes/arma3-marl/capture_bridge")
from capture_receiver import CaptureReceiver

PORT = 8765

if __name__ == "__main__":
    recv = CaptureReceiver(port=PORT).start()
    print(f"[run_receiver] pret, en ecoute sur 0.0.0.0:{PORT}")
    while True:
        time.sleep(10)
        print(f"[run_receiver] stats={recv.stats()}")
