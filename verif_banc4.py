#!/usr/bin/env python3
"""verif_banc4.py — controle de forme AVANT de lancer le banc.
Ne prouve pas que le SQF est correct : prouve seulement qu'il n'est pas casse."""
import re, sys, collections

D = '/home/younes/arma3-marl/bancs/arma/'
ok = True


def eq(label, a, b):
    global ok
    good = a == b
    ok &= good
    print(f"  {label:34s} {a} / {b}   {'OK' if good else 'DESEQUILIBRE'}")


print("=== banc_escouade4.sqf ===")
s = open(D + 'banc_escouade4.sqf').read()
s2 = re.sub(r'//[^\n]*', '', s)
for o, c in [('{', '}'), ('[', ']'), ('(', ')')]:
    eq(f"delimiteurs {o}{c}", s2.count(o), s2.count(c))
eq("guillemets doubles (pair)", s2.count('"') % 2, 0)

# le format doit avoir autant de %N que d'arguments passes
m = re.search(r'format \["(HMT\|ESC4\|essai\|[^"]+)"', s)
n_slots = len(set(re.findall(r'%(\d+)', m.group(1))))
bloc = s[m.start():s.index('call HMT_LOG', m.start())]
n_args = bloc.count(',') - bloc.count('format ["') + 1
print(f"  champs %N dans le format          {n_slots}")
eq("plus haut %N == nb de champs", max(int(x) for x in re.findall(r'%(\d+)', m.group(1))), n_slots)

for v in ['_dGrp', '_dHom', '_casc', '_cascPas', '_repere', 'HMT_SU_UN']:
    n = len(re.findall(re.escape(v), s))
    print(f"  {v:34s} {n} occurrences   {'OK' if n >= 2 else 'JAMAIS UTILISE'}")
    ok &= n >= 2

print("\n=== donnees_escouade4.sqf ===")
d = open(D + 'donnees_escouade4.sqf').read()
eq("delimiteurs []", d.count('['), d.count(']'))
bras = re.findall(r'\["(\w+)",\[\["[MF]"', d)
c = collections.Counter(bras)
print(f"  configurations                     {d.count('HMT_DATA') and len(re.findall(chr(10) + r'\[\[', d)) + 1}")
print(f"  bras : {dict(c)}")
attendu = {'bloc_1axe', 'deux_axes', 'deux_axes_bis', 'flanc_seul', 'flanc_seul_bis', 'flanc_etale'}
eq("bras distincts == 6", len(c), 6)
ok &= set(c) == attendu
print(f"  jeu de bras attendu                {'OK' if set(c) == attendu else 'MANQUE ' + str(attendu - set(c))}")
eq("chaque bras x 20 configs", sorted(set(c.values())), [20])

print("\nVERDICT DE FORME :", "OK — le banc peut partir" if ok else "REFUSE — corriger avant de lancer")
sys.exit(0 if ok else 1)
