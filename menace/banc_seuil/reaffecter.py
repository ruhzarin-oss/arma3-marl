"""Reaffecte MES jobs en file ( jamais ceux d une autre session ) vers les instances libres. L heure du fichier est conservee ( ordre de la file ).
Un job ne change d instance que si la sienne est occupee ; chaque instance libre recoit au plus un job par passage."""
import glob, json, os, re
H = "/mnt/data/hmt"; MIENS = re.compile(r"_(PORTEE|FO|VO|ACCROUPI|BALAYAGE|P2N|BANC3)_")
TOUTES = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13]
occupees = {int(v[1:]) for v in os.listdir(f"{H}/queue/verrous") if re.fullmatch(r"[ij]\d+", v)}
occupees |= {json.load(open(f))["instance"] for f in glob.glob(f"{H}/queue/en_cours/*.json")}
libres = [i for i in TOUTES if i not in occupees]
prises = set()
for f in sorted(glob.glob(f"{H}/queue/*.json"), key=os.path.getmtime):
    j = json.load(open(f))
    if j["instance"] not in occupees and j["instance"] not in prises: prises.add(j["instance"]); continue      # partira tout seul
    if not MIENS.search(os.path.basename(f)): continue
    cible = next((i for i in libres if i not in prises), None)
    if cible is None: break
    st = os.stat(f); avant = j["instance"]; j["instance"] = cible
    json.dump(j, open(f, "w"), indent=1, ensure_ascii=True); os.utime(f, (st.st_atime, st.st_mtime)); prises.add(cible)
    print(os.path.basename(f), ":", avant, "->", cible)
print("libres :", libres, "| occupees :", sorted(occupees))
