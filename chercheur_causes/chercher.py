"""
Chercheur de causes CHACAL v0.

Criteres : CRITERES_CHERCHEUR_CAUSES_V0.md ( commit 6bedbad, ecrit avant cette recherche ).

1. qu est-ce qui cause quoi   : leviers forces, compares a monde et autres leviers egaux, permutations dans les strates
2. pourquoi                   : variables intermediaires qui portent l effet ( regression intra-strate ), puis le pourquoi du pourquoi
3. ou chercher ensuite        : correlations au succes qu aucun levier ne controle ( hypotheses, pas des causes )
"""
import collections, hashlib, json, math, os, warnings
warnings.filterwarnings("ignore")
import numpy as np, pyarrow as pa, pyarrow.parquet as pq

D = "/mnt/data/hmt/chercheur_causes/donnees"
SORTIE = "/mnt/data/hmt/chercheur_causes/resultats"
EXCLUES = {"SANS_CAMPAGNE", "SITUATION-PAR-PHASE-16-09", "FUMEE-SITUATION-16-09"}
EFFETS = ["fini|charges", "fini|detruits_scriptes", "fini|exfiltres", "fini|vivants", "fini|pertes_est", "fini_issue=SUCCES", "fini|duree"]
P, Q, MIN_N, N_BOOT, TAUTO = 1000, 0.05, 5, 300, 0.95
rng = np.random.default_rng(20260916)
np.seterr(all="ignore")
os.makedirs(SORTIE, exist_ok=True)

# ------------------------------------------------------------------ episodes et leviers
ep = [e for e in pq.read_table(f"{D}/episodes.parquet").to_pylist()
      if e["verdict"] == "ACCEPTE" and e["erreurs_sqf"] == 0 and e["campagne"] not in EXCLUES]
for e in ep:
    e["job|porte_B"] = 1.0 if (e["campagne"].startswith("PORTE-") and "-B-" in e["version"]) else 0.0
    e.pop("job|azimut_val", None)
V = pq.read_table(f"{D}/variables.parquet").to_pydict()
avec_fini = {eid for eid, var in zip(V["episode_id"], V["variable"]) if var == "fini|duree"}
sans_fini = [e["episode_id"] for e in ep if e["episode_id"] not in avec_fini]
ep = [e for e in ep if e["episode_id"] in avec_fini]
cles_job = sorted({k for e in ep for k in e if k.startswith("job|")})
LEVIERS = [k for k in cles_job if len({e.get(k) for e in ep if e.get(k) is not None}) >= 2]
n = len(ep); ligne = {e["episode_id"]: i for i, e in enumerate(ep)}
print(f"episodes retenus {n}  ( exclus sans ligne FINI : {len(sans_fini)} )  leviers qui varient : {len(LEVIERS)}")

# ------------------------------------------------------------------ matrice des variables
noms_tous = sorted(set(V["variable"]))
col = {v: j for j, v in enumerate(noms_tous)}
X = np.full((n, len(noms_tous)), np.nan)
for eid, var, val in zip(V["episode_id"], V["variable"], V["valeur"]):
    i = ligne.get(eid)
    if i is not None: X[i, col[var]] = val
compte = np.array([nm.startswith("n|") or "=" in nm or nm.endswith("|joue") for nm in noms_tous])
X[:, compte] = np.nan_to_num(X[:, compte], nan=0.0)
presents = (~np.isnan(X) & (X != 0)).sum(0) >= MIN_N
NOMS = [nm for nm, k in zip(noms_tous, presents) if k]; X = X[:, presents]
J = {nm: j for j, nm in enumerate(NOMS)}
assert all(e_ in J for e_ in EFFETS), [e_ for e_ in EFFETS if e_ not in J]
MEDIATEURS = [j for j, nm in enumerate(NOMS) if not nm.startswith("fini")]
print(f"variables retenues {len(NOMS)}  ( dont intermediaires {len(MEDIATEURS)} )")

def bh(p):
    p = np.asarray(p, float); m = len(p)
    if m == 0: return p
    o = np.argsort(p); q = p[o] * m / np.arange(1, m + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]; out = np.empty(m); out[o] = np.minimum(q, 1); return out

def demean(v, sid):
    ns = sid.max() + 1; cnt = np.bincount(sid, minlength=ns)
    if v.ndim == 1: return v - (np.bincount(sid, v, ns) / cnt)[sid]
    return v - np.stack([np.bincount(sid, v[:, k], ns) / cnt for k in range(v.shape[1])], 1)[sid]

