"""cmo_bridge — pont fichier Python(hote Linux+3090) <-> CMO(VM Windows), via dossier PARTAGE.
Meme principe que le pont Arma : CMO ecrit state.json (etat des unites), Python ecrit cmd_<N>.lua
(ordres en Lua, numerotes). Ecritures ATOMIQUES (tmp+rename) -> a travers le partage VM, CMO ne lit
jamais un fichier a moitie ecrit (lecon payee sur Arma)."""
import os, json, time, glob, re


class CMOBridge:
    def __init__(self, bridge_dir):
        self.dir = bridge_dir
        os.makedirs(self.dir, exist_ok=True)
        self.n_sent = self._max_cmd_on_disk()

    def _state_path(self):
        return os.path.join(self.dir, "state.json")

    def _max_cmd_on_disk(self):
        m = 0
        for f in glob.glob(os.path.join(self.dir, "cmd_*.lua")):
            mm = re.search(r"cmd_(\d+)\.lua$", f)
            if mm:
                m = max(m, int(mm.group(1)))
        return m

    def read_state(self, timeout=0.0):
        """Renvoie le dernier etat ecrit par CMO (dict) ou None. Tolere une lecture pendant l ecriture."""
        p = self._state_path()
        t0 = time.time()
        while True:
            try:
                with open(p, "r") as f:
                    return json.load(f)
            except (FileNotFoundError, ValueError):
                if time.time() - t0 >= timeout:
                    return None
                time.sleep(0.05)

    def last_executed(self):
        """Numero du dernier ordre que CMO a execute (champ n de state.json)."""
        st = self.read_state()
        return st.get("n", 0) if st else 0

    def send(self, lua_code, wait=True, timeout=10.0):
        """Ecrit un ordre Lua (numerote) que l actuateur CMO executera. Ecriture atomique."""
        self.n_sent += 1
        n = self.n_sent
        tmp = os.path.join(self.dir, ".cmd_%d.tmp" % n)
        dst = os.path.join(self.dir, "cmd_%d.lua" % n)
        with open(tmp, "w") as f:
            f.write(lua_code)
        os.replace(tmp, dst)                       # atomique -> CMO ne voit que le fichier complet
        if wait:
            t0 = time.time()
            while time.time() - t0 < timeout:
                if self.last_executed() >= n:
                    return True
                time.sleep(0.05)
            return False
        return True

    def units(self, side=None):
        """Raccourci : liste des unites du dernier etat, filtrable par camp."""
        st = self.read_state()
        if not st:
            return []
        us = st.get("units", [])
        return [u for u in us if side is None or u.get("side") == side]
