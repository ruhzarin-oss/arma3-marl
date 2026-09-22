"""ETAPE 0 DE FABLE - diagnostics gratuits, sur les episodes deja joues, avant tout nouvel episode.
Seuils ecrits d avance dans oracle/autonome/AVIS_FABLE_22_09.md ( commit 239a0d5 ). Processeur seulement.
  0a plafond en verite   0b signes par monde   0c force des paires   0d equilibre des perceptions ( fuite )
  0e cecite de la porte actuelle ( effet realiste injecte )
  python -m oracle.autonome.etape0_fable"""
import copy, os, random, re, time
import numpy as np
from . import config as C, donnees as Dn, architecte as A, architecte_apprend as AA

T0 = time.time()
TOUS = Dn.utilisables(Dn.episodes(lambda c: True))
J = AA.jeu(copy.deepcopy(TOUS))                                  # population de l Architecte, propensions par campagne
EST_ORACLE = lambda e: str(e["campagne"]).startswith(C.PREFIXES_HISTORIQUES)


def poste_percu(e):
    """C2 de Fable : menace vue au moins une fois ET aucun moteur - None si la perception etendue manque."""
    if e.get("p_moteur_entendu") is None: return None
    m = e.get("p_moteur_depuis_fenetre"); m = e.get("p_moteur_entendu") if m is None else m
    return (e.get("p_n_vues_menace") or 0) >= 1 and (m or 0) == 0


def ic_monde(d, mondes, B=4000):
    r = random.Random(C.GRAINE); M = sorted(set(mondes)); par = {w: d[mondes == w] for w in M}; t = []
    for _ in range(B): t.append(np.concatenate([par[r.choice(M)] for _ in M]).mean())
    t.sort(); return float(d.mean()), t[int(0.025 * B)], t[int(0.975 * B)]


print(f"== ETAPE 0 DE FABLE : {len(TOUS)} episodes utilisables ; population de l Architecte {len(J)} ; "
      f"dont episodes de l Oracle {sum(map(EST_ORACLE, J))}\n")

# ---------------- 0a ----------------
print("0a. LE PLAFOND - si l Architecte connaissait la VERITE ( poste proche ), vaudrait-il mieux que « toujours attendre » ?")
regles = {"toujours traverser": lambda e: 1, "toujours attendre": lambda e: 2,
          "PLAFOND : attendre ssi poste proche ( verite )": lambda e: 2 if e["menace_p2"] == 5 else 1,
          "C2 : attendre ssi menace vue et aucun moteur": lambda e: 2 if poste_percu(e) else 1}
for titre, pop in (("toute la population", J), ("episodes de l Oracle seulement", [e for e in J if EST_ORACLE(e)])):
    mondes = np.array([e["graine"] for e in pop]); v1 = AA.valeurs(pop, [2] * len(pop))
    print(f"   {titre} ( {len(pop)} episodes, compromission brute {np.mean([e['compromis'] for e in pop]):.3f} )")
    for nom, f in regles.items():
        v = AA.valeurs(pop, [f(e) for e in pop]); e_, lo, hi = ic_monde(v - v1, mondes)
        print(f"      {nom:<48} valeur {v.mean():.3f}   ecart a « toujours attendre » {e_:+.3f} [{lo:+.3f} ; {hi:+.3f}]")
vp = AA.valeurs(J, [2 if e["menace_p2"] == 5 else 1 for e in J]).mean(); va = AA.valeurs(J, [2] * len(J)).mean()
print(f"   -> seuil ecrit d avance : poursuivre la perception seulement si V(plafond) - V(toujours attendre) <= -0,02 : "
      f"{vp - va:+.3f} -> {'la perception PEUT servir' if vp - va <= -0.02 else 'la perception n est PAS le goulot : cible = toujours attendre'}\n")

# ---------------- 0b ----------------
print("0b. MONDE PAR MONDE - effet d attendre ( attendre - traverser, Hajek ) dans et hors « poste percu »")
def tau(pop):
    w = np.array([1 / e["pi"] for e in pop]); y = np.array([e["compromis"] for e in pop]); a = np.array([e["option_imposee"] for e in pop])
    if min((a == 1).sum(), (a == 2).sum()) < 3: return None
    return float((w * y)[a == 2].sum() / w[a == 2].sum() - (w * y)[a == 1].sum() / w[a == 1].sum())
Je = [e for e in J if poste_percu(e) is not None]
mondes = sorted({e["graine"] for e in Je}); dans, hors = [], []
for w in mondes:
    dans.append(tau([e for e in Je if e["graine"] == w and poste_percu(e)])); hors.append(tau([e for e in Je if e["graine"] == w and not poste_percu(e)]))
