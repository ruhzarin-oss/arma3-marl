#!/usr/bin/env python3
"""banc_v8 — les outils v8 du pont dans le VRAI CMO ( 1.10.1900.20 ), sur une vraie base : Šiauliai 2024, livrée avec CMO.

  1. déployer le Lua v8 avec la liste d'installations, le faire relire par le pont ( sans console ) ;
  2. table rase, camps hostiles ;
  3. importer Šiauliai dans le camp OTAN, la numéroter ( HMT_adopter : CMO renomme-t-il ? ) ;
  4. remplir ses dépôts de munitions ( 10 packs du chargement air-air du F-16 par dépôt ) et les relire ;
  5. poser deux F-16 SUR la base importée ( le groupe accueille-t-il les avions ? ) ;
  6. doctrine : rotation rapide et tempo, écrits et relus ; pertes et dépenses ; dégâts de la piste ;
  7. une patrouille : les F-16 décollent-ils de la vraie base ? ( altitude relevée pendant 3 min ) ;
  8. table rase prouvée.

Chaque étape est notée, réussie ou non, dans /mnt/data/hmt/etat/cmo_sondes/banc_v8_<date>.json : un échec ne masque pas
les suivantes.

    .venv312/bin/python cmo/banc_v8.py
"""
import json
import os
import sys
import time
import traceback

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import deployer                                           # noqa: E402

CAMPS = ("OTAN", "Russie-Chine")
SIAULIAI = "Lithuania/Siauliai Air Base 2024.inst"
INSTALLATIONS = (SIAULIAI,)
PREMIER = 90_100_001
F16, LOADOUT = 7087, 7453
AVIONS = (10_100_001, 10_100_002)


def banc(dossier=None):
    sortie = os.path.join(dossier or os.path.join(CL.ETAT, "cmo_sondes"), time.strftime("banc_v8_%Y%m%d_%H%M%S.json"))
    os.makedirs(os.path.dirname(sortie), exist_ok=True)
    res = {"debut": time.strftime("%Y-%m-%d %H:%M:%S")}

    def etape(nom, fn):
        t0 = time.monotonic()
        try:
            r = fn()
            res[nom] = {"ok": True, "s": round(time.monotonic() - t0, 1), "r": r}
        except Exception as e:
            res[nom] = {"ok": False, "s": round(time.monotonic() - t0, 1), "erreur": f"{type(e).__name__}: {e}",
                        "trace": traceback.format_exc()[-800:]}
        print(f"{'OK ' if res[nom]['ok'] else 'NON'} {nom} ({res[nom]['s']} s) : "
              f"{json.dumps(res[nom].get('r', res[nom].get('erreur')), ensure_ascii=False, default=str)[:400]}", flush=True)
        with open(sortie, "w") as g:
            json.dump(res, g, ensure_ascii=False, indent=1, default=str)
        return res[nom].get("r")

    etape("deployer", lambda: deployer.deployer(camps=CAMPS, installations=INSTALLATIONS))
    etape("recharger", lambda: CL.recharger())
    with CL.Labo(camps=CAMPS, installations=INSTALLATIONS) as l:
        etape("canari", lambda: {k: v for k, v in l.version.items() if k != "recu"})
        etape("nettoyer_avant", lambda: l.nettoyer()["avant"])
        etape("hostiles", lambda: l.hostiles(*CAMPS)["hostiles"])
        etape("importer", lambda: l.importer("OTAN", SIAULIAI)["elements"])
        time.sleep(3)
        el = etape("adopter", lambda: [e for e in l.adopter("OTAN", PREMIER)["elements"]]) or []
        groupe = next((e[0] for e in el if e[4]), None)
        depots = [e[0] for e in el if e[1] in (322, 325, 320)]
        pistes = [e[0] for e in el if e[1] in (757, 55)]
        res["base"] = {"groupe": groupe, "depots": depots, "pistes": pistes, "elements": len(el)}
        etape("armer", lambda: l.armer([(k, LOADOUT, 10) for k in depots]))
        time.sleep(2)
        etape("stocks", lambda: {k: {w: c for w, (c, _) in s.items()} for k, s in l.stocks(depots[:3])["stocks"].items()})
        etape("poser_sur_groupe", lambda: l.poser_base_lots([("OTAN", F16, LOADOUT, groupe, [AVIONS[0]])]))
        etape("poser_sur_piste", lambda: l.poser_base_lots([("OTAN", F16, LOADOUT, pistes[0], [AVIONS[1]])]))
        etape("doctrine_lue", lambda: l.lua("local d = ScenEdit_GetDoctrine({side = 'OTAN'}) R('D', {d.quick_turnaround_for_aircraft, "
                                            "d.air_operations_tempo})", par_humain=True)["lignes"])
        etape("doctrine_rotation_rapide", lambda: l.doctrine("OTAN", "quick_turnaround_for_aircraft", 0)["valeur"])
        etape("doctrine_tempo", lambda: l.doctrine("OTAN", "air_operations_tempo", 0)["valeur"])
        etape("bilan", lambda: {str(k): v for k, v in l.bilan("OTAN")["pertes"].items()})
        etape("etats_pistes", lambda: l.etats(pistes + ([groupe] if groupe else []))["etats"])
        etape("patrouille", lambda: l.missions([(1, "OTAN", 56.5, 23.0, 20, 0)], [(1, list(AVIONS))]))
        vols = []
        for _ in range(12):
            time.sleep(15)
            try:
                p = l.positions(10_000_000, 29_999_999)
                vols.append({k: round(a) for k, _, _, a in p["vivants"]["OTAN"]})
            except CL.ErreurLabo as e:
                vols.append(str(e))
        res["vols"] = vols
        print("vols", vols, flush=True)
        etape("nettoyer_apres", lambda: l.nettoyer())
    res["fin"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(sortie, "w") as g:
        json.dump(res, g, ensure_ascii=False, indent=1, default=str)
    print(f"banc écrit dans {sortie}")
    return res


if __name__ == "__main__":
    banc()
