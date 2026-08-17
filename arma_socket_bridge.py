"""arma_socket_bridge — pont TCP natif Python <-> serveur Arma dedie (via hmt_native_x64.so).
Interface IDENTIQUE a ArmaBridge (send / _log_lines / _last_recv) -> drop-in pour OpArma.
IN  : "c|<n>|<sqf \n->\x01>\n" vers l extension (RAM, plus de cmd_N.sqf).
OUT : lignes TCP poussees par le SQF via callExtension "o|..." (plus de parsing de RPT 500 Ko).
Transformation transparente : les diag_log des requetes sont reecrits en callExtension "o|"."""
import re, time, socket, threading, collections


def to_socket_out(sqf):
    """Reecrit `diag_log format [...]` et `diag_log "..."` en emissions socket "o|..." (respecte
    l imbrication de crochets et l echappement SQF "" dans les chaines)."""
    out = []; i = 0
    while True:
        j = sqf.find("diag_log", i)
        if j < 0:
            out.append(sqf[i:]); break
        out.append(sqf[i:j])
        k = j + len("diag_log")
        while k < len(sqf) and sqf[k] in " \t": k += 1
        if sqf.startswith("format", k):
            k2 = k + 6
            while k2 < len(sqf) and sqf[k2] in " \t": k2 += 1
            if k2 < len(sqf) and sqf[k2] == "[":
                depth = 0; m = k2
                while m < len(sqf):
                    ch = sqf[m]
                    if ch == "\"":
                        m += 1
                        while m < len(sqf):
                            if sqf[m] == "\"":
                                if m + 1 < len(sqf) and sqf[m + 1] == "\"": m += 2; continue
                                break
                            m += 1
                    elif ch == "[": depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0: break
                    m += 1
                out.append("\"hmt_native\" callExtension (\"o|\" + (format %s))" % sqf[k2:m + 1])
                i = m + 1; continue
        if k < len(sqf) and sqf[k] == "\"":
            m = k + 1
            while m < len(sqf):
                if sqf[m] == "\"":
                    if m + 1 < len(sqf) and sqf[m + 1] == "\"": m += 2; continue
                    break
                m += 1
            out.append("\"hmt_native\" callExtension (\"o|\" + %s)" % sqf[k:m + 1])
            i = m + 1; continue
        # REVUE 17/08 : toute forme autre que `diag_log format [...]` et `diag_log "..."`
        # tombait ici et RESTAIT un diag_log — elle partait donc au RPT, que la voie native
        # ne lit plus par construction (cf. docstring). Or le socle journalise par
        # `HMT_LOG = { diag_log _this }` : ces lignes de mesure etaient perdues en silence.
        # On reecrit aussi la forme generique `diag_log <expr>;`, uniquement quand l expr
        # est simple (pas de bloc, pas de tableau, pas de chaine) — sinon on laisse.
        _fin = sqf.find(";", k)
        _seg = sqf[k:_fin].strip() if _fin > k else ""
        if _seg and not any(ch in _seg for ch in "{}[]\""):
            out.append("\"hmt_native\" callExtension (\"o|\" + str (%s))" % _seg)
            i = _fin; continue
        out.append(sqf[j:k]); i = k
    return "".join(out)


class SocketBridge:
    def __init__(self, port, host="127.0.0.1", connect_timeout=30):
        self.lines = collections.deque(maxlen=60000)
        self.alive = True      # REVUE 17/08 : le pont sait desormais dire qu il est mort
        self.n = 0; self._buf = b""
        deadline = time.time() + connect_timeout
        while True:
            try:
                self.sock = socket.create_connection((host, port), timeout=5); break
            except OSError:
                if time.time() > deadline: raise
                time.sleep(0.5)
        self.sock.settimeout(None)
        threading.Thread(target=self._reader, daemon=True).start()
        t0 = time.time()
        while time.time() - t0 < 5:                      # HMT_SYNC <n> = reprise propre inter-ops
            for ln in list(self.lines):
                m = re.match(r"HMT_SYNC (\d+)", ln)
                if m:
                    self.n = int(m.group(1)); return
            time.sleep(0.05)

    def _reader(self):
        # REVUE 17/08 : ce thread mourait en SILENCE. Apres sa mort `self.lines` cesse de
        # grandir et toute lecture rend un tampon FIGE, sans que rien ne le signale.
        while True:
            try:
                data = self.sock.recv(65536)
            except OSError:
                self.alive = False; return
            if not data:
                self.alive = False; return
            self._buf += data
            while b"\n" in self._buf:
                ln, self._buf = self._buf.split(b"\n", 1)
                self.lines.append(ln.decode("utf-8", "ignore"))

    def _log_lines(self, n=4000):
        return list(self.lines)[-n:]

    def _last_recv(self, lines=None):
        lines = lines if lines is not None else self._log_lines()
        n = 0
        for ln in lines:
            m = re.search(r"HARMATTAN_RECV cmd (\d+)", ln)
            if m: n = int(m.group(1))
        return max(n, self.n)

    def send(self, sqf, wait=True, timeout=14):
        self.n += 1; n = self.n
        payload = to_socket_out(sqf).replace("\n", "\x01")
        self.sock.sendall(("c|%d|" % n).encode() + payload.encode() + b"\n")
        if wait:
            pat = "HARMATTAN_RECV cmd %d" % n; t0 = time.time()
            while time.time() - t0 < timeout:
                if any(pat in ln for ln in list(self.lines)[-2000:]): return n
                if not self.alive:
                    raise ConnectionError("pont MORT pendant l attente de l ordre %d" % n)
                time.sleep(0.02)
            # REVUE 17/08 : le timeout rendait `n` comme un succes — un ordre JAMAIS
            # execute etait indiscernable d un ordre acquitte. « mieux vaut un arret
            # qu un chiffre invente » (assault_terrain.py:86).
            raise TimeoutError("ordre %d NON acquitte apres %.1f s" % (n, timeout))
        return n
