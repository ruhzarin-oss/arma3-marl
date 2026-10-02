#!/usr/bin/env python3
"""Pose le Lua du pont dans CMO : <CMO>/Lua/hmt_pont/{ hmt_pont.lua, installer.lua, hmt_config.lua }. Ne touche à rien
d'autre du jeu. L'événement garde le Lua déjà chargé : --recharger le fait relire par le pont ( le canari de
cmo_labo.py compare HMT_VERSION ).

    .venv/bin/python cmo/deployer.py [--recharger]
"""
import os
import re
import shutil
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402

FICHIERS = ("hmt_pont.lua", "installer.lua")


FICHIER_INST = re.compile(r"[A-Za-z0-9 _\-\[\]\(\)\.,&/]{1,160}\.inst")


def deployer(racine: str = CL.CMO, base_lua: str = CL.BASE_WINDOWS, camps=CL.CAMPS, installations=()) -> str:
    """`racine` : le dossier de CMO vu d'ici ; `base_lua` : le même dossier vu de CMO ( chemin Windows ), pour loadfile ;
    `camps` : les camps du théâtre ( lettres, chiffres, espace et tiret seulement : ils vont en clair dans un fichier Lua )."""
    if "'" in base_lua or "\\" in base_lua or not base_lua.endswith("/"):
        raise ValueError(f"base_lua doit finir par / et n'avoir ni ' ni \\ : {base_lua!r}")
    for c in camps:
        if not re.fullmatch(r"[A-Za-z0-9 \-]{1,40}", c):
            raise ValueError(f"nom de camp refusé : {c!r}")
    for f in installations:                              # du texte qui entre dans CMO : écrit ici, jamais par l'agent
        if not FICHIER_INST.fullmatch(f) or ".." in f or f.startswith("/"):
            raise ValueError(f"fichier d'installation refusé : {f!r}")
    dest = os.path.join(racine, "Lua", "hmt_pont")
    os.makedirs(dest, exist_ok=True)
    for f in FICHIERS:
        tmp = os.path.join(dest, f".{f}.tmp")
        shutil.copyfile(os.path.join(ICI, "lua", f), tmp)
        os.replace(tmp, os.path.join(dest, f))
    tmp = os.path.join(dest, ".hmt_config.lua.tmp")
    with open(tmp, "w", encoding="utf-8") as g:
        g.write(f"-- écrit par cmo/deployer.py : le dossier de CMO vu de CMO ( pour loadfile ) et les camps du théâtre.\n"
                f"HMT_BASE = '{base_lua}'\nHMT_CAMPS_CONFIG = {{ {', '.join(repr(c) for c in camps)} }}\n"
                f"HMT_INSTALLATIONS_CONFIG = {{ {', '.join(repr(f) for f in installations)} }}\n")
    os.replace(tmp, os.path.join(dest, "hmt_config.lua"))
    return dest


if __name__ == "__main__":
    camps = tuple(sys.argv[sys.argv.index("--camps") + 1].split(",")) if "--camps" in sys.argv else CL.CAMPS
    d = deployer(camps=camps)
    print(f"camps : {list(camps)}")
    print(f"Lua du pont posé dans {d}")
    if "--recharger" in sys.argv:
        # Le pont bat déjà : il fait relire le Lua à CMO lui-même, sans console.
        print(f"CMO joue maintenant hmt_pont.lua en version {CL.recharger()}")
        print("⚠️ changer de camps demande aussi de relancer installer.lua ( il crée les camps dans CMO )")
    else:
        print("Dans CMO : ouvrir le scénario, console Lua, une ligne :")
        print("    ScenEdit_RunScript('hmt_pont/installer.lua')")
        print("puis Ctrl+S, et laisser le temps s'écouler ( x1 ). Si le pont bat déjà : deployer.py --recharger")
