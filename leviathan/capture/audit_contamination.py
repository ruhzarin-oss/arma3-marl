#!/usr/bin/env python3
"""audit_contamination.py — combien le corpus ouvert est-il contamine par l abstraction ?

Criteres : CRITERES_AUDIT_CAPTURE.md (210f2d7b6bc8d124). Refuse de tourner si le fichier a bouge.

Il CONSTATE, il ne repare rien et ne touche pas au monde. Sept taux, chacun avec son denominateur
explicite — un taux sans denominateur est infalsifiable.

Usage :
  audit_contamination.py --session <dossier>          audite une session
  audit_contamination.py --controles                  passe les trois controles de l audit lui-meme
"""
import argparse, hashlib, json, math, os, shutil, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
CRIT = os.path.join(ICI, 'CRITERES_AUDIT_CAPTURE_v2.md')
ATTENDU = 'b7a64e476c3ea211'
PLAFOND = 60.0          # m/s horizontal : impossibilite physique, pas un reglage
INDICE = 15.0           # m/s : au-dela, un fantassin est suspect (rapporte, non seuille)
FENETRE_MORT = 5.0      # s : une mort est tracee si un impact la precede de moins de ca
SEUIL = 0.01

emp = hashlib.sha256(open(CRIT, 'rb').read()).hexdigest()[:16]
if emp != ATTENDU:
    sys.exit('REFUS : criteres modifies (%s au lieu de %s).' % (emp, ATTENDU))


def charger(d):
    def lire(n):
        p = os.path.join(d, n)
        if not os.path.exists(p):
            return []
        out = []
        for l in open(p):
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except Exception:
                    pass
        return out
    meta = {}
    pm = os.path.join(d, 'meta.json')
    if os.path.exists(pm):
        meta = json.load(open(pm))
    return lire('state.jsonl'), lire('events.jsonl'), meta


def quantile(v, q):
    if not v:
        return None
    s = sorted(v)
    return s[min(len(s) - 1, max(0, int(math.ceil(q * len(s))) - 1))]


def auditer(etats, evts, meta, decalage_impacts=0.0):
    par = {}
    for e in evts:
        par.setdefault(e['evt'], []).append(e)
    apparus = {e['id'] for e in par.get('spawn', [])}
    hits = [dict(h, t=h['t'] + decalage_impacts) for h in par.get('hit', [])]
    morts = par.get('killed', [])
    tirs = par.get('fired', [])

    r = {}

    # (1) FANTOMES : une entite presente dans un tick sans jamais avoir ete vue apparaitre. C est
    #     la signature d une entite deja materialisee avant le debut de la capture, ou d un profil
    #     que le recenseur n a pas vu.
    n_ref = n_fant = 0
    for x in etats:
        for e in x['ents']:
            n_ref += 1
            if e[0] not in apparus:
                n_fant += 1
    r['fantomes'] = (n_fant, n_ref)

    # (2) MORTS SANS TUEUR TRACABLE (coupe v2). La v1 exigeait un impact dans les 5 s : elle
    #     mesurait quelle categorie de degats declenche quel capteur, pas son intention. Une mort
    #     resolue par la comptabilite de virtualisation ne fabrique pas d instigateur materialise
    #     et recense. Cas limites decides AVANT la mesure (criteres v2) :
    #     tueur nul, tueur = victime, tueur jamais recense -> NON TRACEE.
    sans_tueur = 0
    for m in morts:
        k = m.get('killer', -1)
        if k < 0 or k == m['victim'] or k not in apparus:
            sans_tueur += 1
    r['morts_sans_tueur'] = (sans_tueur, len(morts))

    # INDICATEUR rapporte sans seuil : part des morts par arme legere directe.
    non_trace = 0
    for m in morts:
        if not any(h['target'] == m['victim'] and 0 <= m['t'] - h['t'] <= FENETRE_MORT for h in hits):
            non_trace += 1

    # (3) TIREURS INTRACABLES
    r['tireurs_intracables'] = (sum(1 for h in hits if h.get('shooter', -1) < 0), len(hits))

    # (4) TELEPORTATION : par entite, entre deux ticks consecutifs.
    pos = {}
    n_paires = n_tel = n_ind = 0
    vitesses = []
    for x in sorted(etats, key=lambda z: z['t']):
        for e in x['ents']:
            i, px, py = e[0], e[1], e[2]
            if i in pos:
                t0, x0, y0 = pos[i]
                dt = x['t'] - t0
                if dt > 0:
                    v = math.hypot(px - x0, py - y0) / dt
                    vitesses.append(v)
                    n_paires += 1
                    if v > PLAFOND:
                        n_tel += 1
                    if v > INDICE:
                        n_ind += 1
            pos[i] = (x['t'], px, py)
    r['teleportation'] = (n_tel, n_paires)

    # (5) TIRS SANS PROJECTILE
    r['tirs_sans_projectile'] = (sum(1 for t in tirs if t.get('proj') != 1), len(tirs))

    # (6) COUVERTURE : le tick annonce un compte total ; la liste doit le refleter.
    mauvais = 0
    for x in etats:
        n = x.get('n_total') or 0
        k = len(x['ents'])
        if n > 0 and abs(n - k) > max(1, 0.01 * n):
            mauvais += 1
    r['couverture'] = (mauvais, len(etats))

    # (7) HORLOGE
    nom = meta.get('dt_nominal') or 0.2
    ecarts = []
    ts = sorted({x['t'] for x in etats})
    for a_, b_ in zip(ts, ts[1:]):
        ecarts.append(b_ - a_)
    hors = sum(1 for d in ecarts if not (0.8 * nom <= d <= 1.2 * nom))
    r['horloge'] = (hors, len(ecarts))

    # FRONTIERE DE MATERIALISATION : c est la que la comptabilite d abstraction fuirait — une
    # unite materialisee deja condamnee, ou une resolution de rattrapage juste avant de disparaitre.
    naiss = {e['id']: e['t'] for e in par.get('spawn', [])}
    disp = {}
    for e in par.get('despawn', []):
        disp.setdefault(e['id'], e['t'])
    jeunes = sum(1 for m in morts if m['victim'] in naiss and (m['t'] - naiss[m['victim']]) < 10.0)
    vite_parties = sum(1 for m in morts if m['victim'] in disp and 0 <= (disp[m['victim']] - m['t']) < 10.0)

    extra = {
        'frontiere_mort_jeune': (jeunes, len(morts)),
        'frontiere_disp_rapide': (vite_parties, len(morts)),
        'v_p999': quantile(vitesses, 0.999), 'v_max': max(vitesses) if vitesses else None,
        'au_dela_15': (n_ind, n_paires), 'monde': (meta.get('monde') or {}).get('sha256'),
        'ticks': len(etats), 'evenements': len(evts),
        'morts_tracees_pct': (100.0 * (len(morts) - non_trace) / len(morts)) if morts else None,
    }
    return r, extra


