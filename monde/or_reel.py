"""L ETALON-OR DE L ARCHIPEL ( phase F1 ; decisions de Younes le 24-25/09 ) : chaque monnaie est un POIDS D OR.

- Le cours REEL de l or : prix mensuel en dollars l once ( jeu de donnees ouvert « gold-prices », GitHub datasets ),
  divise par le dollar du jour en euros ( taux de reference quotidien de la BCE ), interpole jour par jour sur le
  logarithme : des euros par gramme ( 1 once troy = 31,1034768 g ). Fichiers dans donnees/or/.
- Le monde vit 20 ans apres le reel : le 15 juin 2035 du monde est le 15 juin 2015 reel ( decision du 25/09 ).
- Chaque pays a sa monnaie ( config.MONNAIES ), definie par un poids d or : au jour 0, une unite vaut 1,15 euro
  ( la parite de depart du pays ), pour les six. Ensuite sa valeur en euros suit l or : taux = poids x cours. Entre
  deux iles, le change est le rapport des poids d or. Si l Etat devalue ( domaine 7 ), c est son poids d or qui baisse,
  et il le garde.
- Le prix mondial de l or ( domaine 7 ) suit la serie reelle ; en monnaie du pays, un gramme d or vaut donc toujours
  1 / poids unites : c est l etalon.

   python -m monde.or_reel            ( affiche la serie et les parites )"""
import csv, datetime as dt, math, os, sys
import numpy as np
from . import config as C

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "donnees", "or")
GRAMMES_PAR_ONCE = 31.1034768
DECALAGE_ANS = 20
HEURE = 5 + 50 / 60                      # apres les prix mondiaux du domaine 7 ( 5 h 40 )

_SERIE = None


def serie():
    """( jours ordinaux, euros par gramme ) : la serie quotidienne, construite une fois."""
    global _SERIE
    if _SERIE is not None: return _SERIE
    mois = []
    with open(os.path.join(DOSSIER, "or_usd_mensuel.csv")) as f:
        for r in csv.DictReader(f):
            a, m = map(int, r["Date"].split("-"))
            if a >= 1999: mois.append((dt.date(a, m, 15).toordinal(), float(r["Price"])))
    usd = {}
    with open(os.path.join(DOSSIER, "bce_eur_usd.csv")) as f:
        for r in csv.DictReader(f):
            if r["OBS_VALUE"]: usd[dt.date.fromisoformat(r["TIME_PERIOD"]).toordinal()] = float(r["OBS_VALUE"])
    j0, j1 = max(mois[0][0], min(usd)), min(mois[-1][0], max(usd))
    jours = np.arange(j0, j1 + 1)
    mx, my = np.array([m[0] for m in mois]), np.log([m[1] for m in mois])
    or_usd = np.exp(np.interp(jours, mx, my))                  # dollars l once, interpole sur le logarithme
    kx = np.array(sorted(usd)); ky = np.array([usd[k] for k in kx])
    usd_par_eur = np.interp(jours, kx, ky)                     # dollars pour un euro ( jours feries : interpole )
    _SERIE = (jours, or_usd / usd_par_eur / GRAMMES_PAR_ONCE)
    return _SERIE


def date_reelle(jour_du_monde):
    d = dt.date(*C.DATE_DEPART[:3]) + dt.timedelta(days=int(jour_du_monde))
    return d.replace(year=d.year - DECALAGE_ANS)


def euros_par_gramme(date):
    """Le cours reel de l or ce jour-la ( au-dela de la serie : la derniere valeur connue )."""
    jours, prix = serie()
    k = int(np.clip(date.toordinal() - jours[0], 0, len(jours) - 1))
    return float(prix[k])


# ------------------------------------------------------------------ dans un pays ( routine de 5 h 50 )
def installer(w, p):
    """Pose l etalon-or d un pays : son poids d or ( 1,15 euro l unite au jour 0 ) et sa routine du matin."""
    from .pays import d07_exterieur as EXT
    e = EXT._ext(p)
    p0 = euros_par_gramme(date_reelle(p.jour))
    w.etalon_or = {"monnaie": C.MONNAIES[w.carte.iles[0]], "poids_g": e.taux / p0, "cours0": p0, "dernier_taux": e.taux}
    p.routine(HEURE, 6, "archipel_or", etalon_or)


def etalon_or(p):
    from .pays import d07_exterieur as EXT
    w = p.w; e = EXT._ext(p); o = w.etalon_or
    if abs(e.taux - o["dernier_taux"]) > 1e-12 * o["dernier_taux"]:
        # l Etat a devalue ( ou reevalue ) depuis hier : c est son poids d or qui a change, il le garde
        o["poids_g"] *= e.taux / o["dernier_taux"]
    cours = euros_par_gramme(date_reelle(p.jour))
    i = EXT._id(p, "or")
    e.monde.x[i] = math.log(cours / o["cours0"])               # le prix mondial de l or suit la serie reelle
    taux = o["poids_g"] * cours
    EXT.fixer_parite(p, taux)                                  # ( recalcule les prix au port, suit les reserves )
    o["dernier_taux"] = e.taux
    o["cours"] = cours


def main():
    jours, prix = serie()
    print(f"serie : {dt.date.fromordinal(int(jours[0]))} -> {dt.date.fromordinal(int(jours[-1]))}, {len(jours)} jours")
    for j in (0, 365, 3650, 3650 + 365 * 5, 3650 * 3):
        d = date_reelle(j); c = euros_par_gramme(d)
        print(f"  jour {j:5d} du monde = {d} reel : {c:7.2f} euros le gramme -> une unite vaut {1.15 * c / euros_par_gramme(date_reelle(0)):.3f} euros")
    return 0


if __name__ == "__main__":
    sys.exit(main())
