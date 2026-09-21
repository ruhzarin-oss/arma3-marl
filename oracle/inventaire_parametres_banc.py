"""Inventaire de TOUT ce que le banc chacaloracle expose : chaque parametre de mission ( description.ext ), ses
valeurs permises, sa lecture dans 00_socle.sqf, et s il est pilotable par un job ( lancer.sh )."""
import re
M = "/mnt/data/hmt/depot/bancs/chacaloracle"
de = open(f"{M}/mission.Altis/description.ext", encoding="utf-8", errors="ignore").read()
so = open(f"{M}/mission.Altis/chacal/00_socle.sqf", encoding="utf-8", errors="ignore").read()
la = open(f"{M}/lancer.sh", encoding="utf-8", errors="ignore").read()
blocs = re.findall(r"class\s+(CHACAL_[A-Z0-9_]+)\s*\{(.*?)\};", de, flags=re.S)
print(f"{len(blocs)} parametres de mission\n")
for nom, corps in blocs:
    titre = re.search(r'title\s*=\s*"([^"]*)"', corps); vals = re.search(r"values\[\]\s*=\s*\{([^}]*)\}", corps)
    defaut = re.search(r"default\s*=\s*(-?\d+)", corps)
    court = nom.replace("CHACAL_", "")
    pilote = bool(re.search(rf"ecrire_param\s+{court}\b", la))
    lu = nom in so
    print(f"{court:<24} pilotable={'oui' if pilote else 'NON'} lu={'oui' if lu else 'NON'} defaut={defaut.group(1) if defaut else '?':>5} "
          f"valeurs={vals.group(1).strip()[:70] if vals else '?':<72} | {titre.group(1)[:90] if titre else ''}")
