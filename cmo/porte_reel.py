#!/usr/bin/env python3
"""porte_reel — les outils v8 du pont ( guerre réelle, 02/10 ) face à faux_cmo : remplir et relire un dépôt, importer une
vraie installation et la numéroter, lire pertes et dépenses, régler la doctrine, lire les dégâts, poser un véhicule,
relever les seules unités mobiles. Chaque mutant retire une règle ; la porte doit alors échouer.

    .venv312/bin/python cmo/porte_reel.py [--controles]
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
import porte_cmo as P                                     # noqa: E402
from faux_cmo import FauxCMO                              # noqa: E402

CAMPS = ("OTAN", "Russie-Chine")
BASE_TEST = "Test/Base Reelle 2024.inst"
INSTALLATIONS = ("Lithuania/Siauliai Air Base 2024.inst", BASE_TEST)
# Une vraie base de papier : une piste, deux dépôts de munitions, une cuve ( dbid de la DB3000 ).
MEMBRES = [(757, "Runway (4000m)", 55.89, 23.39), (322, "Ammo Bunker (Surface)", 55.891, 23.392),
           (322, "Ammo Bunker (Surface)", 55.892, 23.393), (942, "AvGas (750k Liter Underground Tank)", 55.888, 23.388)]
F16_7453 = [(897, 4), (945, 2), (1763, 2)]               # 4 AIM-120C-5, 2 AIM-9X, 2 réservoirs ( DB3000 )


@contextlib.contextmanager
def banc(installations=INSTALLATIONS, labo_installations=None):
    racine = tempfile.mkdtemp(prefix="porte_reel_")
    etat = os.path.join(racine, "etat")
    f = FauxCMO(racine, camps=CAMPS, installations=installations)
    try:
        f.installer()
        f.lua("FAUX.loadouts[7453] = { " + ", ".join(f"{{ {w}, {n} }}" for w, n in F16_7453) + " }")
        f.lua(f"FAUX.fichiers_inst['{BASE_TEST}'] = {{ "
              + ", ".join(f"{{ {d}, '{n}', {la}, {lo} }}" for d, n, la, lo in MEMBRES) + " }")
        f.demarrer()
        CL.certifier("1.10.1900.20", {"porte": True}, etat)
        l = CL.Labo(pont=f.pont, sortie=f.sortie, etat=etat, camps=CAMPS,
                    installations=installations if labo_installations is None else labo_installations, **P.RAPIDE)
        l.ouvrir()
        try:
            yield f, l
        finally:
            l.fermer()
        if f.erreurs:
            raise AssertionError(f"HMT_tic a levé : {f.erreurs[:2]}")
    finally:
        f.arreter()
        shutil.rmtree(racine, ignore_errors=True)


def r1_armer_puis_relire_le_depot():
    """Quatre packs du chargement du F-16 : 16 AIM-120C-5, 8 AIM-9X, 8 réservoirs, relus dans le magasin."""
    with banc() as (f, l):
        l.poser("OTAN", "site", 1712, 90_000_001, 52.3, 17.3)
        r = l.armer([(90_000_001, 7453, 4)])
        assert r["armes"] == {90_000_001: 3}, r
        st = l.stocks([90_000_001])["stocks"][90_000_001]
        assert {w: c for w, (c, _) in st.items()} == {897: 16, 945: 8, 1763: 8}, st
        l.armer([(90_000_001, 7453, 1)])
        assert l.stocks([90_000_001])["stocks"][90_000_001][897][0] == 20


def r2_importer_et_numeroter_une_vraie_base():
    """Import d'une vraie installation, numérotation HMT ; le registre la retrouve après un rechargement du scénario."""
    with banc() as (f, l):
        assert l.importer("OTAN", BASE_TEST)["elements"] == len(MEMBRES)
        time.sleep(0.1)
        el = l.adopter("OTAN", 90_100_001)["elements"]
        assert len(el) == len(MEMBRES) + 1 and sum(1 for e in el if e[4]) == 1, el
        assert sorted(e[1] for e in el if not e[4]) == sorted(d for d, *_ in MEMBRES)
        f.recharger()                                    # les globales Lua tombent : le registre se refait par les noms
        time.sleep(0.1)
        depots = [e[0] for e in el if e[1] == 322]
        r = l.armer([(k, 7453, 2) for k in depots])
        assert sorted(r["armes"]) == sorted(depots) and not r["absents"], r
        assert l.etats([e[0] for e in el])["absents"] == []


