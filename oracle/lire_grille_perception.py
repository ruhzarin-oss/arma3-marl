"""Lecture unique de GRILLE-PERCEPTION-19-09 ( criteres : oracle/CRITERES_GRILLE_PERCEPTION.md, ecrits avant ).
Un canal est RETENU s il distingue dans au moins 50 % des episodes avec une specificite de 100 %.
Falsificateur : un seul moteur entendu dans le bras POSTE ou AUCUNE, et le canal est retire."""
import glob, json, os, re, sys
H = "/mnt/data/hmt"
CAMPAGNE = "GRILLE-PERCEPTION-19-09"
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
BRAS = {4: "PATROUILLE", 5: "POSTE", 0: "AUCUNE"}


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-19_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try:
            v = json.load(open(d + "resultat.json")).get("verdict")
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        m = re.search(r'"CHACAL\|E\|decision\|[^"]*point\|TRAVERSEE\|([^"]*)"', t)
        sondes = [champs(s) for s in re.findall(r'"CHACAL\|E\|sonde_decision\|([^"]*)"', t)]
        E.append(dict(bras=BRAS[j["menace_p2"]], monde=int(re.search(r"/g(\d+)", d).group(1)), situation=j["situation"],
                      verdict=v, erreurs=len(RX_ERR.findall(t)), dec=champs(m.group(1)) if m else None, sondes=sondes))
A = [e for e in E if e["verdict"] == "ACCEPTE" and e["erreurs"] == 0 and e["dec"]]
print(f"== GRILLE DE PERCEPTION : {len(E)} episodes, {len(A)} acceptes sans erreur SQF et avec decision")
for b in BRAS.values():
    print(f"   {b:11s} : {sum(1 for e in A if e['bras'] == b)} episodes")


def n(e, k, d=0):
    try: return float(e["dec"].get(k, d))
    except Exception: return d


def part(L, f):
    return (sum(1 for e in L if f(e)) / len(L)) if L else float("nan")


P = [e for e in A if e["bras"] == "PATROUILLE"]; Q = [e for e in A if e["bras"] == "POSTE"]; N = [e for e in A if e["bras"] == "AUCUNE"]
print("\n== LE CRITERE ECRIT D AVANCE")
sens = part(P, lambda e: n(e, "moteur_entendu") > 0)
fauxQ = sum(1 for e in Q if n(e, "moteur_entendu") > 0); fauxN = sum(1 for e in N if n(e, "moteur_entendu") > 0)
print(f"   moteur entendu : sensibilite {sens:5.0%} ( {sum(1 for e in P if n(e,'moteur_entendu')>0)}/{len(P)} en patrouille )")
print(f"                    faux positifs : {fauxQ} en POSTE, {fauxN} en AUCUNE -> specificite "
      f"{(1 - (fauxQ + fauxN) / max(1, len(Q) + len(N))):.0%}")
retenu = sens >= 0.50 and fauxQ == 0 and fauxN == 0
print(f"   -> canal {'RETENU' if retenu else 'REFUSE'} ( il faut 50 % de sensibilite ET 100 % de specificite )")
mobP = part(P, lambda e: n(e, "menace_mobile_vue", -1) == 1)
mobQ = part(Q, lambda e: n(e, "menace_mobile_vue", -1) == 1)
print(f"   mobilite vue   : mobile dans {mobP:5.0%} des patrouilles, {mobQ:5.0%} des postes "
      f"( renseignee dans {part(P + Q, lambda e: n(e, 'menace_mobile_vue', -1) >= 0):.0%} des episodes )")
trancher = part(P + Q, lambda e: (n(e, "moteur_entendu") > 0) or (n(e, "menace_mobile_vue", -1) >= 0))
print(f"\n   POUVOIR DE TRANCHER : {trancher:.0%} des episodes ou au moins un canal parle")

print("\n== LES QUESTIONS SUIVANTES, REPONDUES SANS REJOUER")
print("   a. quelle portee ? part des patrouilles ou un moteur tourne a moins de R metres")
for R in (300, 600, 900, 1200, 2000):
    p = part(P, lambda e, R=R: 0 <= n(e, "distance_moteur", -1) < R)
    q = part(Q + N, lambda e, R=R: 0 <= n(e, "distance_moteur", -1) < R)
    print(f"      R = {R:5d} m : sensibilite {p:5.0%}   faux positifs {q:5.0%}")
print(f"   b. le relief : vue du vehicule dans {part(P, lambda e: n(e,'vue_vehicule')>0):.0%} des patrouilles "
      f"( le son porte donc SANS ligne de vue dans {part(P, lambda e: n(e,'moteur_entendu')>0 and n(e,'vue_vehicule')==0):.0%} )")
print(f"   c. pourquoi ca rate : moteur allume dans {part(P, lambda e: n(e,'moteur_allume')>0):.0%} des patrouilles ; "
      f"distance mediane {sorted(n(e,'distance_moteur',-1) for e in P)[len(P)//2] if P else '-'} m")
print(f"   d. pourquoi mobilite = -1 : l oeil a vu la menace {part(P + Q, lambda e: n(e,'n_vues_menace')>=2):.0%} "
      f"des fois au moins DEUX fois ( il en faut deux )")
print("   e. quelle duree de fenetre ? part des episodes ou le moteur s entend AU MOINS UNE FOIS avant t")
for W in (30, 60, 90, 120, 180, 300, 600):
    def vu(e, W=W):
        return any(float(s.get("moteur_entendu", 0)) > 0 for s in e["sondes"] if float(s.get("depuis", 1e9)) <= W)
    print(f"      fenetre {W:4d} s : patrouille {part(P, vu):5.0%}   poste+aucune {part(Q + N, vu):5.0%}")
print("\n== FALSIFICATEUR")
print(f"   « un seul moteur entendu en POSTE ou AUCUNE et le canal est retire » : "
      f"{'NON FRANCHI' if (fauxQ + fauxN) == 0 else f'FRANCHI ( {fauxQ + fauxN} faux positifs )'}")
