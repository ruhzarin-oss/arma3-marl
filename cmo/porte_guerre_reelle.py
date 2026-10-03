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
import inventaires as INV                                 # noqa: E402
import chef_qwen as CQ                                    # noqa: E402
import json                                               # noqa: E402
import porte_cmo as P                                     # noqa: E402
from faux_cmo import FauxCMO                              # noqa: E402
from theatres import papier_reel as T                     # noqa: E402

# Deux bases de papier : une piste, un accès, deux dépôts, une cuve ( dbid de la DB3000 ).
BASES = {"Test/Malbork.inst": (54.03, 19.13), "Test/Tchkalovsk.inst": (54.77, 20.40)}
MEMBRES = [(757, "Runway"), (353, "Access"), (322, "Ammo 1"), (322, "Ammo 2"), (942, "AvGas")]
CLASSES = {757: "piste", 353: "acces", 322: "depot", 942: "carburant"}
CHARG = {7087: {"aa": 7453, "frappe": 7492, "prix_m": 45, "nom": "F-16"},
         6210: {"aa": 19291, "frappe": 27000, "prix_m": 32, "nom": "Su-30"},
         1626: {"aa": None, "frappe": None, "guet": 8076, "prix_m": 300, "nom": "E-3A"},
         7712: {"aa": None, "frappe": None, "ravitailleur": 19801, "prix_m": 40, "nom": "KC-135R"},
         4518: {"aa": None, "frappe": None, "brouilleur": 22929, "prix_m": 70, "nom": "EA-18G"},
         7611: {"aa": None, "frappe": None, "sead": 34933, "prix_m": 30, "nom": "Tornado ECR"},
         7023: {"aa": None, "frappe": None, "bombardier": 2324, "prix_m": 90, "nom": "Tu-95MSM"},
         7473: {"aa": None, "frappe": None, "reco": 8600, "prix_m": 32, "nom": "MQ-9A"},
         5832: {"aa": None, "frappe": None, "elint": 8824, "prix_m": 150, "nom": "RC-135V"}}
LOADOUTS = {7453: [(897, 4), (945, 2)], 7492: [(1001, 2), (945, 2)], 19291: [(2056, 2), (2053, 2)], 27000: [(1002, 4)],
            33510: [(3000, 2), (945, 2)], 8076: [], 19801: [], 22929: [(4000, 2)], 34933: [(4001, 2)], 2324: [(5000, 6)],
            26997: [(5001, 4)], 8600: [], 8824: []}
PRIX_ARME = {897: 1.0, 945: 0.45, 1001: 0.03, 2056: 0.6, 2053: 0.2, 1002: 0.02, 3000: 1.5, 4000: 1.2, 4001: 0.8, 5000: 13.0,
             5001: 0.6}
# L'état-major : portées réelles de la DB3000 injectées ( S-400 215 km en l'air ; ATACMS 162 km, Iskander 270 km au sol ),
# le chargement DEAD du F-16 ( JASSM-ER, 33510 ), 60 min de préparation.
PORTEE_AIR, PORTEE_SOL = {1937: 215.0}, {3659: 162.0, 254: 270.0}
EM_KW = {"portee_air": lambda d: PORTEE_AIR.get(d, 0.0), "portee_sol": lambda d: PORTEE_SOL.get(d, 0.0),
         "charg_mission": lambda d, m: {7087: 33510}.get(d) if m == "dead" else None}


def prix_pack(lo):
    armes = LOADOUTS[lo]
    return sum(n * PRIX_ARME[w] for w, n in armes), armes


@contextlib.contextmanager
def guerre(bases=None, **kw):
    racine = tempfile.mkdtemp(prefix="porte_reelle_")
    etat = os.path.join(racine, "etat")
    f = FauxCMO(racine, camps=T.CAMPS, installations=tuple(x[0] for x in T.INSTALLATIONS))
    try:
        f.installer()
        for lo, armes in LOADOUTS.items():
            f.lua(f"FAUX.loadouts[{lo}] = {{ " + ", ".join(f"{{ {w}, {n} }}" for w, n in armes) + " }")
        for fi, (la, lo) in (bases or BASES).items():
            f.lua(f"FAUX.fichiers_inst['{fi}'] = {{ "
                  + ", ".join(f"{{ {d}, '{n}', {la + j * 0.001}, {lo + j * 0.001} }}" for j, (d, n) in enumerate(MEMBRES)) + " }")
        f.demarrer()
        CL.certifier("1.10.1900.20", {"porte": True}, etat)
        kw.setdefault("em_kw", EM_KW)
        kw.setdefault("generation", False)               # la génération de force a son test ( e25 )
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
    """Un avion perdu n'est pas remplacé seul ( une patrouille ne part que par vols ) ; au deuxième, une paire part de la
    RÉSERVE nationale ( jamais d'achat : en guerre, un avion ne s'achète pas ) et n'arrive au théâtre qu'après le délai de
    convoyage ( 6 h )."""
    with guerre() as (f, g):
        g.tour()
        r0 = g.reserve["Poland|7087"]
        pol = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] == "aa")
        f.detruire(pol[0])
        g.tour()
        assert g.achats["Poland"] == 0 and len(g.a_remplacer) == 1 and not g.renforts, (g.a_remplacer, g.renforts)
        f.detruire(pol[1])
        g.tour()
        assert len(g.renforts) == 1 and g.reserve["Poland|7087"] == r0 - 2 and g.achats["Poland"] == 0, (g.renforts, g.reserve)
        assert sum(1 for a in g.avions.values() if a["pays"] == "Poland") == 2
        f.lua("FAUX.temps = FAUX.temps + 7 * 3600")
        g.tour()                                         # l'heure du scénario est relue en fin de tour : posé au suivant
        g.tour()
        assert g.achats["Poland"] == 2 and not g.renforts and not g.a_remplacer, (g.achats, g.renforts)
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
        g.reserve["Poland|7087"] = 0.0                    # réserve vide : les deux pertes restent en attente
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
        avant, packs0 = g.depense["Poland"], g.packs_achetes["Poland"]
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
        assert g.packs_achetes["Poland"] - packs0 == GR.PACKS_INITIAUX, g.packs_achetes   # le 2e puise dans le même achat
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
        g.brouillard = False                             # l'apprentissage seul, sur les dégâts réels

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


