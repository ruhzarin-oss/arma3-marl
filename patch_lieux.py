#!/usr/bin/env python3
"""patch_lieux.py — BRANCHER LE GENERATEUR SUR LES COULOIRS QUI FORCENT LE BOND.

Jusqu ici le generateur tirait un point AU HASARD sur Stratis. Rien ne garantissait que ce
terrain EXIGE le geste : sans masques espaces ni ligne de vue longue, alterner ne s achete
rien et les deux bras se confondent. ⟨fiche du 22/06 : « une perception ne paie QUE si la
mission la FORCE » — 5 graines a 78, 0, 0, 0, 0⟩

CE QU ON POSE : huit couloirs choisis sur la carte du bati relevee le 07/08 — objectif dans
du bati dense, approche de 250 m, trois masques et deux zones ouvertes, quatre alternances.
Ni tunnel (tout couvert : tous les chemins se valent) ni desert (rien : le detour est de la
pure sur-exposition).

L OBJECTIF ET L AZIMUT D APPROCHE SONT IMPOSES. Le reste ne bouge pas : meme charge, meme
rapport de force, memes journaux, meme juge, meme filtre de sante.

CE N EST PAS ENCORE UN VERDICT : c est la PORTE 0 DES LIEUX. Chaque couloir doit montrer que
le bond scripte y bat la progression simultanee. Un couloir qui ne separe pas est RECALE — le
geste, lui, n est pas juge.

ET LE CONTROLE NEGATIF EXISTE DEJA : les 25 accrochages sur points quelconques, archives dans
temoin_negatif_lieu_quelconque.out. Si les couloirs separent et que le hasard ne separe pas,
le forcage est PROUVE, pas suppose.
"""
import pathlib
import numpy as np

z = np.load('/home/younes/arma3-marl/lieux_bond.npz')
obj, az = z['obj'], z['az']
lieux = ",".join("[%d,%d,%d]" % (o[0], o[1], a) for o, a in zip(obj, az))
print(f"{len(obj)} couloirs a poser")

M = pathlib.Path('/mnt/data/harmattan-sandbox/arma3server/mpmissions/BancArma.Stratis')
G = M / 'generateur_engagements_v12.sqf'
t = G.read_text(encoding='utf-8')

ANC = "HMT_POINT = {"
NEUF = ("""// ---- LES COULOIRS QUI FORCENT LE BOND, choisis sur la carte du bati du 07/08 ----
// [x, y, azimut d approche] — l objectif est dans du bati dense, l approche fait 250 m et
// alterne masques et zones ouvertes. Aucun n a encore d opinion : chacun doit passer sa
// PORTE 0 avant de juger un agent.
HMT_LIEUX = [""" + lieux + """];

HMT_POINT = {""")
assert t.count(ANC) == 1, "ancre HMT_POINT"
t = t.replace(ANC, NEUF, 1)

# le point d accrochage : on impose le couloir au lieu de tirer au hasard
A2 = """                    private _c = call HMT_POINT;
            if (count _c > 0) then {
                _c params ["_pt", "_bats"];"""
if A2 not in t:
    A2 = """            private _c = call HMT_POINT;
            if (count _c > 0) then {
                _c params ["_pt", "_bats"];"""
N2 = A2 + """
                // COULOIR IMPOSE : on remplace le point tire au hasard par un couloir
                // certifie-en-attente, et l azimut d approche par le sien.
                if (missionNamespace getVariable ["HMT_BOND", false]) then {
                    private _L = HMT_LIEUX select (floor (random (count HMT_LIEUX)));
                    _pt = [_L select 0, _L select 1, 0];
                    HMT_AZ_IMPOSE = _L select 2;
                    HMT_LIEU_ID = HMT_LIEUX find _L;
                };"""
assert t.count(A2) == 1, "ancre du point d accrochage"
t = t.replace(A2, N2, 1)

# l azimut d approche
A3 = "private _az1 = "
i = t.index(A3)
fin = t.index(";", i) + 1
avant = t[i:fin]
apres = (avant + """
                if (missionNamespace getVariable ["HMT_BOND", false]) then {
                    _az1 = HMT_AZ_IMPOSE;   // l approche du couloir, pas un tirage
                };""")
t = t[:i] + apres + t[fin:]

# journaliser le lieu, pour pouvoir juger couloir par couloir
A4 = """                             (if (_fige) then {1} else {0})]) call HMT_LOG;"""
N4 = A4 + """
                    (format ["HMT|G|LIEU|%1|%2|%3", _n,
                             (missionNamespace getVariable ["HMT_LIEU_ID", -1]),
                             (if (missionNamespace getVariable ["HMT_BOND_CE", false])
                              then {1} else {0})]) call HMT_LOG;"""
assert t.count(A4) == 1, "ancre du journal debut"
t = t.replace(A4, N4, 1)

G.write_text(t, encoding='utf-8')
print("generateur branche sur les couloirs ; journal LIEU pose")