def r3_pertes_et_depenses_de_cmo():
    """Les pertes et dépenses que CMO compte, par type et dbid ( avions et installations ne se confondent pas )."""
    with banc() as (f, l):
        f.lua("FAUX.bilans['OTAN'] = { losses = { { type = 'Aircraft', dbid = 7087, count = 3 }, "
              "{ type = 'Facility', dbid = 7087, count = 1 } }, expenditures = { { type = 'Weapon', dbid = 897, count = 12 } } }")
        b = l.bilan("OTAN")
        assert b["pertes"] == {("avion", 7087): 3, ("installation", 7087): 1}, b
        assert b["depenses"] == {("arme", 897): 12}, b
        assert l.bilan("Russie-Chine")["pertes"] == {}


def r4_doctrine_ecrite_et_relue():
    with banc() as (f, l):
        assert l.doctrine("OTAN", "quick_turnaround_for_aircraft", 0)["valeur"] == 0
        assert l.doctrine("OTAN", "air_operations_tempo", 0)["valeur"] == 0
        assert f.lua("return FAUX.doctrines['OTAN'].quick_turnaround_for_aircraft") == 0
        P.leve(CL.Refus, l.doctrine, "OTAN", "io_open", 1)


def r5_meme_liste_d_installations_des_deux_cotes():
    """Un index n'a de sens que si CMO et le module ont la même liste : sinon l'ouverture refuse."""
    with banc(labo_installations=(BASE_TEST,)) as (f, l):
        raise AssertionError("le labo s'est ouvert avec une autre liste d'installations que CMO")


def r6_releve_borne_aux_unites_mobiles():
    """positions( mini, maxi ) ne relève que les numéros demandés : les milliers d'éléments fixes restent dehors."""
    with banc() as (f, l):
        l.poser("OTAN", "site", 1712, 90_000_001, 52.3, 17.3)
        l.poser("OTAN", "air", 7087, 10_100_001, 52.3, 17.3, alt=8000, loadout=7453)
        l.poser("OTAN", "vehicule", 102, 20_000_001, 52.4, 17.3)
        p = l.positions(10_000_000, 29_999_999)
        assert sorted(k for k, *_ in p["vivants"]["OTAN"]) == [10_100_001, 20_000_001], p
        f.detruire(90_000_001)
        f.detruire(20_000_001)
        p = l.positions(10_000_000, 29_999_999)
        assert p["morts"]["OTAN"] == [20_000_001], p        # la base détruite n'est pas dans le relevé borné


def r7_degats_relus():
    """Les dégâts relus, y compris quand CMO rend le pourcentage en texte à la virgule ( « 99,9 » ) : calculés des points
    restants ( 02/10 : six points d'accès de Šiauliai détruits à 99,9 % lus 0 )."""
    with banc() as (f, l):
        l.poser("OTAN", "site", 1712, 90_000_001, 52.3, 17.3)
        l.poser("OTAN", "site", 353, 90_000_003, 52.31, 17.3)
        f.lua("FAUX_endommager(90000001, 40, true)")
        f.lua("FAUX_endommager_cmo(90000003, 1.0, 1000)")
        e = l.etats([90_000_001, 90_000_002, 90_000_003])
        assert e["etats"][90_000_001] == (40, True, False) and e["absents"] == [90_000_002], e
        assert abs(e["etats"][90_000_003][0] - 99.9) < 0.01, e


def r8_table_rase_avec_une_vraie_base():
    """La table rase emporte aussi une base importée ( éléments puis groupe ), et le recompte le prouve."""
    with banc() as (f, l):
        l.importer("OTAN", BASE_TEST)
        time.sleep(0.1)
        l.adopter("OTAN", 90_100_001)
        assert l.nettoyer()["avant"] == len(MEMBRES) + 1
        assert f.compter() == 0


