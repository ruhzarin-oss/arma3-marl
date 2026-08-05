#!/usr/bin/env python3
"""verdict_oracle.py — LE CRITERE 15/20 EST-IL ATTEIGNABLE ?

⟨Fable, 05/08 : « un banc ou l'information PARFAITE fait match nul avec la ligne droite n'a
 pas la marge pour qu'un agent montre 15/20. Le critere exigeait vraisemblablement
 l'impossible, et les cinq refus ne jugent pas l'agent, ils jugent le banc. »⟩

C'est ma propre regle appliquee AU CRITERE lui-meme : avant de corriger l'agent qui echoue,
verifier que la reussite existe. Cinq refus successifs, et je n'ai jamais fait ce controle.

LE TEST. On applique le critere P3 — EXACTEMENT le meme, sans retouche — a l'ORACLE au lieu
de l'agent. L'oracle libre est le chemin optimal calcule avec l'information PARFAITE :
position et cap de chaque defenseur connus, choix libre du point d'abordage.

  P3 tel qu'il est ecrit : « bat STRICTEMENT la droite sur >= 15 configurations sur 20 »

CONDITION D'ECHEC, DEPOSEE PAR FABLE AVANT CE RUN :
  · oracle >= 15/20 -> le banc est SAIN, l'agent echoue vraiment, et le suspect redevient
    le monde de la sandbox (rejeu du corpus).
  · oracle <  15/20 -> LE BANC FERME. Le critere exigeait l'impossible, les cinq refus ne
    jugent pas l'agent. Le prochain instrument se construit a partir du mecanisme du FEU,
    pas d'une quatrieme variante de l'approche solitaire.

Aucun entrainement. On relit les journaux deja produits.
"""
import re, sys, glob
from math import comb
import numpy as np

JOURNAUX = [('/mnt/data/harmattan-sandbox/logs/serverBA_banc150_risque.out', 'cout APPRIS'),
            ('/mnt/data/harmattan-sandbox/logs/serverBA_banc150b.out',       'cout expo')]
BRAS = ['agent', 'droite', 'droite_bis', 'oracle', 'oracle_libre']

def lire(chemin):
    ess = {}
    try:
        f = open(chemin, errors='ignore')
    except FileNotFoundError:
        return None
    for l in f:
        m = re.search(r'HMT\|B150B\|essai\|(\d+)\|(\w+)\|know\|([\d.]+)\|reste\|(\d+)\|jalons\|\[([-\d,]+)\]', l)
        if m:
            ess.setdefault(int(m.group(1)), {})[m.group(2)] = [int(v) for v in m.group(5).split(',')]
    return {c: v for c, v in ess.items() if all(b in v for b in BRAS)}

def signes(g, p):
    n = g + p
    if n == 0: return 1.0
    k = min(g, p)
    return min(2*sum(comb(n, i) for i in range(k+1))/(2**n), 1.0)

print("\n" + "="*78)
print("  LE CRITERE P3 APPLIQUE A CHAQUE BRAS  — « bat STRICTEMENT la droite sur >= 15/20 »")
print("="*78)

for chemin, nom in JOURNAUX:
    ess = lire(chemin)
    if not ess:
        print(f"\n  {nom} : journal absent ou incomplet ({chemin})")
        continue
    comp = sorted(ess)
    sc = lambda c, b: sum(1 for v in ess[c][b] if v == 1)
    print(f"\n  --- {nom} · {len(comp)} configurations ---")
    print(f"  {'bras':16s} {'gagne':>6s} {'egal':>6s} {'perd':>6s} {'p':>8s}   P3")
    for b in BRAS:
        if b == 'droite': continue
        g = sum(1 for c in comp if sc(c, b) > sc(c, 'droite'))
        p_ = sum(1 for c in comp if sc(c, b) < sc(c, 'droite'))
        e = len(comp) - g - p_
        pv = signes(g, p_)
        marque = 'PASSE' if g >= 15 else 'ECHOUE'
        etoile = '   <- INFORMATION PARFAITE' if b == 'oracle_libre' else ''
        print(f"  {b:16s} {g:6d} {e:6d} {p_:6d} {pv:8.3f}   {marque}{etoile}")

# ---------------------------------------------------------------- le verdict
ess = lire(JOURNAUX[0][0]) or lire(JOURNAUX[1][0])
comp = sorted(ess)
sc = lambda c, b: sum(1 for v in ess[c][b] if v == 1)
g_or = sum(1 for c in comp if sc(c, 'oracle_libre') > sc(c, 'droite'))
g_ag = sum(1 for c in comp if sc(c, 'agent') > sc(c, 'droite'))

print("\n" + "="*78)
print(f"  ORACLE LIBRE, avec information PARFAITE : {g_or} victoires sur {len(comp)}")
print(f"  AGENT                                   : {g_ag} victoires sur {len(comp)}")
print(f"  CRITERE EXIGE                           : 15")
print("="*78)
if g_or >= 15:
    print("  LE BANC EST SAIN. L'information parfaite y atteint le critere, donc la reussite")
    print("  existe et l'agent echoue VRAIMENT. Le suspect redevient le monde de la sandbox.")
else:
    print("  LE BANC FERME. L'information PARFAITE n'atteint pas le critere : il exigeait")
    print("  l'impossible. Les cinq refus successifs ne jugent pas l'agent, ils jugent le banc.")
    print()
    print("  Et la lecture qui en decoule — celle de Fable : le +12,3 points est un fait")
    print("  d'ESCOUADE (deux axes = quelqu'un qui FIXE), alors que ce banc mesure un agent")
    print("  SEUL qui approche SANS TIRER. L'avantage du flanc ne s'exprime pas dans un monde")
    print("  sans feu — ce que la mesure « letalite corrigee -> l'avantage disparait »")
    print("  suggerait deja.")
    print()
    print("  Le prochain instrument se construit a partir du MECANISME DU FEU — qui tire sur")
    print("  qui et quand, sur les 1324 engagements deja captures — et non d'une quatrieme")
    print("  variante de l'approche solitaire.")
print("="*78)
