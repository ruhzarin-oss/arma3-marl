#!/usr/bin/env python3
"""poser_preset.py — inscrit @A3U comme mod local du launcher et pose le preset serveur.

Le preset colle EXACTEMENT au -mod du serveur Antistasi : @CBA_A3 puis @A3U, tires
du meme dossier /mnt/data/harmattan-sandbox/mods que le serveur. Meme fichiers des
deux cotes, donc aucune divergence possible client/serveur.

A lancer launcher FERME : il reecrit Local.json en sortant.
"""
import json, pathlib

PFX = pathlib.Path("/mnt/data/harmattan-sandbox/Steam/steamapps/compatdata/107410/pfx")
LAUNCHER = PFX / "drive_c/users/steamuser/AppData/Local/Arma 3 Launcher"
LOCAL = LAUNCHER / "Local.json"
PRESETS = LAUNCHER / "Presets"

MODS_WIN = [
    r"Z:\mnt\data\harmattan-sandbox\mods\@CBA_A3",
    r"Z:\mnt\data\harmattan-sandbox\mods\@A3U",
]

# 1) inscrire les mods dans le registre local du launcher
d = json.loads(LOCAL.read_text(encoding="utf-8-sig"))
for cle in ("knownLocalMods", "userDirectories"):
    liste = d.get(cle, [])
    for m in MODS_WIN:
        if m not in liste:
            liste.append(m)
    d[cle] = liste
LOCAL.write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")
print("Local.json :", len(d["knownLocalMods"]), "mods locaux connus")

# 2) poser le preset
ids = "\n".join("    <id>local:%s</id>" % m for m in MODS_WIN)
xml = (
    '\ufeff<?xml version="1.0" encoding="utf-8"?>\n'
    "<addons-presets>\n"
    "  <last-update>2026-08-10T19:45:00.0000000+02:00</last-update>\n"
    "  <published-ids>\n"
    + ids + "\n"
    "  </published-ids>\n"
    "  <dlcs-appids />\n"
    "</addons-presets>\n"
)
cible = PRESETS / "HMT-Antistasi.preset2"
cible.write_text(xml, encoding="utf-8")
print("preset pose :", cible.name)
print(xml)
