#!/usr/bin/env python3
"""sonde_decollage — pourquoi le F-16 posé sur la vraie base de Šiauliai n'a pas décollé en 3 min ( banc_v8 du 02/10 ) ?
Deux F-16 : l'un sur Šiauliai importée ( dépôts remplis ), l'autre sur un aérodrome générique ; même patrouille ; état de
chacun ( condition, readytime, altitude, mission ) toutes les 20 s pendant 8 min. Lua brut par_humain ( aval du 02/10 )."""
import json, os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402
import banc_v8 as B                                       # noqa: E402

GENERIQUE, AV_REEL, AV_GEN = 90_000_001, 10_100_001, 10_100_002


def main():
    out = {"releves": []}
    with CL.Labo(camps=B.CAMPS, installations=B.INSTALLATIONS) as l:
        l.nettoyer()
        l.hostiles(*B.CAMPS)
        l.importer("OTAN", B.SIAULIAI)
        time.sleep(3)
        el = l.adopter("OTAN", B.PREMIER)["elements"]
        groupe = next(e[0] for e in el if e[4])
        depots = [e[0] for e in el if e[1] in (322, 325, 320)]
        l.armer([(k, B.LOADOUT, 10) for k in depots])
        l.poser("OTAN", "site", 1712, GENERIQUE, 55.5, 23.0)
        l.armer([(GENERIQUE, B.LOADOUT, 10)])
        out["poses"] = l.poser_base_lots([("OTAN", B.F16, B.LOADOUT, groupe, [AV_REEL]),
                                           ("OTAN", B.F16, B.LOADOUT, GENERIQUE, [AV_GEN])])
        out["missions"] = l.missions([(1, "OTAN", 56.5, 23.0, 20, 0)], [(1, [AV_REEL, AV_GEN])])
        t0 = time.time()
        while time.time() - t0 < 480:
            p = os.path.join(CL.SORTIE, "hmt_sonde_etat_avions.inst")
            if os.path.exists(p):
                os.remove(p)
            l.lua(S0.PRELUDE + "local t = {} for _, k in ipairs({%d, %d}) do local e = HMT_recenser()[k] "
                  "local u = e and ScenEdit_GetUnit({guid = e.guid}) "
                  "t[#t + 1] = k .. ' ' .. (u and CHAMPS(u, {'condition', 'readytime', 'altitude', 'unitstate', 'airbornetime'}):gsub('\\n', ' ; ') or 'absent') end "
                  "SORTIE('etat_avions', table.concat(t, '\\n'))" % (AV_REEL, AV_GEN), par_humain=True)
            t = S0.lire_sonde(CL.SORTIE, "etat_avions")
            out["releves"].append({"s": round(time.time() - t0), "etat": t})
            print(round(time.time() - t0), t, flush=True)
            time.sleep(20)
        out["nettoyer"] = l.nettoyer()["avant"]
    d = os.path.join(CL.ETAT, "cmo_sondes", time.strftime("decollage_%Y%m%d_%H%M%S.json"))
    with open(d, "w") as g:
        json.dump(out, g, ensure_ascii=False, indent=1, default=str)
    print("écrit", d)


if __name__ == "__main__":
    main()
