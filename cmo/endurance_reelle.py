#!/usr/bin/env python3
"""endurance_reelle — la guerre réelle ( guerre_reelle.py ) dans le VRAI CMO pendant des heures : le théâtre est construit
au départ dans le scénario ouvert ( qui doit être PROPRE : rechargé, sans tables rases passées ), puis la guerre tourne.

CRITÈRES ÉCRITS D'AVANCE ( rapport_reelle.md ) :
  R1 aucun plantage hors pont ;
  R2 CMO tient la cadence : temps du scénario / temps réel >= 0,9 en médiane ;
  R3 le pont ne meurt pas : pannes cumulées < 5 % de la durée ;
  R4 LA GUERRE DÉTRUIT : chaque camp a perdu au moins un élément d'installation ( piste, accès, dépôt… ) sous les coups de
     l'autre ( journal de CMO ) ;
  R5 LES AVIONS SE RÉARMENT : chaque camp tire encore des munitions après la deuxième heure ( compte de CMO ) — la guerre
     du 29/09 s'était figée faute de munitions en dépôt ;
  R6 l'argent se conserve : versé = dépensé + en caisse, pour chaque pays ;
  R7 chaque avion perdu compté une fois : pertes d'avions du moteur = pertes d'avions comptées par CMO, par camp.

Sorties : /mnt/data/hmt/etat/cmo_reelle/<début>/ ( tours.jsonl, rapport_reelle.md ). Arrêt : fichier STOP, TERM / HUP / INT.

    .venv312/bin/python cmo/endurance_reelle.py [--heures 6] [--theatre baltique_reel]
"""
import json
import os
import signal
import statistics
import sys
import time
import traceback

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import guerre_reelle as GR                                # noqa: E402

DOSSIER = os.path.join(CL.ETAT, "cmo_reelle")


