"""
Types de menace SEPARES, a la meme distance que le niveau 3 ( 18/09 ).
Constat : au niveau 1 ou 2, la menace est posee LOIN ( 400-800 m en P1, 300-700 m en P2 ), au niveau 3 elle est POSEE
PRES ( 150-350 m ). La perception ne porte qu a 150-300 m de nuit : separer les types eloignait donc la menace hors de
portee ( variance mesuree 0 a 2 sur 8 ).
Ajout : niveaux 4 ( type 1 seul, PRES ) et 5 ( type 2 seul, PRES ), qui reprennent exactement la bande du niveau 3.
Rien d autre ne change : les niveaux 0 a 3 gardent leur comportement, octet pour octet.
"""
import re, sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B = f"{D}/bancs/chacal"
M = f"{B}/mission.Altis/chacal/35_menaces.sqf"
s = open(M, encoding="utf-8").read()

# 1. la proximite : le niveau 3 et les nouveaux 4 et 5 posent PRES
avant = s
s = s.replace('private _pres = (CHACAL_MENACE_P1 == 3);', 'private _pres = (CHACAL_MENACE_P1 in [3, 4, 5]);')
for k in (2, 3, 4, 6):
    s = s.replace(f'if (CHACAL_MENACE_P{k} == 3) then {{ [', f'if (CHACAL_MENACE_P{k} in [3, 4, 5]) then {{ [')
assert s != avant, "aucune bande de proximite modifiee"

# 2. l appartenance : le type 1 se joue aux niveaux 1, 3 et 4 ; le type 2 aux niveaux 2, 3 et 5
for k in (1, 2, 3, 4, 5, 6):
    s = s.replace(f'if (CHACAL_MENACE_P{k} in [1, 3]) then {{', f'if (CHACAL_MENACE_P{k} in [1, 3, 4]) then {{')
    s = s.replace(f'if (CHACAL_MENACE_P{k} in [2, 3]) then {{', f'if (CHACAL_MENACE_P{k} in [2, 3, 5]) then {{')
assert 'in [1, 3, 4]' in s and 'in [2, 3, 5]' in s
# la sortie PATROUILLE_ABSENTE de la phase 2 lisait le niveau 3 : elle doit lire les niveaux proches aussi
s = s.replace('if (CHACAL_MENACE_P2 == 3) then', 'if (CHACAL_MENACE_P2 in [3, 4, 5]) then')
open(M, "w", encoding="utf-8").write(s)

# 3. les valeurs declarees
E = f"{B}/mission.Altis/description.ext"
t = open(E, encoding="utf-8").read()
n = 0
for k in (1, 2, 3, 4, 5, 6):
    m = re.search(rf'(class CHACAL_MENACE_P{k}\s*\{{.*?values\[\]\s*=\s*)\{{0,1,2,3\}}(;\s*texts\[\]\s*=\s*)\{{"0","1","2","3"\}}', t, re.S)
    if m:
        t = t[:m.start()] + m.group(1) + '{0,1,2,3,4,5}' + m.group(2) + '{"0","1","2","3","4","5"}' + t[m.end():]
        n += 1
assert n >= 5, f"seulement {n} classes de menace mises a jour"
t = t.replace("3 les deux plus pres", "3 les deux plus pres, 4 type 1 seul mais pres, 5 type 2 seul mais pres")
open(E, "w", encoding="utf-8").write(t)
print(f"patch types proches applique ( {n} classes )")

# ---------------------------------------------------------------- banc : refuser l episode sans ligne de vue ( 18/09 )
P = f"{B}/mission.Altis/chacal/60_phases.sqf"
u = open(P, encoding="utf-8").read()
ancre = """        private _p = _chef getPos [CHACAL_CONTROLE_DIST, _az];
        private _g = createGroup east;"""
assert u.count(ancre) == 1, f"ancre banc trouvee {u.count(ancre)} fois"
nouveau = """        if (!_trouve) exitWith {
            // ! AUCUNE LIGNE DE VUE ( mesure du 18/09 : 4 episodes sur 22 posaient la cible derriere un obstacle ) :
            // on refuse l episode plutot que de mesurer le relief au lieu de la perception.
            (format ["CHACAL|E|banc_refuse|%1|phase|%2|distance|%3|cause|AUCUNE_LIGNE_DE_VUE", round (time * 100) / 100,
                _phase, CHACAL_CONTROLE_DIST]) call CHACAL_LOG;
        };
        private _p = _chef getPos [CHACAL_CONTROLE_DIST, _az];
        private _g = createGroup east;"""
open(P, "w", encoding="utf-8").write(u.replace(ancre, nouveau))
print("banc : episode refuse si aucune ligne de vue")
