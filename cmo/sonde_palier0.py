#!/usr/bin/env python3
"""sonde_palier0 — ce que CMO 1.10 ( build 1900.20 ) offre au palier 0 de la guerre des blocs. Demandée par Younes le
02/10 ( « ok go » au plan des paliers ) : trois inconnues avant de coder.

  1. LES MAGASINS. Les aérodromes génériques de la base ont un magasin « Munitions » VIDE ( DB : magasin 1185, 0 arme ) ;
     un avion posé ne peut donc pas se réarmer, et la guerre du 29/09 s'est figée au tour 167. Quelle fonction remplit
     le magasin d'une base, avec quels arguments : ScenEdit_FillMagsForLoadout, ScenEdit_AddWeaponToUnitMagazine ?
  2. LA REMISE EN ÉTAT. Quels champs d'un avion disent s'il vole, s'il se prépare et quand il sera prêt ; quelles clés de
     doctrine portent la rotation rapide ( quick turnaround ) ?
  3. LE BROUILLARD DE GUERRE. Que rend ScenEdit_GetContacts pour un camp ?

Lua BRUT ( par_humain ) dans le scénario HMT, guerre ARRÊTÉE. Chaque sonde écrit son texte dans
ImportExport/hmt_sonde_<nom>.inst ; ce script le recopie dans /mnt/data/hmt/etat/cmo_sondes/palier0_<date>/. Pose une
base et deux avions ( numéros 95 000 001 à 95 000 003 ), puis fait table rase de TOUTES les unités HMT.

    .venv312/bin/python cmo/sonde_palier0.py [--faux <racine>]
"""
import json
import os
import sqlite3
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402

DB = "/mnt/data/hmt/etat/cmo_db/DB3K_519.db3"
BASE, AV1, AV2 = 95_000_001, 95_000_002, 95_000_003
AERODROME = 1712                                          # Single-Unit Airfield ( 1x 2001-2600 m ), magasin vide
F16, LOADOUT = 7087, 7453                                 # F-16CJ Blk 52+, A/A : 4 AIM-120C-5, 2 AIM-9X, 2 réservoirs
LIEU = (52.30, 17.30)                                     # Pologne, loin des drapeaux de la Baltique

# D( v ) : un texte lisible de n'importe quelle valeur Lua ou objet de CMO ( tables triées, 3 niveaux, 80 clés ).
# ESSAI( f, ... ) : « OK <valeurs> » ou « ERR <message> ». SORTIE( nom, texte ) : ImportExport/hmt_sonde_<nom>.inst.
PRELUDE = r"""
local function D(v, prof)
  prof = prof or 0
  local t = type(v)
  if t == 'userdata' then
    local ok, s = pcall(tostring, v)
    local okf, f = pcall(function() return v.fields end)
    return '<objet ' .. (ok and s or '?') .. (okf and f ~= nil and (' champs=' .. D(f, prof + 1)) or '') .. '>'
  end
  if t ~= 'table' then local ok, s = pcall(tostring, v); return ok and s or ('<' .. t .. '>') end
  if prof > 3 then return '{...}' end
  local cles = {}
  for k in pairs(v) do cles[#cles + 1] = k end
  table.sort(cles, function(a, b) return tostring(a) < tostring(b) end)
  local out = {}
  for i, k in ipairs(cles) do
    if i > 80 then out[#out + 1] = '...(' .. #cles .. ' cles)'; break end
    out[#out + 1] = tostring(k) .. '=' .. D(v[k], prof + 1)
  end
  return '{' .. table.concat(out, ', ') .. '}'
end
local function ESSAI(f, ...)
  local r = table.pack(pcall(f, ...))
  if not r[1] then return 'ERR ' .. tostring(r[2]) end
  local t = {}
  for i = 2, r.n do t[#t + 1] = D(r[i]) end
  return 'OK ' .. table.concat(t, ' | ')
end
local function SORTIE(nom, texte)
  local camps = VP_GetSides()
  ScenEdit_ExportInst(camps[1].name, {}, { filename = 'hmt_sonde_' .. nom .. '.inst', name = 'HMT', comment = texte })
end
local function G(numero)
  local e = HMT_recenser()[numero]
  return e and e.guid
end
local function CHAMPS(u, noms)
  local t = {}
  for _, n in ipairs(noms) do
    local ok, x = pcall(function() return u[n] end)
    t[#t + 1] = n .. '=' .. (ok and D(x, 1) or ('ERR ' .. tostring(x)))
  end
  return table.concat(t, '\n')
end
"""

