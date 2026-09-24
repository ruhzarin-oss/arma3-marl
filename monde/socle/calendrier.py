"""LE CALENDRIER DU MONDE : la date, la semaine, les jours feries, les saisons, le soleil ( socle ).

Le moteur compte des pas de 10 minutes. Presque tout ce qui vit dans un pays suit pourtant un calendrier : on ne
travaille pas le dimanche, les ecoles ferment l ete, les recoltes ont leur saison, la nuit tombe plus tot en octobre
qu en juin. Un domaine qui a besoin du calendrier le lit ici, jamais dans sa propre table.

Le soleil. Le moteur E1 fixe le lever a 6,0 h et le coucher a 20,7 h ( config.LEVER, COUCHER ) : juste a la mi-juin,
faux ensuite. Le monde part le 15 juin et vit 120 jours ; a la mi-octobre, a la latitude d Altis, le soleil se couche
avant 19 h ( porte test_calendrier ). Ici le lever et le coucher suivent la date et la latitude."""
import datetime as dt, math
from .. import config as C

ORIGINE = dt.datetime(*C.DATE_DEPART)

# Jours feries : le calendrier grec, pris pour modele ( la drachme ; Altis et Stratis sont Lemnos et Agios Efstratios ).
# Source : les jours feries nationaux de la Grece ( loi ; liste du ministere du Travail ). Le report du 1er mai quand il
# tombe pendant la semaine sainte, decide chaque annee par arrete, n est pas modelise.
# A confirmer par Younes : un pays de six iles peut vouloir ses propres fetes.
FERIES_FIXES = ((1, 1, "nouvel_an"), (1, 6, "theophanie"), (3, 25, "fete_nationale"), (5, 1, "fete_du_travail"),
                (8, 15, "dormition"), (10, 28, "jour_du_non"), (12, 25, "noel"), (12, 26, "synaxe_theotokos"))
FERIES_PAQUES = ((-48, "lundi_pur"), (-2, "vendredi_saint"), (1, "lundi_de_paques"), (50, "lundi_de_pentecote"))

# Soleil : ( latitude en degres, nord positif ; heure du midi solaire moyen, en heure du monde ).
# Latitudes : celles des iles reelles qui ont servi de modele ( Lemnos 39,9 N ; Agios Efstratios 39,5 N ).
# Midi a 13,35 h : CALE sur les constantes du moteur, ( 6,0 + 20,7 ) / 2, soit l heure d ete grecque. A verifier en jeu.
# Les quatre autres iles : latitude a lire dans CfgWorlds >> ile >> latitude ( signe inverse chez Arma ) AVANT usage.
# En attendant, les demander leve LatitudeInconnue plutot que de leur preter le soleil d Altis.
SOLEIL = {"Altis": (39.9, 13.35), "Stratis": (39.5, 13.35)}
HAUTEUR_LEVER_DEG = -0.833      # centre du soleil a l horizon apparent : refraction ( 34' ) + demi-diametre ( 16' )

SAISONS_NORD = {12: "hiver", 1: "hiver", 2: "hiver", 3: "printemps", 4: "printemps", 5: "printemps",
                6: "ete", 7: "ete", 8: "ete", 9: "automne", 10: "automne", 11: "automne"}
OPPOSEE = {"hiver": "ete", "ete": "hiver", "printemps": "automne", "automne": "printemps"}


class LatitudeInconnue(KeyError):
    pass


def paques_orthodoxe(annee):
    """Paques orthodoxe, en date gregorienne : algorithme de Meeus pour le calendrier julien, plus les 13 jours
    d ecart entre les deux calendriers ( valable de 1900 a 2099 )."""
    if not 1900 <= annee <= 2099: raise ValueError(f"annee {annee} hors [1900 ; 2099] : l ecart julien change")
    a, b, c = annee % 4, annee % 7, annee % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    mois, jour = divmod(d + e + 114, 31)
    return dt.date(annee, mois, jour + 1) + dt.timedelta(days=13)


def lever_coucher(latitude, jour_annee, midi_h):
    """Heures du lever et du coucher, en heure du monde. Declinaison de Cooper ( 1969 ), approximation usuelle de
    l equation du temps : quelques minutes pres, assez pour dire s il fait jour."""
    if not -66.0 < latitude < 66.0: raise ValueError("au-dela des cercles polaires : jour ou nuit continus, non modelises")
    if not 1 <= jour_annee <= 366: raise ValueError(f"jour de l annee hors [1 ; 366] : {jour_annee}")
    decl = math.radians(23.45) * math.sin(2 * math.pi * (284 + jour_annee) / 365)
    b = 2 * math.pi * (jour_annee - 81) / 364
    eq_temps_min = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    phi = math.radians(latitude)
    cos_h = ((math.sin(math.radians(HAUTEUR_LEVER_DEG)) - math.sin(phi) * math.sin(decl))
             / (math.cos(phi) * math.cos(decl)))
    demi_jour = math.degrees(math.acos(max(-1.0, min(1.0, cos_h)))) / 15.0
    midi = midi_h - eq_temps_min / 60.0
    return midi - demi_jour, midi + demi_jour


class Calendrier:
    """La date du monde a partir de son compteur de pas, et ce qu elle implique."""
    __slots__ = ("origine", "minutes_par_pas", "_feries")

    def __init__(self, origine=ORIGINE, minutes_par_pas=C.MINUTES_PAR_PAS):
        if not 1 <= minutes_par_pas <= 1440: raise ValueError(f"minutes par pas hors [1 ; 1440] : {minutes_par_pas}")
        self.origine, self.minutes_par_pas = origine, minutes_par_pas
        self._feries = {}           # annee -> { date : nom }, calcule une fois par annee

    def date(self, pas):
        return self.origine + dt.timedelta(minutes=pas * self.minutes_par_pas)

    def jour_semaine(self, pas):
        """0 = lundi ... 6 = dimanche."""
        return self.date(pas).weekday()

    def feries(self, annee):
        f = self._feries.get(annee)
        if f is None:
            f = {dt.date(annee, m, j): nom for m, j, nom in FERIES_FIXES}
            p = paques_orthodoxe(annee)
            for ecart, nom in FERIES_PAQUES: f[p + dt.timedelta(days=ecart)] = nom
            self._feries[annee] = f
        return f

    def ferie(self, jour):
        if isinstance(jour, dt.datetime): jour = jour.date()
        return self.feries(jour.year).get(jour)

    def ouvre(self, jour):
        """Un jour ou l on travaille a horaire de bureau : du lundi au vendredi, hors jours feries."""
        if isinstance(jour, dt.datetime): jour = jour.date()
        return jour.weekday() < 5 and self.ferie(jour) is None

    def saison(self, jour, latitude):
        """La saison meteorologique ( decembre-fevrier = hiver au nord ). Sous les tropiques, les vraies saisons sont
        seche et humide : c est au domaine 8 ( climat ) de les dire."""
        s = SAISONS_NORD[jour.month]
        return s if latitude >= 0 else OPPOSEE[s]

    def soleil(self, ile, jour):
        if ile not in SOLEIL: raise LatitudeInconnue(f"{ile} : latitude non verifiee ( CfgWorlds >> {ile} >> latitude )")
        if isinstance(jour, dt.datetime): jour = jour.date()
        lat, midi = SOLEIL[ile]
        return lever_coucher(lat, jour.timetuple().tm_yday, midi)

    def nuit(self, ile, pas):
        d = self.date(pas)
        lever, coucher = self.soleil(ile, d.date())
        h = d.hour + d.minute / 60.0
        return not lever <= h < coucher
