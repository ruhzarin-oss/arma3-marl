#!/usr/bin/env python3
"""capture_tail.py — suit le journal d une instance et ecrit le corpus en JSONL.

Le SQF ecrit des lignes prefixees HMT| dans le journal du serveur. Ce programme les suit, les
reassemble et les ecrit proprement. Il ne juge RIEN : ni segmentation, ni audit, ni filtrage.
La lecture est faite par d autres programmes, sur des criteres figes.

Pourquoi le journal et pas le pont : le pont TCP meurt en service (mutisme apres 20-40 min,
mesure chez nous). Le journal survit a tout ce qui tue le pont.

Sorties, par instance et par session :
  <racine>/<instance>/<horodatage>/state.jsonl    un objet par tick d etat
  <racine>/<instance>/<horodatage>/events.jsonl   un objet par evenement
  <racine>/<instance>/<horodatage>/meta.json      dt nominal et observe, trous, sante

Usage : capture_tail.py --journal <fichier> --instance <n> [--dt 0.2] [--racine ...]
"""
import argparse, json, os, re, sys, time

ap = argparse.ArgumentParser()
ap.add_argument('--journal', required=True, help='journal du serveur a suivre')
ap.add_argument('--instance', type=int, required=True)
ap.add_argument('--dt', type=float, default=0.2, help='cadence nominale annoncee au SQF')
ap.add_argument('--racine', default='/mnt/data2/lab/replay/openworld')
ap.add_argument('--horodatage', default=None, help='nom de session (defaut : maintenant)')
a = ap.parse_args()

SESSION = a.horodatage or time.strftime('%Y%m%d_%H%M%S')
DOSSIER = os.path.join(a.racine, 'inst%d' % a.instance, SESSION)
os.makedirs(DOSSIER, exist_ok=True)
F_ETAT = open(os.path.join(DOSSIER, 'state.jsonl'), 'a', buffering=1)
F_EVT = open(os.path.join(DOSSIER, 'events.jsonl'), 'a', buffering=1)
F_META = os.path.join(DOSSIER, 'meta.json')

RX = re.compile(r'HMT\|(.*)$')
CHAMPS_EVT = {
    'spawn':   ['t', 'id', 'x', 'y', 'z', 'side'],
    'despawn': ['t', 'id'],
    'fired':   ['t', 'shooter', 'proj'],
    'hit':     ['t', 'target', 'shooter', 'dmg'],
    'killed':  ['t', 'victim', 'killer'],
}
ENTIERS = {'id', 'side', 'shooter', 'proj', 'target', 'victim', 'killer'}

etat = {
    'instance': a.instance, 'session': SESSION, 'dt_nominal': a.dt,
    'ticks': 0, 'evenements': 0, 'lignes_illisibles': 0,
    'trous_tick': [], 'morceaux_orphelins': 0, 'ok': [], 'cout': [],
    'dt_observe': None, 'premier_t': None, 'dernier_t': None,
    'demarre': time.time(), 'coupures': [],
    'bascules_journal': [], 'impacts_doublons': 0, 'morts_doublons': 0,
    # EMPREINTE DU MONDE. Trou de la specification d origine : l audit verifiait que l instrument
    # mentait peu, jamais que deux corpus mesuraient le MEME monde logiciel. Le 30/07 la ferme a
    # tourne sans aucun mod alors que l instance de mesure tourne avec le jeu complet, et l accord
    # zero contre zero a ete pris pour un accord. L audit refusera de fusionner deux sessions
    # d empreintes differentes.
    'monde': None,
}
_hits_vus = {}


def empreinte_monde(journal):
    """sha256 de la ligne de mods du processus qui ecrit ce journal. Sans elle, deux corpus de
    mondes differents se ressemblent."""
    import hashlib, subprocess
    try:
        cfg = os.path.basename(journal).replace('.out', '')
        out = subprocess.run(['pgrep', '-af', 'arma3server_x64'], capture_output=True,
                             text=True, timeout=10).stdout
        for l in out.splitlines():
            if cfg in l:
                mods = ' '.join(x for x in l.split() if x.startswith(('-mod=', '-serverMod=')))
                return {'mods': mods, 'sha256': hashlib.sha256(mods.encode()).hexdigest()[:16]}
    except Exception:
        pass
    return {'mods': None, 'sha256': None}
# un tick peut arriver en plusieurs morceaux numerotes : on assemble avant d ecrire
en_cours = {'tick': None, 'morceaux': {}, 'n_total': None, 't': None}
dernier_tick = None
ecarts = []


