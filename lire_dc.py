import re, pathlib
L = pathlib.Path("/mnt/data/harmattan-sandbox/logs/sonde_dcover.out").read_text(errors="ignore")
S = dict((m[0], (float(m[1]), float(m[2]), float(m[3])))
         for m in re.findall(r'HMT\|DC\|site\|(\w+)\|moy_locale\|([\d.eE+-]+)\|seuil_nouveau\|([\d.eE+-]+)\|seuil_ancien\|([\d.eE+-]+)', L))
P = {}
for nom, d, a, n in re.findall(r'HMT\|DC\|PT\|(\w+)\|dist\|(\d+)\|ancien\|(\d+)\|nouveau\|(\d+)', L):
    P.setdefault(nom, []).append((int(d), int(a), int(n)))
def med(v):
    v = sorted(v); return v[len(v)//2] if v else 0
print("─── LES SEUILS ───")
for k,(m,sn,sa) in S.items():
    print(f"  {k:<8} moyenne locale {m:.3f} m/cellule   seuil NOUVEAU {sn:.3f}   seuil ANCIEN {sa:.3f}   rapport x{sa/max(sn,1e-9):.1f}")
print("\n─── CONTROLE POSITIF 1 : la moyenne locale est-elle > 0 ? ───")
ok1 = all(m > 0.01 for m,_,_ in S.values())
for k,(m,_,_) in S.items(): print(f"  {k:<8} {m:.4f}")
print("  " + ("✓ PASSE" if ok1 else "⛔ TOMBE — moyenne nulle, seuil nul, tout devient couvert"))
print("\n─── CONTROLE POSITIF 2 : la sonde reproduit-elle la panne connue ? ───")
pl = P.get("PLAT", [])
gf = 100*sum(1 for _,a,_ in pl if a >= 16)/max(len(pl),1)
print(f"  site PLAT, ANCIEN seuil : garde-fou dans {gf:.1f} % des points   (mesure du banc : 78,3 %)")
ok2 = gf > 50
print("  " + ("✓ PASSE — la sonde voit bien la panne" if ok2 else "⛔ TOMBE — elle ne mesure pas ce que le banc mesurait"))
print("\n─── LA PORTE : mediane de dcover dans [0,000 ; 0,131], cible 0,035 ───")
for k, v in P.items():
    ma, mn = med([a for _,a,_ in v])/30, med([n for _,_,n in v])/30
    ga = 100*sum(1 for _,a,_ in v if a>=16)/len(v); gn = 100*sum(1 for _,_,n in v if n>=16)/len(v)
    print(f"  {k:<8} ANCIEN  mediane {ma:.3f}  garde-fou {ga:.1f} %")
    print(f"  {'':<8} NOUVEAU mediane {mn:.3f}  garde-fou {gn:.1f} %   " +
          ("✓ dans la plage" if 0.0 <= mn <= 0.131 else "⛔ HORS plage"))
mn_new = med([n for _,_,n in P.get("NOUVEAU", [(0,0,99)])])/30
print(f"\n  ⇒ site du banc, nouveau seuil : {mn_new:.3f}  (gymnase 0,035)  → " +
      ("PASSE, on deploie" if 0.0 <= mn_new <= 0.131 else "TOMBE, on ne deploie pas"))
