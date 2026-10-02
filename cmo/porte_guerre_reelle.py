#!/usr/bin/env python3
"""porte_guerre_reelle — le moteur de la guerre réelle ( guerre_reelle.py ) face à faux_cmo, sur un théâtre de papier
( theatres/papier_reel.py : une vraie base de papier par camp, quatre avions par camp dont deux en frappe, une unité de
missiles par camp ). Chaque mutant retire une règle ; la porte doit alors échouer.

    .venv312/bin/python cmo/porte_guerre_reelle.py [--controles]
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
import etat_major as EM                                  # noqa: E402
import guerre_reelle as GR                                # noqa: E402
import porte_cmo as P                                     # noqa: E402
from faux_cmo import FauxCMO                              # noqa: E402
from theatres import papier_reel as T                     # noqa: E402

# Deux bases de papier : une piste, un accès, deux dépôts, une cuve ( dbid de la DB3000 ).
BASES = {"Test/Malbork.inst": (54.03, 19.13), "Test/Tchkalovsk.inst": (54.77, 20.40)}
MEMBRES = [(757, "Runway"), (353, "Access"), (322, "Ammo 1"), (322, "Ammo 2"), (942, "AvGas")]
CLASSES = {757: "piste", 353: "acces", 322: "depot", 942: "carburant"}
CHARG = {7087: {"aa": 7453, "frappe": 7492, "prix_m": 45, "nom": "F-16"},
         6210: {"aa": 19291, "frappe": 27000, "prix_m": 32, "nom": "Su-30"}}
LOADOUTS = {7453: [(897, 4), (945, 2)], 7492: [(1001, 2), (945, 2)], 19291: [(2056, 2), (2053, 2)], 27000: [(1002, 4)],
            33510: [(3000, 2), (945, 2)]}
PRIX_ARME = {897: 1.0, 945: 0.45, 1001: 0.03, 2056: 0.6, 2053: 0.2, 1002: 0.02, 3000: 1.5}
# L'état-major : portées réelles de la DB3000 injectées ( S-400 215 km en l'air ; ATACMS 162 km, Iskander 270 km au sol ),
# le chargement DEAD du F-16 ( JASSM-ER, 33510 ), 60 min de préparation.
PORTEE_AIR, PORTEE_SOL = {1937: 215.0}, {3659: 162.0, 254: 270.0}
EM_KW = {"portee_air": lambda d: PORTEE_AIR.get(d, 0.0), "portee_sol": lambda d: PORTEE_SOL.get(d, 0.0),
         "charg_mission": lambda d, m: {7087: 33510}.get(d) if m == "dead" else None}


def prix_pack(lo):
    armes = LOADOUTS[lo]
    return sum(n * PRIX_ARME[w] for w, n in armes), armes


@contextlib.contextmanager
def guerre(**kw):
    racine = tempfile.mkdtemp(prefix="porte_reelle_")
    etat = os.path.join(racine, "etat")
    f = FauxCMO(racine, camps=T.CAMPS, installations=tuple(x[0] for x in T.INSTALLATIONS))
    try:
        f.installer()
        for lo, armes in LOADOUTS.items():
            f.lua(f"FAUX.loadouts[{lo}] = {{ " + ", ".join(f"{{ {w}, {n} }}" for w, n in armes) + " }")
        for fi, (la, lo) in BASES.items():
            f.lua(f"FAUX.fichiers_inst['{fi}'] = {{ "
                  + ", ".join(f"{{ {d}, '{n}', {la + j * 0.001}, {lo + j * 0.001} }}" for j, (d, n) in enumerate(MEMBRES)) + " }")
        f.demarrer()
        CL.certifier("1.10.1900.20", {"porte": True}, etat)
        kw.setdefault("em_kw", EM_KW)
        kw.setdefault("readytime", lambda lo: 60)
        g = GR.GuerreReelle("papier_reel", classer=lambda d: "groupe" if d == 0 else CLASSES.get(d, "autre"),
                            chargements=CHARG, prix_pack=prix_pack, prix_arme=PRIX_ARME.get,
                            labo_kw=dict(pont=f.pont, sortie=f.sortie, etat=etat, **P.RAPIDE), **kw)
        g.ouvrir()
        g.journal = os.path.join(racine, "journal.txt")
        open(g.journal, "w").close()
        g.construire(attente_import=0.1)
        try:
            yield f, g
        finally:
            g.fermer()
        if f.erreurs:
            raise AssertionError(f"HMT_tic a levé : {f.erreurs[:2]}")
    finally:
        f.arreter()
        shutil.rmtree(racine, ignore_errors=True)


def journal(g, *numeros):
    with open(g.journal, "a") as h:
        for k in numeros:
            h.write(f"02/10/2026 20:00:00 - [Russie-Chine] HMT-{k} (x) has been destroyed!\n")


def depots(g, camp):
    return [k for b in g.bases.values() if b["camp"] == camp for k in b["depots"]]


def stocks(g, camp):
    tot = {}
    for s in g.labo.stocks(depots(g, camp))["stocks"].values():
        for w, (c, _) in s.items():
            tot[w] = tot.get(w, 0) + c
    return tot


def e1_construire_le_theatre():
    """Deux vraies bases ( groupe, piste, accès, dépôts ), quatre avions par camp posés par paires ( deux en frappe ),
    des dépôts remplis pour PACKS_INITIAUX sorties par avion, une unité de missiles par camp."""
    with guerre() as (f, g):
        assert len(g.bases) == 2 and all(b["op"] for b in g.bases.values()), g.bases
        for camp in T.CAMPS:
            av = [a for a in g.avions.values() if a["camp"] == camp]
            assert len(av) == 4 and sum(1 for a in av if a["role"] == "frappe") == 2, av
        st = stocks(g, "OTAN")
        assert st[897] == 4 * 2 * GR.PACKS_INITIAUX and st[1001] == 2 * 2 * GR.PACKS_INITIAUX, st
        assert len(g.sol) == 2
        assert f.lua("return FAUX.doctrines['OTAN'].air_operations_tempo") == 0


def e2_defense_et_frappe():
    """Au premier tour : une patrouille sur chaque base, ses chasseurs affectés ; une frappe par camp contre la base
    adverse ( pistes, accès, dépôts ), ses avions de frappe et ses lanceurs affectés."""
    with guerre() as (f, g):
        g.tour()
        for ci, camp in enumerate(T.CAMPS):
            fr = g.frappe[camp]
            adverse = next(i for i, b in g.bases.items() if b["camp"] != camp)
            assert fr and fr["base"] == adverse, fr
            b = g.bases[adverse]
            assert sorted(fr["cibles"]) == sorted(b["pistes"] + b["acces"] + b["depots"]), fr
            cle = f"{camp}/HMT-F{fr['id']}"
            assert f.lua(f"return #FAUX.missions['{cle}'].cibles") == len(fr["cibles"])
            frappeurs = [k for k, a in g.avions.items() if a["camp"] == camp and a["role"] == "frappe"]
            assert all(g.affecte.get(k) == fr["id"] for k in frappeurs), (frappeurs, g.affecte)
            chasseurs = [k for k, a in g.avions.items() if a["camp"] == camp and a["role"] == "aa"]
            assert all(100 <= g.affecte.get(k, 0) < 1000 for k in chasseurs), g.affecte


def e3_une_piste_detruite_ferme_la_base():
    """La piste de la base russe détruite ( journal de CMO ) : la base n'est plus opérationnelle, la frappe de l'OTAN n'a
    plus de cible ; une piste endommagée au-delà de SEUIL_PISTE ferme aussi la base."""
    with guerre() as (f, g):
        g.tour()
        russe = next(i for i, b in g.bases.items() if b["camp"] == "Russie-Chine")
        piste = g.bases[russe]["pistes"][0]
        f.detruire(piste)
        journal(g, piste)
        g.tour()
        assert not g.bases[russe]["op"] and g.frappe["OTAN"] is None, (g.bases[russe], g.frappe)
        assert g.resume("Russie-Chine")["elements_perdus"] == 1
        polonaise = next(i for i, b in g.bases.items() if b["camp"] == "OTAN")
        f.lua(f"FAUX_endommager_cmo({g.bases[polonaise]['acces'][0]}, 1.0, 1000)")   # accès à 99,9 %, texte à virgule
        g.tour()
        assert not g.bases[polonaise]["op"], g.bases[polonaise]


def e4_remplacer_par_paires():
    """Un avion perdu n'est pas remplacé seul ( une patrouille ne part que par vols ) ; le deuxième perdu, la paire est
    rachetée au prix réel sur une base opérationnelle du pays."""
    with guerre() as (f, g):
        g.tour()
        g.caisse["Poland"] = 1000.0
        g.verse["Poland"] += 1000.0
        pol = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] == "aa")
        f.detruire(pol[0])
        g.tour()
        assert g.achats["Poland"] == 0 and len(g.a_remplacer) == 1, (g.achats, g.a_remplacer)
        f.detruire(pol[1])
        g.tour()
        assert g.achats["Poland"] == 2 and not g.a_remplacer, (g.achats, g.a_remplacer)
        assert sum(1 for a in g.avions.values() if a["pays"] == "Poland") == 4


def e5_racheter_les_munitions():
    """Des dépôts vidés : au relevé des stocks, le pays rachète des chargements complets, payés au prix réel."""
    with guerre() as (f, g):
        for k in depots(g, "OTAN"):
            f.lua(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then u.magazines = {{}} end end")
        g.caisse["Poland"] = 500.0
        g.verse["Poland"] += 500.0
        g.tour()                                         # tour 1 : relevé des stocks ( tours % N_STOCKS == 1 )
        assert g.packs_achetes["Poland"] > 0, g.packs_achetes
        st = stocks(g, "OTAN")
        assert st.get(897, 0) >= 4 * GR.SEUIL_PACKS, st


def e6_bilan_de_cmo():
    """Les munitions tirées comptées par CMO, valorisées au prix réel."""
    with guerre() as (f, g):
        f.lua("FAUX.bilans['OTAN'] = { losses = { { type = 'Aircraft', dbid = 7087, count = 1 } }, "
              "expenditures = { { type = 'Weapon', dbid = 897, count = 6 }, { type = 'Weapon', dbid = 1001, count = 10 } } }")
        g.tour()
        b = g.resume("OTAN")["bilan"]
        assert b == {"pertes": 1, "munitions_tirees": 16, "munitions_m": round(6 * 1.0 + 10 * 0.03, 2)}, b


def e7_l_argent_se_conserve():
    with guerre() as (f, g):
        for k in depots(g, "OTAN"):
            f.lua(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then u.magazines = {{}} end end")
        g.caisse["Poland"] = 300.0
        g.verse["Poland"] += 300.0
        pol = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland")
        g.tour()
        f.detruire(pol[0])
        f.detruire(pol[1])
        for _ in range(3):
            g.tour()
        for p in g.pays:
            assert abs(g.verse[p] - g.depense[p] - g.caisse[p]) < 1e-6 and g.caisse[p] >= -1e-9, (p, g.verse[p], g.depense[p], g.caisse[p])
        assert g.depense["Poland"] > 0


def e8_reprendre_sans_reconstruire():
    """L'état du théâtre, passé par JSON, suffit à reprendre la guerre dans le même scénario : mêmes bases, avions, forces
    au sol, caisses ; le tour suivant marche sans rien reposer."""
    import json
    with guerre() as (f, g):
        g.tour()
        e = json.loads(json.dumps(g.etat()))
        n = f.compter()
        g2 = GR.GuerreReelle("papier_reel", labo=g.labo, classer=g.classer, chargements=CHARG, prix_pack=prix_pack,
                             prix_arme=PRIX_ARME.get, em_kw=EM_KW, readytime=lambda lo: 60).charger(e)
        assert g2.resume("OTAN") == g.resume("OTAN") and g2.caisse == g.caisse and g2.bases.keys() == g.bases.keys()
        g2.tour()
        assert f.compter() == n and g2.tours == 2, (f.compter(), n, g2.tours)


def e9_completer_en_cours_de_guerre():
    """Corriger au fur et à mesure ( Younes, 02/10 ) : une base absente et ses avions sont ajoutés à la guerre en cours,
    sans rien reconstruire ; un avion perdu au combat et en attente de remplacement n'est pas reposé en double."""
    with guerre() as (f, g):
        g.tour()
        russe = next(i for i, b in g.bases.items() if b["camp"] == "Russie-Chine")
        # comme si la base russe et ses avions n'avaient jamais été posés : retirés de CMO et de l'état
        absents = [k for k, a in g.avions.items() if a["base"] == russe] + [k for k, e in g.elements.items() if e["inst"] == russe]
        for k in absents:
            f.detruire(k)
            g.avions.pop(k, None)
            g.elements.pop(k, None)
            g.affecte.pop(k, None)
        del g.bases[russe]
        g.frappe = {c: None for c in g.camps}
        pol = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] == "aa")
        f.detruire(pol[0])
        f.detruire(pol[1])
        g.caisse["Poland"] = 0.0                          # pas d'argent : les deux pertes restent en attente
        g.tour()
        assert len(g.a_remplacer) == 2, g.a_remplacer
        a = g.completer(attente_import=0.1)
        assert a["bases"] == ["Test/Tchkalovsk.inst"] and russe in g.bases, a
        assert a["avions"] == 4, a                       # les quatre russes ; pas les deux polonais en attente
        assert sum(1 for x in g.avions.values() if x["camp"] == "Russie-Chine" and x["base"] == russe) == 4
        st = stocks(g, "Russie-Chine")
        assert st.get(2056, 0) >= 2 * GR.PACKS_INITIAUX, st
        g.tour()
        assert g.frappe["OTAN"] and g.frappe["OTAN"]["base"] == russe, g.frappe