def afficher(r, extra, titre):
    print('=== %s ===' % titre)
    print('  monde %s | %d ticks | %d evenements' % (extra['monde'], extra['ticks'], extra['evenements']))
    tout_ok = True
    for k, (num, den) in r.items():
        taux = (num / den) if den else 0.0
        ok = taux < SEUIL
        if den == 0:
            etat = 'vide'
        else:
            etat = 'ok  ' if ok else 'HORS'
            tout_ok = tout_ok and ok
        print('  [%s] %-22s %6d / %-7d = %6.3f %%' % (etat, k, num, den, 100.0 * taux))
    print('  vitesse : p99,9 = %s m/s   max = %s m/s   au-dela de 15 m/s : %d / %d'
          % (('%.1f' % extra['v_p999']) if extra['v_p999'] is not None else '-',
             ('%.1f' % extra['v_max']) if extra['v_max'] is not None else '-',
             extra['au_dela_15'][0], extra['au_dela_15'][1]))
    if extra['morts_tracees_pct'] is not None:
        print('  INDICATEUR morts adossees a un impact <= 5 s : %.1f %% (part d arme legere directe)'
              % extra['morts_tracees_pct'])
    fj, nd = extra['frontiere_mort_jeune']
    fd, _ = extra['frontiere_disp_rapide']
    if nd:
        print('  INDICATEUR frontiere : mort < 10 s apres apparition %d/%d (%.1f %%) | '
              'disparition < 10 s apres mort %d/%d (%.1f %%)'
              % (fj, nd, 100.0 * fj / nd, fd, nd, 100.0 * fd / nd))
    return tout_ok


def corpus_synthetique(d):
    """CONTROLE NUL. Corpus PROPRE ecrit a la main : tout doit sortir a exactement zero.
    Trois entites en ligne droite a 4 m/s, un tir avec projectile, un impact, une mort chainee."""
    os.makedirs(d, exist_ok=True)
    dt, N = 0.2, 100
    with open(os.path.join(d, 'events.jsonl'), 'w') as f:
        for i in (1, 2, 3):
            f.write(json.dumps({'evt': 'spawn', 't': 0.0, 'id': i,
                                'x': 100.0 * i, 'y': 0.0, 'z': 0.0, 'side': i % 2}) + '\n')
        f.write(json.dumps({'evt': 'fired', 't': 5.0, 'shooter': 1, 'proj': 1}) + '\n')
        f.write(json.dumps({'evt': 'hit', 't': 5.1, 'target': 2, 'shooter': 1, 'dmg': 0.6}) + '\n')
        f.write(json.dumps({'evt': 'killed', 't': 6.0, 'victim': 2, 'killer': 1}) + '\n')
    with open(os.path.join(d, 'state.jsonl'), 'w') as f:
        for k in range(N):
            t = round(k * dt, 2)
            ents = []
            for i in (1, 2, 3):
                mort = (i == 2 and t >= 6.0)
                vivant = 0 if mort else 1
                # UN CADAVRE GARDE SA DERNIERE POSITION. Premiere version fautive : je la remettais
                # a zero, soit un saut de 24 m en 0,2 s — 120 m/s. Le controle nul l a attrape, ce
                # qui est exactement son role : c etait mon corpus << propre >> qui etait sale.
                y = round(4.0 * (6.0 if mort else t), 2)
                ents.append([i, 100.0 * i, y, 0.0, vivant, i % 2, 0])
            f.write(json.dumps({'t': t, 'tick': k + 1, 'n_total': 3, 'ents': ents,
                                'incomplet': False}) + '\n')
    json.dump({'dt_nominal': dt, 'monde': {'sha256': 'synthetique'}}, open(os.path.join(d, 'meta.json'), 'w'))


