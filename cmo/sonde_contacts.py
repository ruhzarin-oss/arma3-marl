#!/usr/bin/env python3
"""sonde_contacts — le BROUILLARD DE GUERRE de CMO 1.10 ( 03/10 ) : ce qu'un camp sait réellement de l'autre. Lecture
seule dans la guerre réelle en cours ( aucune unité posée ) : `u.ascontact` d'une unité ( qui la voit ? ), les contacts
d'un camp ( ScenEdit_GetContacts ), leurs champs ( classification, âge, incertitude, actualunitid ), et combien des
défenses sol-air adverses l'OTAN a vraiment détectées. Lua brut par_humain, guerre arrêtée le temps de la sonde.
Relevés dans /mnt/data/hmt/etat/cmo_sondes/contacts_<date>.json.

    .venv312/bin/python cmo/sonde_contacts.py <dossier de la guerre>"""
import json, os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402
from theatres import baltique_reel as T                   # noqa: E402

CHAMPS_CONTACT = ['name', 'guid', 'actualunitid', 'type', 'typed', 'type_description', 'classificationlevel', 'age',
                  'areaofuncertainty', 'latitude', 'longitude', 'posture', 'side', 'fromside', 'detectedBySide',
                  'emissions', 'lastDetections', 'potentialmatches', 'missile_defence', 'weaponsAimedAtUs', 'firedOn']


def main(dossier):
    e = json.load(open(os.path.join(dossier, "theatre.json")))
    sam_ru = sorted(int(k) for k, s in e["sol"].items() if s["camp"] == "Russie-Chine")
    sam_ot = sorted(int(k) for k, s in e["sol"].items() if s["camp"] == "OTAN")
    piste = next(int(k) for k, x in e["elements"].items() if x["camp"] == "Russie-Chine" and x["classe"] == "piste" and x["vivant"])
    out = {"sol_russe": sam_ru, "sol_otan": sam_ot}
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
            print(f"--- {nom}\n{(t or 'AUCUN')[:1500]}", flush=True)
        une("ascontact", "local t = {} for _, k in ipairs({%d, %d, %d}) do local u = ScenEdit_GetUnit({guid = G(k)}) "
                         "t[#t + 1] = k .. ' ' .. CHAMPS(u, {'name', 'ascontact', 'autodetectable'}) end "
                         "SORTIE('ascontact', table.concat(t, '\\n'))" % (sam_ru[0], piste, sam_ot[0]))
        une("contacts_otan", "local c = ScenEdit_GetContacts('OTAN') local t = {'n ' .. ESSAI(function() return #c end)} "
                             "for i = 1, math.min(3, #c) do t[#t + 1] = CHAMPS(c[i], {%s}) end "
                             "SORTIE('contacts_otan', table.concat(t, '\\n'))" % ", ".join(f"'{x}'" for x in CHAMPS_CONTACT))
        une("sam_vus", "local par_guid = {} for k, e in pairs(HMT_recenser()) do par_guid[e.guid] = k end "
                       "local c = ScenEdit_GetContacts('OTAN') local t, n, m = {}, 0, 0 "
                       "for i = 1, #c do local ok, a = pcall(function() return c[i].actualunitid end) "
                       "if ok and a and par_guid[a] then n = n + 1 local k = par_guid[a] "
                       "if k >= 20000000 and k < 30000000 then m = m + 1 t[#t + 1] = k .. ' ' .. CHAMPS(c[i], {'classificationlevel', 'age', 'areaofuncertainty', 'posture'}) end end end "
                       "SORTIE('sam_vus', 'contacts HMT ' .. n .. ' dont sol ' .. m .. '\\n' .. table.concat(t, '\\n'))")
    chemin = os.path.join(CL.ETAT, "cmo_sondes", time.strftime("contacts_%Y%m%d_%H%M%S.json"))
    json.dump(out, open(chemin, "w"), ensure_ascii=False, indent=1)
    print("écrit", chemin)


if __name__ == "__main__":
    main(sys.argv[1])
