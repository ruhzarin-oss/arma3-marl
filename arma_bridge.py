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
    def _last_recv(self, lines=None):
        lines = lines if lines is not None else self._log_lines()
        n = 0
        for ln in lines:
            if "HARMATTAN_ACTUATOR" in ln: n = 0
            m = re.search(r"HARMATTAN_RECV cmd (\d+)", ln)
            if m: n = int(m.group(1))
        return n
    def send(self, sqf, wait=True, timeout=14):
        lines = self._log_lines()
        want = 0
        for ln in lines:
            mw = re.search(r"cmd_(\d+)\.sqf not found", ln)
            if mw: want = int(mw.group(1))
        if want > 0:
            n = want
        else:
            n = self._last_recv(lines) + 1
            existing = [int(m.group(1)) for f in os.listdir(self.bridge) for m in [re.match(r"cmd_(\d+)\.sqf$", f)] if m]
            if existing: n = max(n, max(existing) + 1)
        with open(os.path.join(self.bridge, "cmd_%d.sqf" % n), "w") as f:
            f.write(sqf)
        if wait:
            t0 = time.time()
            while time.time() - t0 < timeout:
                if self._last_recv() >= n: return n
                time.sleep(0.2)
            try: os.remove(os.path.join(self.bridge, "cmd_%d.sqf" % n))   # pas de fichier orphelin -> pas de rejeu périmé ni d'inflation de numérotation
            except OSError: pass
            raise TimeoutError("cmd %d non recue (actuateur ?)" % n)
        return n
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
