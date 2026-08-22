#!/usr/bin/env python3
"""banc_live — LA POLITIQUE APPRISE JOUE DANS ARMA.

Harnais repris de `move_combat.py`, qui marche : serveur lance avec HMT_EXT_PORT, pont TCP
natif, SQF envoye et journal lu par socket. Rien n est invente ici.

LA BOUCLE : PERC18 (18 colonnes sorties du JEU) -> selection base9+posture3 -> politique
-> 10 actions -> SQF (caps / tenir / appuyer).

⚠️ CE QUI EST DECLARE AVANT LE PREMIER PAS :
  · la politique NE SE COUCHE JAMAIS (elle n a pas les actions 10/11/12). Sur Arma, ou se
    montrer coute 4,00 DEFINITIVEMENT, c est un handicap a elle, pas au portage.
  · le monde d entrainement : 4 defenseurs, 4 attaquants, 200 m (LU dans l env le 14/08,
    apres qu une affirmation de ce meme docstring a menti pendant des semaines). On le reproduit.
  · CE RUN EST UN BANC DE MONTAGE, pas un verdict : il prouve que la chaine tourne et que
    les 18 colonnes sortent du jeu. Le verdict de concordance demandera des repetitions.
"""
import sys, os, time, re, math, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
import arma_couture as C
import torch
from porter_boucle import charger, COLS
from boucle import NA

# ⚠️ BRAS DE BASELINE ⟨Fable, 15/08⟩ : « 11,9 % n a pas de sens tant qu on ne sait pas ce
# que le MEILLEUR CORPS CONNU fait sur ce banc. » Trois bras, meme banc, meme site.
BRAS = sys.argv[1] if len(sys.argv) > 1 else "politique"
SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5830, 6062
MIS = "BancLive.Stratis"
# ⚠️ LE JOURNAL PORTE SON RUN ⟨21/08, apres revue⟩. Il s appelait `serverLV.out`, en dur,
# ouvert en AJOUT et jamais tronque : 27,8 Mo accumules sur 279 demarrages d hote, tous
# jours confondus. La ligne 5 du juge — les erreurs de script — ne pouvait donc PAS
# juger une nuit : elle aurait lu les erreurs de la semaine.
# ⚠️ `prevol.py:35` fait exactement ca depuis toujours, et la discipline n a JAMAIS
# traverse. Quatrieme non-transposition de la semaine, apres l ordre scene/socle,
# l idiome du marqueur numerote et le compteur d erreurs.
LOG = SB + "/logs/serverLV%s.out" % (os.environ.get("HMT_SESSION", ""))
OBJ = (4644.0, 5652.0)   # ⚠️ SITE CHANGE LE 14/08 — VERDICT_SITE_LIVE.md.
# L ancien (1734,5391) etait une PLAINE : mediane slope 0,000 contre 0,368 au gymnase,
# 58,3 pourcent de pentes rigoureusement nulles, et dcover coince sur son garde-fou
# (16/30 = 0,533) dans 78,3 pourcent des cas. 100 pourcent des decisions arrivaient hors
# distribution et la politique se figeait. Nouveau site : ecart de pente 0,006, zero
# pente nulle, garde-fou a 3,3 pourcent. Choisi par 80 candidats et une regle deposee AVANT.          # un des six terrains candidats certifies
# ⚠️ 170 m, PAS 200. Mesure du 12/08 : a 200 m les hommes naissent a `apy/S = -0,95` quand le
# gymnase n a JAMAIS depasse -0,71 — quatre colonnes hors plage des le premier pas, simplement
# parce que la geometrie ne correspondait pas. Le gymnase fait naitre a `R_spawn = 170` sur une
# echelle `terr_R = 200`. On reprend ses chiffres exactement : ce n est pas un reglage, c est
# le meme monde.
# ⚠️ 4 CONTRE 4, PAS 13 CONTRE 8. Le docstring de ce fichier a affirme pendant des semaines
# que le monde d entrainement etait « 13 defenseurs, 8 attaquants » et qu on le reproduisait.
# C ETAIT FAUX : `MONDE_ARMA` ne fixe ni `A` ni `D`, donc le gymnase entraine sur les defauts
# d `AssaultTerrain`, soit A=4 et D=4. Verifie le 14/08 : `e.A=4, e.D=4`.
# La politique n avait donc JAMAIS rencontre treize defenseurs. Tripler la menace ecrase `nd`
# et tuait les huit hommes en quatorze pas. Le 51,1 pourcent du gymnase et le 0 pourcent du
# banc ne mesuraient pas le meme monde. On reprend les chiffres du gymnase, pas les miens.
NDEF, NATT, DIST = 4, 4, 170.0
PAS_MAX, PERIODE = 60, 3.28     # meme pas que le gymnase : 3,28 s


def sans_commentaires(sqf):
    """ATTENTION — LES COMMENTAIRES // TUENT LE SQF ENVOYE PAR LE PONT.
    Le protocole du pont remplace les retours a la ligne (\n -> \x01) : le script arrive donc
    en UNE SEULE LIGNE cote Arma, et le premier `//` avale TOUT CE QUI SUIT. Symptome observe :
    « Error Invalid number in expression » pointant sur le commentaire lui-meme, puis un
    HMT_ENNEMI indefini parce que la scene n a jamais fini de se creer.
    On retire donc les commentaires de ligne AVANT l envoi. Ils restent dans le source Python,
    ou ils servent a l humain."""
    return "\n".join(re.sub(r"//.*$", "", l) for l in sqf.split("\n"))


def sh(c):
    subprocess.run(c, shell=True, executable="/bin/bash")


