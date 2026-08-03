#!/usr/bin/env python3
"""audit_boutons.py — COMBIEN DE BOUTONS SONT DÉBRANCHÉS ?

Le 28/07 on a découvert par accident que `def_arc` n'a AUCUN effet quand `def_rand=True`
— et tous les bancs du projet passent `def_rand=True`. Trois défauts d'instrument trouvés
par hasard dans la même journée. Cet audit arrête de compter sur le hasard.

MÉTHODE : pour chaque paramètre, on joue deux fois la MÊME expérience (même graine, même
doctrine, même monde) avec deux valeurs EXTRÊMES du paramètre. Si toutes les sorties sont
identiques au chiffre près, le bouton est INERTE dans la configuration où les bancs tournent.

Ce que l'audit dit : « ce paramètre ne change rien ICI ». Pas « ce paramètre est cassé ».
Un bouton peut être légitimement neutralisé par un autre (c'est le cas de `def_arc` sous
`def_rand`) — ce qui compte, c'est que personne ne croie le piloter.
"""
import sys, os, json, math, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from assault_terrain import AssaultTerrain
from manuel import MANOEUVRES

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument('--episodes', type=int, default=150)
ap.add_argument('--steps', type=int, default=60)
ap.add_argument('--seed', type=int, default=7)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--doctrine', default='debordement_simple')
ap.add_argument('--out', default='audit_boutons.json')
ap.add_argument('--bouton', default=None, help='un seul bouton, dans son propre processus (un assert CUDA empoisonne tout le contexte)')
a = ap.parse_args()

# LA CONFIGURATION DES BANCS — celle que reverdict/balayage/matrice utilisent tous
BASE = dict(A=4, D=8, postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
            def_rand=True, secure_task=True, secure_only=True,
            courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG,
            supp_residuel=0.08, supp_persist=0.35, cible_unique=True)

# chaque bouton : (valeur basse, valeur haute) — deux extrêmes crédibles
BOUTONS = {
    'def_arc':          (math.radians(15), math.pi),
    'def_spread':       (math.radians(5), math.radians(60)),
    'def_rline':        (15.0, 70.0),
    'def_rand':         (False, True),
    'def_line':         (False, True),
    'hull':             (False, True),
    'postures':         (False, True),
    'secure_only':      (False, True),
    'flank_kill':       (0.0, 1.0),
    'nav_around':       (False, True),
    'supp_kill':        (0.2, 2.0),
    'supp_residuel':    (0.01, 0.60),
    'supp_persist':     (0.0, 0.90),
    'cible_unique':     (False, True),
    'tir_par_pas':      (0.3, 4.0),
    'degat_par_impact': (0.05, 0.60),
    'sec_par_pas':      (1.0, 8.0),
    'emergent_expo':    (False, True),
    'arc_obs':          (False, True),
    'champ_risque':     (False, True),
    'stress':           (False, True),
    'approach_w':       (0.0, 1.0),
    'death_pen':        (0.0, 2.0),
}


def joue(surcharge):
    k = dict(BASE); k.update(surcharge)
    k.update(num_envs=a.episodes, seed=a.seed, device=a.device, max_steps=a.steps)
    try:
        e = AssaultTerrain(**k)
    except Exception as exc:
        return {'erreur': str(exc)[:90]}
    e.reset()
    f = MANOEUVRES[a.doctrine]
    N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(N, dtype=torch.bool, device=e.dev)
    pertes = torch.zeros(N, device=e.dev); expo = torch.zeros(N, device=e.dev)
    for t in range(a.steps):
        _, _, done, info = e.step(f(e, t), auto_reset=False)
        v = ~fini
        pris = pris | (info['took'] & v)
        pertes = torch.where(v, info['losses'].float(), pertes)
        expo = expo + info['exposed'] * v.float()
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    return {'prise': round(float(pris.float().mean()), 6),
            'pertes': round(float(pertes.mean()), 6),
            'expo': round(float(expo.mean()), 6)}


if __name__ == '__main__':
    if a.bouton:
        bas, haut = BOUTONS[a.bouton]
        rb, rh = joue({a.bouton: bas}), joue({a.bouton: haut})
        if 'erreur' in rb or 'erreur' in rh:
            v = 'REFUSE'
        elif rb == rh:
            v = 'INERTE'
        else:
            v = 'actif'
        json.dump({'bouton': a.bouton, 'bas': rb, 'haut': rh, 'verdict': v},
                  open(LEV + '/audit_' + a.bouton + '.json', 'w'), indent=1)
        fmt = lambda r: ('erreur' if 'erreur' in r else 'prise %.3f pertes %.2f expo %.1f'
                         % (r['prise'], r['pertes'], r['expo']))
        print('  %-18s %-30s %-30s  %s' % (a.bouton, fmt(rb), fmt(rh), v), flush=True)
        sys.exit(0)
    print('\n'.join(BOUTONS))
