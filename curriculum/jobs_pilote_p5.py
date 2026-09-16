"""Genere les 32 jobs du pilote de la phase 5 ( curriculum/CRITERES_PILOTE_P5.md ). N ecrit que si --ecrire."""
import json, os, sys, time
Q = "/mnt/data/hmt/queue"
MONDES = [4, 5, 6, 7, 8, 9, 11, 12]
CASES = [("TEMOIN", 0, 45), ("TEMOIN", 0, 180), ("MENACE", 3, 45), ("MENACE", 3, 180)]
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
NOTE = ("PILOTE DE LA PHASE 5 : LE DELAI DU PORTEUR SELON LA SITUATION. Criteres ecrits avant : depot curriculum/CRITERES_PILOTE_P5.md.\n"
 "Case {bras} delai {delai} s, monde {g}, 6 repetitions. 32 jobs = 2 bras x 2 delais x 8 mondes ; les 4 cases d un monde partent ensemble.\n"
 "Issue primaire : assaut_utile ( 3 charges et au moins 6 vivants en fin d assaut ). Decision : la modulation ( ecart 180-45 en menace\n"
 "moins ecart 180-45 en temoin ) est-elle etablie ( IC 95 % par reechantillonnage des mondes excluant 0 ) ? Oui : le choix entre au\n"
 "curriculum. Non : choix temoin. Lecture : C:\\hmt\\dbt\\outils\\lire_pilote_p5.py, qui refuse de lire si une porte de qualite echoue.")
gab = json.load(open(f"{Q}/faits/2026-09-16_SITUATION_P5_MENACE.json"))
jobs = []
for g in MONDES:
    for bras, menace, delai in CASES:
        j = dict(gab)
        j.update(menace_p5=menace, delai_porteur=delai, graines=[g], repetitions=6, vignette=1, situation=1,
                 campagne="PILOTE-P5-DELAI-SITUATION-16-09", version=f"P5-{bras}-D{delai}-g{g}",
                 note=NOTE.format(bras=bras, delai=delai, g=g))
        assert j["depart"] == 4 and j["arret"] == 5 and j["obs"] == 0 and j["palier"] == 4 and j["socle"] == 1
        assert all(j[f"menace_p{i}"] == 0 for i in (1, 2, 3, 4, 6)) and j.get("partage") is None and j.get("qrf_n") is None
        jobs.append(j)
for k, j in enumerate(jobs):
    j["instance"] = INSTANCES[k % len(INSTANCES)]
print(f"{len(jobs)} jobs, {sum(j['repetitions'] for j in jobs)} episodes")
from collections import Counter
print("   par case :", Counter((j["version"].split("-")[1], j["delai_porteur"]) for j in jobs))
print("   par instance :", dict(Counter(j["instance"] for j in jobs)))
for k, j in enumerate(jobs[:5] + jobs[-2:]): print("  ", j["version"], "instance", j["instance"])
if "--ecrire" in sys.argv:
    t0 = time.time() + 2
    for k, j in enumerate(jobs):
        p = f"{Q}/2026-09-16_PILOTE_P5_{k:02d}_{j['version']}.json"
        json.dump(j, open(p, "w"), indent=1, ensure_ascii=True); os.utime(p, (t0 + k, t0 + k))
    print("ecrits dans", Q)
