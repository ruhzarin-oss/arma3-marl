"""chacalmulti - construit la mission de l'episode multiple a partir du banc chacaloracle, SANS le modifier.

Principe ( 22/09, apres l'avis de Fable ) : une cellule = une copie COMPLETE du code de la mission, dont toutes les
globales `CHACAL_*` sont renommees `MC<k>_*`. Chaque cellule a donc son propre etat, son propre generateur, son propre
Oracle et son propre enregistreur ; la logique de la phase 2 est celle du banc seul, ligne pour ligne. Seuls les
points ou le code touche le MOTEUR en entier ( allUnits, vehicles, gestionnaires d'evenements de mission, createGroup,
parametres ) sont retouches, et chaque retouche est ecrite ici, comptee, et refusee si elle ne s'applique pas
exactement une fois.

Le journal de la cellule k porte le prefixe `M|k|` : le lecteur le demultiplexe et rend a chaque cellule un journal
identique a celui d'un episode seul, que lit le lecteur du banc seul ( bancs/chacal/lire.py ), portes comprises.

Usage : construire_mission.py <mission source> <mission cible> [KMAX]
"""
import os, re, shutil, sys

SRC, DST = sys.argv[1], sys.argv[2]
KMAX = int(sys.argv[3]) if len(sys.argv) > 3 else 8
ORDRE = ["00_socle", "10_monde", "20_decor", "30_opfor", "35_menaces", "40_blufor", "45_oracle",
         "46_controles_oracle", "50_capture", "70_verdict", "60_phases"]
# Parametres que chaque cellule peut surcharger ; tous les autres sont communs a l'episode ( ceux du banc seul ).
PAR_CELLULE = ["GRAINE", "GRAINE_HAUT", "SITUATION", "MENACE_P2", "TRAVERSEE", "PALIER", "EFFECTIF", "AVANT",
               "OBSERVATION", "QRF_N", "QRF_DELAI", "HMG", "PORTEE_SON", "BALAYAGE", "ORACLE_CMD", "ORACLE_CTRL", "ORACLE_B",
               "ORACLE_NU", "ORACLE_EPS", "ORACLE_DELTA", "SITE_X", "SITE_Y"]
SENTINELLE = -999999


def remplacer(texte, ancien, nouveau, attendu, nom):
    n = texte.count(ancien)
    if n != attendu:
        raise SystemExit(f"RETOUCHE REFUSEE {nom} : '{ancien[:70]}' trouve {n} fois, {attendu} attendu(s)")
    return texte.replace(ancien, nouveau)


