#!/usr/bin/env python3
"""sonde_sol — deuxième sonde du palier 0 ( 02/10, aval de Younes : « la totale, troupes au sol » ). Dans un camp
JETABLE ( HMT-SONDE, retiré à la fin avec tout ce qu'il contient ) :

  1. LES TROUPES AU SOL de la base DB3000 sont des installations MOBILES ( catégorie 5001 ) : pelotons de chars, sections
     mécanisées, batteries d'artillerie, bataillons S-400 et Iskander. Les poser ( type Facility ), lire leurs magasins
     et armes, leur donner une route et voir si elles roulent.
  2. LES VÉHICULES SEULS ( DataGroundUnit, ex. T-72B3 = 102 ) : quel « type » ScenEdit_AddUnit accepte-t-il ?
  3. UN MAGASIN REMPLI, lu en entier ( contenu de mag_weapons ), et les pertes et dépenses d'un camp.

    .venv312/bin/python cmo/sonde_sol.py
"""
import json
import os
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402

LIEU = (52.60, 17.80)                                     # Pologne centrale, loin du théâtre
SOL = {"S400": 1937, "ISKANDER": 254, "T90": 1918, "BMP3": 2045, "MSTA": 1953, "KRAB": 2048}
TYPES_VEHICULE = ["Ground", "GroundUnit", "Land", "LandUnit", "Vehicle", "Mobile", "Army", "Unit"]
PRELUDE = S0.PRELUDE.replace("if prof > 3 then", "if prof > 6 then")
CHAMPS_SOL = ["name", "type", "subtype", "dbid", "classname", "category", "latitude", "longitude", "speed", "heading",
              "throttle", "unitstate", "condition", "course", "mounts", "magazines", "damage", "sensors", "fuel"]


def etapes():
    d = 0.0
    for nom, dbid in SOL.items():
        d += 0.05
        yield f"pose_{nom}", (f"SORTIE('pose_{nom}', ESSAI(function() local u = ScenEdit_AddUnit({{side = 'HMT-SONDE', "
                              f"type = 'Facility', unitname = 'SOL-{nom}', dbid = {dbid}, latitude = {LIEU[0] + d}, "
                              f"longitude = {LIEU[1]}}}) return u and u.guid end))")
    for nom in SOL:
        yield f"lu_{nom}", (f"local u = ScenEdit_GetUnit({{side = 'HMT-SONDE', unitname = 'SOL-{nom}'}}) "
                            f"SORTIE('lu_{nom}', u and CHAMPS(u, {S0.lua_liste(CHAMPS_SOL)}) or 'absent')")
    for t in TYPES_VEHICULE:
        yield f"vehicule_{t}", (f"SORTIE('vehicule_{t}', ESSAI(function() local u = ScenEdit_AddUnit({{side = 'HMT-SONDE', "
                                f"type = '{t}', unitname = 'VEH-{t}', dbid = 102, latitude = {LIEU[0] - 0.1}, "
                                f"longitude = {LIEU[1]}}}) return u and (u.type .. ' ' .. tostring(u.dbid) .. ' ' .. tostring(u.classname)) end))")
    # Rouler : une route à 5 km à l'est pour le peloton de chars ; la position se relit 60 s plus tard ( relire_route ).
    yield "route_T90", (f"SORTIE('route_T90', ESSAI(ScenEdit_SetUnit, {{side = 'HMT-SONDE', unitname = 'SOL-T90', "
                        f"course = {{{{latitude = {LIEU[0] + 0.15}, longitude = {LIEU[1] + 0.075}, TypeOf = 'ManualPlottedCourseWaypoint'}}}}}}))")
    # Un magasin rempli, lu en entier : un aérodrome générique et quatre chargements de F-16.
    yield "aerodrome", (f"SORTIE('aerodrome', ESSAI(function() local u = ScenEdit_AddUnit({{side = 'HMT-SONDE', type = 'Facility', "
                        f"unitname = 'SOL-AERODROME', dbid = 1712, latitude = {LIEU[0] - 0.3}, longitude = {LIEU[1]}}}) "
                        f"return ScenEdit_FillMagsForLoadout({{guid = u.guid, loadoutid = 7453, quantity = 4}}) end))")
    yield "magasin_plein", ("local u = ScenEdit_GetUnit({side = 'HMT-SONDE', unitname = 'SOL-AERODROME'}) "
                            "SORTIE('magasin_plein', D(u.magazines))")
    yield "pertes_depenses", ("local s = VP_GetSide({side = HMT_CAMPS[1]}) SORTIE('pertes_depenses', 'pertes ' .. "
                              "ESSAI(function() return s.losses end) .. '\\nDEPENSES ' .. ESSAI(function() return s.expenditures end))")


def sonder(labo_kw=None, dossier=None, attente_route=60.0):
    labo_kw = dict(labo_kw or {})
    dossier = dossier or os.path.join(CL.ETAT, "cmo_sondes", time.strftime("sol_%Y%m%d_%H%M%S"))
    os.makedirs(dossier, exist_ok=True)
    sortie = labo_kw.get("sortie", CL.SORTIE)
    camps = labo_kw.pop("camps", ("OTAN", "Russie-Chine"))
    res = {}

    def une(labo, nom, corps):
        chemin = os.path.join(sortie, f"hmt_sonde_{nom}.inst")
        if os.path.exists(chemin):
            os.remove(chemin)
        try:
            labo.lua(PRELUDE + corps, par_humain=True, patience=30)
            texte = S0.lire_sonde(sortie, nom)
        except CL.ErreurLabo as e:
            texte = f"ECHEC {type(e).__name__}: {e}"
        res[nom] = texte
        with open(os.path.join(dossier, f"{nom}.txt"), "w") as g:
            g.write(texte or "AUCUN FICHIER")
        print(f"--- {nom}\n{(texte or 'AUCUN FICHIER')[:500]}", flush=True)

    with CL.Labo(camps=camps, **labo_kw) as labo:
        une(labo, "camp_sonde", "SORTIE('camp_sonde', ESSAI(function() return ScenEdit_AddSide({side = 'HMT-SONDE'}).name end))")
        for nom, corps in etapes():
            une(labo, nom, corps)
        time.sleep(attente_route)
        une(labo, "relire_route", ("local u = ScenEdit_GetUnit({side = 'HMT-SONDE', unitname = 'SOL-T90'}) "
                                   "SORTIE('relire_route', u and CHAMPS(u, {'latitude', 'longitude', 'speed', 'throttle', 'unitstate'}) or 'absent')"))
        une(labo, "retirer_sonde", "SORTIE('retirer_sonde', ESSAI(function() return ScenEdit_RemoveSide({side = 'HMT-SONDE'}) ~= nil end))")
        une(labo, "camps_apres", "local t = {} for _, s in ipairs(VP_GetSides()) do t[#t + 1] = s.name end SORTIE('camps_apres', table.concat(t, ', '))")
    with open(os.path.join(dossier, "sonde.json"), "w") as g:
        json.dump(res, g, ensure_ascii=False, indent=1)
    return dossier, res


if __name__ == "__main__":
    d, _ = sonder()
    print(f"sondes écrites dans {d}")
