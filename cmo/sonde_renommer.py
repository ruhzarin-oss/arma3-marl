#!/usr/bin/env python3
"""sonde_renommer — comment renommer une unité dans CMO 1.10 ( banc_v8 du 02/10 : SetUnit{ newname } refusé ou différé ),
puis retrait des unités non HMT du camp OTAN ( la base de Šiauliai importée par le banc, que la table rase ne voit pas ).
Lua brut par_humain ( aval de Younes, 02/10 ). Textes dans /mnt/data/hmt/etat/cmo_sondes/renommer_<date>/."""
import json, os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402
import banc_v8 as B                                       # noqa: E402

AUTRES = ("local s = VP_GetSide({side = 'OTAN'}) local t = {} for _, x in ipairs(s.units or {}) do "
          "if not string.match(x.name or '', '^HMT%-%d+$') then t[#t + 1] = x end end ")


def main():
    d = os.path.join(CL.ETAT, "cmo_sondes", time.strftime("renommer_%Y%m%d_%H%M%S"))
    os.makedirs(d, exist_ok=True)
    res = {}
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
            res[nom] = t
            print(f"--- {nom}\n{(t or 'AUCUN')[:600]}", flush=True)
        une("avant", AUTRES + "SORTIE('avant', 'non HMT ' .. #t .. ' ; premier ' .. tostring(t[1] and t[1].name))")
        # trois façons, chacune sur une unité différente ; relecture au passage suivant
        une("a_newname", AUTRES + "SORTIE('a_newname', ESSAI(ScenEdit_SetUnit, {guid = t[1].guid, newname = 'HMT-99000001'}))")
        une("b_name", AUTRES + "SORTIE('b_name', ESSAI(ScenEdit_SetUnit, {guid = t[2].guid, name = 'HMT-99000002'}))")
        une("c_propriete", AUTRES + "SORTIE('c_propriete', ESSAI(function() local u = ScenEdit_GetUnit({guid = t[3].guid}) "
                                    "u.name = 'HMT-99000003' return u.name end))")
        time.sleep(2)
        une("relire", "local t = {} for _, n in ipairs({'HMT-99000001', 'HMT-99000002', 'HMT-99000003'}) do "
                      "local ok, u = pcall(ScenEdit_GetUnit, {side = 'OTAN', unitname = n}) "
                      "t[#t + 1] = n .. ' : ' .. ((ok and u ~= nil) and ('TROUVE ' .. u.name .. ' ' .. tostring(u.dbid)) or 'absent') end "
                      "SORTIE('relire', table.concat(t, '\\n'))")
        # retrait : éléments d'abord, groupes ensuite ( dans un autre passage )
        une("retirer_elements", AUTRES + "local n, g = 0, 0 for _, x in ipairs(t) do local u = ScenEdit_GetUnit({guid = x.guid}) "
                                         "if u and u.type ~= 'Group' then if pcall(ScenEdit_DeleteUnit, {guid = x.guid}) then n = n + 1 end "
                                         "else g = g + 1 end end SORTIE('retirer_elements', 'elements ' .. n .. ' groupes ' .. g)")
        time.sleep(2)
        une("retirer_groupes", AUTRES + "local n = 0 for _, x in ipairs(t) do if pcall(ScenEdit_DeleteUnit, {guid = x.guid}) then n = n + 1 end end "
                                        "SORTIE('retirer_groupes', 'groupes ' .. n)")
        time.sleep(2)
        une("apres", AUTRES + "SORTIE('apres', 'non HMT ' .. #t)")
        res["nettoyer"] = l.nettoyer()["avant"]
    with open(os.path.join(d, "sonde.json"), "w") as g:
        json.dump(res, g, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