def e13_rearmement_rate_rend_l_ancien_chargement():
    """CMO laisse l'avion SANS armes ( chargement 3 ) quand le dépôt n'a pas les armes : l'état-major ne le croit pas
    réarmé, et l'avion reprend aussitôt son ancien chargement ( 02/10 : trois avions refusés en direct )."""
    with guerre(flottes=FLOTTES_EM, sol=SOL_EM) as (f, g):
        g.caisse["Poland"] = 1000.0
        g.verse["Poland"] += 1000.0
        f.lua("local vrai = ScenEdit_SetLoadout "            # CMO laisse l'avion vide pour le JASSM-ER, comme le 02/10
              "ScenEdit_SetLoadout = function(t) if t.LoadoutID ~= 33510 then return vrai(t) end "
              "for _, x in pairs(FAUX.unites) do if x.name == t.UnitName then x.loadoutdbid = 3 end end return true end")
        g.tour()
        pol = [k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] in ("frappe", "dead")]
        assert all(g.avions[k]["role"] == "frappe" for k in pol), g.avions
        lus = {k: f.lua(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then return u.loadoutdbid end end") for k in pol}
        assert all(v == 7492 for v in lus.values()), lus
        assert any("rendu" in d for d in g.em.journal), g.em.journal


def e14_cible_la_plus_menacante():
    """La cible est la base adverse qui MENACE le plus ( avions basés / distance à la plus proche de nos bases ), pas la
    plus proche : un terrain vide à 30 km passe après Tchkalovsk et ses quatre Su-30 à 117 km. La cible en cours est gardée
    tant qu'elle menace au moins 80 % de la pire ( pas de valse des missions )."""
    with guerre() as (f, g):
        g.brouillard = False                             # le choix seul, sans l'évaluation des dégâts ( e22 )
        tch = next(i for i, b in g.bases.items() if b["camp"] == "Russie-Chine")
        g.bases[99] = {"camp": "Russie-Chine", "pays": "Russia [1992-]", "op": True, "pos": (54.20, 19.50), "fichier": "Test/Leurre.inst",
                       "pistes": [], "acces": [], "depots": [], "groupe": None, "role": "chasse"}
        assert g._choisir_cible("OTAN") == tch, g._choisir_cible("OTAN")
        g.avions[99999] = {"pays": "Russia [1992-]", "camp": "Russie-Chine", "dbid": 6210, "base": 99, "role": "aa", "loadout": 19291}
        g.frappe["OTAN"] = {"id": 1001, "base": 99, "cibles": []}
        assert g._choisir_cible("OTAN") == 99                       # 2/50 >= 0,8 x 5/117 : gardée
        g.frappe["OTAN"] = None
        assert g._choisir_cible("OTAN") == tch                      # sans cible en cours : la pire
        del g.avions[99999], g.bases[99]


def e15_swing_role():
    """Un frappeur SANS arme à distance de sécurité ne va pas sous le parapluie : pendant la DEAD il repasse en chasse
    ( chargement air-air relu dans CMO, patrouille ) ; le S-400 détruit, il revient à la frappe et part sur la base."""
    kw = dict(EM_KW, charg_mission=lambda d, m: None)            # aucun chargement DEAD
    with guerre(flottes=FLOTTES_EM, sol=SOL_EM, em_kw=kw) as (f, g):
        s400 = next(k for k, s in g.sol.items() if s["dbid"] == 1937)
        frappeurs = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] == "frappe")
        g.tour()
        assert g.frappe["OTAN"]["type"] == "dead"
        assert all(g.avions[k]["role"] == "aa" and g.avions[k]["bascule"] == "frappe" for k in frappeurs), g.avions
        assert all(f.lua(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then return u.loadoutdbid end end") == 7453
                   for k in frappeurs)
        g.tour()
        assert all(100 <= g.affecte.get(k, 0) < 1000 for k in frappeurs), g.affecte    # en patrouille
        f.detruire(s400)
        for k in frappeurs:                                         # posés entre deux patrouilles
            f.lua(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then u.mission = nil u.altitude = 0 end end")
        g.tour()
        assert g.frappe["OTAN"]["type"] == "oca"
        assert all(g.avions[k]["role"] == "frappe" and "bascule" not in g.avions[k] for k in frappeurs), g.avions
        g.tour()
        assert all(g.affecte.get(k) == g.frappe["OTAN"]["id"] for k in frappeurs), g.affecte


def e16_cadence_surge_puis_soutenue():
    """Les trois premiers jours de guerre en « surge » ( doctrine air_operations_tempo 0 ), puis cadence soutenue ( 1 ) :
    une sortie par jour et par pilote, comme les campagnes réelles."""
    with guerre() as (f, g):
        g.tour()
        assert f.lua("return FAUX.doctrines['OTAN'].air_operations_tempo") == 0 and g.debut is not None
        f.lua("FAUX.temps = FAUX.temps + 71 * 3600")
        g.tour()
        assert f.lua("return FAUX.doctrines['OTAN'].air_operations_tempo") == 0
        f.lua("FAUX.temps = FAUX.temps + 2 * 3600")
        g.tour()
        assert all(f.lua(f"return FAUX.doctrines['{c}'].air_operations_tempo") == 1 for c in T.CAMPS) and g.tempo == 1


def e17_brouillard_de_guerre():
    """Le brouillard de guerre et la carte des menaces : les garnisons sol-air adverses sont connues d'avance ( le S-400
    déclenche la DEAD dès le premier tour ). Une défense qui n'est PAS sur la carte ( arrivée ou déplacée en secret ) n'existe
    pas pour l'état-major : la frappe part sur la base ; vue mais seulement « milieu connu » ( classe 1 ), toujours rien ;
    classée, elle entre sur la carte ( DEAD ) ; perdue de vue ensuite, elle y RESTE à sa dernière position."""
    with guerre(flottes=FLOTTES_EM, sol=SOL_EM) as (f, g):
        s400 = next(k for k, s in g.sol.items() if s["dbid"] == 1937)
        trouver = f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{s400}' then %s end end"
        g.tour()
        assert g.frappe["OTAN"]["type"] == "dead" and s400 in g.em.memoire["OTAN"], g.frappe["OTAN"]   # avant-guerre
        f.lua(trouver % "FAUX.caches['OTAN/' .. u.guid] = true")
        del g.em.memoire["OTAN"][s400]                   # comme s'il avait bougé en secret
        g.tour()
        assert s400 not in g.vus["OTAN"] and g.frappe["OTAN"]["type"] == "oca", (g.vus["OTAN"], g.frappe["OTAN"])
        f.lua(trouver % "FAUX.caches['OTAN/' .. u.guid] = nil FAUX.classif['OTAN/' .. u.guid] = 1")
        g.tour()
        assert g.vus["OTAN"][s400][0] == 1 and g.frappe["OTAN"]["type"] == "oca", (g.vus["OTAN"], g.frappe["OTAN"])
        f.lua(trouver % "FAUX.classif['OTAN/' .. u.guid] = 3")
        g.tour()
        assert g.frappe["OTAN"]["type"] == "dead" and g.frappe["OTAN"]["cibles"] == [s400], g.frappe["OTAN"]
        f.lua(trouver % "FAUX.caches['OTAN/' .. u.guid] = true")
        g.tour()
        assert s400 not in g.vus["OTAN"] and g.frappe["OTAN"]["type"] == "dead", g.frappe["OTAN"]   # la carte se souvient


# La composante air : la base polonaise à Poznań ( 360 km de Tchkalovsk, hors de portée du S-400 ), douze F-16, deux E-3A,
# deux KC-135R, deux EA-18G, deux Tornado ECR.
BASES_AIR = {"Test/Malbork.inst": (52.40, 16.90), "Test/Tchkalovsk.inst": (54.77, 20.40)}
FLOTTES_AIR = [("Test/Malbork.inst", "Poland", 7087, 12, 0.5), ("Test/Malbork.inst", "Poland", 1626, 2, "guet"),
               ("Test/Malbork.inst", "Poland", 7712, 2, "ravitailleur"), ("Test/Malbork.inst", "Poland", 4518, 2, "brouilleur"),
               ("Test/Malbork.inst", "Poland", 7611, 2, "sead"), ("Test/Tchkalovsk.inst", "Russia [1992-]", 6210, 4, 0.5)]


def e18_composante_air():
    """Donne-lui toute la composante air ( Younes, 03/10 ) : le guet radar orbite radar allumé, le ravitailleur plus en
    arrière, tous deux hors de portée du S-400 connu ( avec leurs marges ) ; le brouilleur en stand-off, brouillage allumé,
    juste hors de portée ; la SEAD sur la défense ; une barrière de chasse avancée ( la paire de la base reste ) ; chaque
    avion de soutien affecté à sa mission."""
    with guerre(bases=BASES_AIR, flottes=FLOTTES_AIR, sol=SOL_EM) as (f, g):
        s400 = next(k for k, s in g.sol.items() if s["dbid"] == 1937)
        sp, r = g.sol[s400]["pos"], PORTEE_AIR[1937]
        g.tour()
        assert g.frappe["OTAN"]["type"] == "dead", g.frappe
        z = g.em.zones

        def mission(i):
            return f.lua(f"local m = FAUX.missions['OTAN/HMT-P{i}'] return m and (m.genre .. '/' .. tostring(m.type))")
        assert [mission(i) for i in range(500, 505)] == ["Support/nil"] * 3 + ["Patrol/SEAD", "Patrol/AAW"], [mission(i) for i in range(500, 505)]
        assert f.lua("return FAUX.emcon['Mission/HMT-P500']") == "Radar=Active"
        assert "OECM=Active" in f.lua("return FAUX.emcon['Mission/HMT-P502']")
        marges = {500: 60, 501: 100, 502: 15, 504: 20}
        assert all(GR.km(z[i], sp) >= r + m for i, m in marges.items()), {i: round(GR.km(z[i], sp)) for i in z}
        assert GR.km(z[500], BASES_AIR["Test/Malbork.inst"]) > 30, z           # pas sur la base : en avant
        assert GR.km(z[503], sp) < 1, z
        roles = {"guet": 500, "ravitailleur": 501, "brouilleur": 502, "sead": 503}
        mal = [(k, a["role"], g.affecte.get(k)) for k, a in g.avions.items() if a["role"] in roles and g.affecte.get(k) != roles[a["role"]]]
        assert not mal, mal
        bar = [k for k, m in g.affecte.items() if m == 504]
        assert len(bar) == 2, bar                                              # 6 chasseurs : 2 gardent, 2 sur 4 en barrière


def e19_bombardiers():
    """Les bombardiers ( Tu-95MSM et ses Kh-101 ) rejoignent la frappe de la base ennemie, avec les frappeurs ; tirant de
    loin, ils ne réclament pas d'escorte."""
    fl = T.FLOTTES + [("Test/Tchkalovsk.inst", "Russia [1992-]", 7023, 2, "bombardier")]
    with guerre(flottes=fl) as (f, g):
        bomb = sorted(k for k, a in g.avions.items() if a["role"] == "bombardier")
        g.tour()
        fr = g.frappe["Russie-Chine"]
        assert len(bomb) == 2 and fr["type"] == "oca" and all(g.affecte.get(k) == fr["id"] for k in bomb), (bomb, fr, g.affecte)
        esc = [k for k, m in g.affecte.items() if m == -fr["id"]]
        assert not esc, esc                              # 2 frappeurs : pas d'escorte de plus ( 2 aa seulement à la base )


def e20_sead_russe():
    """Sans avions SEAD dédiés, la Russie réarme une paire de Su-30 en Kh-31P quand un Patriot couvre sa cible ; la paire
    part en patrouille SEAD sur la défense ; les autres frappeurs ne sont pas pris en double."""
    sol = T.SOL + [("Poland", 3653, "Patriot", 54.05, 19.16)]
    kw = dict(EM_KW, portee_air=lambda d: {3653: 60.0, 1937: 215.0}.get(d, 0.0),
              charg_mission=lambda d, m: {"dead": {7087: 33510}, "sead": {6210: 26997}}.get(m, {}).get(d))
    with guerre(sol=sol, em_kw=kw) as (f, g):
        g.caisse["Russia [1992-]"] = 1000.0
        g.verse["Russia [1992-]"] += 1000.0
        g.tour()
        assert g.frappe["Russie-Chine"]["type"] == "dead", g.frappe
        sead = sorted(k for k, a in g.avions.items() if a["role"] == "sead")
        assert len(sead) == 2 and all(g.avions[k]["camp"] == "Russie-Chine" and g.avions[k]["bascule"] == "frappe" for k in sead), g.avions
        assert all(f.lua(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then return u.loadoutdbid end end") == 26997 for k in sead)
        g.tour()
        assert all(g.affecte.get(k) == 513 for k in sead), g.affecte
        assert f.lua("local m = FAUX.missions['Russie-Chine/HMT-P513'] return m and m.type") == "SEAD"


def e21_balayage():
    """Ciel ouvert ( frappe OCA ) : la moitié de la chasse avancée balaie la cible, l'autre tient la barrière."""
    fl = [("Test/Malbork.inst", "Poland", 7087, 16, 0.25), ("Test/Tchkalovsk.inst", "Russia [1992-]", 6210, 4, 0.5)]
    with guerre(bases=BASES_AIR, flottes=fl) as (f, g):
        g.tour()
        assert g.frappe["OTAN"]["type"] == "oca", g.frappe
        tch = g.bases[g.frappe["OTAN"]["base"]]["pos"]
        bal, bar = ([k for k, m in g.affecte.items() if m == z] for z in (505, 504))
        assert len(bal) == 2 and len(bar) == 2 and GR.km(g.em.zones[505], tch) < 1, (bal, bar, g.em.zones)
        assert f.lua("local m = FAUX.missions['OTAN/HMT-P505'] return m and m.type") == "AAW"


def e22_evaluation_des_degats():
    """L'évaluation des dégâts ( BDA ) : la piste de Tchkalovsk détruite SANS qu'aucun capteur de l'OTAN ne voie la base
    ( contacts vieux de 2 h ), l'OTAN la croit encore ouverte et continue de la viser ; un contact frais ( reconnaissance,
    avions qui frappent ) montre la piste détruite : la base sort des cibles."""
    with guerre() as (f, g):
        g.tour()
        russe = next(i for i, b in g.bases.items() if b["camp"] == "Russie-Chine")
        b = g.bases[russe]
        vieux = " ".join(f"for _, u in pairs(FAUX.unites) do if u.name == 'HMT-{k}' then FAUX.ages['OTAN/' .. u.guid] = %s end end"
                         for k in b["pistes"] + b["acces"] + b["depots"])
        f.lua(vieux % tuple([7200] * len(b["pistes"] + b["acces"] + b["depots"])))
        piste = b["pistes"][0]
        f.detruire(piste)
        journal(g, piste)
        g.tour()
        assert not b["op"] and g.frappe["OTAN"] and g.frappe["OTAN"]["base"] == russe, (b["op"], g.frappe["OTAN"])
        assert g.percu("OTAN", piste) < 100.0
        f.lua(vieux % tuple([60] * len(b["pistes"] + b["acces"] + b["depots"])))
        g.tour()
        assert g.percu("OTAN", piste) == 100.0 and g.frappe["OTAN"] is None, (g.bda["OTAN"], g.frappe["OTAN"])


def e23_reconnaissance():
    """La reconnaissance : les drones ( MQ-9A ) orbitent sur la cible quand aucune défense connue ne la couvre, l'avion
    d'écoute ( RC-135V ) en stand-off ; chacun affecté à sa mission."""
    fl = [("Test/Malbork.inst", "Poland", 7087, 8, 0.5), ("Test/Malbork.inst", "Poland", 7473, 2, "reco"),
          ("Test/Malbork.inst", "Poland", 5832, 2, "elint"), ("Test/Tchkalovsk.inst", "Russia [1992-]", 6210, 4, 0.5)]
    with guerre(bases=BASES_AIR, flottes=fl) as (f, g):
        g.tour()
        assert g.frappe["OTAN"]["type"] == "oca", g.frappe
        tch = g.bases[g.frappe["OTAN"]["base"]]["pos"]
        z = g.em.zones
        assert GR.km(z[506], tch) < 1 and GR.km(z[507], tch) > 30, z
        mal = [(k, a["role"]) for k, a in g.avions.items() if a["role"] in ("reco", "elint")
               and g.affecte.get(k) != {"reco": 506, "elint": 507}[a["role"]]]
        assert not mal, mal


def e24_reserve_et_production():
    """Réserve nationale vide : la perte n'est PAS remplacée ( aucun achat, quel que soit l'argent ) ; la production
    mensuelle remplit la réserve au rythme réel et la paire repart vers le théâtre."""
    with guerre() as (f, g):
        g.tour()
        g.reserve["Poland|7087"] = 0.0
        g.caisse["Poland"] = 1e6
        pol = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] == "aa")
        f.detruire(pol[0])
        f.detruire(pol[1])
        g.tour()
        assert len(g.a_remplacer) == 2 and not g.renforts, (g.a_remplacer, g.renforts)
        with P.mutant(INV, "PRODUCTION_MOIS", {("Poland", 7087): 2.0 * 30 * 24 * 60 / g.periode_min}):
            g.tour()
        assert len(g.renforts) == 1 and not g.a_remplacer, (g.renforts, g.a_remplacer, g.reserve["Poland|7087"])


def e25_generation_de_force():
    """Le moteur CHOISIT ses forces ( Younes, 03/10 ) : face à 4 avions russes menaçants, sa chasse ( 2 ) est en déficit :
    il engage une paire de F-16 de la réserve en chasse, et une paire de frappeurs pour les cibles, qui arrivent après le
    convoyage. Il s'adapte : un ratio de chasse doublé ( menace jugée plus forte ) double l'engagement suivant."""
    with guerre(generation=True) as (f, g):
        g.tour()
        eng = [r for r in g.renforts if r.get("engage") and r["pays"] == "Poland"]
        assert sorted((r["role"], r["n"]) for r in eng) == [("aa", 2), ("frappe", 2)], g.renforts
        d = next(x for x in g.em.journal if x.get("camp") == "OTAN" and "besoins" in x)
        assert d["besoins"]["aa"] == [4, 2] and d["besoins"]["_menace_air"] == 4, d
        g.em.ratio["OTAN"]["aa"] = 2.0
        for _ in range(10):
            g.tour()
        d = [x for x in g.em.journal if x.get("camp") == "OTAN" and "besoins" in x][-1]
        (besoin, tenu), menace = d["besoins"]["aa"], d["besoins"]["_menace_air"]
        assert d["tour"] == 11 and menace >= 4 and besoin == 2 * menace, d                 # la menace lue, au ratio doublé
        attendu = min(EM.MAX_PAR_DECISION, besoin - tenu) // 2 * 2
        assert ["Poland", 7087, "aa", attendu] == d["engage"][0][:4] and attendu >= 4, d


def e26_apprentissage_des_forces():
    """L'état-major apprend de ses pertes : la chasse polonaise perd 3 avions sans en abattre -> plus de chasseurs par avion
    menaçant ; une fenêtre où les Russes perdent plus -> on redescend doucement ; la valeur des F-16 en chasse tombe avec
    leurs pertes ; les ratios restent dans leurs bornes ( 0,5 à 3 )."""
    with guerre() as (f, g):
        g.tour()
        em = g.em
        pol = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] == "aa")
        ru = sorted(k for k, a in g.avions.items() if a["pays"] != "Poland")

        def perdre(ks):
            for k in ks:
                a = g.avions[k]
                g.morts.append({"numero": k, "genre": "avion", "pays": a["pays"], "tour": g.tours,
                                "cle": [None, a["pays"], a["dbid"], a["role"]]})
        perdre(pol[:2])
        g.detruits.append({"numero": 1, "classe": "piste", "camp": "OTAN", "inst": 0, "tour": g.tours})
        em.apprendre_forces("OTAN")
        assert abs(em.ratio["OTAN"]["aa"] - 1.25) < 1e-9 and em.valeur["7087|aa"] < 1.0, (em.ratio, em.valeur)
        g.tours += 1
        perdre(ru[:3])
        em.apprendre_forces("OTAN")
        assert em.ratio["OTAN"]["aa"] < 1.25, em.ratio
        for _ in range(40):
            g.tours += 1
            perdre(pol[:2])
            em.apprendre_forces("OTAN")
        assert abs(em.ratio["OTAN"]["aa"] - 3.0) < 1e-9, em.ratio                 # borne haute ( à valider )


def e27_chef_qwen():
    """Le chef d'état-major ( Qwen, ici un faux qui répond comme lui ) : à la période, il reçoit la situation et trois modes
    d'action JOUÉS sur la copie ( prévisions ) ; sa décision, BORNÉE ( multiplicateur 3 ramené à 2 ), devient la cible
    prioritaire et les ratios de l'état-major ; une réponse illisible laisse « poursuivre » ; à l'horizon, le résultat
    obtenu est comparé à la prévision et l'estimateur se recale."""
    import chef_qwen as CQ
    vus = []

    def faux(messages):
        vus.append(json.loads(messages[1]["content"]))
        if len(vus) == 1:
            russe = next(b["index"] for b in vus[0]["situation"]["bases_adverses"])
            return json.dumps({"mode": "concentrer", "raison": "la base russe concentre la menace", "cible": russe,
                               "mult_aa": 1.0, "mult_frappe": 3.0, "reserves": "engager"})
        return "ce n'est pas du JSON"
    with guerre() as (f, g):
        g.chef = CQ.ChefQwen(g, appeler=faux)
        g.tour()
        g.tour()                                          # tour 2 : les deux camps demandent
        for th in g.chef.en_cours.values():
            th.join(5)
        g.tour()                                          # tour 3 : décisions appliquées
        modes = vus[0]["modes_d_action"]
        assert [m["id"] for m in modes] == ["poursuivre", "concentrer", "defendre"] and all("prevision" in m for m in modes)
        decs = {d["camp"]: d["decision"] for d in g.chef.decisions}
        russe = next(i for i, b in g.bases.items() if b["camp"] == "Russie-Chine")
        ot = decs["OTAN"] if decs["OTAN"]["id"] == "concentrer" else decs["Russie-Chine"]
        autre = decs["Russie-Chine"] if ot is decs["OTAN"] else decs["OTAN"]
        assert ot["mult_frappe"] == 2.0 and ot["valide"] and autre["id"] == "poursuivre" and not autre["valide"], decs
        assert g.em.mult_chef[[c for c, d in decs.items() if d is ot][0]]["frappe"] == 2.0
        if decs["OTAN"] is ot:
            assert g.em.cible_imposee["OTAN"] == russe and g.frappe["OTAN"]["base"] == russe
        for _ in range(CQ.HORIZON_TOURS):
            g.tour()
        assert all(d["bilan"] is not None for d in g.chef.decisions[:2]), [d["bilan"] for d in g.chef.decisions]
        assert any("bilan_chef" in x for x in g.em.journal)


NAVIRES_TEST = [("Russia [1992-]", 9001, "Karakurt", 2, 54.70, 19.80, "lance_missiles", "navire"),
                ("Russia [1992-]", 9002, "Kilo", 1, 54.75, 19.60, "sous_marin", "sous_marin"),
                ("Poland", 9003, "Kormoran", 2, 54.60, 18.70, "corvette", "navire")]
ZONES_TEST = {"Russie-Chine": {"mer": (55.0, 19.5, 30.0), "asm": (55.3, 18.5, 30.0)}, "OTAN": {"mer": (55.0, 18.5, 40.0)}}


def e28_composante_navale():
    """La marine : les navires réels posés en rade ; frégates et corvettes en CONTRÔLE DE LA MER, sous-marins en LUTTE
    ANTI-SOUS-MARINE ; les lance-missiles de croisière ( Karakurt, Kalibr ) engagés dans la frappe de la base ennemie À
    PORTÉE ; un navire coulé est compté une fois, et le complément ne le repose pas."""
    kw = dict(EM_KW, portee_nav=lambda d: {9001: 1500.0}.get(d, 0.0))
    with guerre(navires=NAVIRES_TEST, zones_navales=ZONES_TEST, em_kw=kw) as (f, g):
        assert len(g.navires) == 5, g.navires
        g.tour()
        fr = g.frappe["Russie-Chine"]
        kara = sorted(k for k, n in g.navires.items() if n["nom"] == "Karakurt")
        assert all(g.affecte.get(k) == fr["id"] for k in kara), (kara, fr, g.affecte)
        kilo = next(k for k, n in g.navires.items() if n["nom"] == "Kilo")
        korm = sorted(k for k, n in g.navires.items() if n["nom"] == "Kormoran")
        assert g.affecte.get(kilo) == 611 and all(g.affecte.get(k) == 600 for k in korm), g.affecte
        typ = lambda c, i: f.lua(f"local m = FAUX.missions['{c}/HMT-P{i}'] return m and m.type")       # noqa: E731
        # pas de frégate russe ici : pas de contrôle de la mer russe ; le Kilo en lutte ASM, les Kormoran en contrôle de la mer
        assert (typ("Russie-Chine", 610), typ("Russie-Chine", 611), typ("OTAN", 600)) == (None, "SUB", "SEA")
        f.detruire(korm[0])
        g.tour()
        assert korm[0] not in g.navires and any(m["genre"] == "navire" and m["numero"] == korm[0] for m in g.morts)
        assert g.completer_navires() == [] and len(g.navires) == 4


