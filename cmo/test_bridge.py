"""test_bridge — TEST A BLANC du pont CMO sans CMO ni VM.
Un FAUX CMO (mock) simule ce que le Lua ecrira/lira dans le dossier partage :
 - il ecrit state.json (etat des unites),
 - il execute les cmd_<N>.lua en simulant l effet (deplace une unite),
 - il accuse reception (n = dernier ordre execute).
On verifie que CMOBridge (cote hote) lit l etat, envoie un ordre, et voit l accuse. Round-trip complet."""
import os, json, tempfile, sys
sys.path.insert(0, os.path.dirname(__file__))
from cmo_bridge import CMOBridge

class FakeCMO:
    """Imite l actuateur Lua : ecrit l etat, applique les ordres recus, accuse reception."""
    def __init__(self, d):
        self.d = d; self.n = 0; self.t = 0.0
        self.units = [{"side": "BLUE", "name": "Hornet 1", "lon": 10.0, "lat": 40.0, "hdg": 90, "spd": 400, "alt": 8000, "dmg": 0},
                      {"side": "RED",  "name": "SA-10 Site", "lon": 11.0, "lat": 40.5, "hdg": 0,  "spd": 0,   "alt": 0,    "dmg": 0}]
    def _write_state(self):
        tmp = os.path.join(self.d, "state.tmp")
        with open(tmp, "w") as f:
            json.dump({"t": self.t, "n": self.n, "units": self.units}, f)
        os.replace(tmp, os.path.join(self.d, "state.json"))
    def tick(self):
        """Un pas de sim : applique le prochain ordre s il existe (le Lua fait load(code)())."""
        self.t += 1.0
        nx = self.n + 1
        p = os.path.join(self.d, "cmd_%d.lua" % nx)
        if os.path.exists(p):
            code = open(p).read()
            # simulation de l effet : on reconnait un ordre "deplace Hornet 1 a (lon,lat)"
            import re
            m = re.search(r"MOVE Hornet 1 to ([\d.]+) ([\d.]+)", code)
            if m:
                self.units[0]["lon"] = float(m.group(1)); self.units[0]["lat"] = float(m.group(2))
            self.n = nx
        self._write_state()

def run():
    d = tempfile.mkdtemp(prefix="hmt_cmo_")
    cmo = FakeCMO(d); cmo._write_state()         # CMO publie l etat initial
    br = CMOBridge(d)

    # 1) l hote lit l etat
    st = br.read_state(); assert st is not None, "lecture etat KO"
    assert len(br.units("BLUE")) == 1 and br.units("BLUE")[0]["name"] == "Hornet 1", "unites KO"
    print("1. lecture etat OK : t=%.0f, %d unites (%s)" % (st["t"], len(st["units"]), ", ".join(u["name"] for u in st["units"])))

    # 2) l hote envoie un ordre Lua (non bloquant), le faux CMO fait un tick -> execute -> accuse
    ok = br.send("ScenEdit_SetUnit({name=Hornet 1, lon=10.5, lat=40.2}) -- MOVE Hornet 1 to 10.5 40.2", wait=False)
    assert os.path.exists(os.path.join(d, "cmd_1.lua")), "cmd_1.lua non ecrit"
    print("2. ordre #1 ecrit (cmd_1.lua) : envoi OK")
    cmo.tick()                                   # CMO execute l ordre + accuse (n=1)

    # 3) l hote voit l accuse et l effet
    assert br.last_executed() == 1, "accuse reception KO (n != 1)"
    h = br.units("BLUE")[0]
    assert abs(h["lon"] - 10.5) < 1e-6 and abs(h["lat"] - 40.2) < 1e-6, "effet de l ordre non applique"
    print("3. accuse n=1 + effet applique : Hornet 1 -> (%.1f, %.1f) OK" % (h["lon"], h["lat"]))

    # 4) ordre BLOQUANT : send(wait=True) doit rendre True des que CMO accuse (on simule le tick en parallele)
    import threading, time
    def cmo_loop():
        for _ in range(5): time.sleep(0.1); cmo.tick()
    threading.Thread(target=cmo_loop, daemon=True).start()
    ok = br.send("ScenEdit_SetUnit({name=Hornet 1, lon=9.9, lat=39.8}) -- MOVE Hornet 1 to 9.9 39.8", wait=True, timeout=5)
    assert ok, "send bloquant : pas d accuse dans le delai"
    h = br.units("BLUE")[0]
    print("4. ordre #2 BLOQUANT confirme (n=%d) + effet : Hornet 1 -> (%.1f, %.1f) OK" % (br.last_executed(), h["lon"], h["lat"]))

    print("\n===== PONT CMO : TEST A BLANC COMPLET PASSE (lecture etat + envoi ordre + accuse + effet) =====")
    import shutil; shutil.rmtree(d, ignore_errors=True)

run()
