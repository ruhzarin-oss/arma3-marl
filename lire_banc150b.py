#!/usr/bin/env python3
"""lire_banc150b.py — LA PREMIERE MESURE VALIDE DE L'AGENT.

METRIQUE : la SURVIE AUX JALONS. Etait-il encore invisible en franchissant 120, 90, 60,
puis 40 m ? Un jalon est une POSITION, pas une duree — aucun chemin n'est avantage par sa
forme. ⟨la distance de reperage, utilisee jusqu'ici, est structurellement biaisee contre
les chemins longs : un serpentin passe l'essentiel de ses points loin de l'objectif, donc
a hasard EGAL il enregistre mecaniquement une distance plus grande⟩

Score d'un bras sur une configuration = nombre de jalons franchis encore invisible, de 0 a 4.

LES QUATRE PORTES, ECRITES AVANT LE RUN, RECOPIEES ICI SANS RETOUCHE :
  P1 PRESENCE : la droite doit etre vue avant 40 m dans >= 16 configurations sur 20.
  P2 NUL      : droite et droite_bis doivent donner le meme score sur >= 18 configurations.
  P3 AGENT    : l'agent bat STRICTEMENT la droite sur >= 15 configurations sur 20.
  P4 PLAFOND  : l'oracle libre doit faire au moins aussi bien que la droite en mediane.
"""
import re, sys
import numpy as np

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
BRAS = ['agent', 'droite', 'droite_bis', 'oracle', 'oracle_libre']
JALONS = [120, 90, 60, 40]

