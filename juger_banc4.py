#!/usr/bin/env python3
"""juger_banc4.py — applique CRITERES_BANC_ESCOUADE4.md au journal, sans rien decider.

Le juge est ecrit AVANT le run et ne lit que les criteres deposes. Il n'a pas le droit
d'inventer un seuil : chaque nombre en dur ici doit se retrouver mot pour mot dans le .md.

  D0 CONTROLE POSITIF  cascade mediane de flanc_etale >= 15 m
  D1 DESCRIPTION       distribution de la cascade par bras — sans seuil
  D2 BRUIT             bruit sur d_grp entre rejeux identiques <= 25 m
  D3 HYPOTHESE         lue SEULEMENT si D0 et D2 passent
  D4 CONTROLE NEGATIF  rien entre flanc_seul et flanc_seul_bis
  D5 PRESENCE          bloc_1axe repere dans >= 18 configs sur 20
  D6 TIR               config ou deux_axes tire 0 coup -> exclue de D3
"""
import re, sys, math
from statistics import median

JOURNAL = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/harmattan-sandbox/logs/serverBA.out'
SEUIL_D0, SEUIL_D2, SEUIL_D3_N, SEUIL_D3_P, SEUIL_D5 = 15.0, 25.0, 14, 0.05, 18


def signes(p):
    """test des signes bilateral, sans scipy : p = liste d'ecarts, egalites exclues."""
    v = [x for x in p if x != 0]
    n = len(v)
    if n == 0:
        return 0, 0, len(p), 1.0
    k = sum(1 for x in v if x < 0)          # k = victoires (ecart negatif = repere plus pres)
    q = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return k, n - k, len(p) - n, min(1.0, 2 * q)


essais = {}
for l in open(JOURNAL, errors='ignore'):
    m = re.search(r'HMT\|ESC4\|essai\|(\d+)\|(\w+)\|d_grp\|(-?\d+)\|d_hom\|(\[[^\]]*\])\|'
                  r'casc\|(-?\d+)\|casc_pas\|(-?\d+)\|repere\|(\d)\|.*?\|tirs\|(\d+)\|', l)
    if m:
        cfg, bras = int(m.group(1)), m.group(2)
        essais.setdefault(cfg, {})[bras] = dict(
            d_grp=max(0, int(m.group(3))),       # -1 (jamais repere) -> 0 m, cf criteres
            casc=int(m.group(5)), casc_pas=int(m.group(6)),
            repere=int(m.group(7)), tirs=int(m.group(8)))

cfgs = sorted(essais)
complets = [c for c in cfgs if len(essais[c]) == 6]
print(f"JOURNAL  {JOURNAL}")
print(f"  {len(cfgs)} configurations vues, {len(complets)} completes (6 bras)\n")
if not complets:
    sys.exit("aucune configuration complete — rien a juger")

BRAS = ['bloc_1axe', 'deux_axes', 'deux_axes_bis', 'flanc_seul', 'flanc_seul_bis', 'flanc_etale']
col = lambda b, k: [essais[c][b][k] for c in complets if b in essais[c]]
verdicts = {}

# ---- D1 DESCRIPTION (sans seuil : elle ne peut pas rater) -------------------
print("D1  DESCRIPTION — cascade, en metres (les -1 sont exclus)")
casc = {}
for b in BRAS:
    v = [x for x in col(b, 'casc') if x >= 0]
    casc[b] = v
    z = 100 * sum(1 for x in v if x == 0) / len(v) if v else float('nan')
    print(f"      {b:16s} n={len(v):2d}  mediane {median(v) if v else float('nan'):5.1f} m"
          f"   part a 0 m : {z:4.0f} %")

# ---- D0 CONTROLE POSITIF ---------------------------------------------------
m_et = median(casc['flanc_etale']) if casc['flanc_etale'] else 0.0
m_fs = median(casc['flanc_seul']) if casc['flanc_seul'] else 0.0
verdicts['D0'] = m_et >= SEUIL_D0
print(f"\nD0  CONTROLE POSITIF   flanc_etale {m_et:.1f} m  (flanc_seul {m_fs:.1f} m)"
      f"   seuil {SEUIL_D0:.0f} m   -> {'PASSE' if verdicts['D0'] else 'ECHOUE'}")
if not verdicts['D0']:
    print("      La detection ne s'etale pas meme a 40 m d'ecartement.")
    print("      La connaissance est de CAMP et instantanee. Toute mesure « combien")
    print("      d'hommes » est morte definitivement — c'est un resultat, pas un echec.")

