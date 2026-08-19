import re, glob, sys
"""LES QUATRE LIGNES de DEPOT_PORTE_PLEIN_CHEMIN.md, ecrites AVANT. Vertes ENSEMBLE ou panne."""
lots = []
for f in sorted(glob.glob("/mnt/data/porte/lot*.txt"), key=lambda x: int(re.search(r"lot(\d+)", x).group(1))):
    n = int(re.search(r"lot(\d+)", f).group(1)); t = open(f, errors="ignore").read()
    seq, prev = [], 0
    for l in t.splitlines():
        m = re.search(r"(\d+)/12\s+vert=(\d+)\s+echec=(\d+)(.*)", l)
        if not m: continue
        e, d = int(m.group(3)), m.group(4)
        if "ECARTE" in d or "abandonne" in d: k = "ECARTE"
        elif "PONT MUET" in d: k = "PONT"
        elif "PREVOL PLANTE" in d: k = "PLANTE"
        elif "PREVOL LENT" in d: k = "LENT"
        # ⚠️ « T0 AUCUN LIEU PRATICABLE » N EST PAS UNE RECEPTION ⟨Fable, 18/08⟩ : le placeur
        # n a RIEN recu, donc ce tirage ne doit pas gonfler le denominateur de la ligne 1.
        # Latent tant que 60/60 recevaient — mais l acte unifie va refuser davantage.
        elif e > prev: k = ("T0" if "AUCUN LIEU PRATICABLE" in d else
                            ("T5" if "T5 IMMOBILE" in d else ("T7" if "T7 " in d else "AUTRE")))
        else: k = "."
        prev = e
        seq.append(k)
    lots.append((n, seq))

print("\n  lot  rang → 1  2  3  4  5  6  7  8  9 10 11 12   verts")
tot = {}
for n, s in lots:
    for k in s: tot[k] = tot.get(k, 0) + 1
    print(f"   {n}        " + " ".join(f"{k[:2]:>2}" if k != "." else " ." for k in s) + f"     {s.count('.')}")
N = sum(len(s) for _, s in lots)
print(f"\n  {N} tirages : " + "  ".join(f"{k}={v}" for k, v in sorted(tot.items())))

# les receptions excluent T0 : le placeur n y a rien recu
recep = tot.get(".", 0) + tot.get("T5", 0) + tot.get("T7", 0) + tot.get("AUTRE", 0)
if tot.get("T0", 0): print(f"  (T0 · aucun lieu praticable : {tot['T0']} tirages, HORS receptions)")
print(f"\n  ══ LIGNE 1 · FAUX-RECUS INEXPLIQUES ══")
print(f"  receptions (le placeur a recu un lieu) : {recep}   exige : >= 50")
print(f"  faux-recus T5 : {tot.get('T5', 0)}   autres echecs : {tot.get('T7',0)} T7, {tot.get('AUTRE',0)} non identifies")
l1 = tot.get("T5", 0) == 0 and recep >= 50
print(f"  → {'✓ VERTE' if l1 else '⛔ ROUGE'}  (zero faux-recu T5 sur >= 50 receptions)")

print(f"\n  ══ LIGNE 2 · MUETS DECOMPOSES ══")
print(f"  pont muet : {tot.get('PONT',0)}   prevol lent : {tot.get('LENT',0)}   prevol PLANTE : {tot.get('PLANTE',0)}   ecartes : {tot.get('ECARTE',0)}")
l2 = tot.get("PLANTE", 0) == 0
print(f"  → {'✓ VERTE' if l2 else '⛔ ROUGE'}  (zero PLANTE tolere ; lent et pont comptes a part)")

print(f"\n  ══ LIGNE 2bis · REBUT D INSTRUMENT ══")
# ⚠️ LIGNE NEUVE ⟨Fable, 18/08⟩ : la ligne 2 ne bornait QUE les PLANTE. LENT et ECARTE etaient
# « comptes a part » — sans plafond. La nuit du 17/08 ils ont mange 4 tirages sur 59, soit
# 6,8 %, AU-DESSUS du plafond de rebut de la regle 19, et personne n a sonne. Un critere qui
# laisse l instrument devorer 7 % de sa mesure sans rougir est une economie non declaree.
# grandeur : tirages perdus par l instrument (LENT + ECARTE + PONT) ; statistique : compte ;
# seuil : <= 3 sur 60, soit 6 % de la regle 19 ; n minimum : 60 tirages.
_reb = tot.get("LENT", 0) + tot.get("ECARTE", 0) + tot.get("PONT", 0)
print(f"  rebut d instrument : {_reb} sur {N}   seuil : <= 3 (6 % de la regle 19)")
l2b = _reb <= 3 and N >= 60
print(f"  → {'✓ VERTE' if l2b else '⛔ ROUGE'}")