def r9_table_rase_des_orphelins():
    """Un import interrompu avant l'adoption laisse des unités non HMT dans nos camps : la table rase les emporte aussi
    ( 02/10 : 111 éléments de 4 bases construites restés invisibles ), et laisse les fantômes."""
    with banc() as (f, l):
        l.importer("Russie-Chine", BASE_TEST)
        time.sleep(0.1)
        assert f.compter() == len(MEMBRES) + 1
        assert l.nettoyer()["avant"] == len(MEMBRES) + 1
        assert f.compter() == 0


def r10_frappe_activee_et_ciblee():
    """Une frappe naît active et en vols de deux, ses cibles sont des unités ennemies ( une cible amie est refusée ), et
    l'avion affecté rejoint sa cible ( le faux CMO, comme CMO, laisse au parking un avion d'une frappe « OnHold » )."""
    with banc() as (f, l):
        l.poser("Russie-Chine", "site", 325, 92_000_001, 54.70, 20.40)
        l.poser("OTAN", "site", 1712, 90_000_001, 54.03, 19.13)
        l.poser_base_lots([("OTAN", 7087, 7492, 90_000_001, [10_100_001, 10_100_002])])
        r = l.frappes([(1, "OTAN", [92_000_001, 90_000_001])], [(1, [10_100_001, 10_100_002])])
        assert r["frappes"] == [(1, True, 1)] and r["cibles"] == [92_000_001] and r["refus"] == [90_000_001], r
        assert sorted(r["affectes"]) == [10_100_001, 10_100_002], r
        assert f.lua("return FAUX.missions['OTAN/HMT-F1'].Phase") == 20
        time.sleep(0.2)
        p = l.positions(10_000_000, 29_999_999)["vivants"]["OTAN"]
        assert all(abs(la - 54.70) < 1e-6 and a > 500 for _, la, _, a in p), p


def r11_appels_en_paquets():
    """450 numéros d'un coup ( dégâts, stocks ) : le module découpe en appels de ARGS_MAX valeurs ( 02/10 : 300 numéros
    en un appel ne compilaient pas, « too many registers » ), et tout revient."""
    with banc() as (f, l):
        l.poser_lot("OTAN", "site", 1712, [(90_000_001 + i, 52.0 + i * 0.001, 17.0) for i in range(150)])
        ks = list(range(90_000_001, 90_000_451))
        e = l.etats(ks)
        assert len(e["etats"]) == 150 and len(e["absents"]) == 300, (len(e["etats"]), len(e["absents"]))
        assert len(l.stocks(ks)["absents"]) == 300


def r12_registre_refait_a_l_ouverture():
    """Un registre gardé d'une partie précédente ( les globales Lua survivent au rechargement, et une installation
    réimportée reprend les mêmes guid ) ne doit pas bloquer l'adoption : l'ouverture du labo refait le registre."""
    with banc() as (f, l):
        l.importer("OTAN", BASE_TEST)
        time.sleep(0.1)
        f.lua("local g for k, u in pairs(FAUX.unites) do if u.type == 'Facility' then g = k end end "
              "HMT_unites = HMT_unites or {} HMT_unites[90100001] = { guid = g, camp = 1 }")
        l.fermer()
        l.ouvrir()
        assert len(l.adopter("OTAN", 90_100_001)["elements"]) == len(MEMBRES) + 1


TESTS = [r1_armer_puis_relire_le_depot, r2_importer_et_numeroter_une_vraie_base, r3_pertes_et_depenses_de_cmo,
         r4_doctrine_ecrite_et_relue, r6_releve_borne_aux_unites_mobiles, r7_degats_relus, r8_table_rase_avec_une_vraie_base, r9_table_rase_des_orphelins,
         r10_frappe_activee_et_ciblee, r11_appels_en_paquets, r12_registre_refait_a_l_ouverture]


def r5_test():
    try:
        r5_meme_liste_d_installations_des_deux_cotes()
    except CL.Incomplet as e:
        assert "installations" in str(e), e
        return
    raise AssertionError("aucun refus")


r5_test.__name__ = "r5_meme_liste_d_installations_des_deux_cotes"
TESTS.insert(4, r5_test)


