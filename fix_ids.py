#!/usr/bin/env python3
"""fix_ids.py — les aretes portent des IDENTIFIANTS, pas des places.

`xt[j,0]` porte l identifiant du soldat ; les aretes portent ces identifiants. Les confondre
avec des indices de tableau fait sortir du tableau — c est exactement le piege que convertir.py
avait note en commentaire : « les aretes portent les IDENTIFIANTS, pas des places : une place
change de sens d un tick a l autre, un identifiant non. »

Je l ai lu, et je l ai quand meme fait. On passe par une table identifiant -> etat, comme
sonde1.py.
"""
import pathlib

p = pathlib.Path('/home/younes/arma3-marl/etiquette_avenir.py')
t = p.read_text(encoding='utf-8')

A1 = """def etat(ti):
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    vu = {}
    dirn = {}
    for a, b, v in par_tick[ti]:
        if not (pt[a] and pt[b] and xt[a, 4] > 0.5 and xt[b, 4] > 0.5):
            continue
        if v < 0.5:
            continue
        dx, dy = xt[a, 1] - xt[b, 1], xt[a, 2] - xt[b, 2]
        gis = math.degrees(math.atan2(dx, dy)) % 360
        a_lui = abs(((gis - xt[b, 7] + 180) % 360) - 180)
        if a_lui < DEMI_CONE:                       # il me voit VRAIMENT
            vu[a] = True
            # d ou vient-il, relativement a MON cap
            rel = ((gis + 180) % 360 - xt[a, 7] + 180) % 360 - 180
            dirn[a] = int(((rel + 45) % 360) // 90)  # 0 devant, 1 droite, 2 derriere, 3 gauche
    return vu, dirn"""
N1 = """def table(ti):
    \"\"\"identifiant -> (x, y, azimut, posture, suppression), vivants presents seulement.\"\"\"
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    d = {}
    for j in range(N):
        if pt[j] and xt[j, 0] > 0 and xt[j, 4] > 0.5:
            d[int(xt[j, 0])] = (xt[j, 1], xt[j, 2], xt[j, 7], xt[j, 8], xt[j, 9])
    return d


def etat(ti, T_):
    vu, dirn = {}, {}
    for a, b, v in par_tick[ti]:
        if a not in T_ or b not in T_ or v < 0.5:
            continue
        xa, ya, aa, _, _ = T_[a]
        xb, yb, ab, _, _ = T_[b]
        gis = math.degrees(math.atan2(xa - xb, ya - yb)) % 360
        a_lui = abs(((gis - ab + 180) % 360) - 180)
        if a_lui < DEMI_CONE:                       # il me voit VRAIMENT
            vu[a] = True
            rel = ((gis + 180) % 360 - aa + 180) % 360 - 180
            dirn[a] = int(((rel + 45) % 360) // 90)  # 0 devant 1 droite 2 derriere 3 gauche
    return vu, dirn"""
assert t.count(A1) == 1, "ancre etat"
t = t.replace(A1, N1, 1)

A2 = """    vu_p, dir_p = etat(ti)
    vu_f, dir_f = etat(tf)
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    ennemis = defaultdict(list)
    for a, b, v in par_tick[ti]:
        if pt[a] and pt[b] and xt[a, 4] > 0.5 and xt[b, 4] > 0.5:
            ennemis[a].append(b)
    for u, es in ennemis.items():
        if not pt[u] or xt[u, 4] < 0.5 or u not in set(np.where(np.asarray(P[tf]))[0]):
            continue
        d = [math.hypot(xt[u, 1] - xt[e, 1], xt[u, 2] - xt[e, 2]) for e in es]
        if not d:
            continue
        j = int(np.argmin(d))
        e = es[j]
        dx, dy = xt[u, 1] - xt[e, 1], xt[u, 2] - xt[e, 2]
        gis = math.degrees(math.atan2(dx, dy)) % 360
        a_lui = abs(((gis - xt[e, 7] + 180) % 360) - 180)
        a_moi = abs((((gis + 180) % 360) - xt[u, 7] + 180) % 360 - 180)
        lignes.append([min(d[j], 400) / 400, a_lui / 180, a_moi / 180,
                       len(es) / 12.0, xt[u, 8] / 3.0, xt[u, 9],
                       1.0 if u in vu_p else 0.0])"""
N2 = """    Tp, Tf = table(ti), table(tf)
    vu_p, dir_p = etat(ti, Tp)
    vu_f, dir_f = etat(tf, Tf)
    ennemis = defaultdict(list)
    for a, b, v in par_tick[ti]:
        if a in Tp and b in Tp:
            ennemis[a].append(b)
    for u, es in ennemis.items():
        if u not in Tf:                       # il doit etre encore la a l arrivee
            continue
        xu, yu, au, pu, su = Tp[u]
        d = [math.hypot(xu - Tp[e][0], yu - Tp[e][1]) for e in es]
        if not d:
            continue
        j = int(np.argmin(d)); e = es[j]
        xe, ye, ae, _, _ = Tp[e]
        gis = math.degrees(math.atan2(xu - xe, yu - ye)) % 360
        a_lui = abs(((gis - ae + 180) % 360) - 180)
        a_moi = abs((((gis + 180) % 360) - au + 180) % 360 - 180)
        lignes.append([min(d[j], 400) / 400, a_lui / 180, a_moi / 180,
                       len(es) / 12.0, pu / 3.0, su,
                       1.0 if u in vu_p else 0.0])"""
assert t.count(A2) == 1, "ancre boucle"
t = t.replace(A2, N2, 1)

p.write_text(t, encoding='utf-8')
import ast
ast.parse(t)
print("identifiants corriges, syntaxe OK")
