#!/usr/bin/env python3
"""sans_pauses — coupe les pauses automatiques de CMO : les pop-ups du journal des messages.

Dans CMO, un type de message réglé sur « Raise Pop-Up » ouvre une fenêtre ET met le jeu en pause jusqu'à ce qu'on
clique ( manuel, 6.4.3 ). Nuit du 29/09 : le jeu s'est figé à 2 h 50, après 2 h 11 de vol des F-15C ( carburant :
UnitAIEmergency ), 3 h 49 de PontMort. Le réglage vit dans Config/Command.ini, section [MessageLog Preferences] :
Type = journal|pop-up|bulle|retour_x1, -1 vrai, 0 faux. On met le 2e champ à 0 partout, rien d'autre.

⚠️ CMO réécrit Command.ini EN QUITTANT : modifier le fichier pendant qu'il tourne serait effacé. Le script refuse donc
de toucher au fichier tant que Command.exe tourne ; --attendre attend sa fermeture, applique, et vérifie.
⚠️ Le réglage est global : les scénarios ordinaires perdent aussi leurs pop-ups ( briefings, messages spéciaux ).
--retablir remet la copie d'avant.

    .venv312/bin/python cmo/sans_pauses.py [--attendre | --retablir | --voir]
"""
import os
import shutil
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402

INI = os.path.join(CL.CMO, "Config", "Command.ini")
COPIE = INI + ".hmt-avant-sans-pauses"
SECTION = b"[MessageLog Preferences]"
POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"


def cmo_tourne():
    r = subprocess.run([POWERSHELL, "-NoProfile", "-Command",
                        "if (Get-Process Command -ErrorAction SilentlyContinue) { 'oui' } else { 'non' }"],
                       capture_output=True, text=True, timeout=30)
    rep = r.stdout.strip()
    if rep not in ("oui", "non"):
        raise RuntimeError(f"impossible de savoir si CMO tourne : {r.stdout!r} {r.stderr[:200]!r}")
    return rep == "oui"


def lignes_messages(octets):
    """[ ( index de ligne, type, champs ) ] de la section, sur les octets du fichier ( fins de ligne gardées )."""
    lignes = octets.splitlines(keepends=True)
    out, dedans = [], False
    for i, l in enumerate(lignes):
        s = l.strip()
        if s.startswith(b"["):
            dedans = s == SECTION
            continue
        if dedans and b"=" in s:
            cle, val = (x.strip() for x in s.split(b"=", 1))
            out.append((i, cle.decode("latin-1"), val.decode("latin-1").split("|")))
    return lignes, out


def popups(octets):
    return {t: c[1] == "-1" for _, t, c in lignes_messages(octets)[1] if len(c) >= 2}


def appliquer():
    if cmo_tourne():
        raise RuntimeError("Command.exe tourne : il réécrirait Command.ini en quittant. Fermer CMO, ou --attendre.")
    octets = open(INI, "rb").read()
    if not os.path.exists(COPIE):
        shutil.copy2(INI, COPIE)
    lignes, msgs = lignes_messages(octets)
    if not msgs:
        raise RuntimeError(f"section {SECTION.decode()} introuvable dans {INI}")
    coupes = []
    for i, t, c in msgs:
        if len(c) >= 2 and c[1] != "0":
            c[1] = "0"
            fin = lignes[i][len(lignes[i].rstrip(b"\r\n")):]
            lignes[i] = f"{t} = {'|'.join(c)}".encode("latin-1") + fin
            coupes.append(t)
    tmp = INI + ".tmp"
    with open(tmp, "wb") as g:
        g.write(b"".join(lignes))
    os.replace(tmp, INI)
    reste = [t for t, p in popups(open(INI, "rb").read()).items() if p]
    if reste:
        raise RuntimeError(f"pop-ups encore actifs après écriture : {reste}")
    return coupes


def retablir():
    if cmo_tourne():
        raise RuntimeError("Command.exe tourne : fermer CMO d'abord")
    shutil.copy2(COPIE, INI)
    return [t for t, p in popups(open(INI, "rb").read()).items() if p]


if __name__ == "__main__":
    if "--voir" in sys.argv:
        print({t: p for t, p in popups(open(INI, "rb").read()).items() if p} or "aucun pop-up")
    elif "--retablir" in sys.argv:
        print("pop-ups rétablis :", retablir())
    else:
        if "--attendre" in sys.argv:
            print(time.strftime("%H:%M:%S"), "j'attends la fermeture de CMO", flush=True)
            while cmo_tourne():
                time.sleep(2)
        print(time.strftime("%H:%M:%S"), "pop-ups coupés :", appliquer(), flush=True)
