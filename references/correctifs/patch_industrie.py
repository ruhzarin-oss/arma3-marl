"""29/09 ( HMT-140, cause 5, suite ) : l industrie au reel - chaque mine, carriere et fonderie ( les sites de d10 ) a le
PLUS GRAND de son niveau reel ( la part de son secteur dans l emploi grec ) et du travail qu elle fournit ( ses heures
payees mesurees ) ; les postes liberes vont aux metiers ouverts par le remplissage vers la structure reelle de
population.effectifs ( ACCUEIL : agriculture et commerce ). La taille du pays ne change pas. Idempotent. A passer APRES
patch_convoyeurs ( il se place devant son etape, qui reste la derniere ). Ancres propres : ni la ligne de POSTES_PAR_SITE
ni `_lieux_ponderes` ( que le bras de la raffinerie reecrit ), ni le corps d `effectifs` ou de `_effectif_patrons` ( ou
ancrent la politique par ile et la raffinerie ) ; se compose avec eux dans n importe quel ordre.
  - un depot d aujourd hui ( `def effectifs` ) : les postes par site de la mine, de la carriere et de la fonderie changes
    dans POSTES_PAR_SITE ( la cle de la raffinerie n est pas touchee ), et `_lieux_ponderes` enveloppee pour des postes non
    entiers ( la suite de Sainte-Lague ) ; ancre : le debut de l etape des convoyeurs ;
  - un arbre d origine ou l ancien moteur temoin ( la boucle des effectifs d E1 ) : la meme etape, qui enveloppe
    `_effectif_patrons` sans reecrire sa ligne `def`, et les lieux de travail des mineurs et des ouvriers donnes par la
    meme suite ; ancres : le debut de l etape des convoyeurs, les trois lignes des candidats de `generer`.
   python patch_industrie.py <racine>      ( racine/monde/... pour un depot, racine/... pour le temoin )"""
import os, sys
racine = sys.argv[1]
base = os.path.join(racine, "monde") if os.path.exists(os.path.join(racine, "monde", "population.py")) else racine
fp = os.path.join(base, "population.py")
s = open(fp).read()
if "def postes_reels(" in s: print("deja :", fp); sys.exit(0)
ANCRE = "\n\n# ================================================================== les convoyeurs au reel ( 29/09, HMT-140 cause 5 )\n"
assert s.count(ANCRE) == 1, (fp, "patch_convoyeurs doit passer avant")


def sub(t, a, b, f):
    assert t.count(a) == 1, (f, a[:70], t.count(a))
    return t.replace(a, b)


