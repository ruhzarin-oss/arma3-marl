"""Pont fichier Python <-> Arma 3 (sandbox Harmattan).
IN  : écrit cmd_N.sqf (N croissant, synchro sur le log) dans <MISSION>/hmt_bridge/ -> l'actuateur exécute.
OUT : lit les lignes HARMATTAN_* dans logs/server.out (le RPT)."""
import os, re, time

SANDBOX = "/mnt/data/harmattan-sandbox"
MISSION = os.environ.get("HMT_MISSION", SANDBOX + "/arma3server/mpmissions/HarmattanBridge.Altis")
BRIDGE  = os.environ.get("HMT_BRIDGE", MISSION + "/hmt_bridge")
LOG     = os.environ.get("HMT_LOG", SANDBOX + "/logs/server.out")

OBS_SQF = (
    'diag_log format ["HARMATTAN_OBS n=%1", count allUnits];\n'
    '{ private _p = getPosATL _x; diag_log format ["HARMATTAN_UNIT %1 %2 %3 %4 %5", '
    '_forEachIndex, round (_p select 0), round (_p select 1), (alive _x), (str side _x)]; } forEach allUnits;\n'
)

class ArmaBridge:
    def __init__(self, mission=None, log=None):
        self.bridge = (mission + "/hmt_bridge") if mission else BRIDGE
        self.log = log if log else LOG
        os.makedirs(self.bridge, exist_ok=True)
        self.counter = None      # numero de commande MONOTONE (synchro lazy sur l'actuateur) -> plus de course
    def _log_lines(self, n=4000):
        try:
            with open(self.log, "rb") as f:
                f.seek(0, 2); size = f.tell()
                back = min(size, 500000)
                f.seek(size - back)
                data = f.read().decode("utf-8", "ignore")
            return data.splitlines(keepends=True)[-n:]
        except FileNotFoundError:
            return []
    def _last_recv_big(self):
        """Init robuste du compteur : lit un GROS bloc (5 Mo) pour retrouver le dernier 'RECV cmd' malgre le
        spam 'cmd_N not found' (~5/s) qui sinon pousse le marqueur hors de la fenetre normale -> sync casse."""
        try:
            with open(self.log, "rb") as f:
                f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 5_000_000))
                data = f.read().decode("utf-8", "ignore")
            return self._last_recv(data.splitlines())
        except FileNotFoundError:
            return 0

    def _last_recv(self, lines=None):
        lines = lines if lines is not None else self._log_lines()
        n = 0
        for ln in lines:
            if "HARMATTAN_ACTUATOR" in ln: n = 0
            m = re.search(r"HARMATTAN_RECV cmd (\d+)", ln)
            if m: n = int(m.group(1))
        return n
    def send(self, sqf, wait=True, timeout=14):
        """Numerotation MONOTONE : compteur synchro lazy sur l'actuateur (_last_recv), puis +1 strict.
        Plus de devinette via le log -> plus de course entre 2 envois rapproches. Resync sur timeout."""
        if self.counter is None:
            self.counter = self._last_recv_big()             # position reelle de l'actuateur (gros bloc -> robuste au spam)
        n = self.counter + 1
        path = os.path.join(self.bridge, "cmd_%d.sqf" % n)
        with open(path, "w") as f:
            f.write(sqf)
        if not wait:
            self.counter = n; return n
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self._last_recv() >= n:
                self.counter = n; return n
            time.sleep(0.08)
        try: os.remove(path)
        except OSError: pass
        self.counter = self._last_recv()                     # resync sur l'etat reel (l'actuateur a pu repartir)
        raise TimeoutError("cmd %d non recue (resync counter=%d)" % (n, self.counter))
    def query(self, sqf, pattern, want=None, timeout=14, settle=0.05):
        """Lecture FIABLE : envoie sqf, puis POLL le log jusqu'a ce que les lignes 'pattern' (regex) ecrites
        APRES 'RECV cmd n' soient completes (>=want), borne par timeout. Corrélé a n => jamais perimé ni partiel.
        Renvoie la liste des re.Match. (Remplace le pari sleep+parse-unique.)"""
        n = self.send(sqf, wait=True, timeout=timeout)
        rx = re.compile(pattern); t0 = time.time(); last = []
        while time.time() - t0 < timeout:
            time.sleep(settle)
            lines = self._log_lines()
            idx = -1
            for i, ln in enumerate(lines):
                if ("HARMATTAN_RECV cmd %d" % n) in ln: idx = i      # derniere occurrence du marqueur de NOTRE cmd
            if idx >= 0:
                res = [m for ln in lines[idx + 1:] for m in [rx.search(ln)] if m]   # tous les matchs apres RECV n
                last = res
                if (want is None and res) or (want is not None and len(res) >= want):
                    return res[-want:] if want is not None else res  # les + recents (robuste a l'exec isolee/retard)
        return (last[-want:] if want is not None else last) if last else []

    def read_obs(self, timeout=6):
        n = self.send(OBS_SQF, wait=True, timeout=timeout)
        # laisse le temps aux lignes UNIT de s'écrire après le RECV
        time.sleep(0.6)
        lines = self._log_lines()
        # trouver le dernier "RECV cmd n" et parser les HARMATTAN_UNIT qui suivent
        idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln)
        units = []
        for ln in lines[idx:]:
            if "HARMATTAN_RECV cmd %d" % (n + 1) in ln: break
            m = re.search(r"HARMATTAN_UNIT (\d+) (-?\d+) (-?\d+) (\w+) (\w+)", ln)
            if m:
                units.append({"id": int(m.group(1)), "x": int(m.group(2)), "y": int(m.group(3)),
                              "alive": m.group(4) == "true", "side": m.group(5)})
        # dédoublonner par id (dernière occurrence)
        d = {}
        for u in units: d[u["id"]] = u
        return list(d.values())
