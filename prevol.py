#!/usr/bin/env python3
"""prevol.py — LA PORTE DU PREVOL.

⟨Fable, 16/08⟩ La porte n est pas 50 EPISODES, c est 50 TIRAGES DU PREVOL. Un tirage dure
une vingtaine de secondes et le prevol cree puis detruit ses propres hommes : on les
enchaine donc sur UN serveur, ce qui ramene la porte de deux heures a une vingtaine de
minutes. Le serveur n est relance a aucun moment — si sa duree de vie devenait le sujet,
ce serait un autre banc.

  prevol.py <nb_tirages> [normal|sabotage]

CRITERES ⟨poses avant, et separement de tout resultat⟩
  · CONTROLE POSITIF, EN PREMIER — en mode `sabotage`, les munitions du temoin sont
    retirees et T4 DOIT rougir. Si le sabotage ne fait rien rougir, la porte ne mesure
    rien et TOUT S ARRETE : on ne lit aucun tirage normal.
  · LA PORTE — 50 tirages, 2 echecs tolerables (5 %), coupure au 3e.
"""
import sys, os, time, subprocess, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
import arma_couture as C
# ⚠️ LA SCENE VIT DANS `banc_live.py`, pas dans la couture. On l IMPORTE au lieu de la
# recopier : deux scenes qui derivent l une de l autre, c est deux mondes qu on croit pareils.
from banc_live import SCENE, sans_commentaires

N    = int(sys.argv[1]) if len(sys.argv) > 1 else 50
MODE = sys.argv[2] if len(sys.argv) > 2 else "normal"
# ⚠️ LE DELAI D ECHAUFFEMENT EST UN PARAMETRE, PAS UNE CONSTANTE. Mesure du 16/08 : les
# echecs de T5 se concentrent aux tirages 1-3 d une session (4 m, 10 m, puis 18-24 m sur
# les quatorze suivants), et la nuit tirait son prevol 48 s apres un serveur NEUF a chaque
# episode — toujours dans la zone froide, d ou 70 % de rouges contre 4 % a la porte.
CHAUD = int(sys.argv[3]) if len(sys.argv) > 3 else 45
SB   = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5830, 6062
LOG  = SB + "/logs/serverPV%s.out" % (os.environ.get("HMT_SESSION", ""))
OBJ, NDEF, NATT, DIST = (4644.0, 5652.0), 4, 4, 170.0
MAX_ECHECS = 2

def sh(c): subprocess.run(c, shell=True, executable="/bin/bash")

