#!/usr/bin/env python3
"""depouille_appui.py — v3 — TROIS BRAS : temoin, feu SCRIPTE, feu NATIF du moteur.

REGLE DE DECISION DEPOSEE AVANT ⟨Fable, 08/08⟩ : le professeur du n°2 adoptera l implementation
qui passe l etage 1 ; a EGALITE, le NATIF est prefere — moins de code, moins de fautes.
Le banc cesse d etre une reparation et devient un COMPARATEUR D IMPLEMENTATIONS.


LA PORTE EST EN DEUX ETAGES ⟨Fable, 08/08⟩, et ce script n en juge QU UN :
  · ETAGE 1, ici : la baisse de riposte doit etre LISIBLE — intervalle excluant zero.
    AUCUN SEUIL CHIFFRE EMPRUNTE : l ancre certifiee du -92 % vient du regime A DECOUVERT
    et ne se convertit pas dans le regime a couvert. On refuse d inventer la conversion.
  · ETAGE 2, PAS ICI : le verdict qui compte est la PORTE 0 du lieu, ses 10 points sur la prise.

  > Ce banc n a qu UN SEUL DROIT : tuer la mission a bas prix si la suppression est NULLE.
  > S il la trouve faiblement vivante, IL SE TAIT et laisse le banc du lieu trancher.

LES CONTROLES SONT LUS AVANT LA GRANDEUR. Si l un tombe, aucun verdict n est prononce.
"""
import re, sys, math

# ⚠️ TROIS SESSIONS, TROIS FICHIERS. `relancer.sh` repart sur un journal neuf a chaque
# lancement : serverAP.out ne porte plus que la DERNIERE session. Un depouillement qui ne lirait
# que lui analyserait un tiers de la campagne en croyant la lire entiere — panne silencieuse.
# La session est un BLOC ⟨plan depose⟩, et les trois blocs se lisent ensemble.
F = sys.argv[1:] or ['/mnt/data/harmattan-sandbox/logs/session1.out',
                     '/mnt/data/harmattan-sandbox/logs/session2.out',
                     '/mnt/data/harmattan-sandbox/logs/serverAP.out']
# L ORDRE DES CHAMPS SUIT LE JOURNAL, verifie sur une ligne reelle plutot que de memoire :
#   bras|rep|terrain|delivre|armes|cap0|cap1|coupsdef|coupsapp|murs|corps|angle|refus|vise|supp|vivants
# ⚠️ FORMAT MIS A JOUR APRES L AMENDEMENT N°1. Le recensement est desormais DESAGREGE PAR
# ROLE — `cap0|<defenseurs>/<appuis>` et `cap1|<defenseurs>/<appuis>/res<N>` — parce que ce ne
# sont pas les memes hommes qui s assechent. Le depouillement, lui, lisait encore l ancien
# format : il aurait analyse ZERO essai et refuse de conclure sans dire pourquoi. C est l essai
# a blanc qui l a vu, en dix secondes, au lieu de trois sessions de serveur.
pat = re.compile(r'HMT\|AP\|essai\|(\d+)\|(\d+)\|terrain\|(-?\d+)\|delivre\|(\d+)\|delivre2\|(\d+)'
                 r'\|combat\|(\d+)\|armes\|(\d+)\|cap0\|([\d,]+)/([\d,]+)'
                 r'\|cap1\|([\d,]+)/([\d,]+)/res(\d+)\|coupsdef\|(\d+)\|coupsapp\|(\d+)'
                 r'\|murs\|(\d+)\|corps\|(\d+)\|angle\|([-\d.]+)\|refus\|(\d+)\|vise\|([-\d.]+)'
                 r'\|supp\|([-\d.]+)\|vivants\|(\d+)\|(\d+)')
