"""FauxCMO : le vrai Lua du pont ( lua/hmt_pont.lua, lua/installer.lua, déployés par deployer.py ) dans un Lua 5.4
( lupa, la version de lua54.dll de CMO ), face à un faux Command ( lua/faux_cmo.lua ). Un fil joue l'action de
l'événement que l'installateur a posé, toutes les `periode` s, comme le déclencheur RegularTime de CMO.

Il ne prouve que la plomberie et le Lua du pont. Ce que CMO fait vraiment ( ExportInst, RunScript, le bac à sable,
les unités ), seul le banc pontcmo le prouve."""
import json
import os
import threading
import time

from lupa import lua54

ICI = os.path.dirname(os.path.abspath(__file__))
import deployer                                           # noqa: E402


class FauxCMO:
    def __init__(self, racine, *, periode=0.05, build="1900.20", lecteur="loadfile", ecriture_lente=0.0,
                 tronquer=0):
        self.racine = racine
        self.periode, self.ecriture_lente, self.tronquer = periode, ecriture_lente, tronquer
        self.sortie = os.path.join(racine, "ImportExport")
        os.makedirs(self.sortie, exist_ok=True)
        self.pont = deployer.deployer(racine, racine.rstrip("/") + "/")
        self.verrou = threading.Lock()
        self.pause_ = False
        self.stop = False
        self.erreurs = []
        self.passages = 0
        self.L = lua54.LuaRuntime(unpack_returned_tuples=True)
        g = self.L.globals()
        g.PY_ecrire = self._ecrire
        g.FAUX_BASE = racine.rstrip("/") + "/"
        with open(os.path.join(ICI, "lua", "faux_cmo.lua"), encoding="utf-8") as f:
            self.L.execute(f.read())
        g.FAUX.build = build
        if lecteur == "runscript":
            self.L.execute("loadfile = nil")
        self.fil = threading.Thread(target=self._boucle, daemon=True)

    # ---- ce que CMO écrit : le JSON d'un .inst, texte dans Comments ( BOM compris, comme .NET )
    def _ecrire(self, nom, texte):
        if self.tronquer and nom.startswith("hmt_r_"):
            texte = texte[:self.tronquer]
        d = {"DB_ID": 0, "FormatVersion": 0, "MemberRecords": [], "ValidFrom": None, "ValidUntil": None,
             "Name": "HMT", "Comments": texte, "Template": False}
        octets = ("﻿" + json.dumps(d, indent=2, ensure_ascii=False)).encode("utf-8")
        with open(os.path.join(self.sortie, nom), "wb") as f:
            if self.ecriture_lente:
                f.write(octets[: len(octets) // 2])
                f.flush()
                time.sleep(self.ecriture_lente)
            f.write(octets[len(octets) // 2:] if self.ecriture_lente else octets)

    def _boucle(self):
        while not self.stop:
            if not self.pause_:
                try:
                    with self.verrou:
                        self.L.globals().FAUX_passer()
                        self.passages += 1
                except Exception as e:                    # HMT_tic ne doit jamais lever : c'est une faute du pont
                    self.erreurs.append(repr(e))
            time.sleep(self.periode)

    def lua(self, code):
        with self.verrou:
            return self.L.execute(code)

    def installer(self):
        return self.lua("return ScenEdit_RunScript('hmt_pont/installer.lua')")

    def demarrer(self):
        self.fil.start()
        return self

    def arreter(self):
        self.stop = True
        if self.fil.is_alive():
            self.fil.join(timeout=2)

    def pause(self): self.pause_ = True
    def reprendre(self): self.pause_ = False
    def recharger(self): self.lua("FAUX_recharger()")
    def detruire(self, numero): self.lua(f"FAUX_detruire({int(numero)})")
    def compter(self): return int(self.lua("return FAUX_compter()"))
    def regler(self, **kw):
        for k, v in kw.items():
            with self.verrou:
                self.L.globals().FAUX[k] = v
