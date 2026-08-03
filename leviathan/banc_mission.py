#!/usr/bin/env python3
"""banc_mission.py — L INSTRUMENT DE MESURE UNIQUE (jalon 1).

Il COLLECTE, il n analyse pas. Il ecrit des episodes bruts sur disque, une fois, sans
filtre. Les taux se calculent ailleurs (`analyse_journal.py`), en relisant ces fichiers.
Si l analyse est fausse, on reecrit l analyse et on relit les MEMES fichiers — on ne
relance pas le monde.

Motif : sept pannes en deux jours, toutes dans l instrument. Journaux tronques par un
`tail`, mesures lues apres que l etat avait bouge, taux calcules a la volee et jamais
verifiables. Ici la source de verite est un fichier en AJOUT SEUL, jamais tronque.

Deux pilotes, un seul chemin de mesure :
    --pilote doctrine:debordement_simple     (une des six manoeuvres du manuel)
    --pilote reseau:/chemin/mission_v3.pt    (une politique entrainee)

Criteres : CRITERES_JALON1.md. Sans ce fichier, le banc refuse de demarrer.
"""
import sys, os, json, uuid, hashlib, argparse, datetime
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch

LEV = '/home/younes/arma3-marl/leviathan'
CRITERES = LEV + '/CRITERES_JALON1.md'


def _sha(chemin):
    try:
        return hashlib.sha256(open(chemin, 'rb').read()).hexdigest()[:16]
    except Exception:
        return None