E = []
for L in [x for f in F for x in open(f, encoding='utf-8', errors='ignore')]:
    m = pat.search(L)
    if m:
        (b, r, te, dl, dl2, cb, ar, c0d, c0a, c1d, c1a, res,
         cd, ca, mu, co, an, rf, vi, su, vd, vv) = m.groups()
        E.append(dict(bras=int(b), rep=int(r), terrain=int(te), dl=int(dl), dl2=int(dl2),
                      combat=int(cb), armes=int(ar), res=int(res), cd=int(cd), ca=int(ca),
                      murs=int(mu), corps=int(co), angle=float(an), refus=int(rf),
                      vise=float(vi), supp=float(su), vd=int(vd), vv=int(vv),
                      cap0d=[int(x) for x in c0d.split(',')],
                      cap0a=[int(x) for x in c0a.split(',')],
                      cap1d=[int(x) for x in c1d.split(',')],
                      cap1a=[int(x) for x in c1a.split(',')]))

pre = [e for e in E if e['rep'] == 0]
E = [e for e in E if e['rep'] > 0]
BRAS = {0: 'temoin', 1: 'feu scripte', 2: 'feu natif'}
G = {b: [e for e in E if e['bras'] == b] for b in BRAS}
print(f"\n  pre-vols : {len(pre)} · essais juges : {len(E)}  ("
      + " · ".join(f"{len(G[b])} {n}" for b, n in BRAS.items()) + ")")

# ═══════════════════════════════════════════════════════════════════════════════════════
# LES CONTROLES, EN DEUX FAMILLES — protocole REDEPOSE le 11/08 a 00 h 30.
#
# ⚠️ POURQUOI LE PROTOCOLE PRECEDENT EST MORT. Tous ses controles etaient des MINIMA ou des
# MAXIMA sur des essais individuels. Un tel controle affirme que le phenomene qu il surveille
# a une probabilite de defaut de ZERO. Or la sonde radio du 10/08 a MESURE ~8 % de rate
# silencieux sur un bras qui prend son ordre : mon propre registre refutait donc la forme de
# mes propres controles. Consequence : un seul essai pathologique — session 2, terrain 4,
# temoin a zero impact — a condamne DEFINITIVEMENT quatre sessions et 48 essais, sans recours,
# puisqu un minimum ne remonte jamais quand on ajoute des donnees.
# ⟨Fable, 11/08⟩ « L ACCORD D INSTRUMENT reste absolu par essai — un desaccord vrai n est pas
# une malchance, c est une impossibilite. La PRESENCE D UN PHENOMENE est stochastique : sa
# forme correcte est celle d une porte — TAUX, seuil, TAILLE, et NIVEAU egal a celui que la
# decision emploie. »
#
# LE NIVEAU QUE LA DECISION EMPLOIE EST LE TERRAIN, pas l essai : la grandeur est le rapport
# apparie PAR TERRAIN. Un zero isole parmi quatre repetitions ne rend rien d indefini ; un
# terrain dont le temoin TOTAL est nul, si.
#
# ⚠️ LES 48 ESSAIS DES QUATRE PREMIERES SESSIONS SONT DES PARTIELS. Ils ont DIMENSIONNE les
# seuils ci-dessous ; ils ne certifient rien et ne se relisent pas sous ce protocole.
# ═══════════════════════════════════════════════════════════════════════════════════════
PARTIELS = ('session1.out', 'session2.out', 'session3.out', 'session4.out')
for _f in F:
    if any(_p in _f for _p in PARTIELS):
        print(f"\n  REFUS : {_f} est un PARTIEL de la campagne close le 11/08.")
        print("  Les partiels ont dimensionne ce protocole ; les relire sous lui serait")
        print("  exactement l interdit depose. ⟨Fable : « aucune relecture des 48 »⟩")
        sys.exit(1)

ok = True
def dire(nom, cond, detail):
    global ok
    print(f"    {'PASSE' if cond else 'TOMBE':>6}  {nom:<40} {detail}")
    if not cond: ok = False
