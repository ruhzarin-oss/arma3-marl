#!/usr/bin/env python3
"""pont — la couture Arma <-> Python du harnais.

ALLER  : on ecrit C:\\hmt_bridge\\cmd_<N>.sqf, la DLL `hmt_ext` le lit au niveau OS.
RETOUR : diag_log -> RPT, suivi depuis WSL.
Latence certifiee le 30/08 : mediane 0,516 s, p99 0,566 s, 0 perte sur 100.

⚠️ L'actuateur consomme les commandes DANS L'ORDRE, cmd_(n+1) et rien d'autre. Partir
d'un autre numero fait attendre les deux cotes, et cette attente est indiscernable d'un
pont mort. On se cale donc sur `HMT_SYNC`, publie par la mission.

⚠️ Un episode dont le geste n'arrive pas est VOID : jamais compte, cause journalisee.
Un pont mort ne doit JAMAIS fabriquer un echec — c'est le mensonge le plus cher.
"""
import os, glob, time, re

PONT_DIR = "/mnt/c/hmt_bridge"

class Pont:
    def __init__(self, profil, patience_sync=25.0, pont_dir=PONT_DIR):
        # ⚠️ UN DOSSIER DE COMMANDES PAR INSTANCE. Deux harnais sur le meme dossier
        # se volent leurs cmd_N et s'effacent mutuellement au demarrage (le `os.remove`
        # ci-dessous). C'est ce qui a tue R2-bis le 30/08. Le defaut reste l'ancien
        # chemin pour ne rien casser de ce qui tourne.
        self.dir = pont_dir
        self.profil = profil
        self.rpt = self._dernier_rpt()
        if self.rpt is None:
            raise RuntimeError("aucun RPT : le serveur ne tourne pas")
        self.f = open(self.rpt, "r", errors="ignore")
        self.f.seek(0, os.SEEK_END)
        self.n = self._sync(patience_sync)
        for vieux in glob.glob(f"{self.dir}/cmd_*.sqf"):
            try: os.remove(vieux)
            except OSError: pass
        self.vivant = True

    def _dernier_rpt(self):
        fs = sorted(glob.glob(os.path.join(self.profil, "*.rpt")), key=os.path.getmtime)
        return fs[-1] if fs else None

    def _sync(self, patience):
        t0 = time.time()
        while time.time() - t0 < patience:
            l = self.f.readline()
            if not l:
                time.sleep(0.1); continue
            m = re.search(r"HMT_SYNC (\d+)", l)
            if m:
                return int(m.group(1))
        raise RuntimeError("HMT_SYNC absent : la mission ne publie pas son compteur")

    def envoyer(self, sqf):
        self.n += 1
        tmp = f"{self.dir}/.tmp_{self.n}"
        with open(tmp, "w") as g:
            g.write(sqf if sqf.endswith("\n") else sqf + "\n")
        os.replace(tmp, f"{self.dir}/cmd_{self.n}.sqf")   # atomique

    def lignes(self, motif, patience):
        """Rend les lignes contenant `motif`, jusqu'a `patience` secondes. Generateur."""
        t0 = time.time()
        while time.time() - t0 < patience:
            l = self.f.readline()
            if not l:
                time.sleep(0.02); continue
            if motif in l:
                yield l.rstrip("\n")

    def attendre(self, motif, patience):
        for l in self.lignes(motif, patience):
            return l
        return None

    def fermer(self):
        try: self.f.close()
        except Exception: pass
