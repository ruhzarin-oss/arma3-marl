#!/usr/bin/env python3
"""porte_blocs — la guerre des blocs ( guerre_blocs.py ) hors du jeu : le vrai théâtre Baltique, le vrai Lua du pont face à
faux_cmo ( qui mène chaque avion affecté au centre de sa patrouille au passage suivant ), un petit catalogue fixe ( la porte
ne dépend pas de la base DB3000 ). Trois mutants retirent chacun une règle ; la porte doit alors échouer.

    .venv312/bin/python cmo/porte_blocs.py [--controles]
"""
import contextlib
import os
import shutil
import sys
import tempfile
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import guerre_blocs as GB                                 # noqa: E402
import porte_cmo as P                                     # noqa: E402
from faux_cmo import FauxCMO                              # noqa: E402

F16 = {"dbid": 7087, "nom": "F-16CJ Blk 52+ Falcon", "famille": "F-16", "prix_m": 45, "loadout": 0}
SU35 = {"dbid": 8333, "nom": "Su-35S", "famille": "Su-35", "prix_m": 38, "loadout": 0}
CAMPS = ("OTAN", "Russie-Chine")


@contextlib.contextmanager
def guerre(catalogue=None, **kw):
    racine = tempfile.mkdtemp(prefix="porte_blocs_")
    etat = os.path.join(racine, "etat")
    f = FauxCMO(racine, camps=CAMPS)
    try:
        f.installer()
        f.demarrer()
        CL.certifier("1.10.1900.20", {"porte": True}, etat)
        g = GB.GuerreBlocs("baltique", catalogue=catalogue if catalogue is not None else {"Poland": [F16], "Russia [1992-]": [SU35]},
                           labo_kw=dict(pont=f.pont, sortie=f.sortie, etat=etat, **P.RAPIDE), **kw).ouvrir()
        try:
            yield f, g
        finally:
            g.fermer()
        if f.erreurs:
            raise AssertionError(f"HMT_tic a levé : {f.erreurs[:2]}")
    finally:
        f.arreter()
        shutil.rmtree(racine, ignore_errors=True)


def b1_ouverture():
    with guerre() as (f, g):
        n = sum(1 for d in g.drapeaux if d["dbid"])
        time.sleep(0.2)
        assert f.compter() == n, (f.compter(), n)
        assert f.lua("return FAUX.postures['OTAN>Russie-Chine']") == "H"


def b2_credit_de_depart_et_budget():
    """Le crédit de départ achète une flotte au premier tour, posée sur les bases ; l'argent se conserve au centime."""
    with guerre() as (f, g):
        t = g.tour()
        assert g.achats["Poland"] > 0 and g.achats["Russia [1992-]"] > 0 and g.achats["Lithuania [1992-]"] == 0, g.achats
        bases_pl = {g.drapeaux[n]["pos"] for n in g.bases_de["Poland"]}
        assert all(g.positions[k] in bases_pl for k, a in g.avions.items() if a["pays"] == "Poland")
        for p in g.pays:
            assert abs(g.verse[p] - g.depense[p] - g.caisse[p]) < 1e-6 and g.caisse[p] >= 0, p
        assert len(t["achats"]) == sum(g.achats.values())


def b3_offensive_en_paquet():
    """Sous MASSE avions libres, l'offensive ne reçoit personne ; au-dessus, tout le paquet part d'un coup."""
    with guerre(masse=100) as (f, g):
        g.tour()
        assert not [k for k, i in g.affecte.items() if i % 10 == 1], "une offensive est partie sous la masse"
        assert any(i % 10 == 2 for i in g.affecte.values()), "la défense doit être tenue"
    with guerre(masse=6) as (f, g):
        g.tour()
        off = [k for k, i in g.affecte.items() if i == 11]
        assert len(off) >= 6 and len({g.avions[k]["pays"] for k in off}) >= 1, off


def b4_tenir_trois_tours():
    """Seul au-dessus d'un drapeau : il ne change de main qu'au 3e tour, pas avant."""
    with guerre(catalogue={"Poland": [F16]}, masse=3) as (f, g):
        g.tour()                                         # achats, défense, offensive posée ; les avions y seront au passage
        cible = g.offensive["OTAN"]
        time.sleep(0.2)
        g.tour()
        g.tour()
        assert g.proprio[cible] == "Russie-Chine" and g.seul[cible] == ("OTAN", 2), (g.proprio[cible], g.seul[cible])
        g.tour()
        assert g.proprio[cible] == "OTAN", g.seul[cible]
        assert g.flips and g.flips[-1]["n"] == cible


def b5_le_qg_gagne_la_guerre():
    with guerre(catalogue={"Poland": [F16]}, masse=3) as (f, g):
        qg = next(d["n"] for d in g.drapeaux if d["qg"] and d["camp0"] == "Russie-Chine")
        for d in g.drapeaux:                             # tout est pris, sauf le QG : l'offensive le vise
            if d["n"] != qg:
                g.proprio[d["n"]] = "OTAN"
        for _ in range(5):
            g.tour()
            time.sleep(0.1)
        assert g.victoire == "OTAN" and g.proprio[qg] == "OTAN", (g.offensive, g.victoire, g.seul[qg])


def b6_morts_par_pays_une_fois():
    with guerre() as (f, g):
        g.tour()
        k = next(k for k, a in g.avions.items() if a["pays"] == "Poland")
        f.detruire(k)
        g.tour()
        g.tour()
        assert g.pertes["Poland"] == 1 and len(g.morts) == 1 and g.morts[0]["numero"] == k, (g.pertes, g.morts)


