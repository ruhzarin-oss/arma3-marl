#!/usr/bin/env python3
"""sonde_lancement — un F-16 affecté à une patrouille reste au parking ( 02/10 ). Essai 1 : doctrine de rotation rapide
remise à sa valeur d'origine ( 1 ). Essai 2 : l'ordre direct u:Launch(). État relevé toutes les 15 s. Lua brut par_humain."""
import os, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import sonde_palier0 as S0                                # noqa: E402
import banc_v8 as B                                       # noqa: E402

AV, GEN = 10_100_001, 90_000_001
ETAT = (f"local e = HMT_recenser()[{AV}] local u = ScenEdit_GetUnit({{guid = e.guid}}) "
        "SORTIE('{n}', CHAMPS(u, {'unitstate', 'condition', 'altitude', 'readytime'}):gsub('\\n', ' ; '))")


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
            print(f"{nom} : {(t or 'AUCUN')[:400]}", flush=True)
        l.nettoyer()
        l.poser("OTAN", "site", 1712, GEN, 55.5, 23.0)
        l.poser("Russie-Chine", "site", 1712, GEN + 1, 54.8, 21.5)
        l.armer([(GEN, B.LOADOUT, 10)])
        l.poser_base_lots([("OTAN", B.F16, B.LOADOUT, GEN, [AV]), ("Russie-Chine", 8333, 11076, GEN + 1, [AV + 1_000_000])])
        print(l.missions([(8, "OTAN", 56.0, 23.0, 20, 0), (9, "Russie-Chine", 55.2, 21.5, 20, 0)],
                         [(8, [AV]), (9, [AV + 1_000_000])])["affectes"])
        etat2 = ETAT.replace("local e = HMT_recenser()[%d]" % AV, "local e = HMT_recenser()[%d]" % (AV + 1_000_000))
        for i in range(6):
            time.sleep(15)
            une(f"otan_{(i + 1) * 15}s", ETAT.replace("{n}", f"otan_{(i + 1) * 15}s"))
            une(f"russe_{(i + 1) * 15}s", etat2.replace("{n}", f"russe_{(i + 1) * 15}s"))
        une("launch_true", f"local e = HMT_recenser()[{AV}] local u = ScenEdit_GetUnit({{guid = e.guid}}) "
                           "SORTIE('launch_true', ESSAI(function() return u:Launch(true) end))")
        for i in range(4):
            time.sleep(15)
            une(f"otan_launch_{(i + 1) * 15}s", ETAT.replace("{n}", f"otan_launch_{(i + 1) * 15}s"))
        l.nettoyer()


if __name__ == "__main__":
    main()
