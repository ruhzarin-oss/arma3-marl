#!/usr/bin/env python3
"""sonde_soutien — la composante air complète, brique 1 ( 03/10, Younes : « donne-lui toute la composante air » ) : les
champs d'une mission de frappe ( ravitaillement, escorte ), une mission de SOUTIEN ( guet radar, ravitailleur, brouilleur )
sur une zone, l'allumage du brouillage ( ScenEdit_SetEMCON OECM ), une patrouille SEAD. Dans la guerre réelle arrêtée le
temps de la sonde ; missions et points créés puis retirés. Lua brut par_humain.

    .venv312/bin/python cmo/sonde_soutien.py <id de la frappe OTAN en cours>"""
import json, os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402
from theatres import baltique_reel as T                   # noqa: E402

ZONE = [(52.6, 18.0), (52.6, 19.0), (52.0, 19.0), (52.0, 18.0)]   # Pologne centrale, loin du front


def main(fid):
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
            print(f"--- {nom}\n{(t or 'AUCUN')[:3000]}", flush=True)
        une("frappe", f"local m = ScenEdit_GetMission('OTAN', 'HMT-F{fid}') "
                      "SORTIE('frappe', D(m) .. '\\nSTRIKE ' .. ESSAI(function() return m.strikemission end))")
        rps = " ".join(f"ScenEdit_AddReferencePoint({{side = 'OTAN', name = 'HMT-SONDE-{i}', latitude = {la}, longitude = {lo}}})"
                       for i, (la, lo) in enumerate(ZONE))
        zone = "{" + ", ".join(f"'HMT-SONDE-{i}'" for i in range(len(ZONE))) + "}"
        une("soutien", rps + f" local a = ESSAI(ScenEdit_AddMission, 'OTAN', 'HMT-SONDE-S', 'Support', {{zone = {zone}}}) "
                       "local m = ScenEdit_GetMission('OTAN', 'HMT-SONDE-S') "
                       "SORTIE('soutien', 'ajout ' .. a .. '\\nMISSION ' .. D(m) .. '\\nSUPPORT ' .. ESSAI(function() return m.supportmission end))")
        une("oecm", "SORTIE('oecm', 'mission ' .. ESSAI(ScenEdit_SetEMCON, 'Mission', 'HMT-SONDE-S', 'OECM=Active') .. "
                    "'\\ncamp lu ' .. ESSAI(function() return ScenEdit_GetDoctrine({side = 'OTAN'}).emcon end))")
        une("sead", f"local a = ESSAI(ScenEdit_AddMission, 'OTAN', 'HMT-SONDE-P', 'Patrol', {{type = 'SEAD', zone = {zone}}}) "
                    "local m = ScenEdit_GetMission('OTAN', 'HMT-SONDE-P') "
                    "SORTIE('sead', 'ajout ' .. a .. '\\nPATROL ' .. ESSAI(function() return m.patrolmission end) .. "
                    "'\\nsubtype ' .. ESSAI(function() return m.subtype end))")
        une("retrait", "local t = {ESSAI(ScenEdit_DeleteMission, 'OTAN', 'HMT-SONDE-S'), ESSAI(ScenEdit_DeleteMission, 'OTAN', 'HMT-SONDE-P')} "
                       + " ".join(f"t[#t + 1] = ESSAI(ScenEdit_DeleteReferencePoint, {{side = 'OTAN', name = 'HMT-SONDE-{i}'}})"
                                  for i in range(len(ZONE)))
                       + " SORTIE('retrait', table.concat(t, ' ; '))")
    chemin = os.path.join(CL.ETAT, "cmo_sondes", time.strftime("soutien_%Y%m%d_%H%M%S.json"))
    json.dump(out, open(chemin, "w"), ensure_ascii=False, indent=1)
    print("écrit", chemin)


if __name__ == "__main__":
    main(int(sys.argv[1]))
