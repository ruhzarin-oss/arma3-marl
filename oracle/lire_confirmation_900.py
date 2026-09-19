"""Lecture unique de CONFIRMATION-900-19-09 ( criteres : oracle/CRITERES_CONFIRMATION_900.md, ecrits avant ).
Confirme si la sensibilite de moteur_depuis_fenetre >= 80 % ET zero faux positif. Infirme sous 65 % ou au premier
faux positif : on revient alors a 600 m, pre-enregistre et deja tenu."""
import glob, json, os, re
H = "/mnt/data/hmt"
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
BRAS = {4: "PATROUILLE", 5: "POSTE", 0: "AUCUNE"}


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != "CONFIRMATION-900-19-09": continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try:
            v = json.load(open(d + "resultat.json")).get("verdict")
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        m = re.search(r'"CHACAL\|E\|decision\|[^"]*point\|TRAVERSEE\|([^"]*)"', t)
        E.append(dict(bras=BRAS[j["menace_p2"]], monde=int(re.search(r"/g(\d+)", d).group(1)), situation=j["situation"],
                      verdict=v, erreurs=len(RX_ERR.findall(t)), dec=champs(m.group(1)) if m else None))
A = [e for e in E if e["verdict"] == "ACCEPTE" and e["erreurs"] == 0 and e["dec"]]
print(f"== CONFIRMATION 900 m : {len(E)} episodes, {len(A)} lus ( graines de situation 5, 6, 7 : NEUVES )")


def n(e, k, d=0):
    try: return float(e["dec"].get(k, d))
    except Exception: return d


def part(L, f): return (sum(1 for e in L if f(e)) / len(L)) if L else float("nan")


P = [e for e in A if e["bras"] == "PATROUILLE"]; Q = [e for e in A if e["bras"] == "POSTE"]; N = [e for e in A if e["bras"] == "AUCUNE"]
print(f"   PATROUILLE {len(P)} | POSTE {len(Q)} | AUCUNE {len(N)}")
for nom, cle in (("moteur_depuis_fenetre ( le canal retenu )", "moteur_depuis_fenetre"),
                 ("moteur_entendu ( a l instant du choix )", "moteur_entendu")):
    s = part(P, lambda e, c=cle: n(e, c) > 0)
    fq = sum(1 for e in Q if n(e, cle) > 0); fn = sum(1 for e in N if n(e, cle) > 0)
    print(f"\n   {nom}")
    print(f"      sensibilite {s:5.0%} ( {sum(1 for e in P if n(e,cle)>0)}/{len(P)} )   faux positifs : {fq} POSTE, {fn} AUCUNE")
s = part(P, lambda e: n(e, "moteur_depuis_fenetre") > 0)
fq = sum(1 for e in Q if n(e, "moteur_depuis_fenetre") > 0); fn = sum(1 for e in N if n(e, "moteur_depuis_fenetre") > 0)
print("\n== LE CRITERE ECRIT D AVANCE")
if fq + fn > 0: print(f"   INFIRME : {fq + fn} faux positif(s) -> retour a 600 m")
elif s >= 0.80: print(f"   CONFIRME : sensibilite {s:.0%} >= 80 % et zero faux positif -> 900 m et memoire de fenetre adoptes")
elif s < 0.65: print(f"   INFIRME : sensibilite {s:.0%} < 65 % -> retour a 600 m")
else: print(f"   INDECIS : sensibilite {s:.0%} entre 65 et 80 % -> on garde 600 m et on double les episodes")
print(f"\n   distance mediane au moteur, en patrouille : "
      f"{sorted(n(e,'distance_moteur',-1) for e in P)[len(P)//2] if P else '-'} m")
print(f"   falsificateur « un seul faux positif a 900 m » : {'NON FRANCHI' if fq + fn == 0 else 'FRANCHI'}")