# ------------------------------------------------------------------ la regle, commune aux deux formes
REGLE = '''

# ================================================================== l industrie au reel ( 29/09, HMT-140 cause 5, suite )
# Le monde E1 donne 40 mineurs et 40 ouvriers par unite d echelle ( 500 habitants ) : a 10 000 habitants, Altis emploie
# 735 personnes a ses six sites de d10 ( une mine, trois carrieres, deux fonderies ), 7 % de sa population, pour 0,15 a
# 3,8 heures payees par personne et par jour ( session du moteur, 29/09 : 120 jours, graine 71 ). Le reel : 1,5 % de
# l emploi grec ( B, C24, C25 ). Chaque site a desormais, par unite d echelle, le PLUS GRAND de deux niveaux, pour ne pas
# affamer un site qui travaille :
#  - le REEL : la part de son secteur dans l emploi de la Grece en 2024 ( Eurostat lfsa_egan22d, milliers de personnes de
#    15-74 ans, 4 265,9 en tout ) - mine : minerais metalliques ( B07 ) 2,3 ; carriere : autres industries extractives
#    ( B08 ) 4,6 ; fonderie : metallurgie ( C24 ) 17,1 et produits metalliques ( C25 ) 47,3, car la fonderie du moteur
#    est une acierie integree avec forge et usinage ( d10, PLAN_ALTIS ). La part, portee aux 306 travailleurs civils d une
#    unite d echelle ( config.ROLES ), se partage entre les sites du type sur Altis ;
#  - le TRAVAIL FOURNI : les heures payees par jour du calendrier ( jours 11 a 120 ; le site du type qui travaille le plus,
#    sur les deux mesures du moteur, avant et apres la reparation du demarrage ) en emplois a plein temps de 1 880 heures
#    par an ( OCDE, comme d10 ; un site ferme le samedi, le dimanche et les feries : 8 heures par jour compteraient un
#    ouvrier qui travaille 7 jours sur 7 ), rapportees aux nes : le recensement du domaine 4 ne laisse a son poste qu une
#    partie des nes ( mine : 136 des 200 ).
# Mine : travail 4,94 par unite ( reel 0,17 ) ; carriere : travail 0,83 ( reel 0,11 ) ; fonderie : reel 2,31 ( travail
# 1,40 ). A 10 000 habitants : 99 a la mine, 17 par carriere, 46 par fonderie, soit 241 au lieu de 1 040.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_egan22d?geo=EL&time=2024&sex=T&age=Y15-74&unit=THS_PER
EMPLOI_GRECE_2024 = 4265.9
EMPLOI_SECTEUR_2024 = {"mine": 2.3, "carriere": 4.6, "fonderie": 17.1 + 47.3}
SITES_D_ALTIS = {"mine": 1, "carriere": 3, "fonderie": 2}
# le site qui travaille le plus : heures payees par jour, equipe moyenne, nes ( Altis a l echelle 20 )
TRAVAIL_MESURE = {"mine": (345.3, 135.8, 200), "carriere": (58.4, 137.3, 200), "fonderie": (98.0, 81.8, 120)}
ECHELLE_MESURE = 20.0
HEURES_PLEIN_TEMPS_J = 1880.0 / 365.0
CIVILS_E1 = sum(k for r, (k, _, _) in C.ROLES.items() if r not in ("enfant", "retraite", "soldat", "officier"))
LONGUEUR_SUITE = 1 << 16      # au-dela ( plus de ~ 65 000 travailleurs d un metier ), la suite recommence


def postes_reels(t):
    """Les postes d un site de d10 ( mine, carriere, fonderie ) par unite d echelle : max( reel, travail fourni )."""
    reel = EMPLOI_SECTEUR_2024[t] / EMPLOI_GRECE_2024 * CIVILS_E1 / SITES_D_ALTIS[t]
    h, equipe, nes = TRAVAIL_MESURE[t]
    return max(reel, h / HEURES_PLEIN_TEMPS_J * nes / equipe / ECHELLE_MESURE)


def _suite_des_postes(lieux, poids, longueur=LONGUEUR_SUITE):
    """Les lieux dans l ordre ou ils recoivent leurs postes : un chacun d abord ( dans l ordre de la carte ), puis au plus
    fort quotient poids / ( 2 s + 1 ), s les postes deja recus ( Sainte-Lague ) ; a egalite, le premier de la carte. Chaque
    prefixe est un partage au prorata des poids, a une personne pres : le tour de role de la generation ( les N premiers
    de la liste ) pourvoit chaque site comme ses postes, a toute echelle, meme avec des postes non entiers."""
    w = np.asarray(poids, np.float64)
    m = np.floor(longueur * w / w.sum()).astype(np.int64) + 3
    site = np.repeat(np.arange(len(w)), m)
    rang = np.concatenate([np.arange(k) for k in m.tolist()])
    prio = np.where(rang == 0, np.inf, w[site] / (2.0 * rang + 1.0))
    ordre = np.lexsort((site, -prio))[:longueur]
    return [lieux[i] for i in site[ordre].tolist()]


_SUITES = {}


def _suite_en_cache(lieux, poids):
    """_suite_des_postes, gardee pour les memes lieux ( les memes objets, tenus par le cache ) et les memes poids."""
    cle = (tuple(id(l) for l in lieux), tuple(float(x) for x in poids))
    v = _SUITES.get(cle)
    if v is None:
        if len(_SUITES) >= 16: _SUITES.pop(next(iter(_SUITES)))
        v = _SUITES[cle] = (tuple(lieux), _suite_des_postes(lieux, poids))
    return v[1]'''

if "def effectifs(" in s:
    # --- un depot d aujourd hui : les postes de rule b, et le partage des postes non entiers
    s = sub(s, ANCRE, REGLE + '''


POSTES_REELS = {t: postes_reels(t) for t in SITES_D_ALTIS}
POSTES_PAR_SITE["mineur"] = {**POSTES_PAR_SITE["mineur"], "mine": POSTES_REELS["mine"], "carriere": POSTES_REELS["carriere"]}
POSTES_PAR_SITE["ouvrier"] = {**POSTES_PAR_SITE["ouvrier"], "fonderie": POSTES_REELS["fonderie"]}   # la raffinerie : inchangee

_lieux_avant_industrie = _lieux_ponderes


def _lieux_aux_postes(carte, role, *n):
    """`_lieux_ponderes` ( la fonction d avant ) ; des postes non entiers ( les sites de d10 au reel ) sans effectif donne :
    la suite de Sainte-Lague, dont chaque prefixe est au prorata des postes. Un effectif donne ( le bras de la raffinerie
    partage lui-meme au plus fort reste ) ou des postes entiers gardent la fonction d avant."""
    poids = POSTES_PAR_SITE.get(role)
    if poids is None or (n and n[0] is not None): return _lieux_avant_industrie(carte, role, *n)
    lieux = carte.de_type(*TRAVAIL[role][0])
    if not lieux or all(float(poids[l.type]).is_integer() for l in lieux): return _lieux_avant_industrie(carte, role, *n)
    return _suite_en_cache(lieux, [poids[l.type] for l in lieux])


_lieux_ponderes = _lieux_aux_postes''' + ANCRE, fp)
    open(fp, "w").write(s); print("corrige :", fp)
    sys.exit(0)

