#!/usr/bin/env python3
"""manuel.py — LE RÉPERTOIRE DOCTRINAL : six manœuvres du manuel, figées.

Le manuel n'est PAS un référentiel de vérité : il n'a pas mesuré Arma, il a mesuré des
hommes qui ont peur, des radios en panne et de la logistique. Il sert ici à deux choses,
et à rien d'autre :

  1. FOURNIR LES COUPS. Le banc n'en avait que deux (frontal, débordement) avec des
     paramètres posés à la main. Six coups, c'est un répertoire — et un répertoire permet
     enfin de poser la vraie question : QUELLE manœuvre pour QUELLE situation.
  2. FOURNIR DES PRÉDICTIONS FALSIFIABLES. Chaque manœuvre arrive avec sa CONDITION
     D'EMPLOI telle que le manuel l'énonce. Cette condition est une prédiction pré-enregistrée,
     pas une justification. Arma tranche.

Ce que ce fichier NE fait PAS : décider. Le choix de la manœuvre reste appris — c'est le
patron de la brique 0 (géométrie × manœuvre, sélecteur adaptatif +13 contre la meilleure
fixe). Coder le choix, ce serait écrire la réponse.

Espace d'action du bac à sable (postures=True, 13 actions) :
    0-7  = caps de 45 deg     8 = HOLD     9 = SUPPRESS     10/11/12 = debout/accroupi/couché
Les postures sont COLLANTES : les poser coûte un pas sans mouvement.
"""
import math
import torch


def cap(dx, dy):
    """cap 0-7 vers le vecteur (dx,dy) ; l'objectif est à l'origine"""
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def _vers_objectif(e):
    return cap(-e.apx, -e.apy)


def _tangente(e, sens=1.0):
    """perpendiculaire à l'axe de l'objectif ; sens=+1 un flanc, -1 l'autre"""
    return cap(-e.apy * sens, e.apx * sens)


def _masque_premiers(e, n):
    m = torch.zeros(e.N, e.A, dtype=torch.bool, device=e.dev)
    m[:, :min(n, e.A)] = True
    return m


def _d_obj(e):
    return torch.sqrt(e.apx ** 2 + e.apy ** 2)


# ----------------------------------------------------------------------------------
# 1. ASSAUT FRONTAL DÉLIBÉRÉ
# ----------------------------------------------------------------------------------
def frontal_delibere(e, t):
    """Tout le monde droit sur l'objectif, sans élément d'appui.
    MANUEL : réservé au rapport de forces écrasant ou à la défense négligeable ;
    c'est la manœuvre de référence, pas une bonne manœuvre."""
    return _vers_objectif(e)


# ----------------------------------------------------------------------------------
# 2. APPUI-MOUVEMENT (base de feu + élément d'assaut)
# ----------------------------------------------------------------------------------
def appui_mouvement(e, t, part_appui=0.34):
    """La base de feu se met à portée et SUPPRIME sans discontinuer ; l'élément d'assaut
    ferme droit devant, protégé par ce feu.
    MANUEL : la manœuvre fondamentale. Elle exige que la base de feu ATTEIGNE réellement
    l'adversaire — hors de portée, elle n'est qu'un tiers de la force en moins."""
    n_appui = max(1, int(round(e.A * part_appui)))
    appui = _masque_premiers(e, n_appui)
    act = _vers_objectif(e)
    a_portee = _d_obj(e) < e.fire_range * 0.9
    act = torch.where(appui & a_portee, torch.full_like(act, 9), act)      # en position : on supprime
    act = torch.where(appui & ~a_portee, _vers_objectif(e), act)           # sinon on se met à portée
    return act


# ----------------------------------------------------------------------------------
# 3. DÉBORDEMENT SIMPLE
# ----------------------------------------------------------------------------------
def debordement_simple(e, t, n_fixe=2, pas_crochet=14):
    """Un élément FIXE au contact et occupe l'arc de tir ; le reste crochète large et
    rentre hors du cône défensif.
    MANUEL : exige un angle mort exploitable et un élément de fixation capable de fixer.
    Sans fixation crédible, le crochet arrive seul contre une défense intacte."""
    act = _vers_objectif(e)
    fixe = _masque_premiers(e, n_fixe)
    a_portee = _d_obj(e) < e.fire_range * 0.9
    act = torch.where(fixe & a_portee, torch.full_like(act, 9), act)
    act = torch.where(fixe & ~a_portee, _vers_objectif(e), act)
    if t < pas_crochet:
        act = torch.where(~fixe, _tangente(e, 1.0), act)
    return act