def cellule(k, fichier, t):
    """Renomme puis retouche. Les retouches sont ecrites APRES le renommage ( MC<k>_ )."""
    t = t.replace("CHACAL_", f"MC{k}_")
    p = f"MC{k}_"
    if fichier == "00_socle":
        # ! UNE CELLULE FINIE SE TAIT ( fumee v2, 22/09 ) : dans le banc seul, le serveur est arrete sur la ligne FINI ;
        # ici il tourne pour les autres cellules, et le canari d'un positif fini ecrivait encore - porte « rien apres FINI »
        # en echec. Apres FINI, seules passent les lignes OK et AVERT, celles que le lecteur du banc seul tolere.
        t = remplacer(t, f"{p}LOG = {{ diag_log _this }};",
                      f'{p}MUET = false;\n{p}LOG = {{ if (!{p}MUET || {{ (_this find "CHACAL|OK|") == 0 }} || {{ (_this find "CHACAL|AVERT|") == 0 }}) then {{ diag_log ("M|{k}|" + _this) }} }};',
                      1, fichier)
        n = t.count("call BIS_fnc_getParamValue")
        if n < 60: raise SystemExit(f"RETOUCHE REFUSEE 00_socle : {n} lectures de parametres, >= 60 attendues")
        t = t.replace("call BIS_fnc_getParamValue", "call MULTI_fnc_param")
    # tout groupe cree par une cellule porte son numero : c'est ce qui rend a chaque cellule SES unites
    for camp in ("east", "west"):
        t = re.sub(rf"\bcreateGroup {camp}\b", f"([{camp}, {k}] call MULTI_fnc_groupe)", t)
    if fichier == "30_opfor":
        t = remplacer(t, f"{p}EST_SITE = allUnits select {{ side _x == east && {{ !(_x in {p}QRF) }} }};",
                      f"{p}EST_SITE = (allUnits select {{ (_x call MULTI_fnc_cellule) == {k} }}) select {{ side _x == east && {{ !(_x in {p}QRF) }} }};",
                      1, fichier)
    if fichier == "50_capture":
        t = remplacer(t, f"{p}TOUS = {{ allUnits + allDeadMen }};",
                      f"{p}TOUS = {{ (allUnits + allDeadMen) select {{ private _c = _x getVariable [\"multi_c\", -1]; if (_c < 0) then {{ _c = _x call MULTI_fnc_cellule }}; _c == {k} }} }};", 1, fichier)
        t = remplacer(t, f"{{ if (count (crew _x) > 0) then {{ _x call {p}fnc_identifierVehicule }} }} forEach vehicles;",
                      f"{{ if ((count (crew _x) > 0) && {{ ((crew _x select 0) call MULTI_fnc_cellule) == {k} }}) then {{ _x setVariable [\"multi_c\", {k}]; _x call {p}fnc_identifierVehicule }} }} forEach vehicles;",
                      1, fichier)
        t = remplacer(t, "private _vivants = allUnits select { alive _x };",
                      f"private _vivants = (call {p}TOUS) select {{ alive _x }};", 1, fichier)
        t = remplacer(t, 'params ["_vic", "_tueur", ["_instig", objNull]];',
                      f'params ["_vic", "_tueur", ["_instig", objNull]];\n    if ((_vic call MULTI_fnc_cellule) != {k}) exitWith {{}};   // MULTI : une mort d une autre cellule ne s ecrit pas ici',
                      1, fichier)
        # ! L'ORDONNANCEUR SQF EST LE GOULOT, PAS LE PROCESSEUR ( balayage C3 v1, 22/09, 13 h 38 ). A K = 5 : 29 images/s,
        # fil principal occupe a 36 %, mais chaque boucle de 2 s des cellules tournait toutes les 3,6 a 4,2 s - le budget
        # de l'ordonnanceur ( 3 ms par image ) est partage par toutes les cellules. La boucle des trois vues est un
        # INSTRUMENT : elle ne commande rien. Elle devient non ordonnancee, contenu identique, a pas fixe ; la logique de
        # mission garde seule l'ordonnanceur. Ses tours sont decales d'une cellule a l'autre pour ne pas s'empiler.
        debut_vues = f"[] spawn {{\n    while {{ !{p}FIN }} do {{\n        private _tr = round (time * 100) / 100;"
        fin_vues = f"        sleep {p}DTV;\n    }};\n}};\n\"CHACAL|OK|vues|1\" call {p}LOG;"
        t = remplacer(t, debut_vues,
                      f"{p}T_VUES = time - ({k} * 0.37);\n{p}EH_VUES = addMissionEventHandler [\"EachFrame\", {{\n"
                      f"    if ({p}FIN || {{ {p}CAP_VERSION != 1 }} || {{ (time - {p}T_VUES) < {p}DTV }}) exitWith {{}};\n"
                      f"    {p}T_VUES = time;\n    call {{\n        private _tr = round (time * 100) / 100;", 1, fichier)
        t = remplacer(t, fin_vues,
                      f"    }};\n}}];\n\"CHACAL|OK|vues|1\" call {p}LOG;\n"
                      f"// MULTI : le POULS de la cellule - une boucle ordonnancee de 2 s qui ne fait rien d'autre que dire quand elle\n"
                      f"// tourne. Son retard est celui de toute la logique de mission de la cellule : c'est la porte de cadence.\n"
                      f"[] spawn {{ while {{ !{p}FIN }} do {{ sleep 2; (format [\"CHACAL|C|pouls|%1\", round (time * 100) / 100]) call {p}LOG }} }};",
                      1, fichier)
        t = remplacer(t, f'removeMissionEventHandler ["EachFrame", {p}EH_FRAME];',
                      f'removeMissionEventHandler ["EachFrame", {p}EH_FRAME];\n    removeMissionEventHandler ["EachFrame", {p}EH_VUES];', 1, fichier)
        t = remplacer(t, f'{{ _x removeAllEventHandlers "Fired" }} forEach ((call {p}TOUS) + vehicles);',
                      f'{{ _x removeAllEventHandlers "Fired" }} forEach ((call {p}TOUS) + (vehicles select {{ (_x getVariable ["multi_c", -1]) == {k} }}));',
                      1, fichier)
    # ! LES HORLOGES PARTENT AU DEPART COMMUN, PAS AU MONTAGE ( fumee du 22/09, 13 h 08 ). Dans le banc seul, l'Oracle,
    # le controle positif, le canari et la machine a phases partent au chargement de la mission, a quelques secondes
    # les uns des autres. Dans le multiple, la cellule 1 est montee jusqu'a une minute et demie avant la derniere : son
    # Oracle aurait decide trois fois avant que son detachement ne bouge, et son controle positif aurait frappe des
    # l'ouverture de la phase. Chaque horloge attend donc MULTI_DEPART, qui joue le role du chargement du banc seul.
    ATTENTE = 'waitUntil { sleep 1; !isNil "MULTI_DEPART" };   // MULTI : l horloge part au depart commun'
    if fichier == "60_phases":
        t = remplacer(t, f'[] spawn {{\nsleep 3;\nif ({p}ISSUE == "VOID") exitWith {{ {p}FIN = true }};',
                      f'[] spawn {{\n{ATTENTE}\nsleep 3;\nif ({p}ISSUE == "VOID") exitWith {{ {p}FIN = true }};', 1, fichier)
    if fichier in ("45_oracle", "46_controles_oracle"):
        w = f'waitUntil {{ sleep 2; {p}FIN || {{ !isNil "{p}TPHASE" }} }};'
        t = remplacer(t, w, f"{ATTENTE}\n    {w}", 1 if fichier == "45_oracle" else 2, fichier)
    if fichier == "70_verdict":
        t = remplacer(t, "[] spawn {\n    sleep 20;", "[] spawn {\n    " + ATTENTE + "\n    sleep 20;", 1, fichier)
        t = remplacer(t, f"{p}SANS_JAMBES, {p}OBS]) call {p}LOG;", f"{p}SANS_JAMBES, {p}OBS]) call {p}LOG;\n    {p}MUET = true;   // MULTI : la cellule se tait, comme un serveur arrete", 1, fichier)
        # le canari tire trois coups : il ne doit pas etre pose a portee d'une autre cellule
        t = remplacer(t, "if (surfaceIsWater _c0) then { continue };",
                      f"if (surfaceIsWater _c0 || {{ !([_c0, {k}] call MULTI_fnc_loin) }}) then {{ continue }};", 1, fichier)
        t = remplacer(t, f"_p = [{p}SITE getPos [3000, 360 call {p}fnc_al], 150] call {p}fnc_plat;",
                      f"_p = [{p}SITE getPos [3000, 360 call {p}fnc_al], 150] call {p}fnc_plat;\n"
                      f"        {{ private _c9 = [{p}SITE getPos [3000, _x], 150] call {p}fnc_plat; if (!surfaceIsWater _c9 && {{ [_c9, {k}] call MULTI_fnc_loin }}) exitWith {{ _p = _c9 }} }} forEach [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];",
                      1, fichier)
    # aucune globale du banc seul ne doit survivre
    if "CHACAL_" in t: raise SystemExit(f"{fichier} cellule {k} : CHACAL_ subsiste")
    if re.search(r"\bcreateGroup (east|west)\b", t): raise SystemExit(f"{fichier} cellule {k} : createGroup non marque")
    return t