def controles():
    """Chaque mutant se pose dans le Lua du faux CMO après l'installation ( ou dans le module ) ; la porte doit échouer."""
    global banc
    rates, vrai_banc = [], banc

    def banc_mute(code_lua):
        @contextlib.contextmanager
        def b(*a, **kw):
            with vrai_banc(*a, **kw) as (f, l):
                f.lua(code_lua)
                yield f, l
        return b

    m = [("l'armement ne remplit pas le dépôt", r1_armer_puis_relire_le_depot,
          "HMT_armer = function(R, k, lo, n) R('ARME', { k, lo, n, 3 }) end"),
         ("l'adoption ne renomme pas", r2_importer_et_numeroter_une_vraie_base, "FAUX.renommer_refuse = true"),
         ("le relevé ignore ses bornes", r6_releve_borne_aux_unites_mobiles,
          "local p = HMT_positions HMT_positions = function(R, a, b) return p(R) end"),
         ("la table rase oublie les groupes", r8_table_rase_avec_une_vraie_base,
          "local d = ScenEdit_DeleteUnit ScenEdit_DeleteUnit = function(t, x) local u = FAUX.unites[t.guid] "
          "if u and u.type == 'Group' then return true end return d(t, x) end"),
         ("la frappe reste en attente", r10_frappe_activee_et_ciblee,
          "local g = ScenEdit_GetMission ScenEdit_GetMission = function(s, n) local m = g(s, n) if m == nil then return nil end "
          "return setmetatable({}, {__index = m, __newindex = function() end}) end"),
         ("les appels ne sont plus découpés", r11_appels_en_paquets, None),
         ("le pourcentage à la virgule lu comme 0", r7_degats_relus,
          "local e = HMT_etats HMT_etats = function(R, ...) for _, k in ipairs({...}) do local x = HMT_recenser()[k] "
          "local u = x and ScenEdit_GetUnit({guid = x.guid}) if u == nil then R('ABSENT', {k}) else local d = u.damage "
          "R('ETAT', {k, tonumber(d.dp_percent_now) or 0, (d.fires ~= 'NoFire') and 1 or 0, 0}) end end end"),
         ("l'ouverture garde le vieux registre", r12_registre_refait_a_l_ouverture,
          "local r = HMT_recenser HMT_recensement = function(R) R('RECENSE', { 0 }) end"),
         ("la table rase ignore les orphelins", r9_table_rase_des_orphelins,
          "local v = VP_GetSide VP_GetSide = function(t) local s = v(t) local us = {} for _, x in ipairs(s.units) do "
          "if string.match(x.name or '', '^HMT') then us[#us + 1] = x end end s.units = us return s end")]
    for nom, test, code in m:
        if code is None:                                 # mutant du module, pas du Lua
            with P.mutant(CL, "ARGS_MAX", 100_000):
                try:
                    test()
                    rates.append(nom)
                    print(f"  RATÉ   mutant « {nom} » : {test.__name__} passe encore", flush=True)
                except Exception as e:
                    print(f"  TUÉ    mutant « {nom} » par {test.__name__} ({type(e).__name__})", flush=True)
            continue
        banc = banc_mute(code)
        try:
            test()
            rates.append(nom)
            print(f"  RATÉ   mutant « {nom} » : {test.__name__} passe encore", flush=True)
        except Exception as e:
            print(f"  TUÉ    mutant « {nom} » par {test.__name__} ({type(e).__name__})", flush=True)
        finally:
            banc = vrai_banc
    with P.mutant(CL.Labo, "_verifier_installations", lambda self, r: None):
        try:
            r5_test()
            rates.append("la liste d'installations n'est plus vérifiée")
            print("  RATÉ   mutant « liste d'installations non vérifiée » : r5 passe encore", flush=True)
        except Exception as e:
            print(f"  TUÉ    mutant « liste d'installations non vérifiée » par r5 ({type(e).__name__})", flush=True)
    controles.n = len(m) + 1
    return rates


if __name__ == "__main__":
    print("porte_reel : les outils v8 du pont face à faux_cmo")
    e = P.passer(TESTS)
    print(f"{len(TESTS) - len(e)}/{len(TESTS)} tests passent")
    if "--controles" in sys.argv:
        r = controles()
        print(f"{controles.n - len(r)}/{controles.n} mutants tués")
        sys.exit(1 if e or r else 0)
    sys.exit(1 if e else 0)