if __name__ == "__main__":
    C.CX, C.CY = OBJ; C.SCALE = 200.0; C.FIRE_RANGE = 110.0; C.MOVE_SPD = 6.0
    open(LOG, "w").close()
    # ⚠️ ON NE TUE QUE CE QU ON A LANCE ⟨cliquet du 17/08, machine PARTAGEE⟩. `pgrep -f
    # arma3server_x64` tue tout serveur x64 de la machine, y compris ceux d une autre session.
    MES_PIDS = []
    def tuer_les_miens():
        for pid in MES_PIDS: subprocess.run("kill %d 2>/dev/null" % pid, shell=True)
        MES_PIDS.clear()
    tuer_les_miens(); time.sleep(4)
    print("  serveur...", flush=True)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    print('  echauffement : %d s' % CHAUD, flush=True)
    time.sleep(2)
    MES_PIDS.extend(int(x) for x in subprocess.run(
        "pgrep -f arma3server_x64", shell=True, capture_output=True, text=True).stdout.split())
    print("  mes serveurs : %s" % MES_PIDS, flush=True)
    time.sleep(max(CHAUD - 2, 0))
    b = SocketBridge(EXT); time.sleep(3)
    # ⚠️ LE SOCLE AVANT LA SCENE. La scene appelle `HMT_CERTIFIER_POSITIONS`, definie
    # dans le socle : envoyee avant, elle plantait a chaque appel — 38 erreurs par lot,
    # certification a vide, hommes nes NON certifies. Le bloc C n avait jamais tourne.
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(3)
    b.send(sans_commentaires(SCENE), wait=False)
    # ⚠️ ATTENTE DE LA SCENE, DERIVEE DE SON COUT REEL. Le bloc C certifie chaque
    # position par des ACTES (pose 2 s + traverse 4 s + tir 4 s) : jusqu a 6 essais
    # d azimut pour les 8 attaquants, puis jusqu a 8 essais par defenseur. Pire cas
    # ~460 s. Un `sleep(6)` laissait la scene inachevee et faisait croire a son absence.
    # ⚠️ ANGLE MORT DECLARE : ce plafond ne distingue pas une scene LENTE d une scene
    # MORTE ; les rejets de position sont journalises (`SCENE_POS`, `SCENE_AZ`) et c est
    # la qu on lira laquelle des deux.
    _t_sc = time.time(); _sc = []
    while time.time() - _t_sc < 480:
        _sc = [L for L in b._log_lines(600) if 'HARMATTAN_SCENE' in L]
        if _sc: break
        time.sleep(5)
    print('  scene : %s  (%.0f s)' % (_sc[-1][-42:] if _sc else 'AUCUNE en 480 s',
          time.time() - _t_sc), flush=True)
    time.sleep(6)
    lg = [L for L in b._log_lines(400) if "HARMATTAN_SCENE" in L]
    print("  scene : %s" % (lg[-1][-40:] if lg else "AUCUNE — on n ira pas plus loin"), flush=True)
    if not lg: sys.exit(1)
    # ⚠️ LES QUATRE SABOTAGES doivent etre rejoues sur le hash que la porte certifie
    # ⟨ligne 4 du critere⟩. « sabotage » vide les munitions du temoin de T4 ; « jambes »
    # retire `PATH` au temoin de T5. Les deux du placeur (traverse, tir) passent par le smoke.
    # ⚠️ QUATRIEME LEVIER NE SANS CHEMIN D EXECUTION ⟨Fable, 18/08⟩. « gel » et « lenteur »
    # etaient ecrits dans le socle et absents de cette table : le mode envoyait `""`, et les
    # deux branches neuves ne s executaient JAMAIS. L arbre syntaxique ne voit pas la couture
    # Python -> SQF ; cote SQF, le seul arbre est l EXECUTION.
    _sab = {"sabotage": "munitions", "jambes": "jambes",
            "gel": "gel", "lenteur": "lenteur"}.get(MODE, "")
    b.send('HMT_SABOTER = "%s";' % _sab, wait=False)
    time.sleep(1)
    # Le reveil fait partie du monde. `banc_live.py natif` l envoie ENTRE la scene et le
    # prevol ; la porte du 16/08 n en envoyait aucun, et c est pour ca qu elle a certifie
    # un monde que la nuit ne jouait pas.
    WAKE_NATIF = ('{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_ENNEMI;\n'
                  '{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_FR;\n'
                  'HMT_POST = []; { HMT_POST pushBack 0 } forEach HMT_FR;\n')
    if MODE == "natif":
        b.send(sans_commentaires(WAKE_NATIF), wait=False); time.sleep(2)
        print("  reveil NATIF envoye — regime de la nuit", flush=True)
    # ⚠️ LE GARDIEN DE VERSION ⟨Fable, 18/08⟩. La version circulait dans chaque reponse et
    # python n en lisait que le vrai/faux : « une porte certifie UN hash » n avait AUCUN
    # mecanisme d execution, seulement une discipline de recopie — qui avait deja lache, le
    # `mpmissions/*/socle.sqf` du DEPOT etant reste a 1.13.0 quand le canonique etait a 2.8.0.
    VERSION_ATTENDUE = subprocess.run(
        "grep -o 'HMT_SOCLE_VERSION = .[^\"]*.' /home/younes/arma3-marl/bancs/socle/socle.sqf",
        shell=True, capture_output=True, text=True).stdout.strip().split('"')[1]
    b.send('diag_log format ["HMT|VER|%1", HMT_SOCLE_VERSION];', wait=False); time.sleep(1.2)
    _v = [L for L in b._log_lines(120) if "HMT|VER|" in L]
    VERSION_MONDE = (_v[-1].split("HMT|VER|")[1].strip().strip('"')[:22] if _v else "AUCUNE")
    print("  socle attendu  : %s" % VERSION_ATTENDUE, flush=True)
    print("  socle DU MONDE : %s" % VERSION_MONDE, flush=True)
    if VERSION_MONDE != VERSION_ATTENDUE:
        print("  ⛔ VERSION DU MONDE != ATTENDUE — PANNE NOMMEE, pas un tirage rouge.", flush=True)
        tuer_les_miens(); sys.exit(7)
    print("  socle charge — mode %s, %d tirages" % (MODE, N), flush=True)

    # `callExtension "version"` rend « hmt_native 1.2 | <etat> | jetes ring=N send=N ligne=N ».
    # Le bind est hors de cause : s il avait echoue, le pont ne se serait pas connecte et la
    # session aurait AVORTE — or les mortes creaient bien leur scene. On mesure les JETES.
    def pont(quand):
        b.send('diag_log format ["HMT|PONT|%s|%%1", ("hmt_native" callExtension "version")];' % quand, wait=False)
        time.sleep(1.2)
        ls = [L for L in b._log_lines(150) if "HMT|PONT|" + quand in L]
        e = ls[-1].split("HMT|PONT|")[1][:120].rstrip('"') if ls else quand + "|AUCUNE REPONSE"
        print("  pont %s" % e, flush=True)
        return e
    pont("debut")

    verts, ech, det = 0, 0, []
    ecartes = 0
    sansrep = 0                      # REVUE 17/08 : les pannes de pont, comptees A PART
    # ⚠️ LES CINQ LIEUX SONT ALTERNES DANS LA MEME SESSION. C est le point du protocole :
    # si les lieux morts echouent et les vivants passent COTE A COTE sous le meme serveur,
    # l effet de session est elimine comme explication concurrente.
    LIEUX = [("mort_4989_5877", 4989, 5877), ("vif_4776_5196", 4776, 5196),
             ("mort_4716_5207", 4716, 5207), ("vif_4445_6138", 4445, 6138),
             ("mort_4210_5369", 4210, 5369)]
    for i in range(1, N + 1):
        if MODE == "lieux":
            nom, lx, ly = LIEUX[(i - 1) % len(LIEUX)]
            b.send('HMT_LIEU_FORCE = [%d, %d];' % (lx, ly), wait=False); time.sleep(0.6)
            print("  lieu force : %s" % nom, flush=True)
        if MODE == "compare":
            b.send(sans_commentaires(WAKE_NATIF if i % 2 else C.WAKE), wait=False); time.sleep(2)
        # ⚠️ ON N ENCHAINE JAMAIS SUR UN PREVOL NON TERMINE — seconde moitie du correctif A2,
        # que je n avais pas posee. Le jeton de generation empeche bien deux prevols d ecrire
        # ensemble, mais si python lance le suivant, le precedent ABANDONNE et rend `false`
        # SANS ecart. Lot 1 de la porte du 17/08 : cinq echecs a ecart vide, en cascade apres
        # un seul « PREVOL LENT ». Un tirage dont l INSTRUMENT n a pas fini n est pas un echec
        # DU MONDE : on attend la fin, et si l attente expire on ECARTE le tirage.
        for _att in range(30):
            b.send('diag_log format ["HMT|FIN|%1", HMT_PV_ETAPE];', wait=False); time.sleep(0.6)
            _f = [L for L in b._log_lines(80) if "HMT|FIN|" in L]
            _et = _f[-1].split("HMT|FIN|")[1][:20].strip().strip('"') if _f else ""
            if _et in ("fini", "neant", ""): break
            time.sleep(1.4)
        # ⚠️ LE VERDICT PORTE DESORMAIS L IDENTITE DE CELUI QUI L A PRODUIT ⟨20/08⟩.
        # Cause mesuree : le sabotage `gel` ne plantait plus que 1 fois sur 3. Le premier
        # tirage gele correctement, python rompt sur figement et lance le suivant — mais le
        # prevol GELE finit par se reveiller et ecrit son `false` dans `HMT_PV`, la meme
        # case que le tirage courant vient de remettre a nil. Le tirage 2 lisait donc le
        # verdict du tirage 1 : 27 s, ecarts vides. Le tirage 3 pareil, en 5 s.
        # Le jeton de generation existait deja, mais il ne gardait que les POINTS DE
        # CONTROLE — et un prevol gele n en atteint aucun, puisque c est ce que le gel lui
        # fait. La garde manquait la ou elle comptait : au moment de DEPOSER le verdict.
        # ⚠️ `_att` est capture DANS le spawn, pas dans une globale : une globale serait
        # ecrasee par le lancement suivant et la garde laisserait tout passer.
        b.send('HMT_PV = nil; '
               'private _att = (missionNamespace getVariable ["HMT_PV_GEN", 0]) + 1; '
               '[_att] spawn { params ["_att"]; '
               '  private _r = [HMT_FR] call HMT_PREVOL; '
               '  if ((missionNamespace getVariable ["HMT_PV_GEN", 0]) == _att) then { HMT_PV = _r } '
               '  else { (format ["HMT|SOCLE|PREVOL|VERDICT_TU|gen|%1|courante|%2|valeur|%3", '
               '                  _att, missionNamespace getVariable ["HMT_PV_GEN", 0], _r]) call HMT_LOG }; '
               '};', wait=False)
        # ⚠️ TIMEOUT PAR ETAPE ⟨lecture de Fable⟩. Le plafond etait GLOBAL contre un prevol
        # de duree VARIABLE : au depassement on enchainait sur un prevol encore vivant. On
        # suit desormais `HMT_PV_ETAPE` — tant qu elle AVANCE on attend, si elle STAGNE c est
        # un plante, si elle ne repond pas du tout c est le pont. Trois causes, trois causes
        # nommees, au lieu d un « muet » indistinct qui mangeait 17 % de la mesure.
        # ⚠️ PATIENCE-AU-PROGRES ⟨Fable, 18/08⟩. Le commentaire ci-dessous promettait deja un
        # timeout PAR ETAPE ; la boucle etait restee un plafond GLOBAL de 40 sondages, seule
        # l ETIQUETTE etant devenue par-etape. Troisieme fois du jour qu un ecrit temoigne
        # d un acte qui n a pas eu lieu.
        # ⚠️ ET LA FORME COMPTE : l anneau de 24 candidats est FIXE PAR SESSION, donc un
        # plafond global convertit la pauvrete d un anneau en echecs REGROUPES par session —
        # le destin de session, gueri dans le canal du VERDICT, renaitrait dans celui du
        # TEMPS. Mesure de la nuit : les 4 echecs sont les 4 tirages les plus chers (15, 12,
        # 9, 9 candidats) et 8 candidats passent quand 9 tombent.
        # On attend tant que l ETAPE **ou** le NUMERO DE CANDIDAT avance ; 12 sondages sans
        # progres (~26 s, au-dessus du plus long acte legitimement silencieux — la fenetre
        # T4 de 2+12 s) → PLANTE. BORNE EXTERIEURE derivee du mecanisme : le socle declare
        # ~30 s fixes + ~5,5 s par candidat, 24 candidats au plus, soit ~160 s → 180 s avec
        # marge. Au-dela, le prevol depasse ce qu il PEUT couter : c est un bug.
        # ⚠️ ANGLE MORT DECLARE ⟨regle 20⟩ : un vrai gel coute jusqu a 26 s a detecter, et le
        # garde-fou des trois sans-reponse tombe plus tard dans la vie du pont (mort en 20-40 min).
        BORNE_EXT = 180.0
        r = None; etape = None; ncand = -1; fige = 0; _fige_break = False
        _t_deb = time.time(); _chrono = {}
        # REVUE 17/08 : on lisait la DERNIERE ligne `HMT|PV|` du tampon, sans borne de
        # fraicheur. Sur serveur charge, une ligne du tirage PRECEDENT (true/false, jamais
        # « attente ») validait le tirage courant en 2 s pendant que son propre prevol
        # tournait encore — les deux se superposaient sur les globales HMT_PV_COUPS.
        # La reponse porte desormais le NUMERO du tirage.
        _tag = "HMT|PV|%d|" % i
        while time.time() - _t_deb < BORNE_EXT:
            time.sleep(1.5)
            if not getattr(b, "alive", True):
                break
            b.send('diag_log format ["HMT|PV|%d|%%1|%%2", (if (isNil "HMT_PV") then {"attente"} else {HMT_PV}), HMT_SOCLE_VERSION];' % i, wait=False)
            time.sleep(0.4)
            b.send('diag_log format ["HMT|ET|%1", HMT_PV_ETAPE];', wait=False)
            time.sleep(0.3)
            _e = [L for L in b._log_lines(120) if "HMT|ET|" in L]
            _cur = _e[-1].split("HMT|ET|")[1][:20].strip().strip('"') if _e else None
            b.send('diag_log format ["HMT|NC|%1", (missionNamespace getVariable ["HMT_PV_NCAND", -1])];', wait=False)
            time.sleep(0.25)
            _nc = [L for L in b._log_lines(120) if "HMT|NC|" in L]
            try: _cn = int(re.sub(r"\D", "", _nc[-1].split("HMT|NC|")[1][:6]) or "-1") if _nc else -1
            except Exception: _cn = -1
            if _cur != etape and _cur is not None: _chrono[etape] = round(time.time() - _t_deb, 1)
            if _cur == etape and _cn == ncand: fige += 1
            else: etape, ncand, fige = _cur, _cn, 0
            # ⚠️ SANS CE `break`, PLANTE N EXISTAIT PAS ⟨Fable⟩. La stagnation ne faisait
            # qu ETIQUETER a l expiration de la borne : un gel de 60 s se reveillait, finissait
            # vers 120-140 s, et rendait VERT. Mon message annoncait « 12 sondages sans progres
            # -> PLANTE » — cinquieme ecrit du jour decrivant un acte que le code ne fait pas,
            # dans l annonce meme du correctif de cette famille.
            # ⚠️ MARGE DECLAREE ⟨regle 20⟩ : le plus long silence LEGITIME est l etape T4
            # entiere — reveal 2 s + fenetre de tir 12 s + suppression + sleep 1 + sleep 0,5
            # ≈ 17 s. Un sondage coute ~2,5-3 s reels (1,5+0,4+0,3+0,25 et les lectures), donc
            # 12 sondages ≈ 30-36 s : marge ~2x. Si la charge serveur etire T4 au-dela de 2x,
            # c est un FAUX PLANTE, et le `fps` que T5 journalise deja en est le temoin.
            if fige >= 12:
                _fige_break = True
                break
            ls = [L for L in b._log_lines(200) if _tag in L]
            if ls and "attente" not in ls[-1]:
                r = "true" in ls[-1].split(_tag)[1][:6]; break
        if r is None:
            # REVUE 17/08 : « SANS REPONSE » entrait dans le MEME compteur que les vrais
            # rouges, puis « PORTE TOMBEE » (exit 4) : une panne du pont etait rendue
            # comme un verdict sur la tactique. Elle est comptee a part.
            # l etiquette nommait l etape ou l HORLOGE expire, pas celle ou le TEMPS
            # s est depense ⟨Fable⟩ : on joint les horodatages par etape.
            _hist = " ".join("%s@%ss" % (k, v) for k, v in _chrono.items() if k)
            # PLANTE se decide sur la STAGNATION ; LENT devient exclusivement le
            # depassement de la borne exterieure — « le prevol avance au-dela de son propre
            # maximum », qui est un bug et le dit.
            cause = ("SANS REPONSE / PONT MUET (aucune etape lue)" if etape is None else
                     ("SANS REPONSE / PREVOL PLANTE a l etape %s cand %s [%s]" % (etape, ncand, _hist) if _fige_break
                      else "SANS REPONSE / PREVOL LENT, etape %s cand %s [%s]" % (etape, ncand, _hist)))
            sansrep += 1; det.append((i, cause))
        elif r:
            verts += 1
        else:
            ech += 1
            b.send('diag_log format ["HMT|PVE|%1", (if (isNil "HMT_PV_ECARTS") then {"?"} else {HMT_PV_ECARTS})];', wait=False)
            time.sleep(0.6)
            # ⚠️ UN PREVOL ABANDONNE N EST PAS UN ECHEC DU MONDE. Le socle journalise
            # « HMT|SOCLE|PREVOL|ABANDONNE » quand une generation plus recente l a double.
            # Ces tirages sortent du compte au lieu de charger la porte a tort.
            _ab = [L for L in b._log_lines(200) if "PREVOL|ABANDONNE" in L]
            if _ab and (i, "ABANDONNE") not in det:
                ech -= 1; ecartes += 1; det.append((i, "ECARTE / prevol abandonne (generation doublee)"))
                print("    %2d/%d  ECARTE — prevol abandonne" % (i, N), flush=True)
                continue
            e = [L for L in b._log_lines(200) if "HMT|PVE|" in L]
            det.append((i, e[-1].split("HMT|PVE|")[1][:110] if e else "?"))
        # ⚠️ LA DUREE SE JOURNALISE TOUJOURS ⟨18/08⟩. `_chrono` n etait imprime que dans le
        # message d ECHEC : un run sans echec ne laissait AUCUNE trace de temps, et le critere
        # « duree > 90 s » du controle de lenteur devenait illisible. Deux verts sans temoin
        # ne prouvent rien — c est l ecrit qui temoigne d un acte que rien n observe, la faute
        # de la journee, cette fois sur ma propre instrumentation.
        _duree = round(time.time() - _t_deb, 1)
        _etapes = " ".join("%s@%ss" % (k, v) for k, v in _chrono.items() if k)
        print("    %2d/%d  %5.1fs  [%s]" % (i, N, _duree, _etapes), flush=True)
        print("    %2d/%d  vert=%d  echec=%d%s" % (i, N, verts, ech,
              ("   ← " + det[-1][1][:70]) if det and det[-1][0] == i else ""), flush=True)
        # ⚠️ LE GARDE-FOU NE S APPLIQUE PAS AUX SABOTAGES D INSTRUMENT ⟨19/08⟩. « gel »
        # FABRIQUE des prevols plantes : c est sa raison d etre. Le garde-fou generique
        # coupait a `sansrep >= 3` AVANT que le verdict du gel puisse lire ses PLANTE — le
        # controle positif reussissait (PLANTE 3/3 a l etape T4) et etait PUNI pour avoir
        # produit exactement ce qu on lui demandait. Un controle qui fabrique une panne doit
        # pouvoir l OBSERVER. Enonce sans reference a aucun resultat.
        if sansrep >= 3 and MODE not in ("gel", "lenteur"):
            print("\n  ⛔ TROIS TIRAGES SANS REPONSE — causes MELEES (pont, lent, plante).\n     Le compteur ne les distingue pas : il nomme ce qu'il compte, pas une cause.\n     AUCUN verdict n'est rendu sur la tactique.", flush=True)
            sys.exit(5)
        if MODE == "normal" and ech > MAX_ECHECS:
            print("\n  ⛔ COUPURE AU %dE ECHEC — la porte tombe, la nuit reste vide." % ech, flush=True); break
    pont("fin")
    tuer_les_miens()

    print("\n  ── %d tirages : %d verts, %d echecs, %d sans reponse ──"
          % (verts + ech + sansrep, verts, ech, sansrep), flush=True)
    if MODE == "gel":
        # ⚠️ SANS CETTE BRANCHE, UN RUN GEL SERAIT TOMBE DANS `else` ET AURAIT IMPRIME
        # « PORTE TENUE » : le cas echouant rendu comme un SUCCES, structure exacte du
        # `clamp(min=1)` de la revue. Le gel DOIT rendre PLANTE 3 fois sur 3.
        _pl = [d for _, d in det if "PLANTE" in d]
        print("\n  PLANTE : %d sur %d tirages" % (len(_pl), verts + ech + sansrep))
        for _, d in det: print("     %s" % d[:150])
        if len(_pl) < 3:
            print("  ⛔ LE GEL NE FAIT PAS PLANTER — le detecteur de la ligne 2 est infirme."); sys.exit(8)
        if not all("T4" in d for d in _pl):
            print("  ⛔ PLANTE detecte, mais PAS a l etape T4 — l instrument nomme mal l etage."); sys.exit(9)
        print("  ✓ gel : PLANTE 3/3 a l etape T4 — le detecteur de la ligne 2 fonctionne")
        sys.exit(0)
    if MODE == "lenteur":
        # la lenteur ne doit RIEN faire rougir : elle allonge sans figer.
        _d = [float(x) for x in re.findall(r"@([\d.]+)s", " ".join(d for _, d in det))] or [0.0]
        print("\n  verts %d / rouges %d / sans reponse %d" % (verts, ech, sansrep))
        # ⚠️ CE CONTROLE JUGE LA PATIENCE, PAS LE MONDE ⟨regle 6⟩. Mon critere comptait TOUT
        # rouge comme un echec, or un refus du monde (T2 chargeur vide, T4 sans balle) n a
        # aucun rapport avec la propriete testee : la patience-au-progres. Le critere se
        # RESSERRE sur ce qu il teste — zero SANS REPONSE — et le verdict du monde est note
        # a part. Enonce sans reference a aucun resultat.
        if sansrep > 0:
            print("  ⛔ LA LENTEUR FAIT PLANTER — la patience ne suit pas le progres."); sys.exit(10)
        if ech > 0:
            print("  ⚠️ %d refus DU MONDE (hors sujet pour ce controle) : %s"
                  % (ech, "; ".join(d[:70] for _, d in det)), flush=True)
        print("  ✓ lenteur : VERT %d/%d sous patience-au-progres" % (verts, verts))
        sys.exit(0)
    if MODE in ("sabotage", "jambes"):
        if ech == 0:
            print("  ⛔ LE SABOTAGE N A RIEN FAIT ROUGIR. La porte ne mesure rien. ARRET TOTAL."); sys.exit(2)
        _cible = "T4" if MODE == "sabotage" else "T5"
        rouges_t4 = sum(1 for _, d in det if _cible in d)
        print("  ✓ le sabotage fait rougir : %d echecs, dont %d sur %s" % (ech, rouges_t4, _cible))
        if rouges_t4 == 0:
            print("  ⛔ mais AUCUN sur %s — ce n est pas la panne qu on a fabriquee. ARRET." % _cible); sys.exit(3)
    else:
        if ech > MAX_ECHECS: print("  ⛔ PORTE TOMBEE (%d echecs > %d)" % (ech, MAX_ECHECS)); sys.exit(4)
        print("  ✓ PORTE TENUE : %d echecs sur %d, seuil %d" % (ech, verts + ech, MAX_ECHECS))
    for i, d in det: print("     tirage %2d : %s" % (i, d))
