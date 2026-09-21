"""LE LECTEUR DE MOTIFS. L Oracle sort des situations piegees ; ce module dit POURQUOI elles le sont, sous trois
angles independants, puis confronte chaque motif aux episodes reellement joues.
  1. ce que l imagination a appris : l effet d ATTENDRE plutot que traverser, arme par arme ( les interactions
     arme x option ), et sa stabilite sur les 10 modeles ;
  2. ce qui revient dans les pieges imagines : quelles valeurs d armes y sont sur-representees ;
  3. une regle courte : un arbre de profondeur 3 qui resume le regret imagine.
  4. l epreuve : pour chaque motif, l ecart traverser / attendre MESURE dans les episodes joues, avec son IC.
Un motif n est qu une hypothese tant que 4 ne l a pas vu.   python -m oracle.autonome.motifs"""
import numpy as np
from collections import Counter
from sklearn.tree import DecisionTreeRegressor, export_text
from . import config as C, donnees as Dn, monde as M, generateur as Gen, architecte as A


def lire():
    E = Dn.utilisables(Dn.episodes(lambda c: True))
    m = M.Monde().apprendre(E)
    base = m.taux; pente = base * (1 - base)                    # un coefficient logit -> points de probabilite, au taux de base
    n = len(M.COLS)
    print(f"== MOTIFS DE L ORACLE : imagination apprise sur {len(E)} episodes, compromission {base:.3f}\n")

    # ---- 1. l effet d attendre, arme par arme ----
    coefs = np.array([r.coef_[0] for r in m.reseaux])           # 10 x ( 2n )
    inter = coefs[:, n:]                                         # interactions : colonne x attendre
    lignes = []
    for j, (k, v) in enumerate(M.COLS):
        if k == "attendre": continue
        moy, acc = inter[:, j].mean(), int(np.sum(np.sign(inter[:, j]) == np.sign(inter[:, j].mean())))
        lignes.append((abs(moy), k, v, moy * pente, acc))
    print("1. CE QUE L IMAGINATION A APPRIS - effet d ATTENDRE plutot que traverser, quand cette arme vaut cette valeur")
    print("   ( en points de compromission ; + = attendre est PIRE, - = attendre SAUVE ; accord = modeles d accord sur le signe )")
    for _, k, v, eff, acc in sorted(lignes, reverse=True)[:12]:
        print(f"   {k:<13} = {str(v):<6}  {eff * 100:+6.1f} points   accord {acc}/10")

    # ---- 2. ce qui revient dans les pieges imagines ----
    rng = np.random.default_rng(C.GRAINE)
    cands = []
    joues = [dict(zip(C.ARMES, c)) for c in set(m.configs)]
    for i in range(8000):
        if i % 2 == 0:
            s = dict(joues[rng.integers(len(joues))])
            for kk in rng.choice(list(C.ARMES), int(rng.integers(1, 5)), replace=False): s[kk] = int(rng.choice(C.ARMES[kk]))
            s = {kk: (vv if vv in C.ARMES[kk] else int(rng.choice(C.ARMES[kk]))) for kk, vv in s.items()}
        else:
            s = {kk: int(rng.choice(vv)) for kk, vv in C.ARMES.items()}
        cands.append((s, tuple(int(x) for x in rng.choice(C.GRAINES, 2, replace=False))))
    p_choix = Gen.modele_du_choix(A.charger(), E)
    r, sd, p2, regret = Gen.evaluer(m, p_choix, cands)
    piege = (r.min(1) <= C.SEUIL_JOUABLE_IMAGINE) & (regret >= C.REGRET_MIN_PIEGE)
    print(f"\n2. CE QUI REVIENT DANS LES PIEGES IMAGINES - {piege.sum()} pieges sur {len(cands)} situations imaginees")
    if piege.sum():
        tous = Counter((k, s[k]) for s, _ in cands for k in C.ARMES)
        dans = Counter((k, cands[i][0][k]) for i in np.where(piege)[0] for k in C.ARMES)
        lift = sorted(((dans[kv] / piege.sum()) / (tous[kv] / len(cands)), kv, dans[kv] / piege.sum()) for kv in tous if dans[kv] >= 10)
        for l, (k, v), f in sorted(lift, reverse=True)[:10]:
            print(f"   {k:<13} = {str(v):<6}  present dans {f:5.0%} des pieges, {l:4.1f} fois plus que par hasard")

    # ---- 3. une regle courte ----
    X = np.array([[s[k] for k in C.ARMES] for s, _ in cands], dtype=float)
    arbre = DecisionTreeRegressor(max_depth=3, min_samples_leaf=200, random_state=C.GRAINE).fit(X, regret)
    print(f"\n3. LA REGLE COURTE - arbre de profondeur 3 sur le regret imagine ( il en explique {arbre.score(X, regret):.0%} )")
    print("   " + export_text(arbre, feature_names=list(C.ARMES), decimals=3).replace("\n", "\n   "))

    # ---- 4. l epreuve des episodes joues ----
    print("4. L EPREUVE - l ecart ( compromission sous traverser ) - ( sous attendre ), MESURE dans les episodes joues")
    print("   ( un motif de piege predit un ecart POSITIF : traverser pire qu attendre )")
    for _, k, v, eff, acc in sorted(lignes, reverse=True)[:8]:
        if k == "graine": Ek = [e for e in E if e["graine"] == v]
        else: Ek = [e for e in E if e[k] == v]
        t = [e["compromis"] for e in Ek if e["option"] == 1]; a = [e["compromis"] for e in Ek if e["option"] == 2]
        if len(t) < 5 or len(a) < 5: print(f"   {k:<13} = {str(v):<6}  trop peu d episodes ( {len(t)} traverser, {len(a)} attendre )"); continue
        d = np.mean(t) - np.mean(a); se = np.sqrt(np.var(t) / len(t) + np.var(a) / len(a))
        signe = "confirme le sens" if (d > 0) == (eff < 0) and abs(d) > 1.96 * se else ("meme sens, pas significatif" if (d > 0) == (eff < 0) else "SENS CONTRAIRE")
        print(f"   {k:<13} = {str(v):<6}  mesure {d * 100:+6.1f} points  IC [{(d - 1.96 * se) * 100:+.1f} ; {(d + 1.96 * se) * 100:+.1f}]  "
              f"( n {len(t)} / {len(a)} )  {signe}")


