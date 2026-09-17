"""Genere les 160 jobs des cinq campagnes de choix ( curriculum/CRITERES_CHOIX_17_09.md ). N ecrit que si --ecrire."""
import json, os, sys, time
from collections import Counter
Q = "/mnt/data/hmt/queue"
MONDES = [4, 5, 6, 7, 8, 9, 11, 12]
# ! AMENDEMENT AVANT LANCEMENT ( 17/09, 02:35 ) : le controle avant run refuse un job d une seule graine a moins de 5
# repetitions ( regle de non-singularite ). Les mondes vont donc PAR PAIRES dans un meme job : chaque monde garde ses R
# repetitions, chaque case garde 8 mondes x R episodes. Le dispositif ne change pas, seul le decoupage en jobs change.
PAIRES = [[4, 5], [6, 7], [8, 9], [11, 12]]
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
CAMPAGNES = [  # ordre de la file
    dict(nom="CHOIX-P2-17-09", ph=2, gabarit="2026-09-16_SITUATION_P2_TEMOIN.json", levier="traversee", options=[1, 2], R=4, vig=(2, 2, 0)),
    dict(nom="CHOIX-P1-17-09", ph=1, gabarit="2026-09-16_SITUATION_P1_TEMOIN.json", levier="p1_attente", options=[1, 2], R=4, vig=(1, 1, 0)),
    dict(nom="CHOIX-P4-17-09", ph=4, gabarit="2026-09-16_PHASE4_REGROUPEMENT_TEMOIN.json", levier="itineraire", options=[1, 2], R=4, vig=(3, 4, 0)),
    dict(nom="CHOIX-P3-17-09", ph=3, gabarit="2026-09-16_SITUATION_P3_TEMOIN.json", levier="obs_duree", options=[120, 480], R=3, vig=(3, 3, 1)),
    dict(nom="CHOIX-P6-17-09", ph=6, gabarit="2026-09-16_SITUATION_P6_TEMOIN.json", levier="exfil", options=[0, 1], R=3, vig=(4, 6, 0)),
]
NOTE = ("CAMPAGNE {nom} : le choix {levier} de la phase {ph} selon la situation. Criteres ecrits avant : depot curriculum/CRITERES_CHOIX_17_09.md.\n"
 "Case {bras} ( menace_p{ph} = {men} ), {levier} = {val}, mondes {g}, {R} repetitions par monde. 16 jobs = 2 bras x 2 options x 4 paires de mondes ; les 4 cases d une paire partent ensemble.\n"
 "Decision : modulation ( ecart d option en menace moins en temoin ) etablie si son IC 95 % par reechantillonnage des mondes exclut 0 -> DEPENDANT ;\n"
 "sinon DOMINE si l ecart moyen est etabli, INDIFFERENT sinon. Lecture unique : C:\\hmt\\dbt\\outils\\lire_choix.py {nom}.")
jobs = []
for c in CAMPAGNES:
    gab = json.load(open(f"{Q}/faits/{c['gabarit']}"))
    for paire in PAIRES:
        g = paire[0]
        for bras, men in (("TEMOIN", 0), ("MENACE", 3)):
            for val in c["options"]:
                j = dict(gab)
                for kk in ("partage", "qrf_n", "qrf_delai", "qrf_dist", "acc", "p1_attente", "traversee", "obs_duree", "itineraire"): j.pop(kk, None)
                j.update({c["levier"]: val, f"menace_p{c['ph']}": men, "graines": paire, "repetitions": c["R"], "situation": 1, "vignette": 1,
                          "campagne": c["nom"], "version": f"P{c['ph']}-{bras}-{c['levier']}{val}-g{paire[0]}g{paire[1]}",
                          "note": NOTE.format(nom=c["nom"], levier=c["levier"], ph=c["ph"], bras=bras, men=men, val=val, g=f"{paire[0]} et {paire[1]}", R=c["R"])})
                for x in range(1, 7): j[f"menace_p{x}"] = men if x == c["ph"] else 0
                dep, arr, obs = c["vig"]
                assert (j["depart"], j["arret"], j.get("obs", 1)) == (dep, arr, obs), (c["nom"], j["depart"], j["arret"], j.get("obs"))
                assert j["palier"] == 4 and j["socle"] == 1 and j.get("delai_porteur", 45) == 45 and j.get("exfil", 0) in (0, 1)
                jobs.append(j)
for k, j in enumerate(jobs):
    j["instance"] = INSTANCES[k % len(INSTANCES)]
print(f"{len(jobs)} jobs, {sum(j['repetitions'] * len(j['graines']) for j in jobs)} episodes")
for c in CAMPAGNES:
    js = [j for j in jobs if j["campagne"] == c["nom"]]
    print(f"   {c['nom']} : {len(js)} jobs, {sum(j['repetitions'] * len(j['graines']) for j in js)} episodes, cases {dict(Counter((j['version'].split('-')[1], j[c['levier']]) for j in js))}")
print("   par instance :", dict(Counter(j["instance"] for j in jobs)))
if "--ecrire" in sys.argv:
    t0 = time.time() + 2
    for k, j in enumerate(jobs):
        p = f"{Q}/2026-09-17_CHOIX_{k:03d}_{j['campagne'][6:8]}_{j['version']}.json"
        json.dump(j, open(p, "w"), indent=1, ensure_ascii=True); os.utime(p, (t0 + k, t0 + k))
    print("ecrits dans", Q)