# ---- D2 BRUIT --------------------------------------------------------------
def med_d(b): return median(col(b, 'd_grp'))
b1 = abs(med_d('deux_axes') - med_d('deux_axes_bis'))
b2 = abs(med_d('flanc_seul') - med_d('flanc_seul_bis'))
bruit = max(b1, b2)
verdicts['D2'] = bruit <= SEUIL_D2
print(f"\nD2  BRUIT              deux_axes/bis {b1:.1f} m · flanc_seul/bis {b2:.1f} m"
      f"   -> retenu {bruit:.1f} m   seuil {SEUIL_D2:.0f} m   -> {'PASSE' if verdicts['D2'] else 'ECHOUE'}")

# ---- D5 PRESENCE -----------------------------------------------------------
n_rep = sum(col('bloc_1axe', 'repere'))
verdicts['D5'] = n_rep >= SEUIL_D5
print(f"\nD5  PRESENCE           bloc_1axe repere {n_rep}/{len(complets)}"
      f"   seuil {SEUIL_D5}   -> {'PASSE' if verdicts['D5'] else 'ECHOUE'}")

# ---- D6 TIR + D3 HYPOTHESE -------------------------------------------------
exclues = [c for c in complets if essais[c]['deux_axes']['tirs'] == 0]
retenues = [c for c in complets if c not in exclues]
print(f"\nD6  TIR                {len(exclues)} config(s) exclue(s) pour 0 coup tire {exclues or ''}")

print(f"\nD3  HYPOTHESE          lue seulement si D0 et D2 passent")
if not (verdicts['D0'] and verdicts['D2']):
    verdicts['D3'] = None
    print("      NON LUE — l'instrument ne s'est pas qualifie. Aucune conclusion tactique.")
else:
    ec = [essais[c]['deux_axes']['d_grp'] - essais[c]['flanc_seul']['d_grp'] for c in retenues]
    k, p_, eg, pv = signes(ec)
    med_ec = median(ec) if ec else float('nan')
    verdicts['D3'] = (k >= SEUIL_D3_N) and (pv < SEUIL_D3_P) and (abs(med_ec) > bruit)
    print(f"      deux_axes repere plus pres (donc plus tard) dans {k}/{len(retenues)}"
          f"  (contre {p_}, egalites {eg})")
    print(f"      p = {pv:.4f}   ecart median {med_ec:+.1f} m   bruit D2 {bruit:.1f} m")
    print(f"      seuils : >= {SEUIL_D3_N} victoires, p < {SEUIL_D3_P}, |ecart| > bruit"
          f"   -> {'PASSE' if verdicts['D3'] else 'ECHOUE'}")

# ---- D4 CONTROLE NEGATIF ---------------------------------------------------
ec4 = [essais[c]['flanc_seul']['d_grp'] - essais[c]['flanc_seul_bis']['d_grp'] for c in complets]
k4, p4, eg4, pv4 = signes(ec4)
verdicts['D4'] = pv4 >= SEUIL_D3_P
print(f"\nD4  CONTROLE NEGATIF   flanc_seul vs son propre rejeu : {k4} / {p4}, egalites {eg4},"
      f" p = {pv4:.4f}   -> {'PASSE' if verdicts['D4'] else 'ECHOUE — D3 ne vaut rien'}")

# ---- VERDICT ---------------------------------------------------------------
print("\n" + "=" * 72)
if not verdicts['D0']:
    print("VERDICT : BRANCHE CLOSE — la detection est de camp et instantanee.")
    print("          Ne plus proposer de mesure « combien d'hommes vus », a aucun ecartement.")
elif not verdicts['D2'] or not verdicts['D5']:
    print("VERDICT : BANC NUL — l'instrument ne se qualifie pas. Rien de tactique n'est conclu.")
elif not verdicts['D4']:
    print("VERDICT : BANC NUL — le controle negatif a bouge. D3 n'est pas lisible.")
elif verdicts['D3']:
    print("VERDICT : HYPOTHESE SOUTENUE — la base de feu retarde la detection du groupe.")
    print("          A rejouer avec des hommes qui peuvent mourir avant tout usage tactique.")
else:
    print("VERDICT : HYPOTHESE NON SOUTENUE sur un instrument qualifie. C'est un vrai negatif.")
print("=" * 72)
print("  " + " · ".join(f"{k}={'PASSE' if v else ('NON LUE' if v is None else 'ECHOUE')}"
                        for k, v in sorted(verdicts.items())))