def b7_quatre_envois_et_plafond():
    with guerre(plafond=10) as (f, g):
        g.tour()
        n0 = g.labo.liaison.n_confirme
        g.tour()
        assert g.labo.liaison.n_confirme - n0 <= 4, g.labo.liaison.n_confirme - n0
        assert sum(g.plafond_camp.values()) in (10, 11) and g.plafond_camp["OTAN"] > g.plafond_camp["Russie-Chine"], g.plafond_camp
        for c in g.camps:
            assert sum(1 for a in g.avions.values() if a["camp"] == c) <= g.plafond_camp[c]


def b8_pertes_d_un_camp_a_tiret():
    """Le journal de CMO écrit le camp entre crochets, tiret compris ( lignes réelles du 29/09 ) : une perte russe compte."""
    import causes_cmo
    t = ("29/09/2026 21:20:44 - [Russie-Chine] HMT-11100021 (Su-57 Felon) has run out of fuel and crashed!\n"
         "29/09/2026 21:20:44 - [Russie-Chine] HMT-11100021 (Su-57 Felon) has been destroyed!\n"
         "29/09/2026 19:02:10 - R-77M #4 HIT: Weapon: R-77M #4 is attacking HMT-10100003 (F-16CJ Blk 52+ Falcon) with a base PH "
         "of 80%.\n"
         "29/09/2026 19:02:10 - [OTAN] HMT-10100003 (F-16CJ Blk 52+ Falcon) has been destroyed!\n")
    c, _ = causes_cmo.causes(t)
    assert c == {11100021: "carburant", 10100003: "combat"}, c


def b9_un_avion_gare_ne_tient_pas_le_ciel():
    """Un avion posé sur sa base ne défend pas le drapeau : l'avion ennemi qui vole au-dessus le prend en TENUE tours.
    Guerre du 29/09 : 21 avions russes cloués au sol à Tchkalovsk ont bloqué ce drapeau 160 tours sous 18 avions de l'OTAN."""
    with guerre() as (f, g):
        n = next(d["n"] for d in g.drapeaux if d["nom"].startswith("Tchkalovsk"))
        pos = g.drapeaux[n]["pos"]
        russe, polonais = 11_100_001, 10_100_001
        g.avions = {russe: {"pays": "Russia [1992-]", "camp": "Russie-Chine", "famille": "Su-35", "base": n},
                    polonais: {"pays": "Poland", "camp": "OTAN", "famille": "F-16", "base": 1}}
        g.positions = {russe: pos, polonais: pos}
        g.altitudes = {russe: 120.0, polonais: 8000.0}
        for _ in range(g.tenue):
            g._drapeaux()
        assert g.proprio[n] == "OTAN", (g.proprio[n], g.seul[n])
        g.altitudes[russe] = 8000.0                      # le Russe décolle : le ciel est disputé, le compte retombe
        g._drapeaux()
        assert g.seul[n] == (None, 0), g.seul[n]


TESTS = [b1_ouverture, b2_credit_de_depart_et_budget, b3_offensive_en_paquet, b4_tenir_trois_tours,
         b5_le_qg_gagne_la_guerre, b6_morts_par_pays_une_fois, b7_quatre_envois_et_plafond, b8_pertes_d_un_camp_a_tiret,
         b9_un_avion_gare_ne_tient_pas_le_ciel]


def controles():
    rates = []
    vrai_init = GB.GuerreBlocs.__init__

    def sans_masse(self, *a, **kw):
        kw["masse"] = 0
        vrai_init(self, *a, **kw)

    vrai_acheter = GB.GuerreBlocs._acheter

    def achat_gratuit(self):
        avant = dict(self.depense)
        r = vrai_acheter(self)
        for p in self.pays:
            self.caisse[p] += self.depense[p] - avant[p]
        return r

    def tenue_un(self, *a, **kw):
        kw["tenue"] = 1
        vrai_init(self, *a, **kw)
    m = [("l'offensive part sans masse", b3_offensive_en_paquet, (GB.GuerreBlocs, "__init__", sans_masse)),
         ("un seul tour suffit à prendre", b4_tenir_trois_tours, (GB.GuerreBlocs, "__init__", tenue_un)),
         ("les achats sont gratuits", b2_credit_de_depart_et_budget, (GB.GuerreBlocs, "_acheter", achat_gratuit)),
         ("un avion garé tient le ciel", b9_un_avion_gare_ne_tient_pas_le_ciel, (GB.GuerreBlocs, "en_vol", lambda self, k: True))]
    for nom, test, (obj, attr, val) in m:
        with P.mutant(obj, attr, val):
            try:
                test()
                rates.append(nom)
                print(f"  RATÉ   mutant « {nom} » : {test.__name__} passe encore", flush=True)
            except Exception as e:
                print(f"  TUÉ    mutant « {nom} » par {test.__name__} ({type(e).__name__})", flush=True)
    controles.n = len(m)
    return rates


if __name__ == "__main__":
    print("porte_blocs : la guerre des blocs face à faux_cmo, théâtre Baltique")
    e = P.passer(TESTS)
    print(f"{len(TESTS) - len(e)}/{len(TESTS)} tests passent")
    r = controles() if "--controles" in sys.argv else []
    if "--controles" in sys.argv:
        print(f"{controles.n - len(r)}/{controles.n} mutants tués")
    sys.exit(1 if e or r else 0)