CHAMPS_AVION = ["name", "guid", "side", "type", "subtype", "dbid", "classname", "loadoutdbid", "condition",
                "condition_v", "unitstate", "readytime", "readytime_v", "airbornetime", "airbornetime_v",
                "altitude", "speed", "fuelstate", "weaponstate", "fuel", "mission", "base", "group", "proficiency",
                "QuickTurnaround", "quickturnaround", "loadout", "sensors", "mounts", "magazines", "damage",
                "throttle", "manualAltitude", "category", "avoidCavitation", "outOfComms", "fields"]
BASE_REELLE = "Lithuania/Siauliai Air Base 2024.inst"    # 2024 : modèle récent livré avec CMO
CHAR = 102                                                # T-72B3 ( DataGroundUnit, Russie )
CHAMPS_SOL = ["name", "guid", "side", "type", "dbid", "classname", "latitude", "longitude", "speed", "unitstate",
              "condition", "mounts", "magazines", "damage", "fields"]
# Combien d'unités dans le camp jetable, les dix premières ( nom, dbid ), et le magasin du premier dépôt de munitions.
COMPTER = ("local s = VP_GetSide({side = 'HMT-SONDE'}) local us = s and s.units or {} local t = {'unites ' .. #us} "
           "local mag = nil "
           "for i, u in ipairs(us) do "
           "  if i <= 10 then local ok, x = pcall(ScenEdit_GetUnit, {guid = u.guid}) "
           "    t[#t + 1] = (u.name or '?') .. ' dbid=' .. tostring(ok and x and x.dbid) end "
           "  if mag == nil and string.find(string.lower(u.name or ''), 'ammo') then mag = u.guid end "
           "end "
           "if mag then local x = ScenEdit_GetUnit({guid = mag}) t[#t + 1] = 'DEPOT ' .. CHAMPS(x, {'name', 'magazines'}) end "
           "SORTIE('{n}', table.concat(t, '\\n'))")
CHAMPS_BASE = ["name", "guid", "side", "type", "dbid", "classname", "magazines", "mounts", "airbases",
               "hostedUnits", "hostedunits", "embarkedUnits", "unitstate", "condition", "damage", "fields"]


def lua_liste(noms):
    return "{" + ", ".join(f"'{n}'" for n in noms) + "}"


