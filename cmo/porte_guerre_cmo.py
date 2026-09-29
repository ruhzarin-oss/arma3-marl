#!/usr/bin/env python3
"""porte_guerre_cmo — CmoGuerre hors du jeu : sur le vrai Lua du pont ( faux_cmo ), puis sous la VRAIE horloge de guerre
( guerre/horloge.py ) avec un archipel de papier. Chaque règle a son test ; trois mutants retirent chacun une garde.

    .venv/bin/python cmo/porte_guerre_cmo.py [--controles]
"""
import contextlib
import os
import shutil
import sys
import tempfile
import time

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(ICI)
sys.path.insert(0, ICI)
sys.path.insert(0, DEPOT)
import cmo_labo as CL                                     # noqa: E402
import guerre_cmo as G                                    # noqa: E402
import porte_cmo as P                                     # noqa: E402
from faux_cmo import FauxCMO                              # noqa: E402

# Une carte de Malden de papier : deux bases ( camp_base 0 = EAST, 1 = WEST ) et trois secteurs, en mètres Arma.
ZONES = [{"n": 0, "genre": "base", "x": 1000.0, "y": 1000.0, "camp_base": 1, "lieux": []},
         {"n": 1, "genre": "base", "x": 11800.0, "y": 11800.0, "camp_base": 0, "lieux": []},
         {"n": 2, "genre": "secteur", "x": 7921.0, "y": 9516.0, "camp_base": None, "lieux": ["Malden_aeroport"]},
         {"n": 3, "genre": "secteur", "x": 3000.0, "y": 6000.0, "camp_base": None, "lieux": ["Malden_ville"]},
         {"n": 4, "genre": "secteur", "x": 9000.0, "y": 3000.0, "camp_base": None, "lieux": ["Malden_port"]}]
PRIX = G.CATALOGUE["prix_points"]


@contextlib.contextmanager
def guerre(**kw):
    racine = tempfile.mkdtemp(prefix="porte_guerre_cmo_")
    etat = os.path.join(racine, "etat")
    f = FauxCMO(racine)
    try:
        f.installer()
        f.demarrer()
        CL.certifier("1.10.1900.20", {"porte": True}, etat)
        g = G.CmoGuerre(ZONES, labo_kw=dict(pont=f.pont, sortie=f.sortie, etat=etat, **P.RAPIDE), **kw).ouvrir()
        try:
            yield f, g
        finally:
            g.fermer()
        if f.erreurs:
            raise AssertionError(f"HMT_tic a levé : {f.erreurs[:2]}")
    finally:
        f.arreter()
        shutil.rmtree(racine, ignore_errors=True)


def noms_cmo(f, camp):
    t = f.lua(f"local t = {{}} for _, u in pairs(FAUX.unites) do if u.side == '{camp}' then t[#t+1] = u.name end end "
              "return table.concat(t, ',')")
    return sorted(x for x in t.split(",") if x)


# --- LES TESTS ---------------------------------------------------------------------------------------------------------
def g0_geo():
    """Le repère Arma posé sur la Terre fait l'aller-retour au mètre, et Stratis est à ~75 km de Malden."""
    geo = G.Geo(*G.ILES_REELLES["Malden"])
    for x, y in ((0, 0), (6400, 6400), (12800, 3000)):
        x2, y2 = geo.vers_xy(*geo.vers_latlon(x, y))
        assert abs(x2 - x) < 1e-6 and abs(y2 - y) < 1e-6
    s = G.Geo(*G.ILES_REELLES["Stratis"])
    x, y = geo.vers_xy(*s.vers_latlon(4096, 4096))
    d = ((x - 6400) ** 2 + (y - 6400) ** 2) ** 0.5
    assert 60_000 < d < 90_000, d


def g1_ouverture():
    with guerre() as (f, g):
        assert f.lua("return FAUX.postures['Stratis>Malden']") == "H" == f.lua("return FAUX.postures['Malden>Stratis']")
        assert g.proprio == {0: "WEST", 1: "EAST", 2: "WEST", 3: "WEST", 4: "WEST"}, g.proprio


