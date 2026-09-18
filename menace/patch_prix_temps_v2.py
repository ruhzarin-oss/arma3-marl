"""
PRIX DU TEMPS, version 2 ( 18/09, apres lecture des causes de la campagne PRIX-DU-TEMPS-18-09 ).

La version 1 mesurait sa propre derive. Faire attendre un detachement sans lui donner d ordre laisse l IA reprendre
son mouvement precedent : mesure homme par homme, six a sept hommes marchent 818 m pendant l attente, puis reviennent.
A 600 s l assaut se retrouve a 330-670 m de sa position et la mission renonce ( ARTICULATION_ROMPUE ) dans 14 episodes
sur 16, contre 0 sur 16 a 0 s et 2 sur 16 a 1200 s - alarme 0, compromis 0, 10 vivants sur 10 : l ennemi n y est pour
rien. Le trou a 600 s etait l instrument, pas le monde.

v2 : le detachement est FIGE pendant l attente ( doStop + PATH coupe ), rendu a lui-meme juste apres ( PATH + doFollow ),
et la derive maximale est journalisee pour que la mesure sache echouer. L appui deja fixe par CHACAL_APPUI_FIXE n est
pas touche : le degeler aurait change la mission dans les seuls bras qui attendent.
"""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B = f"{D}/bancs/chacal"


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:70]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


remplacer(f"{B}/mission.Altis/chacal/60_phases.sqf",
 '''if (CHACAL_ATTENTE_TEST > 0) then {
    private _tA = time;
    (format ["CHACAL|E|attente_test|%1|debut|duree_prevue|%2|vivants|%3|alarme|%4", round (time * 100) / 100,
        CHACAL_ATTENTE_TEST, count (CHACAL_FS select { alive _x }), (if (CHACAL_ALARME) then {1} else {0})]) call CHACAL_LOG;
    waitUntil { sleep 2; CHACAL_FIN || ((time - _tA) >= (CHACAL_ATTENTE_TEST * CHACAL_ECHELLE)) };
    (format ["CHACAL|E|attente_test|%1|fin|duree|%2|vivants|%3|alarme|%4|compromis|%5", round (time * 100) / 100,
        round (time - _tA), count (CHACAL_FS select { alive _x }), (if (CHACAL_ALARME) then {1} else {0}),
        (if (CHACAL_COMPROMIS) then {1} else {0})]) call CHACAL_LOG;
};''',
 '''if (CHACAL_ATTENTE_TEST > 0) then {
    private _tA = time;
    // ! V2 - ON FIGE PENDANT L ATTENTE. La v1 laissait les hommes sans ordre : ils reprenaient leur mouvement
    // precedent, marchaient 818 m, puis revenaient. A 600 s l assaut etait a 330-670 m de sa place et la mission
    // renoncait ( ARTICULATION_ROMPUE ) 14 fois sur 16, alarme 0 et 10 vivants sur 10. Une attente doit couter le
    // temps du monde qui tourne, pas la dislocation du detachement.
    // L appui deja fige par CHACAL_APPUI_FIXE n est pas touche : lui rendre PATH le ferait partir, et seulement
    // dans les bras qui attendent.
    private _fige = (CHACAL_FS select { alive _x }) select { !(CHACAL_APPUI_FIXE == 1 && { group _x == CHACAL_gAppui }) };
    private _avant = _fige apply { [_x, getPosATL _x] };
    { doStop _x; _x disableAI "PATH" } forEach _fige;
    (format ["CHACAL|E|attente_test|%1|debut|duree_prevue|%2|vivants|%3|alarme|%4|figes|%5", round (time * 100) / 100,
        CHACAL_ATTENTE_TEST, count (CHACAL_FS select { alive _x }), (if (CHACAL_ALARME) then {1} else {0}),
        count _fige]) call CHACAL_LOG;
    waitUntil { sleep 2; CHACAL_FIN || ((time - _tA) >= (CHACAL_ATTENTE_TEST * CHACAL_ECHELLE)) };
    private _derive = 0;
    { _x params ["_u", "_p"]; if (alive _u) then { _derive = _derive max (_u distance2D _p) } } forEach _avant;
    { if (alive _x) then { _x enableAI "PATH"; _x doFollow (leader (group _x)) } } forEach _fige;
    (format ["CHACAL|E|attente_test|%1|fin|duree|%2|vivants|%3|alarme|%4|compromis|%5|derive|%6", round (time * 100) / 100,
        round (time - _tA), count (CHACAL_FS select { alive _x }), (if (CHACAL_ALARME) then {1} else {0}),
        (if (CHACAL_COMPROMIS) then {1} else {0}), round _derive]) call CHACAL_LOG;
};''')
print("patch prix du temps v2 applique : le detachement est fige pendant l attente")
