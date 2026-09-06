#!/usr/bin/env python3
"""reg_para — SEPARER LA CHARGE DE LA TENDANCE.

⚠️ LA FAUTE DE PLAN, nommee apres coup et assumee : j'ai pre-inscrit un ABAB. Un ABAB
N'ANNULE PAS une tendance lineaire. Avec une pente -d par bloc :
    A1=m, B1=m-d, A2=m-2d, B2=m-3d  ->  moyenne(B) - moyenne(A) = -d
Il reste exactement une pente dans le contraste. C'est ABBA qui l'annule ( = 0 ).
Le contraste brut sur-crediterait donc la parallelisation d'une acceleration qui vient
de l'apprentissage. Le biais va, une fois de plus, dans le sens qui rassure.

Ce qu'on fait a la place, sur les episodes un par un :
    duree ~ a + b*(minutes depuis le debut) + c*(charge)
`b` absorbe la condensation de la politique, `c` est ce qu'on cherche.

⚠️ CE QUE CETTE REGRESSION NE SAIT PAS FAIRE. Elle suppose les episodes independants.
Ils ne le sont pas : ils se groupent par phase de politique. L'IC95 rendu ici est donc
OPTIMISTE — trop etroit. On le lit comme une borne inferieure de l'incertitude, jamais
comme la verite. Deux blocs par condition ne feront jamais une preuve solide ; ils font
une indication, et c'est ce mot-la qu'on emploiera.
"""
import re, sys, math
sys.path.insert(0, "/home/younes/arma3-marl")

LIGNE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}) .*\[ECHP\] RESULT (\d+) ")

def series(rpt):
    out, prec = [], None
    for l in open(rpt, errors="ignore"):
        m = LIGNE.match(l)
        if not m: continue
        t = int(m[1])*3600 + int(m[2])*60 + int(m[3])
        if prec is not None and t < prec: t += 86400
        prec = t
        out.append(t)
    return [(out[i], out[i]-out[i-1]) for i in range(1, len(out)) if 0 < out[i]-out[i-1] < 300]

def hm(s): return int(s[:2])*3600 + int(s[3:])*60

BLOCS = [("A1","18:18","18:38",0), ("B1","18:38","18:58",1),
         ("A2","18:58","19:18",0), ("B2","19:18","19:38",1)]

def main():
    rpt = sys.argv[1]
    pts = []
    for nom, g, h, charge in BLOCS:
        t0, t1 = hm(g), hm(h)
        for t, d in series(rpt):
            if t0 <= t < t1: pts.append((t, d, charge))
    if len(pts) < 20: print("pas assez de points"); return 1
    t_ref = min(p[0] for p in pts)
    X = [[1.0, (t - t_ref)/60.0, float(c)] for t, d, c in pts]
    y = [d for _, d, _ in pts]
    n, k = len(y), 3

    # moindres carres par equations normales 3x3
    A = [[sum(X[i][a]*X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    B = [sum(X[i][a]*y[i] for i in range(n)) for a in range(k)]
    M = [A[r][:] + [B[r]] for r in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(M[r][c])); M[c], M[p] = M[p], M[c]
        for r in range(k):
            if r != c:
                f = M[r][c]/M[c][c]
                for j in range(c, k+1): M[r][j] -= f*M[c][j]
    beta = [M[r][k]/M[r][r] for r in range(k)]
    res = [y[i] - sum(beta[j]*X[i][j] for j in range(k)) for i in range(n)]
    s2 = sum(r*r for r in res)/(n-k)
    # (X'X)^-1 par Gauss-Jordan
    G = [A[r][:] + [1.0 if i == r else 0.0 for i in range(k)] for r in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(G[r][c])); G[c], G[p] = G[p], G[c]
        d = G[c][c]
        for j in range(2*k): G[c][j] /= d
        for r in range(k):
            if r != c:
                f = G[r][c]
                for j in range(2*k): G[r][j] -= f*G[c][j]
    se = [math.sqrt(s2*G[r][k+r]) for r in range(k)]

    print(f"n = {n} episodes de l'instance 0, repartis sur les quatre blocs\n")
    print(f"  tendance    b = {beta[1]:+.4f} s/ep par minute   (IC95 {beta[1]-1.96*se[1]:+.4f} ; {beta[1]+1.96*se[1]:+.4f})")
    print(f"              soit {beta[1]*60:+.2f} s/ep par heure — c'est la politique qui se condense\n")
    lo, hi = beta[2]-1.96*se[2], beta[2]+1.96*se[2]
    print(f"  ==> CHARGE  c = {beta[2]:+.3f} s/ep          (IC95 {lo:+.3f} ; {hi:+.3f})")
    base = sum(y)/n
    print(f"      soit {100*beta[2]/base:+.1f} % du debit de reference ({base:.2f} s/ep)")
    print(f"      IC95 en % : [{100*lo/base:+.1f} ; {100*hi/base:+.1f}]\n")
    if lo <= 0 <= hi:
        print("  Zero est dans l'intervalle : AUCUNE DEGRADATION DETECTEE.")
        print(f"  Ce que le banc exclut : une degradation superieure a {100*hi/base:+.1f} %.")
        print("  Ce qu'il n'exclut pas : tout ce qui est plus petit. Et l'IC est optimiste")
        print("  (episodes traites comme independants alors qu'ils se groupent).")
    else:
        print("  Zero est HORS de l'intervalle : la charge a un effet mesurable.")
    return 0

sys.exit(main())