def g2_caisse_puis_achat():
    """Sous le prix, rien n'est acheté et la caisse monte ; au prix, un avion, nommé du numéro décalé du pilote."""
    with guerre() as (f, g):
        for _ in range(4):
            a = g.tour({"EAST": PRIX / 5, "WEST": 0.0}, {"EAST": [1, 2, 3], "WEST": []})
            assert a["camps"]["EAST"]["achats"] == 0 and a["camps"]["EAST"]["depense"] == 0
        a = g.tour({"EAST": PRIX / 5, "WEST": 0.0}, {"EAST": [], "WEST": []})
        c = a["camps"]["EAST"]
        assert c["achats"] == 1 and c["depense"] == PRIX and c["caisse"] == 0 and c["pilotes"] == 2, c
        assert noms_cmo(f, "Stratis") == ["HMT-10000001"], noms_cmo(f, "Stratis")


def g3_pas_de_pilote_pas_d_avion():
    with guerre() as (f, g):
        a = g.tour({"EAST": 0.0, "WEST": 3 * PRIX}, {"EAST": [], "WEST": []})
        assert a["camps"]["WEST"]["achats"] == 0 and a["camps"]["WEST"]["caisse"] == 3 * PRIX
        a = g.tour({"EAST": 0.0, "WEST": 0.0}, {"EAST": [], "WEST": [7]})
        assert a["camps"]["WEST"]["achats"] == 1 and noms_cmo(f, "Malden") == ["HMT-20000007"]


def g4_plafond():
    with guerre(plafond=2) as (f, g):
        a = g.tour({"EAST": 10 * PRIX, "WEST": 0.0}, {"EAST": list(range(1, 9)), "WEST": []})
        assert a["camps"]["EAST"]["vivants"] == 2 and a["camps"]["EAST"]["caisse"] == 8 * PRIX


def g5_le_ciel_tient_les_zones():
    """L'envahisseur seul au-dessus d'une zone la prend ; les deux au-dessus d'une zone : elle ne change pas ; le ciel
    redevenu libre, le défenseur va reprendre ce qu'il a perdu."""
    with guerre() as (f, g):
        g.tour({"EAST": PRIX, "WEST": 0.0}, {"EAST": [1], "WEST": []})     # achat, ordre vers la première cible
        c1 = g.cible["EAST"]
        assert c1 in (2, 3, 4)
        a = g.tour({"EAST": 0.0, "WEST": PRIX}, {"EAST": [], "WEST": [1]})  # seul au-dessus de c1 : prise
        assert a["zones"][c1] == "EAST", a["zones"]
        c2 = g.cible["EAST"]
        assert c2 != c1 and g.cible["WEST"] == c2, (c1, c2, g.cible)        # le défenseur défend la zone attaquée
        a = g.tour({"EAST": 0.0, "WEST": 0.0}, {})                           # les deux au-dessus de c2 : disputée
        assert a["zones"][c2] == "WEST" and a["zones"][c1] == "EAST", a["zones"]
        f.detruire(10000001)
        g.tour({"EAST": 0.0, "WEST": 0.0}, {})                               # ciel libre : le défenseur va vers c1
        assert g.cible["WEST"] == c1, g.cible
        a = g.tour({"EAST": 0.0, "WEST": 0.0}, {})
        assert a["zones"][c1] == "WEST" and a["camps"]["EAST"]["pertes"] == 1, (a["zones"], a["camps"]["EAST"])


def g6_morts_rendus_une_fois():
    """Une mort vue pendant un tour est rendue par positions(), une fois ; un pilote de Stratis n'est pas un de Malden."""
    with guerre() as (f, g):
        g.tour({"EAST": PRIX, "WEST": PRIX}, {"EAST": [5], "WEST": [5]})
        f.detruire(10000005)
        g.tour({"EAST": 0.0, "WEST": 0.0}, {})
        v, m = g.positions()
        assert m == {"EAST": [5], "WEST": []} and [u[0] for u in v["WEST"]] == [5], (v, m)
        assert g.positions()[1] == {"EAST": [], "WEST": []}


