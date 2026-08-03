#!/usr/bin/env python3
"""reverdict_cible.py — L AVANTAGE DU FLANC SURVIT-IL A LA LETALITE CORRIGEE ?

Meme protocole que les re-verdicts n1 et n2, memes doctrines scriptees, memes graines.
Cette fois LES DEUX MONDES ONT LES DEUX COURBES : seule la REPARTITION DU FEU differe.

  ANCIEN  : cible_unique=False -> chaque defenseur frappe TOUS les attaquants
  MESURE  : cible_unique=True  -> un attaquant par defenseur et par pas
            (Arma, 2026-07-28 : 0,68 homme different par tireur par fenetre de 3,28 s,
             seuil pre-enregistre <1,5 ; banc bissection_selection.py, capteur HitPart)

Ce qu on attend : l ancien monde noyait les attaquants sous un feu 4x trop dense.
Le flanc y etait le seul moyen de survivre. Si l avantage disparait une fois la
letalite corrigee, il etait un artefact de mesure et non une verite tactique.

Criteres figes AVANT le run dans CRITERES_REVERDICT_CIBLE.md (empreinte a26a97a30c0eed05).

Ancien en-tete conserve ci-dessous.

reverdict_supp.py — LA COURBE N2 CHANGE-T-ELLE LES VERDICTS ?

Meme protocole que le re-verdict de la courbe n1, meme doctrines scriptees, memes graines.
Cette fois LES DEUX MONDES ONT LA COURBE DE TOUCHER : seule la suppression differe.

  ANCIEN  : suppression en TOUT OU RIEN (dsupp >= 0,5 -> le defenseur ne tire plus du tout,
            et tout est efface au pas suivant)
  MESURE  : supp_residuel=0.08  il lui reste 8 % de capacite de nuire (Arma, 28/07)
            supp_persist=0.35   le repit survit a un pas (cadence revenue a ~89 % en 2 s)

La politique reste SCRIPTEE, pour la meme raison qu'au chantier 1 : une politique apprise
dans l'ancien monde a appris a exploiter le tout-ou-rien, et la rejouer mesurerait son
inadaptation, pas la fidelite du monde.

Ce qu'on attend : le feu de couverture etait GRATUITEMENT protecteur (l'adversaire
s'eteignait). Il devient couteux et partiel. Si le flanc garde son avantage malgre ca,
l'avantage tient a la geometrie et non a un bug de suppression.

Ancien en-tete conserve ci-dessous.

reverdict.py — LA question qui justifie tout le chantier 1.

La courbe n1 (toucher, mesuree sur Arma) suffit-elle, A ELLE SEULE, a faire rendre au
sandbox les verdicts qu'Arma rend ?

PROTOCOLE : meme politique, deux mondes.
La politique doit etre INSENSIBLE au monde, donc SCRIPTEE. Une politique apprise dans
l'ancien monde a appris a exploiter le sanctuaire au-dela de 110 m ; la rejouer
mesurerait son inadaptation, pas la fidelite du monde.

  ANCIEN monde  : hit=0.06 partout sous 110 m puis ZERO, posture posee [1.00,0.50,0.20]
  NOUVEAU monde : courbe Arma + les 3 conversions mesurees

Deux doctrines, memes graines, meme geometrie defensive :
  FRONTAL : tout le monde droit sur l'objectif
  FLANC   : un element FIXE au contact, le reste crochete large hors de l'arc de tir

Criteres figes AVANT le run dans CRITERES_REVERDICT.md (empreinte dcb0a5d9e57d70a5).
Ce script ne les redefinit pas : il les lit et les applique.
"""
import sys, os, json, math, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233          # mesures Arma du 26/07

ap = argparse.ArgumentParser()
ap.add_argument('--episodes', type=int, default=200, help='episodes par bras et par monde (fige a 200)')
ap.add_argument('--steps', type=int, default=60)
ap.add_argument('--seed', type=int, default=7)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='reverdict_cible.json')
a = ap.parse_args()