med = lambda v: sorted(v)[len(v)//2] if v else -1
T, tir = G[0], G[1] + G[2]
_ter = sorted(set(e['terrain'] for e in E if e['terrain'] >= 0))

# ─────────────────────────────────────────────────────────────────────────────────────
print("\n  FAMILLE 1 — ACCORD D INSTRUMENT · ABSOLU, par essai")
print("    Un desaccord entre les deux chemins n est pas une malchance : c est une")
print("    impossibilite. Aucun taux ne s applique ici.")
# R11 : deux chemins vers LA MEME grandeur. `HandleDamage` retourne ~7,3 fois `HitPart`.
_rap = [e['dl2'] / e['dl'] for e in E if e['dl'] > 0]
if _rap:
    _m = sorted(_rap)[len(_rap)//2]
    _hors = [x for x in _rap if abs(x - _m) / _m > 0.20]
    dire("accord des deux chemins (±20 % de la mediane)", not _hors,
         f"mediane {_m:.2f} · {len(_hors)} essais hors tolerance sur {len(_rap)}")
# un zero doit etre un zero SUR LES DEUX CHEMINS, sinon c est l instrument qui invente
_zdes = [e for e in E if e['dl'] == 0 and e['dl2'] != 0]
dire("un zero est un zero sur LES DEUX chemins", not _zdes,
     f"{len(_zdes)} desaccords sur zero")
# garanties de CONSTRUCTION : elles ne dependent d aucun alea du monde.
dire("nul — l appui se tait au temoin", bool(T) and all(e['ca'] == 0 for e in T),
     f"max {max((e['ca'] for e in T), default=-1)} coups")
dire("charge — les fusils qui doivent tirer sont pleins",
     bool(E) and all(e['armes'] == (6 if e['bras'] == 0 else 9) for e in E),
     f"temoin min {min([e['armes'] for e in G[0]], default=-1)}/6 · feux min "
     f"{min([e['armes'] for e in G[1]+G[2]], default=-1)}/9")
dire("effectif constant 6 def / 4 vic", bool(E) and all(e['vd'] == 6 and e['vv'] == 4 for e in E),
     f"{sum(1 for e in E if e['vd'] != 6 or e['vv'] != 4)} essais degrades")
JOUES = [b for b in BRAS if G[b]]
dire("bras equilibres", len(set(len(G[b]) for b in JOUES)) == 1 and 0 in JOUES and len(JOUES) >= 2,
     " contre ".join(f"{len(G[b])} {BRAS[b]}" for b in JOUES))
dire("terrains — le banc ne juge pas UN endroit", len(_ter) >= 2, f"{len(_ter)} terrains joues")
if E:
    _d = [e['cap0d'] for e in E] + [e['cap1d'] for e in E]
    _a = [e['cap0a'] for e in E] + [e['cap1a'] for e in E]
    _af = [e['cap0a'] for e in E if e['bras'] != 0] + [e['cap1a'] for e in E if e['bras'] != 0]
    dire("capacite — les 6 defenseurs pouvaient combattre", all(x[0] == 6 for x in _d),
         f"min {min(x[0] for x in _d)} sur 6")
    dire("capacite — les defenseurs pouvaient tirer", all(x[1] == 6 for x in _d),
         f"min {min(x[1] for x in _d)} sur 6")
    dire("capacite — les appuis du bras de feu pouvaient tirer",
         all(x[1] == 3 for x in _af), f"min {min((x[1] for x in _af), default=-1)} sur 3")
    dire("capacite — les appuis pouvaient pivoter", all(x[2] == 3 for x in _a),
         f"min {min(x[2] for x in _a)} sur 3")
    dire("reserve — personne ne descend sous 60 coups", all(e['res'] >= 60 for e in E),
         f"minimum observe {min((e['res'] for e in E), default=-1)} coups")

# ─────────────────────────────────────────────────────────────────────────────────────
print("\n  FAMILLE 2 — PRESENCE D UN PHENOMENE · en TAUX, au niveau du TERRAIN")
print("    Ces phenomenes ratent parfois : la sonde du 10/08 a mesure ~8 % de rate")
print("    silencieux. Un `min` par essai leur affirmerait une probabilite de defaut nulle.")
# ─── LE SEUL ABSOLU DE CETTE FAMILLE, et il l est parce que la DECISION le rend impossible :
# un terrain dont le temoin total est nul n a pas de rapport. Ce n est pas un alea, c est une
# division par zero. Sur les partiels : 0 terrain sur 6.
_tnul = [te for te in _ter if sum(e['dl'] for e in G[0] if e['terrain'] == te) == 0]
dire("TERRAIN — aucun temoin TOTAL nul (rapport defini)", not _tnul,
     f"{len(_tnul)} terrains indefinis sur {len(_ter)}")
# ─── LES TAUX. Seuil depose : 15 %. DIMENSIONNE SUR LES PARTIELS, qui ont rendu 4,2 %
# (1 essai temoin a zero sur 24), 0 % de bras natif muet et 0 % de muret vierge. Le seuil est
# pose a plus de trois fois le taux observe et au double du rate silencieux mesure par la
# sonde : il laisse passer l alea sans laisser passer un monde qui se vide.
# TAILLE deposee : au moins 24 essais par bras — quatre repetitions sur six terrains. En deca,
# le taux n est pas lisible et le controle se declare INSUFFISANT, jamais « passe ».
SEUIL_TAUX, TAILLE_MIN = 0.15, 24
def taux(nom, mauvais, total, detail):
    global ok
    if total < TAILLE_MIN:
        print(f"    {'INSUFF':>6}  {nom:<40} {total} essais sur {TAILLE_MIN} requis — pas lisible")
        ok = False; return
    p = mauvais / total
    print(f"    {'PASSE' if p <= SEUIL_TAUX else 'TOMBE':>6}  {nom:<40} "
          f"{mauvais}/{total} = {100*p:.1f} % (seuil {100*SEUIL_TAUX:.0f} %) {detail}")
    if p > SEUIL_TAUX: ok = False
taux("le temoin delivre", sum(1 for e in T if e['dl'] == 0), len(T), "")
taux("les deux feux tirent vraiment", sum(1 for e in tir if e['ca'] == 0), len(tir), "")
taux("les murets encaissent", sum(1 for e in tir if e['murs'] == 0), len(tir),
     f"median {med([e['murs'] for e in tir])} impacts")

if not ok:
    print("\n  AUCUN VERDICT. Un controle est tombe — le banc ne mesure pas ce qu il pretend.")
    sys.exit(0)

def moy(v): return sum(v)/len(v) if v else 0.0
def ec(v):
    m = moy(v)
    return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1)) if len(v) > 1 else 0.0