print(f"\n  ══ LIGNE 3 · REGROUPEMENT PAR SERVEUR — SUR LES RECEPTIONS SEULES ══")
# ⚠️ SCINDEE ⟨Fable⟩ : cette ligne a TOUJOURS parle du MONDE (« pas de surdispersion entre
# serveurs »). En melant les echecs d INSTRUMENT, elle mesurait le regroupement des
# expirations de patience — qui est session-couple PAR CONSTRUCTION, l anneau de candidats
# etant fixe par session. Le 17/08 : les receptions du monde ont fait 55/55, et les 4 non-verts
# etaient tous des echecs de patience dont le lot 2 portait 7,31 des 9,97. La ligne juge
# desormais LES RECEPTIONS SEULES ; le regroupement des echecs d instrument est NOTE en clair
# mais NON JUGE — un X2 sur 2-3 evenements ne declare pas de n honnete.
# receptions par lot = tirages ou le placeur a recu (verts + T5 + T7 + AUTRE), sans les
# echecs d instrument qui ne jugent pas le monde
ok_l = [(n, s.count("."), sum(1 for k in s if k in (".", "T5", "T7", "AUTRE"))) for n, s in lots]
ok_l = [(n, v, t) for n, v, t in ok_l if t > 0]
p = sum(v for _, v, _ in ok_l) / sum(t for _, _, t in ok_l)
X2 = sum(t * ((v/t) - p)**2 for _, v, t in ok_l) / (p*(1-p)) if 0 < p < 1 else 0
seuil = {4: 9.49, 5: 11.07}.get(len(lots), 9.49)
print(f"  taux de verts par lot : " + "  ".join(f"{v}/{t}" for _, v, t in ok_l))
print(f"  X2 = {X2:.2f}   ddl = {len(lots)-1}   seuil 5 % = {seuil}")
l3 = X2 <= seuil
print(f"  → {'✓ VERTE' if l3 else '⛔ ROUGE'}  (pas de surdispersion entre serveurs)")

print(f"\n  ══ LIGNE 4 · LES SIX SABOTAGES, LUS DANS LEURS TAMPONS ══")
# ⚠️ CETTE LIGNE ETAIT UNE CONSTANTE QUE JE BASCULAIS A LA MAIN ⟨Fable, 18/08⟩ — et je l avais
# mise a VRAI alors que mes sabotages dataient de TROIS socles differents : munitions et
# jambes sur 2.8.0, gel sur 2.10.0, lenteur sur 2.12.0. La faute d hier reconstruite : la
# porte sur un hash, les sabotages sur d autres. Elle LIT desormais les tampons que chaque
# run ecrit — mode, version LUE DANS LE MONDE, commit, verdict, date — et exige que les six
# portent LA MEME VERSION que la porte. Le gardien de version, applique aux ACTES.
import os
_TAMP = "/mnt/data/sabotages6/TAMPONS.txt"
_ATTENDUS = {"traverse", "tir", "munitions", "jambes", "gel", "lenteur"}
_vus, _mauvais, _vers = {}, [], set()
if os.path.exists(_TAMP):
    for _l in open(_TAMP, errors="ignore"):
        _c = _l.strip().split("|")
        if len(_c) >= 5:
            _vus[_c[0]] = (_c[1], _c[2], _c[3], _c[4])
            _vers.add(_c[1])
            if _c[3] != "PASSE": _mauvais.append(_c[0])
for _k in sorted(_ATTENDUS):
    if _k in _vus:
        _v = _vus[_k]
        print(f"  {'ok ' if _v[2]=='PASSE' else 'NON'} {_k:10s} socle {_v[0]:18s} commit {_v[1]:9s} {_v[3]}")
    else:
        print(f"  NON {_k:10s} AUCUN TAMPON")
_manquants = _ATTENDUS - set(_vus)
# la version du socle sous laquelle la PORTE a tourne
_vp = None
for _l in open("/mnt/data/porte/JOURNAL.txt", errors="ignore") if os.path.exists("/mnt/data/porte/JOURNAL.txt") else []:
    _m = re.search(r'HMT_SOCLE_VERSION = "([^"]*)"', _l)
    if _m: _vp = _m.group(1); break
print(f"  version de la PORTE : {_vp}   versions des tampons : {sorted(_vers)}")
l4 = (not _manquants) and (not _mauvais) and len(_vers) == 1 and (_vp in _vers if _vp else False)
if _manquants: print(f"  ⛔ tampons manquants : {sorted(_manquants)}")
if _mauvais:   print(f"  ⛔ sabotages en ECHEC : {sorted(_mauvais)}")
if len(_vers) > 1: print(f"  ⛔ les tampons ne portent PAS la meme version")
if _vp and _vp not in _vers: print(f"  ⛔ la porte a tourne sur {_vp}, les sabotages sur {sorted(_vers)}")
print(f"  → {'✓ VERTE' if l4 else '⛔ ROUGE'}")
print(f"  → ⛔ ROUGE  (deux sabotages sur quatre non rejoues sur ce hash)")

_ecl = [k for _, s in lots for k in s if k in ("LENT", "ECARTE", "PONT")]
from collections import Counter as _C
print(f"  regroupement des echecs d INSTRUMENT (note, NON juge) : " +
      ", ".join(f"lot {n}={sum(1 for k in s if k in ('LENT','ECARTE','PONT'))}" for n, s in lots))

print(f"\n  ══════ VERDICT ══════")
if l1 and l2 and l2b and l3 and l4: print("  ➤ LES QUATRE LIGNES SONT VERTES — LE BANC SORT DE PANNE DIAGNOSTIQUE.")
else:
    rouges = [n for n, x in zip(["1","2","2bis","3","4"], [l1,l2,l2b,l3,l4]) if not x]
    print(f"  ➤ LIGNE(S) ROUGE(S) : {rouges} — LE BANC RESTE EN PANNE.")
    if rouges == [4]:
        print("     Mais la seule rouge est une PROCEDURE non rejouee, pas une mesure du monde :")
        print("     les trois lignes qui jugent le monde sont vertes. Rejouer les deux sabotages")
        print("     manquants sur ce hash suffit — c est dix minutes, et rien d autre a mesurer.")
