#!/usr/bin/env python3
"""endurance_guerre — une VRAIE guerre dans CMO pendant des heures ( demande de Younes, 29/09 : « tester des missions,
des camps, c'est ça une vraie endurance » ). La vraie horloge de guerre ( guerre/horloge.py ) mène CmoGuerre sur la carte
de Malden de la guerre Arma ( 21 zones Warlords ) ; l'économie est un archipel de papier ( recettes fixes, asymétriques ).

Ce qu'une vraie endurance exerce : deux camps hostiles, des achats, des patrouilles de défense aérienne de CMO qui
bougent avec les cibles, des combats, des morts rendues au moteur, des zones prises et reprises, des paiements, et CMO
qui tient la cadence.

CRITÈRES ÉCRITS D'AVANT ( verdict dans rapport_guerre.md ) :
  E1 aucun plantage hors pont ( une exception qui n'est pas une ErreurLabo arrête tout : c'est un bogue ) ;
  E2 chaque mort rendue une fois : morts reçues par le moteur = pertes comptées par CmoGuerre ;
  E3 chaque achat payé : dernier paiement du moteur = dépense de CmoGuerre, par île ;
  E4 CMO tient la cadence : temps du scénario / temps réel >= 0,9 en médiane ( 29/09 : des sondes l'avaient mis à 0,13 ) ;
  E5 LA GUERRE A EU LIEU : au moins une zone a changé de main ET au moins une mort au combat estimée ( un ennemi à moins
     de 40 km au dernier relevé ) — une « guerre » sans combat est un échec du banc, pas un succès ;
  E6 le pont ne meurt pas : pannes PontMort cumulées < 5 % de la durée.

Sorties : /mnt/data/hmt/etat/cmo_guerre/<début>/ ( journal.jsonl de l'horloge, suivi.jsonl, rapport_guerre.md ).
Arrêt propre : fichier STOP dans ce dossier, ou TERM / HUP / INT.

    .venv312/bin/python cmo/endurance_guerre.py [--heures 6] [--carte chemin/carte.json]
"""
import glob
import json
import math
import os
import signal
import statistics
import sys
import time
import traceback

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(ICI)
sys.path.insert(0, ICI)
sys.path.insert(0, DEPOT)
import cmo_labo as CL                                     # noqa: E402
import guerre_cmo as G                                    # noqa: E402
from archipel_papier import ArchipelDePapier              # noqa: E402
import endurance as E                                     # noqa: E402  ( journaux et mémoire de CMO )

DOSSIER = os.path.join(CL.ETAT, "cmo_guerre")
# Un avion ( 500 000 points ) toutes les 6 minutes pour Stratis, toutes les 7 pour Malden : points = 0,05 x recettes / 100.
RECETTES = {"Stratis": 1.67e8, "Malden": 1.43e8}
PERIODE_S, SUIVI_S, POINT_S = 60.0, 10.0, 600.0
RAYON_COMBAT_M = 40_000.0


