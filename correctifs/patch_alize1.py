#!/usr/bin/env python3
# Banc ALIZE 1 (HMT-39) : la copie de mission enregistre, homme par homme, « on me touche » et
# « une balle me frole ». Ne touche QUE bancs/alize1 ; la mission CHACAL de la campagne n est pas lue.
import sys
M = "/mnt/data/hmt/depot/bancs/alize1/mission.Altis/chacal/50_capture.sqf"
s = open(M, encoding="utf-8", errors="surrogateescape").read()
if "coup_recu" in s: print("  deja present"); sys.exit(0)
avant = '''    CHACAL_NEXT_ID = CHACAL_NEXT_ID + 1;
    CHACAL_NEXT_ID - 1
};'''
apres = '''    // ! BANC ALIZE 1 ( HMT-39, 11/09 ) : les deux signaux qu attend l alarme locale de SIROCCO,
    // homme par homme, pour notre camp seulement. IMPACT = on me touche ( Hit ) ; FROLEMENT = un
    // ennemi tire pres de moi ( FiredNear, porte mesuree ~60 m, un evenement par voisin ).
    if ((side _u) == west) then {
        _u addEventHandler ["Hit", {
            params ["_unit", "_source", "_damage", "_instigator"];
            private _src = if (!isNull _instigator) then {_instigator} else {_source};
            (format ["CHACAL|E|coup_recu|%1|%2|%3|%4|%5|%6|%7", round (time * 100) / 100,
                (_unit getVariable ["chacal_id", -1]),
                (if (isNull _src) then {-1} else {_src getVariable ["chacal_id", -1]}),
                round (_damage * 1000) / 1000, round ((damage _unit) * 1000) / 1000,
                (if (isNull _src) then {-1} else {round (_unit distance _src)}),
                (if (isNull _src) then {[]} else {(getPosATL _src) apply {round _x}})]) call CHACAL_LOG;
        }];
        _u addEventHandler ["FiredNear", {
            params ["_unit", "_firer", "_distance"];
            if ((side (group _firer)) == west) exitWith {};
            (format ["CHACAL|E|frole|%1|%2|%3|%4|%5", round (time * 100) / 100,
                (_unit getVariable ["chacal_id", -1]), (_firer getVariable ["chacal_id", -1]),
                round _distance, (getPosATL _firer) apply {round _x}]) call CHACAL_LOG;
        }];
    };
    CHACAL_NEXT_ID = CHACAL_NEXT_ID + 1;
    CHACAL_NEXT_ID - 1
};'''
if s.count(avant) != 1: print("  !! motif x%d" % s.count(avant)); sys.exit(1)
b = lambda t: (t.count("{") - t.count("}"), t.count("[") - t.count("]"), t.count("(") - t.count(")"))
s2 = s.replace(avant, apres, 1)
if b(s) != b(s2): print("  !! equilibre", b(s), b(s2)); sys.exit(1)
open(M, "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  PATCHE : 50_capture.sqf de la copie alize1 (coup_recu + frole)")