# ------------------------------------------------------------------ 1. comparaisons
def comparaisons(lev, avec_campagne, cle_leviers, ep_leviers=None):
    groupes = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, e in enumerate(ep):
        x = (ep_leviers[i] if ep_leviers is not None else e.get(lev))
        if x is None: continue
        cle = ((e["campagne"],) if avec_campagne else ()) + (e["site"],) + tuple(e.get(k) for k in cle_leviers if k != lev)
        groupes[cle][x].append(i)
    paires = collections.defaultdict(list)
    for cle, par_val in groupes.items():
        vals = sorted(par_val)
        for ia in range(len(vals)):
            for ib in range(ia + 1, len(vals)):
                paires[(vals[ia], vals[ib])].append((par_val[vals[ia]], par_val[vals[ib]]))
    return {k: s for k, s in paires.items() if sum(len(a) for a, _ in s) >= MIN_N and sum(len(b) for _, b in s) >= MIN_N}

def tester(strates):
    rows, lab, ca, cb, sid = [], [], [], [], []
    W = 0.0
    for s, (ia, ib) in enumerate(strates):
        na, nb = len(ia), len(ib); w = na * nb / (na + nb); W += w
        for grp, l in ((ia, 0), (ib, 1)):
            for i in grp: rows.append(i); lab.append(l); ca.append(w / na); cb.append(w / nb); sid.append(s)
    rows, lab, ca, cb, sid = map(np.array, (rows, lab, ca, cb, sid))
    lab = lab.astype(float)
    Y = X[rows]
    usable = ~np.isnan(Y).any(0) & (np.nanstd(Y, 0) > 0)
    Yu = Y[:, usable]
    if Yu.shape[1] == 0:
        return {}, dict(rows=rows, lab=lab, sid=sid, na=int((lab == 0).sum()), nb=int((lab == 1).sum()), strates=len(strates))
    T = (lab * (ca + cb) - ca) @ Yu / W
    ma = ((1 - lab) * ca) @ Yu / W; mb = (lab * cb) @ Yu / W
    Lp = np.empty((P, len(rows)))
    for s in range(len(strates)):
        m = sid == s
        Lp[:, m] = rng.permuted(np.tile(lab[m], (P, 1)), axis=1)
    Tp = (Lp * (ca + cb) - ca) @ Yu / W
    mu, sd = Tp.mean(0), Tp.std(0)
    z = np.where(sd > 0, (T - mu) / np.where(sd > 0, sd, 1), 0.0)
    p = np.array([math.erfc(abs(x) / math.sqrt(2)) for x in z])
    sdw = demean(Yu, sid).std(0)
    res = {}
    for k, j in enumerate(np.where(usable)[0]):
        res[j] = dict(ecart=float(T[k]), moy_a=float(ma[k]), moy_b=float(mb[k]), z=float(z[k]), p=float(p[k]),
                      ecart_std=float(T[k] / sdw[k]) if sdw[k] > 0 else 0.0)
    return res, dict(rows=rows, lab=lab, sid=sid, na=int((lab == 0).sum()), nb=int((lab == 1).sum()), strates=len(strates))

def lancer(lecture, leviers, avec_campagne, cle_leviers, ep_leviers=None):
    sortie = []
    for lev in leviers:
        for (a, b), strates in sorted(comparaisons(lev, avec_campagne, cle_leviers, ep_leviers.get(lev) if ep_leviers else None).items()):
            res, meta = tester(strates)
            sortie.append(dict(lecture=lecture, levier=lev, a=a, b=b, res=res, meta=meta))
    return sortie

print("\n== 1. recherche des causes")
comps = lancer("entrelacee", LEVIERS, True, LEVIERS) + lancer("non_entrelacee", LEVIERS, False, LEVIERS)
print(f"   comparaisons : {len(comps)}")
# famille E : tous les leviers, les deux lectures, ensemble
fam_e = [(ci, J[e_]) for ci, c in enumerate(comps) for e_ in EFFETS if J[e_] in c["res"]]
qe = bh([comps[ci]["res"][j]["p"] for ci, j in fam_e])
for (ci, j), q in zip(fam_e, qe):
    comps[ci]["res"][j]["q"] = float(q); comps[ci]["res"][j]["famille"] = "E"; comps[ci]["res"][j]["decouverte"] = bool(q <= Q)
