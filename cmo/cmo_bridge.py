"""cmo_bridge — cote Python du pont CMO (jumeau de arma_bridge). Lit /tmp/cmo_bridge/state.txt
ecrit par le Lua de CMO, parse les unites, envoie des commandes Lua via cmd.lua.
Interface volontairement proche d ArmaBridge pour reutiliser la logique de harnais plus tard."""
import os, time

BRIDGE = "/tmp/cmo_bridge"

class CmoBridge:
    def __init__(self, bridge=BRIDGE):
        self.bridge = bridge
        os.makedirs(bridge, exist_ok=True)

    def ping(self, timeout=30):
        """Attend le ping.txt ecrit par cmo_ping.lua -> prouve que le Lua de CMO ecrit des fichiers."""
        p = os.path.join(self.bridge, "ping.txt")
        if os.path.exists(p): os.remove(p)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if os.path.exists(p):
                return open(p).read().strip()
            time.sleep(0.3)
        return None

    def read_state(self):
        """Parse state.txt -> (t_sim, [unites]). Chaque unite : dict side/name/guid/lat/lon/hdg/spd/alt."""
        p = os.path.join(self.bridge, "state.txt")
        if not os.path.exists(p): return None, []
        t = None; units = []
        for ln in open(p):
            ln = ln.rstrip("\n")
            if ln.startswith("T "):
                t = float(ln[2:])
            elif ln.startswith("U "):
                f = ln[2:].split("|")
                if len(f) >= 8:
                    units.append(dict(side=f[0], name=f[1], guid=f[2],
                                      lat=float(f[3]), lon=float(f[4]),
                                      hdg=float(f[5]), spd=float(f[6]), alt=float(f[7])))
        return t, units

    def send(self, lua, wait_ack=True, timeout=10):
        """Ecrit cmd.lua (le pont CMO l execute au tick suivant) ; attend ack.txt si demande."""
        ack = os.path.join(self.bridge, "ack.txt")
        if os.path.exists(ack): os.remove(ack)
        with open(os.path.join(self.bridge, "cmd.lua"), "w") as f:
            f.write(lua)
        if wait_ack:
            t0 = time.time()
            while time.time() - t0 < timeout:
                if os.path.exists(ack): return True
                time.sleep(0.2)
            return False
        return True


if __name__ == "__main__":
    import sys
    b = CmoBridge()
    if len(sys.argv) > 1 and sys.argv[1] == "ping":
        print("attente du ping CMO (colle cmo_ping.lua dans la console Lua de CMO)...")
        r = b.ping(timeout=120)
        print("RESULTAT :", r if r else "AUCUN ping recu (timeout) -> io.open bloque ou pont KO")
    else:
        t, u = b.read_state()
        print("t_sim =", t, "| unites =", len(u))
        for x in u[:12]: print(" ", x["side"], x["name"], "(%.3f, %.3f)" % (x["lat"], x["lon"]))
