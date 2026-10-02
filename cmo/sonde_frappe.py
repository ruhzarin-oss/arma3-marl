#!/usr/bin/env python3
"""sonde_frappe — une vraie mission de frappe dans CMO 1.10 ( 02/10, aval de Younes : « la guerre avance par ce qui est
détruit » ). Un vol de deux F-16 ( GBU-12 guidées laser, nacelle Sniper, chargement 7492 ) part d'un aérodrome de
Pologne du Nord contre un dépôt de munitions enterré russe posé près de Kaliningrad ( ~ 120 km ). On veut voir :
mission Strike créée, cible affectée ( ScenEdit_AssignUnitAsTarget ), décollage, tir, dégâts de la cible relus.
Peu d'unités, retirées une à une à la fin ( pas de table rase en masse : elle ralentit CMO, banc du 02/10 ).
Lua brut par_humain. Relevés dans /mnt/data/hmt/etat/cmo_sondes/frappe_<date>.json."""
import json, os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402
from theatres import baltique_reel as T                   # noqa: E402

BASE, AV, CIBLE = 90_000_001, (10_100_001, 10_100_002), 92_000_001
F16, LO_FRAPPE = 7087, 7492
LIEU_BASE, LIEU_CIBLE = (54.03, 19.13), (54.70, 20.40)   # Malbork ; Kaliningrad ( schématique )


def main(duree_s=900):
    out = {"releves": []}
    with CL.Labo(camps=T.CAMPS, installations=T.FICHIERS) as l:
        def une(nom, corps, attente=30):
            p = os.path.join(CL.SORTIE, f"hmt_sonde_{nom}.inst")
            if os.path.exists(p):
                os.remove(p)
            try:
                l.lua(S0.PRELUDE + corps, par_humain=True, patience=60)
                t = S0.lire_sonde(CL.SORTIE, nom, attente)
            except CL.ErreurLabo as e:
                t = f"ECHEC {type(e).__name__}: {e}"
            out[nom] = t
            print(f"--- {nom}\n{(t or 'AUCUN')[:700]}", flush=True)
            return t
        l.lua("pcall(ScenEdit_SetStartTime, { Duration = '365:00:00:00' })", par_humain=True)
        l.hostiles(*T.CAMPS)
        out["base"] = l.poser("OTAN", "site", 1712, BASE, *LIEU_BASE)["numero"]
        out["armer"] = l.armer([(BASE, LO_FRAPPE, 8)])["armes"]
        out["avions"] = l.poser_base_lots([("OTAN", F16, LO_FRAPPE, BASE, list(AV))])
        out["cible"] = l.poser("Russie-Chine", "site", 325, CIBLE, *LIEU_CIBLE)["numero"]
        une("cible_vue", f"local e = HMT_recenser()[{CIBLE}] local u = ScenEdit_GetUnit({{guid = e.guid}}) "
                         "SORTIE('cible_vue', CHAMPS(u, {'name', 'autodetectable', 'damage'}) .. '\\nCONTACTS OTAN ' .. "
                         "ESSAI(function() local s = VP_GetSide({side = 'OTAN'}) return #(s.contacts or {}) end))")
        une("mission", "SORTIE('mission', ESSAI(function() local m = ScenEdit_AddMission('OTAN', 'HMT-F1', 'Strike', {type = 'Land'}) "
                       "return m and (m.name .. ' ' .. tostring(m.type) .. ' ' .. tostring(m.subtype)) end))")
        une("cible_affectee", f"local e = HMT_recenser()[{CIBLE}] SORTIE('cible_affectee', "
                              "'guid ' .. ESSAI(ScenEdit_AssignUnitAsTarget, e.guid, 'HMT-F1') .. "
                              f"'\\nnom ' .. ESSAI(ScenEdit_AssignUnitAsTarget, 'HMT-{CIBLE}', 'HMT-F1'))")
        une("avions_affectes", "local t = {} for _, k in ipairs({%d, %d}) do local e = HMT_recenser()[k] "
                               "t[#t + 1] = ESSAI(ScenEdit_AssignUnitToMission, e.guid, 'HMT-F1') end SORTIE('avions_affectes', table.concat(t, ' ; '))" % AV)
        une("mission_lue", "local m = ScenEdit_GetMission('OTAN', 'HMT-F1') SORTIE('mission_lue', CHAMPS(m, {'isactive', 'unitlist', 'targetlist', 'subtype'}))")
        t0 = time.time()
        while time.time() - t0 < duree_s:
            time.sleep(20)
            t = une("releve", "local t = {} for _, k in ipairs({%d, %d, %d}) do local e = HMT_recenser()[k] "
                              "local u = e and ScenEdit_GetUnit({guid = e.guid}) "
                              "t[#t + 1] = k .. ' ' .. (u and CHAMPS(u, {'condition', 'altitude', 'weaponstate'}):gsub('\\n', ' ; ') .. "
                              "' ; dp ' .. tostring(u.damage and u.damage.dp_percent_now) or 'DETRUIT ou absent') end "
                              "SORTIE('releve', table.concat(t, ' | '))" % (AV[0], AV[1], CIBLE), 20)
            out["releves"].append({"s": round(time.time() - t0), "etat": t})
            if t and f"{CIBLE} DETRUIT" in t:
                break
        out["bilan_otan"] = {str(k): v for k, v in l.bilan("OTAN")["depenses"].items()}
        # retrait une à une ( quelques unités : sans effet mesurable sur la vitesse )
        une("retrait", "local n = 0 for _, k in ipairs({%d, %d, %d, %d}) do local e = HMT_recenser()[k] "
                       "if e and pcall(ScenEdit_DeleteUnit, {guid = e.guid}) then n = n + 1 end end "
                       "pcall(ScenEdit_DeleteMission, 'OTAN', 'HMT-F1') SORTIE('retrait', 'retirees ' .. n)" % (BASE, AV[0], AV[1], CIBLE))
    d = os.path.join(CL.ETAT, "cmo_sondes", time.strftime("frappe_%Y%m%d_%H%M%S.json"))
    with open(d, "w") as g:
        json.dump(out, g, ensure_ascii=False, indent=1, default=str)
    print("écrit", d)


if __name__ == "__main__":
    main()
