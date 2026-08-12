#!/usr/bin/env python3
"""patch_bond.py — GESTE N°1 : LE BOND PAR BINOME. Le professeur, et son temoin.

⟨cahier du repertoire, 07/08⟩ Un geste porte trois choses : le FAIT CERTIFIE qu il exploite,
le PROFESSEUR scripte, et sa PORTE. Et le premier filtre est GRATUIT : un geste dont le
professeur ne bat pas son temoin ne s enseigne pas.

LE FAIT CERTIFIE : le bounding overwatch perce a 96 % / 91 % face a 12 gardes.
LE PROFESSEUR   : deux equipes sur le MEME axe, qui alternent. L une bondit de 40 m vers
                  l objectif pendant que l autre s arrete, tient et tire. Puis elles echangent.
LE TEMOIN       : le comportement actuel — tout le monde avance en meme temps, un seul ordre.
EFFECTIF IDENTIQUE des deux cotes : sinon on mesure le nombre d hommes, pas le geste.

CE QUI EST MESURE : la TENUE, la meme grandeur que l A/B et la porte A2. Rien d autre ne
change — meme monde, meme charge, meme rapport de force, memes journaux, meme juge.

PORTE, deposee avant : le bond doit battre le simultane d au moins 5 POINTS de tenue — le
tiers du plus petit effet certifie du dossier. En dessous, le geste ne s enseigne pas.

⚠️ AVANT DE LIRE LE MOINDRE BRAS : la PORTE 0 du banc doit tenir — les deux doctrines doivent
atterrir dans la bande 20-80 % d arrivee, au point de fonctionnement du jugement.
"""
import pathlib

M = pathlib.Path('/mnt/data/harmattan-sandbox/arma3server/mpmissions/BancArma.Stratis')
G = M / 'generateur_engagements_v12.sqf'
t = G.read_text(encoding='utf-8')

# ---------------------------------------------------------------- 1. le tirage des bras
ANC = """                    private _d = random 1;
                    if (missionNamespace getVariable ["HMT_A2PUR", false]) then {"""
NEUF = """                    private _d = random 1;
                    if (missionNamespace getVariable ["HMT_BOND", false]) then {
                        // GESTE N°1 : le professeur (bond alterne) contre son temoin
                        // (progression simultanee). UN SEUL axe des deux cotes, effectif
                        // identique : on mesure le GESTE, pas le nombre d hommes ni l angle.
                        _nAxes = 1; _fige = false;
                        HMT_BOND_CE = (_d < 0.5);
                    } else {
                    if (missionNamespace getVariable ["HMT_A2PUR", false]) then {"""
assert t.count(ANC) == 1, "ancre du tirage"
t = t.replace(ANC, NEUF, 1)

A2 = """                    else { _nAxes = (if (_d < 0.9) then {1} else {2}); _fige = true } };
                    };
                };"""
N2 = """                    else { _nAxes = (if (_d < 0.9) then {1} else {2}); _fige = true } };
                    };
                    };
                };"""
assert t.count(A2) == 1, "ancre de fermeture du tirage"
t = t.replace(A2, N2, 1)

# ---------------------------------------------------------------- 2. le professeur
A3 = """                        _g move _pt;
                        _gs pushBack _g;"""
N3 = """                        if (missionNamespace getVariable ["HMT_BOND", false]
                            && {HMT_BOND_CE}) then {
                            // LE PROFESSEUR. On coupe le groupe en deux equipes et on les fait
                            // alterner : l une bondit de 40 m vers l objectif, l autre s arrete,
                            // tient et tire. Puis elles echangent. C est le bond par binome.
                            private _u = units _g;
                            private _gB = createGroup _cAtt;
                            for "_k" from 0 to ((count _u) - 1) do {
                                if (_k % 2 == 1) then { [_u select _k] joinSilent _gB };
                            };
                            _gs pushBack _gB;
                            [_g, _gB, _pt, _n] spawn {
                                params ["_a", "_b", "_pt", "_id"];
                                private _tour = 0;
                                private _t0 = time;
                                while { time - _t0 < 900
                                        && {({alive _x} count (units _a)) + ({alive _x} count (units _b)) > 0} } do {
                                    private _mob = if (_tour % 2 == 0) then { _a } else { _b };
                                    private _fix = if (_tour % 2 == 0) then { _b } else { _a };
                                    // celui qui tient s arrete et appuie
                                    { doStop _x; _x setUnitPos "MIDDLE" } forEach (units _fix);
                                    // celui qui bondit avance de 40 m vers l objectif
                                    private _p0 = getPosATL (leader _mob);
                                    private _dd = (_p0 distance2D _pt) max 1;
                                    private _f = ((_dd - 40) max 0) / _dd;
                                    { _x setUnitPos "AUTO" } forEach (units _mob);
                                    _mob move [(_pt select 0) + ((_p0 select 0) - (_pt select 0)) * _f,
                                               (_pt select 1) + ((_p0 select 1) - (_pt select 1)) * _f, 0];
                                    (format ["HMT|G|BOND|%1|%2|%3|%4", _id,
                                             (round (time*100))/100, _tour,
                                             round _dd]) call HMT_LOG;
                                    sleep 12;
                                    _tour = _tour + 1;
                                };
                            };
                        } else {
                            _g move _pt;
                        };
                        _gs pushBack _g;"""
assert t.count(A3) == 1, "ancre du mouvement"
t = t.replace(A3, N3, 1)

G.write_text(t, encoding='utf-8')

# ---------------------------------------------------------------- 3. l init
I = M / 'init.sqf'
s = I.read_text(encoding='utf-8')
c = "    HMT_A2PUR = true;"
d = ("    HMT_A2PUR = false;\n"
     "    // GESTE N°1 — le bond par binome contre la progression simultanee.\n"
     "    // Criteres : CAHIER_REPERTOIRE_GESTES.md. Porte : 5 points de tenue.\n"
     "    HMT_BOND = true;\n"
     "    HMT_BOND_CE = false;")
assert s.count(c) == 1, "ancre de l init"
I.write_text(s.replace(c, d, 1), encoding='utf-8')
print("geste n°1 pose : professeur (bond alterne) contre temoin (simultane)")
