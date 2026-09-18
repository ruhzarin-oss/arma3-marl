"""
Banc de perception : si AUCUN azimut n offre de ligne de vue, on ne pose plus la cible et on ecrit une ligne
CHACAL|E|banc_refuse. Mesure du 18/09 : 4 episodes sur 22 posaient la cible derriere un obstacle ( ligne_de_vue = 0 )
et mesuraient donc le relief, pas la perception.
"""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
P = f"{D}/bancs/chacal/mission.Altis/chacal/60_phases.sqf"
s = open(P, encoding="utf-8").read()
ancre = '''        private _p = _chef getPos [CHACAL_CONTROLE_DIST, _az];
        private _g = createGroup east;'''
assert s.count(ancre) == 1, f"ancre trouvee {s.count(ancre)} fois"
nouveau = '''        if (!_trouve) exitWith {
            // ! AUCUNE LIGNE DE VUE ( mesure du 18/09 ) : poser la cible derriere un obstacle mesurerait le relief,
            // pas la perception. On refuse l episode plutot que de le polluer.
            (format ["CHACAL|E|banc_refuse|%1|phase|%2|distance|%3|cause|AUCUNE_LIGNE_DE_VUE", round (time * 100) / 100,
                _phase, CHACAL_CONTROLE_DIST]) call CHACAL_LOG;
        };
        private _p = _chef getPos [CHACAL_CONTROLE_DIST, _az];
        private _g = createGroup east;'''
open(P, "w", encoding="utf-8").write(s.replace(ancre, nouveau))
print("patch banc_refuse applique")