# ═══ LE RATIO APPARIE PAR TERRAIN — la statistique que le protocole a DEPOSEE ═══
# ⚠️ LE CODE NE L IMPLEMENTAIT PAS. Il comparait des MOYENNES NON APPARIEES, ou la variance
# entre terrains (temoin de 110 a 292) noie tout : intervalle [-8,9 ; 144,6], verdict « nul »,
# alors que SIX terrains sur SIX etaient sous l unite. Ce n est pas un changement de critere
# apres coup — c est le code qui ne faisait pas ce que le protocole disait. ⟨regle 12 : la
# ligne de base appartient au lieu ; les repetitions n achetent presque rien, les terrains
# achetent tout⟩
t_ = [e['dl'] for e in G[0]]
print(f"\n  LA GRANDEUR — impacts DELIVRES par les defenseurs a couvert, en 120 s")
verdict = {}
for b in [x for x in (1, 2) if G[x]]:
    ratios, noms = [], []
    for te in sorted(set(e['terrain'] for e in E if e['terrain'] >= 0)):
        a = [e['dl'] for e in G[b] if e['terrain'] == te]
        w = [e['dl'] for e in G[0] if e['terrain'] == te]
        if a and w and moy(w) > 0:
            ratios.append(moy(a) / moy(w)); noms.append(te)
    if len(ratios) < 2:
        verdict[b] = False; continue
    # on travaille en LOGARITHMES : un ratio est multiplicatif, sa moyenne l est aussi.
    lr = [math.log(r) for r in ratios]
    m, s = moy(lr), ec(lr)
    se = s / math.sqrt(len(lr))
    tc = {2: 12.71, 3: 4.30, 4: 3.18, 5: 2.78, 6: 2.57, 7: 2.45, 8: 2.36}.get(len(lr), 2.26)
    lo, hi = math.exp(m - tc * se), math.exp(m + tc * se)
    geo = math.exp(m)
    sous = sum(1 for r in ratios if r < 1)
    vivant = hi < 1.0
    verdict[b] = vivant
    print(f"    {BRAS[b]}")
    print(f"      ratios par terrain : " + " · ".join(f"{r:.2f}" for r in ratios))
    print(f"      moyenne geometrique : {geo:.3f}   soit {100*(1-geo):.0f} % de capacite en moins")
    print(f"      intervalle 95 %     : [{lo:.3f} ; {hi:.3f}]   sur {len(lr)} terrains")
    print(f"      terrains sous l unite : {sous} sur {len(ratios)}"
          + (f"   (un sur {2**len(ratios)} par hasard)" if sous == len(ratios) else ""))
    print(f"      ETAGE 1 : {'VIVANT — l intervalle exclut l unite' if vivant else 'non conclu — l intervalle contient l unite'}")

