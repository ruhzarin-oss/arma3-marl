#!/usr/bin/env python3
"""Pose le Lua du pont dans CMO : <CMO>/Lua/hmt_pont/{ hmt_pont.lua, installer.lua, hmt_config.lua }. Ne touche à rien
d'autre du jeu. L'événement garde le Lua déjà chargé : --recharger le fait relire par le pont ( le canari de
cmo_labo.py compare HMT_VERSION ).

    .venv/bin/python cmo/deployer.py [--recharger]
"""
import os
import shutil
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402

FICHIERS = ("hmt_pont.lua", "installer.lua")


def deployer(racine: str = CL.CMO, base_lua: str = CL.BASE_WINDOWS) -> str:
    """`racine` : le dossier de CMO vu d'ici ; `base_lua` : le même dossier vu de CMO ( chemin Windows ), pour loadfile."""
    if "'" in base_lua or "\\" in base_lua or not base_lua.endswith("/"):
        raise ValueError(f"base_lua doit finir par / et n'avoir ni ' ni \\ : {base_lua!r}")
    dest = os.path.join(racine, "Lua", "hmt_pont")
    os.makedirs(dest, exist_ok=True)
    for f in FICHIERS:
        tmp = os.path.join(dest, f".{f}.tmp")
        shutil.copyfile(os.path.join(ICI, "lua", f), tmp)
        os.replace(tmp, os.path.join(dest, f))
    tmp = os.path.join(dest, ".hmt_config.lua.tmp")
    with open(tmp, "w", encoding="utf-8") as g:
        g.write(f"-- écrit par cmo/deployer.py : le dossier de CMO vu de CMO, pour loadfile.\nHMT_BASE = '{base_lua}'\n")
    os.replace(tmp, os.path.join(dest, "hmt_config.lua"))
    return dest


if __name__ == "__main__":
    d = deployer()
    print(f"Lua du pont posé dans {d}")
    if "--recharger" in sys.argv:
        # Le pont bat déjà : il fait relire le Lua à CMO lui-même, sans console.
        print(f"CMO joue maintenant hmt_pont.lua en version {CL.recharger()}")
    else:
        print("Dans CMO : ouvrir le scénario, console Lua, une ligne :")
        print("    ScenEdit_RunScript('hmt_pont/installer.lua')")
        print("puis Ctrl+S, et laisser le temps s'écouler ( x1 ). Si le pont bat déjà : deployer.py --recharger")