def monde(nouveau, seed):
    """meme geometrie, meme graine ; SEUL le modele de combat change"""
    k = dict(num_envs=a.episodes, A=4, D=4, seed=seed, device=a.device,
             max_steps=a.steps, postures=True, hull=True,
             def_line=True,          # LIGNE defensive (pas un blob) — la geometrie ou le flanc a un sens
             def_arc=math.pi / 3,    # arc de tir 120 deg : le flanc EXISTE comme angle mort
             def_rand=True,          # geometrie randomisee par episode : pas de "toujours a gauche" memorisable
             secure_task=True, secure_only=True)   # gagner = ATTEINDRE l'objectif, comme Arma
    # LES DEUX MONDES ONT LA COURBE N1 : on isole la seule courbe n2.
    k.update(courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG)
    # LES DEUX MONDES ONT AUSSI LA COURBE N2 : on isole la seule repartition du feu.
    k.update(supp_residuel=0.08, supp_persist=0.35)
    k.update(cible_unique=bool(nouveau))
    return AssaultTerrain(**k)


def cap(dx, dy):
    """cap 0-7 (pas de 45 deg) vers le vecteur (dx,dy) ; l'objectif est a l'origine"""
    ang = torch.atan2(dx, dy)
    return (torch.round(ang / (math.pi / 4.0)).long() % 8)


def doctrine_frontal(e, t):
    """tout le monde droit sur l'objectif"""
    return cap(-e.apx, -e.apy)


def doctrine_flanc(e, t, n_fixe=2, pas_crochet=14):
    """FIXER puis CROCHETER.
    Les n_fixe premiers tiennent et appuient : ils occupent l'arc de tir.
    Les autres partent en TANGENTE (perpendiculaire a l'axe de l'objectif) pendant
    pas_crochet pas, puis rentrent — ils arrivent donc hors du cone defensif."""
    N, A = e.N, e.A
    act = cap(-e.apx, -e.apy)                                  # par defaut : vers l'objectif
    # --- element de fixation : HOLD au-dela, SUPPRESS des qu'on est a portee ---
    d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
    fixe = torch.zeros(N, A, dtype=torch.bool, device=e.dev); fixe[:, :n_fixe] = True
    a_portee = d_obj < e.fire_range * 0.9
    act = torch.where(fixe & a_portee, torch.full_like(act, 9), act)     # 9 = SUPPRESS
    act = torch.where(fixe & ~a_portee, cap(-e.apx, -e.apy), act)        # sinon on se met a portee
    # --- element de crochet : tangente puis rentree ---
    if t < pas_crochet:
        tang = cap(-e.apy, e.apx)                              # perpendiculaire, meme sens pour tous
        act = torch.where(~fixe, tang, act)
    return act


DOCTRINES = {'frontal': doctrine_frontal, 'flanc': doctrine_flanc}


def joue(nouveau, doctrine, seed):
    e = monde(nouveau, seed)
    e.reset()
    N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(N, dtype=torch.bool, device=e.dev)
    pertes = torch.zeros(N, device=e.dev)
    expo_cum = torch.zeros(N, device=e.dev)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
    dmin = d0.clone()
    nsteps = torch.zeros(N, device=e.dev)
    f = DOCTRINES[doctrine]
    for t in range(a.steps):
        acts = f(e, t)
        _, _, done, info = e.step(acts, auto_reset=False)
        vivant = ~fini
        pris = pris | (info['took'] & vivant)
        pertes = torch.where(vivant, info['losses'].float(), pertes)
        expo_cum = expo_cum + info['exposed'] * vivant.float()
        nsteps = nsteps + vivant.float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(vivant, d, dmin))
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    gagne = (d0 - dmin).clamp(min=1.0)                         # metres gagnes vers l'objectif
    expo_par_metre = expo_cum / gagne
    return {
        'prise': float(pris.float().mean()),
        'pertes_moy': float(pertes.mean()),
        'pertes_par_prise': float(pertes[pris].mean()) if bool(pris.any()) else float('nan'),
        'expo_par_metre': float(expo_par_metre.mean()),
        'metres_gagnes': float(gagne.mean()),
        'pas_moyens': float(nsteps.mean()),
        'n': int(N),
    }


