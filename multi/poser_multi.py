"""Pose les jobs de l episode multiple. Base commune = un job reel de l Oracle ( memes parametres ). Usage : poser_multi.py fumee|charge"""
import glob, json, sys, time
H = "/mnt/data/hmt"
base = json.load(open(sorted(glob.glob(f"{H}/queue_suspendue/*.json"))[0]))
for k in ("graines", "situation", "menace_p2", "traversee", "version", "note", "oracle_ctrl", "instance", "azimut_val"):
    base.pop(k, None)
base.update({"banc": "chacalmulti", "repetitions": 1, "plafond_s": 5400, "multi_tmax": 1500, "multi_sonde": 1, "multi_espacement": 3000})
quoi = sys.argv[1]
if quoi == "fumee":
    pos = lambda w: {"graine": w, "oracle_ctrl": 1, "menace_p2": 1, "oracle_cmd": 1, "situation": 1, "traversee": 1, "role": "positif"}
    neg = lambda w: {"graine": w, "palier": 9, "menace_p2": 0, "oracle_cmd": 0, "situation": 1, "traversee": 1, "role": "negatif"}
    job = dict(base, instance=1, graines=[1, 2], episodes={"1": [pos(8), neg(120)], "2": [pos(120), neg(8)]},
               note="Episode multiple, etape 1 : fumee K = 2, controle positif et negatif, mondes echanges ( multi/CRITERES_MULTI.md ).")
    nom = "MULTI-FUMEE"
elif quoi == "charge":
    MONDES = [8, 120, 217, 223, 230]; P2 = [5, 4, 3, 1, 2]
    def cellules(k, ep):
        return [{"graine": MONDES[i], "menace_p2": P2[i], "traversee": 1 + ((i + ep) % 2), "situation": ep, "oracle_cmd": 1, "role": f"charge_k{k}"} for i in range(k)]
    ordre = [1, 5, 5, 5, 1, 1, 3, 3, 3, 2, 2, 2]
    job = dict(base, instance=1, graines=list(range(1, len(ordre) + 1)),
               episodes={str(e): cellules(k, e) for e, k in enumerate(ordre, start=1)},
               note="Episode multiple, etape 2 : charge C3, K dans {1,2,3,5}, 3 episodes chacun, un serveur a la fois ( multi/CRITERES_MULTI.md ).")
    nom = "MULTI-CHARGE"
f = f"{H}/queue/{nom}-{time.strftime('%Y%m%d-%H%M%S')}.json"
json.dump(job, open(f, "w"), indent=1)
print("pose :", f, "| episodes :", {e: [c["graine"] for c in v] for e, v in job["episodes"].items()})