# famille M : par comparaison
for c in comps:
    js = [j for j in MEDIATEURS if j in c["res"]]
    for j, q in zip(js, bh([c["res"][j]["p"] for j in js])):
        c["res"][j]["q"] = float(q); c["res"][j]["famille"] = "M"; c["res"][j]["decouverte"] = bool(q <= Q)

# ------------------------------------------------------------------ 2. pourquoi
def raisons(c, jy, exclure=(), top=5):
    rows, lab, sid = c["meta"]["rows"], c["meta"]["lab"], c["meta"]["sid"]
    ns = sid.max() + 1
    Ld = demean(lab, sid); Yd = demean(X[rows, jy], sid)
    if Ld @ Ld == 0: return []
    beta = (Ld @ Yd) / (Ld @ Ld)
    if abs(beta) < 1e-9: return []
    cands = []
    for j, r in c["res"].items():
        if r.get("famille") != "M" or not r["decouverte"] or j == jy or j in exclure: continue
        Md = demean(X[rows, j], sid)
        if Md.std() == 0: continue
        r_my = float(np.corrcoef(Md, Yd)[0, 1]); r_ml = float(np.corrcoef(Md, Ld)[0, 1])
        if abs(r_my) >= TAUTO: continue
        A = np.column_stack([Ld, Md]); ata = A.T @ A
        if abs(np.linalg.det(ata)) < 1e-9: continue
        coef = np.linalg.solve(ata, A.T @ Yd); resid = Yd - A @ coef
        dof = max(len(rows) - ns - 2, 1); s2 = resid @ resid / dof
        t = coef[1] / math.sqrt(s2 * np.linalg.inv(ata)[1, 1]) if s2 > 0 else 0.0
        if abs(t) < 2: continue
        cands.append(dict(variable=NOMS[j], j=j, proportion=float(1 - coef[0] / beta), t_raison=float(t),
                          sens_levier=float(np.sign(r_ml)), corr_levier=r_ml, corr_effet=r_my))
    cands.sort(key=lambda d: -d["proportion"])
    cands = [d for d in cands if d["proportion"] > 0][:top]
    for d in cands:
        props = []
        for _ in range(N_BOOT):
            pick = np.concatenate([rng.choice(np.where(sid == s)[0], (sid == s).sum()) for s in range(ns)])
            s_ = sid[pick]; Lb = demean(lab[pick], s_); Yb = demean(X[rows[pick], jy], s_); Mb = demean(X[rows[pick], d["j"]], s_)
            if Lb @ Lb == 0: continue
            bt = (Lb @ Yb) / (Lb @ Lb); A = np.column_stack([Lb, Mb]); ata = A.T @ A
            if abs(bt) < 1e-9 or abs(np.linalg.det(ata)) < 1e-9: continue
            props.append(1 - np.linalg.solve(ata, A.T @ Yb)[0] / bt)
        d["ic"] = [float(np.percentile(props, 2.5)), float(np.percentile(props, 97.5))] if len(props) > 50 else None
        d.pop("j")
    return cands

print("== 2. recherche des raisons")
decouvertes = []
for ci, c in enumerate(comps):
    for e_ in EFFETS:
        r = c["res"].get(J[e_])
        if not r or not r["decouverte"]: continue
        rs = raisons(c, J[e_])
        chaine = raisons(c, J[rs[0]["variable"]], exclure={J[e_]}, top=3) if rs else []
        decouvertes.append(dict(lecture=c["lecture"], levier=c["levier"], a=c["a"], b=c["b"], effet=e_, na=c["meta"]["na"], nb=c["meta"]["nb"],
                                strates=c["meta"]["strates"], **{k: r[k] for k in ("ecart", "moy_a", "moy_b", "ecart_std", "z", "p", "q")},
                                raisons=rs, pourquoi_du_pourquoi=chaine))
print(f"   decouvertes famille E : {len(decouvertes)}")

# ------------------------------------------------------------------ 3. pistes : correlations sans levier
print("== 3. pistes")
sid_all = {}
for i, e in enumerate(ep):
    sid_all.setdefault((e["campagne"], e["site"]) + tuple(e.get(k) for k in LEVIERS), len(sid_all))