def main():
    if os.path.exists(DST): shutil.rmtree(DST)
    os.makedirs(DST)
    for k in range(1, KMAX + 1):
        os.makedirs(os.path.join(DST, f"c{k}"))
        for f in ORDRE:
            t = open(os.path.join(SRC, "chacal", f + ".sqf"), encoding="utf-8", errors="strict").read()
            open(os.path.join(DST, f"c{k}", f + ".sqf"), "w", encoding="utf-8").write(cellule(k, f, t))
    # description.ext : les parametres du banc seul, inchanges, plus ceux du multiple
    d = open(os.path.join(SRC, "description.ext"), encoding="utf-8").read()
    d = remplacer(d, 'onLoadName = "CHACAL";', 'onLoadName = "CHACAL MULTI";', 1, "description.ext")
    ajout = ["\n    // ===== EPISODE MULTIPLE ( 22/09 ) : K cellules ; chaque cellule peut surcharger quelques parametres ====="]
    def classe(nom, defaut, titre):
        return (f"    class {nom}\n    {{\n        title = \"{titre}\";\n        values[] = {{{defaut}}};\n"
                f"        texts[]  = {{\"{defaut}\"}};\n        default = {defaut};\n    }};")
    ajout.append(classe("MULTI_K", 1, "Nombre de cellules"))
    ajout.append(classe("MULTI_TMAX", 1200, "Censure : secondes apres le depart commun"))
    ajout.append(classe("MULTI_SONDE", 1, "Sonde de connaissance hors cellules"))
    ajout.append(classe("MULTI_ESPACEMENT", 3000, "Distance minimale entre emprises, en metres"))
    ajout.append(classe("MULTI_ESPACEMENT_MIN", 2000, "Sous cette distance a une autre cellule, la cellule est annulee au montage"))
    for k in range(1, KMAX + 1):
        for x in PAR_CELLULE:
            ajout.append(classe(f"MULTI_C{k}_{x}", SENTINELLE, f"Cellule {k} : {x} ( {SENTINELLE} = valeur commune )"))
    i = d.rfind("};")
    if "class Params" not in d or i < 0: raise SystemExit("description.ext sans class Params")
    # la derniere accolade fermante du fichier est celle de class Params : on insere avant
    j = d.rfind("};", 0, i)
    fin_params = d.rfind("};")
    d = d[:fin_params] + "\n".join(ajout) + "\n" + d[fin_params:]
    open(os.path.join(DST, "description.ext"), "w", encoding="utf-8").write(d)
    shutil.copy(os.path.join(SRC, "mission.sqm"), os.path.join(DST, "mission.sqm"))
    print(f"mission multiple : {KMAX} cellules x {len(ORDRE)} fichiers, {len(PAR_CELLULE)} parametres par cellule")


main()