if __name__ == '__main__':
    if not os.path.exists(LEV + '/CRITERES_REVERDICT_CIBLE.md'):
        print('!! les criteres ne sont pas figes — ARRET.'); sys.exit(2)
    print('=== RE-VERDICT : l avantage du flanc survit-il a la letalite corrigee ? ===', flush=True)
    print('    %d episodes par bras et par monde | graine %d | criteres figes d avance'
          % (a.episodes, a.seed), flush=True)
    t0 = time.time()
    res = {}
    for nom_monde, nouveau in (('ancien', False), ('nouveau', True)):
        for doctrine in ('frontal', 'flanc'):
            r = joue(nouveau, doctrine, a.seed)
            res['%s/%s' % (nom_monde, doctrine)] = r
            print('  %-8s %-8s : prise %5.1f%%  pertes/prise %4.2f  expo/m %.3f'
                  % (nom_monde, doctrine, 100 * r['prise'], r['pertes_par_prise'], r['expo_par_metre']),
                  flush=True)

    print('', flush=True)
    print('=== LE VERDICT N1 : LE FLANC PAIE-T-IL ? ===', flush=True)
    verdicts = {}
    for nom_monde in ('ancien', 'nouveau'):
        fr = res['%s/frontal' % nom_monde]; fl = res['%s/flanc' % nom_monde]
        rp = fl['prise'] / fr['prise'] if fr['prise'] > 0 else float('inf')
        rc = (fl['pertes_par_prise'] / fr['pertes_par_prise']
              if fr['pertes_par_prise'] and fr['pertes_par_prise'] == fr['pertes_par_prise'] else float('nan'))
        paie = (rp >= 1.5) and (rc == rc) and (rc <= 0.6)
        verdicts[nom_monde] = {'rapport_prise': rp, 'rapport_cout': rc, 'le_flanc_paie': bool(paie)}
        print('  %-8s : prise flanc/frontal x%.2f   cout flanc/frontal x%.2f   -> %s'
              % (nom_monde, rp, rc, 'LE FLANC PAIE' if paie else 'le flanc ne paie pas'), flush=True)

    print('', flush=True)
    ok_nouveau = verdicts['nouveau']['le_flanc_paie']
    ok_ancien = verdicts['ancien']['le_flanc_paie']
    print('=== CONCLUSION (selon les criteres figes, non negociables) ===', flush=True)
    if ok_ancien and not ok_nouveau:
        print('  >>> L AVANTAGE DU FLANC ETAIT UN ARTEFACT DE LETALITE.', flush=True)
        print('      Il paie dans le monde 4x trop letal, il ne paie plus dans le monde mesure.', flush=True)
        print('      Les conclusions sur la manoeuvre tirees de l ancien monde sont a reprendre.', flush=True)
    elif ok_nouveau and not ok_ancien:
        print('  >>> LE MONDE MESURE REND LE VERDICT, L ANCIEN NON.', flush=True)
        print('      RESULTAT INATTENDU : le flanc ne payait PAS dans le monde 4x trop letal', flush=True)
        print('      et paie une fois la letalite corrigee. A consigner tel quel, sans explication', flush=True)
        print('      apres coup. Chercher pourquoi.', flush=True)
    elif ok_nouveau and ok_ancien:
        print('  >>> LES DEUX MONDES rendent le verdict.', flush=True)
        print('      L avantage du flanc TIENT A LA GEOMETRIE : la letalite ne le portait pas.', flush=True)
        print('      Les conclusions des deux dernieres semaines tiennent.', flush=True)
    elif verdicts['nouveau']['rapport_prise'] > 1.0:
        print('  >>> AVANTAGE AFFAIBLI MAIS PRESENT (prise x%.2f, cout x%.2f).'
              % (verdicts['nouveau']['rapport_prise'], verdicts['nouveau']['rapport_cout']), flush=True)
        print('      Fidelite DIRECTIONNELLE acquise. On le note et on s INTERDIT de', flush=True)
        print('      retuner les courbes pour forcer le rapport.', flush=True)
    else:
        print('  >>> LE FLANC NE PAIE PLUS DANS AUCUN DES DEUX MONDES.', flush=True)
        print('      Si l ancien monde le rendait avant, c est le banc qui a change, pas la doctrine :', flush=True)
        print('      verifier la geometrie defensive et la doctrine scriptee avant toute conclusion.', flush=True)

    json.dump({'criteres': 'CRITERES_REVERDICT_CIBLE.md (a26a97a30c0eed05)',
               'episodes': a.episodes, 'graine': a.seed, 'bras': res, 'verdicts': verdicts,
               'duree_s': round(time.time() - t0)},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s  (%.0f s)' % (LEV, a.out, time.time() - t0), flush=True)
    print('REVERDICT_DONE', flush=True)