SID = np.array([sid_all[(e["campagne"], e["site"]) + tuple(e.get(k) for k in LEVIERS)] for e in ep])
pistes = {}
for e_ in ("fini_issue=SUCCES", "fini|charges"):
    y = X[:, J[e_]]; lignes_p = []
    for j in MEDIATEURS:
        m = ~np.isnan(X[:, j])
        if m.sum() < 30: continue
        s_ = SID[m]; _, s_ = np.unique(s_, return_inverse=True)
        xd, yd = demean(X[m, j], s_), demean(y[m], s_)
        if xd.std() == 0 or yd.std() == 0: continue
        r = float(np.corrcoef(xd, yd)[0, 1])
        if abs(r) >= TAUTO: continue
        dof = int(m.sum() - (s_.max() + 1) - 1)
        if dof < 20: continue
        zz = math.atanh(max(min(r, 0.999999), -0.999999)) * math.sqrt(dof - 2)
        lignes_p.append(dict(variable=NOMS[j], r=r, p=math.erfc(abs(zz) / math.sqrt(2)), n=int(m.sum()), dof=dof))
    for d, q in zip(lignes_p, bh([d["p"] for d in lignes_p])): d["q"] = float(q)
    lignes_p = sorted([d for d in lignes_p if d["q"] <= Q], key=lambda d: -abs(d["r"]))
    for d in lignes_p:
        d["leviers_qui_la_bougent"] = sorted({f"{c['levier']} {c['a']:g}->{c['b']:g} ({c['lecture']})" for c in comps
                                              if J[d["variable"]] in c["res"] and c["res"][J[d["variable"]]].get("decouverte")})
    pistes[e_] = lignes_p
    print(f"   {e_} : {len(lignes_p)} correlations intra-strate retenues")

# ------------------------------------------------------------------ placebos
print("== placebos")
placebo_lev = {}
for k in range(5):
    placebo_lev[f"placebo_{k}"] = [float(hashlib.md5(f"{e['episode_id']}|placebo{k}".encode()).digest()[0] % 2) for e in ep]
pl = []
for nom, vals in placebo_lev.items():
    pl += lancer("entrelacee", [nom], True, LEVIERS, ep_leviers={nom: vals})
fam = [(ci, J[e_]) for ci, c in enumerate(pl) for e_ in EFFETS if J[e_] in c["res"]]
for (ci, j), q in zip(fam, bh([pl[ci]["res"][j]["p"] for ci, j in fam])): pl[ci]["res"][j]["decouverte"] = bool(q <= Q)
placebos = []
for c in pl:
    js = [j for j in MEDIATEURS if j in c["res"]]
    nm = int((bh([c["res"][j]["p"] for j in js]) <= Q).sum()) if js else 0
    ne = sum(1 for e_ in EFFETS if c["res"].get(J[e_], {}).get("decouverte"))
    placebos.append(dict(placebo=c["levier"], na=c["meta"]["na"], nb=c["meta"]["nb"], decouvertes_E=ne, decouvertes_M=nm))
    print(f"   {c['levier']} : n {c['meta']['na']}/{c['meta']['nb']}  decouvertes E {ne}  M {nm}")

# ------------------------------------------------------------------ controles
def trouve(lecture, lev, cond_paire, effet, signe):
    cs = [c for c in comps if c["lecture"] == lecture and c["levier"] == lev and cond_paire(c["a"], c["b"])]
    if not cs: return None, []
    ok = [c for c in cs if c["res"].get(J[effet], {}).get("decouverte") and np.sign(c["res"][J[effet]]["ecart"]) == signe]
    return bool(ok), ok

def rangs(c, effet, top, test_nom):
    for d in decouvertes:
        if d["lecture"] == c["lecture"] and d["levier"] == c["levier"] and d["a"] == c["a"] and d["b"] == c["b"] and d["effet"] == effet:
            return any(test_nom(r["variable"]) for r in d["raisons"][:top]), [r["variable"] for r in d["raisons"][:top]]
    return False, []

