"""
Jobs des controles « menace visible » ( menace/CONTROLES_MENACE_VISIBLE.md ). Gabarits : les jobs des campagnes de choix
de la nuit ( memes vignettes ). --poser : controle avant run puis file ; sinon a sec.
"""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"
CAMPAGNE = "CONTROLE-MENACE-VISIBLE-17-09"
INSTANCES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]


def gabarit(campagne, **filtre):
    for jf in sorted(glob.glob(f"{H}/runs/2026-09-17_*/job.json")):
        j = json.load(open(jf))
        if j.get("campagne") == campagne and all(j.get(k) == v for k, v in filtre.items()):
            return {k: v for k, v in j.items() if k not in ("note",)}
    raise SystemExit(f"gabarit introuvable : {campagne} {filtre}")


def jobs():
    p2 = gabarit("CHOIX-P2-17-09", traversee=1)
    p1 = gabarit("CHOIX-P1-17-09", p1_attente=1)
    p4 = gabarit("CHOIX-P4-17-09", itineraire=1)
    L = []
    def ajouter(nom, base, graines, reps, **champs):
        j = dict(base, campagne=CAMPAGNE, graines=graines, repetitions=reps, observation=90, controle_perception=0,
                 menace_p1=0, menace_p2=0, menace_p3=0, menace_p4=0, menace_p5=0, menace_p6=0)
        j.update(champs)
        j["version"] = f"MV-{nom}-g{'g'.join(map(str, graines))}"
        j["note"] = f"Controle menace visible {nom} ( plans/plan-menace-visible.md, menace/CONTROLES_MENACE_VISIBLE.md )."
        L.append((f"2026-09-17_MV_{len(L):02d}_{nom}.json", j))
    ajouter("ORIGINE", p2, [4, 5], 1, observation=0, menace_p2=3)
    for w in ([4, 5], [6, 7]):
        ajouter("POSITIF", p2, w, 2, controle_perception=1)
        ajouter("NEGATIF", p2, w, 2, controle_perception=2)
        ajouter("NUL", p2, w, 2)
        ajouter("P2_TYPE1", p2, w, 2, menace_p2=1)
        ajouter("P2_TYPE2", p2, w, 2, menace_p2=2)
        ajouter("P1_TYPE1", p1, w, 2, menace_p1=1)
        ajouter("P1_TYPE2", p1, w, 2, menace_p1=2)
        ajouter("P4_TYPE1", p4, w, 2, menace_p4=1)
        ajouter("P4_TYPE2", p4, w, 2, menace_p4=2)
    for i, (nom, j) in enumerate(L):
        j["instance"] = INSTANCES[i % len(INSTANCES)]
    return L


if __name__ == "__main__":
    poser = "--poser" in sys.argv
    t0 = time.time() - 7200
    for rang, (nom, j) in enumerate(jobs()):
        prep = f"{H}/queue_preparation/{nom}"
        json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
        r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
        ok = "CONTROLE OK" in r.stdout
        print(nom, j["instance"], j["graines"], j["repetitions"], "obs", j["observation"], "ctl", j["controle_perception"],
              "m1/m2/m4", j["menace_p1"], j["menace_p2"], j["menace_p4"], "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
        if not ok:
            raise SystemExit("un controle refuse : rien n est pose")
        if poser:
            os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
        else:
            os.remove(prep)