# ----------------------------------------------------------------------------------
# 4. DÉBORDEMENT DOUBLE
# ----------------------------------------------------------------------------------
def debordement_double(e, t, n_fixe=2, pas_crochet=14):
    """Fixation au centre, deux crochets symétriques sur les deux flancs.
    MANUEL : prend la défense en tenaille, mais divise la force en trois. Interdit sous
    un certain effectif : chaque branche peut être battue séparément."""
    act = _vers_objectif(e)
    fixe = _masque_premiers(e, n_fixe)
    a_portee = _d_obj(e) < e.fire_range * 0.9
    act = torch.where(fixe & a_portee, torch.full_like(act, 9), act)
    act = torch.where(fixe & ~a_portee, _vers_objectif(e), act)
    if t < pas_crochet:
        idx = torch.arange(e.A, device=e.dev).expand(e.N, e.A)
        gauche = (~fixe) & (idx % 2 == 0)
        droite = (~fixe) & (idx % 2 == 1)
        act = torch.where(gauche, _tangente(e, 1.0), act)
        act = torch.where(droite, _tangente(e, -1.0), act)
    return act


# ----------------------------------------------------------------------------------
# 5. INFILTRATION
# ----------------------------------------------------------------------------------
def infiltration(e, t, pas_disperse=20):
    """Aucun élément d'appui, aucun tir : on se fait petit et on passe entre les mailles.
    Chaque homme prend un axe propre puis converge tard sur l'objectif.
    MANUEL : exige du couvert et une défense NON continue. Lente, et sans réponse si
    elle est détectée — elle n'a pas de base de feu pour se dégager."""
    if t == 0:
        return torch.full((e.N, e.A), 11, dtype=torch.long, device=e.dev)   # accroupi : petite cible
    act = _vers_objectif(e)
    if t < pas_disperse:
        idx = torch.arange(e.A, device=e.dev).expand(e.N, e.A)
        # un éventail : chaque homme décale son cap d'un cran différent
        decal = (idx - (e.A - 1) // 2)
        act = (act + decal) % 8
    return act


# ----------------------------------------------------------------------------------
# 6. PROGRESSION PAR BONDS (bounding overwatch)
# ----------------------------------------------------------------------------------
def bonds_alternes(e, t, longueur_bond=4):
    """La force se coupe en deux. Un demi bondit pendant que l'autre SUPPRIME, puis
    on échange. Un élément est TOUJOURS en train de tirer.
    MANUEL : la progression sous feu observé. Coûte la moitié de la vitesse ; en échange
    l'adversaire n'a jamais un instant sans être sous le feu."""
    act = _vers_objectif(e)
    idx = torch.arange(e.A, device=e.dev).expand(e.N, e.A)
    premier_demi = idx < (e.A // 2)
    bond_pair = ((t // longueur_bond) % 2) == 0
    bondit = premier_demi if bond_pair else ~premier_demi
    a_portee = _d_obj(e) < e.fire_range * 0.9
    # celui qui ne bondit pas supprime s'il atteint, sinon il tient
    act = torch.where(~bondit & a_portee, torch.full_like(act, 9), act)
    act = torch.where(~bondit & ~a_portee, torch.full_like(act, 8), act)
    return act


MANOEUVRES = {
    'frontal_delibere': frontal_delibere,
    'appui_mouvement': appui_mouvement,
    'debordement_simple': debordement_simple,
    'debordement_double': debordement_double,
    'infiltration': infiltration,
    'bonds_alternes': bonds_alternes,
}

# CONDITIONS D'EMPLOI telles que le manuel les énonce, écrites comme PRÉDICTIONS.
# Elles ne justifient rien : elles se mesurent, et Arma tranche.
CONDITIONS = {
    'frontal_delibere':   "ne paie que contre une défense faible : doit être battu dès que la menace monte",
    'appui_mouvement':    "exige que la base de feu soit à portée : doit dominer le frontal partout où elle l'est",
    'debordement_simple': "exige un angle mort ET une fixation crédible : doit payer quand la défense a un arc étroit",
    'debordement_double':  "divise la force en trois : doit perdre contre le débordement simple à faible effectif",
    'infiltration':       "exige du couvert et une défense non continue : doit payer en exposition, pas en vitesse",
    'bonds_alternes':     "moitié de la vitesse contre un feu continu : doit payer là où le frontal s'enlise",
}