class EnduranceReelle:
    def __init__(self, heures, theatre="baltique_reel", *, dossier=None, periode_s=60.0, guerre_kw=None, labo_kw=None,
                 reprendre=None, completer=False):
        self.dossier = dossier or os.path.join(DOSSIER, time.strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.dossier, exist_ok=True)
        self.duree, self.theatre, self.periode = 3600 * heures, theatre, periode_s
        self.guerre_kw, self.labo_kw = guerre_kw or {}, labo_kw or {}
        self.g, self.stop, self.plantage = None, False, None
        self.pannes, self.panne_depuis, self.erreurs = [], None, {}
        self.vitesses, self.rtt, self.dernier_temps = [], [], None
        self.tirs = []                                   # ( secondes, { camp : munitions tirées } )
        self.reprendre = reprendre                       # dossier d'une endurance précédente : son theatre.json
        self.completer = completer                       # ajouter ce que la construction n'avait pas posé

    def noter(self, quoi, **d):
        with open(os.path.join(self.dossier, "tours.jsonl"), "a") as g:
            g.write(json.dumps({"t": round(time.time() - self.t0, 1), "quoi": quoi, **d}, ensure_ascii=False, default=str) + "\n")

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

    def tourner(self):
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            signal.signal(sig, lambda *a: setattr(self, "stop", True))
        self.t0 = time.time()
        fin, stop = self.t0 + self.duree, os.path.join(self.dossier, "STOP")
        try:
            self.g = GR.GuerreReelle(self.theatre, periode_min=self.periode / 60.0, labo_kw=dict(
                {"patience": 60.0, "battement_max": 30.0, "patience_ouverture": 120.0}, **self.labo_kw), **self.guerre_kw)
            t = time.monotonic()
            if self.reprendre:                           # même scénario, unités HMT déjà là : on ne reconstruit rien
                self.g.ouvrir()
                with open(os.path.join(self.reprendre, "theatre.json")) as h:
                    self.g.charger(json.load(h))
                # un journal NEUF : après un redémarrage de CMO, l'ancien chemin n'est plus celui où CMO écrit ( 02/10 )
                self.g.journal = self.g.labo.journal_messages(int(time.strftime("%Y%m%d%H%M%S")) % 10 ** 12)
                self.g.journal_pos = 0
                if self.completer:
                    self.noter("complete", **self.g.completer())
            else:
                self.g.ouvrir(journal_id=int(time.strftime("%Y%m%d%H%M%S")) % 10 ** 12)
                self.g.construire()
            self._sauver()
            self.pertes_cmo_debut = self._pertes_cmo()       # CMO compte depuis la création du scénario : on part d'ici
            self.noter("construit", s=round(time.monotonic() - t), bases=len(self.g.bases), avions=len(self.g.avions),
                       sol=len(self.g.sol), elements=len(self.g.elements), journal=self.g.journal,
                       stock_initial_m={p: round(v) for p, v in self.g.stock_initial_m.items() if v},
                       refus=self.g.refus_construction, repris_de=self.reprendre)
            prochain = time.time()
            while not self.stop and time.time() < fin and not os.path.exists(stop):
                if time.time() < prochain:
                    time.sleep(0.5)
                    continue
                prochain = max(prochain + self.periode, time.time() + 0.5 * self.periode)
                try:
                    r = self.g.tour()
                    self._reprise()
                except CL.ErreurLabo as e:
                    self._panne(e, "tour")
                    continue
                if r["temps"] is not None:
                    if self.dernier_temps and time.time() > self.dernier_temps[1]:
                        self.vitesses.append(round((r["temps"] - self.dernier_temps[0]) / (time.time() - self.dernier_temps[1]), 3))
                    self.dernier_temps = (r["temps"], time.time())
                self.rtt.append(r["rtt_ms"])
                tirs = {c: (r["camps"][c]["bilan"] or {}).get("munitions_tirees", 0) for c in self.g.camps}
                self.tirs.append((round(time.time() - self.t0), tirs))
                self.noter("tour", **{k: r[k] for k in ("tour", "morts", "detruits", "achats", "munitions", "camps")},
                           vitesse=self.vitesses[-1] if self.vitesses else None)
                self._sauver()                           # à CHAQUE tour : une reprise ne perd aucun mort déjà relevé
                if r["tour"] % 10 == 0:
                    self.rapport()
        except Exception as e:                           # R1 : un plantage hors pont est un échec, noté puis relevé
            self.plantage = f"{type(e).__name__}: {e}"
            self.noter("plantage", message=self.plantage[:500], trace=traceback.format_exc()[-2000:])
            raise
        finally:
            v = self.rapport(final=True)
            if self.g is not None:
                self.g.fermer()
        return v

    def _sauver(self):
        tmp = os.path.join(self.dossier, ".theatre.json.tmp")
        with open(tmp, "w") as h:
            json.dump(self.g.etat(), h, ensure_ascii=False, default=str)
        os.replace(tmp, os.path.join(self.dossier, "theatre.json"))

    def _pertes_cmo(self):
        return {c: sum(n for (t, _), n in self.g.labo.bilan(c)["pertes"].items() if t == "avion") for c in self.g.camps}

    def verdict(self):
        duree = max(1.0, time.time() - self.t0)
        pannes = sum(self.pannes) + (time.time() - self.panne_depuis if self.panne_depuis else 0.0)
        g = self.g
        vit = statistics.median(self.vitesses) if self.vitesses else None
        perdus = {c: sum(1 for d in (g.detruits if g else []) if d["camp"] == c) for c in (g.camps if g else ())}
        apres_2h = [x for x in self.tirs if x[0] >= 7200]
        avant = next((x[1] for x in self.tirs if x[0] >= 7200), None)
        tire_apres = {c: bool(apres_2h) and avant is not None and apres_2h[-1][1][c] > avant[c] for c in (g.camps if g else ())}
        pertes_moteur = {c: sum(1 for m in (g.morts if g else []) if m["genre"] == "avion" and g.camp_de_pays(m["pays"]) == c)
                         for c in (g.camps if g else ())}
        pertes_cmo = {}
        if g and g.labo is not None and getattr(self, "pertes_cmo_debut", None) is not None:
            try:
                fin = self._pertes_cmo()
                pertes_cmo = {c: fin[c] - self.pertes_cmo_debut.get(c, 0) for c in g.camps}
            except CL.ErreurLabo:
                pertes_cmo = {}
        return {"R1_pas_de_plantage": not self.plantage, "R2_cadence": vit is not None and vit >= 0.9,
                "R3_pont_vivant": pannes / duree < 0.05, "R4_la_guerre_detruit": bool(perdus) and all(perdus.values()),
                "R5_les_avions_se_rearment": bool(tire_apres) and all(tire_apres.values()),
                "R6_argent_conserve": bool(g) and all(abs(g.verse[p] - g.depense[p] - g.caisse[p]) < 1e-6 for p in g.pays),
                "R7_pertes_comptees_une_fois": bool(pertes_cmo) and pertes_cmo == pertes_moteur,
                "_mesures": {"heures": round(duree / 3600, 2), "vitesse_mediane": vit,
                             "vitesse_min": min(self.vitesses) if self.vitesses else None,
                             "rtt_ms_mediane": statistics.median(self.rtt) if self.rtt else None,
                             "pannes_s": self.pannes, "erreurs": self.erreurs, "plantage": self.plantage,
                             "elements_perdus": perdus, "tire_apres_2h": tire_apres,
                             "pertes_avions_moteur": pertes_moteur, "pertes_avions_cmo": pertes_cmo,
                             "camps": {c: g.resume(c) for c in g.camps} if g else None,
                             "achats": g.achats if g else None, "packs_achetes": g.packs_achetes if g else None,
                             "depense_m": {p: round(v) for p, v in g.depense.items() if v} if g else None,
                             "stock_initial_m": {p: round(v) for p, v in g.stock_initial_m.items() if v} if g else None}}

    def rapport(self, final=False):
        v = self.verdict()
        ok = all(x for k, x in v.items() if k.startswith("R"))
        l = [f"# Guerre réelle ( {self.theatre} ) — {time.strftime('%Y-%m-%d %H:%M', time.localtime(self.t0))}, "
             f"{v['_mesures']['heures']} h ({'terminée' if final else 'EN COURS'}) : {'PASSE' if ok else 'ÉCHOUE' if final else '…'}", ""]
        l += [f"- {'✅' if x else '❌'} {k}" for k, x in v.items() if k.startswith("R")]
        l += ["", "## Mesures", "```", json.dumps(v["_mesures"], ensure_ascii=False, indent=1, default=str), "```"]
        with open(os.path.join(self.dossier, "rapport_reelle.md"), "w") as g:
            g.write("\n".join(l) + "\n")
        return v


if __name__ == "__main__":
    h = float(sys.argv[sys.argv.index("--heures") + 1]) if "--heures" in sys.argv else 6.0
    th = sys.argv[sys.argv.index("--theatre") + 1] if "--theatre" in sys.argv else "baltique_reel"
    rep = sys.argv[sys.argv.index("--reprendre") + 1] if "--reprendre" in sys.argv else None
    print(json.dumps(EnduranceReelle(h, th, reprendre=rep, completer="--completer" in sys.argv).tourner(),
                     ensure_ascii=False, indent=1, default=str))