controles = {}
r, cs = trouve("entrelacee", "job|socle", lambda a, b: (a, b) == (0, 1), "fini|charges", 1)
controles["C+1"] = dict(testable=r is not None, passe=bool(r))
r, cs = trouve("entrelacee", "job|tactique", lambda a, b: a == 0 and b > 0, "fini|charges", -1)
controles["C+2"] = dict(testable=r is not None, passe=bool(r), comparaisons=[f"{c['a']:g}->{c['b']:g}" for c in cs])
r, cs = trouve("entrelacee", "job|arret", lambda a, b: (a, b) == (5, 6), "fini_issue=SUCCES", 1)
ok3, noms3 = (rangs(cs[0], "fini_issue=SUCCES", 5, lambda v: v.startswith("ph|6|")) if cs else (False, []))
controles["C+3"] = dict(testable=r is not None, passe=bool(r) and ok3, cause_trouvee=bool(r), raisons=noms3)
r, cs = trouve("non_entrelacee", "job|delai_porteur", lambda a, b: (a, b) == (45, 180), "fini|charges", 1)
ok4, noms4 = (rangs(cs[0], "fini|charges", 3, lambda v: "porteur" in v.lower()) if cs else (False, []))
controles["C+4"] = dict(testable=r is not None, passe=bool(r) and ok4, cause_trouvee=bool(r), raisons=noms4)
cp = [c for c in comps if c["levier"] == "job|porte_B"]
fausses = [f"{c['lecture']} {e_}" for c in cp for e_ in ("fini|charges", "fini|detruits_scriptes", "fini_issue=SUCCES") if c["res"].get(J[e_], {}).get("decouverte")]
controles["C-1"] = dict(testable=bool(cp), passe=bool(cp) and not fausses, lectures=[c["lecture"] for c in cp], fausses_decouvertes=fausses)
nb_pl = sum(1 for p_ in placebos if p_["decouvertes_E"] + p_["decouvertes_M"] > 0)
controles["C-2"] = dict(testable=True, passe=nb_pl <= 1, placebos_avec_decouverte=nb_pl)
positifs_testables = sum(1 for k in ("C+1", "C+2", "C+3", "C+4") if controles[k]["testable"])
cru = all(v["passe"] for v in controles.values() if v["testable"]) and positifs_testables >= 3
print("\n== CONTROLES")
for k, v in controles.items(): print(f"   {k}  {'non testable' if not v['testable'] else ('PASSE ' if v['passe'] else 'ECHOUE')}  {v}")
print(f"\n   CHERCHEUR {'CRU' if cru else 'NON CRU'}  ( positifs testables : {positifs_testables} )")

# ------------------------------------------------------------------ sorties
matrice = [dict(lecture=c["lecture"], levier=c["levier"], a=c["a"], b=c["b"], variable=NOMS[j], n_a=c["meta"]["na"], n_b=c["meta"]["nb"],
                strates=c["meta"]["strates"], **{k: r.get(k) for k in ("famille", "ecart", "moy_a", "moy_b", "ecart_std", "z", "p", "q", "decouverte")})
           for c in comps for j, r in c["res"].items()]
pq.write_table(pa.Table.from_pylist(matrice), f"{SORTIE}/matrice.parquet")
json.dump(dict(criteres_commit="6bedbad", episodes=n, variables=len(NOMS), leviers=LEVIERS, controles=controles, cru=cru,
               placebos=placebos, decouvertes=decouvertes, pistes=pistes), open(f"{SORTIE}/resultats.json", "w"), indent=1, default=float)

print("\n== DECOUVERTES ( famille E ), par force")
for d in sorted(decouvertes, key=lambda d: -abs(d["z"])):
    print(f"   [{d['lecture'][:6]}] {d['levier']} {d['a']:g}->{d['b']:g}  {d['effet']:22s} {d['moy_a']:.2f} -> {d['moy_b']:.2f}  z={d['z']:+.1f} q={d['q']:.3g}  n={d['na']}/{d['nb']} strates={d['strates']}")
    for r in d["raisons"][:3]:
        ic = f"[{r['ic'][0]:.2f} ; {r['ic'][1]:.2f}]" if r.get("ic") else ""
        print(f"        raison : {r['variable']:45s} part {r['proportion']:.2f} {ic}  (levier {'+' if r['corr_levier'] > 0 else '-'}, effet r={r['corr_effet']:+.2f})")
    for r in d["pourquoi_du_pourquoi"][:2]:
        print(f"          pourquoi de la raison : {r['variable']:35s} part {r['proportion']:.2f}")
print("\n== PISTES ( correlations intra-strate, PAS des causes ) : 12 premieres par effet")
for e_, ls in pistes.items():
    print(f"   {e_}")
    for d in ls[:12]:
        print(f"      r={d['r']:+.2f} q={d['q']:.2g} n={d['n']:4d}  {d['variable']:48s} leviers : {', '.join(d['leviers_qui_la_bougent'][:3]) or 'AUCUN - levier a construire'}")
print("\nsorties ->", SORTIE)