if __name__ == "__main__":
    lire()


# ------------------------------------------------------------------ dans la boucle : l epreuve PROSPECTIVE
def motifs_du_modele(m, top=12, accord_min=9):
    """Les motifs appris : effet d attendre plutot que traverser, par valeur d arme, stable sur au moins 9 modeles sur 10."""
    n = len(M.COLS); pente = m.taux * (1 - m.taux)
    inter = np.array([r.coef_[0] for r in m.reseaux])[:, n:]
    out = []
    for j, (k, v) in enumerate(M.COLS):
        if k == "attendre": continue
        moy = inter[:, j].mean(); acc = int(np.sum(np.sign(inter[:, j]) == np.sign(moy)))
        if acc >= accord_min: out.append(dict(arme=k, valeur=v, effet_attendre=float(moy * pente), accord=acc))
    return sorted(out, key=lambda x: -abs(x["effet_attendre"]))[:top]


def compter(motif, E):
    """Sur des episodes que le modele n a PAS vus : compromissions sous traverser et sous attendre, la ou le motif s applique."""
    k, v = motif["arme"], motif["valeur"]
    Ek = [e for e in E if (e["graine"] if k == "graine" else e.get(k)) == v]
    t = [e["compromis"] for e in Ek if e["option"] == 1]; a = [e["compromis"] for e in Ek if e["option"] == 2]
    return dict(n_t=len(t), c_t=int(sum(t)), n_a=len(a), c_a=int(sum(a)))


def cumuler(journal_motifs):
    """Chaque motif ( arme, valeur, sens ) cumule ses comptes prospectifs d une iteration a l autre."""
    cum = {}
    for it in journal_motifs:
        for mo in it["motifs"]:
            cle = (mo["arme"], mo["valeur"], "attendre_sauve" if mo["effet_attendre"] < 0 else "attendre_coute")
            c = cum.setdefault(cle, dict(n_t=0, c_t=0, n_a=0, c_a=0, vu=0))
            for x in ("n_t", "c_t", "n_a", "c_a"): c[x] += mo["compte"][x]
            c["vu"] += 1
    return cum


def epreuve(cle, c, alpha=0.05, n_min=20):
    """Test exact de Fisher unilateral, dans le SENS PREDIT par le motif. Pas de verdict sous 20 episodes par option."""
    from scipy.stats import fisher_exact
    if min(c["n_t"], c["n_a"]) < n_min: return "en attente", None
    tab = [[c["c_t"], c["n_t"] - c["c_t"]], [c["c_a"], c["n_a"] - c["c_a"]]]
    alt = "greater" if cle[2] == "attendre_sauve" else "less"        # attendre sauve -> traverser compromet PLUS
    _, p = fisher_exact(tab, alternative=alt)
    return ("CONFIRME" if p < alpha else "non confirme"), float(p)
