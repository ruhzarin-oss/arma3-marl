"""Sonde croisee de perception ( plans/plan-menace-visible.md v2 ) : menace inerte a 150 m devant, accroupie ou debout,
de nuit ou de jour ; fenetre de 300 s, une ligne toutes les 5 s. 4 jobs, 8 episodes. --poser pour les mettre en file."""
import glob, json, os, shutil, subprocess, sys, time
H = "/mnt/data/hmt"; CAMPAGNE = "SONDE-PERCEPTION-17-09"


def gabarit():
    for jf in sorted(glob.glob(f"{H}/runs/2026-09-17_*/job.json")):
        j = json.load(open(jf))
        if j.get("campagne") == "CHOIX-P2-17-09" and j.get("traversee") == 1:
            return {k: v for k, v in j.items() if k != "note"}
    raise SystemExit("gabarit P2 introuvable")


def jobs():
    g = gabarit(); L = []
    for posture, ctl in (("accroupi", 1), ("debout", 3)):
        for nuit, jour in (("nuit", 0), ("jour", 1)):
            nom = f"{posture}_{nuit}"
            j = dict(g, campagne=CAMPAGNE, graines=[4, 5], repetitions=1, observation=300, sonde=1,
                     controle_perception=ctl, jour=jour, menace_p1=0, menace_p2=0, menace_p3=0, menace_p4=0,
                     menace_p5=0, menace_p6=0, instance=[1, 2, 3, 4][len(L)],
                     version=f"SONDE-{nom}", note=f"Sonde de perception {nom} : menace inerte a 150 m devant, fenetre de 300 s, ligne toutes les 5 s.")
            L.append((f"2026-09-17_SONDE_{len(L)}_{nom}.json", j))
    return L


if __name__ == "__main__":
    poser = "--poser" in sys.argv
    t0 = time.time() - 7200
    for rang, (nom, j) in enumerate(jobs()):
        prep = f"{H}/queue_preparation/{nom}"
        json.dump(j, open(prep, "w"), indent=1, ensure_ascii=True)
        r = subprocess.run(["bash", f"{H}/depot/outils/controle_avant_run.sh", prep], capture_output=True, text=True)
        ok = "CONTROLE OK" in r.stdout
        print(nom, "instance", j["instance"], "ctl", j["controle_perception"], "jour", j["jour"], "OK" if ok else "REFUS : " + " | ".join(l for l in r.stdout.splitlines() if "REFUS" in l))
        if not ok: raise SystemExit("controle refuse")
        if poser: os.utime(prep, (t0 + rang, t0 + rang)); shutil.move(prep, f"{H}/queue/{nom}")
        else: os.remove(prep)
