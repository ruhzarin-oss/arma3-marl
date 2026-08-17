#!/usr/bin/env python3
"""native_bridge.py — client du pont NATIF C++ (hmt_native, TCP). DROP-IN pour ArmaBridge :
même interface (send / query / _log_lines), mais via socket TCP EN MÉMOIRE → plus de troncature
1024, plus de latence de fichier/RPT → pilote les 500 sans perte.

Protocole (côté hmt_native.c) :
  Python -> Arma : 'c|<n>|<sqf avec \\n encodés en \\x01>\\n'  (stocké en RAM, servi par poll 'p|<n>')
  Arma -> Python : les 'o|<ligne>' du SQF arrivent en clair '<ligne>\\n' sur le socket
  à la connexion : le C++ envoie 'HMT_SYNC <last_delivered>\\n' -> auto-sync du compteur

Usage : remplacer  ArmaBridge(mission=MIS, log=LOG)  par  NativeBridge(port=5816)  — le reste ne change pas."""
import socket, threading, time, re
from collections import deque


class NativeBridge:
    def __init__(self, host="127.0.0.1", port=5816, timeout=10):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(None)
        self.lines = deque(maxlen=50000)
        self.alive = True      # REVUE 17/08 : le pont sait desormais dire qu il est mort
        self.counter = 0
        self._buf = b""
        self._lock = threading.Lock()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        time.sleep(0.3)                                              # laisse arriver le HMT_SYNC

    def _read_loop(self):
        # REVUE 17/08 : ce thread mourait en SILENCE (3e client de pont du depot avec le
        # meme defaut). Apres sa mort, `query()` rend [] pour toujours et les appelants
        # ecrivent la panne dans la mesure comme un fait du monde.
        while True:
            try:
                data = self.sock.recv(65536)
            except Exception:
                self.alive = False; break
            if not data:
                self.alive = False; break
            self._buf += data
            while b"\n" in self._buf:
                raw, self._buf = self._buf.split(b"\n", 1)
                s = raw.decode("utf-8", "ignore")
                m = re.match(r"HMT_SYNC (\d+)", s)
                if m:
                    with self._lock:
                        self.counter = int(m.group(1))
                else:
                    with self._lock:
                        self.lines.append(s)

    def _log_lines(self, n=4000):
        with self._lock:
            return list(self.lines)[-n:]

    def _last_recv(self):
        n = 0
        for s in self._log_lines():
            if "HARMATTAN_ACTUATOR" in s:
                n = 0
            m = re.search(r"HARMATTAN_RECV cmd (\d+)", s)
            if m:
                n = int(m.group(1))
        return n

    def send(self, sqf, wait=True, timeout=14):
        with self._lock:
            self.counter += 1
            n = self.counter
        payload = ("c|%d|%s\n" % (n, sqf.replace("\n", "\x01"))).encode("utf-8")
        self.sock.sendall(payload)
        if not wait:
            return n
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self._last_recv() >= n:
                return n
            if not self.alive:
                raise ConnectionError("pont MORT pendant l attente de l ordre %d" % n)
            time.sleep(0.02)
        # REVUE 17/08 : on rendait `n` avec le commentaire « l actuateur rattrape ». Il ne
        # rattrape PAS : apres un rechargement de mission l actuateur repart de 1 pendant
        # que Python continue a 350, et l interblocage etait muet et documente comme normal.
        raise TimeoutError("ordre %d NON acquitte apres %.1f s (desync du compteur ?)" % (n, timeout))

    def query(self, sqf, pattern, want=1, timeout=14, settle=0.03):
        """Lecture FIABLE corrélée à la cmd n (comme ArmaBridge.query). Renvoie la liste des re.Match."""
        n = self.send(sqf, wait=True, timeout=timeout)
        rx = re.compile(pattern); t0 = time.time(); last = []
        while time.time() - t0 < timeout:
            time.sleep(settle)
            lines = self._log_lines()
            idx = -1
            for i, s in enumerate(lines):
                if ("HARMATTAN_RECV cmd %d" % n) in s:
                    idx = i
            if idx >= 0:
                res = [m for s in lines[idx + 1:] for m in [rx.search(s)] if m]
                last = res
                if (want is None and res) or (want is not None and len(res) >= want):
                    return res[-want:] if want is not None else res
        # REVUE 17/08 : `[]` signifiait A LA FOIS « Arma a repondu, rien ne correspond »
        # et « personne n a repondu ». Les appelants ecrivaient la panne dans la mesure.
        if not self.alive:
            raise ConnectionError("pont MORT pendant la requete (motif %r)" % pattern)
        return (last[-want:] if want is not None else last) if last else []

    def close(self):
        """Libère la ligne : le pont Arma n'accepte qu'un seul client actif à la fois.
        À appeler avant de lancer un autre script qui doit se connecter."""
        try:
            self.sock.shutdown(2)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass
