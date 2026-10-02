#!/usr/bin/env python3
"""porte_cmo — le pont CMO hors du jeu : le VRAI Lua ( hmt_pont.lua, installer.lua ) face à faux_cmo, et le vrai
cmo_labo.py de l'autre côté. Chaque garde a son test, isolé : une garde masquée par une autre ne compte pas
( leçon du labo Arma, 11/09 : 3 casses volontaires sur 5 survivaient ).

Contrôles négatifs ( --controles ) : trois mutants retirent chacun une garde ; la porte doit alors ÉCHOUER sur le test
de cette garde. Un mutant qui passe = un test qui ne sait pas échouer.

    .venv/bin/python cmo/porte_cmo.py [--controles]
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
from faux_cmo import FauxCMO                              # noqa: E402

RAPIDE = dict(battement_max=1.0, patience=1.5, patience_ouverture=2.0)


@contextlib.contextmanager
def banc(build="v1.10 - Build 1900.20", certifie="1.10.1900.20", strict=True, labo=True, **faux):
    racine = tempfile.mkdtemp(prefix="porte_cmo_")
    etat = os.path.join(racine, "etat")
    f = FauxCMO(racine, build=build, **faux)
    try:
        f.installer()
        f.demarrer()
        if certifie:
            CL.certifier(certifie, {"porte": True}, etat)
        if not labo:
            yield f, None
            return
        l = CL.Labo(pont=f.pont, sortie=f.sortie, etat=etat, strict=strict, **RAPIDE)
        l.ouvrir()
        try:
            yield f, l
        finally:
            l.fermer()
        if f.erreurs:
            raise AssertionError(f"HMT_tic a levé dans le faux CMO : {f.erreurs[:2]}")
    finally:
        f.arreter()
        shutil.rmtree(racine, ignore_errors=True)


def leve(exc, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except exc as e:
        return e
    raise AssertionError(f"{exc.__name__} attendue, rien n'a été levé")


# --- LES TESTS ---------------------------------------------------------------------------------------------------------
def p0_accords():
    """Le Lua et le Python disent la même chose : version, camps, genres, action de l'événement."""
    from lupa import lua54
    L = lua54.LuaRuntime(unpack_returned_tuples=True)
    L.execute(open(os.path.join(ICI, "lua", "hmt_pont.lua"), encoding="utf-8").read())
    g = L.globals()
    assert g.HMT_VERSION == CL.VERSION_LUA, (g.HMT_VERSION, CL.VERSION_LUA)
    assert tuple(g.HMT_CAMPS.values()) == CL.CAMPS, tuple(g.HMT_CAMPS.values())
    assert len(g.HMT_GENRES) == len(CL.GENRES)
    inst = open(os.path.join(ICI, "lua", "installer.lua"), encoding="utf-8").read()
    assert f'local SCRIPT = "{CL.ACTION_EVENEMENT}"' in inst, "ACTION_EVENEMENT diffère de SCRIPT dans installer.lua"
    for f in ("hmt_pont.lua", "installer.lua", "faux_cmo.lua"):
        ok, err = L.eval("function(s) local f, e = load(s) return f ~= nil, e end")(
            open(os.path.join(ICI, "lua", f), encoding="utf-8").read())
        assert ok, (f, err)


def p1_installer():
    """Un seul événement, déclencheur RegularTime '0' ( 1 s ), l'action exacte ; réinstaller ne double rien."""
    with banc(labo=False) as (f, _):
        f.installer()
        ev = f.lua("local t = {} for _, e in ipairs(FAUX.evenements) do t[#t+1] = e.name end return table.concat(t, ',')")
        assert ev == "HMT_PONT", ev
        assert f.lua("return FAUX.declencheurs['HMT_PONT_1s'].Interval") == "0"
        assert f.lua("return FAUX.actions['HMT_PONT_tic'].ScriptText") == CL.ACTION_EVENEMENT
        camps = f.lua("local t = {} for _, s in ipairs(FAUX.camps) do t[#t+1] = s.name end return table.concat(t, ',')")
        assert camps == ",".join(CL.CAMPS), camps
        assert CL.lire_inst(os.path.join(f.sortie, "hmt_sonde.inst")).startswith("SONDE ")


def p2_canaris():
    """100 canaris, 0 perte, version et build lus dans le jeu."""
    with banc() as (f, l):
        coeurs = []
        for _ in range(100):
            c = l.canari()
            coeurs.append(c["recu"]["coeur"])
        assert all(a < b for a, b in zip(coeurs, coeurs[1:])), "deux commandes dans le même passage"
        assert c["version_lua"] == CL.VERSION_LUA and c["build"] == "1.10.1900.20" and c["lecteur"] == "loadfile", c


def p3_poser_etat_positions():
    with banc() as (f, l):
        for k in range(1, 9):
            l.poser("Stratis" if k % 2 else "Malden", "air", 3500, k, 37.5 + k / 100, 24.3, 6000, 16934)
        e = l.etat_camps()["camps"]
        assert e["Stratis"]["hmt_vivants"] == 4 and e["Malden"]["hmt_vivants"] == 4, e
        p = l.positions()
        assert sorted(k for c in p["vivants"].values() for k, *_ in c) == list(range(1, 9)), p
        l.aller(3, 38.0, 25.0)
        u3 = [u for u in l.positions()["vivants"]["Stratis"] if u[0] == 3][0]
        assert abs(u3[1] - 38.0) < 1e-6 and abs(u3[2] - 25.0) < 1e-6, u3


def p4_morts_une_fois():
    with banc() as (f, l):
        for k in (1, 2, 3):
            l.poser("Malden", "air", 3500, k, 37.5, 24.3, 6000)
        f.detruire(2)
        p = l.positions()
        assert p["morts"]["Malden"] == [2] and [u[0] for u in p["vivants"]["Malden"]] == [1, 3], p
        assert l.positions()["morts"]["Malden"] == [], "un mort rendu deux fois serait compté deux fois par le moteur"


def p5_erreur_lua_certaine():
    """Une erreur au MILIEU du corps : EchecLua avec le message, et aucune ligne rendue ; le pont continue."""
    with banc() as (f, l):
        e = leve(CL.EchecLua, l.lua, "R('AVANT', {1}) error('boum') R('APRES', {2})", par_humain=True)
        assert "boum" in str(e), e
        assert l.canari()["pont"] == "vivant"


def p6_refus_deux_etages():
    with banc() as (f, l):
        leve(CL.Refus, l.poser, "Altis", "air", 3500, 1, 37.5, 24.3)      # refusé en Python : rien n'est écrit
        assert not os.listdir(f.pont) or all(not x.startswith("cmd_") for x in os.listdir(f.pont))
        l.poser("Malden", "air", 3500, 1, 37.5, 24.3, 6000)
        e = leve(CL.Refus, l.poser, "Stratis", "air", 3500, 1, 37.6, 24.3, 6000)   # refusé dans le Lua
        assert "déjà tenu" in str(e), e
        f.regler(dbid_refuse=4242)
        assert "refuse d'ajouter" in str(leve(CL.Refus, l.poser, "Malden", "air", 4242, 2, 37.5, 24.3, 6000))


def p7_compilation():
    """Avec lupa : refusé avant d'écrire. Sans : le Lua de CMO le dit ( code 2 ), et le pont continue."""
    with banc() as (f, l):
        leve(CL.Refus, l.lua, "R('X', {1}", par_humain=True)
        l.liaison.compiler = None
        e = leve(CL.EchecLua, l.lua, "R('X', {1}", par_humain=True)
        assert "ne compile pas" in str(e), e
        assert l.canari()["pont"] == "vivant"


def abandonner(f, l, fn, *a):
    """Met le jeu en pause JUSTE APRÈS un battement : la commande PART ( battement frais ), puis n'est jamais prise.
    ⚠️ Une pause suivie d'une attente ferait refuser l'envoi faute de battement : la commande ne serait jamais
    écrite, et les gardes d'abandon ne seraient pas exercées ( les contrôles négatifs l'ont montré le 28/09 )."""
    l.canari()
    f.pause()
    with f.verrou:                                       # le passage en cours, s'il y en a un, est fini
        pass
    return leve(CL.PontMort, fn, *a)


def p8_pause_jamais_aucun():
    """Jeu en pause pendant une commande : PontMort, jamais un résultat vide ; et la commande est effacée."""
    with banc() as (f, l):
        e = abandonner(f, l, l.positions)
        assert "sans reçu" in str(e), e                  # la commande est bien partie avant la pause
        assert not [x for x in os.listdir(f.pont) if x.startswith("cmd_")], os.listdir(f.pont)


def p9_rechargement_recalage():
    """Scénario rechargé : HMT_n repart à 0, le registre se refait par les noms HMT-<n>, le module se recale."""
    with banc() as (f, l):
        for k in (1, 2):
            l.poser("Stratis", "air", 3500, k, 37.5, 24.3, 6000)
        for _ in range(5):
            l.canari()
        f.recharger()
        time.sleep(0.3)
        c = l.canari()
        assert c["recu"]["n_cmd"] == 1, c["recu"]
        assert [u[0] for u in l.positions()["vivants"]["Stratis"]] == [1, 2]


def p10_un_seul_ecrivain():
    with banc() as (f, l):
        l2 = CL.Labo(pont=f.pont, sortie=f.sortie, etat=l.etat, **RAPIDE)
        leve(CL.Occupe, l2.ouvrir)


def p11_recu_ecrit_lentement():
    """Un reçu lu pendant que CMO l'écrit n'est pas une réponse : on attend le JSON complet."""
    with banc(ecriture_lente=0.15) as (f, l):
        for k in range(1, 4):
            l.poser("Malden", "air", 3500, k, 37.5, 24.3, 6000)
        assert len(l.positions()["vivants"]["Malden"]) == 3


def p12_que_des_nombres():
    with banc() as (f, l):
        assert "non numérique" in str(leve(CL.EchecLua, l.lua, "R('X', {'abc'})", par_humain=True))
        assert "clé invalide" in str(leve(CL.EchecLua, l.lua, "R('x y', {1})", par_humain=True))


def p13_build_non_certifie():
    """Steam a mis CMO à jour : refusé en strict, accepté ( et dit ) pour le banc."""
    with banc(labo=False, build="v1.10 - Build 1900.21") as (f, _):
        etat = os.path.join(f.racine, "etat")
        l = CL.Labo(pont=f.pont, sortie=f.sortie, etat=etat, strict=True, **RAPIDE)
        assert "Steam a mis CMO à jour" in str(leve(CL.Incomplet, l.ouvrir))
        assert not l.ecrivain.pris, "un refus à l'ouverture doit rendre le verrou"
        with CL.Labo(pont=f.pont, sortie=f.sortie, etat=etat, strict=False, **RAPIDE) as l2:
            assert l2.version["build"] == "1.10.1900.21" and l2.version["build_certifie"] == "1.10.1900.20"


def p14_lecteur_runscript():
    """Si le bac à sable retire loadfile, RunScript prend le relais."""
    with banc(lecteur="runscript") as (f, l):
        assert l.canari()["lecteur"] == "RunScript"
        l.poser("Stratis", "air", 3500, 1, 37.5, 24.3, 6000)
        assert l.etat_camps()["camps"]["Stratis"]["hmt_vivants"] == 1