SCENE = '''
HMT_OBJ = [%f, %f, 0];

// ═══ LES POSITIONS SONT CERTIFIEES AVANT QUE QUICONQUE NAISSE ⟨bloc C, plan de Fable⟩ ═══
// La scene ne testait RIEN : les hommes naissaient au pur hasard, et le prevol ne les
// eprouvait pas non plus — T5 et T7 testent un TEMOIN a 250-370 m de la. On certifie donc
// ICI, AVANT la creation : personne n existe encore, donc rien a corrompre et personne a
// alerter (un homme qui tire renseigne le camp adverse, et `knowsAbout` est de CAMP).
//
// ⚠️ LES ATTAQUANTS SE RE-TIRENT PAR L AZIMUT GLOBAL, JAMAIS POSITION PAR POSITION : leur
// formation recopie celle du gymnase (`assault_terrain.py:316`) et la casser rendrait le
// banc infidele. Les defenseurs, eux, sont deja aleatoires : re-tirage individuel.
HMT_SCENE_REJETS = 0;
private _az = random 360; private _posA = []; private _essaiAz = 0;
while { _essaiAz < 6 } do {
    _essaiAz = _essaiAz + 1; _posA = [];
    for "_i" from 1 to %d do {
        _posA pushBack [(HMT_OBJ select 0) + %f * sin _az + (((_i - 1) mod 2) * 6 - 3),
                        (HMT_OBJ select 1) + %f * cos _az + ((_i - 2) * 6), 0];
    };
    private _v = [_posA] call HMT_CERTIFIER_POSITIONS;
    private _ok = { (_x select 0) == "recu" } count _v;
    (format ["HMT|SOCLE|SCENE_AZ|essai|%%1|az|%%2|recus|%%3|sur|%%4",
             _essaiAz, round _az, _ok, count _posA]) call HMT_LOG;
    if (_ok == count _posA) exitWith {};
    HMT_SCENE_REJETS = HMT_SCENE_REJETS + 1;
    _az = random 360;
};

private _gd = createGroup east; HMT_ENNEMI = [];
for "_i" from 1 to %d do {
    private _p = []; private _essai = 0;
    while { _essai < 8 } do {
        _essai = _essai + 1;
        private _a = random 360; private _r = 10 + random 25;
        _p = [(HMT_OBJ select 0) + _r * sin _a, (HMT_OBJ select 1) + _r * cos _a, 0];
        private _v = [[_p]] call HMT_CERTIFIER_POSITIONS;
        if (((_v select 0) select 0) == "recu") exitWith {};
        HMT_SCENE_REJETS = HMT_SCENE_REJETS + 1;
    };
    private _u = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u setSkill 0.5; _u disableAI "PATH";
    _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
    HMT_ENNEMI pushBack _u;
};
private _ga = createGroup west; HMT_GA = _ga; HMT_FR = [];
for "_i" from 1 to %d do {
    // ⚠️ LA FORMULE DU GYMNASE, RECOPIEE — assault_terrain.py:316. Ce n est pas un reglage.
    // Le banc formait UNE SEULE FILE le long de x : `apy` etait IDENTIQUE pour les huit
    // hommes, variance rigoureusement nulle sur une coordonnee entiere. Les huit recevaient
    // donc la meme observation et la meme action — mesure du 14/08 : etalement 0,069 contre
    // 0,160 au gymnase, et 100 pourcent d action 2 sur Arma.
    // Le gymnase fait : apx = sx + (ar %% 2)*6 - 3  ·  apy = sy + (ar - 1)*6, avec ar = 0..7.
    // L indice SQF va de 1 a 8, donc ar = _i - 1.
    // la position vient du jeu DEJA CERTIFIE ci-dessus — on ne la recalcule pas, sans quoi
    // deux formules divergeraient sur la meme grandeur.
    private _p = _posA select (_i - 1);
    private _u = _ga createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u setSkill 0.5;
    // PATH coupe : c est la politique qui pilote, par setVelocity — comme au gymnase.
    if (HMT_BRAS == "natif") then {
        // ⚠️ REPARATION DU 22/08 AU SOIR. L IA d Arma joue entiere PENDANT L EPISODE — mais
        // elle recevait son ordre d assaut DANS CE BLOC, donc AVANT le prevol, et elle
        // marchait pendant les 60 a 180 s du prevol. Mesure : depart median 135 m contre
        // 164 m pour la politique ; 88 episodes sur 113 deja sous 150 m, contre 13 sur 112 ;
        // budget de 60 pas dont 9 arrivees sur 10 consomment 52 a 56. Environ SIX PAS
        // ⚠️ AUCUN SIGNE POUR CENT DANS CE BLOC : SCENE est une chaine de FORMAT (7
        // substituants). Un seul pour-cent litteral ici et le fichier ne se charge plus.
        // C est la sonde de verification qui l a attrape, avant 14 heures de run.
        // offerts a un seul bras. La comparaison du 22/08 a ete retiree pour ca.
        // On coupe donc les MEMES facultes que dans l autre bras jusqu au pas 0, et on les
        // REND au pas 0, a l instant ou la politique envoie son premier ordre.
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
        _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
    } else {
        // ⚠️ `RED`, PAS `BLUE`. `combatMode "BLUE"` signifie « NE JAMAIS TIRER » dans le
        // moteur : les attaquants du banc n ont donc jamais tire une balle en 67 episodes.
        // Mesure du 15/08 : memes deux `disableAI`, BLUE = 0 coup, RED = 145 coups, et la
        // progression est IDENTIQUE (154 m) — la politique garde tout son controle du
        // deplacement. Rendre les facultes d IA (AUTOCOMBAT/FSM) est au contraire le PIRE
        // des quatre bras : 14 coups et 111 m, l IA pilote contre la politique.
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
        _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
    };
    // ⚠️ L ARME EN MAIN, PAS DANS LE SAC. `forceWeaponFire` (action 9) et
    // `commandSuppressiveFire` emploient tous deux `currentWeapon` : arme non selectionnee,
    // aucun des deux ne fait rien. Mesure du 15/08 au soir : le banc du feu force a rendu
    // ZERO balle dans les DEUX bras et son controle positif est tombe. Meme faute que le
    // banc d appui ce matin, reparee la-bas et pas reportee ici ni dans ce banc.
    _u selectWeapon (primaryWeapon _u);
    _u setVariable ["HMT_LASTDMG", 0];
    HMT_FR pushBack _u;
    // MESURE DU 11/08 — poussee continue de 6 m/s pendant 8 s, ~48 m attendus :
    //   PATH+AUTOCOMBAT+FSM ....  9 m     disableAI ALL ....  9 m
    //   aucun disableAI ........ 48 m     disableAI MOVE ... 18 m
    // C est `disableAI PATH` qui bloque. La ligne venait du banc d appui, ou les hommes NE
    // DOIVENT PAS bouger ; recopiee sur des assaillants pilotes a la vitesse, elle leur
    // retirait les jambes. Huit morts en sept pas sans gagner deux metres : la politique
    // n avait jamais eu la main. On garde AUTOCOMBAT et FSM coupes — c est la POLITIQUE qui
    // decide, pas l IA d Arma — mais PATH reste actif.
};
HMT_POST = []; { HMT_POST pushBack 0 } forEach HMT_FR;
// ⚠️ LE COMPTEUR DE COUPS ⟨20/08⟩. La condition 3 du predicat depose le 16/08 — « le natif
// TIRE, au moins 1 coup par episode en mediane » — n a PAS PU ETRE LEVEE sur les 107
// episodes de la nuit : ce fichier n enregistrait AUCUN coup. On ne pouvait affirmer que
// les episodes la satisfaisaient, seulement qu aucun ne l avait dementie.
// L idiome existait deja dans le socle (l EH `Fired` de T4 et de HMT_TIRER_C9) : il n avait
// jamais ete transpose ici. Une condition eliminatoire qu on ne peut pas mesurer n elimine rien.
HMT_COUPS_ATT = 0; HMT_COUPS_DEF = 0;
{ _x addEventHandler ["Fired", { HMT_COUPS_ATT = HMT_COUPS_ATT + 1 }] } forEach HMT_FR;
{ _x addEventHandler ["Fired", { HMT_COUPS_DEF = HMT_COUPS_DEF + 1 }] } forEach HMT_ENNEMI;
// ⚠️ CANDIDAT B ⟨22/08⟩. Deux observables de plus, ajoutes en FIN de ligne d etat pour ne
// casser aucun lecteur existant (les regex de banc_live et de lire_natif ne s ancrent pas
// sur la fin). `HitPart` et non `HandleDamage` — c est l EH qui a servi a mesurer la
// courbe de toucher le 26/07, et changer d EH changerait l unite sans le dire.
HMT_TOUCHES = 0; HMT_D1 = -1;
{ _x addEventHandler ["HitPart", { HMT_TOUCHES = HMT_TOUCHES + 1 }] } forEach HMT_FR;
// distance du PREMIER coup tire par un defenseur : a l attaquant vivant le plus proche.
{ _x addEventHandler ["Fired", {
    if (HMT_D1 < 0) then {
        private _t = _this select 0; private _m = 1e9;
        { if (alive _x) then { private _d = _x distance2D _t; if (_d < _m) then { _m = _d } } } forEach HMT_FR;
        if (_m < 1e8) then { HMT_D1 = round _m };
    };
}] } forEach HMT_ENNEMI;
// ⚠️ L ORDRE D ASSAUT DU NATIF N EST PLUS DONNE ICI — il l etait avant le prevol.
// Il part au PAS 0, depuis la boucle, au meme instant que le premier ordre de la politique.
diag_log format ["HARMATTAN_SCENE def=%%1 att=%%2 enmain=%%3", count HMT_ENNEMI, count HMT_FR,
  ({(currentWeapon _x) != ""} count HMT_FR)];
// ⚠️ L ARTEFACT PORTE SON CANAL ⟨Fable, 20/08⟩. Le monde declarait `HMT_CANAL`, mais AUCUN
// artefact ne le portait — ni les lots de la porte ni les episodes de la nuit. L identite de
// canal entre la porte et la campagne reposait sur la seule continuite du hash. Un artefact
// qui ne dit pas dans quel monde il est ne peut pas etre compare a un autre.
diag_log format ["HARMATTAN_CANAL %%1", (if (isNil "HMT_CANAL") then {"INCONNU"} else {HMT_CANAL})];
'''.replace("HMT_BRAS", '"' + BRAS + '"') % (OBJ[0], OBJ[1], NATT, DIST, DIST, NDEF, NATT)
# ⚠️ SEPT substituants depuis le bloc C, et dans un ORDRE NOUVEAU : la certification des
# positions attaquantes vient AVANT la creation des defenseurs, donc `NATT` passe en 3e.
# Un format positionnel qui change d ordre sans que le tuple suive donne un monde faux et
# SILENCIEUX — un `%d` qui recoit une distance et un `%f` qui recoit un compte.

