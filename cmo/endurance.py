#!/usr/bin/env python3
"""endurance — le pont CMO sur une nuit : est-ce qu'il meurt en service ? ( le pont Arma mourait au bout de quelques
heures, cf. mémoire « pont-arma-meurt-en-service » ). Un banc de durée, pas le labo.

Deux F-15C en patrouille, tous deux au camp Stratis ( pas de combat entre eux ), entre deux points à l'ouest et à l'est
de Kéa ; un canari toutes les 30 s, les positions toutes les minutes, un point toutes les 10 min ( journaux de CMO,
mémoire du processus Command ). Un avion à court de carburant est une VRAIE mort de CMO : elle doit être rendue une
fois et une seule, puis un avion neuf est posé. Un PontMort ( jeu en pause, CMO fermé ) est noté avec sa durée ; la
nuit continue jusqu'au bout.

Sorties : /mnt/data/hmt/etat/cmo_nuit/<début>.jsonl ( un événement par ligne ) et resume.json, réécrit toutes les
10 min et à la fin.

    .venv/bin/python cmo/endurance.py [--heures 6]
"""
import json
import logging
import os
import signal
import statistics
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402

LOGS = os.path.join(CL.CMO, "Logs")
DOSSIER = os.path.join(CL.ETAT, "cmo_nuit")
POINTS = ((37.75, 23.95), (37.45, 24.60))                 # ouest et est de Kéa
DEPART = (37.60, 24.25)
F15C, LOADOUT, ALT = 3500, 16934, 6000
CANARI_S, POSITIONS_S, POINT_S, PATROUILLE_S = 30, 60, 600, 600
# Chemin complet : sous tmux, le PATH de WSL n'a pas les dossiers Windows ( 29/09 : mémoire à null ).
POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"


def taille_journaux(logs=LOGS):
    t = {}
    for nom in sorted(os.listdir(logs)) if os.path.isdir(logs) else []:
        if nom.startswith(("LuaHistory_", "ExceptionLog_")):
            t[nom] = os.path.getsize(os.path.join(logs, nom))
    return t


def memoire_command():
    """Octets de mémoire du processus Command de CMO ( interop WSL -> Windows ), ou None."""
    try:
        r = subprocess.run([POWERSHELL, "-NoProfile", "-Command",
                            "(Get-Process Command -ErrorAction SilentlyContinue).WorkingSet64"],
                           capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip().splitlines()[-1])
    except Exception:
        return None


