#!/usr/bin/env python3
"""capture_receiver.py — cote WSL : recoit le flux de capture_bridge.py (Windows natif),
garde le DERNIER cadre en memoire (pas de file : un cadre perime ne sert a rien), l'expose
a la boucle d'entrainement via get_latest(max_age_s).

Protocole (un message par frame, longueur variable) :
    !dIffI  -> timestamp(double), taille_image(uint32), mdx(float), mdy(float), touches(uint32)
    puis <taille_image> octets = image niveaux de gris IMG_SIZE x IMG_SIZE (uint8)

Usage typique dans la boucle d'entrainement :
    recv = CaptureReceiver(port=8765); recv.start()
    ...
    frame = recv.get_latest(max_age_s=0.3)   # None si rien de frais -> agent 0 aura has_pixel=0
"""
import socket
import struct
import threading
import time

import numpy as np

HEADER = struct.Struct("!dIffI")
IMG_SIZE = 96   # doit matcher fusion_net.IMG_SIZE et capture_bridge.IMG_SIZE


class CaptureReceiver:
    def __init__(self, port=8765, img_size=IMG_SIZE):
        self.port = port
        self.img_size = img_size
        self._lock = threading.Lock()
        self._latest = None   # (ts, gray_uint8[H,W], mdx, mdy, kmask)
        self._n_recv = 0
        self._stop = False
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop = True

    def get_latest(self, max_age_s=0.3):
        with self._lock:
            if self._latest is None:
                return None
            ts, gray, mdx, mdy, kmask = self._latest
        if time.time() - ts > max_age_s:
            return None   # perime : freshness_bench.sqf sert a mesurer ce que "perime" veut dire ici
        return gray, mdx, mdy, kmask, ts

    def stats(self):
        with self._lock:
            return {"n_recv": self._n_recv, "has_latest": self._latest is not None}

    def _serve(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", self.port))
        srv.listen(1)
        srv.settimeout(1.0)
        print(f"[capture_receiver] en ecoute sur 0.0.0.0:{self.port}")
        while not self._stop:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            print(f"[capture_receiver] connexion de {addr}")
            conn.settimeout(5.0)
            try:
                self._read_loop(conn)
            except (ConnectionError, socket.timeout, OSError) as e:
                print(f"[capture_receiver] connexion perdue ({e}), en attente d'une nouvelle")
            finally:
                conn.close()

    def _read_loop(self, conn):
        expect_img = self.img_size * self.img_size
        while not self._stop:
            header = self._recv_exact(conn, HEADER.size)
            ts, img_bytes, mdx, mdy, kmask = HEADER.unpack(header)
            payload = self._recv_exact(conn, img_bytes)
            if img_bytes != expect_img:
                continue   # taille inattendue : on jette plutot que de planter le reshape
            gray = np.frombuffer(payload, dtype=np.uint8).reshape(self.img_size, self.img_size)
            with self._lock:
                self._latest = (ts, gray, mdx, mdy, kmask)
                self._n_recv += 1

    @staticmethod
    def _recv_exact(conn, n):
        buf = bytearray()
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("pont capture ferme cote emetteur")
            buf += chunk
        return bytes(buf)


def _selftest():
    """Boucle client+serveur en local (127.0.0.1), sans Windows ni Arma : verifie le
    protocole de bout en bout. Ne prouve rien sur la vraie latence Windows->WSL."""
    recv = CaptureReceiver(port=18765).start()
    time.sleep(0.3)

    sock = socket.create_connection(("127.0.0.1", 18765), timeout=5)
    gray = (np.random.rand(IMG_SIZE, IMG_SIZE) * 255).astype(np.uint8)
    ts = time.time()
    header = HEADER.pack(ts, gray.nbytes, 0.1, -0.2, 0b101)
    sock.sendall(header + gray.tobytes())
    time.sleep(0.2)

    out = recv.get_latest(max_age_s=2.0)
    assert out is not None, "rien recu"
    g2, mdx, mdy, kmask, ts2 = out
    assert np.array_equal(g2, gray), "image corrompue en transit"
    assert abs(mdx - 0.1) < 1e-5 and abs(mdy - (-0.2)) < 1e-5, "delta souris corrompu"
    assert kmask == 0b101, "masque touches corrompu"
    print(f"[selftest] round-trip TCP OK : {recv.stats()}, image {g2.shape} preservee, "
          f"mdx={mdx}, mdy={mdy}, kmask={bin(kmask)}")

    stale = recv.get_latest(max_age_s=0.0)
    assert stale is None, "un cadre de latence >=0 devrait etre perime avec max_age_s=0.0"
    print("[selftest] peremption (max_age_s) OK")

    sock.close()
    recv.stop()


if __name__ == "__main__":
    _selftest()