def joue(pilote, verbe='tire', permute=0, episodes=1024, graine=3, D=8, pas=80,
         mode='episode', journal=None, hidden=256, layers=3, device='cuda:0',
         silencieux=False, budget=None, reflexe=False):
    """Joue une passe et ECRIT le journal. Renvoie (chemin_journal, resume).
    `audit_ordre.py` appelle cette fonction — il ne duplique jamais cette boucle."""
    if not os.path.exists(CRITERES):
        print('!! CRITERES_JALON1.md absent — aucune mesure avant les criteres.'); sys.exit(2)
    from monde_mission import fabrique, VERBES
    from manuel import MANOEUVRES

    est_doctrine = pilote.startswith('doctrine:')
    nom_pilote = pilote.split(':', 1)[1]
    if est_doctrine and mode != 'episode':
        print("!! mode '%s' interdit pour une doctrine : manuel.py lit un pas SCALAIRE, "
              "invalide hors mode episode." % mode); sys.exit(3)
    auto_reset = (mode == 'continu')

    # --budget active le monde v5 et FORCE la valeur : c est ainsi qu on mesure la
    # frontiere par budget avant d entrainer quoi que ce soit.
    m = fabrique(episodes=episodes, D=D, seed=graine, device=device, steps=pas,
                 mode_budget=(budget is not None), budget_force=budget)
    obs = m.reset(permute=permute)

    if est_doctrine:
        f = MANOEUVRES[nom_pilote]; net = None
    else:
        from train_koth_gpu import Net
        from torch.distributions import Categorical
        # MEME PIPELINE QU A L ENTRAINEMENT. Un reseau v6 entraine avec la couche et evalue
        # sans elle voit des situations qu il n a jamais rencontrees — l erreur commise sur
        # v5, qui a fait lire 4,3 % au lieu du vrai taux.
        from reflexe import CoucheReflexe, N_SEUILS
        _ns = N_SEUILS if reflexe else 0
        net = Net(m.obs_dim, m.n_actions + _ns, hidden, layers).to(device)
        _ck = torch.load(nom_pilote, map_location=device)
        net.load_state_dict(_ck['net'] if isinstance(_ck, dict) and 'net' in _ck else _ck)
        net.eval()
        f = None
        couche = CoucheReflexe(m.N, m.A, device) if reflexe else None

    # --- forcage du verbe : APRES le tirage, sans toucher au flux du generateur ---
    if verbe != 'tire':
        m.verbe[:] = VERBES.index(verbe)
        obs = m._obs(m.env._obs(), permute)

    run = uuid.uuid4().hex[:12]
    if journal is None:
        os.makedirs(LEV + '/journaux', exist_ok=True)
        journal = '%s/journaux/j1_%s_%s_p%d_g%d.jsonl' % (
            LEV, nom_pilote.replace('/', '_').replace('.pt', ''), verbe, permute, graine)

    def ecrit_episode(fh, run_, i, g, cause, perm, A, Dv):
        from monde_mission import VERBES as _VV
        v = int(g['verbe'])
        mh = hashlib.sha1(('%.4f|%.4f|%.4f|%.4f|%.4f' % (g['R'], g['T'], g['Kmax'],
                                                         g['Emax'], g['d0'])).encode()).hexdigest()[:10]
        rec = {'type': 'episode', 'run': run_, 'env': i, 'mission_hash': mh,
               'verbe': v, 'verbe_nom': _VV[v],
               'verbe_affiche': _VV[(v + perm) % len(_VV)],
               'R': g['R'], 'T': g['T'], 'Kmax': g['Kmax'], 'Emax': g['Emax'], 'D': Dv, 'd0': g['d0'],
               'succes_monde': bool(g['succes']),
               # `took` = il y a eu prise DANS CET EPISODE (le pas du toucher fait foi),
               # et non l instantane du dernier pas : melanger les deux moments
               # desalignait le predicat recalcule du verdict du monde (2026-07-29).
               'took': bool(g['pas_took'] >= 0),
               # ARRIVEE : l escouade a-t-elle atteint l objectif, budget IGNORE.
               # C est ce chiffre, et non `took`, qui dit s il y a matiere a reetiqueter.
               'arrive': bool(g.get('arrive', False)),
               'pas_took': g['pas_took'],
               'expo_au_took': g['expo_au_took'], 'pertes_au_took': g['pertes_au_took'],
               't_au_took': g['pas_took'],
               'expo_cum': g['expo_cum'], 'pertes': g['pertes'],
               'pertes_h': g['pertes'] * A, 'duree': g['duree'],
               'dmin': g['dmin'], 'fin': cause}
        fh.write(json.dumps(rec) + '\n')

    ecrits = [0]
    N = m.N
    dev = m.dev
    fini = torch.zeros(N, dtype=torch.bool, device=dev)
    dmin = m._dist().clone()
    fin_cause = ['horizon'] * N
    gel = {}

    jf = open(journal, 'a')     # AJOUT SEUL. Jamais 'w'. Un run rate reste au journal.
    entete = {'type': 'entete', 'run': run,
              'horodate': datetime.datetime.now().isoformat(timespec='seconds'),
              'argv': sys.argv, 'pilote': pilote, 'verbe': verbe, 'permute': permute,
              'episodes': episodes, 'graine': graine, 'D': D, 'pas': pas, 'mode': mode,
              'sha_monde': _sha(LEV + '/monde_mission.py'),
              'sha_manuel': _sha(LEV + '/manuel.py'),
              'sha_banc': _sha(LEV + '/banc_mission.py'),
              'sha_criteres': _sha(CRITERES),
              'budget': budget, 'reflexe': reflexe,
              'sha_poids': None if est_doctrine else _sha(nom_pilote)}
    jf.write(json.dumps(entete) + '\n'); jf.flush()

    for t in range(pas):
        if net is None:
            acts = f(m.env, t)
        else:
            with torch.no_grad():
                lg = net.a_logits(obs)
                if reflexe:
                    acts = Categorical(logits=lg[..., :m.n_actions]).sample()
                    acts = couche.applique(acts, torch.sigmoid(lg[..., m.n_actions:]), m)[0]
                else:
                    acts = Categorical(logits=lg).sample()
        obs, _, d, info = m.step(acts, permute=permute, auto_reset=auto_reset)
        if net is not None and reflexe and bool(d.any()):
            couche.reset(d.nonzero(as_tuple=False).squeeze(-1))
        vivants = m.env._aalive().float().sum(1)
        dmin = torch.minimum(dmin, torch.where(fini, dmin, m._dist()))
        # MODE EPISODE : un episode par environnement, on VERROUILLE a la premiere fin.
        # MODE CONTINU : les environnements rejouent, on ecrit CHAQUE episode termine.
        # Ajout du 2026-07-29 pour l operation O1 — calibrer le compteur interne de
        # l entrainement, qui annonce 43,6 % la ou l evaluation en mode episode donne 4,1 %.
        # Le chemin du mode episode n est pas touche : son etalonnage reste valide.
        neuf = d if auto_reset else (d & ~fini)
        if bool(neuf.any()):
            for i in neuf.nonzero(as_tuple=False).squeeze(-1).tolist():
                g = {k: (v[i].item() if torch.is_tensor(v) else v) for k, v in info.items()}
                g['dmin'] = float(dmin[i])
                if bool(info['succes'][i]):
                    cause = 'took'
                elif vivants[i] == 0:
                    cause = 'wiped'
                else:
                    cause = 'timeout'
                if auto_reset:
                    ecrit_episode(jf, run, i, g, cause, permute, m.A, D)
                    ecrits[0] += 1
                    dmin[i] = 1e4
                else:
                    gel[i] = g; fin_cause[i] = cause
            if not auto_reset:
                fini = fini | neuf
        if verbe != 'tire' and auto_reset:
            m.verbe[:] = VERBES.index(verbe)

    from monde_mission import VERBES as _V
    lignes = ecrits[0]
    for i in ([] if auto_reset else range(N)):
        g = gel.get(i)
        if g is None:      # jamais termine dans la fenetre
            g = {k: (v[i].item() if torch.is_tensor(v) else v) for k, v in info.items()}
            g['dmin'] = float(dmin[i])
        v = int(g['verbe'])
        mh = hashlib.sha1(('%.4f|%.4f|%.4f|%.4f|%.4f' % (g['R'], g['T'], g['Kmax'],
                                                         g['Emax'], g['d0'])).encode()).hexdigest()[:10]
        rec = {'type': 'episode', 'run': run, 'env': i, 'mission_hash': mh,
               'verbe': v, 'verbe_nom': _V[v],
               'verbe_affiche': _V[(v + permute) % len(_V)],
               'R': g['R'], 'T': g['T'], 'Kmax': g['Kmax'], 'Emax': g['Emax'], 'D': D, 'd0': g['d0'],
               'succes_monde': bool(g['succes']),
               # `took` = il y a eu prise DANS CET EPISODE (le pas du toucher fait foi),
               # et non l instantane du dernier pas : melanger les deux moments
               # desalignait le predicat recalcule du verdict du monde (2026-07-29).
               'took': bool(g['pas_took'] >= 0),
               # ARRIVEE : l escouade a-t-elle atteint l objectif, budget IGNORE.
               # C est ce chiffre, et non `took`, qui dit s il y a matiere a reetiqueter.
               'arrive': bool(g.get('arrive', False)),
               'pas_took': g['pas_took'],
               'expo_au_took': g['expo_au_took'], 'pertes_au_took': g['pertes_au_took'],
               't_au_took': g['pas_took'],
               'expo_cum': g['expo_cum'], 'pertes': g['pertes'],
               'pertes_h': g['pertes'] * m.A, 'duree': g['duree'],
               'dmin': g['dmin'], 'fin': fin_cause[i]}
        jf.write(json.dumps(rec) + '\n'); lignes += 1
    resume = {'type': 'fin', 'run': run, 'episodes_ecrits': lignes}
    jf.write(json.dumps(resume) + '\n'); jf.flush(); jf.close()

    if not silencieux:
        import statistics
        succ = sum(1 for i in range(N) if bool(gel.get(i, {}).get('succes', False)))
        tk = sum(1 for i in range(N) if bool(gel.get(i, {}).get('took', False)))
        ex = sorted(float(gel.get(i, {}).get('expo_cum', 0.0)) for i in range(N))
        du = sorted(float(gel.get(i, {}).get('duree', 0.0)) for i in range(N))
        pe = [float(gel.get(i, {}).get('pertes', 0.0)) * m.A for i in range(N)]
        print('  %-26s %-10s n=%-5d succes %5.1f%%  took %5.1f%%  expo med %5.2f  '
              'pertes moy %4.2f  duree med %4.0f'
              % (pilote, verbe, N, 100.0 * succ / N, 100.0 * tk / N,
                 statistics.median(ex), sum(pe) / N, statistics.median(du)), flush=True)
        print('  -> %s' % journal)
        print('BANC_DONE')
    return journal, {'n': N}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilote', required=True)
    ap.add_argument('--verbe', default='tire', choices=['prendre', 'infiltrer', 'tire'])
    ap.add_argument('--permute', type=int, default=0)
    ap.add_argument('--episodes', type=int, default=1024)
    ap.add_argument('--graine', type=int, default=3)
    ap.add_argument('--D', type=int, default=8)
    ap.add_argument('--pas', type=int, default=80)
    ap.add_argument('--mode', default='episode', choices=['episode', 'continu'])
    ap.add_argument('--journal', default=None)
    ap.add_argument('--hidden', type=int, default=256)
    ap.add_argument('--layers', type=int, default=3)
    ap.add_argument('--device', default='cuda:0')
    ap.add_argument('--reflexe', action='store_true',
                    help='applique la couche reactive : OBLIGATOIRE pour un reseau v6')
    ap.add_argument('--budget', type=float, default=None,
                    help='force le budget de dose et active le monde v5')
    a = ap.parse_args()
    joue(a.pilote, a.verbe, a.permute, a.episodes, a.graine, a.D, a.pas, a.mode,
         a.journal, a.hidden, a.layers, a.device, budget=a.budget, reflexe=a.reflexe)
