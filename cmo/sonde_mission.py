#!/usr/bin/env python3
"""sonde_mission — l'affectation à une patrouille répond oui mais l'avion reste « Unassigned » ( sonde_decollage du 02/10 ).
On lit la mission HMT-P1 existante, on en crée une neuve ( HMT-P7 ), on affecte par guid puis par nom, et on relit
mission et avion. Lua brut par_humain ( aval du 02/10 )."""
import os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402
import banc_v8 as B                                       # noqa: E402

AV, GEN = 10_100_001, 90_000_001
CH_M = ["name", "type", "subtype", "isactive", "starttime", "endtime", "side", "unitlist", "targetlist", "zone",
        "OneThirdRule", "SISH", "fields"]


def main():
    with CL.Labo(camps=B.CAMPS, installations=B.INSTALLATIONS) as l:
        def une(nom, corps):
            p = os.path.join(CL.SORTIE, f"hmt_sonde_{nom}.inst")
            if os.path.exists(p):
                os.remove(p)
            try:
                l.lua(S0.PRELUDE + corps, par_humain=True, patience=30)
                t = S0.lire_sonde(CL.SORTIE, nom)
            except CL.ErreurLabo as e:
                t = f"ECHEC {type(e).__name__}: {e}"
            print(f"--- {nom}\n{(t or 'AUCUN')[:1500]}", flush=True)
        l.nettoyer()
        une("missions_otan", "local s = VP_GetSide({side = 'OTAN'}) local t = {} for _, m in ipairs(s.missions or {}) do "
                             "t[#t + 1] = tostring(m.name) .. ' actif=' .. tostring(m.isactive) end SORTIE('missions_otan', table.concat(t, '\\n'))")
        une("p1", f"local m = ScenEdit_GetMission('OTAN', 'HMT-P1') SORTIE('p1', m and CHAMPS(m, {S0.lua_liste(CH_M)}) or 'absente')")
        l.poser("OTAN", "site", 1712, GEN, 55.5, 23.0)
        l.armer([(GEN, B.LOADOUT, 10)])
        l.poser_base_lots([("OTAN", B.F16, B.LOADOUT, GEN, [AV])])
        l.missions([(7, "OTAN", 56.5, 23.0, 20, 0)], [])
        une("p7", f"local m = ScenEdit_GetMission('OTAN', 'HMT-P7') SORTIE('p7', m and CHAMPS(m, {S0.lua_liste(CH_M)}) or 'absente')")
        une("affecter_guid", f"local e = HMT_recenser()[{AV}] SORTIE('affecter_guid', ESSAI(ScenEdit_AssignUnitToMission, e.guid, 'HMT-P7'))")
        time.sleep(3)
        une("avion_apres_guid", f"local e = HMT_recenser()[{AV}] local u = ScenEdit_GetUnit({{guid = e.guid}}) "
                                "SORTIE('avion_apres_guid', CHAMPS(u, {'unitstate', 'condition', 'readytime'}))")
        une("affecter_nom", f"SORTIE('affecter_nom', ESSAI(ScenEdit_AssignUnitToMission, 'HMT-{AV}', 'HMT-P7'))")
        time.sleep(3)
        une("avion_apres_nom", f"local e = HMT_recenser()[{AV}] local u = ScenEdit_GetUnit({{guid = e.guid}}) "
                               "SORTIE('avion_apres_nom', CHAMPS(u, {'unitstate', 'condition', 'readytime'}))")
        une("p7_apres", f"local m = ScenEdit_GetMission('OTAN', 'HMT-P7') SORTIE('p7_apres', m and CHAMPS(m, {S0.lua_liste(['isactive', 'unitlist', 'starttime'])}) or 'absente')")
        for i in range(12):
            time.sleep(20)
            une(f"avion_{(i + 1) * 20}s", f"local e = HMT_recenser()[{AV}] local u = ScenEdit_GetUnit({{guid = e.guid}}) "
                f"SORTIE('avion_{(i + 1) * 20}s', CHAMPS(u, {{'unitstate', 'condition', 'altitude', 'readytime', 'loadoutdbid', 'weaponstate', 'fuelstate'}}):gsub('\\n', ' ; '))")
        l.nettoyer()


if __name__ == "__main__":
    main()