ess, cfgs, regard = {}, {}, {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|B150B\|essai\|(\d+)\|(\w+)\|know\|([\d.]+)\|reste\|(\d+)\|jalons\|\[([-\d,]+)\]\|points\|(\d+)\|couche\|(\d+)', l)
    if m:
        ess.setdefault(int(m.group(1)), {})[m.group(2)] = dict(
            know=float(m.group(3)), reste=int(m.group(4)),
            jal=[int(v) for v in m.group(5).split(',')],
            n=int(m.group(6)), couche=int(m.group(7)))
    m = re.search(r'HMT\|B150B\|config\|(\d+)\|defenseurs\|(\d+)\|derive_max\|([\d.]+)', l)
    if m: cfgs[int(m.group(1))] = dict(n=int(m.group(2)), derive=float(m.group(3)))
    m = re.search(r'HMT\|B150B\|regard\|(\d+)\|ecart_max\|(\d+)\|ecart_moyen\|(\d+)', l)
    if m: regard.setdefault(int(m.group(1)), []).append((int(m.group(2)), int(m.group(3))))

comp = sorted(c for c in ess if all(b in ess[c] for b in BRAS))
print(f"  configurations completes : {len(comp)} / 20   ({len(BRAS)} bras chacune)")
if not comp:
    print(f"  ({sum(len(v) for v in ess.values())} essais — le run n'est pas fini)"); sys.exit(1)

der = [cfgs[c]['derive'] for c in comp if c in cfgs]
if der: print(f"  derive de POSITION des defenseurs : mediane {np.median(der):.1f} m · max {max(der):.1f} m")

# ------------------------------------------------------------------ LE REGARD
tous_r = [v for c in comp for v in regard.get(c, [])]
if tous_r:
    emax = [a for a, _ in tous_r]; emoy = [b for _, b in tous_r]
    print(f"\n  LE REGARD DES DEFENSEURS  ({len(tous_r)} releves a 1 Hz, eyeDirection)")
    print(f"     ecart au cap voulu : median {np.median(emoy):.0f}° · "
          f"90e centile {np.percentile(emax,90):.0f}° · max {max(emax):.0f}°")
    if np.percentile(emax, 90) > 20:
        print("     -> LES TETES BALAIENT. La carte d'ombre STATIQUE ne veut plus rien dire,")
        print("        et l'effet de duree s'explique mecaniquement : cone balayant x temps.")
    else:
        print("     -> les regards sont FIXES. La carte d'ombre statique tient, et la duree")
        print("        ne s'explique pas par un balayage.")
else:
    print("\n  AUCUNE TELEMETRIE DE REGARD — le pas a echoue, voir Fable (condition d'echec).")

# ------------------------------------------------------------------ LES SCORES
def score(c, b):
    """nombre de jalons franchis encore invisible. -1 = jalon non franchi, ne compte pas."""
    return sum(1 for v in ess[c][b]['jal'] if v == 1)
def franchis(c, b):
    return sum(1 for v in ess[c][b]['jal'] if v >= 0)

print("\n  " + "="*74)
print("  SURVIE AUX JALONS 120 / 90 / 60 / 40 m   (score = jalons franchis invisible, /4)")
print("  " + "-"*74)
print("  bras            score median   jalons survecus   arrive invisible   longueur")
for b in BRAS:
    s = [score(c, b) for c in comp]
    tot = sum(s); pos = sum(franchis(c, b) for c in comp)
    inv = sum(1 for c in comp if ess[c][b]['jal'][-1] == 1)
    L = [ess[c][b]['n'] for c in comp]
    print(f"  {b:14s}  {np.median(s):6.1f}       {tot:3d} / {pos:3d}"
          f"            {inv:2d} / {len(comp)}         {np.median(L):5.0f} pts")
print("  " + "="*74)

nc = sum(ess[c]['agent']['couche'] for c in comp)
np_ = sum(ess[c]['agent']['n'] for c in comp)
print(f"\n  POSTURES DE L'AGENT : couche sur {nc}/{np_} pas ({nc/max(np_,1):.0%})"
      f"   ⟨0 % avant le cliquet⟩")

# ------------------------------------------------------------------ LES PORTES
vue = sum(1 for c in comp if score(c, 'droite') < 4)
p1 = vue >= 16
print(f"\n  P1 PRESENCE : la droite est vue avant 40 m dans {vue}/{len(comp)} (exige >= 16)"
      f"  -> {'OK' if p1 else 'ECHEC'}")

acc = sum(1 for c in comp if score(c, 'droite') == score(c, 'droite_bis'))
p2 = acc >= 18
print(f"  P2 NUL      : droite et droite_bis donnent le meme score sur {acc}/{len(comp)} "
      f"(exige >= 18)  -> {'OK' if p2 else 'ECHEC'}")

gagne = sum(1 for c in comp if score(c, 'agent') > score(c, 'droite'))
egal  = sum(1 for c in comp if score(c, 'agent') == score(c, 'droite'))
perd  = len(comp) - gagne - egal
p3 = gagne >= 15
print(f"  P3 AGENT    : bat la droite sur {gagne}/{len(comp)} (exige >= 15) · "
      f"egalite {egal} · perd {perd}  -> {'OK' if p3 else 'ECHEC'}")

m_lib = np.median([score(c, 'oracle_libre') for c in comp])
m_dr  = np.median([score(c, 'droite') for c in comp])
p4 = m_lib >= m_dr
print(f"  P4 PLAFOND  : oracle libre {m_lib:.1f} contre droite {m_dr:.1f}  "
      f"-> {'OK' if p4 else 'ECHEC'}")

# ------------------------------------------------------------------ L'EFFET DUREE, REJUGE
# Avec une metrique non biaisee par la forme du trajet, l'effet de duree tient-il encore ?
paires = [(ess[c][b]['n'], score(c, b)) for c in comp for b in BRAS]
r = lambda v: np.argsort(np.argsort(v)).astype(float)
rho = float(np.corrcoef(r([a for a, _ in paires]), r([b for _, b in paires]))[0, 1])
lo = [s for n, s in paires if n >= 60]; ct = [s for n, s in paires if n < 60]
print(f"\n  L'EFFET DUREE, REJUGE SUR UNE METRIQUE NON BIAISEE")
print(f"     correlation longueur <-> survie : rho = {rho:+.2f}  (n={len(paires)})")
if ct and lo:
    print(f"     chemins courts (< 60 pts) : score {np.median(ct):.1f}   (n={len(ct)})")
    print(f"     chemins longs (>= 60 pts) : score {np.median(lo):.1f}   (n={len(lo)})")
print(f"     ⟨sur la distance de reperage, l'effet valait rho = +0,43 — mais cette metrique")
print(f"      etait biaisee contre les chemins longs. Voici le verdict propre.⟩")

print("\n  " + "="*74)
cedees = [k for k, v in dict(P1=p1, P2=p2, P3=p3, P4=p4).items() if not v]
if not cedees:
    print("  L'AGENT EST CERTIFIE. Premiere mesure valide, sur un instrument controle.")
elif cedees == ['P3']:
    print("  L'INSTRUMENT TIENT, L'AGENT NE PASSE PAS. C'est enfin un refus INTERPRETABLE :")
    print("  banc non sature, metrique non biaisee, posture libre, controle nul passe.")
else:
    print(f"  PORTES CEDEES : {', '.join(cedees)}. Voir ci-dessus avant toute conclusion.")
print("  " + "="*74)
