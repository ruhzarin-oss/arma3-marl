#!/usr/bin/env python3
"""patch_vise.py — LE TEMOIN DE TIR, TROISIEME PROGRAMMATION. Il part, ou il se signe annule.

Le journal `TIR` existant est emis sur l evenement `Fired` : une ligne n existe que si le
defenseur TIRE. Dans 26 % des accrochages, aucun defenseur n a tire sur un assaillant, et ces
accrochages sortent muets. On ne peut donc pas distinguer « il sait et ne peut pas tirer » de
« personne n a tire ».

CE QU ON AJOUTE : `HMT|G|VISE`, l echantillonnage de `assignedTarget` toutes les 2 s pour
chaque defenseur vivant, INDEPENDAMMENT du tir. C est l intention, prise au fil du temps et
non au moment de la detente.

  HMT|G|VISE|<accrochage>|<temps>|<defenseur>|<cible ou -1>

Le reste du generateur ne bouge pas : meme monde, memes bras, meme journal de sante.
"""
import pathlib

M = pathlib.Path('/mnt/data/harmattan-sandbox/arma3server/mpmissions/BancArma.Stratis')
G = M / 'generateur_engagements_v12.sqf'
t = G.read_text(encoding='utf-8')

ANC = "HMT_POINT = {"
NEUF = '''// ---- LE TEMOIN D INTENTION, echantillonne toutes les 2 s ----
// `TIR` est emis sur Fired : il ne dit rien des accrochages ou personne ne tire, qui sont
// justement ceux ou le sursis a joue a fond. Ici on releve `assignedTarget` au fil du temps,
// que le defenseur tire ou non. Criteres : CRITERES_TEMOIN_VISE.md, deposes avant lancement.
[] spawn {
    while { true } do {
        {
            _x params ["_unites", "", "", "", "_id"];
            {
                if (alive _x && {(_x getVariable ["hmt_axe", -1]) == -1}) then {
                    private _c = assignedTarget _x;
                    (format ["HMT|G|VISE|%1|%2|%3|%4", _id, (round (time*100))/100,
                             _x getVariable ["hmt_id", -1],
                             (if (isNull _c) then {-1} else {_c getVariable ["hmt_id", -1]})
                            ]) call HMT_LOG;
                };
            } forEach _unites;
        } forEach HMT_ACC;
        sleep 2;
    };
};

HMT_POINT = {'''
assert t.count(ANC) == 1, "ancre HMT_POINT introuvable"
t = t.replace(ANC, NEUF, 1)
G.write_text(t, encoding='utf-8')
print("journal VISE pose — echantillonnage 2 s, independant du tir")
