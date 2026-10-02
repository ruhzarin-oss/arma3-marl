#!/usr/bin/env python3
"""reglages_perf — les réglages de CMO qui coûtent du temps de calcul, posés dans Config/Command.ini CMO FERMÉ ( il réécrit
le fichier en quittant ). 02/10 : la guerre réelle ( 228 avions, 2 056 éléments ) tournait à x0,33 avec le calcul
multicœur COUPÉ ( RunCoreMultithreaded = False : un cœur et demi sur 24 ), la sauvegarde automatique toutes les 20 s
( tout le scénario réécrit ) et le journal de débogage écrit en continu. La FAQ officielle conseille aussi de couper
« Hi-fidelity mode » et « No-pulse time mode » ( menu des options, hors de ce fichier ).

    python3 cmo/reglages_perf.py [--voir | --retablir]
"""
import os
import re
import shutil
import subprocess
import sys

INI = "/mnt/e/SteamLibrary/steamapps/common/Command - Modern Operations/Config/Command.ini"
COPIE = INI + ".hmt-avant-perf"
VOULU = {"RunCoreMultithreaded": "True", "UseAutosave": "False", "LogDebugInfoToFile": "False"}


def cmo_tourne():
    r = subprocess.run(["/mnt/c/Windows/System32/tasklist.exe"], capture_output=True)
    return b"Command.exe" in r.stdout


def lire():
    with open(INI, encoding="utf-8-sig") as f:
        return f.read()


def voir():
    t = lire()
    return {k: (re.search(rf"^{k} = (\S+)", t, re.M) or [None, "absent"])[1] for k in VOULU}


if __name__ == "__main__":
    if "--voir" in sys.argv:
        print(voir())
        sys.exit(0)
    if cmo_tourne():
        sys.exit("CMO tourne : il réécrirait Command.ini en quittant. Le fermer d'abord.")
    if "--retablir" in sys.argv:
        if not os.path.exists(COPIE):
            sys.exit("rien à rétablir")
        shutil.copyfile(COPIE, INI)
        print("rétabli :", voir())
        sys.exit(0)
    if not os.path.exists(COPIE):
        shutil.copyfile(INI, COPIE)
    t = lire()
    for k, v in VOULU.items():
        t = re.sub(rf"^{k} = \S+", f"{k} = {v}", t, flags=re.M)
    with open(INI, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(t.replace("\r\n", "\n"))
    print("appliqué :", voir())
