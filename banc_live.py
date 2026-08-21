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
private _ga = createGroup west; HMT_FR = [];
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
        // AUCUN disableAI : l IA d Arma joue entiere, elle choisit son chemin.
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
if (HMT_BRAS == "natif") then {
    private _w = _ga addWaypoint [HMT_OBJ, 0];
    _w setWaypointType "SAD"; _w setWaypointBehaviour "COMBAT"; _w setWaypointSpeed "NORMAL";
};
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
diag_log format ["HARMATTAN_ETAT vivants=%1 def=%2 dmin=%3", _v, _ve, round _dmin];
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
    if BRAS == "natif":
        b.send(sans_commentaires(
            '{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_ENNEMI;\n'
            '{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_FR;\n'
            'HMT_POST = []; { HMT_POST pushBack 0 } forEach HMT_FR;\n'
            'diag_log "HARMATTAN_WAKE natif ok";\n'))
    else:
        b.send(sans_commentaires(C.WAKE))
    time.sleep(2)

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
        o = torch.tensor([obs[i] for i in sorted(obs)], dtype=torch.float32)
        with torch.no_grad():
            lo, _ = pol(o[:, COLS])
        acts = lo.argmax(-1).tolist()
        if BRAS == "natif":
            acts = []                       # l IA d Arma pilote : AUCUN ordre envoye
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
            m = re.search(r"HARMATTAN_ETAT vivants=(\d+) def=(\d+) dmin=(\d+)", L)
            if m: break
        if t % 5 == 0 or t == PAS_MAX - 1:
            e = (m.group(1), m.group(2), m.group(3)) if m else ("?", "?", "?")
            print(f"  {t:>4}{len(obs):>12}{e[0]:>9}{e[1]:>6}{e[2]:>7}  {acts}", flush=True)
        if m and (int(m.group(1)) == 0 or int(m.group(3)) < 25):
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
