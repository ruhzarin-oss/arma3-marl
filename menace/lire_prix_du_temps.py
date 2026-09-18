"""Lecture unique du test du prix du temps ( menace/CRITERES_PRIX_DU_TEMPS.md, amendement 1 ). Ecrite avant les episodes.
  python lire_prix_du_temps.py [ CAMPAGNE ]
Issue primaire : mission_reussie = 3 charges ET au moins 6 exfiltres. Trois controles d instrument peuvent annuler la lecture."""
import glob, json, os, re, sys
import numpy as np
H = "/mnt/data/hmt"
CAMPAGNE = sys.argv[1] if len(sys.argv) > 1 else "PRIX-DU-TEMPS-V2-18-09"
B, GRAINE, SEUIL, DERIVE_MAX = 10000, 20260918, 0.10, 30
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1)}


E = []
for jf in glob.glob(f"{H}/runs/2026-09-*/job.json"):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try:
            v = json.load(open(d + "resultat.json")).get("verdict")
            rpt = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        m = re.search(r'"CHACAL\|FINI\|([^"]*)"', rpt)
        if not m: continue
        f = champs(m.group(1))
        fin = re.search(r'"CHACAL\|E\|attente_test\|[^"]*\|fin\|duree\|(\d+)[^"]*\|derive\|(\d+)', rpt)
        disp = re.findall(r'"CHACAL\|E\|dispositif\|[0-9.]+\|appui\|(\d)\|assaut\|(\d)\|bouchon\|(\d)', rpt)
        E.append(dict(attente=int(j.get("attente_test", 0)),
                      monde=int(re.match(r"g(\d+)", os.path.basename(d.rstrip("/"))).group(1)),
                      verdict=v, erreurs=len(RX_ERR.findall(rpt)),
                      exfiltres=int(f.get("exfiltres", -1)), charges=int(f.get("charges", -1)),
                      vivants=int(f.get("vivants", -1)), alarme=int(f.get("alarme", -1)),
                      compromis=int(f.get("compromis", -1)), duree=int(f.get("duree", -1)),
                      issue=f.get("issue", ""), cause=m.group(1).split("|")[1],
                      attente_jouee=int(fin.group(1)) if fin else 0, derive=int(fin.group(2)) if fin else 0,
                      assaut_en_place=int(disp[0][1]) if disp else -1))
P = [e for e in E if e["verdict"] == "ACCEPTE" and e["erreurs"] == 0]
print(f"== PRIX DU TEMPS ( {CAMPAGNE} ) : {len(E)} episodes, {len(P)} acceptes sans erreur SQF")
if not P: raise SystemExit
for e in P:
    e["reussi"] = int(e["charges"] >= 3 and e["exfiltres"] >= 6)     # issue primaire, amendement 1
    e["exfil"] = int(e["exfiltres"] >= 6)
    e["trois_charges"] = int(e["charges"] >= 3)
    e["rompue"] = int(e["cause"] == "ARTICULATION_ROMPUE")
niveaux = sorted({e["attente"] for e in P}); mondes = sorted({e["monde"] for e in P})

print("\n== CONTROLES D INSTRUMENT ( ecrits avant les episodes ; un echec annule la lecture )")
att = [e for e in P if e["attente"] > 0]
c1 = (np.mean([e["derive"] <= DERIVE_MAX for e in att]) if att else 1.0)
print(f"   1. derive <= {DERIVE_MAX} m : {c1:.0%} des episodes qui attendent "
      f"( max {max([e['derive'] for e in att], default=0)} m ) -> {'OK' if c1 >= 0.95 else 'ECHEC'}")
c2 = c3 = True
for n in niveaux:
    L = [e for e in P if e["attente"] == n]
    place = np.mean([e["assaut_en_place"] == 1 for e in L]); rompue = np.mean([e["rompue"] for e in L])
    c2 &= place >= 0.80; c3 &= rompue < 0.20
    print(f"   2/3. {n:5d} s : assaut a sa place {place:.0%} ( >= 80 % ) ; abandon ARTICULATION_ROMPUE {rompue:.0%} ( < 20 % )"
          f" -> {'OK' if place >= 0.80 and rompue < 0.20 else 'ECHEC'}")
valide = (c1 >= 0.95) and c2 and c3
print(f"   INSTRUMENT : {'VALIDE' if valide else 'REFUSE - la lecture est nulle'}")

print("\nattente  episodes  MISSION REUSSIE  3 charges  >=6 exfiltres  vivants  alarme  compromis  duree  attente jouee  derive")
for n in niveaux:
    L = [e for e in P if e["attente"] == n]
    print(f"{n:5d} s  {len(L):5d}      {np.mean([e['reussi'] for e in L]):.3f}           {np.mean([e['trois_charges'] for e in L]):.3f}      "
          f"{np.mean([e['exfil'] for e in L]):.3f}       {np.mean([e['vivants'] for e in L]):.2f}    {np.mean([e['alarme'] for e in L]):.2f}     "
          f"{np.mean([e['compromis'] for e in L]):.2f}     {np.mean([e['duree'] for e in L]):.0f}   {np.mean([e['attente_jouee'] for e in L]):.0f}          "
          f"{np.mean([e['derive'] for e in L]):.0f} m")


def ecart(n1, n0, cle="reussi"):
    par = {}
    for w in mondes:
        a = [e[cle] for e in P if e["attente"] == n1 and e["monde"] == w]
        b = [e[cle] for e in P if e["attente"] == n0 and e["monde"] == w]
        if a and b: par[w] = np.mean(a) - np.mean(b)
    if not par: return None
    rng = np.random.default_rng(GRAINE); ws = list(par)
    boot = [np.mean([par[w] for w in rng.choice(ws, len(ws))]) for _ in range(B)]
    return float(np.mean(list(par.values()))), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)), len(ws)


print("\n== ECARTS APPARIES PAR MONDE ( mission reussie )")
for n in niveaux[1:]:
    r = ecart(n, niveaux[0])
    if r: print(f"   {n} s - 0 s : {r[0]:+.3f}  IC95 [{r[1]:+.3f} ; {r[2]:+.3f}]  sur {r[3]} mondes")
print("\n== CRITERE ECRIT AVANT")
r = ecart(niveaux[-1], niveaux[0])
if r:
    prix = (r[0] < -SEUIL) and (r[2] < 0)
    gratuit = (r[1] > -SEUIL) and (r[2] < SEUIL)
    print(f"   ecart {niveaux[-1]} s - 0 s = {r[0]:+.3f} IC [{r[1]:+.3f} ; {r[2]:+.3f}]")
    print(f"   LE TEMPS A UN PRIX : {'OUI' if prix else 'NON'} ( baisse > 10 points et IC excluant 0 )")
    print(f"   LE TEMPS EST GRATUIT : {'OUI' if gratuit else 'NON'} ( IC contenu dans +-10 points )")
    if not prix and not gratuit: print("   INDECIS : doubler les repetitions")
if not valide: print("\n   !! INSTRUMENT REFUSE : rien de ce qui precede ne vaut comme resultat.")