def etapes(wpn_aim120, wpn_aim9, wpn_reservoir):
    b = f"G({BASE})"
    a = f"G({AV1})"
    yield "base", f"local u = ScenEdit_GetUnit({{guid = {b}}}) SORTIE('base', CHAMPS(u, {lua_liste(CHAMPS_BASE)}) .. '\\nTOSTRING ' .. D(u))"
    yield "avion", f"local u = ScenEdit_GetUnit({{guid = {a}}}) SORTIE('avion', CHAMPS(u, {lua_liste(CHAMPS_AVION)}) .. '\\nTOSTRING ' .. D(u))"
    yield "doctrine_camp", "SORTIE('doctrine_camp', ESSAI(ScenEdit_GetDoctrine, {side = HMT_CAMPS[1]}))"
    yield "doctrine_avion", f"SORTIE('doctrine_avion', ESSAI(ScenEdit_GetDoctrine, {{guid = {a}}}))"
    yield "options_camp", ("SORTIE('options_camp', ESSAI(ScenEdit_GetSideOptions, {side = HMT_CAMPS[1]}) .. '\\nPOSTURE ' "
                           ".. ESSAI(ScenEdit_GetSidePosture, HMT_CAMPS[1], HMT_CAMPS[2]))")
    yield "contacts", ("local s = VP_GetSide({side = HMT_CAMPS[1]}) "
                       "local okc, c = pcall(function() return s.contacts end) "
                       "local t = {'VP_GetSide.contacts ' .. (okc and c ~= nil and #c or -1)} "
                       "if okc and c ~= nil and #c > 0 then t[#t + 1] = 'premier ' .. D(c[1]) "
                       "t[#t + 1] = 'GetContact ' .. ESSAI(ScenEdit_GetContact, {side = HMT_CAMPS[1], guid = c[1].guid}) end "
                       "t[#t + 1] = 'GetContacts ' .. ESSAI(function() local x = ScenEdit_GetContacts(HMT_CAMPS[1]) "
                       "return {n = x and #x or -1, premier = x and x[1]} end) "
                       "SORTIE('contacts', table.concat(t, '\\n'))")
    yield "meteo", "SORTIE('meteo', ESSAI(ScenEdit_GetWeather))"
    # LES MAGASINS : chaque essai est suivi d'une relecture, dans un passage ultérieur ( CMO applique certains effets
    # entre deux passages : sonde du 29/09 sur DeleteUnit ).
    lire = f"local u = ScenEdit_GetUnit({{guid = {b}}}) SORTIE('{{n}}', CHAMPS(u, {{'magazines'}}))"
    yield "remplir_a", f"SORTIE('remplir_a', ESSAI(ScenEdit_FillMagsForLoadout, {{guid = {b}, loadoutid = {LOADOUT}, quantity = 4}}))"
    yield "mag_apres_a", lire.replace("{n}", "mag_apres_a")
    yield "remplir_b", (f"SORTIE('remplir_b', ESSAI(ScenEdit_FillMagsForLoadout, {{unitname = 'HMT-{BASE}', side = HMT_CAMPS[1], "
                        f"loadoutid = {LOADOUT}, quantity = 4}}))")
    yield "mag_apres_b", lire.replace("{n}", "mag_apres_b")
    yield "ajouter_a", f"SORTIE('ajouter_a', ESSAI(ScenEdit_AddWeaponToUnitMagazine, {{guid = {b}, wpn_dbid = {wpn_aim120}, number = 8}}))"
    yield "mag_apres_c", lire.replace("{n}", "mag_apres_c")
    yield "ajouter_b", (f"SORTIE('ajouter_b', ESSAI(ScenEdit_AddWeaponToUnitMagazine, {{guid = {b}, wpn_dbid = {wpn_aim9}, "
                        f"number = 8, new = true}}))")
    yield "mag_apres_d", lire.replace("{n}", "mag_apres_d")
    yield "ajouter_c", (f"SORTIE('ajouter_c', ESSAI(ScenEdit_AddWeaponToUnitMagazine, {{guid = {b}, wpn_dbid = {wpn_reservoir}, "
                        f"number = 8, new = true}}))")
    yield "mag_apres_e", lire.replace("{n}", "mag_apres_e")
    # La remise en état : l'avion 2 a reçu un loadout vide au départ ? on relit les deux avions après les essais.
    yield "avion_2", f"local u = ScenEdit_GetUnit({{guid = G({AV2})}}) SORTIE('avion_2', CHAMPS(u, {lua_liste(CHAMPS_AVION)}))"
    # LES VRAIES INSTALLATIONS ( ImportExport/<pays>/*.inst, livrées avec CMO ) et LES TROUPES AU SOL, dans un camp
    # JETABLE ( HMT-SONDE ) retiré à la fin avec tout ce qu'il contient : le scénario de guerre n'en garde rien.
    yield "camp_sonde", "SORTIE('camp_sonde', ESSAI(ScenEdit_AddSide, {side = 'HMT-SONDE'}))"
    yield "importer_a", f"SORTIE('importer_a', ESSAI(ScenEdit_ImportInst, 'HMT-SONDE', '{BASE_REELLE}'))"
    yield "importe_a", COMPTER.replace("{n}", "importe_a")
    yield "importer_b", f"SORTIE('importer_b', ESSAI(ScenEdit_ImportInst, 'HMT-SONDE', '{BASE_REELLE.replace('/', chr(92) * 2)}'))"
    yield "importe_b", COMPTER.replace("{n}", "importe_b")
    yield "sol_a", (f"SORTIE('sol_a', ESSAI(ScenEdit_AddUnit, {{side = 'HMT-SONDE', type = 'GroundUnit', unitname = 'SONDE-SOL-A', "
                    f"dbid = {CHAR}, latitude = {LIEU[0] + 0.2}, longitude = {LIEU[1]}}}))")
    yield "sol_b", (f"SORTIE('sol_b', ESSAI(ScenEdit_AddUnit, {{side = 'HMT-SONDE', type = 'Facility', unitname = 'SONDE-SOL-B', "
                    f"dbid = {CHAR}, latitude = {LIEU[0] + 0.3}, longitude = {LIEU[1]}}}))")
    yield "sol_lu", ("local t = {} for _, n in ipairs({'SONDE-SOL-A', 'SONDE-SOL-B'}) do "
                     "local ok, u = pcall(ScenEdit_GetUnit, {side = 'HMT-SONDE', unitname = n}) "
                     f"t[#t + 1] = n .. ' : ' .. (ok and u ~= nil and CHAMPS(u, {lua_liste(CHAMPS_SOL)}) or 'absent') end "
                     "SORTIE('sol_lu', table.concat(t, '\\n----\\n'))")
    yield "retirer_sonde", "SORTIE('retirer_sonde', ESSAI(ScenEdit_RemoveSide, {side = 'HMT-SONDE'}))"
    yield "camps_apres", "local t = {} for _, s in ipairs(VP_GetSides()) do t[#t + 1] = s.name end SORTIE('camps_apres', table.concat(t, ', '))"


