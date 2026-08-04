#!/usr/bin/env python3
"""smoke_juge4.py — LE JUGE DOIT SAVOIR ECHOUER.

Un juge qui dit toujours oui ne mesure rien. On lui donne trois mondes fabriques dont on
CONNAIT la reponse, et on exige qu'il les separe. Si les trois verdicts ne sortent pas
differents, le juge est casse et le banc ne doit pas partir.

  monde A  cascade nulle partout          -> D0 doit ECHOUER, branche close
  monde B  cascade etalee, aucun effet    -> D0 passe, D3 doit ECHOUER (vrai negatif)
  monde C  cascade etalee, effet net      -> D0 passe, D3 doit PASSER
"""
import subprocess, sys, random

BRAS = ['bloc_1axe', 'deux_axes', 'deux_axes_bis', 'flanc_seul', 'flanc_seul_bis', 'flanc_etale']


def ligne(cfg, bras, d_grp, casc, repere, tirs):
    return (f'20:00:00 "HMT|ESC4|essai|{cfg}|{bras}|d_grp|{d_grp}|d_hom|[1,2,3]|'
            f'casc|{casc}|casc_pas|2|repere|{repere}|man|4|fix|4|jalons|[0,0,0,0]|'
            f'vus|3|sur|3|pas|29|tirs|{tirs}|arme_vers_man|50|regard_vers_man|50|'
            f'vus_jalons|[0,0,0,0]"')


def monde(nom, casc_etale, effet):
    rnd = random.Random(7)
    out = []
    for c in range(1, 21):
        base = rnd.randint(90, 130)
        for b in BRAS:
            d = base + rnd.randint(-8, 8)
            # L'EFFET PORTE SUR LE BRAS, DONC SUR SON REJEU AUSSI. Le monde qui ne
            # decale que `deux_axes` et pas `deux_axes_bis` fabrique un faux bruit de
            # 40 m et fait echouer D2 — c'est un monde impossible, pas un juge casse.
            if b.startswith('deux_axes'):
                d -= effet
            casc = 0 if b != 'flanc_etale' else casc_etale
            out.append(ligne(c, b, d, casc, 1, 150 if 'deux_axes' in b else 0))
    f = f'/tmp/smoke_juge4_{nom}.out'
    open(f, 'w').write("\n".join(out) + "\n")
    return f


attendu = {'A': ('D0', False), 'B': ('D3', False), 'C': ('D3', True)}
mondes = {'A': monde('A', 0, 0), 'B': monde('B', 30, 0), 'C': monde('C', 30, 40)}

ok = True
for nom, f in mondes.items():
    r = subprocess.run([sys.executable, '/home/younes/arma3-marl/juger_banc4.py', f],
                       capture_output=True, text=True)
    ligne_v = [l for l in r.stdout.splitlines() if l.startswith('VERDICT')]
    etat = dict(p.split('=') for p in r.stdout.splitlines()[-1].strip().split(' · '))
    cle, veut = attendu[nom]
    obtenu = etat.get(cle)
    bon = (obtenu == 'PASSE') == veut
    ok &= bon
    print(f"monde {nom} : {cle}={obtenu:8s} attendu {'PASSE' if veut else 'ECHOUE':6s}"
          f"  {'OK' if bon else '!! LE JUGE NE DISCRIMINE PAS'}")
    print(f"          {ligne_v[0] if ligne_v else '(pas de verdict)'}")

print("\nSMOKE JUGE :", "OK — le juge sait dire non" if ok else "REFUSE — juge casse")
sys.exit(0 if ok else 1)