ETAT = '''
private _v = 0; private _dmin = 1e9;
{ if (alive _x) then { _v = _v + 1; private _d = _x distance2D HMT_OBJ;
    if (_d < _dmin) then { _dmin = _d } } } forEach HMT_FR;
private _ve = 0; { if (alive _x) then { _ve = _ve + 1 } } forEach HMT_ENNEMI;
// ⚠️ LA SENTINELLE DISAIT UNE PRISE ⟨mesure du 21/08⟩. Sans attaquant vivant, `_dmin`
// restait a 1e9 — et le JEU l imprime « 1e+09 » (demande au jeu, pas suppose). La
// regex du lecteur, qui exigeait des CHIFFRES, n en capturait que le « 1 » : l episode s arretait sur
// une condition « objectif a un metre » qui n existait pas. Dans le journal brut,
// « TOUS MORTS » etait indiscernable d « ARRIVE AU BUT ».
// ⚠️ ON REND -1, QUI NE PEUT PAS ETRE UNE DISTANCE. Une mesure doit savoir dire
// qu elle n a pas eu lieu.
diag_log format ["HARMATTAN_ETAT vivants=%1 def=%2 dmin=%3 tou=%4 cda=%5 cdd=%6 d1=%7", _v, _ve,
                 (if (_v == 0) then {-1} else {round _dmin}),
                 (if (isNil "HMT_TOUCHES") then {-1} else {HMT_TOUCHES}),
                 (if (isNil "HMT_COUPS_ATT") then {-1} else {HMT_COUPS_ATT}),
                 (if (isNil "HMT_COUPS_DEF") then {-1} else {HMT_COUPS_DEF}),
                 (if (isNil "HMT_D1") then {-1} else {HMT_D1})];
'''