def e29_frappe_antinavire():
    """La guerre navale : les navires ennemis IDENTIFIÉS entrent sur la carte des menaces ; à moins de 400 km et hors des
    parapluies connus, ils sont la cible d'une frappe antinavire ( Strike de type Sea ) ; un frappeur qui attendait y est
    engagé ; le navire coulé, la frappe se referme sur les autres."""
    kw = dict(EM_KW, portee_nav=lambda d: {9001: 1500.0}.get(d, 0.0), portee_mer=lambda d: 0.0)
    with guerre(navires=NAVIRES_TEST, zones_navales=ZONES_TEST, em_kw=kw) as (f, g):
        g.tour()
        russes = sorted(k for k, n in g.navires.items() if n["camp"] == "Russie-Chine")
        an = g.em.antinav["OTAN"]
        assert an and an["cibles"] == russes and all(k in g.em.memoire["OTAN"] for k in russes), (an, g.em.memoire["OTAN"])
        assert f.lua(f"local m = FAUX.missions['OTAN/HMT-F{an['id']}'] return m and (m.type .. '/' .. #m.cibles)") == f"Sea/{len(russes)}"
        libre = sorted(k for k, a in g.avions.items() if a["pays"] == "Poland" and a["role"] == "frappe")[:2]
        for k in libre:
            g.affecte.pop(k, None)                        # comme pendant une DEAD : des frappeurs qui attendent
        g.em.frappe_libre = True
        f.detruire(russes[0])
        g.tour()
        an2 = g.em.antinav["OTAN"]
        assert an2["cibles"] == russes[1:] and an2["id"] != an["id"], an2
        assert f.lua(f"return FAUX.missions['OTAN/HMT-F{an['id']}'] == nil"), "l'ancienne frappe antinavire n'est pas fermée"


