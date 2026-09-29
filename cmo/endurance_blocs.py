#!/usr/bin/env python3
"""endurance_blocs — la guerre des blocs ( guerre_blocs.py ) dans le VRAI CMO pendant des heures : OTAN contre Russie-Chine
sur un théâtre, pays par pays, en capture de drapeaux. Une victoire ( QG pris ) clôt une MANCHE : table rase, nouvelle
manche, jusqu'à la fin de la durée.

CRITÈRES ÉCRITS D'AVANCE ( rapport_blocs.md ) :
  B1 aucun plantage hors pont ;
  B2 chaque mort rendue une fois : pertes comptées = avions HMT détruits selon le journal de CMO, par manche ;
  B3 l'argent se conserve : versé = dépensé + en caisse, pour chaque pays, au centime ;
  B4 CMO tient la cadence : temps du scénario / temps réel >= 0,9 en médiane ;
  B5 LA GUERRE A EU LIEU : au moins un drapeau a changé de main ET au moins un avion ABATTU selon le journal de CMO ;
  B6 le pont ne meurt pas : pannes cumulées < 5 % de la durée ;
  B7 LES BASES SERVENT : les pertes à sec restent sous 10 % des pertes ( 29/09 : 37 des 48 pertes de Malden sans base ).

Sorties : /mnt/data/hmt/etat/cmo_blocs/<début>/ ( tours.jsonl, rapport_blocs.md ). Arrêt : fichier STOP, ou TERM / HUP / INT.

    .venv312/bin/python cmo/endurance_blocs.py [--heures 6] [--theatre baltique]
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
import guerre_blocs as GB                                 # noqa: E402
import causes_cmo                                         # noqa: E402
import endurance as E                                     # noqa: E402

DOSSIER = os.path.join(CL.ETAT, "cmo_blocs")


class EnduranceBlocs:
    def __init__(self, heures, theatre="baltique", *, dossier=None, labo_kw=None, periode_s=60.0, catalogue=None,
                 logs=E.LOGS, guerre_kw=None):
        self.dossier = dossier or os.path.join(DOSSIER, time.strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.dossier, exist_ok=True)
        self.duree, self.theatre, self.periode, self.logs = 3600 * heures, theatre, periode_s, logs
        self.labo_kw, self.catalogue, self.guerre_kw = labo_kw or {}, catalogue, guerre_kw or {}
        self.manches, self.g = [], None
        self.stop, self.plantage = False, None
        self.pannes, self.panne_depuis, self.erreurs = [], None, {}
        self.vitesses, self.rtt, self.dernier_temps = [], [], None

    def noter(self, quoi, **d):
        with open(os.path.join(self.dossier, "tours.jsonl"), "a") as g:
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

    def _nouvelle_manche(self):
        labo = self.g.labo if self.g else getattr(self, "labo", None)   # un seul pont pour toute l'endurance : un second
        # serait refusé ( écrivain unique, verrou déjà tenu par ce processus )
        self.g = GB.GuerreBlocs(self.theatre, labo=labo, labo_kw=self.labo_kw, catalogue=self.catalogue,
                                periode_min=self.periode / 60.0, **self.guerre_kw)
        if labo is None:
            self.g.labo = CL.Labo(camps=self.g.camps, **self.labo_kw).ouvrir()
            self.labo = self.g.labo
        self.g.possede = False
        self.g.ouvrir(journal_id=int(time.strftime("%Y%m%d%H%M%S")) % 10 ** 12)
        self.manches.append(self.g)
        self.noter("manche", numero=len(self.manches), journal=self.g.journal,
                   catalogue={p: [x["famille"] for x in c] for p, c in self.g.cat.items() if c})

    def tourner(self):
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            signal.signal(sig, lambda *a: setattr(self, "stop", True))
        self.t0 = time.time()
        fin, stop = self.t0 + self.duree, os.path.join(self.dossier, "STOP")
        while self.g is None and not self.stop and time.time() < fin:
            try:
                self._nouvelle_manche()                  # attend le premier battement ( scénario rouvert en pause )
                self._reprise()
            except CL.ErreurLabo as e:
                self.g = None
                self._panne(e, "ouvrir")
                time.sleep(10)
        self.noter("debut", journaux=E.taille_journaux(self.logs), memoire=E.memoire_command())
        prochain, t_point = time.time(), 0.0
        try:
            while not self.stop and time.time() < fin and not os.path.exists(stop):
                if time.time() < prochain:
                    time.sleep(0.5)
                    continue
                prochain = max(prochain + self.periode, time.time() + 0.5 * self.periode)
                try:
                    t = self.g.tour()
                    self._reprise()
                except CL.ErreurLabo as e:
                    self._panne(e, "tour")
                    continue
                if t["temps"] is not None:
                    if self.dernier_temps and time.time() > self.dernier_temps[1]:
                        self.vitesses.append(round((t["temps"] - self.dernier_temps[0]) / (time.time() - self.dernier_temps[1]), 3))
                    self.dernier_temps = (t["temps"], time.time())
                self.rtt.append(t["rtt_ms"])
                self.noter("tour", manche=len(self.manches), **{k: t[k] for k in ("tour", "flips", "victoire", "camps")},
                           achats=len(t["achats"]), morts=len(t["morts"]))
                if time.time() - t_point >= 600:
                    t_point = time.time()
                    self.noter("point", journaux=E.taille_journaux(self.logs), memoire=E.memoire_command(),
                               vitesse=self.vitesses[-1] if self.vitesses else None)
                    self.rapport()
                if t["victoire"]:
                    self.noter("victoire", manche=len(self.manches), camp=t["victoire"], tour=t["tour"])
                    try:
                        self._nouvelle_manche()
                    except CL.ErreurLabo as e:
                        self._panne(e, "nouvelle manche")
        except Exception as e:                           # B1 : un plantage hors pont est un échec, noté puis relevé
            self.plantage = f"{type(e).__name__}: {e}"
            self.noter("plantage", message=self.plantage[:500], trace=traceback.format_exc()[-2000:])
            raise
        finally:
            self.noter("fin", journaux=E.taille_journaux(self.logs), memoire=E.memoire_command())
            v = self.rapport(final=True)
            if getattr(self, "labo", None):
                self.labo.fermer()
        return v

    def _causes(self, g):
        """{ pays : { combat, carburant, autre } } lus dans le journal de CMO de la manche."""
        out = {}
        try:
            c, _ = causes_cmo.causes(open(g.journal, errors="ignore").read()) if g.journal else ({}, {})
        except OSError:
            return None
        for k, cause in c.items():
            p = g.pays_de(k)
            if p:
                out.setdefault(p, {}).setdefault(cause, 0)
                out[p][cause] += 1
        return out

    def verdict(self):
        duree = max(1.0, time.time() - self.t0)
        pannes = sum(self.pannes) + (time.time() - self.panne_depuis if self.panne_depuis else 0.0)
        manches, b2, b3, abattus, sec, total, flips = [], True, True, 0, 0, 0, 0
        for i, g in enumerate(self.manches, 1):
            cz = self._causes(g) or {}
            n_cmo = sum(sum(v.values()) for v in cz.values())
            n_pertes = sum(g.pertes.values())
            b2 &= n_cmo == n_pertes
            b3 &= all(abs(g.verse[p] - g.depense[p] - g.caisse[p]) < 1e-6 for p in g.pays)
            abattus += sum(v.get("combat", 0) for v in cz.values())
            sec += sum(v.get("carburant", 0) for v in cz.values())
            total += n_cmo
            flips += len(g.flips)
            manches.append({"manche": i, "tours": g.tours, "victoire": g.victoire, "score": g.score,
                            "achats": {p: n for p, n in g.achats.items() if n}, "pertes_cmo": cz,
                            "pertes_comptees": {p: n for p, n in g.pertes.items() if n}, "drapeaux_pris": len(g.flips),
                            "depense_m": {p: round(v) for p, v in g.depense.items() if v}})
        vit = statistics.median(self.vitesses) if self.vitesses else None
        return {"B1_pas_de_plantage": not self.plantage, "B2_morts_une_fois": b2, "B3_argent_conserve": b3,
                "B4_cadence": vit is not None and vit >= 0.9, "B5_la_guerre_a_eu_lieu": flips > 0 and abattus > 0,
                "B6_pont_vivant": pannes / duree < 0.05, "B7_les_bases_servent": total == 0 or sec / total < 0.10,
                "_mesures": {"heures": round(duree / 3600, 2), "manches": manches, "vitesse_mediane": vit,
                             "vitesse_min": min(self.vitesses) if self.vitesses else None,
                             "rtt_ms_mediane": statistics.median(self.rtt) if self.rtt else None,
                             "pannes_s": self.pannes, "erreurs": self.erreurs, "plantage": self.plantage}}

    def rapport(self, final=False):
        v = self.verdict()
        ok = all(x for k, x in v.items() if k.startswith("B"))
        l = [f"# Guerre des blocs ( {self.theatre} ) — {time.strftime('%Y-%m-%d %H:%M', time.localtime(self.t0))}, "
             f"{v['_mesures']['heures']} h ({'terminée' if final else 'EN COURS'}) : {'PASSE' if ok else 'ÉCHOUE' if final else '…'}", ""]
        l += [f"- {'✅' if x else '❌'} {k}" for k, x in v.items() if k.startswith("B")]
        l += ["", "## Mesures", "```", json.dumps(v["_mesures"], ensure_ascii=False, indent=1), "```"]
        with open(os.path.join(self.dossier, "rapport_blocs.md"), "w") as g:
            g.write("\n".join(l) + "\n")
        return v


if __name__ == "__main__":
    h = float(sys.argv[sys.argv.index("--heures") + 1]) if "--heures" in sys.argv else 6.0
    th = sys.argv[sys.argv.index("--theatre") + 1] if "--theatre" in sys.argv else "baltique"
    print(json.dumps(EnduranceBlocs(h, th).tourner(), ensure_ascii=False, indent=1))
