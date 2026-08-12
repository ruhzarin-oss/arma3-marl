#!/usr/bin/env python3
"""ecoute.py — se branche sur le pont Antistasi et imprime ce que le capteur emet.

Usage : python3 ecoute.py [duree_s] [port]
Le pont n'ecoute que sur la loopback : a lancer SUR la workstation.
"""
import socket, sys, time

duree = float(sys.argv[1]) if len(sys.argv) > 1 else 40.0
port = int(sys.argv[2]) if len(sys.argv) > 2 else 5876

s = socket.create_connection(("127.0.0.1", port), timeout=10)
s.settimeout(2.0)
buf = b""
t0 = time.time()
n = 0
while time.time() - t0 < duree:
    try:
        d = s.recv(65536)
    except socket.timeout:
        continue
    if not d:
        print("PONT FERME"); break
    buf += d
    while b"\n" in buf:
        ln, buf = buf.split(b"\n", 1)
        ln = ln.decode("utf-8", "replace").strip()
        if ln:
            n += 1
            print("%6.1fs  %s" % (time.time() - t0, ln[:300]))
s.close()
print("--- %d lignes en %.0f s ---" % (n, time.time() - t0))
