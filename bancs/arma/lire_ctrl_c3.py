#!/usr/bin/env python3
"""lire_ctrl_c3 — LE BANC N°3 SAIT-IL DIRE OUI ?

Protocole depose : CONTROLE_POSITIF_C3.md
On compare la survie du TEMOIN a NEUF defenseurs (banc de controle) a celle du TEMOIN a TREIZE
(le banc du verdict), APPARIEE PAR LIEU. Effet attendu, mesure par le balayage du 11/08 dans ce
monde : +11 points. Porte : la borne inferieure a 95 pour cent doit depasser ZERO — on ne
demande pas au controle de franchir la porte du geste, on lui demande de prouver que l aiguille
BOUGE.
"""
import re, sys, math, statistics as stx
from collections import defaultdict
sys.path.insert(0, "/home/younes/arma3-marl")
from cles import Segmenteur

CTRL = "/mnt/data/harmattan-sandbox/logs/serverC3C.out"
REF = "/mnt/data/harmattan-sandbox/logs/pause_12-08_soir/c3_corpus_du_verdict.out"

deb = re.compile(r'HMT\|G\|debut\|(\d+)\|[\d.]+\|\d+\|\d+\|\d+\|(\d+)\|(\d+)\|(\d+)\|')
fin = re.compile(r'HMT\|G\|fin\|(\d+)\|[\d.]+\|\d+\|(\w+)\|(\d+)\|(-?\d+)\|(\d+)\|\d+\|(\d+)\|(\d+)\|')
lieu = re.compile(r'HMT\|G\|LIEUC3\|(\d+)\|(-?\d+)\|(-?\d+)')
couv = re.compile(r'HMT\|G\|COUVERT\|(\d+)\|-?\d+\|\d\|\d\|\d\|(\d)')


def lire(f, temoin_seul):
    seg = Segmenteur(); D, R, L, B = {}, {}, {}, {}
    for line in open(f, encoding='utf-8', errors='ignore'):
        m = lieu.search(line)
        if m: L[seg.cle(f, int(m.group(1)))] = (int(m.group(2)), int(m.group(3))); continue
        m = deb.search(line)
        if m: D[seg.cle_passive(f, int(m.group(1)))] = dict(campDef=int(m.group(2)), nDef=int(m.group(3)), nAtt=int(m.group(4))); continue
        m = fin.search(line)
        if m: R[seg.cle_passive(f, int(m.group(1)))] = dict(ve=int(m.group(6)), vo=int(m.group(7))); continue
        m = couv.search(line)
        if m: B[seg.cle_passive(f, int(m.group(1)))] = int(m.group(2))
    out = defaultdict(list)
    nd = set()
    for k in L:
        if k not in D or k not in R: continue
        if temoin_seul and B.get(k, 0) != 0: continue
        d, r = D[k], R[k]
        nd.add(d['nDef'])
        surv = r['vo'] if d['campDef'] == 0 else r['ve']
        out[L[k]].append(100.0 * surv / max(d['nAtt'], 1))
    return out, nd


C, ndC = lire(CTRL, True)
Rf, ndR = lire(REF, True)
moy = lambda v: sum(v) / len(v) if v else 0.0
print(f"\n  CONTROLE : {sum(len(v) for v in C.values())} accrochages temoin, nDef {sorted(ndC)}")
print(f"  REFERENCE : {sum(len(v) for v in Rf.values())} accrochages temoin, nDef {sorted(ndR)}")

comm = sorted(set(C) & set(Rf), key=str)
comm = [l for l in comm if len(C[l]) >= 8 and len(Rf[l]) >= 8]
print(f"\n  {'lieu':<16}{'9 def n':>9}{'9 def %':>10}{'13 def n':>10}{'13 def %':>11}{'ecart':>9}")
ec = []
for l in comm:
    a, b = moy(C[l]), moy(Rf[l])
    ec.append(a - b)
    print(f"  {str(l):<16}{len(C[l]):>9}{a:>9.1f}%{len(Rf[l]):>10}{b:>10.1f}%{a-b:>+9.1f}")
if len(ec) < 2:
    print("\n  MOINS DE DEUX LIEUX COMMUNS — pas assez pour apparier. On ne lit rien."); sys.exit(0)
m = moy(ec)
s = stx.stdev(ec) if len(ec) > 1 else 0.0
tv = {2:12.71,3:4.30,4:3.18,5:2.78,6:2.57,7:2.45}.get(len(ec), 2.36)
lo = m - tv * s / math.sqrt(len(ec))
print(f"\n    ecart moyen apparie : {m:+.1f} points   borne inferieure 95 % : {lo:+.1f}")
print(f"    (effet attendu, mesure au balayage du 11/08 : +11 points)")
print("\n  LA PORTE DU CONTROLE : la borne doit depasser ZERO.")
print("  " + "-" * 66)
if lo > 0:
    print("    L AIGUILLE BOUGE. Le banc sait dire oui a ce point de fonctionnement.")
    print("    -> Le null du geste n°3 est un VERDICT : se jeter a couvert sous le feu ne")
    print("       change pas la survie, et l intervalle exclut tout effet au-dela de +8,5.")
else:
    print("    L AIGUILLE NE BOUGE PAS. Le banc est MUET a 75 % de survie.")
    print("    -> Le null du geste n°3 n est PAS un verdict, c est un SILENCE. Il se retire")
    print("       du registre en attendant un monde plus severe.")