def e10_mort_pendant_une_bascule():
    """Un avion meurt et sa mort est relevée par un autre processus ( le registre l'oublie ) : le moteur constate auprès
    de CMO qu'il n'existe plus et le compte mort une fois ; une unité présente mais hors relevé reste une erreur."""
    with guerre() as (f, g):
        g.tour()
        k = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland")[0]
        f.detruire(k)
        f.lua("HMT_positions(function() end)")           # le relevé d'un autre processus consomme la mort
        g.tour()
        assert k not in g.avions and any(m["numero"] == k and m.get("constatee") for m in g.morts), g.morts
        assert g.pertes["Poland"] == 1


# Le théâtre de l'état-major : huit F-16 polonais ( quatre en frappe ), un S-400 russe à Gvardeïsk qui couvre Tchkalovsk,
# un HIMARS à 95 km du S-400 et un autre à Poznań, hors de portée.
FLOTTES_EM = [("Test/Malbork.inst", "Poland", 7087, 8, 0.5), ("Test/Tchkalovsk.inst", "Russia [1992-]", 6210, 4, 0.5)]
SOL_EM = T.SOL + [("Russia [1992-]", 1937, "S-400", 54.65, 21.07), ("Poland", 3659, "HIMARS Poznan", 52.40, 16.90)]