class GuerreLongue:
    def __init__(self, heures, carte, *, dossier=None, labo_kw=None, periode_s=PERIODE_S, suivi_s=SUIVI_S,
                 point_s=POINT_S, recettes=RECETTES, logs=E.LOGS):
        from guerre.horloge import HorlogeDeGuerre
        self.dossier = dossier or os.path.join(DOSSIER, time.strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.dossier, exist_ok=True)
        self.duree, self.point_s, self.logs = 3600 * heures, point_s, logs
        self.carte = carte
        self.arc = ArchipelDePapier(recettes, pas_s=0.2)
        self.g = G.CmoGuerre(carte["zones"], labo_kw=labo_kw or {})
        self.h = HorlogeDeGuerre(self.arc, self.g, carte, periode_s=periode_s, dossier=self.dossier,
                                 periode_suivi_s=suivi_s)
        self.stop = False
        self.pannes, self.panne_depuis, self.erreurs = [], None, {}
        self.vitesses, self.rtt, self.flips, self.morts = [], [], 0, []
        self.dernier_temps = None                        # ( temps du scénario, temps réel ) au dernier tour
        self.dernieres_pos = {}                          # ( camp, numéro ) -> ( x, y )

    def noter(self, quoi, **d):
        with open(os.path.join(self.dossier, "suivi.jsonl"), "a") as g:
            g.write(json.dumps({"t": round(time.time() - self.t0, 1), "quoi": quoi, **d}, ensure_ascii=False) + "\n")

    def _panne(self, e, ou):
        k = type(e).__name__
        self.erreurs[k] = self.erreurs.get(k, 0) + 1
        self.noter("erreur", ou=ou, type=k, message=str(e)[:300])
        if isinstance(e, CL.PontMort) and self.panne_depuis is None:
            self.panne_depuis = time.time()

    def _reprise(self):
        if self.panne_depuis is not None:
            self.pannes.append(round(time.time() - self.panne_depuis, 1))
            self.noter("reprise", panne_s=self.pannes[-1])
            self.panne_depuis = None

    def _apres_tour(self, l):
        a = l["arma"]
        if a["temps"] is not None:
            if self.dernier_temps:
                d_scen, d_reel = a["temps"] - self.dernier_temps[0], time.time() - self.dernier_temps[1]
                if d_reel > 0:
                    self.vitesses.append(round(d_scen / d_reel, 3))
            self.dernier_temps = (a["temps"], time.time())
        if a.get("rtt_ms") is not None:
            self.rtt.append(a["rtt_ms"])
        self.flips += len(l["occupations"]["prises"]) + len(l["occupations"]["liberees"])

    def _apres_suivi(self, s):
        """Une mort est estimée « au combat » si un avion ennemi était à moins de RAYON_COMBAT_M au dernier relevé."""
        vivants, morts = self.g_dernier
        for camp, ks in morts.items():
            for k in ks:
                p = self.dernieres_pos.get((camp, k))
                ennemis = [xy for (c, _), xy in self.dernieres_pos.items() if c != camp]
                combat = bool(p) and any(math.hypot(p[0] - x, p[1] - y) <= RAYON_COMBAT_M for x, y in ennemis)
                self.morts.append({"camp": camp, "numero": k, "t": round(time.time() - self.t0), "combat": combat})
                self.noter("mort", camp=camp, numero=k, combat=combat)
                self.dernieres_pos.pop((camp, k), None)
        for camp, us in vivants.items():
            for k, x, y, _d in us:
                self.dernieres_pos[(camp, k)] = (x, y)

    def tourner(self):
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            signal.signal(sig, lambda *a: setattr(self, "stop", True))
        stop = os.path.join(self.dossier, "STOP")
        self.t0 = time.time()
        # positions() est appelée par l'horloge ; on la double pour garder une copie du relevé ( morts, positions )
        vraie_positions = self.g.positions

        def positions():
            r = vraie_positions()
            self.g_dernier = r
            return r
        self.g.positions = positions
        fin = self.t0 + self.duree
        while not self.g.ouvert and not self.stop and time.time() < fin:
            try:
                self.g.ouvrir()                          # attend le premier battement ( scénario rouvert en pause )
                self.h.ouvrir()
                self._reprise()
            except CL.ErreurLabo as e:
                self._panne(e, "ouvrir")
                time.sleep(10)
        self.noter("debut", carte=len(self.carte["zones"]), journaux=E.taille_journaux(self.logs), memoire=E.memoire_command())
        t_point = 0.0
        try:
            while not self.stop and time.time() < fin and not os.path.exists(stop):
                now = self.h.horloge()
                try:
                    if now >= self.h.prochain_suivi:
                        s = self.h.suivre_soldats()
                        self._apres_suivi(s)
                        self.h.prochain_suivi = max(self.h.prochain_suivi + self.h.periode_suivi, self.h.horloge())
                        self._reprise()
                    if now >= self.h.prochain:
                        self._apres_tour(self.h.tour())
                        self.h.prochain = max(self.h.prochain + self.h.periode, self.h.horloge() + 0.5 * self.h.periode)
                        self._reprise()
                    else:
                        self.arc.un_pas()
                except CL.ErreurLabo as e:               # une panne du pont se note et se retente ; un bogue, lui, arrête tout
                    self._panne(e, "tour")
                    time.sleep(10)
                if time.time() - t_point >= self.point_s:
                    t_point = time.time()
                    self.noter("point", journaux=E.taille_journaux(self.logs), memoire=E.memoire_command(),
                               vitesse=self.vitesses[-1] if self.vitesses else None, zones=self.g.proprio,
                               vivants={c: len(v) for c, v in self.g.en_vol.items()})
                    self.rapport()
        except Exception as e:                           # E1 : un plantage hors pont est un échec, noté puis relevé
            self.noter("plantage", type=type(e).__name__, message=str(e)[:500], trace=traceback.format_exc()[-2000:])
            self.plantage = f"{type(e).__name__}: {e}"
            raise
        finally:
            try:                                         # les morts vues au dernier tour vont au moteur ( E2 )
                self._apres_suivi(self.h.suivre_soldats())
            except CL.ErreurLabo as e:
                self._panne(e, "dernier relevé")
            self.noter("fin", journaux=E.taille_journaux(self.logs), memoire=E.memoire_command())
            self.rapport(final=True)
            self.g.fermer()
        return self.rapport(final=True)

    def verdict(self):
        g, arc = self.g, self.arc
        duree = max(1.0, time.time() - self.t0)
        pannes = sum(self.pannes) + (time.time() - self.panne_depuis if self.panne_depuis else 0.0)
        morts_moteur = sum(arc.morts.values())
        pertes = sum(g.pertes.values())
        payes = {ile: (arc.payes.get(ile) or [0.0])[-1] for ile in g.camps.values()}
        depenses = {g.camps[c]: g.depense[c] for c in g.camps}
        vit = statistics.median(self.vitesses) if self.vitesses else None
        combats = sum(1 for m in self.morts if m["combat"])
        return {
            "E1_pas_de_plantage": not getattr(self, "plantage", None),
            "E2_morts_une_fois": morts_moteur == pertes,
            "E3_achats_payes": all(abs(payes[i] - depenses[i]) < 1e-6 for i in payes),
            "E4_cadence": vit is not None and vit >= 0.9,
            "E5_la_guerre_a_eu_lieu": self.flips > 0 and combats > 0,
            "E6_pont_vivant": pannes / duree < 0.05,
            "_mesures": {"heures": round(duree / 3600, 2), "tours": self.h.tours, "achats": g.achats, "pertes": g.pertes,
                         "morts_moteur": morts_moteur, "morts_combat_estimees": combats, "changements_de_zone": self.flips,
                         "payes": payes, "depenses": depenses, "vitesse_mediane": vit,
                         "vitesse_min": min(self.vitesses) if self.vitesses else None,
                         "rtt_ms_mediane": statistics.median(self.rtt) if self.rtt else None,
                         "pannes_s": self.pannes, "erreurs": self.erreurs, "zones_finales": g.proprio},
        }

    def rapport(self, final=False):
        v = self.verdict()
        m = v["_mesures"]
        ok = all(x for k, x in v.items() if k.startswith("E"))
        l = [f"# Endurance de guerre CMO — {time.strftime('%Y-%m-%d %H:%M', time.localtime(self.t0))}, "
             f"{m['heures']} h ({'terminée' if final else 'EN COURS'}) : {'PASSE' if ok else 'ÉCHOUE' if final else '…'}", ""]
        for k, x in v.items():
            if k.startswith("E"):
                l.append(f"- {'✅' if x else '❌'} {k}")
        l += ["", "## Mesures", "```", json.dumps(m, ensure_ascii=False, indent=1), "```"]
        with open(os.path.join(self.dossier, "rapport_guerre.md"), "w") as g:
            g.write("\n".join(l) + "\n")
        return v


def carte_de_malden():
    """La carte de guerre de la dernière guerre Arma ( guerre/horloge.py la sauve dans son dossier )."""
    cartes = sorted(glob.glob("/mnt/data/hmt/guerre/*/carte.json"), key=os.path.getmtime)
    if not cartes:
        raise FileNotFoundError("aucune carte.json de guerre Arma : --carte chemin")
    return json.load(open(cartes[-1]))


if __name__ == "__main__":
    h = float(sys.argv[sys.argv.index("--heures") + 1]) if "--heures" in sys.argv else 6.0
    carte = json.load(open(sys.argv[sys.argv.index("--carte") + 1])) if "--carte" in sys.argv else carte_de_malden()
    v = GuerreLongue(h, carte).tourner()
    print(json.dumps(v, ensure_ascii=False, indent=1))