TESTS = [e1_construire_le_theatre, e2_defense_et_frappe, e3_une_piste_detruite_ferme_la_base, e4_remplacer_par_paires,
         e5_racheter_les_munitions, e6_bilan_de_cmo, e7_l_argent_se_conserve, e8_reprendre_sans_reconstruire,
         e9_completer_en_cours_de_guerre, e10_mort_pendant_une_bascule, e11_dead_avant_la_frappe, e12_apprentissage_borne,
         e13_rearmement_rate_rend_l_ancien_chargement, e14_cible_la_plus_menacante, e15_swing_role,
         e16_cadence_surge_puis_soutenue, e17_brouillard_de_guerre, e18_composante_air,
         e19_bombardiers, e20_sead_russe, e21_balayage, e22_evaluation_des_degats, e23_reconnaissance,
         e24_reserve_et_production, e25_generation_de_force, e26_apprentissage_des_forces, e27_chef_qwen,
         e28_composante_navale, e29_frappe_antinavire]


def controles():
    rates = []
    vrai_remplacer = GR.GuerreReelle._remplacer

    def remplacer_un_par_un(self):
        self.a_remplacer = [x for x in self.a_remplacer for _ in (0, 1)]       # chaque perte compte double : achat seul
        return vrai_remplacer(self)
    vrai_racheter = GR.GuerreReelle._racheter_munitions

    def remplacer_sans_reserve(self):
        for c in self.reserve:
            self.reserve[c] = 1e9
        return vrai_remplacer(self)

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

    vrai_charger = CL.Labo.charger

    def charger_sans_retour(self, lots):
        return vrai_charger(self, [x for x in lots if x[2] != 0]) if any(x[2] != 0 for x in lots) else {"charges": {}, "absents": []}
    vrai_renseigner = EM.EtatMajor.renseigner

    def renseigner_sans_navires(self):
        vrai_renseigner(self)
        for c, m in self.memoire.items():
            for k in [k for k in m if k in self.g.navires]:
                del m[k]
    vrai_p_nav = EM.EtatMajor._p

    def portee_nav_nulle(self, quoi, dbid):
        return 0.0 if quoi == "nav" else vrai_p_nav(self, quoi, dbid)

    def recul_aveugle(self, camp, C, T, t, marge, marge_b):
        return (C[0] + t * (T[0] - C[0]), C[1] + t * (T[1] - C[1]))
    vrai_p = EM.EtatMajor._p

    def portee_ignoree(self, quoi, dbid):
        return 1e6 if quoi == "sol" else vrai_p(self, quoi, dbid)

    def cible_la_plus_proche(self, camp):                       # l'ancienne règle : la plus proche du centre du camp
        miennes = [b["pos"] for b in self.bases.values() if b["camp"] == camp]
        c = (sum(p[0] for p in miennes) / len(miennes), sum(p[1] for p in miennes) / len(miennes))
        cand = [(GR.km(b["pos"], c), i) for i, b in self.bases.items() if b["camp"] != camp and b["op"]]
        return min(cand)[1] if cand else None

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
         ("l'apprentissage n'a pas de plancher", e12_apprentissage_borne, (EM, "PART_DEAD_MIN", 0.0)),
         ("un avion laissé vide reste vide", e13_rearmement_rate_rend_l_ancien_chargement,
          (CL.Labo, "charger", charger_sans_retour)),
         ("la cible est la base la plus proche", e14_cible_la_plus_menacante, (GR.GuerreReelle, "_choisir_cible", cible_la_plus_proche)),
         ("pas de swing-role", e15_swing_role, (EM.EtatMajor, "_basculer", lambda self, camp, vers: [])),
         ("la guerre reste en surge", e16_cadence_surge_puis_soutenue, (GR, "SURGE_H", 1e9)),
         ("l'état-major voit tout", e17_brouillard_de_guerre, (EM.EtatMajor, "_connu", lambda self, camp, k: True)),
         ("la carte des menaces oublie", e17_brouillard_de_guerre,
          (EM.EtatMajor, "_connu", lambda self, camp, k: (self.g.vus.get(camp, {}).get(k) or (0,))[0] >= EM.CLASSIF_MIN
           or (not self.g.tours > 1 and k in self.memoire.get(camp, {})))),
         ("le soutien orbite sous le parapluie", e18_composante_air, (EM.EtatMajor, "_recul", recul_aveugle)),
         ("le brouilleur ne brouille pas", e18_composante_air, (EM, "SOUTIEN", dict(EM.SOUTIEN, brouilleur=EM.SOUTIEN["brouilleur"][:6] + (1,)))),
         ("pas de barrière de chasse", e18_composante_air, (EM.EtatMajor, "_barriere", lambda self, camp, zid: [])),
         ("les bombardiers restent au sol", e19_bombardiers, (EM, "ROLES_OCA", ("frappe", "dead"))),
         ("pas de SEAD sans avions dédiés", e20_sead_russe, (EM.EtatMajor, "_rearmer_sead", lambda self, camp: [])),
         ("pas de balayage", e21_balayage, (EM, "SOUTIEN", {k: v for k, v in EM.SOUTIEN.items() if k != "balayage"})),
         ("l'état-major lit les dégâts réels", e22_evaluation_des_degats, (GR.GuerreReelle, "op_percu", lambda self, camp, i: self.bases[i]["op"])),
         ("un avion s'achète en guerre", e24_reserve_et_production, (GR.GuerreReelle, "_remplacer", remplacer_sans_reserve)),
         ("pas de frappe antinavire", e29_frappe_antinavire, (EM.EtatMajor, "antinavire", lambda self, ci, camp: ([], []))),
         ("la carte oublie les navires", e29_frappe_antinavire, (EM.EtatMajor, "renseigner", renseigner_sans_navires)),
         ("pas de marine", e28_composante_navale, (EM.EtatMajor, "marine", lambda self, ci, camp: ([], []))),
         ("un Kalibr tire hors de portée", e28_composante_navale, (EM.EtatMajor, "_p", portee_nav_nulle)),
         ("la décision du chef n'est pas appliquée", e27_chef_qwen, (CQ.ChefQwen, "appliquer", lambda self: None)),
         ("le chef dépasse ses bornes", e27_chef_qwen, (CQ, "MULT_MAX", 5.0)),
         ("l'état-major n'apprend rien de ses pertes", e26_apprentissage_des_forces, (EM.EtatMajor, "apprendre_forces", lambda self, camp: None)),
         ("le moteur n'engage rien", e25_generation_de_force, (EM.EtatMajor, "engager", lambda self, camp: [])),
         ("la menace n'est pas lue", e25_generation_de_force, (EM, "PORTEE_MENACE_AIR_KM", 0.0)),
         ("pas de reconnaissance", e23_reconnaissance, (EM, "SOUTIEN", {k: v for k, v in EM.SOUTIEN.items() if k != "reco"}))]
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
