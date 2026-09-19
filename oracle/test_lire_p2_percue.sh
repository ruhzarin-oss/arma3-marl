cd /mnt/c/hmt/tmp/oracle
python3 - <<'PY'
src = open("lire_p2_percue.py").read()
src = src.replace('CAMPAGNE = "P2-PERCUE-19-09"', 'CAMPAGNE = "CHOIX-P2-TYPES-19-09"')
# perception FICTIVE egale au type : le lecteur doit alors rendre, pour la perception, exactement la modulation par le type
src = src.replace("prevus = 2 * 2 * 8 * 4", "for e in E:\n    e['fenetre'] = int(e['bras'] == 'PATROUILLE'); e['instant'] = e['fenetre']\nprevus = 2 * 2 * 8 * 4")
open("test_lecteur.py", "w").write(src)
PY
/mnt/data/hmt/equation/.venv/bin/python test_lecteur.py --sans-monde 11 2>&1 | head -40