print(f"\n  LE MEME VERDICT SUR CHAQUE TERRAIN ? ⟨la question de Younes, 09/08⟩")
print(f"    {'terrain':<9}{'temoin':>9}{'scripte':>9}{'natif':>9}{'ecart natif':>13}")
for te in sorted(set(e['terrain'] for e in E if e['terrain'] >= 0)):
    l = {b: [e['dl'] for e in E if e['terrain'] == te and e['bras'] == b] for b in BRAS}
    if l[0] and moy(l[0]) > 0:
        print(f"    {te:<9}{moy(l[0]):>9.0f}{moy(l[1]):>9.0f}{moy(l[2]):>9.0f}"
              f"{(100.0*(moy(l[0])-moy(l[2]))/moy(l[0]) if l[2] else 0):>12.0f}%")
print("    ⟨si l ecart change de signe ou d ordre de grandeur d un terrain a l autre, ce banc")
print("     ne mesure pas une mecanique mais un ENDROIT, et son verdict est un accident.⟩")

print(f"\n  LE REGIME, pour qu on sache de quel monde on parle")
for b in BRAS:
    print(f"    {BRAS[b]:<14} murets {moy([e['murs'] for e in G[b]]):>6.0f} · corps "
          f"{moy([e['corps'] for e in G[b]]):>5.0f} · suppression {moy([e['supp'] for e in G[b]]):.3f}"
          f" · coups appui {moy([e['ca'] for e in G[b]]):>6.0f}")

print(f"\n  ETAGE 1 — la suppression est-elle vivante ?")
if not any(verdict.values()):
    print("    NON, PAR AUCUN CHEMIN. Ni mon feu scripte ni le feu natif du moteur ne font")
    print("    tomber la capacite des defenseurs a couvert. Le geste n°2 TOMBE, et aucun")
    print("    terrain ne le sauvera — la mission est tuee a bas prix, seul droit de ce banc.")
else:
    gagne = 2 if verdict.get(2) else 1  # le NATIF prefere a egalite, regle deposee avant
    print(f"    OUI. Implementation retenue pour le professeur du n°2 : {BRAS[gagne].upper()}.")
    if verdict.get(1) and verdict.get(2):
        print("    Les deux passent — le natif l emporte par la regle deposee : moins de code,")
        print("    moins de fautes. Deux cents lignes remplacees par huit.")
    print("    Le banc s ARRETE LA : c est la PORTE 0 du lieu qui rendra le verdict qui compte.")

print("\n  CE QUE CE BANC NE DIT PAS : il mesure une MECANIQUE sur terrain plat, murets")
print("  identiques, defenseurs immobiles au meme endroit. Il ne dit rien du gain d une")
print("  manoeuvre en mission — ni de sa taille.")
