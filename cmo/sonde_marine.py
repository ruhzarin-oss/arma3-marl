#!/usr/bin/env python3
"""sonde_marine — la composante navale dans CMO 1.10 ( 03/10 ) : les types de patrouille navale ( SUR_SEA, SUB, SEA ), la
frappe antinavire ( Strike type Sea ) : créées, relues ( sous-type ), retirées. Lecture et création jetable seulement, dans
la guerre arrêtée le temps de la sonde. Lua brut par_humain.

    .venv312/bin/python cmo/sonde_marine.py"""
import json, os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402
from theatres import baltique_reel as T                   # noqa: E402

ZONE = [(55.6, 17.0), (55.6, 18.0), (55.0, 18.0), (55.0, 17.0)]   # mer Baltique centrale


def main():
    out = {}
    with CL.Labo(camps=T.CAMPS, installations=T.FICHIERS) as l:
        def une(nom, corps, attente=30):
            p = os.path.join(CL.SORTIE, f"hmt_sonde_{nom}.inst")
            if os.path.exists(p):
                os.remove(p)
            try:
                l.lua(S0.PRELUDE + corps, par_humain=True, patience=60)
                t = S0.lire_sonde(CL.SORTIE, nom, attente)
            except CL.ErreurLabo as x:
                t = f"ECHEC {type(x).__name__}: {x}"
            out[nom] = t
            print(f"--- {nom}\n{(t or 'AUCUN')[:800]}", flush=True)
        rps = " ".join(f"ScenEdit_AddReferencePoint({{side = 'OTAN', name = 'HMT-SM-{i}', latitude = {la}, longitude = {lo}}})"
                       for i, (la, lo) in enumerate(ZONE))
        zone = "{" + ", ".join(f"'HMT-SM-{i}'" for i in range(len(ZONE))) + "}"
        corps = rps + " local t = {} "
        for ty in ("SUR_SEA", "SUB", "SEA", "SUR_LAND", "SUR_MIXED"):
            corps += (f"t[#t + 1] = '{ty} ' .. ESSAI(function() local m = ScenEdit_AddMission('OTAN', 'HMT-SM-{ty}', 'Patrol', "
                      f"{{type = '{ty}', zone = {zone}}}) return m and m.subtype end) ")
        corps += ("t[#t + 1] = 'STRIKE_SEA ' .. ESSAI(function() local m = ScenEdit_AddMission('OTAN', 'HMT-SM-STRIKE', 'Strike', "
                  "{type = 'Sea'}) return m and m.subtype end) ")
        corps += "t[#t + 1] = 'MINING ' .. ESSAI(function() local m = ScenEdit_AddMission('OTAN', 'HMT-SM-MINES', 'Mining', {zone = " + zone + "}) return m and m.subtype end) "
        corps += "t[#t + 1] = 'MINECLEAR ' .. ESSAI(function() local m = ScenEdit_AddMission('OTAN', 'HMT-SM-DEMINE', 'Mine Clearing', {zone = " + zone + "}) return m and m.subtype end) "
        corps += "SORTIE('marine', table.concat(t, '\\n'))"
        une("marine", corps)
        ret = " ".join(f"pcall(ScenEdit_DeleteMission, 'OTAN', 'HMT-SM-{x}')" for x in ("SUR_SEA", "SUB", "SEA", "SUR_LAND", "SUR_MIXED", "STRIKE", "MINES", "DEMINE"))
        ret += " " + " ".join(f"pcall(ScenEdit_DeleteReferencePoint, {{side = 'OTAN', name = 'HMT-SM-{i}'}})" for i in range(len(ZONE)))
        une("marine_retrait", ret + " SORTIE('marine_retrait', 'ok')")
    chemin = os.path.join(CL.ETAT, "cmo_sondes", time.strftime("marine_%Y%m%d_%H%M%S.json"))
    json.dump(out, open(chemin, "w"), ensure_ascii=False, indent=1)
    print("écrit", chemin)


if __name__ == "__main__":
    main()