# --- un arbre d origine ou le temoin : la boucle d E1 corrigee par patch_patrons, puis l etape des convoyeurs
assert "_effectif_patrons" in s and "import numpy as np" in s, (fp, "patch_patrons et patch_convoyeurs doivent passer avant")
s = sub(s, ANCRE, REGLE + '''


# les postes par site par unite d echelle, ceux de population.POSTES_PAR_SITE ( regle b ) avec les sites de d10 au reel
POSTES_INDUSTRIE = {"mineur": {"mine": postes_reels("mine"), "carriere": postes_reels("carriere")}, "petrolier": {"puits": 15},
                    "ouvrier": {**C.OUVRIERS_PAR_SITE, "fonderie": postes_reels("fonderie")}}


def industrie_au_reel(carte, eff, echelle):
    """Les metiers industriels a leurs postes ( ceux des sites de la carte, a l echelle ; un metier sans site : 0 ), le
    surplus aux metiers ouverts par le remplissage vers la structure reelle, comme population.effectifs."""
    eff = dict(eff)
    surplus = 0
    for r, par_site in POSTES_INDUSTRIE.items():
        x = sum(par_site[l.type] for l in carte.de_type(*par_site)) * echelle
        k = max(1, int(round(x))) if x else 0
        surplus += eff[r] - k
        eff[r] = k
    ouverts = [r for r in ACCUEIL_CONVOYEURS if _metier_ouvert(carte, r)]
    if surplus and ouverts:
        c = [float(eff[r]) for r in ouverts]
        d = _remplir_vers(c, [ACCUEIL_CONVOYEURS[r] for r in ouverts], max(0.0, sum(c) + surplus)) - np.asarray(c)
        k = int(round(abs(d.sum())))
        d = np.sign(surplus) * _parts_entieres(k, np.abs(d))
        for r, x in zip(ouverts, d.tolist()): eff[r] += int(x)
    return eff


_effectif_avant_industrie = _effectif_patrons


def _effectif_industrie(carte, role, n, echelle):
    """L effectif d un metier a la naissance ( la fonction d avant, quelle qu elle soit ), l industrie au reel appliquee ;
    un metier d effectif nul a 0. Elle prend le nom de la fonction qu elle enveloppe, sans redefinir sa ligne `def`."""
    eff = {r: (_effectif_avant_industrie(carte, r, k, echelle) if k else 0) for r, (k, _, _) in C.ROLES.items()}
    return industrie_au_reel(carte, eff, echelle)[role]


_effectif_patrons = _effectif_industrie


def _lieux_industrie(carte, role, types):
    """Les lieux de travail d un metier pour le tour de role, comme population._lieux_ponderes : des postes entiers
    repetent chaque site selon ses postes divises par leur plus grand diviseur commun ( la liste d E1 : les ouvriers
    14, 3, 6, 5 ; les mineurs une fois chaque site ) ; des postes non entiers donnent la suite de Sainte-Lague."""
    lieux = carte.de_type(*types)
    poids = POSTES_INDUSTRIE.get(role)
    if poids is None or not lieux: return lieux
    if all(float(poids[l.type]).is_integer() for l in lieux):
        g = int(np.gcd.reduce([int(poids[l.type]) for l in lieux]))
        return [l for l in lieux for _ in range(int(poids[l.type]) // g)]
    return _suite_en_cache(lieux, [poids[l.type] for l in lieux])''' + ANCRE, fp)
s = sub(s, '''        elif h.role == "ouvrier":         # les ouvriers vont ou il faut des bras : la raffinerie d abord
            cands = [l for l in carte.de_type(*types) for _ in range(C.OUVRIERS_PAR_SITE[l.type])]
        else: cands = carte.de_type(*types)
''', '''        else: cands = _lieux_industrie(carte, h.role, types)   # ( 29/09 ) les sites de d10 a leurs postes reels
''', fp)
open(fp, "w").write(s); print("corrige :", fp)
