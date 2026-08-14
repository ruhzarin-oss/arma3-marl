#!/usr/bin/env python3
"""banc_live — LA POLITIQUE APPRISE JOUE DANS ARMA.

Harnais repris de `move_combat.py`, qui marche : serveur lance avec HMT_EXT_PORT, pont TCP
natif, SQF envoye et journal lu par socket. Rien n est invente ici.

LA BOUCLE : PERC18 (18 colonnes sorties du JEU) -> selection base9+posture3 -> politique
-> 10 actions -> SQF (caps / tenir / appuyer).

⚠️ CE QUI EST DECLARE AVANT LE PREMIER PAS :
  · la politique NE SE COUCHE JAMAIS (elle n a pas les actions 10/11/12). Sur Arma, ou se
    montrer coute 4,00 DEFINITIVEMENT, c est un handicap a elle, pas au portage.
  · le monde d entrainement : 13 defenseurs, 8 attaquants, 200 m. On le reproduit.
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

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5830, 6062
MIS = "BancLive.Stratis"
LOG = SB + "/logs/serverLV.out"
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
NDEF, NATT, DIST = 13, 8, 170.0
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
private _gd = createGroup east; HMT_ENNEMI = [];
for "_i" from 1 to %d do {
    private _a = random 360; private _r = 10 + random 25;
    private _p = [(HMT_OBJ select 0) + _r * sin _a, (HMT_OBJ select 1) + _r * cos _a, 0];
    private _u = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u setSkill 0.5; _u disableAI "PATH";
    _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
    HMT_ENNEMI pushBack _u;
};
private _ga = createGroup west; HMT_FR = [];
private _az = random 360;
for "_i" from 1 to %d do {
    private _p = [(HMT_OBJ select 0) + %f * sin _az + (_i * 6),
                  (HMT_OBJ select 1) + %f * cos _az, 0];
    private _u = _ga createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u setSkill 0.5;
    // PATH coupe : c est la politique qui pilote, par setVelocity — comme au gymnase.
    _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
    _u setBehaviour "AWARE"; _u setCombatMode "BLUE"; _u setVariable ["HMT_LASTDMG", 0];
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
diag_log format ["HARMATTAN_SCENE def=%%1 att=%%2", count HMT_ENNEMI, count HMT_FR];
''' % (OBJ[0], OBJ[1], NDEF, NATT, DIST, DIST)

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
    b.send(sans_commentaires(C.WAKE))
    time.sleep(2)

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
        # ═══ RELEVE ⟨Fable, 14/08⟩ : on garde les 18 colonnes BRUTES telles qu Arma les
        # produit, plus les logits et l action. C est la premiere machoire. La seconde est
        # le rejeu hors-ligne : un releve seul donne un indice, le rejeu donne un verdict.
        RELEVE.append((t, o.numpy().copy(), lo.numpy().copy(), list(acts)))
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