def p14b_runscript_qui_leve():
    """Le bac à sable de la 1.10 ( sonde du 28/09 : ni loadfile, ni dofile, ni load ), et un RunScript qui lève sur un
    fichier absent : l'actuateur ne doit pas avancer d'un numéro à chaque seconde."""
    with banc(lecteur="runscript_leve") as (f, l):
        time.sleep(0.5)                                  # une dizaine de passages sans commande
        # ouverture = canari ( 1 ) + recensement du registre ( 2, depuis le 02/10 ) ; ce canari est donc la commande 3
        assert l.canari()["recu"]["n_cmd"] == 3, "l'actuateur a sauté des numéros sur des fichiers absents"
        l.poser("Malden", "air", 3500, 1, 37.5, 24.3, 6000)
        assert l.etat_camps()["camps"]["Malden"]["hmt_vivants"] == 1


def p15_commande_non_prise_effacee():
    """Pause, commande abandonnée, reprise : la commande ne joue PAS au réveil."""
    with banc() as (f, l):
        e = abandonner(f, l, l.poser, "Malden", "air", 3500, 9, 37.5, 24.3, 6000)
        assert "sans reçu" in str(e), e
        f.reprendre()
        time.sleep(0.5)
        assert f.compter() == 0, "la commande abandonnée a joué au réveil"
        assert l.canari()["pont"] == "vivant"


def p16_gros_recu():
    with banc() as (f, l):
        r = l.lua("for i = 1, 3000 do R('X', {i, i / 7}) end", par_humain=True)
        assert len(r["lignes"]) == 3000 and r["lignes"][-1]["nombres"][0] == 3000


def p17_recu_tronque():
    """CMO coupe le champ Comments : Incomplet tout de suite, et le pont se recale pour la suite."""
    with banc() as (f, l):
        f.tronquer = 40
        e = leve(CL.Incomplet, l.lua, "for i = 1, 50 do R('X', {i}) end", par_humain=True)
        assert "tronqué" in str(e), e
        f.tronquer = 0
        assert l.canari()["pont"] == "vivant"


def p18_nettoyer_prouve():
    with banc() as (f, l):
        for k in range(1, 6):
            l.poser("Stratis", "air", 3500, k, 37.5, 24.3, 6000)
        r = l.nettoyer()
        assert r["avant"] == 5 and r["apres"] == 0, r
        assert f.compter() == 0


def p19_poser_apres_nettoyer():
    """La suppression est différée d'un passage ( CMO 1.10 ) : après une table rase prouvée, les mêmes numéros se
    reposent sans refus."""
    with banc() as (f, l):
        for k in (1, 2, 3):
            l.poser("Malden", "air", 3500, k, 37.5, 24.3, 6000)
        assert l.nettoyer()["avant"] == 3
        for k in (1, 2, 3):
            l.poser("Stratis", "air", 3500, k, 37.6, 24.3, 6000)
        assert l.etat_camps()["camps"]["Stratis"]["hmt_vivants"] == 3


def p20_recharger_sans_console():
    """CMO joue un ancien Lua : l'ouverture le refuse, recharger() le fait relire par le pont, l'ouverture passe."""
    with banc(labo=False) as (f, _):
        etat = os.path.join(f.racine, "etat")
        f.lua("HMT_VERSION = 1")
        assert "version 1" in str(leve(CL.Incomplet, CL.Labo(pont=f.pont, sortie=f.sortie, etat=etat, **RAPIDE).ouvrir))
        kw = {k: v for k, v in RAPIDE.items() if k != "patience_ouverture"}
        assert CL.recharger(pont=f.pont, sortie=f.sortie, etat=etat, **kw) == CL.VERSION_LUA
        with CL.Labo(pont=f.pont, sortie=f.sortie, etat=etat, **RAPIDE) as l:
            assert l.version["version_lua"] == CL.VERSION_LUA


def p21_hostiles():
    with banc() as (f, l):
        assert l.hostiles("Stratis", "Malden")["hostiles"]
        assert f.lua("return FAUX.postures['Malden>Stratis']") == "H"
        leve(CL.Refus, l.hostiles, "Stratis", "Stratis")


def p22_recu_tardif():
    """Une commande plus longue que la patience ( 500 poses dans CMO, 29/09 ) : le reçu arrive après, c'est une réponse ;
    et une commande vraiment sans reçu reste SansRecu."""
    with banc() as (f, l):
        r = l.lua("local t = os.clock() while os.clock() - t < 2.0 do end R('LENT', {1})", par_humain=True)
        assert r["lignes"] == [{"cle": "LENT", "nombres": [1]}], r
        assert l.canari()["pont"] == "vivant"


def p23_lecture_impossible_nest_pas_une_panne():
    """Toute OSError de lecture ( WSL rend OSError 61 quand Windows écrit le fichier au même instant ) = pas encore
    lisible, jamais une exception qui ferait tomber la guerre."""
    d = tempfile.mkdtemp(prefix="porte_cmo_")
    try:
        assert CL.lire_inst(d) is None                   # un dossier : IsADirectoryError, une OSError
        assert CL.lire_inst(os.path.join(d, "absent.inst")) is None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def p24_patrouilles():
    """Une patrouille créée puis déplacée ( pas recréée ), deux avions affectés, un absent dit ABSENT."""
    with banc() as (f, l):
        l.poser("Stratis", "air", 3500, 1, 37.5, 24.3, 6000)
        l.poser("Stratis", "air", 3500, 2, 37.5, 24.3, 6000)
        r = l.missions([(7, "Stratis", 38.0, 24.5, 3.5)], [(7, [1, 2, 99])])
        assert r["patrouilles"] == [(7, True)] and r["affectes"] == [1, 2] and r["absents"] == [99], r
        r = l.missions([(7, "Stratis", 38.2, 24.6, 3.5)], [])
        assert r["patrouilles"] == [(7, False)], r
        time.sleep(0.2)
        u = [x for x in l.positions()["vivants"]["Stratis"] if x[0] == 1][0]
        assert abs(u[1] - 38.2) < 1e-6 and abs(u[2] - 24.6) < 1e-6, u


def p25_calme_moins_de_runscript():
    """Après 30 passages sans commande, un passage sur dix seulement cherche une commande ( dix fois moins de lignes dans
    LuaHistory ) ; une commande envoyée pendant le calme passe quand même."""
    with banc(lecteur="runscript") as (f, l):
        f.lua("local rs = ScenEdit_RunScript FAUX.rs = 0 ScenEdit_RunScript = function(r) FAUX.rs = FAUX.rs + 1 return rs(r) end")
        time.sleep(4.0)                                  # ~80 passages sans commande
        n = f.lua("return FAUX.rs")
        assert n < 45, f"{n} RunScript en 80 passages de calme"
        assert l.canari()["pont"] == "vivant"


def p26_journal_des_messages():
    with banc() as (f, l):
        chemin = l.journal_messages(202609291200)
        assert chemin.endswith("hmt_messages_202609291200.txt") and f.lua("return FAUX.journal") == "hmt_messages_202609291200.txt"