def g7_pont_mort_jamais_rien():
    with guerre() as (f, g):
        g.labo.canari()
        f.pause()
        with f.verrou:
            pass
        P.leve(CL.PontMort, g.tour, {"EAST": 1.0, "WEST": 1.0}, {})


def g8_quatre_envois_par_tour():
    """Relevé, achats, missions, canari : tous les ordres d'un tour partent ensemble, même avec six avions neufs."""
    with guerre() as (f, g):
        n0 = g.labo.liaison.n_confirme
        g.tour({"EAST": 3 * PRIX, "WEST": 3 * PRIX}, {"EAST": [1, 2, 3], "WEST": [1, 2, 3]})
        assert g.labo.liaison.n_confirme - n0 == 4, g.labo.liaison.n_confirme - n0


def g9_un_refus_de_cmo_ne_coute_rien():
    """CMO refuse l'avion ( dbid ) : pas payé, et le pilote revient en réserve."""
    with guerre() as (f, g):
        f.regler(dbid_refuse=G.CATALOGUE["dbid"])
        a = g.tour({"EAST": PRIX, "WEST": 0.0}, {"EAST": [1], "WEST": []})
        c = a["camps"]["EAST"]
        assert c["achats"] == 0 and c["depense"] == 0 and c["caisse"] == PRIX and c["pilotes"] == 1, c


class ArchipelDePapier:
    """Ce que l'horloge demande à l'archipel, rien de plus : des recettes fixes, des soldats numérotés, des paiements
    notés. Il ne prouve que la jointure horloge <-> CmoGuerre ; le moteur a ses propres portes."""

    def __init__(self, recettes):
        self.recettes, self.numero, self.payes, self.occupe, self.suivis, self.morts = recettes, {}, {}, [], {}, {}

    def commande(self, ile, ordre, *a):
        if ordre == "guerre_voir":
            return "regles"
        if ordre == "guerre_releve":
            return {"recettes": self.recettes, "part_defense": 0.05, "euros_par_unite": 1.0, "militaires": 50,
                    "occupees": [], "front": {"reserve": 0, "front": 0, "mort": 0}, "jour": 1, "jours_clos": 1}
        if ordre == "guerre_mobiliser":
            k0 = self.numero.get(ile, 1)
            self.numero[ile] = k0 + a[0]
            return list(range(k0, k0 + a[0]))
        if ordre == "guerre_payer":
            self.payes.setdefault(ile, []).append(a[0])
            return {"paye": a[0], "dette_points": 0.0}
        if ordre == "occuper":
            self.occupe.append((ile, a[0], a[2]))
            return None
        if ordre == "guerre_suivre":
            self.suivis[ile] = len(a[0])
            return len(a[0])
        if ordre == "guerre_morts":
            self.morts[ile] = self.morts.get(ile, 0) + len(a[0])
            return len(a[0])
        if ordre == "guerre_gouverner":
            return "conseil"
        raise KeyError(ordre)                            # tourisme_risque : l'horloge le tolère

    def un_pas(self):
        pass


def g11_les_avions_sont_en_mission():
    """Chaque avion acheté est affecté à la patrouille de son camp dans CMO ; la patrouille suit la cible."""
    def missions(f):
        return f.lua("local t = {} for _, u in pairs(FAUX.unites) do t[#t+1] = u.name .. '=' .. tostring(u.mission) end "
                     "table.sort(t) return table.concat(t, ',')")
    with guerre() as (f, g):
        g.tour({"EAST": 2 * PRIX, "WEST": 0.0}, {"EAST": [1, 2], "WEST": []})
        assert missions(f) == "HMT-10000001=HMT-P1,HMT-10000002=HMT-P1", missions(f)
        c1 = g.zone_mission["EAST"]
        g.tour({"EAST": 0.0, "WEST": PRIX}, {"EAST": [], "WEST": [1]})      # c1 prise : la patrouille avance
        assert g.zone_mission["EAST"] != c1 and g.zone_mission["WEST"] == g.zone_mission["EAST"], g.zone_mission
        assert missions(f).endswith("HMT-20000001=HMT-P2"), missions(f)


