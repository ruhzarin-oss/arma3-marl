"""Variance de la perception au moment du choix, campagne VARIANCE-PROCHE-18-09 ( niveaux 4 et 5 : un seul type, pose PRES ).
Critere du plan : la part d episodes ou menace_percue > 0 au moment du choix doit tomber dans 30-70 %, par phase et par type."""
import glob, json, os, re, sys
H = "/mnt/data/hmt"
CAMPAGNE = sys.argv[1] if len(sys.argv) > 1 else "VARIANCE-PROCHE-18-09"
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
POINTS = {"TRAVERSEE", "INSERTION_ATTENTE", "ITINERAIRE", "OBS_DUREE", "DELAI_PORTEUR", "EXFIL_ALLURE"}

def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}

E = []
for jf in glob.glob(f"{H}/runs/2026-09-1[89]_*/job.json"):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    phase = int(re.search(r"P(\d)", j["version"]).group(1))
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try:
            v = json.load(open(d + "resultat.json")).get("verdict")
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        dec = [champs(m) for m in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', t)]
        dec = [x for x in dec if x.get("point") in POINTS and int(x.get("phase", -1)) == phase]
        sit = re.search(rf'"CHACAL\|E\|situation\|[^"]*\|phase\|{phase}\|niveau\|(\d+)\|type\|([A-Z_]+)\|hommes\|(\d+)\|[^"]*\|distance\|(\d+)', t)
        x = dec[0] if dec else None
        E.append(dict(version=j["version"], phase=phase, monde=os.path.basename(d.rstrip("/")), verdict=v,
                      erreurs=len(RX_ERR.findall(t)),
                      percue=int(x["menace_percue"]) if x and "menace_percue" in x else None,
                      vues=int(x["menaces_vues"]) if x and "menaces_vues" in x else None,
                      connues=int(x["menaces_connues"]) if x and "menaces_connues" in x else None,
                      niveau=int(sit.group(1)) if sit else None, type=sit.group(2) if sit else None,
                      distance=int(sit.group(4)) if sit else None))
print(f"== {CAMPAGNE} : {len(E)} episodes, {sum(e['verdict']=='ACCEPTE' for e in E)} acceptes, "
      f"{sum(e['erreurs'] for e in E)} erreurs SQF, {sum(e['percue'] is None for e in E)} sans ligne de decision")
P = [e for e in E if e["verdict"] == "ACCEPTE" and e["erreurs"] == 0 and e["percue"] is not None]
print("\n bras            niveau  type                 n   distance posee   PERCUE > 0   dont connue ( niveau 2 )")
ok = True
for v in sorted({e["version"] for e in P}):
    L = [e for e in P if e["version"] == v]
    part = sum(e["percue"] > 0 for e in L) / len(L); part2 = sum(e["percue"] == 2 for e in L) / len(L)
    dmin = min(e["distance"] for e in L if e["distance"]); dmax = max(e["distance"] for e in L if e["distance"])
    dans = 0.30 <= part <= 0.70
    ok &= dans
    print(f" {v:15s} {L[0]['niveau']}     {str(L[0]['type'])[:18]:18s} {len(L):3d}   {dmin:4d}-{dmax:4d} m      "
          f"{part:5.0%} {'DANS 30-70' if dans else 'HORS PLAGE'}    {part2:5.0%}")
# ! LA PORTE NE DOIT PAS POUVOIR ETRE PASSEE POUR LA MAUVAISE RAISON. Le 18/09, les cinq bras donnaient 50 %
# alors que le monde 4 n etait JAMAIS percu et le monde 5 TOUJOURS : une part globale de 50 % peut n etre que
# deux mondes constants. Une regle conditionnee sur la perception serait alors confondue avec le monde.
# On exige donc EN PLUS qu au moins un monde melange les deux issues.
intra = False
for v in sorted({e["version"] for e in P}):
    for w in sorted({e["monde"].split("_")[0] for e in P if e["version"] == v}):
        L = [e for e in P if e["version"] == v and e["monde"].split("_")[0] == w]
        parts = {e["percue"] > 0 for e in L}
        if len(L) > 1 and len(parts) > 1: intra = True
        print(f"   intra-monde {v:18s} {w:5s} : {len(L)} episodes, percue > 0 dans {sum(e['percue'] > 0 for e in L)}"
              f"{'  <- melange' if len(parts) > 1 else '  ( constant )'}")
print(f"\n PORTE, part globale 30-70 % : {'OK' if ok else 'ECHEC'}")
print(f" PORTE, variance A L INTERIEUR d un monde : {'OK' if intra else 'ECHEC - la perception est une propriete du monde, pas de l episode'}")
print(f" DECISION : {'la campagne P2 peut partir' if (ok and intra) else 'la campagne P2 ne part pas ; faire varier le placement ( graine de situation ) ou placer a d* x [0,8 ; 1,2]'}")
print(" detail par episode :")
for e in sorted(P, key=lambda e: (e["version"], e["monde"])):
    print(f"   {e['version']:15s} {e['monde']:8s} percue {e['percue']} ( vues {e['vues']} connues {e['connues']} ) distance {e['distance']} m")