def p27_camps_du_theatre_et_bases():
    """Les camps d'un théâtre écrits par le déployeur et reconnus par leur signature ; des avions posés sur leur base ;
    une base invalide refuse SES avions sans défaire le reste de la commande."""
    camps = ("OTAN", "Russie-Chine")
    with banc(camps=camps, labo=False) as (f, _):
        etat = os.path.join(f.racine, "etat")
        assert "redéployer" in str(leve(CL.Incomplet, CL.Labo(pont=f.pont, sortie=f.sortie, etat=etat, **RAPIDE).ouvrir))
        with CL.Labo(pont=f.pont, sortie=f.sortie, etat=etat, camps=camps, **RAPIDE) as l:
            l.poser("OTAN", "site", 1712, 90000001, 51.55, 19.18)                  # Łask
            l.poser("Russie-Chine", "site", 1712, 90000002, 54.77, 20.40)          # Tchkalovsk
            r = l.poser_base_lots([("OTAN", 7087, 0, 90000001, [11000001, 11000002]),
                                   ("Russie-Chine", 8333, 0, 90000002, [21000001]),
                                   ("OTAN", 7087, 0, 90000002, [11000003]),        # base de l'autre camp
                                   ("OTAN", 7087, 0, 90000099, [11000004])])       # base inconnue
            assert sorted(r["poses"]) == [11000001, 11000002, 21000001] and r["refus"] == {11000003: 8, 11000004: 7}, r
            u = [x for x in l.positions()["vivants"]["OTAN"] if x[0] == 11000001][0]
            assert abs(u[1] - 51.55) < 1e-6 and abs(u[2] - 19.18) < 1e-6, u     # au sol, sur sa base
            assert f.compter() == 5, f.compter()


TESTS = [p0_accords, p1_installer, p2_canaris, p3_poser_etat_positions, p4_morts_une_fois, p5_erreur_lua_certaine,
         p6_refus_deux_etages, p7_compilation, p8_pause_jamais_aucun, p9_rechargement_recalage, p10_un_seul_ecrivain,
         p11_recu_ecrit_lentement, p12_que_des_nombres, p13_build_non_certifie, p14_lecteur_runscript,
         p14b_runscript_qui_leve, p15_commande_non_prise_effacee, p16_gros_recu, p17_recu_tronque, p18_nettoyer_prouve,
         p19_poser_apres_nettoyer, p20_recharger_sans_console,
         p21_hostiles, p22_recu_tardif, p23_lecture_impossible_nest_pas_une_panne, p24_patrouilles,
         p25_calme_moins_de_runscript, p26_journal_des_messages, p27_camps_du_theatre_et_bases]


def passer(tests):
    echecs = []
    for t in tests:
        t0 = time.monotonic()
        try:
            t()
            print(f"  PASSE  {t.__name__}  ({time.monotonic() - t0:.1f} s)", flush=True)
        except Exception as e:
            echecs.append(t.__name__)
            print(f"  ÉCHOUE {t.__name__} : {type(e).__name__}: {e}", flush=True)
    return echecs


# --- LES CONTRÔLES NÉGATIFS : chaque mutant retire UNE garde, son test doit échouer --------------------------------------
@contextlib.contextmanager
def mutant(obj, nom, valeur):
    ancien = getattr(obj, nom)
    setattr(obj, nom, valeur)
    try:
        yield
    finally:
        setattr(obj, nom, ancien)


def controles():
    ratés = []
    effacer = CL._effacer
    m = [("commande non prise gardée", p15_commande_non_prise_effacee,
          (CL, "_effacer", lambda c: None if c.endswith(".lua") else effacer(c))),
         ("build jamais contrôlé", p13_build_non_certifie, (CL, "build_certifie", lambda etat=None: "1.10.1900.21")),
         ("pas de réponse rendu comme « rien »", p8_pause_jamais_aucun,
          (CL.Liaison, "_diagnostiquer", lambda self, n, c, v: None))]
    for nom, test, (obj, attr, val) in m:
        with mutant(obj, attr, val):
            try:
                test()
                ratés.append(nom)
                print(f"  RATÉ   mutant « {nom} » : {test.__name__} passe encore", flush=True)
            except Exception as e:
                print(f"  TUÉ    mutant « {nom} » par {test.__name__} ({type(e).__name__})", flush=True)
    return ratés


if __name__ == "__main__":
    print("porte_cmo : le Lua du pont face à faux_cmo")
    e = passer(TESTS)
    print(f"{len(TESTS) - len(e)}/{len(TESTS)} tests passent")
    r = []
    if "--controles" in sys.argv:
        print("contrôles négatifs")
        r = controles()
        print(f"{3 - len(r)}/3 mutants tués")
    sys.exit(1 if e or r else 0)
