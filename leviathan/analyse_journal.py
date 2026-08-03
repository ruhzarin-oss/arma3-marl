#!/usr/bin/env python3
"""analyse_journal.py — L ANALYSE, SEPAREE DE LA COLLECTE (jalon 1).

Ne mesure rien, ne lance rien, ne touche pas au monde. Lit des journaux `.jsonl` produits
par `banc_mission.py` et en tire des taux. Si l analyse est fausse, on la reecrit et on
relit LES MEMES fichiers.

Trois travaux, dans cet ordre :

  (a) RECALCUL DU PREDICAT — le succes est reconstruit a partir des ingredients bruts
      (toucher, pas du toucher, exposition et pertes a cet instant, bornes de la mission)
      et compare a ce que le monde a declare. Une divergence est un BUG D INSTRUMENT,
      jamais un resultat. On s arrete.

  (b) APPARIEMENT — pour un meme indice d environnement, la mission doit etre identique
      entre les passes comparees. Deux passes qui ne jouent pas les memes missions ne se
      comparent pas.

  (c) TAUX — par verbe, avec n, et l ecart a la table publiee.

Motif : hier, un taux calcule a la volee dans la boucle de mesure a fait conclure trois
fois de suite sur un instrument casse. La collecte et le jugement sont desormais deux
programmes distincts.
"""
import sys, json, glob, argparse, statistics, collections

# ETALON DE REFERENCE — AMENDEMENT 4, accepte par Younes le 2026-07-29.
# Protocole persiste : etalon_j1.sh, mode episode, 1024 episodes, graine 3, D=8, 80 pas.
# L ancienne table (44,0 / 54,3 / 53,0 ...) est RETIREE : elle mesurait des doctrines
# amputees. Le pas etait desynchronise, donc passe le 14e pas global plus aucun episode ne
# recevait le signal qui declenche le crochet ou l eventail.
PUBLIEE = {
    'frontal_delibere':   (46.2, 5.8),
    'appui_mouvement':    (46.8, 11.6),
    'debordement_simple': (84.2, 60.2),
    'debordement_double': (86.3, 59.6),
    'infiltration':       (83.8, 48.9),
    'bonds_alternes':     (22.1, 7.7),
}
TOLERANCE = 3.0


def lire(chemin):
    """Les journaux sont en AJOUT SEUL (interdit n 7) : un fichier peut contenir plusieurs
    runs empiles. On ne lit QUE le dernier, identifie par son uuid — jamais un melange."""
    entetes, tous = [], []
    for l in open(chemin):
        r = json.loads(l)
        if r['type'] == 'entete':
            entetes.append(r)
        elif r['type'] == 'episode':
            tous.append(r)
    if not entetes:
        return [], tous
    dernier = entetes[-1]['run']
    return entetes, [e for e in tous if e.get('run') == dernier]


def recalcule(e):
    """Le predicat, reconstruit depuis les ingredients bruts. Doit egaler succes_monde."""
    if e['pas_took'] < 0:      # le PAS DU TOUCHER fait foi, jamais l instantane
        return False
    dans_delai = e['t_au_took'] <= e['T']
    dans_pertes = e['pertes_au_took'] * 4.0 <= e['Kmax']
    if not (dans_delai and dans_pertes):
        return False
    if e['verbe_nom'] == 'infiltrer':
        return e['expo_au_took'] < e['Emax']
    return True


def controle(episodes, chemin):
    ecarts = [e for e in episodes if recalcule(e) != e['succes_monde']]
    if ecarts:
        print('  !! BUG D INSTRUMENT : %d episodes sur %d ou le predicat recalcule differe'
              % (len(ecarts), len(episodes)))
        for e in ecarts[:3]:
            print('     env %d verbe %s took=%s pas_took=%.0f T=%.0f expo=%.2f Emax=%.2f '
                  'pertes=%.2f Kmax=%.0f | monde=%s recalcule=%s'
                  % (e['env'], e['verbe_nom'], e['took'], e['pas_took'], e['T'],
                     e['expo_au_took'], e['Emax'], e['pertes_au_took'], e['Kmax'],
                     e['succes_monde'], recalcule(e)))
        print('     -> %s' % chemin)
        return False
    return True


def taux(episodes):
    par = collections.defaultdict(list)
    for e in episodes:
        par[e['verbe_nom']].append(e)
    out = {}
    for v, lot in par.items():
        n = len(lot)
        out[v] = {'n': n,
                  'succes': 100.0 * sum(1 for e in lot if e['succes_monde']) / n,
                  'took': 100.0 * sum(1 for e in lot if e['took']) / n,
                  'expo_med': statistics.median([e['expo_cum'] for e in lot]),
                  'pertes_moy': sum(e['pertes_h'] for e in lot) / n}
    return out


def apparie(jeux):
    """Les memes indices d environnement doivent porter la meme mission entre passes."""
    ref = None
    for chemin, eps in jeux:
        cle = {e['env']: e['mission_hash'] for e in eps}
        if ref is None:
            ref = (chemin, cle); continue
        communs = set(ref[1]) & set(cle)
        casses = [k for k in communs if ref[1][k] != cle[k]]
        if casses:
            print('  !! APPARIEMENT ROMPU : %d environnements sur %d portent des missions '
                  'differentes entre\n     %s\n     et %s'
                  % (len(casses), len(communs), ref[0], chemin))
            return False
    return True


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('journaux', nargs='+')
    ap.add_argument('--apparier', action='store_true',
                    help='exiger que les passes jouent les memes missions')
    a = ap.parse_args()

    chemins = []
    for motif in a.journaux:
        chemins += sorted(glob.glob(motif)) or [motif]

    jeux = []
    sain = True
    for c in chemins:
        ent, eps = lire(c)
        if not eps:
            print('  (vide) %s' % c); continue
        if not controle(eps, c):
            sain = False
        jeux.append((c, eps))

    if not sain:
        print('\n>>> ANALYSE REFUSEE : le predicat recalcule ne colle pas au monde.')
        print('    C est un defaut d instrument, pas un resultat. Rien ne se lit.')
        sys.exit(4)

    if a.apparier and len(jeux) > 1 and not apparie(jeux):
        sys.exit(4)

    print('  %-26s %-10s %6s %9s %8s %9s %9s' %
          ('pilote', 'verbe', 'n', 'succes', 'took', 'expo med', 'ecart table'))
    for c, eps in jeux:
        ent, _ = lire(c)
        pil = ent[-1]['pilote'] if ent else '?'
        nom = pil.split(':', 1)[1] if ':' in pil else pil
        for v, r in sorted(taux(eps).items()):
            att = None
            if nom in PUBLIEE:
                att = PUBLIEE[nom][0 if v == 'prendre' else 1]
            ec = ('%+.1f' % (r['succes'] - att)) if att is not None else '   -'
            marque = '' if att is None or abs(r['succes'] - att) <= TOLERANCE else '  HORS'
            print('  %-26s %-10s %6d %8.1f%% %7.1f%% %9.2f %9s%s'
                  % (nom, v, r['n'], r['succes'], r['took'], r['expo_med'], ec, marque))
    print('ANALYSE_DONE')
