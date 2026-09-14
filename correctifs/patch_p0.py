#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-P0
# P0 : la phase qui commande toutes les autres. Trois gestes, prepares ici, appliques des que la
# campagne rend la main.
#
# 1. LE TEMOIN HASARD N EN EST PAS UN. CHACAL_fnc_rnd est seme par la graine : deux episodes de meme
#    graine tirent le MEME azimut. Le bras HASARD ne tire donc pas douze azimuts, il en tire UN par
#    graine - un azimut fixe deguise en hasard. C est ce qui a produit l artefact du 13/09 : le bras
#    hasard avait tire 180 sur la graine 7 (le meilleur) et 300 sur la graine 8 (le pire), et son
#    taux global moyennait les deux. Sans vrai temoin, aucun agent n est distinguable de la chance.
#    Remede : un second generateur, seme par la graine ET par le numero de repetition, qui ne sert
#    QU AU TEMOIN. Le tirage du monde reste intact - c est lui qui doit rester reproductible.
#
# 2. LA PHASE 3 COUTE LA MOITIE DE CHAQUE MISSION POUR RIEN. 110 echecs sur 111, seuil 3 jamais
#    atteint, maximum 2, zero renseignement restitue, verdict ecrit. On ajoute CHACAL_OBS : a 0, la
#    phase 3 se ferme immediatement en declarant ce qu elle fait. Elle n est pas supprimee - on doit
#    pouvoir la rejouer le jour ou on la reparera.
#
# 3. LE CATALOGUE N EXPOSE NI azimut NI azimut_mode. Tant qu ils manquent, aucun corpus
#    d apprentissage ne peut etre constitue hors ligne. C est la piece qui bloque tout.
import re, sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
bil = lambda t: (t.count("{")-t.count("}"), t.count("[")-t.count("]"), t.count("(")-t.count(")"), t.count('"') % 2)

# --- 1. le vrai temoin ---------------------------------------------------------
p = f"{M}/00_socle.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_fnc_rndTemoin" in s:
    print("  00_socle : temoin deja present")
else:
    a = "CHACAL_fnc_rnd = {"
    if a not in s: print("  !! ancre rnd absente"); sys.exit(1)
    f = '''// ! UN TEMOIN QUI NE TIRE QU UNE VALEUR N EST PAS UN TEMOIN ( 14/09 ).
// CHACAL_fnc_rnd est seme par la graine, et c est voulu : le MONDE doit etre reproductible.
// Mais le bras HASARD s en servait aussi, donc il tirait le meme azimut a chaque repetition d une
// graine - un azimut fixe deguise en hasard. C est ce qui a produit l artefact du 13/09 : hasard a
// tire 180 sur la graine 7, le meilleur, et 300 sur la graine 8, le pire ; son taux global
// moyennait les deux et ressemblait a celui du script.
// Ce second generateur est seme par la graine ET par l heure de demarrage du serveur, donc il varie
// d une repetition a l autre. Il ne sert QU AU TEMOIN, jamais au monde.
CHACAL_RNG_T = ((CHACAL_GRAINE * 2654435761) + (round (serverTime * 1000)) + (round (diag_tickTime * 997))) % 65537;
if (CHACAL_RNG_T == 0) then { CHACAL_RNG_T = 1 };
CHACAL_fnc_rndTemoin = {
    CHACAL_RNG_T = ((CHACAL_RNG_T * 75) + 74) % 65537;
    CHACAL_RNG_T / 65537
};

'''
    s2 = s.replace(a, f + a, 1)
    if bil(s) != bil(s2): print("  !! equilibre 00_socle"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 00_socle : CHACAL_fnc_rndTemoin, seme par episode et non par graine")

# --- 1b. la couture utilise le temoin ------------------------------------------
p = f"{M}/60_phases.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_fnc_rndTemoin" in s:
    print("  60_phases : couture deja branchee sur le temoin")
else:
    a = "private _k = floor ((call CHACAL_fnc_rnd) * (count _candidats));"
    if a not in s: print("  !! ancre tirage absente"); sys.exit(1)
    n = ("// ! le TEMOIN, pas le generateur du monde : sinon le bras hasard tire un azimut fixe par graine\n"
         "        private _k = floor ((call CHACAL_fnc_rndTemoin) * (count _candidats));")
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre 60_phases"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 60_phases : le bras hasard tire avec le temoin")

# --- 2. CHACAL_OBS -------------------------------------------------------------
p = f"{M}/00_socle.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_OBS " in s:
    print("  00_socle : CHACAL_OBS deja present")