if __name__ == "__main__":
    C.CX, C.CY = OBJ
    C.SCALE = 200.0
    C.FIRE_RANGE = 110.0
    C.MOVE_SPD = 6.0

    print("  lancement du serveur live...", flush=True)
    # ⚠️ TRONQUER AVANT DE LANCER — sinon le journal du run precedent reste dessous
    # et la ligne 5 imputerait a ce run des erreurs qui ne sont pas les siennes.
    open(LOG, "w").close()
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       # ATTENTION : le -mod= porte des POINTS-VIRGULES. Sans guillemets, le shell coupe la
       # commande : le serveur est parti avec @CBA_A3 SEUL, les autres fragments ont ete
       # executes comme des commandes, et la redirection ">> LOG" ne s appliquait plus qu au
       # dernier — d ou le journal d Arma deverse dans la sortie du pilote. relancer.sh
       # protege ce meme argument depuis le debut ; je ne l avais pas repris.
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(45)

    b = SocketBridge(EXT)
    print("  pont TCP ouvert", flush=True)
    print("  scene : %d defenseurs, %d attaquants a %d m" % (NDEF, NATT, DIST), flush=True)
    time.sleep(3)
    b.send(sans_commentaires('call compile preprocessFileLineNumbers "socle.sqf";'), wait=False)
    time.sleep(2)
    # ⚠️ LE SOCLE AVANT LA SCENE ⟨21/08⟩. La scene appelait `HMT_CERTIFIER_POSITIONS`,
    # definie dans le socle, alors que le socle se chargeait 44 lignes PLUS BAS :
    # 6 764 erreurs dans la seule nuit du 20/08, et l orpheline `_v` avec (13 fois).
    # Meme mal que le bloc C, repare dans `prevol.py` le 19/08 et JAMAIS transpose ici —
    # troisieme non-transposition qui coute, apres l idiome du marqueur numerote et le
    # compteur d erreurs de script.
    # ⚠️ LE DRAPEAU ATTERRIT AVEC L ORDRE, OU PAS DU TOUT : corriger l ordre SEUL
    # activerait le bloc C sur le chemin de campagne, avec son critere a 23 m dont on a
    # mesure qu il refuse le monde entier (0 position recue sur 37, six azimuts a 0/4).
    b.send('HMT_CERTIFIER = false;', wait=False); time.sleep(0.5)
    b.send(sans_commentaires(SCENE))
    # ATTENTION : le journal d Arma ne porte RIEN de tout ceci. `to_socket_out` reecrit les
    # diag_log en emissions socket : la scene, les obs et les accuses arrivent par le PONT,
    # pas dans le .rpt. J ai cherche HARMATTAN_SCENE dans le fichier pendant une heure ; il
    # n y a jamais ete, et son absence ne prouvait rien.
    ok = False
    for _ in range(20):
        if any("HARMATTAN_SCENE" in L for L in b._log_lines(400)):
            ok = True; break
        time.sleep(0.5)
    # ⚠️ ON DEMANDE AU JEU COMBIEN DE DEFENSEURS SONT VIVANTS, A TROIS MOMENTS.
    # `HARMATTAN_SCENE def=%d` compte `count HMT_ENNEMI` — la TAILLE DU TABLEAU, pas les
    # vivants. Il disait 4 dans les 26 episodes joues sans aucun defenseur.
    b.send(sans_commentaires(
        'private _n=0; { if (alive _x) then { _n=_n+1 } } forEach HMT_ENNEMI;'
        'diag_log format ["HARMATTAN_DEFVIV apres_scene def=%1", _n];'), wait=False)
    time.sleep(1.0)      # 0,5 s ne suffisait pas : la sonde n arrivait pas avant la lecture
    ligne = [L for L in b._log_lines(400) if "HARMATTAN_SCENE" in L]
    print("  scene confirmee par le jeu : %s" % (ligne[-1][:70] if ligne else "AUCUNE"), flush=True)
    if not ok:
        print("  la scene ne s est pas creee — on ne joue pas.", flush=True)
        sys.exit(1)
    # ⚠️ `WAKE` RECOUPE FSM ET AUTOCOMBAT SUR TOUS LES ATTAQUANTS. Il est envoye APRES la
    # scene, donc il defaisait le bras natif trois lignes plus loin : `disableAI "FSM"` retire
    # la machine a decision de l IA, et les hommes ne suivaient plus leur point de passage.
    # Mesure du 15/08 : deplacement median 0,07 m/pas, 18 episodes sur 20 au bout des 60 pas,
    # 2 morts. Le controle positif depose (« le natif doit BOUGER, > 1 m/pas ») l a attrape.
    # Huitieme fois du jour qu une etape ULTERIEURE annule silencieusement une etape anterieure.
    # ⚠️ 22/08 AU SOIR, NEUVIEME FOIS. Le commentaire ci-dessus prevenait qu une etape
    # ULTERIEURE annule silencieusement une etape anterieure — et c est ce que ce bloc
    # faisait a la reparation du depart, deux lignes apres elle : je coupais AUTOCOMBAT et
    # FSM du natif dans la SCENE, et ce reveil les rendait, AVANT le prevol. Mesure de la
    # sonde de verification : `APRES PREVOL att=4 def=0` — l IA du natif avait deja tue les
    # quatre defenseurs pendant le prevol, sans point de passage, par le seul AUTOCOMBAT.
    # LES DEUX BRAS RECOIVENT DONC LE MEME REVEIL. Le natif retrouve ses facultes au PAS 0,
    # avec son point de passage, dans le meme geste (voir la boucle plus bas).
    b.send(sans_commentaires(C.WAKE))
    # ⚠️ RIEN NE VIT AVANT LE PAS 0 ⟨22/08 au soir⟩. `C.WAKE` reveille les defenseurs en
    # COMBAT/RED, a 10-35 m de l objectif, AVANT le prevol — et le prevol promene les
    # attaquants pendant 60 a 180 s pour certifier le canal. Le resultat n est pas un
    # controle : c est une FUSILLADE, dont l issue varie d un episode a l autre. Deux
    # episodes de verification suffisent a le voir : l un perd DEUX attaquants, l autre
    # TROIS defenseurs, avant que la mesure ait commence.
    # C est la source commune des deux biais deja mesures : les 26 et 31 episodes joues sans
    # aucun defenseur (61e8800), et les episodes ecartes pour escouade morte avant le depart.
    # `combatMode BLUE` signifie NE JAMAIS TIRER dans le moteur (mesure du 15/08, deja
    # deposee dans ce fichier). On s en sert pour taire les defenseurs, et on les rend a
    # RED au pas 0 — dans le meme geste que le premier ordre des deux bras.
    b.send(sans_commentaires(
        '{ _x disableAI "AUTOCOMBAT"; _x disableAI "FSM"; _x setCombatMode "BLUE";'
        '  _x setBehaviour "CARELESS" } forEach HMT_ENNEMI;'
        'diag_log "HARMATTAN_DEFENSEURS_ENDORMIS";'))
    # ⚠️ ET PERSONNE N EST BLESSABLE AVANT LE PAS 0. Les endormir ne suffit pas : les
    # sondes le montrent — `apres_scene def=4`, `apres_wake def=4`, puis `def=0` APRES le
    # prevol, alors que defenseurs ET attaquants sont inertes. Ce n est donc pas un duel.
    # C est le prevol lui-meme : son binome jetable « vide un chargeur » (T4) sur un axe
    # balaye a 250-370 m du premier attaquant, SANS ALEA — donc FIXE PAR SESSION. Quand cet
    # axe passe par l objectif, la rafale traverse les defenseurs postes a 10-35 m de lui.
    # Un lieu fixe par session explique aussi pourquoi la panne revenait par paquets.
    # On ne touche pas au prevol — il certifie le canal et il a ses raisons. On rend les
    # hommes de l EPISODE insensibles jusqu a l instant ou l episode commence.
    b.send(sans_commentaires(
        '{ _x allowDamage false } forEach (HMT_FR + HMT_ENNEMI);'
        'diag_log "HARMATTAN_INVULNERABLES avant prevol";'))
    time.sleep(2)
    b.send(sans_commentaires(
        'private _n=0; { if (alive _x) then { _n=_n+1 } } forEach HMT_ENNEMI;'
        'diag_log format ["HARMATTAN_DEFVIV apres_wake def=%1", _n];'), wait=False)
    time.sleep(1.0)
    _dv = sorted(set(L.split("HARMATTAN_DEFVIV")[1].strip()[:34]
                     for L in b._log_lines(400) if "HARMATTAN_DEFVIV" in L))
    # ⚠️ UNE SONDE MUETTE DOIT LE DIRE. La version d avant imprimait une ligne VIDE quand
    # elle ne trouvait rien : indiscernable d une sonde qui n a pas ete posee.
    print("  DEFVIV : %s" % (" | ".join(_dv) if _dv else "AUCUNE LIGNE RECUE"), flush=True)

    # ⚠️ ET UNE TROISIEME, JUSTE AVANT QUE LE PREVOL NE PARTE. Entre le reveil et le prevol
    # il y a deux secondes de monde vivant : il faut savoir si elles coutent des defenseurs.
    # ═══ LE PREVOL ⟨Fable : « pas de prevol vert, pas d episode »⟩ ═══
    # Le socle RELIT le monde avant de jouer. Six tests, tous nes d une faute payee :
    #   T1 arme en main · T2 chargeur · T3 mode declare = mode reel (WAKE recoupait FSM)
    #   T4 une BALLE REELLE part · T5 24 m parcourus · T6 combatMode (BLUE = jamais tirer)
    # « La volonte n est pas un mecanisme » : l episode ne demarre pas sans le vert.
    # ⚠️ LE SOCLE SE CHARGE PAR FICHIER, PAS PAR LA SOCKET. 197 lignes envoyees en inline
    # ne passent pas — piege deja paye par le projet (« gros inline -> fichier »). Le fichier
    # est depose dans la mission ; le jeu le compile lui-meme.
    # ⚠️ LE JOURNAL DU SOCLE EST INVISIBLE DU PONT. Le pont ne reecrit `diag_log` en
    # `callExtension "o|"` que dans le texte QU IL ENVOIE ; un fichier compile par le jeu
    # ecrit dans le RPT, pas dans la socket. Diagnostic du 16/08 : le socle se charge bien
    # (`HMT_PREVOL` defini = true), c est mon controle qui cherchait un marqueur qui n arrive
    # jamais. On ne lit donc plus SON journal : on lui DEMANDE son resultat par la socket.
    time.sleep(2.5)
    b.send(sans_commentaires('HMT_PV = nil; [] spawn { HMT_PV = [HMT_FR] call HMT_PREVOL; };'), wait=False)
    _vert, _rap = None, ""
    for _ in range(45):                      # le prevol dort ~15 s
        time.sleep(1.5)
        b.send(sans_commentaires(
            'diag_log format ["HMT|PV|%1|%2", (if (isNil "HMT_PV") then {"attente"} else {HMT_PV}), HMT_SOCLE_VERSION];'),
            wait=False)
        time.sleep(0.6)
        for L in reversed(b._log_lines(300)):
            if "HMT|PV|" in L:
                _rap = L.strip()
                if "|true|" in L:  _vert = True
                if "|false|" in L: _vert = False
                break
        if _vert is not None: break
    print(f"  PREVOL : {_rap[-90:] if _rap else 'AUCUNE REPONSE'}", flush=True)
    # ⚠️ QUI EST ENCORE DEBOUT QUAND L EPISODE COMMENCE ? ⟨22/08⟩ 26 episodes natif et 31
    # politique se sont joues SANS AUCUN DEFENSEUR (61e8800), et personne ne savait a quel
    # moment ils tombaient. On le demande au jeu, avant et apres, au lieu de le supposer.
    # ⚠️ SQF NU, AUCUNE FONCTION BIS. `BIS_fnc_conditionalSelect` et `BIS_fnc_arithmeticMean`
    # peuvent manquer ou changer ; une sonde qui depend d une bibliotheque tierce peut
    # echouer en SILENCE et rendre un diagnostic vide qu on lirait comme un monde vide.
    b.send(sans_commentaires(
        'private _n = 0; private _s = 0;'
        '{ if (alive _x) then { _n = _n + 1; _s = _s + (_x distance2D HMT_OBJ) } } forEach HMT_FR;'
        'diag_log format ["HARMATTAN_APRES_PREVOL att=%1 def=%2 dmoy=%3", _n,'
        ' ({alive _x} count HMT_ENNEMI), (if (_n == 0) then {-1} else {round (_s / _n)})];'),
        wait=False)
    time.sleep(1.0)
    _ap = [L for L in b._log_lines(300) if "HARMATTAN_APRES_PREVOL" in L]
    print("  APRES PREVOL : %s" % (_ap[-1].split("HARMATTAN_APRES_PREVOL")[1].strip()[:60]
                                   if _ap else "NON RELEVE"), flush=True)
    if _vert is not True:
        b.send(sans_commentaires(
            'diag_log format ["HMT|PVE|%1", (if (isNil "HMT_PV_ECARTS") then {"(pas d ecarts : le prevol n a pas fini)"} else {HMT_PV_ECARTS})];'),
            wait=False)
        time.sleep(2.0)
        _e = [L for L in b._log_lines(300) if "HMT|PVE|" in L]
        print(f"  ECARTS : {_e[-1].strip()[-200:] if _e else 'illisibles'}", flush=True)
        print("  ⛔ PREVOL NON VERT — aucun episode ne sera joue.", flush=True)
        sys.exit(2)
    print("  ✓ prevol VERT", flush=True)

    pol = charger()
    RELEVE = []
    perc = C.perc_sqf()
    _D0 = {}        # distance de depart du candidat B, PAR IDENTIFIANT d attaquant
    print(f"\n  {'pas':>4}{'obs recues':>12}{'vivants':>9}{'def':>6}{'dmin':>7}  actions", flush=True)
    for t in range(PAS_MAX):
        b.send(sans_commentaires(perc), wait=False)
        # ATTENTION : 0,4 s ne suffisait pas. L actuateur dort 0,1 s entre deux sondages,
        # puis parcourt 21 hommes. Je declarais « aucune obs » avant que le jeu ait eu le
        # temps de repondre, et je SORTAIS a la premiere absence — sans reessayer une fois.
        # La panne etait ma patience, pas la couture.
        obs = {}
        for _ in range(12):
            time.sleep(0.25)
            obs = C.parse_obs(b._log_lines(900))
            if len(obs) >= 1: break
        if len(obs) < 1:
            print(f"  {t:>4}   AUCUNE OBS apres 3 s d attente.", flush=True)
            break
        if t == 0:
            # ⚠️ LE MEME INSTANT POUR TOUT LE MONDE. Les defenseurs retrouvent leurs
            # facultes au pas 0, dans les DEUX bras, en meme temps que l attaquant recoit
            # son premier ordre. Avant ce pas, le monde ne compte pas de morts.
            b.send(sans_commentaires(
                '{ _x allowDamage true } forEach (HMT_FR + HMT_ENNEMI);'
                '{ _x enableAI "AUTOCOMBAT"; _x enableAI "FSM"; _x setCombatMode "RED";'
                '  _x setBehaviour "COMBAT" } forEach HMT_ENNEMI;'
                'diag_log "HARMATTAN_DEFENSEURS_REVEILLES et tout le monde blessable";'),
                wait=False)
        o = torch.tensor([obs[i] for i in sorted(obs)], dtype=torch.float32)
        with torch.no_grad():
            lo, _ = pol(o[:, COLS])
        acts = lo.argmax(-1).tolist()
        if BRAS == "natif":
            acts = []                       # l IA d Arma pilote : AUCUN ordre envoye
            if t == 0:
                # ⚠️ ICI, ET PAS DANS LA SCENE. C est l instant exact ou la politique envoie
                # son premier ordre : les deux bras partent de la meme ligne.
                b.send(sans_commentaires(
                    '{ _x enableAI "AUTOCOMBAT"; _x enableAI "FSM" } forEach HMT_FR;'
                    'private _w = HMT_GA addWaypoint [HMT_OBJ, 0];'
                    '_w setWaypointType "SAD"; _w setWaypointBehaviour "COMBAT";'
                    '_w setWaypointSpeed "NORMAL";'
                    'diag_log "HARMATTAN_ORDRE_NATIF donne au pas 0";'), wait=False)
        elif BRAS == "script":
            # ═══ FEU-ET-MOUVEMENT SCRIPTE ⟨Fable, 15/08⟩ ═══
            # « Une politique fixe idiote — l un appuie pendant que l autre bondit, on
            #  alterne. Si le script ne bat pas FLANC, aucune politique posee dessus ne le
            #  battra. »  C est le proces du GESTE, a vocabulaire ferme, sans apprentissage.
            _apx = o[:, 0] * 200.0; _apy = o[:, 1] * 200.0
            _cap = lambda dx, dy: (torch.round(torch.atan2(dx, dy) / (math.pi/4.0)).long() % 8)
            _a = _cap(-_apx, -_apy)                       # tout le monde cap vers l objectif
            # une equipe bondit pendant que l autre appuie ; on echange tous les 3 pas
            _demi = max(1, len(o)//2)
            _bond_dabord = ((t // 3) % 2 == 0)
            _appui = torch.zeros(len(o), dtype=torch.bool)
            if _bond_dabord: _appui[_demi:] = True
            else:            _appui[:_demi] = True
            # on n appuie que si l ennemi est a portee utile (0,9 x portee du gymnase)
            _d = torch.sqrt(_apx**2 + _apy**2)
            _a = torch.where(_appui & (_d < 110.0*0.9), torch.full_like(_a, 9), _a)
            acts = _a.tolist()
        elif BRAS in ("b_frontale", "b_flanc", "b_arret"):
            # ═══ CANDIDAT B — TROIS MANOEUVRES FIXES ⟨pre-inscription 82101f9⟩ ═══
            # ⚠️ CE BLOC EST LE JUMEAU LITTERAL de `candidat_b_gymnase.py:manoeuvre`.
            # Meme vocabulaire (0-7 caps, 8 TENIR, 9 APPUYER), meme portee, meme demi-distance.
            # Si les deux se separent, le differentiel mesure MA divergence, pas les deux mondes.
            _apx = o[:, 0] * 200.0; _apy = o[:, 1] * 200.0
            _cap = lambda dx, dy: (torch.round(torch.atan2(dx, dy) / (math.pi/4.0)).long() % 8)
            _d = torch.sqrt(_apx**2 + _apy**2)
            # ⚠️ CLE PAR IDENTIFIANT, PAS PAR RANG. Quand un attaquant meurt, `o` retrecit :
            # `_D0[:len(_d)]` rendrait la distance de depart de l homme n°2 a l homme n°3.
            # Un realignement silencieux est exactement la faute que ce projet paie le plus cher.
            _ids = sorted(obs)
            for _k, _i in enumerate(_ids):
                if _i not in _D0:
                    _D0[_i] = float(_d[_k])           # figee au premier pas OU on le voit
            _d0v = torch.tensor([_D0[_i] for _i in _ids], dtype=torch.float32)
            _a = _cap(-_apx, -_apy)                   # tout le monde cap vers l objectif
            if BRAS == "b_flanc":
                _f = torch.zeros(len(o), dtype=torch.bool); _f[:2] = True
                _a = torch.where(_f & (_d < 110.0*0.9), torch.full_like(_a, 9), _a)
                if t < 14:
                    _a = torch.where(~_f, _cap(-_apy, _apx), _a)
            elif BRAS == "b_arret":
                _mi = _d <= (_d0v * 0.5)
                _a = torch.where(_mi, torch.full_like(_a, 8), _a)
                _a = torch.where(_mi & (_d < 110.0*0.9), torch.full_like(_a, 9), _a)
            acts = _a.tolist()
        elif BRAS == "flanc":
            # doctrine portee TELLE QUELLE de boucle.py : cap vers l objectif ; les deux
            # premiers appuient (9) sous 0,9 x portee ; les autres crochetent 14 pas.
            _apx = o[:, 0] * 200.0; _apy = o[:, 1] * 200.0      # obs = apx/S, S = terr_R
            _cap = lambda dx, dy: (torch.round(torch.atan2(dx, dy) / (math.pi/4.0)).long() % 8)
            _a = _cap(-_apx, -_apy)
            _d = torch.sqrt(_apx**2 + _apy**2)
            _f = torch.zeros(len(o), dtype=torch.bool); _f[:2] = True
            _a = torch.where(_f & (_d < 110.0*0.9), torch.full_like(_a, 9), _a)
            if t < 14:
                _a = torch.where(~_f, _cap(-_apy, _apx), _a)
            acts = _a.tolist()
        # ═══ RELEVE ⟨Fable, 14/08⟩ : on garde les 18 colonnes BRUTES telles qu Arma les
        # produit, plus les logits et l action. C est la premiere machoire. La seconde est
        # le rejeu hors-ligne : un releve seul donne un indice, le rejeu donne un verdict.
        RELEVE.append((t, o.numpy().copy(), lo.numpy().copy(), list(acts) if acts else [-1]*len(o)))
        if acts:
            b.send(sans_commentaires(C.acts_to_sqf(acts)), wait=False)
        b.send(sans_commentaires(ETAT), wait=False)
        time.sleep(0.3)
        m = None
        for L in reversed(b._log_lines(200)):
            m = re.search(r"HARMATTAN_ETAT vivants=(\d+) def=(\d+) dmin=(-?\d+)", L)
            if m: break
        if t % 5 == 0 or t == PAS_MAX - 1:
            e = (m.group(1), m.group(2), m.group(3)) if m else ("?", "?", "?")
            print(f"  {t:>4}{len(obs):>12}{e[0]:>9}{e[1]:>6}{e[2]:>7}  {acts}", flush=True)
        # ⚠️ UN EPISODE QUI COMMENCE SANS ESCOUADE N A PAS EU LIEU ⟨mesure du 21/08⟩.
        # Sur 147 episodes archives, NEUF demarrent a zero attaquant vivant — et dans les
        # neuf, la scene avait bien cree « def=4 att=4 enmain=4 ». Ils sont donc morts
        # ENTRE la scene et le premier etat, et entre les deux il n y a que le PREVOL :
        # 60 a 80 s dans un monde EVEILLE, defenseurs a 170 m. Le prevol qui certifie le
        # canal laisse le temps de tuer l escouade qu on allait mesurer.
        # ⚠️ CES EPISODES NE SONT PAS DES ECHECS : les compter comme des non-prises deprime
        # le taux — du natif comme de la politique. Ils se NOMMENT.
        if m and t == 0 and int(m.group(1)) == 0:
            print(f"\n  ⛔ ESCOUADE MORTE AVANT LE DEPART — 0 attaquant vivant au premier etat")
            print(f"     (scene creee, prevol vert : ils sont tombes pendant le prevol)")
            print(f"     CET EPISODE N A PAS EU LIEU — il ne compte ni en prise ni en echec.")
            break
        if m and (int(m.group(1)) == 0 or int(m.group(3)) >= 0 and int(m.group(3)) < 25):
            print(f"\n  fin au pas {t} : vivants={m.group(1)} dmin={m.group(3)}")
            break
        time.sleep(max(0.0, PERIODE - 0.7))
    # ⚠️ LES COMPTEURS PARLENT DANS L ARTEFACT, SINON ILS NE SERVENT A RIEN ⟨20/08⟩.
    # Ecrire un compteur qui n est jamais lu, c est la faute de la ligne GESTE qui a ecrit
    # `any` pendant trois jours. La condition 3 du predicat se leve ICI ou nulle part.
    b.send('diag_log format ["HARMATTAN_COUPS att=%1 def=%2", '
           '(if (isNil "HMT_COUPS_ATT") then {-1} else {HMT_COUPS_ATT}), '
           '(if (isNil "HMT_COUPS_DEF") then {-1} else {HMT_COUPS_DEF})];', wait=False)
    time.sleep(0.8)
    _cp = [L for L in b._log_lines(300) if "HARMATTAN_COUPS" in L]
    _cn = [L for L in b._log_lines(600) if "HARMATTAN_CANAL" in L]
    print("  COUPS  : %s" % (_cp[-1].split("HARMATTAN_COUPS")[1].strip()[:40] if _cp else "NON RELEVES"), flush=True)
    print("  CANAL  : %s" % (_cn[-1].split("HARMATTAN_CANAL")[1].strip()[:40] if _cn else "NON DECLARE"), flush=True)

    # ⚠️ REGLE 17 : le fichier porte son STATUT dans sa donnee, pas dans sa prose.
    # `montage` = aucune ligne d ici n est citable dans une lecture.
    import numpy as _np
    # ⚠️ APLATI, PAS EMPILE. Le nombre d hommes VIVANTS baisse en cours d episode (8 puis 7
    # puis moins) : `np.stack` refuse des tableaux de formes differentes. Une ligne par
    # DECISION, avec son numero de pas — c est de toute facon la forme que le rejeu emploie.
    _np.savez("/tmp/releve_live.npz", statut="montage",
              pas=_np.concatenate([_np.full(len(r[3]), r[0]) for r in RELEVE]) if RELEVE else _np.zeros(0),
              obs18=_np.concatenate([r[1] for r in RELEVE]) if RELEVE else _np.zeros((0, 18)),
              logits=_np.concatenate([r[2] for r in RELEVE]) if RELEVE else _np.zeros((0, 10)),
              actions=_np.concatenate([_np.array(r[3]) for r in RELEVE]) if RELEVE else _np.zeros(0))
    print(f"\n  RELEVE : {len(RELEVE)} pas ecrits dans /tmp/releve_live.npz (statut=montage)")
    print("\n  BANC DE MONTAGE TERMINE. Ce qu il prouve : la chaine tourne bout en bout.", flush=True)
    print("  Ce qu il ne prouve pas : aucun verdict de concordance sans repetitions.")
