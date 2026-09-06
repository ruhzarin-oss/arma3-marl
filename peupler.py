#!/usr/bin/env python3
"""peupler — POSER UNE SCENE MESURABLE SUR ARMA.

⚠️ CE N EST PAS UN BANC. C est le minimum pour que le pont ait quelque chose a mesurer :
un lieu, deux camps, et la verification que le monde REPOND (les hommes vivent, se voient,
se tirent dessus). On ne mesure aucune doctrine ici — on etablit qu il y a un monde.

Prudence heritee du dossier : le lieu se CHOISIT par `BIS_fnc_findSafePos` puis se VERIFIE
(z, eau, pente), jamais on ne pose des hommes sur une coordonnee ecrite a la main.
"""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

B = NativeBridge(port=5801, timeout=20)
def q(sqf, pat, want=1, t=20):
    r = B.query(sqf, pat, want=want, timeout=t)
    return r
def emit(txt, *a):
    return 'format ["%s"%s] call HMT_EMIT;' % (txt, "".join("," + x for x in a))

print("=" * 88); print(" PEUPLER LA SCENE"); print("=" * 88, flush=True)

print("\n─── 1. NETTOYER (une scene precedente fausserait tout) ───")
q('{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;'
  '{ deleteGroup _x } forEach (allGroups select {count units _x == 0});'
  + emit("HMTCLEAN %1", "count allUnits"), r"HMTCLEAN (\d+)")
print("  unites restantes : %s" % (q(emit("HMTN %1", "count allUnits"), r"HMTN (\d+)")[0].group(1)))

print("\n─── 2. CHOISIR UN LIEU, ET LE VERIFIER ───")
r = q('HMT_POS = [] call BIS_fnc_randomPos; '
      'HMT_POS = [HMT_POS, 0, 800, 12, 0, 0.25, 0] call BIS_fnc_findSafePos; '
      + emit("HMTPOS %1 %2 %3", "HMT_POS select 0", "HMT_POS select 1",
             "getTerrainHeightASL HMT_POS"),
      r"HMTPOS ([-\d.]+) ([-\d.]+) ([-\d.]+)", t=30)
if not r: print("  ⛔ aucun lieu trouve"); sys.exit(1)
x, y, z = (float(g) for g in r[0].groups())
print("  lieu : x=%.0f  y=%.0f  altitude=%.1f m" % (x, y, z))
if z <= 0: print("  ⛔ dans l eau — on ne pose pas d hommes ici"); sys.exit(1)

print("\n─── 3. POSER DEUX CAMPS ───")
# ⚠️ DEUX FAUTES DU PREMIER PASSAGE :
#  · j ecrivais `_i%%4` — reflexe de format Python. La chaine n est PAS formatee, donc Arma
#    recevait litteralement `%%`, erreur de syntaxe, et la boucle mourait en silence.
#  · `sleep` exige un contexte PLANIFIE ; le pont execute en `call compile`. -> `spawn`.
q('HMT_GB = createGroup west; HMT_GO = createGroup east;'
  'for "_i" from 0 to 7 do { HMT_GB createUnit ["B_Soldier_F", HMT_POS vectorAdd [(_i mod 4)*6-9, floor(_i/4)*6, 0], [], 0, "NONE"] };'
  'for "_i" from 0 to 7 do { HMT_GO createUnit ["O_Soldier_F", HMT_POS vectorAdd [(_i mod 4)*6-9, 220 + floor(_i/4)*6, 0], [], 0, "NONE"] };'
  '{ _x setSkill 0.5; _x allowFleeing 0 } forEach allUnits;'
  + emit("HMTPOSE bleu=%1 rouge=%2", "count units HMT_GB", "count units HMT_GO"),
  r"HMTPOSE bleu=(\d+) rouge=(\d+)", t=30)
r = q(emit("HMTV %1 %2", "count allUnits", "{alive _x} count allUnits"), r"HMTV (\d+) (\d+)")
POSES = int(r[0].group(1)) if r else 0
print("  unites posees : %s   vivantes : %s" % (r[0].groups() if r else ("?", "?")))
if POSES == 0:
    print("\n  ⛔ AUCUNE UNITE POSEE — on s arrete. Une scene vide ne se mesure pas,")
    print("     et un banc qui la lirait annoncerait « tout le monde est mort ».")
    B.close(); sys.exit(1)

print("\n─── 4. LE MONDE REPOND-IL ? (on les laisse se voir et s engager) ───")
q('HMT_GB move (getPos leader HMT_GO); HMT_GO move (getPos leader HMT_GB);', r"", want=0, t=10)
for pas in range(6):
    time.sleep(12)
    r = q(emit("HMTETAT t=%1 vivants=%2 connus=%3 tirs=%4",
               str(pas), "{alive _x} count allUnits",
               "{ (side _x == west) && {(east knowsAbout _x) > 0} } count allUnits",
               "{ (currentCommand _x) == \"\"\"FIRE\"\"\" } count allUnits"),
          r"HMTETAT t=(\d+) vivants=(\d+) connus=(\d+) tirs=(\d+)", t=20)
    if r:
        t_, v_, c_, f_ = r[0].groups()
        print("  t=%-2s  vivants %-3s  bleus connus des rouges %-3s  en tir %s" % (t_, v_, c_, f_), flush=True)

r = q(emit("HMTFIN vivants=%1 bleus=%2 rouges=%3", "{alive _x} count allUnits",
           "{alive _x && side _x == west} count allUnits",
           "{alive _x && side _x == east} count allUnits"),
      r"HMTFIN vivants=(\d+) bleus=(\d+) rouges=(\d+)")
if r:
    v, b_, o = (int(g) for g in r[0].groups())
    print("\n  BILAN : %d vivants  (bleus %d, rouges %d) sur 16 poses" % (v, b_, o))
    # ⚠️ LE VERDICT DU PREMIER PASSAGE MENTAIT : il testait `v < 16` et 0 < 16, donc une
    # scene VIDE etait annoncee « le monde combat ». On compare desormais aux POSES.
    morts = POSES - v
    print("  -> %s" % ("LE MONDE COMBAT : %d morts sur %d poses, la scene est mesurable." % (morts, POSES)
                       if morts > 0 else
                       "personne n est mort sur %d poses — ils ne se sont pas trouves." % POSES))
B.close()