else:
    a = 'CHACAL_AZIMUT = ["CHACAL_AZIMUT", 0] call BIS_fnc_getParamValue;'
    if a not in s: print("  !! ancre azimut absente"); sys.exit(1)
    n = (a + '\n'
         '// ! LA PHASE 3 COUTE LA MOITIE DE CHAQUE MISSION POUR RIEN. Verdict du 13/09 : 110 echecs\n'
         '// sur 111, seuil de renseignement a 3 et maximum jamais atteint 2, zero renseignement\n'
         '// restitue a l assaut, soit 55 heures de calcul pour zero information. A 0, la phase 3 se\n'
         '// ferme immediatement et le DIT. On ne la supprime pas : on doit pouvoir la rejouer le jour\n'
         '// ou on la reparera.\n'
         'CHACAL_OBS = ["CHACAL_OBS", 1] call BIS_fnc_getParamValue;')
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre OBS"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 00_socle : parametre CHACAL_OBS")

p = f"{M}/60_phases.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "observation_coupee" in s:
    print("  60_phases : coupure deja presente")
else:
    a = "    _plafond = 3 call CHACAL_fnc_duree;\n    [3, \"OBSERVATION\", _plafond] call CHACAL_fnc_debutPhase;"
    if a not in s: print("  !! ancre phase 3 absente"); sys.exit(1)
    n = ('''    _plafond = 3 call CHACAL_fnc_duree;
    [3, "OBSERVATION", _plafond] call CHACAL_fnc_debutPhase;
    // ! COUPURE ASSUMEE ET ECRITE. Voir verdicts/phase3-porte-hors-datteinte.md.
    if (CHACAL_OBS == 0) exitWith {
        (format ["CHACAL|AVERT|hors_corpus|observation_coupee|1|seuil|%1|jamais_atteint|1",
            CHACAL_SEUIL_RENS]) call CHACAL_LOG;
        (format ["CHACAL|E|observation_coupee|%1|economie_s|%2", round (time * 100) / 100,
            round _plafond]) call CHACAL_LOG;
        [3, "OBSERVATION", "COUPEE"] call CHACAL_fnc_finPhase;
    };''')
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre coupure", bil(s), bil(s2)); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 60_phases : la phase 3 se coupe quand CHACAL_OBS vaut 0")

# --- 3. description.ext et lancer.sh ------------------------------------------
p = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/description.ext"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_OBS" in s:
    print("  description.ext : deja present")
else:
    i = s.index("class CHACAL_AZIMUT"); j = s.index("{", i); prof = 0
    for k in range(j, len(s)):
        if s[k] == "{": prof += 1
        elif s[k] == "}":
            prof -= 1
            if prof == 0: fin = s.index(";", k) + 1; break
    bloc = ('\n    class CHACAL_OBS\n    {\n'
            '        title = "Phase 3 OBSERVATION : 1 = jouee, 0 = coupee (verdict : 110 echecs sur 111)";\n'
            '        values[] = {0,1};\n        texts[]  = {"COUPEE","JOUEE"};\n        default  = 1;\n    };')
    s2 = s[:fin] + bloc + s[fin:]
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    t = open(p, encoding="utf-8", errors="surrogateescape").read()
    pr = lambda n: t[:t.index(n)].count("{") - t[:t.index(n)].count("}")
    a1, a2 = pr("class CHACAL_AZIMUT"), pr("class CHACAL_OBS")
    print(f"  PATCHE : description.ext : CHACAL_OBS | imbrication AZIMUT={a1} OBS={a2}",
          "-> OK" if a1 == a2 else "-> !! DIFFERENTES")
    if a1 != a2: sys.exit(1)

p = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "OBS=" in s:
    print("  lancer.sh : deja present")
else:
    a = "AZIMUT=$(lit azimut 0);"
    b = 'ecrire_param AZIMUT "$AZIMUT";'
    if a not in s or b not in s: print("  !! ancres lancer.sh absentes"); sys.exit(1)
    s = s.replace(a, a + " OBS=$(lit obs 1);", 1)
    s = s.replace(b, b + ' ecrire_param OBS "$OBS";', 1)
    s = s.replace('"exfil","azimut")', '"exfil","azimut","obs")', 1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  PATCHE : lancer.sh : obs lu, ecrit, et controle dans LEVIERS_CONTROLES")

# --- 4. la ligne FINI ----------------------------------------------------------
p = f"{M}/70_verdict.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "|obs|%50" in s:
    print("  70_verdict : deja present")
else:
    a = "|sans_jambes|%49"
    if a not in s: print("  !! ancre FINI absente"); sys.exit(1)
    s2 = s.replace(a, a + "|obs|%50", 1)
    b = "CHACAL_AZIMUT_CHOISI, CHACAL_SANS_JAMBES]) call CHACAL_LOG;"
    if b not in s2: print("  !! ancre valeurs absente"); sys.exit(1)
    s3 = s2.replace(b, "CHACAL_AZIMUT_CHOISI, CHACAL_SANS_JAMBES, CHACAL_OBS]) call CHACAL_LOG;", 1)
    if bil(s) != bil(s3): print("  !! equilibre FINI"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s3)
    print("  PATCHE : 70_verdict : obs dans la ligne FINI")