def armes_du_loadout(loadout):
    c = sqlite3.connect(DB)
    out = []
    for (rid,) in c.execute("select ComponentID from DataLoadoutWeapons where ID=?", (loadout,)):
        w, n = c.execute("select ComponentID, DefaultLoad from DataWeaponRecord where ID=?", (rid,)).fetchone()
        out.append((w, n, c.execute("select Name from DataWeapon where ID=?", (w,)).fetchone()[0]))
    return out


def lire_sonde(sortie, nom, attente=20.0):
    chemin = os.path.join(sortie, f"hmt_sonde_{nom}.inst")
    fin = time.time() + attente
    while time.time() < fin:
        t = CL.lire_inst(chemin)
        if t is not None:
            return t
        time.sleep(0.5)
    return None


def sonder(labo_kw=None, dossier=None, armes=None):
    labo_kw = labo_kw or {}
    dossier = dossier or os.path.join(CL.ETAT, "cmo_sondes", time.strftime("palier0_%Y%m%d_%H%M%S"))
    os.makedirs(dossier, exist_ok=True)
    armes = armes or armes_du_loadout(LOADOUT)
    par_nom = {nom: w for w, _, nom in armes}
    w120 = next(w for n, w in par_nom.items() if "AIM-120" in n)
    w9 = next(w for n, w in par_nom.items() if "AIM-9" in n)
    wres = next(w for n, w in par_nom.items() if "Tank" in n)
    sortie = labo_kw.get("sortie", CL.SORTIE)
    camps = labo_kw.pop("camps", ("OTAN", "Russie-Chine"))
    resultats = {"armes_du_loadout": armes}
    with CL.Labo(camps=camps, **labo_kw) as labo:
        resultats["nettoyer_avant"] = labo.nettoyer()
        resultats["base"] = labo.poser_lots([(camps[0], "site", AERODROME, [(BASE, *LIEU)], 0, 0)])
        resultats["avions"] = labo.poser_base_lots([(camps[0], F16, LOADOUT, BASE, [AV1]),
                                                    (camps[0], F16, 0, BASE, [AV2])])
        for nom, corps in etapes(w120, w9, wres):
            for vieux in (os.path.join(sortie, f"hmt_sonde_{nom}.inst"),):
                if os.path.exists(vieux):
                    os.remove(vieux)
            try:
                labo.lua(PRELUDE + corps, par_humain=True, patience=30)
                texte = lire_sonde(sortie, nom)
            except CL.ErreurLabo as e:
                texte = f"ECHEC {type(e).__name__}: {e}"
            resultats[nom] = texte
            with open(os.path.join(dossier, f"{nom}.txt"), "w") as g:
                g.write(texte or "AUCUN FICHIER")
            print(f"--- {nom}\n{(texte or 'AUCUN FICHIER')[:600]}", flush=True)
        resultats["nettoyer_apres"] = labo.nettoyer()
    with open(os.path.join(dossier, "sonde.json"), "w") as g:
        json.dump(resultats, g, ensure_ascii=False, indent=1)
    return dossier, resultats


if __name__ == "__main__":
    d, _ = sonder()
    print(f"sondes écrites dans {d}")