nd = [x for x in dans if x is not None]; nh = [x for x in hors if x is not None]
print(f"   {len(Je)} episodes avec perception etendue, {sum(map(poste_percu, Je))} en « poste percu » ( {np.mean([poste_percu(e) for e in Je]):.0%} )")
print(f"   face au poste percu : attendre sauve dans {sum(x < 0 for x in nd)} mondes sur {len(nd)} evaluables ( ecart moyen {np.mean(nd):+.3f} )")
print(f"   hors poste percu    : TRAVERSER gagne dans {sum(x > 0 for x in nh)} mondes sur {len(nh)} evaluables ( ecart moyen {np.mean(nh):+.3f} )")
print(f"   -> seuil ecrit d avance : poursuivre C2 si traverser gagne hors poste dans >= 13 mondes sur 20 : "
      f"{'OUI, C2 reste en lice' if sum(x > 0 for x in nh) >= 13 else 'NON, la cible est « toujours attendre » ( C1 )'}\n")

# ---------------- 0c ----------------
print("0c. LA FORCE DES PAIRES - meme situation de l Oracle, jouee sous les deux options")
paires = {}
for e in TOUS:
    if not EST_ORACLE(e): continue
    m = re.match(r"(DIA|ORA)-(\d+)-c(\d+)-o(\d)-r(\d)", str(e["version"]))
    if m: paires.setdefault((m.group(2), m.group(3), m.group(5), e["graine"]), {})[int(m.group(4))] = e["compromis"]
p = np.array([[v[1], v[2]] for v in paires.values() if 1 in v and 2 in v], dtype=float)
rho = float(np.corrcoef(p[:, 0], p[:, 1])[0, 1]); d = p[:, 1] - p[:, 0]
ratio = float(np.sqrt(d.var() / (p[:, 0].var() + p[:, 1].var())))
print(f"   {len(p)} paires ; correlation intra-paire rho = {rho:.3f} ; erreur appariee / non appariee = {ratio:.3f}")
print(f"   -> seuil ecrit d avance : adopter le test apparie si le rapport < 0,85 : {'OUI' if ratio < 0.85 else 'le gain est faible, mais le test apparie reste exact et gratuit'}")
print(f"   ( ecart moyen attendre - traverser sur les paires : {d.mean():+.3f} )\n")

# ---------------- 0d ----------------
print("0d. LA FUITE - les perceptions a la decision sont-elles EQUILIBREES entre les options ? ( options tirees au sort :")
print("    tout desequilibre voudrait dire que la perception est mesuree APRES le choix )")
Jd = [e for e in J if e.get("p_moteur_entendu") is not None]
alertes = []
for k in ["n_vues_menace", "menaces_vues", "moteur_entendu", "moteur_depuis_fenetre", "menace_percue", "distance_moteur",
          "vehicule_vu", "menaces_connues", "distance_menace", "alarme", "depuis_alarme", "vue_depuis"]:
    x1 = np.array([e.get("p_" + k) or 0 for e in Jd if e["option_imposee"] == 1], dtype=float)
    x2 = np.array([e.get("p_" + k) or 0 for e in Jd if e["option_imposee"] == 2], dtype=float)
    sd = np.sqrt((x1.var() + x2.var()) / 2) or 1.0; smd = (x2.mean() - x1.mean()) / sd
    z = (x2.mean() - x1.mean()) / np.sqrt(x1.var() / len(x1) + x2.var() / len(x2) + 1e-12)
    flag = abs(smd) > 0.1 and abs(z) > 3
    if flag: alertes.append(k)
    print(f"   {k:<22} traverser {x1.mean():8.2f}   attendre {x2.mean():8.2f}   ecart standardise {smd:+.3f}  z {z:+.1f}  {'<<< DESEQUILIBRE' if flag else ''}")
print(f"   -> BLOQUANT si une perception est desequilibree : {alertes if alertes else 'aucune - pas de fuite visible dans les donnees'}\n")

# ---------------- 0e ----------------
print("0e. LA CECITE DE LA PORTE ACTUELLE - effet realiste injecte ( attendre retire 8 points de compromission face au")
print("    poste percu ), dans les VRAIES donnees, 20 fois ; combien de fois la porte actuelle l adopte-t-elle ?")
rng = np.random.default_rng(C.GRAINE)
cellule = [e for e in J if poste_percu(e) and e["option_imposee"] == 2]
p_cell = np.mean([e["compromis"] for e in cellule]) if cellule else 0.0
adopt, qui = 0, []
for i in range(20):
    E = copy.deepcopy(TOUS)
    for e in E:
        if e.get("atteint_decision") and (e.get("p_compromis") or 0) == 0 and poste_percu(e) and e["option_imposee"] == 2 and e["compromis"] == 1:
            if rng.random() < 0.08 / max(p_cell, 0.08): e["compromis"] = 0
    r = AA.apprendre(E, {"type": "constante", "option": 1}, candidats=("logistique",))
    adopt += int(r["adoptee"]); qui.append(r["meilleur"] if r["adoptee"] else "-")
    print(f"   injection {i + 1:>2} : {'ADOPTE ' + r['meilleur'] if r['adoptee'] else 'rien'}  ( meilleur {r['meilleur']}, IC {[round(x, 3) for x in r['candidats'][r['meilleur']]['ic']]} )", flush=True)
print(f"   -> la porte actuelle voit un effet realiste dans {adopt} cas sur 20 ; Fable predit moins de 30 % ( <= 6 )")
print(f"\nduree {(time.time() - T0) / 60:.0f} min")