def g10_sous_la_vraie_horloge():
    """La VRAIE HorlogeDeGuerre mène CmoGuerre : points de la bourse, pilotes mobilisés, achats payés, zone prise
    occupée dans le moteur, soldats suivis."""
    from guerre.horloge import HorlogeDeGuerre
    with guerre() as (f, g):
        arc = ArchipelDePapier(recettes=2.5e7)            # 0,05 x 2,5e7 / 100 = 12 500 points par île et par tour
        h = HorlogeDeGuerre(arc, g, {"zones": ZONES}, periode_s=0.0)
        h.ouvrir()
        for _ in range(3):
            l = h.tour()
        assert l["iles"]["Stratis"]["points"] == 12_500.0
        g.caisse["EAST"] = PRIX                          # la bourse est lente : on avance la caisse de l'envahisseur
        h.tour()
        time.sleep(0.2)
        l = h.tour()
        assert arc.payes["Stratis"][-1] == PRIX, arc.payes
        assert l["occupations"]["tenues"], l["occupations"]
        assert any(ile == "Malden" and actif for ile, _, actif in arc.occupe), arc.occupe
        h.suivre_soldats()
        assert arc.suivis.get("Stratis") == 1, arc.suivis


TESTS = [g0_geo, g1_ouverture, g2_caisse_puis_achat, g3_pas_de_pilote_pas_d_avion, g4_plafond,
         g5_le_ciel_tient_les_zones, g6_morts_rendus_une_fois, g7_pont_mort_jamais_rien, g8_quatre_envois_par_tour,
         g9_un_refus_de_cmo_ne_coute_rien, g10_sous_la_vraie_horloge, g11_les_avions_sont_en_mission]


def _une_affectation_par_envoi(self, patrouilles=(), affectations=()):
    """Mutant : les patrouilles ensemble, puis un envoi par avion affecté."""
    out = {"patrouilles": [], "affectes": [], "absents": [], "refus": []}
    r = CL.Labo.__dict__["_vrai_missions"](self, patrouilles, ())
    out["patrouilles"] = r["patrouilles"]
    for i, ks in affectations:
        for k in ks:
            out["affectes"] += CL.Labo.__dict__["_vrai_missions"](self, (), [(i, [k])])["affectes"]
    return out


def controles():
    rates = []
    # le même décalage pour les deux îles : le pilote 5 de Stratis et le 5 de Malden portent le même nom dans CMO
    m = [("les pilotes des deux îles se confondent", g6_morts_rendus_une_fois,
          (G.CmoGuerre, "_vers_cmo", lambda self, camp, k: G.DECALAGE + int(k))),
         ("morts vues pendant un tour perdues", g6_morts_rendus_une_fois,
          (G.CmoGuerre, "positions", lambda self: ({c: [] for c in self.camps}, {c: [] for c in self.camps}))),
         ("un envoi par avion affecté", g8_quatre_envois_par_tour, (CL.Labo, "missions", _une_affectation_par_envoi))]
    CL.Labo._vrai_missions = CL.Labo.missions
    for nom, test, (obj, attr, val) in m:
        with P.mutant(obj, attr, val):
            try:
                test()
                rates.append(nom)
                print(f"  RATÉ   mutant « {nom} » : {test.__name__} passe encore", flush=True)
            except Exception as e:
                print(f"  TUÉ    mutant « {nom} » par {test.__name__} ({type(e).__name__})", flush=True)
    return rates


if __name__ == "__main__":
    print("porte_guerre_cmo : CmoGuerre face à faux_cmo, puis sous la vraie horloge")
    e = P.passer(TESTS)
    print(f"{len(TESTS) - len(e)}/{len(TESTS)} tests passent")
    r = controles() if "--controles" in sys.argv else []
    if "--controles" in sys.argv:
        print(f"{3 - len(r)}/3 mutants tués")
    sys.exit(1 if e or r else 0)