ap = argparse.ArgumentParser()
ap.add_argument('--session')
ap.add_argument('--controles', action='store_true')
a = ap.parse_args()

if a.controles:
    echecs = []
    tmp = tempfile.mkdtemp(prefix='audit_ctrl_')
    try:
        # --- 1. CONTROLE NUL ---
        d = os.path.join(tmp, 'nul'); corpus_synthetique(d)
        etats, evts, meta = charger(d)
        r, extra = auditer(etats, evts, meta)
        print()
        afficher(r, extra, 'CONTROLE 1 — NUL (doit sortir a EXACTEMENT zero)')
        non_nuls = {k: v for k, v in r.items() if v[0] != 0}
        if non_nuls:
            print('  >>> RATE : %s' % non_nuls)
            echecs.append('nul')
        else:
            print('  >>> OK : les sept taux valent exactement zero.')

        # --- 3. FAUSSETE DU CHAINAGE (sur le corpus synthetique, chainage connu = 100 %) ---
        r2, e2 = auditer(etats, evts, meta, decalage_impacts=300.0)
        tr = e2['morts_tracees_pct']
        print()
        print('=== CONTROLE 3 — FAUSSETE DU CHAINAGE ===')
        print('  impacts decales de +300 s : morts adossees %.1f %% (doit tomber sous 5 %%)' % tr)
        if tr is None or tr >= 5.0:
            print('  >>> RATE : la fenetre de 5 s apparie par hasard, « mort tracee » ne veut rien dire.')
            echecs.append('faussete')
        else:
            print('  >>> OK : le chainage s effondre quand on le fausse. Le critere mesure quelque chose.')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        # --- 4. CANARI DE FALSIFIABILITE DE LA COUPE NEUVE ---
        # Une coupe qui ne sait pas echouer n a pas le droit de passer. On injecte UNE mort
        # illegitime par cas limite et on exige que la coupe la compte, exactement une fois.
        print()
        print('=== CONTROLE 4 — FALSIFIABILITE DE LA COUPE NEUVE ===')
        for nom_cas, mort in (('tueur nul', {'evt': 'killed', 't': 7.0, 'victim': 3, 'killer': -1}),
                              ('tueur = victime', {'evt': 'killed', 't': 7.0, 'victim': 3, 'killer': 3}),
                              ('tueur jamais recense', {'evt': 'killed', 't': 7.0, 'victim': 3, 'killer': 999})):
            r3, _ = auditer(etats, evts + [mort], meta)
            num, den = r3['morts_sans_tueur']
            ok = (num == 1 and den == 2)
            print('  [%s] %-22s -> %d mort(s) sans tueur sur %d (attendu 1 sur 2)'
                  % ('OK ' if ok else 'RATE', nom_cas, num, den))
            if not ok:
                echecs.append('falsifiabilite:%s' % nom_cas)
        # et la mort legitime du corpus propre ne doit PAS mordre
        r4, _ = auditer(etats, evts, meta)
        if r4['morts_sans_tueur'][0] != 0:
            print('  [RATE] la mort legitime est comptee a tort')
            echecs.append('falsifiabilite:faux positif')
        else:
            print('  [OK ] la mort legitime n est PAS comptee')
    print()
    print('CONTROLES_HORS_LIGNE : %s' % ('TOUS VERTS' if not echecs else 'ECHECS -> %s' % echecs))
    print('  (le controle 2, le canari, demande le serveur : canari_audit.py)')
    sys.exit(0 if not echecs else 5)

if not a.session:
    sys.exit('donner --session <dossier> ou --controles')
etats, evts, meta = charger(a.session)
if not etats:
    sys.exit('REFUS : aucun tick d etat dans %s' % a.session)
r, extra = auditer(etats, evts, meta)
ok = afficher(r, extra, 'AUDIT DE CONTAMINATION — %s' % os.path.basename(a.session.rstrip('/')))
print()
print('VERDICT : %s' % ('CORPUS PROPRE (tous les taux sous 1 %)' if ok
                        else 'CORPUS SALE — un taux au moins depasse 1 %. Ne pas entrainer dessus.'))
