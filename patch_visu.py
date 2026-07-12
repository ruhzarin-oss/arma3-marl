"""patch_visu — branche run_op_visual sur le theatre Paros (via HMT_THEATER) + braque la camera de preview
sur Paros. Idempotent (re-execute sans casser)."""
import os

# 1) run_op_visual.py : import conditionnel du theatre + ne pas forcer les spawns/LZ de l'ancien complexe pour Paros
f = "run_op_visual.py"; s = open(f).read()
if "HMT_THEATER" not in s:
    s = s.replace("import maneuvers as M",
                  "if os.environ.get('HMT_THEATER') == 'paros':\n    import paros as M\nelse:\n    import maneuvers as M", 1)
    s = s.replace("        spawns = VISU_SPAWNS",
                  "        if os.environ.get('HMT_THEATER') != 'paros':\n            spawns = VISU_SPAWNS", 1)
    s = s.replace("        plan = _swap_point(plan, M.LZ, VISU_LZ)",
                  "        if os.environ.get('HMT_THEATER') != 'paros':\n            plan = _swap_point(plan, M.LZ, VISU_LZ)", 1)
    open(f, "w").write(s)
    print("run_op_visual.py patche (theatre conditionnel).")
else:
    print("run_op_visual.py deja patche.")

# 2) camera de la preview EDEN -> Paros (20885,16959)
ED = "/mnt/data/harmattan-sandbox/Steam/steamapps/compatdata/107410/pfx/drive_c/users/steamuser/Documents/Arma 3/missions/HMT-EcoleDeGuerre.Altis/initPlayerLocal.sqf"
if os.path.exists(ED):
    c = open(ED).read()
    c = c.replace("[15000, 15950, 800]", "[20885, 16959, 800]")     # vue du dessus -> Paros
    c = c.replace("[15000, 15960, 0]", "[20885, 16959, 0]")
    c = c.replace("[15000, 15350, 550]", "[20885, 16359, 550]")     # vue oblique (depuis le sud de Paros)
    c = c.replace("[15000, 16000, 0]", "[20885, 16959, 0]")
    open(ED, "w").write(c)
    print("camera EDEN -> Paros.")
else:
    print("mission EDEN introuvable (chemin) :", ED)