def e11_dead_avant_la_frappe():
    """Mets-toi en mode chef d'état-major ( Younes, 02/10 ) : la base russe sous le parapluie d'un S-400 intact n'est PAS
    frappée ; une mission DEAD vise le S-400, avec le seul lanceur À PORTÉE et une ESCORTE ; des frappeurs posés sont
    réarmés en JASSM-ER ( dépôt rempli au prix réel, chargement relu dans CMO ), puis engagés en DEAD. Le S-400 détruit, la
    mission DEAD est fermée dans CMO et notée, la frappe de la base part avec frappeurs et avions DEAD."""
    with guerre(flottes=FLOTTES_EM, sol=SOL_EM) as (f, g):
        s400 = next(k for k, s in g.sol.items() if s["dbid"] == 1937)
        proche, loin = (next(k for k, s in g.sol.items() if s["dbid"] == 3659 and s["pos"][0] > 54),
                        next(k for k, s in g.sol.items() if s["dbid"] == 3659 and s["pos"][0] < 53))
        g.caisse["Poland"] = 1000.0                       # de quoi payer les JASSM-ER ( sinon le réarmement attend )
        g.verse["Poland"] += 1000.0
        avant = g.depense["Poland"]
        g.tour()
        fr = g.frappe["OTAN"]
        assert fr["type"] == "dead" and fr["cibles"] == [s400], fr
        mid = fr["id"]
        assert g.affecte.get(proche) == mid and loin not in g.affecte, (g.affecte, proche, loin)
        frappeurs = [k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] in ("frappe", "dead")]
        assert not any(g.affecte.get(k) == mid for k in frappeurs if g.avions[k]["role"] == "frappe"), g.affecte
        assert not any(m == -mid for m in g.affecte.values()), g.affecte   # le lanceur seul ne demande pas d'escorte
        dead = [k for k in frappeurs if g.avions[k]["role"] == "dead"]
        assert len(dead) == 2 and g.depense["Poland"] > avant, (dead, g.depense)
        assert all(f.lua(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then return u.loadoutdbid end end") == 33510
                   for k in dead)
        g.tour()
        assert all(g.affecte.get(k) == mid for k in dead), (dead, g.affecte)
        esc = [k for k, m in g.affecte.items() if m == -mid]               # les avions DEAD partent escortés
        assert len(esc) == 2 and all(f.lua(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then return u.escorte end end")
                                     for k in esc), esc
        f.detruire(s400)
        g.tour()
        fr2 = g.frappe["OTAN"]
        assert fr2["type"] == "oca" and fr2["id"] != mid, fr2
        assert f.lua(f"return FAUX.missions['OTAN/HMT-F{mid}'] == nil"), "la mission DEAD n'est pas fermée dans CMO"
        assert all(g.affecte.get(k) == fr2["id"] for k in frappeurs), (frappeurs, g.affecte)
        note = next(d for d in g.em.journal if d.get("cloture") == mid)
        assert note["type"] == "dead" and note["degats"] == 100.0 and g.em.part_dead["OTAN"] > EM.PART_DEAD_DEPART, note


def e12_apprentissage_borne():
    """L'état-major apprend : des missions DEAD qui perdent des avions sans rien détruire font baisser la part d'avions
    réarmés en DEAD, jamais sous 0,2 ; des DEAD qui détruisent la font monter, jamais au-dessus de 0,8 ( choix à valider ).
    L'apprentissage survit à une reprise ( état JSON )."""
    import json
    with guerre() as (f, g):
        em = g.em

        def noter(typ, degats, pertes, n):
            for i in range(n):
                m = {"id": 9000 + len(em.missions), "type": typ, "camp": "OTAN", "cibles": [1], "ouverte": True, "t0": 0,
                     "degats0": {1: 100.0 - degats}, "avions": set(), "pertes": pertes}
                em.missions[m["id"]] = m
                g.elements[1] = {"vivant": True, "degats": 100.0 if degats else 0.0}
                em._clore(m)
        noter("dead", 0.0, 4, 30)
        assert abs(em.part_dead["OTAN"] - 0.2) < 1e-9, em.part_dead
        noter("dead", 100.0, 0, 30)
        noter("oca", 0.0, 4, 30)
        assert abs(em.part_dead["OTAN"] - 0.8) < 1e-9, em.part_dead
        g.elements.pop(1)
        e = json.loads(json.dumps(g.etat()))
        g2 = GR.GuerreReelle("papier_reel", labo=g.labo, classer=g.classer, chargements=CHARG, prix_pack=prix_pack,
                             prix_arme=PRIX_ARME.get, em_kw=EM_KW, readytime=lambda lo: 60).charger(e)
        assert g2.em.part_dead == em.part_dead and g2.em.efficacite == em.efficacite


TESTS = [e1_construire_le_theatre, e2_defense_et_frappe, e3_une_piste_detruite_ferme_la_base, e4_remplacer_par_paires,
         e5_racheter_les_munitions, e6_bilan_de_cmo, e7_l_argent_se_conserve, e8_reprendre_sans_reconstruire,
         e9_completer_en_cours_de_guerre, e10_mort_pendant_une_bascule, e11_dead_avant_la_frappe, e12_apprentissage_borne]


def controles():
    rates = []
    vrai_remplacer = GR.GuerreReelle._remplacer

    def remplacer_un_par_un(self):
        self.a_remplacer = [x for x in self.a_remplacer for _ in (0, 1)]       # chaque perte compte double : achat seul
        return vrai_remplacer(self)
    vrai_racheter = GR.GuerreReelle._racheter_munitions

    def munitions_gratuites(self):
        avant = dict(self.caisse)
        r = vrai_racheter(self)
        for p in self.pays:
            self.caisse[p] = avant[p] - (self.depense[p] - self.depense[p])
        return r

    def relever_strict(self):
        p = self.labo.positions(*GR.MOBILES)
        vus = {k for us in p["vivants"].values() for k, *_ in us}
        morts = {k for ks in p["morts"].values() for k in ks}
        perdus = (set(self.avions) | set(self.sol)) - vus - morts
        if perdus:
            raise CL.Incomplet(f"unités {sorted(perdus)[:5]} ni vivantes ni mortes dans CMO")
        return []
    vrai_completer = GR.GuerreReelle.completer

    def completer_oublieux(self, *a, **kw):
        self.a_remplacer = []                            # oublie les pertes en attente : il les reposerait en double
        return vrai_completer(self, *a, **kw)

    vrai_p = EM.EtatMajor._p

    def portee_ignoree(self, quoi, dbid):
        return 1e6 if quoi == "sol" else vrai_p(self, quoi, dbid)

    def cible_amie(self, camp):
        return next((i for i, b in self.bases.items() if b["camp"] == camp), None)
    m = [("l'état des bases n'est jamais relu", e3_une_piste_detruite_ferme_la_base, (GR.GuerreReelle, "_etat_bases", lambda self: None)),
         ("un avion seul est remplacé", e4_remplacer_par_paires, (GR.GuerreReelle, "_remplacer", remplacer_un_par_un)),
         ("les munitions sont gratuites", e7_l_argent_se_conserve, (GR.GuerreReelle, "_racheter_munitions", munitions_gratuites)),
         ("la frappe vise sa propre base", e2_defense_et_frappe, (GR.GuerreReelle, "_choisir_cible", cible_amie)),
         ("une mort hors relevé bloque la guerre", e10_mort_pendant_une_bascule, (GR.GuerreReelle, "_relever", relever_strict)),
         ("le complément repose les pertes en attente", e9_completer_en_cours_de_guerre,
          (GR.GuerreReelle, "completer", completer_oublieux)),
         ("le parapluie sol-air est ignoré", e11_dead_avant_la_frappe, (EM.EtatMajor, "couvrent", lambda self, camp, pos: [])),
         ("un lanceur est engagé hors de portée", e11_dead_avant_la_frappe, (EM.EtatMajor, "_p", portee_ignoree)),
         ("la frappe part sans escorte", e11_dead_avant_la_frappe, (EM.EtatMajor, "_escorteurs", lambda self, camp, n: [])),
         ("l'apprentissage n'a pas de plancher", e12_apprentissage_borne, (EM, "PART_DEAD_MIN", 0.0))]
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
    print("porte_guerre_reelle : la guerre réelle face à faux_cmo, théâtre de papier")
    e = P.passer(TESTS)
    print(f"{len(TESTS) - len(e)}/{len(TESTS)} tests passent")
    if "--controles" in sys.argv:
        r = controles()
        print(f"{controles.n - len(r)}/{controles.n} mutants tués")
        sys.exit(1 if e or r else 0)
    sys.exit(1 if e else 0)