def sauver_meta():
    e = dict(etat)
    if ecarts:
        s = sorted(ecarts)
        e['dt_observe'] = round(s[len(s) // 2], 4)
        e['dt_p95'] = round(s[int(0.95 * (len(s) - 1))], 4)
    e['duree_s'] = round(time.time() - etat['demarre'], 1)
    json.dump(e, open(F_META, 'w'), indent=1)


def vider_tick():
    """Ecrit le tick assemble. Un tick dont un morceau manque est ecrit QUAND MEME, avec le
    drapeau 'incomplet' : c est au programme d audit de decider quoi en faire, pas a moi."""
    global en_cours
    if en_cours['tick'] is None:
        return
    idx = sorted(en_cours['morceaux'])
    complet = (idx == list(range(len(idx))))
    ents = []
    mauvais = 0
    for i in idx:
        try:
            ents.extend(json.loads(en_cours['morceaux'][i]))
        except Exception:
            mauvais += 1
    if mauvais:
        etat['morceaux_orphelins'] += mauvais
    F_ETAT.write(json.dumps({
        't': en_cours['t'], 'tick': en_cours['tick'], 'n_total': en_cours['n_total'],
        'ents': ents, 'incomplet': (not complet) or bool(mauvais),
    }, separators=(',', ':')) + '\n')
    etat['ticks'] += 1
    en_cours = {'tick': None, 'morceaux': {}, 'n_total': None, 't': None}


def traiter(corps):
    global dernier_tick
    p = corps.split('|')
    genre = p[0]
    if genre == 'S':
        # HMT|S|tick|seq|t|n_total|[[...],...]
        tick, seq, t, n = int(p[1]), int(p[2]), float(p[3]), int(p[4])
        charge = '|'.join(p[5:])
        if en_cours['tick'] is not None and en_cours['tick'] != tick:
            vider_tick()
        if en_cours['tick'] is None:
            en_cours['tick'] = tick; en_cours['t'] = t; en_cours['n_total'] = n
            if dernier_tick is not None:
                if tick != dernier_tick + 1:
                    etat['trous_tick'].append([dernier_tick, tick])
                if etat['dernier_t'] is not None:
                    ecarts.append(t - etat['dernier_t'])
            dernier_tick = tick
            if etat['premier_t'] is None:
                etat['premier_t'] = t
            etat['dernier_t'] = t
        en_cours['morceaux'][seq] = charge
    elif genre == 'E':
        nom = p[1]
        noms = CHAMPS_EVT.get(nom)
        if not noms:
            etat['lignes_illisibles'] += 1
            return
        vals = p[2:2 + len(noms)]
        if len(vals) != len(noms):
            etat['lignes_illisibles'] += 1
            return
        o = {'evt': nom}
        for k, v in zip(noms, vals):
            o[k] = int(float(v)) if k in ENTIERS else float(v)
        # DEDOUBLONNAGE DES IMPACTS. Le capteur rend UNE entree par partie du corps touchee, donc
        # plusieurs lignes pour une SEULE balle. Sans ca le denominateur de coups portes est gonfle
        # et le taux de morts tracees EMBELLI : un audit qui se flatte. On garde le premier impact
        # d un triplet (cible, tireur, meme instant) et on compte les doublons ecartes.
        # Le gestionnaire de mort se declenche parfois DEUX FOIS pour la meme entite (constate le
        # 31/07 : 2 morts pour un seul homme). On dedoublonne par victime, sinon le denominateur
        # du taux de morts non tracees est faux.
        if nom == 'killed':
            cle = ('k', o['victim'])
            if cle in _hits_vus:
                etat['morts_doublons'] += 1
                return
            _hits_vus[cle] = True
        if nom == 'hit':
            cle = (o['target'], o['shooter'], round(o['t'], 2))
            if cle in _hits_vus:
                etat['impacts_doublons'] += 1
                return
            _hits_vus[cle] = True
            if len(_hits_vus) > 20000:
                for k2 in list(_hits_vus)[:10000]:
                    del _hits_vus[k2]
        F_EVT.write(json.dumps(o, separators=(',', ':')) + '\n')
        etat['evenements'] += 1
    elif genre == 'OK':
        etat['ok'].append('|'.join(p[1:]))
        print('  OK %s' % '|'.join(p[1:]), flush=True)
    elif genre == 'C':
        etat['cout'].append('|'.join(p[1:]))
    else:
        etat['lignes_illisibles'] += 1


etat['monde'] = empreinte_monde(a.journal)
def rouler(motif, quand):
    """Ferme la session en cours et en ouvre une neuve. Les deux restent sur le disque : aucune
    donnee n est perdue, elles sont seulement separees comme les mondes distincts qu elles sont."""
    global F_ETAT, F_EVT, F_META, DOSSIER, dernier_tick, en_cours, etat, _hits_vus
    F_ETAT.close(); F_EVT.close()
    n = etat.get('rang', 1) + 1
    DOSSIER = os.path.join(a.racine, 'inst%d' % a.instance, '%s_r%d' % (SESSION, n))
    os.makedirs(DOSSIER, exist_ok=True)
    F_ETAT = open(os.path.join(DOSSIER, 'state.jsonl'), 'a', buffering=1)
    F_EVT = open(os.path.join(DOSSIER, 'events.jsonl'), 'a', buffering=1)
    F_META = os.path.join(DOSSIER, 'meta.json')
    dernier_tick = None
    en_cours = {'tick': None, 'morceaux': {}, 'n_total': None, 't': None}
    _hits_vus = {}
    del ecarts[:]
    etat = dict(etat, ticks=0, evenements=0, lignes_illisibles=0, trous_tick=[],
                morceaux_orphelins=0, ok=[], cout=[], dt_observe=None, premier_t=None,
                dernier_t=None, demarre=quand, coupures=[], bascules_journal=[],
                impacts_doublons=0, morts_doublons=0, rang=n,
                origine='journal %s a %.0f' % (motif, quand))
    etat['monde'] = empreinte_monde(a.journal)
    print('  -> session %s' % DOSSIER, flush=True)


etat['rang'] = 1
print('=== lecteur de capture : instance %d -> %s ===' % (a.instance, DOSSIER), flush=True)
print('  empreinte du monde : %s' % (etat['monde']['sha256'] or 'INCONNUE'), flush=True)
if not etat['monde']['sha256']:
    sys.exit('REFUS : empreinte du monde introuvable. Un corpus sans identite de monde est inutilisable.')
if not os.path.exists(a.journal):
    sys.exit('REFUS : journal absent (%s)' % a.journal)

# TRONCATURE ET ROTATION. Defaut le plus grave signale sur ce script : il suivait UN fichier.
# Quand la sentinelle relance une instance, elle vide le journal ; le lecteur se retrouvait
# au-dela de la fin et mourait EN SILENCE — exactement le mode de panne qu on jure d eviter.
# On surveille donc la taille et l inode a chaque tour : plus petit = tronque, inode different
# = fichier remplace. Dans les deux cas on rouvre depuis le DEBUT (c est une session neuve) et
# on consigne la bascule.
def ouvrir(depuis_fin):
    fh = open(a.journal, 'r', errors='ignore')
    if depuis_fin:
        fh.seek(0, os.SEEK_END)
    st = os.fstat(fh.fileno())
    return fh, st.st_ino, fh.tell()


# on part de la FIN du journal : ce qui precede appartient a une session anterieure
f, inode, _ = ouvrir(True)
dernier_vu = time.time()
dernier_meta = 0.0
while True:
    ligne = f.readline()
    if not ligne:
        maintenant = time.time()
        try:
            st = os.stat(a.journal)
            if st.st_ino != inode or st.st_size < f.tell():
                quoi = 'remplace' if st.st_ino != inode else 'tronque'
                # UN REDEMARRAGE N EST PAS UNE CONTINUATION. Au redemarrage du serveur, le temps
                # de mission repart de zero ET les identifiants repartent de 1 : des hommes
                # differents portent le meme numero et sautent d un bout de la carte a l autre.
                # Mesure du 31/07 sur une session couvrant trois redemarrages : 72,8 % d ecarts
                # d horloge hors norme et 9,1 % de teleportations. On ROULE donc vers une session
                # neuve au lieu de continuer d ecrire dans la meme.
                print('  JOURNAL %s -> nouvelle session (le temps et les ids repartent a zero)'
                      % quoi, flush=True)
                vider_tick(); sauver_meta()
                f.close()
                rouler(quoi, maintenant)
                f, inode, _ = ouvrir(False)
                dernier_vu = maintenant
                continue
        except OSError:
            pass
        # SILENCE : plus de tick depuis 10 s alors que le serveur vit. On le CONSIGNE, on ne
        # repare pas le monde : le chien de garde exterieur decide de reinstaller le script.
        if etat['ticks'] and maintenant - dernier_vu > 10:
            etat['coupures'].append([round(dernier_vu, 1), round(maintenant, 1)])
            print('  SILENCE %.0f s sans tick' % (maintenant - dernier_vu), flush=True)
            dernier_vu = maintenant
        if maintenant - dernier_meta > 30:
            vider_tick(); sauver_meta(); dernier_meta = maintenant
        time.sleep(0.2)
        continue
    m = RX.search(ligne)
    if not m:
        continue
    try:
        traiter(m.group(1).strip().rstrip('"'))
        dernier_vu = time.time()
    except Exception:
        etat['lignes_illisibles'] += 1