class Nuit:
    def __init__(self, heures, *, labo_kw=None, intervalles=(CANARI_S, POSITIONS_S, POINT_S, PATROUILLE_S),
                 dossier=DOSSIER, logs=LOGS):
        self.labo_kw, self.intervalles, self.dossier, self.logs = labo_kw or {}, intervalles, dossier, logs
        os.makedirs(dossier, exist_ok=True)
        self.debut = time.time()
        self.fin = self.debut + 3600 * heures
        self.fichier = os.path.join(dossier, time.strftime("%Y%m%d_%H%M%S") + ".jsonl")
        self.rtt, self.erreurs, self.morts, self.vus_morts = [], {}, [], set()
        self.panne_depuis, self.pannes = None, []
        self.prochain_numero = 101
        self.volants = []                                 # numéros vivants posés par la nuit
        self.cible = 0
        self.stop = False

    def noter(self, quoi, **d):
        with open(self.fichier, "a") as g:
            g.write(json.dumps({"t": round(time.time() - self.debut, 1), "quoi": quoi, **d}, ensure_ascii=False) + "\n")

    def appel(self, nom, fn, *a):
        """Un appel du pont : rend le résultat, ou None après avoir noté l'erreur. Une panne ouvre une période."""
        try:
            r = fn(*a)
        except CL.ErreurLabo as e:
            k = type(e).__name__
            self.erreurs[k] = self.erreurs.get(k, 0) + 1
            self.noter("erreur", appel=nom, type=k, message=str(e)[:300])
            if isinstance(e, CL.PontMort) and self.panne_depuis is None:
                self.panne_depuis = time.time()
            return None
        if self.panne_depuis is not None:
            self.pannes.append(round(time.time() - self.panne_depuis, 1))
            self.noter("reprise", panne_s=self.pannes[-1])
            self.panne_depuis = None
        return r

    def poser(self, l):
        k = self.prochain_numero
        self.prochain_numero += 1
        if self.appel("poser", l.poser, "Stratis", "air", F15C, k, DEPART[0] + (k % 7) / 100, DEPART[1], ALT, LOADOUT):
            self.volants.append(k)
            self.noter("pose", numero=k)
            self.appel("aller", l.aller, k, *POINTS[self.cible])

    def relever(self, l):
        p = self.appel("positions", l.positions)
        if p is None:
            return
        for camp, ks in p["morts"].items():
            for k in ks:
                double = k in self.vus_morts
                self.vus_morts.add(k)
                self.morts.append({"numero": k, "t": round(time.time() - self.debut), "double": double})
                self.noter("mort", numero=k, camp=camp, double=double)
                if k in self.volants:
                    self.volants.remove(k)
        vivants = {u[0] for us in p["vivants"].values() for u in us}
        disparus = [k for k in self.volants if k not in vivants]
        if disparus:                                      # parti sans MORT : ce serait une perte du pont
            self.noter("disparu_sans_mort", numeros=disparus)
            for k in disparus:
                self.volants.remove(k)
        self.noter("positions", vivants=sorted(vivants))
        for _ in range(2 - len(self.volants)):          # borné : une pose qui échoue ne boucle pas
            self.poser(l)

    def resume(self, final=False):
        r = sorted(self.rtt)
        d = {"debut": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.debut)),
             "maintenant": time.strftime("%Y-%m-%d %H:%M:%S"), "final": final,
             "heures": round((time.time() - self.debut) / 3600, 2),
             "canaris_ok": len(r), "erreurs": self.erreurs,
             "rtt_ms": {"mediane": statistics.median(r) if r else None,
                        "p99": r[min(len(r) - 1, int(0.99 * len(r)))] if r else None, "max": r[-1] if r else None},
             "morts": self.morts, "morts_doubles": sum(m["double"] for m in self.morts),
             "pannes_s": self.pannes + ([round(time.time() - self.panne_depuis, 1)] if self.panne_depuis else []),
             "journal": self.fichier}
        with open(os.path.join(self.dossier, "resume.json"), "w") as g:
            json.dump(d, g, ensure_ascii=False, indent=1)
        return d

    def ouvrir(self, attente_s):
        """Attend le premier battement jusqu'à attente_s : un scénario rouvert démarre EN PAUSE dans CMO, et rien en Lua
        ne relance le temps sur la version Steam ( 29/09 ). La nuit compte à partir du premier battement."""
        limite = time.time() + attente_s
        while True:
            try:
                l = CL.Labo(**self.labo_kw).ouvrir()
                break
            except CL.PontMort as e:
                if time.time() > limite or self.stop:
                    raise
                self.noter("attente_battement", message=str(e)[:120])
                time.sleep(10)
        duree = self.fin - self.debut
        self.debut = time.time()
        self.fin = self.debut + duree
        return l

    def tourner(self, attente_s=1800):
        # TERM, HUP ( tmux kill-session ) et INT : la même sortie propre, table rase comprise ( 29/09 : un HUP sans
        # gestionnaire tuait la nuit sans nettoyer ).
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            signal.signal(sig, lambda *a: setattr(self, "stop", True))
        canari_s, positions_s, point_s, patrouille_s = self.intervalles
        l = self.ouvrir(attente_s)                       # strict : le build doit être certifié
        try:
            self.noter("debut", version=l.version, journaux=taille_journaux(self.logs), memoire=memoire_command())
            self.appel("nettoyer", l.nettoyer)
            t_canari = t_pos = t_point = t_patrouille = 0.0
            try:
                while not self.stop and time.time() < self.fin:
                    now = time.time()
                    if now - t_canari >= canari_s:
                        t_canari = now
                        c = self.appel("canari", l.canari)
                        if c:
                            self.rtt.append(c["recu"]["rtt_ms"])
                            self.noter("canari", rtt=c["recu"]["rtt_ms"], coeur=c["recu"]["coeur"],
                                       n=c["recu"]["n_cmd"], recalages=c["recu"]["recalages"],
                                       redemarrages=c["recu"]["redemarrages"])
                    if now - t_pos >= positions_s:
                        t_pos = now
                        self.relever(l)
                    if now - t_patrouille >= patrouille_s:
                        t_patrouille = now
                        self.cible = 1 - self.cible
                        for k in list(self.volants):
                            self.appel("aller", l.aller, k, *POINTS[self.cible])
                    if now - t_point >= point_s:
                        t_point = now
                        self.noter("point", journaux=taille_journaux(self.logs), memoire=memoire_command(),
                                   etat=(self.appel("etat", l.etat_camps) or {}).get("camps"))
                        self.resume()
                    time.sleep(min(1.0, canari_s / 3))
            finally:
                self.appel("nettoyer", l.nettoyer)
                self.noter("fin", journaux=taille_journaux(self.logs), memoire=memoire_command())
        finally:
            l.fermer()
        return self.resume(final=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    h = float(sys.argv[sys.argv.index("--heures") + 1]) if "--heures" in sys.argv else 6.0
    print(json.dumps(Nuit(h).tourner(), ensure_ascii=False, indent=1))
