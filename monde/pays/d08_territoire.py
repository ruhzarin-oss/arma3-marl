"""DOMAINE 8 - TERRITOIRE, CLIMAT, ENVIRONNEMENT.

FICHE
1. Classes. Les lois : ProfilClimatique ( les normales mensuelles d une ile, avec leur station modele et leur source ),
   Sismicite ( Gutenberg-Richter d une region ), TypeDeSol, Polluant. Les tableaux : TableClimat ( les normales
   JOURNALIERES de n stations, interpolees en conservant les moyennes mensuelles ), EtatMeteo ( la persistance du
   temps : chaine de Markov de la pluie, regime lent des annees seches, anomalies de temperature, vent, neige, KBDI,
   deficit de pluie ), MeteoDuJour ( le temps d un jour, par ile ), NormalesPays ( ce que le climat donne en moyenne un
   jour donne de l annee, MESURE en faisant vivre le generateur 32 ans a l installation : sols, irrigation, recharge,
   seuils de secheresse, remplissage des reserves ). L etat : Bassins ( les unites de gestion de l eau brute : une par
   ville ou capitale et les villages qui en dependent ; nappe et retenue en m3, bilan exact ), Parcelles ( une par
   village : surface, sol, part irriguee, deux reservoirs de sol ), Pollution ( masses par lieu et par bassin ),
   Catastrophe, ContexteEau, Territoire ( l etat du domaine ). Tout est en tableaux numpy indexes : portable en Rust.
2. Invariants. BILAN DE L EAU BRUTE, au m3, par bassin et par ile : stock - stock de depart = recharge de la nappe
   + ruissellement capte par la retenue - evaporation de la retenue - exutoire naturel de la nappe - debordements a la
   mer - prelevements + forcages de scenario ( porte test_bilan_eau ). Bilans des sols au mm : eau recue + irrigation =
   ruissellement + drainage + ETR + pertes d irrigation + variation de la reserve ; neige tombee - fonte = manteau.
   Bilan des polluants au kg : rejete - degrade - evacue = masse presente. L eau brute n est PAS un bien du catalogue :
   c est l etat du milieu. Le domaine ne DETIENT ni argent ni bien : aucune famille au registre.
3. Decision `gerer_eau` ( un gestionnaire par bassin, tous le meme jour, tous les 7 jours ) : aucune restriction,
   restriction legere, restriction severe des prelevements ( plans de secheresse par paliers ). Traits : remplissage,
   jours d autonomie, pluie des 30 derniers jours, pluie normale a venir, tendance, restriction en cours, penurie des
   7 derniers jours, classe de secheresse publiee. Note ( horizon 21 jours : une reserve se vide en semaines ) : 1 par
   jour sans penurie dans CE bassin, moins la part de la demande coupee par CETTE restriction. Regle : paliers en mois
   d autonomie ( severe sous un mois, legere sous trois ou en secheresse severe ). Temoin : jamais de restriction. Plusieurs bassins decident le meme jour : la part du
   choix se mesure a jour egal ( 21 bassins sur Altis ).
4. Evenements. Individuels : secheresse, fin_secheresse, inondation, seisme, cyclone, alerte_incendie,
   restriction_eau. Comptes : seisme_non_ressenti, penurie_eau ( m3 manquants ), prelevement_eau ( m3 ),
   rejet_polluant ( kg ).
5. Liens. Donne : la meteo du jour par ile ou par lieu, la saison, le rendement climatique d une parcelle, l eau
   disponible et `prelever`, `reprendre_usage`, `rejeter`, la pollution par lieu, le risque d incendie ( FFDI ), les
   catastrophes en cours ( avec l intensite MMI par lieu pour un seisme ). Recoit : les prelevements ( services
   publics 12, agriculture 9, industrie 10, energie 11 ) et les rejets ( industrie, energie, transport ). En attendant
   ces domaines, il fait lui-meme les prelevements de fond ( domestique, irrigation, industrie, energie ) et les rejets
   de fond des sites du moteur E1 ; un domaine qui reprend un usage appelle `reprendre_usage`. Pont avec le moteur E1 :
   tant que l agriculture ( 9 ) n est pas installee, le rendement climatique de chaque village entre dans `w.chocs`
   ( une DONNEE lue par Monde.facteur_choc ), compose avec les chocs poses par d autres. Rien n est remplace.
6. Portes : tests_d08_territoire.py.
7. Arma. La meteo du jour se traduit en commandes du moteur de jeu ( `vers_arma` : setOvercast, setRain, setWind,
   setFog ; BIS_fnc_earthquake pour un seisme ressenti ). arma_preuve = None : rien n a encore ete vu en jeu.
8. Cout. Tout est par ile, par bassin, par village ou par lieu : le cout ne suit PAS la population ( seuls le recensement
   hebdomadaire des menages par bassin et la lecture de la production des sites la touchent ). A l installation, les
   normales ( 32 annees de climat par ile, vectorisees ) coutent de l ordre de 0,2 s par ile."""
import math
import numpy as np
from ..socle import decision as D

# ================================================================== le calendrier du climat
JOURS_AN = 365
MOIS_J = np.array((31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31))
DEBUT_MOIS = np.concatenate(([0], np.cumsum(MOIS_J)[:-1]))
MOIS_DU_JOUR = np.repeat(np.arange(12), MOIS_J)          # jour de l an ( 0 a 364 ) -> mois ( 0 a 11 )
MILIEU_MOIS = DEBUT_MOIS + MOIS_J / 2.0


def quotidien(mensuel, iterations=30):
    """12 moyennes mensuelles -> 365 valeurs journalieres continues. Une interpolation lineaire entre les milieux de
    mois rabote les pics ( juillet trop frais, decembre trop sec ) : les ancres sont corrigees jusqu a ce que la
    moyenne de chaque mois interpole retrouve la normale ( a 1e-6 pres ), sans descendre sous zero."""
    cible = np.asarray(mensuel, float)
    if cible.shape != (12,): raise ValueError("12 valeurs mensuelles attendues")
    x = np.concatenate(([MILIEU_MOIS[-1] - JOURS_AN], MILIEU_MOIS, [MILIEU_MOIS[0] + JOURS_AN]))
    t = np.arange(JOURS_AN) + 0.5
    ancres = cible.copy()
    positif = bool((cible >= 0).all())
    for _ in range(iterations):
        y = np.interp(t, x, np.concatenate(([ancres[-1]], ancres, [ancres[0]])))
        if positif: y = np.maximum(y, 0.0)
        moy = np.add.reduceat(y, DEBUT_MOIS) / MOIS_J
        ecart = cible - moy
        if np.abs(ecart).max() < 1e-6: break
        ancres = ancres + ecart
    return y


def rayonnement_extraterrestre(latitude):
    """Ra, en mm d eau evaporable par jour, pour chaque jour de l an ( FAO-56, equations 21 a 25 )."""
    if not -66.0 < latitude < 66.0: raise ValueError("latitude hors des cercles polaires non modelisee")
    J = np.arange(1, JOURS_AN + 1)
    phi = math.radians(latitude)
    dr = 1 + 0.033 * np.cos(2 * np.pi * J / JOURS_AN)
    decl = 0.409 * np.sin(2 * np.pi * J / JOURS_AN - 1.39)
    ws = np.arccos(np.clip(-math.tan(phi) * np.tan(decl), -1.0, 1.0))
    ra = 24 * 60 / np.pi * 0.0820 * dr * (ws * math.sin(phi) * np.sin(decl) + math.cos(phi) * np.cos(decl) * np.sin(ws))
    return 0.408 * ra


# ================================================================== les climats des six iles
class ProfilClimatique:
    """Les normales mensuelles d une ile, prises sur une station reelle qui lui ressemble. Chaque serie a sa source ;
    ce qui n en a pas est « a calibrer ». Les jours de pluie sont ceux a >= 1 mm ( convention OMM ) : une station qui
    compte a 0,1 mm est convertie, et la conversion est ecrite.
      tmax, tmin    degres C, moyennes mensuelles des maximales et minimales
      pluie         mm par mois ; jours_pluie : jours >= 1 mm par mois
      hr            humidite relative moyenne, % ; vent : vitesse moyenne a 10 m, m/s
      sigma_t       ecart-type des anomalies journalieres de la temperature moyenne, degres C ( a calibrer )
      cyclones      cyclones tropicaux passant a moins de 200 km, par mois ( esperance )
      mois_humides  pour une ile tropicale, les mois de la saison humide ( 1 a 12 )"""
    __slots__ = ("ile", "station", "latitude", "tmax", "tmin", "pluie", "jours_pluie", "hr", "vent", "sigma_t",
                 "cyclones", "mois_humides", "source")

    def __init__(self, ile, station, latitude, tmax, tmin, pluie, jours_pluie, hr, vent, sigma_t, cyclones=None,
                 mois_humides=(), source="a calibrer"):
        tab = [np.asarray(v, float) for v in (tmax, tmin, pluie, jours_pluie, hr, vent, sigma_t)]
        if any(v.shape != (12,) for v in tab): raise ValueError(f"{ile} : 12 valeurs par serie")
        tmax, tmin, pluie, jours, hr, vent, sig = tab
        cyc = np.zeros(12) if cyclones is None else np.asarray(cyclones, float)
        if not -66.0 < latitude < 66.0: raise ValueError(f"{ile} : latitude {latitude}")
        if (tmax < tmin).any() or (tmax > 50).any() or (tmin < -40).any(): raise ValueError(f"{ile} : temperatures")
        if (pluie < 0).any() or (pluie > 1500).any(): raise ValueError(f"{ile} : pluie hors [0 ; 1500] mm par mois")
        if (jours < 0).any() or (jours > MOIS_J).any() or ((pluie > 0) & (jours <= 0)).any():
            raise ValueError(f"{ile} : jours de pluie hors [0 ; longueur du mois]")
        if (hr < 0).any() or (hr > 100).any() or (vent < 0).any() or (vent > 30).any(): raise ValueError(f"{ile} : hr ou vent")
        if (sig <= 0).any() or (sig > 15).any() or cyc.shape != (12,) or (cyc < 0).any() or (cyc > 2).any():
            raise ValueError(f"{ile} : sigma_t ou cyclones hors bornes")
        if any(not 1 <= m <= 12 for m in mois_humides): raise ValueError(f"{ile} : mois humides hors [1 ; 12]")
        self.ile, self.station, self.latitude = ile, station, float(latitude)
        self.tmax, self.tmin, self.pluie, self.jours_pluie, self.hr, self.vent, self.sigma_t = tmax, tmin, pluie, jours, hr, vent, sig
        self.cyclones, self.mois_humides, self.source = cyc, tuple(mois_humides), source

    def tropical(self): return abs(self.latitude) < 23.5

    def decale(self, mois):
        """Le meme profil decale de `mois` mois ( falsificateur de la porte du climat )."""
        r = lambda v: np.roll(v, mois)
        return ProfilClimatique(self.ile, self.station + f" decale de {mois} mois", self.latitude, r(self.tmax),
                                r(self.tmin), r(self.pluie), r(self.jours_pluie), r(self.hr), r(self.vent),
                                r(self.sigma_t), r(self.cyclones), self.mois_humides, self.source)


_LEMNOS = dict(
    station="Limnos ( aeroport de Myrina ), 39,9 N", latitude=39.9,
    tmax=(10.7, 11.0, 13.1, 17.1, 22.1, 27.2, 29.5, 29.1, 25.3, 20.3, 15.7, 12.3),
    tmin=(4.4, 4.5, 6.2, 9.0, 13.0, 17.3, 20.4, 20.7, 16.7, 12.9, 9.1, 6.2),
    pluie=(66.5, 55.6, 51.5, 36.4, 21.6, 15.5, 11.0, 6.3, 29.3, 43.9, 80.4, 84.7),
    jours_pluie=(11.3, 10.7, 9.6, 8.9, 6.6, 4.7, 2.1, 2.3, 4.0, 7.1, 10.1, 12.9),
    hr=(77.3, 74.9, 74.9, 73.4, 68.1, 59.9, 57.0, 61.0, 66.8, 73.7, 77.9, 78.5),
    vent=(5.6, 5.6, 5.2, 4.4, 3.9, 4.3, 5.6, 6.0, 5.2, 5.0, 5.4, 5.8),
    sigma_t=(2.2, 2.3, 2.2, 2.0, 1.8, 1.7, 1.6, 1.6, 1.7, 1.9, 2.1, 2.2))
_SOURCE_LEMNOS = ("HNMS et NOAA, normales 1974-2010 ( temperatures, pluie, jours de pluie, humidite ) ; vent moyen a "
                  "calibrer ( Limnos : 5 a 6 m/s, pointe du meltem en juillet-aout ) ; sigma_t a calibrer")

PROFILS = {
    # Altis et Stratis sont Lemnos et Agios Efstratios ( socle/calendrier.py ).
    "Altis": ProfilClimatique("Altis", source=_SOURCE_LEMNOS, **_LEMNOS),
    "Stratis": ProfilClimatique("Stratis", source="Agios Efstratios n a pas de normale publiee : celles de Limnos, a "
                                "30 km ( a calibrer )", **_LEMNOS),
    "Malden": ProfilClimatique(
        "Malden", "Ajaccio ( Campo dell Oro ), 41,9 N", 41.9,
        tmax=(14.0, 14.2, 16.0, 18.5, 22.1, 25.9, 28.6, 29.2, 26.1, 22.8, 18.3, 15.1),
        tmin=(4.7, 4.3, 5.9, 8.4, 11.8, 15.4, 17.7, 18.1, 15.4, 12.6, 9.0, 5.8),
        pluie=(54.1, 48.1, 50.4, 53.1, 49.8, 25.9, 8.6, 15.8, 57.8, 85.7, 111.8, 73.9),
        jours_pluie=(7.0, 6.7, 6.3, 7.2, 5.0, 2.8, 1.2, 1.4, 5.1, 7.4, 9.3, 8.6),
        hr=(81, 80, 80, 80, 80, 78, 76, 76, 78, 80, 81, 82),
        vent=(3.6, 3.7, 3.9, 3.9, 3.6, 3.5, 3.5, 3.4, 3.3, 3.4, 3.6, 3.6),
        sigma_t=(2.0, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.5, 1.6, 1.8, 1.9, 2.0),
        source="Meteo-France, normales 1991-2020 ; vent et sigma_t a calibrer"),
    "Tanoa": ProfilClimatique(
        "Tanoa", "Nadi ( Fidji ), 17,8 S", -17.8,
        tmax=(31.4, 31.5, 31.3, 30.8, 29.7, 29.0, 28.5, 28.6, 29.2, 30.1, 30.8, 31.4),
        tmin=(23.3, 23.3, 23.3, 22.6, 21.1, 20.1, 19.2, 19.4, 20.3, 21.3, 22.3, 23.0),
        pluie=(365.2, 335.5, 350.5, 187.8, 92.2, 57.0, 50.5, 64.7, 72.3, 87.0, 126.5, 210.2),
        jours_pluie=(14.1, 15.1, 16.2, 9.9, 4.9, 3.6, 3.1, 4.1, 4.7, 6.5, 8.7, 11.9),
        hr=(81, 82, 84, 82, 80, 79, 76, 75, 74, 75, 76, 78),
        vent=(3.4, 3.4, 3.3, 3.4, 3.6, 3.8, 4.0, 4.2, 4.3, 4.2, 3.9, 3.6),
        sigma_t=(0.9, 0.9, 0.9, 0.9, 1.0, 1.1, 1.1, 1.1, 1.0, 0.9, 0.9, 0.9),
        cyclones=(0.12, 0.12, 0.08, 0.03, 0, 0, 0, 0, 0, 0, 0.04, 0.08), mois_humides=(11, 12, 1, 2, 3, 4),
        source="OMM et NOAA, normales 1991-2020 ( Nadi ) ; cyclones : ordre de grandeur Fiji Meteorological Service, "
               "saison novembre-avril, ~0,5 par an a moins de 200 km d un point ( a calibrer sur SPEArTC ) ; vent a calibrer"),
    "Enoch": ProfilClimatique(   # Livonia
        "Enoch", "Vilnius, 54,7 N", 54.7,
        tmax=(-1.5, -0.4, 4.5, 12.7, 18.5, 21.8, 23.8, 23.1, 17.4, 10.3, 3.9, -0.1),
        tmin=(-6.0, -5.6, -2.7, 2.6, 7.5, 11.2, 13.6, 12.7, 8.5, 3.8, -0.1, -4.1),
        pluie=(48, 42, 41, 43, 56, 65, 92, 76, 57, 60, 47, 51),
        jours_pluie=tuple(round(0.62 * j, 1) for j in (21.7, 18.4, 17.5, 10.2, 12.4, 11.7, 11.4, 10.5, 9.7, 13.5, 16.7, 21.2)),
        hr=(86, 84, 78, 69, 67, 70, 72, 74, 79, 84, 88, 88),
        vent=(4.0, 3.9, 3.7, 3.4, 3.1, 2.9, 2.8, 2.8, 3.1, 3.5, 3.8, 4.0),
        sigma_t=(5.0, 4.8, 4.0, 3.0, 2.8, 2.5, 2.3, 2.3, 2.5, 3.0, 3.8, 4.6),
        source="Service hydrometeorologique lituanien et OMM, normales 1991-2020 ; jours >= 0,1 mm convertis en "
               "jours >= 1 mm par 0,62 ( a calibrer ) ; humidite, vent, sigma_t a calibrer"),
    "Sara": ProfilClimatique(    # Sahrani
        "Sara", "San Juan ( Porto Rico ), 18,4 N", 18.4,
        tmax=(28.4, 28.8, 29.3, 30.1, 30.8, 31.7, 31.5, 31.7, 31.8, 31.4, 30.1, 29.0),
        tmin=(22.2, 22.1, 22.4, 23.3, 24.3, 25.1, 25.3, 25.4, 25.3, 24.8, 23.8, 22.9),
        pluie=(103, 66, 55, 117, 141, 118, 153, 160, 165, 132, 187, 123),
        jours_pluie=tuple(round(0.75 * j, 1) for j in (12, 10, 10, 12, 14, 15, 15, 15, 16, 15, 14, 13)),
        hr=(74.0, 72.4, 71.0, 71.3, 74.9, 75.5, 75.9, 76.4, 76.4, 76.9, 76.2, 74.7),
        vent=(4.6, 4.6, 4.7, 4.6, 4.4, 4.9, 5.3, 4.8, 4.0, 3.6, 4.0, 4.5),
        sigma_t=(0.8,) * 12,
        cyclones=(0, 0, 0, 0, 0, 0.03, 0.05, 0.12, 0.14, 0.06, 0.02, 0), mois_humides=(5, 6, 7, 8, 9, 10, 11),
        source="NOAA, normales 1991-2020 ( San Juan ) ; jours >= 0,01 pouce convertis en jours >= 1 mm par 0,75 ( a "
               "calibrer ) ; cyclones : ordre de grandeur NOAA HURDAT2, saison juin-novembre ( a calibrer ) ; vent a calibrer"),
}
ILES_CONNUES = tuple(PROFILS)        # l ordre fixe les sous-flux de hasard des normales : ne pas le changer


# ================================================================== la sismicite
class Sismicite:
    """La loi de Gutenberg-Richter d une region : log10 N( >= M ) = a - b M. `n4_an` : seismes de fond de magnitude
    >= 4 par an a moins de `rayon_km` du centre de l ile ; les repliques s y ajoutent ( Reasenberg et Jones 1989 )."""
    __slots__ = ("n4_an", "b", "m_max", "rayon_km", "profondeur_km", "source")

    def __init__(self, n4_an, b, m_max, rayon_km, profondeur_km=(5.0, 20.0), source="a calibrer"):
        if not 0.0 <= n4_an <= 1000 or not 0.5 <= b <= 2.0 or not 4.5 <= m_max <= 9.5 or not 10 <= rayon_km <= 500:
            raise ValueError("sismicite hors bornes")
        if not 0 < profondeur_km[0] <= profondeur_km[1] <= 700: raise ValueError("profondeurs hors bornes")
        self.n4_an, self.b, self.m_max, self.rayon_km, self.profondeur_km, self.source = n4_an, b, m_max, rayon_km, profondeur_km, source


_EGEE_NORD = Sismicite(15.0, 0.95, 7.5, 120.0, source=(
    "Egee du Nord ( fosse nord-egeenne ) : b ~ 1 dans l Egee ( Papazachos et al., catalogues NOA et AUTH ) ; taux de "
    "fond a calibrer sur le catalogue declustere - il donne un M >= 6,8 tous les ~20 ans a 120 km de Lemnos "
    "( observe : 1968 M7,1 et 1982 M6,9 pres d Agios Efstratios, 2014 M6,9 )"))
SISMICITE = {
    "Altis": _EGEE_NORD,
    "Stratis": _EGEE_NORD,           # meme region : deux iles dans un meme monde tirent chacune la leur ( a revoir )
    "Malden": Sismicite(0.5, 1.0, 6.0, 120.0, source="Corse : sismicite faible ( a calibrer, BCSF )"),
    "Tanoa": Sismicite(3.0, 1.0, 7.2, 120.0, source="Fidji hors fosse des Tonga : moderee ( a calibrer, USGS )"),
    "Enoch": Sismicite(0.02, 1.0, 5.5, 120.0, source="Baltique : tres faible ( Kaliningrad 2004, M5,2 ) - a calibrer"),
    "Sara": Sismicite(8.0, 1.0, 7.8, 120.0, source="Porto Rico : fosse et zone des Iles Vierges ( 2020 M6,4 ) - a calibrer, PRSN"),
}
M_MIN = 4.0                     # plus petite magnitude simulee
M_SEQUENCE = 5.0                # un seisme de fond a partir duquel on suit ses repliques
RJ_A, RJ_B, RJ_C, RJ_P = -1.67, 0.91, 0.05, 1.08     # Reasenberg et Jones 1989, parametres generiques ( Californie )
SEQUENCE_J = 365
MMI = (3.67, 1.17, -3.19)       # MMI = a + b M + c log10( distance hypocentrale ) : forme de Bakun et Wentworth 1997, a calibrer pour l Egee
MMI_RESSENTI = 3.0


def magnitude_gr(sism, u):
    """Magnitude de Gutenberg-Richter tronquee a [M_MIN ; m_max] ( inversion de la loi exponentielle )."""
    b = sism.b
    return M_MIN - np.log10(1.0 - u * (1.0 - 10.0 ** (-b * (sism.m_max - M_MIN)))) / b


def intensite(magnitude, distance_km):
    return MMI[0] + MMI[1] * magnitude + MMI[2] * np.log10(np.maximum(distance_km, 5.0))


def seismes_du_jour(sism, sequences, jour, rng):
    """Les seismes d un jour dans la region d une ile : ceux du fond ( Poisson, magnitude de Gutenberg-Richter,
    epicentre uniforme dans le disque ) et les repliques des sequences en cours ( taux de Reasenberg et Jones integre
    sur la journee ). Un seisme de fond de M >= 5 ouvre une sequence qui compte des le jour meme. Les magnitudes des
    repliques suivent la meme loi ( comme dans ETAS ) : le catalogue entier reste de Gutenberg-Richter.
    Rend [ ( magnitude, x_km, y_km, profondeur_km, replique ) ] ; `sequences` ( [ M, jour, x, y ] ) est mis a jour."""
    out = []
    n = int(rng.poisson(sism.n4_an / JOURS_AN))
    for _ in range(n):
        m = float(magnitude_gr(sism, rng.random()))
        r = sism.rayon_km * math.sqrt(rng.random()); th = 2 * math.pi * rng.random()
        x, y = r * math.cos(th), r * math.sin(th)
        out.append((m, x, y, float(rng.uniform(*sism.profondeur_km)), False))
        if m >= M_SEQUENCE: sequences.append([m, jour, x, y])
    for s in sequences:
        t0 = jour - s[1]; t1 = t0 + 1
        lam = 10 ** (RJ_A + RJ_B * (s[0] - M_MIN)) * ((t0 + RJ_C) ** (1 - RJ_P) - (t1 + RJ_C) ** (1 - RJ_P)) / (RJ_P - 1)
        for _ in range(int(rng.poisson(lam))):
            m = float(magnitude_gr(sism, rng.random()))
            demi = 0.5 * 10 ** (-3.22 + 0.69 * s[0])            # demi-longueur de rupture ( Wells et Coppersmith 1994 )
            r = demi * math.sqrt(rng.random()); th = 2 * math.pi * rng.random()
            out.append((m, s[2] + r * math.cos(th), s[3] + r * math.sin(th), float(rng.uniform(*sism.profondeur_km)), True))
    sequences[:] = [s for s in sequences if jour + 1 - s[1] < SEQUENCE_J]
    return out


def catalogue(sism, jours, rng):
    """Le catalogue de `jours` jours de seismes, par la fonction du monde ( porte de Gutenberg-Richter )."""
    seq, out = [], []
    for j in range(jours): out.extend((j,) + e for e in seismes_du_jour(sism, seq, j, rng))
    return out


# ================================================================== les sols
class TypeDeSol:
    """Un sol : sa reserve utile ( mm d eau entre capacite au champ et point de fletrissement, sur la profondeur des
    racines ) et son numero de courbe SCS ( ruissellement, conditions moyennes )."""
    __slots__ = ("nom", "ru_mm", "cn2", "source")

    def __init__(self, nom, ru_mm, cn2, source):
        if not 10 <= ru_mm <= 400 or not 30 <= cn2 <= 98: raise ValueError(f"sol {nom} hors bornes")
        self.nom, self.ru_mm, self.cn2, self.source = nom, float(ru_mm), float(cn2), source


SOLS = (
    TypeDeSol("calcaire", 60, 80, "leptosol sur calcaire, ~0,4 m de terre : FAO-56 tableau 19 ; CN groupe C-D, a calibrer"),
    TypeDeSol("argileux", 160, 85, "FAO-56 tableau 19 ( argile 0,12-0,20 m3/m3 sur 1 m ) ; CN groupe D ( TR-55 )"),
    TypeDeSol("limoneux", 155, 72, "FAO-56 tableau 19 ( limon 0,13-0,18 ) ; CN groupe B ( TR-55 )"),
    TypeDeSol("sableux", 80, 60, "FAO-56 tableau 19 ( sable 0,05-0,11 ) ; CN groupe A ( TR-55 )"),
    TypeDeSol("volcanique", 180, 70, "andosol : forte retention, bonne infiltration - a calibrer"),
)
SOL_INDEX = {s.nom: k for k, s in enumerate(SOLS)}
SOL_RU = np.array([s.ru_mm for s in SOLS])
SOL_CN = np.array([s.cn2 for s in SOLS])
# Part de chaque sol par ile ( a calibrer : Lemnos est volcanique a l ouest, sedimentaire a l est )
SOLS_ILE = {"Altis": {"calcaire": 0.3, "argileux": 0.2, "limoneux": 0.3, "volcanique": 0.2},
            "Stratis": {"calcaire": 0.5, "volcanique": 0.5},
            "Malden": {"calcaire": 0.4, "limoneux": 0.4, "sableux": 0.2},
            "Tanoa": {"volcanique": 0.6, "argileux": 0.3, "sableux": 0.1},
            "Enoch": {"limoneux": 0.5, "sableux": 0.4, "argileux": 0.1},
            "Sara": {"calcaire": 0.3, "argileux": 0.4, "limoneux": 0.3}}
# Part irriguee des terres agricoles ( Grece : ~ 30 % de la SAU irriguee, Eurostat ; le reste a calibrer ) et indice
# d exploitation de l eau vise en annee normale ( WEI+ de l AEE : > 20 % = stress, > 40 % = stress severe ; iles de l Egee
# stressees - a calibrer ). Le monde E1 est une maquette ( 500 habitants sur 270 km2 ) : l eau exploitable est a l echelle
# de la maquette, dimensionnee pour que prelevements / ressource renouvelable = WEI.
IRRIGUE = {"Altis": 0.30, "Stratis": 0.20, "Malden": 0.25, "Tanoa": 0.05, "Enoch": 0.02, "Sara": 0.15}
WEI = {"Altis": 0.30, "Stratis": 0.35, "Malden": 0.20, "Tanoa": 0.05, "Enoch": 0.05, "Sara": 0.15}

# ================================================================== les lois du temps ( generateur de Richardson etendu, a calibrer )
SEUIL_PLUIE = 1.0                # mm : un jour de pluie
R_OCC = 0.30                     # persistance de la pluie : P( pluie | pluie ) - P( pluie | sec ) ( Wilks et Wilby 1999 : 0,2 a 0,5 )
ALPHA_MIXTE, B1_MIXTE, B2_MIXTE = 0.7, 0.4, 2.4    # hauteur d un jour de pluie : melange de deux exponentielles
#                                  ( Woolhiser et Roldan 1982 ) ; la seconde, 2,4 fois la moyenne, porte les pluies extremes
PHI_REGIME, BETA_REGIME = 0.99, 0.35   # regime lent ( ~100 jours ) : les saisons seches et humides d une annee a l autre
PI_MAX = 0.95
PHI_T, PART_LENTE = 0.7, 0.25    # anomalies de temperature : rapide ( 3 jours ) et lente ( le regime : sec = chaud )
DT_HUMIDE, DTR_HUMIDE = 1.0, 0.7 # un jour de pluie est plus frais ( degres C ) et son amplitude plus faible
PHI_VENT = 0.6
RACINE_PI_2 = math.sqrt(math.pi / 2)
HR_APREM, HR_PAR_C, HR_PLUIE = -12.0, -2.5, 10.0   # humidite de l apres-midi ( indice d incendie ), a calibrer
DDF = 3.0                        # fonte de la neige, mm par degre-jour ( 2 a 5 : OMM ), a calibrer
LAMBDA_SECHERESSE = math.exp(-1.0 / 180)   # memoire du deficit de pluie : ~6 mois ( SPI-6 )
QUANTILES_SECHERESSE = (0.80, 0.933, 0.977)  # classes de McKee et al. 1993 ( SPI <= -0,84 ; -1,5 ; -2 )
CLASSES_SECHERESSE = ("normale", "moderee", "severe", "extreme")
SEUIL_CHALEUR, K_CHALEUR = 35.0, 0.03       # rendement : -3 % par degre moyen au-dessus de 35 C ( Schlenker et Roberts 2009 : a calibrer )
EMA_J = 30.0
A_EMA = 1.0 / EMA_J
CYCLONE_CUMUL = np.cumsum((0.35, 0.25, 0.20, 0.13, 0.07))   # categories 1 a 5 ( a calibrer )
CYC_PLUIE, CYC_PLUIE_CAT, CYC_VENT = 60.0, 50.0, (0.0, 18.0, 24.0, 28.0, 32.0, 39.0)   # mm le premier jour ; m/s moyens
# pluie moyenne d un cyclone sur ses deux jours ( le second en donne la moitie ) : les normales des stations la contiennent
PLUIE_CYCLONE = 1.5 * (CYC_PLUIE + CYC_PLUIE_CAT * float(np.dot(np.arange(1, 6), np.diff(np.concatenate(([0.0], CYCLONE_CUMUL))))))
FFDI_SEUILS = (12.0, 25.0, 50.0, 75.0, 100.0)   # McArthur ( Noble et al. 1980 ) : classes australiennes d avant 2022
FFDI_CLASSES = ("faible", "eleve", "tres_eleve", "severe", "extreme", "catastrophique")
FFDI_ALERTE = 50.0

# ================================================================== les lois du sol et de l eau ( a calibrer )
KC = {"sec": 0.8, "irr": 1.0, "bv": 0.6}   # coefficients culturaux moyens ( FAO-56 ) : cultures seches, irriguees, maquis
P_FAO = 0.5                      # part de la reserve utile consommable sans stress ( FAO-56 tableau 22 )
EFFICIENCE = 0.75                # irrigation : part de l eau prelevee qui atteint les racines
KY = 1.1                         # reponse du rendement au deficit d evapotranspiration ( FAO-33, Doorenbos et Kassam )
Q_MAX, F_MAX = 1.2, 1.15
HA_PAR_PAYSAN = 5.0              # Grece : 6,6 ha de SAU par exploitation, ~1 UTA ( Eurostat 2016 ), a calibrer
DOTATION_M3 = 0.20               # eau brute par habitant et par jour, pertes du reseau comprises ( Grece : 150-250 l ), a calibrer
HAB_MIN = 20                     # un bassin dimensionne au moins pour 20 habitants
CAPTAGE = 0.30                   # part du ruissellement que les retenues interceptent
CAP_NAPPE, MIN_NAPPE, TAU_NAPPE = 2.0, 0.20, 400.0   # capacite ( annees de recharge ), plancher ( intrusion saline ), exutoire ( jours )
CAP_RETENUE, MIN_RETENUE, PROF_RETENUE = 0.8, 0.10, 8.0   # capacite ( annees de captage ), culot mort, profondeur moyenne ( m )
KC_EAU = 1.05                    # evaporation d un plan d eau sur ET0 ( FAO-56 )
ACTIVITE_NOMINALE = 0.6
EAU_PAR_UNITE = {"mine": 0.3, "carriere": 0.2, "fonderie": 2.0, "pharmacie": 1.0, "puits": 0.05, "raffinerie": 1.0,
                 "centrale": 0.2}   # m3 par unite produite ( l unite du moteur E1 n a pas de masse : a calibrer )
USAGE_SITE = {"mine": "industrie", "carriere": "industrie", "fonderie": "industrie", "pharmacie": "industrie",
              "puits": "energie", "raffinerie": "energie", "centrale": "energie"}
USAGES = ("domestique", "irrigation", "industrie", "energie")
PROPRIETAIRE_USAGE = {"domestique": "services_publics", "irrigation": "agriculture", "industrie": "industrie",
                      "energie": "energie"}
SEUILS_CRUE = (30.0, 60.0, 100.0)  # mm de ruissellement du bassin en un jour : crue moderee, grave, majeure ( a calibrer )
DEGAT_CRUE, DUREE_DEGAT_J = 0.25, 7   # rendement des villages inondes : -25 % par degre de gravite pendant 7 jours

# ================================================================== la decision
ACTIONS_EAU = ("aucune", "legere", "severe")
# Part de chaque usage coupee par palier ( plans speciaux de secheresse espagnols : pre-alerte, alerte, urgence -
# ordre de grandeur, a calibrer ). L eau potable est protegee ( directive 2000/60/CE, loi grecque 3199/2003 ).
COUPURES = np.array(((0.0, 0.0, 0.0, 0.0), (0.05, 0.20, 0.10, 0.05), (0.15, 0.50, 0.25, 0.10)))
JOURS_ENTRE_DECISIONS = 7
HORIZON_EAU = 21
KAPPA = 1.0                      # une journee de coupure totale annoncee pese autant qu une journee de penurie subie
SEUIL_PENURIE = 0.05             # un jour de penurie : plus de 5 % de la demande ( apres restriction ) non servie


# ================================================================== la pollution
class Polluant:
    """Un polluant : son milieu, l unite de sa concentration, la limite qui donne l indice 1, sa demi-vie dans le
    milieu ( math.inf : aucune degradation ), sa concentration de fond."""
    __slots__ = ("nom", "milieu", "unite", "limite", "demi_vie_j", "fond", "source")

    def __init__(self, nom, milieu, unite, limite, demi_vie_j, fond, source):
        if milieu not in ("air", "eau", "sol") or not limite > 0 or not demi_vie_j > 0 or fond < 0:
            raise ValueError(f"polluant {nom} hors bornes")
        self.nom, self.milieu, self.unite, self.limite = nom, milieu, unite, float(limite)
        self.demi_vie_j, self.fond, self.source = float(demi_vie_j), float(fond), source


POLLUANTS = (
    Polluant("pm25", "air", "ug/m3", 25.0, math.inf, 8.0, "valeur limite annuelle UE ( 2008/50/CE ) ; fond a calibrer"),
    Polluant("no2", "air", "ug/m3", 40.0, math.inf, 3.0, "valeur limite annuelle UE ( 2008/50/CE ) ; fond a calibrer"),
    Polluant("so2", "air", "ug/m3", 125.0, math.inf, 1.0, "valeur limite journaliere UE ( 2008/50/CE ) ; fond a calibrer"),
    Polluant("nitrates", "eau", "mg/l", 50.0, 1000.0, 5.0, "directive 98/83/CE ; denitrification des nappes a calibrer"),
    Polluant("hydrocarbures", "eau", "mg/l", 0.01, 30.0, 0.0, "ancienne limite francaise 10 ug/l ; biodegradation a calibrer"),
    Polluant("plomb", "eau", "mg/l", 0.01, math.inf, 0.0, "directive 98/83/CE : 10 ug/l"),
    Polluant("plomb_sol", "sol", "mg/kg", 300.0, math.inf, 20.0, "seuil a calibrer ( valeur d intervention neerlandaise 530 mg/kg )"),
    Polluant("hydrocarbures_sol", "sol", "mg/kg", 5000.0, 180.0, 0.0,
             "valeur d intervention neerlandaise ( huiles minerales ) ; biodegradation a calibrer"),
)
POLLUANT = {x.nom: x for x in POLLUANTS}
AIR = tuple(x.nom for x in POLLUANTS if x.milieu == "air")
EAU = tuple(x.nom for x in POLLUANTS if x.milieu == "eau")
SOL = tuple(x.nom for x in POLLUANTS if x.milieu == "sol")
HAUTEUR_MELANGE = 800.0          # m : la boite d air d un lieu ( a calibrer : 500 m l hiver, 1 500 m l ete )
PROF_SOL, DENSITE_SOL = 0.2, 1300.0   # m et kg/m3 : la couche de sol qui recoit les retombees
# Rejets de fond des sites du moteur E1, en kg par unite produite, tant que leur domaine n est pas installe ( a calibrer :
# l unite du moteur n a pas de masse ; facteurs d emission a reprendre du guide EMEP/AEE par les domaines 10 et 11 ).
EMISSIONS_E1 = {"centrale": (("so2", 0.02), ("no2", 0.03), ("pm25", 0.002)),
                "raffinerie": (("so2", 0.01), ("hydrocarbures", 0.0005)),
                "mine": (("pm25", 0.005), ("plomb", 0.00005), ("plomb_sol", 0.0005)),
                "carriere": (("pm25", 0.01),),
                "fonderie": (("pm25", 0.05), ("plomb_sol", 0.005)),
                "puits": (("hydrocarbures_sol", 0.002),)}


# ================================================================== la table du climat et le generateur
class TableClimat:
    """Les normales journalieres de n stations ( une par ile, ou n repliques d une meme ile ), en tableaux ( n, 365 )."""
    __slots__ = ("n", "latitude", "tmoy", "dtr", "pi", "r", "r_ord", "hr", "vent", "sig", "ra", "cyc", "p_an", "r90")

    def __init__(self, profils):
        self.n = len(profils)
        self.latitude = np.array([pr.latitude for pr in profils])
        col = lambda f: np.array([f(pr) for pr in profils])
        self.tmoy = col(lambda pr: quotidien((pr.tmax + pr.tmin) / 2))
        self.dtr = col(lambda pr: quotidien(pr.tmax - pr.tmin))
        self.pi = col(lambda pr: np.clip(quotidien(pr.jours_pluie / MOIS_J), 1e-4, 0.9))
        self.r = col(lambda pr: quotidien(pr.pluie / MOIS_J))
        self.hr = col(lambda pr: quotidien(pr.hr))
        self.vent = col(lambda pr: quotidien(pr.vent))
        self.sig = col(lambda pr: quotidien(pr.sigma_t))
        self.ra = col(lambda pr: rayonnement_extraterrestre(pr.latitude))
        self.cyc = col(lambda pr: (pr.cyclones / MOIS_J)[MOIS_DU_JOUR])
        self.r_ord = np.maximum(0.3 * self.r, self.r - self.cyc * PLUIE_CYCLONE)   # la pluie hors cyclones
        self.p_an = self.r.sum(axis=1)
        k = np.concatenate((self.r, self.r[:, :90]), axis=1).cumsum(axis=1)
        self.r90 = k[:, 89:89 + JOURS_AN] - np.concatenate((np.zeros((self.n, 1)), k[:, :JOURS_AN - 1]), axis=1)


class EtatMeteo:
    """La memoire du temps, par station : ce qui fait qu un jour ressemble a la veille."""
    __slots__ = ("humide", "z", "a", "vx", "vy", "neige", "kbdi", "jsp", "dpluie", "deficit", "chaleur", "cyc_reste",
                 "cyc_cat", "cyc_pluie2")

    def __init__(self, n):
        self.humide = np.zeros(n, bool)
        self.z = np.zeros(n); self.a = np.zeros(n)
        self.vx = np.full(n, math.sqrt(0.5)); self.vy = np.full(n, math.sqrt(0.5))
        self.neige = np.zeros(n); self.kbdi = np.zeros(n)
        self.jsp = np.zeros(n); self.dpluie = np.zeros(n)
        self.deficit = np.zeros(n); self.chaleur = np.zeros(n)
        self.cyc_reste = np.zeros(n, np.int64); self.cyc_cat = np.zeros(n, np.int64); self.cyc_pluie2 = np.zeros(n)


class MeteoDuJour:
    """Le temps d un jour, un tableau par grandeur ( une valeur par station ).
      pluie       mm tombes ( pluie et neige, en eau ) ; liquide, neige_tombee, fonte : mm ; eau : ce qui arrive au sol
      tmin, tmax, tmoy  degres C ; vent : m/s moyens ( vent_x, vent_y : composantes ) ; hr : humidite de l apres-midi, %
      et0         evapotranspiration de reference, mm ( Hargreaves et Samani 1985, FAO-56 equation 52 )
      ffdi        indice de danger d incendie de McArthur ; kbdi : secheresse du combustible, mm ( Keetch et Byram )
      neige_sol   manteau neigeux, mm d eau ; cyclone : categorie en cours ( 0 : aucun ) ; cyclone_nouveau : il arrive"""
    __slots__ = ("pluie", "liquide", "neige_tombee", "fonte", "eau", "tmin", "tmax", "tmoy", "vent", "vent_x", "vent_y",
                 "hr", "et0", "ffdi", "kbdi", "neige_sol", "cyclone", "cyclone_nouveau")

    def __init__(self, **v):
        for k in self.__slots__: setattr(self, k, v[k])


def _tirages(rng, n):
    """Les tirages d un jour. `rng` : un generateur pour toutes les stations, ou une liste de generateurs qui tirent
    chacun pour un bloc egal de stations ( les normales d une ile ne dependent pas des autres iles du monde )."""
    if isinstance(rng, (list, tuple)):
        t = [_tirages(r, n // len(rng)) for r in rng]
        return np.concatenate([a for a, _, _ in t], 1), np.concatenate([b for _, b, _ in t], 1), np.concatenate([c for _, _, c in t])
    return rng.random((5, n)), rng.standard_normal((4, n)), rng.exponential(1.0, n)


def tirer_meteo(tab, e, j, rng, pluie_mult=None, chaleur=None):
    """Un jour de temps pour toutes les stations de `tab`, le jour de l an `j` ( 0 a 364 ). Generateur de Richardson
    ( 1981 ) etendu : chaine de Markov d ordre 1 pour la pluie, hauteurs en melange d exponentielles, un regime lent
    qui module la probabilite de pluie ( les annees seches existent ) et la chaleur ( une periode seche est chaude ),
    anomalies de temperature autoregressives ( vagues de chaleur ), vent de Rayleigh persistant, neige et fonte,
    KBDI, indice d incendie de McArthur, deficit de pluie. Tous les tirages sont faits chaque jour dans le meme ordre :
    un forcage ou un cyclone ne decale pas le hasard des jours suivants."""
    n = tab.n
    u, g, x = _tirages(rng, n)
    # la pluie
    e.z = PHI_REGIME * e.z + math.sqrt(1 - PHI_REGIME ** 2) * g[0]
    pi0 = tab.pi[:, j]
    pi = np.minimum(PI_MAX, pi0 * np.exp(BETA_REGIME * e.z - 0.5 * BETA_REGIME ** 2))
    humide = u[0] < pi * (1 - R_OCC) + R_OCC * e.humide
    mu = np.maximum(0.1, tab.r_ord[:, j] / pi0 - SEUIL_PLUIE)
    pluie = np.where(humide, SEUIL_PLUIE + x * mu * np.where(u[1] < ALPHA_MIXTE, B1_MIXTE, B2_MIXTE), 0.0)
    # les cyclones : deux jours de pluie et de vent
    reste = e.cyc_reste > 0
    nouveau = (~reste) & (u[2] < tab.cyc[:, j])
    cat = np.where(nouveau, 1 + np.minimum(4, np.searchsorted(CYCLONE_CUMUL, u[3])), 0)
    pl = (CYC_PLUIE + CYC_PLUIE_CAT * cat) * (0.6 + 0.8 * u[4])
    cat_jour = np.where(nouveau, cat, np.where(reste, e.cyc_cat, 0))
    pluie = np.maximum(pluie, np.where(nouveau, pl, np.where(reste, e.cyc_pluie2, 0.0)))
    humide = humide | (cat_jour > 0)
    e.cyc_pluie2 = np.where(nouveau, 0.5 * pl, 0.0)
    e.cyc_cat = np.where(nouveau, cat, e.cyc_cat)
    e.cyc_reste = np.where(nouveau, 1, np.maximum(0, e.cyc_reste - 1))
    e.humide = humide
    if pluie_mult is not None: pluie = pluie * pluie_mult
    # la temperature
    e.a = PHI_T * e.a + math.sqrt(1 - PHI_T ** 2) * g[1]
    anom = math.sqrt(1 - PART_LENTE) * e.a - math.sqrt(PART_LENTE) * e.z
    pic = np.minimum(pi0, 0.9)
    tmoy = tab.tmoy[:, j] + tab.sig[:, j] * anom + np.where(humide, -DT_HUMIDE * (1 - pic), DT_HUMIDE * pic)
    if chaleur is not None: tmoy = tmoy + chaleur
    dtr = tab.dtr[:, j] * np.where(humide, DTR_HUMIDE, 1 + (1 - DTR_HUMIDE) * pic / (1 - pic))
    tmax, tmin = tmoy + dtr / 2, tmoy - dtr / 2
    # le vent
    e.vx = PHI_VENT * e.vx + math.sqrt(1 - PHI_VENT ** 2) * g[2]
    e.vy = PHI_VENT * e.vy + math.sqrt(1 - PHI_VENT ** 2) * g[3]
    s = tab.vent[:, j] / RACINE_PI_2
    vent = np.maximum(s * np.hypot(e.vx, e.vy), np.take(CYC_VENT, cat_jour))
    # la neige
    tombee = np.where(tmoy < 0.0, pluie, 0.0)
    liquide = pluie - tombee
    e.neige = e.neige + tombee
    fonte = np.minimum(e.neige, DDF * np.maximum(0.0, tmoy))
    e.neige = e.neige - fonte
    eau = liquide + fonte
    # evapotranspiration, humidite
    et0 = np.maximum(0.0, 0.0023 * (tmoy + 17.8) * np.sqrt(np.maximum(dtr, 0.0)) * tab.ra[:, j])
    hr = np.clip(tab.hr[:, j] + HR_APREM + HR_PAR_C * (tmoy - tab.tmoy[:, j]) + np.where(humide, HR_PLUIE, 0.0), 5.0, 100.0)
    # KBDI ( forme metrique, Crane 1982 ) : la pluie d un episode ne compte qu au-dela de 5,08 mm
    net = np.where(e.jsp == 0, liquide, np.maximum(0.0, liquide - 5.08))
    kb = np.maximum(0.0, e.kbdi - net)
    dq = (203.2 - kb) * (0.968 * np.exp(0.0875 * tmax + 1.5552) - 8.30) / (1 + 10.88 * np.exp(-0.001736 * tab.p_an)) * 1e-3
    e.kbdi = np.minimum(203.2, kb + np.where(e.neige > 0, 0.0, np.maximum(0.0, dq)))
    plu = liquide >= SEUIL_PLUIE
    e.jsp = np.where(plu, 0.0, e.jsp + 1); e.dpluie = np.where(plu, liquide, e.dpluie)
    n1 = (e.jsp + 1.0) ** 1.5
    df = np.clip(0.191 * (e.kbdi + 104.0) * n1 / (3.52 * n1 + e.dpluie - 1.0), 1e-3, 10.0)   # Noble et al. 1980
    ffdi = 2.0 * np.exp(-0.45 + 0.987 * np.log(df) - 0.0345 * hr + 0.0338 * tmax + 0.0234 * 3.6 * vent)
    ffdi = np.where(e.neige > 0, 0.0, ffdi)
    # memoires : deficit de pluie ( secheresse ), chaleur ( rendement )
    e.deficit = LAMBDA_SECHERESSE * e.deficit + (tab.r[:, j] - pluie)
    e.chaleur = (1 - A_EMA) * e.chaleur + A_EMA * np.maximum(0.0, tmax - SEUIL_CHALEUR)
    return MeteoDuJour(pluie=pluie, liquide=liquide, neige_tombee=tombee, fonte=fonte, eau=eau, tmin=tmin, tmax=tmax,
                       tmoy=tmoy, vent=vent, vent_x=s * e.vx, vent_y=s * e.vy, hr=hr, et0=et0, ffdi=ffdi,
                       kbdi=e.kbdi.copy(), neige_sol=e.neige.copy(), cyclone=cat_jour, cyclone_nouveau=nouveau)


def simuler(profils, jours, rng, j0=0):
    """Fait vivre le generateur `jours` jours pour ces profils, depuis le jour de l an j0. Rend des tableaux
    ( stations, jours ) : pluie, tmoy, tmax, neige_tombee, fonte, neige_sol. Pour les portes et les etudes."""
    tab = TableClimat(profils); e = EtatMeteo(tab.n)
    out = {k: np.zeros((tab.n, jours)) for k in ("pluie", "tmoy", "tmax", "neige_tombee", "fonte", "neige_sol")}
    for d in range(jours):
        m = tirer_meteo(tab, e, (j0 + d) % JOURS_AN, rng)
        for k in out: out[k][:, d] = getattr(m, k)
    return out


# ================================================================== le sol et la ressource
def pas_sol(W, ru, cn2, kc, eau, et0):
    """Un jour d un reservoir de sol ( mm ). Ruissellement par numero de courbe SCS continu ( le CN suit l humidite
    entre les conditions seches et humides, Chow et al. 1988 ), infiltration, drainage au-dela de la reserve utile,
    evapotranspiration reelle ( FAO-56 : stress lineaire sous ( 1 - p ) RU ). Rend ( W, ruissellement, drainage, ETR,
    ETM ). Bilan exact : eau = ruissellement + drainage + ETR + ( W - W_avant )."""
    cn1 = cn2 / (2.281 - 0.01281 * cn2); cn3 = cn2 / (0.427 + 0.00573 * cn2)
    cn = cn1 + (cn3 - cn1) * np.clip(W / ru, 0.0, 1.0)
    s = 25400.0 / cn - 254.0
    q = np.where(eau > 0.2 * s, (eau - 0.2 * s) ** 2 / (eau + 0.8 * s), 0.0)
    W = W + (eau - q)
    dr = np.maximum(0.0, W - ru); W = W - dr
    etm = kc * et0
    eta = np.minimum(W, np.clip(W / ((1 - P_FAO) * ru), 0.0, 1.0) * etm)
    return W - eta, q, dr, eta, etm


def besoin_irrigation(W, ru):
    """Le pilotage de l irrigation ( FAO-56 ) : quand la reserve est consommee au-dela de p, on la remplit. mm nets."""
    return np.where(W < (1 - P_FAO) * ru, ru - W, 0.0)


def pas_ressource(n, r, cap_n, cap_r, surf_max, in_n, in_r, et0):
    """Le jour naturel des reserves ( m3 ) : entrees, debordements a la mer, evaporation de la retenue ( surface en
    S^(2/3) de son volume ), exutoire de la nappe ( reservoir lineaire ). Chaque stock n est modifie QUE par la
    soustraction d un flux compte : le bilan ferme. Rend ( n, r, evaporation, exutoire, debordement )."""
    n = n + in_n; r = r + in_r
    dn = np.maximum(0.0, n - cap_n); n = n - dn
    dr = np.maximum(0.0, r - cap_r); r = r - dr
    frac = np.clip(r / np.maximum(cap_r, 1e-12), 0.0, 1.0)
    ev = np.minimum(r, KC_EAU * et0 / 1000.0 * surf_max * frac ** (2.0 / 3.0)); r = r - ev
    ex = n / TAU_NAPPE; n = n - ex
    return n, r, ev, ex, dn + dr


def retirer(n, r, min_n, min_r, voulu):
    """Prelever `voulu` m3 : la retenue d abord ( jusqu a son culot ), la nappe ensuite ( jusqu a son plancher ).
    Rend ( n, r, livre )."""
    dr = np.maximum(0.0, r - min_r); dn = np.maximum(0.0, n - min_n)
    livre = np.minimum(voulu, dr + dn)
    x = np.minimum(livre, dr)
    return n - (livre - x), r - x, livre


# ================================================================== les normales, mesurees sur le generateur
GENRES = ("sec", "irr", "bv")
NORMALES_REPLIQUES, NORMALES_ANNEES = 16, 3     # 16 x 2 annees mesurees apres une annee de mise en route


class NormalesPays:
    """Ce que le climat de chaque ile donne en moyenne chaque jour de l an, par type de sol, mesure en faisant vivre le
    generateur et les reservoirs de sol. Sert : l etat de depart ( le monde nait dans un etat normal pour sa date ),
    la reference du rendement ( une annee normale donne 1 ), les seuils de secheresse, le dimensionnement de l eau.
      w_*        ( iles, sols, 365 ) reserve du sol, mm ; eta_*, etm_* : moyennes glissantes de 30 jours, mm/j
      irr_an     ( iles, sols ) irrigation nette par an, mm ; drain_an, ruis_an : drainage et ruissellement du maquis, mm/an
      kbdi, neige ( iles, 365 ) ; seuils ( iles, 3 ) : deficit de pluie / pluie annuelle aux quantiles de McKee
      rempl_n, rempl_r ( iles, 365 ) : remplissage normal de la nappe et de la retenue"""
    __slots__ = ("w_sec", "w_irr", "w_bv", "eta_sec", "etm_sec", "eta_irr", "etm_irr", "irr_an", "drain_an", "ruis_an",
                 "kbdi", "neige", "seuils", "rempl_n", "rempl_r")

    def __init__(self, n_iles):
        S = len(SOLS)
        for k in ("w_sec", "w_irr", "w_bv", "eta_sec", "etm_sec", "eta_irr", "etm_irr"):
            setattr(self, k, np.zeros((n_iles, S, JOURS_AN)))
        for k in ("irr_an", "drain_an", "ruis_an"): setattr(self, k, np.zeros((n_iles, S)))
        for k in ("kbdi", "neige", "rempl_n", "rempl_r"): setattr(self, k, np.zeros((n_iles, JOURS_AN)))
        self.seuils = np.zeros((n_iles, 3))


def mesurer_normales(profils, rngs, N, repliques=NORMALES_REPLIQUES, annees=NORMALES_ANNEES):
    """Remplit N ( phase climat et sols ) pour toutes les iles a la fois : `repliques` stations par ile, chaque ile avec
    son propre generateur. Rend les series journalieres dont le dimensionnement de l eau a besoin : drainage et
    ruissellement du maquis, irrigation nette ( stations, sols, jours mesures ), ET0 ( stations, jours )."""
    n, R, S = len(profils), repliques, len(SOLS)
    tab = TableClimat([pr for pr in profils for _ in range(R)]); e = EtatMeteo(n * R)
    ru = np.tile(SOL_RU, (n * R, 1)); cn = np.tile(SOL_CN, (n * R, 1))
    W = {g: 0.5 * ru for g in GENRES}
    ema = {g: [np.zeros((n * R, S)), np.zeros((n * R, S))] for g in ("sec", "irr")}
    Dm = (annees - 1) * JOURS_AN
    ser = {k: np.zeros((n * R, S, Dm)) for k in ("dr", "q", "irr")}
    et0s = np.zeros((n * R, Dm)); defi = np.zeros((n * R, Dm))
    par_ile = lambda v: v.reshape(n, R, *v.shape[1:]).sum(1)
    for d in range(annees * JOURS_AN):
        j = d % JOURS_AN
        m = tirer_meteo(tab, e, j, rngs)
        eau = m.eau[:, None]; et0 = m.et0[:, None]
        k = d - JOURS_AN
        for g in GENRES:
            W[g], q, dr, eta, etm = pas_sol(W[g], ru, cn, KC[g], eau, et0)
            if g == "irr":
                b = besoin_irrigation(W[g], ru); W[g] = W[g] + b
            if g != "bv":
                ema[g][0] += A_EMA * (eta - ema[g][0]); ema[g][1] += A_EMA * (etm - ema[g][1])
            if k >= 0:
                getattr(N, "w_" + g)[:, :, j] += par_ile(W[g])
                if g != "bv":
                    getattr(N, "eta_" + g)[:, :, j] += par_ile(ema[g][0]); getattr(N, "etm_" + g)[:, :, j] += par_ile(ema[g][1])
                if g == "bv": ser["dr"][:, :, k] = dr; ser["q"][:, :, k] = q
                if g == "irr": ser["irr"][:, :, k] = b
        if k >= 0:
            N.kbdi[:, j] += par_ile(e.kbdi); N.neige[:, j] += par_ile(e.neige)
            et0s[:, k] = m.et0; defi[:, k] = e.deficit / tab.p_an
    n_obs = R * (annees - 1)
    for k in ("w_sec", "w_irr", "w_bv", "eta_sec", "etm_sec", "eta_irr", "etm_irr", "kbdi", "neige"): getattr(N, k)[:] /= n_obs
    N.irr_an[:] = par_ile(ser["irr"].sum(2)) / n_obs
    N.drain_an[:] = par_ile(ser["dr"].sum(2)) / n_obs
    N.ruis_an[:] = par_ile(ser["q"].sum(2)) / n_obs
    for i in range(n): N.seuils[i] = np.quantile(defi[i * R:(i + 1) * R], QUANTILES_SECHERESSE)
    return ser, et0s


def remplissage_normal(N, ser, et0s, poids, parts, wei, repliques=NORMALES_REPLIQUES, passes=3):
    """Le remplissage normal des reserves de chaque ile, jour par jour : une ressource ramenee a 1 million de m3
    renouvelables par an, dimensionnee comme les bassins, alimentee par les series du maquis ( sols melanges selon
    `poids` ( iles, sols ) ), videe par une demande de la composition de l ile ( `parts` ( iles, 3 ) : domestique,
    irrigation, industrie ) a hauteur de son WEI, SANS restriction. Trois passages des series pour oublier le depart."""
    n, R = len(wei), repliques
    w = np.repeat(np.asarray(poids, float), R, axis=0)[:, :, None]
    dr = (ser["dr"] * w).sum(1); q = (ser["q"] * w).sum(1); irr = (ser["irr"] * w).sum(1)
    Dm = dr.shape[1]; ans = Dm / JOURS_AN
    moy = lambda v: np.repeat(v.sum(1).reshape(n, R).mean(1) / ans, R)
    d_an, q_an, irr_an = moy(dr), moy(q), moy(irr)
    A = 1e6 / np.maximum(1e-9, (d_an + CAPTAGE * q_an) / 1000.0)
    cap_n = CAP_NAPPE * A * d_an / 1000.0; cap_r = CAP_RETENUE * A * CAPTAGE * q_an / 1000.0
    min_n, min_r = MIN_NAPPE * cap_n, MIN_RETENUE * cap_r
    parts = np.repeat(np.asarray(parts, float), R, axis=0)
    p_irr = np.where(irr_an > 1e-9, parts[:, 1], 0.0)
    p_fixe = parts[:, 0] + parts[:, 2] + (parts[:, 1] - p_irr)
    ww = np.repeat(np.asarray(wei, float), R)
    irr_rel = irr / np.maximum(irr_an, 1e-9)[:, None]
    nn = 0.6 * cap_n; rr = 0.5 * cap_r
    acc_n = np.zeros((n * R, JOURS_AN)); acc_r = np.zeros((n * R, JOURS_AN))
    for passe in range(passes):
        for k in range(Dm):
            nn, rr, _, _, _ = pas_ressource(nn, rr, cap_n, cap_r, cap_r / PROF_RETENUE, A * dr[:, k] / 1000.0,
                                            A * CAPTAGE * q[:, k] / 1000.0, et0s[:, k])
            nn, rr, _ = retirer(nn, rr, min_n, min_r, ww * 1e6 * (p_fixe / JOURS_AN + p_irr * irr_rel[:, k]))
            if passe == passes - 1:
                acc_n[:, k % JOURS_AN] += np.divide(nn, cap_n, out=np.zeros_like(nn), where=cap_n > 0)
                acc_r[:, k % JOURS_AN] += np.divide(rr, cap_r, out=np.zeros_like(rr), where=cap_r > 0)
    N.rempl_n[:] = acc_n.reshape(n, R, JOURS_AN).sum(1) / (R * ans)
    N.rempl_r[:] = acc_r.reshape(n, R, JOURS_AN).sum(1) / (R * ans)


# ================================================================== l etat du territoire
class Bassins:
    """Les unites de gestion de l eau brute, en tableaux indexes par bassin. Un bassin = une ville ou une capitale et
    les lieux de son ile dont elle est la plus proche : sur une ile egeenne, pas de reseau d ile, des forages et des
    retenues par groupe de villages ( la regie municipale, DEYA ). Volumes en m3.
      surface_m2    bassin d alimentation exploite ( dimensionne par le WEI ) ; sol : son type
      cap_n, min_n  capacite et plancher de la nappe ; cap_r, min_r, surf_max : retenue
      c_*           cumuls du bilan depuis l installation ; par_usage : m3 livres par usage
      c_dem, c_cut, c_liv    demande, part coupee par la restriction, eau livree : du jour ( la note )
      h_dem, h_manque, h_dispo  les 7 derniers jours ( les traits )"""
    __slots__ = ("nom", "ile", "sol", "surface_m2", "cap_n", "min_n", "cap_r", "min_r", "surf_max", "nappe", "retenue",
                 "stock0", "c_in_n", "c_in_r", "c_evap", "c_exut", "c_debord", "c_prel", "c_forc", "par_usage", "pop",
                 "restriction", "c_dem", "c_cut", "c_liv", "h_dem", "h_manque", "h_dispo", "ruis_jour", "jours_penurie",
                 "w_bv", "s_eau", "s_q", "s_dr", "s_eta", "s_w0", "demande_an")

    def __init__(self, noms, iles, sols):
        nb = len(noms)
        self.nom, self.ile, self.sol = list(noms), np.array(iles, np.int64), np.array(sols, np.int64)
        for k in ("surface_m2", "cap_n", "min_n", "cap_r", "min_r", "surf_max", "nappe", "retenue", "stock0", "c_in_n",
                  "c_in_r", "c_evap", "c_exut", "c_debord", "c_prel", "c_forc", "pop", "c_dem", "c_cut", "c_liv",
                  "ruis_jour", "w_bv", "s_eau", "s_q", "s_dr", "s_eta", "s_w0", "demande_an"):
            setattr(self, k, np.zeros(nb))
        self.par_usage = np.zeros((nb, len(USAGES)))
        self.restriction = np.zeros(nb, np.int64)
        self.jours_penurie = np.zeros(nb, np.int64)
        self.h_dem = np.zeros((nb, 7)); self.h_manque = np.zeros((nb, 7)); self.h_dispo = np.zeros((nb, 7))

    def dispo(self):
        return np.maximum(0.0, self.nappe - self.min_n) + np.maximum(0.0, self.retenue - self.min_r)

    def exploitable(self):
        return (self.cap_n - self.min_n) + (self.cap_r - self.min_r)


class Parcelles:
    """Une parcelle agricole par village, en tableaux. Deux reservoirs de sol : la part seche et la part irriguee
    ( mm, sur leur propre surface ). eta_*, etm_* : moyennes glissantes de 30 jours de l ETR et de l ETM ; facteur : le
    rendement climatique du jour ; inond_* : degats d une crue en cours ; c_* : cumuls des bilans ( mm )."""
    __slots__ = ("lieu_id", "bassin", "ile", "sol", "surface_ha", "irrigue", "ru", "cn", "w_sec", "w_irr", "eta_sec",
                 "etm_sec", "eta_irr", "etm_irr", "facteur", "inond_facteur", "inond_fin", "c_eau", "c_q_sec", "c_dr_sec",
                 "c_eta_sec", "c_q_irr", "c_dr_irr", "c_eta_irr", "c_irr_brut", "c_irr_pertes", "w0_sec", "w0_irr")

    def __init__(self, lieux, bassins, iles, sols, surfaces, irrigue):
        n = len(lieux)
        self.lieu_id = list(lieux)
        self.bassin, self.ile, self.sol = np.array(bassins, np.int64), np.array(iles, np.int64), np.array(sols, np.int64)
        self.surface_ha, self.irrigue = np.array(surfaces, float), np.array(irrigue, float)
        if (self.surface_ha <= 0).any() or ((self.irrigue < 0) | (self.irrigue > 1)).any(): raise ValueError("parcelles hors bornes")
        self.ru, self.cn = SOL_RU[self.sol], SOL_CN[self.sol]
        for k in ("w_sec", "w_irr", "eta_sec", "etm_sec", "eta_irr", "etm_irr", "c_eau", "c_q_sec", "c_dr_sec",
                  "c_eta_sec", "c_q_irr", "c_dr_irr", "c_eta_irr", "c_irr_brut", "c_irr_pertes", "w0_sec", "w0_irr"):
            setattr(self, k, np.zeros(n))
        self.facteur = np.ones(n); self.inond_facteur = np.ones(n); self.inond_fin = np.full(n, -1, np.int64)


class Pollution:
    """Les masses de polluants ( kg ) : dans l air d un lieu, le jour meme ( une boite ventilee : tout ce qui est emis
    part avec le vent dans la journee ) ; dans l eau brute d un bassin ( melangee a la nappe et a la retenue, degradee,
    emportee par l eau qui sort ) ; dans le sol d un lieu ( degrade, jamais emporte : le plomb reste ). Cumuls pour le
    bilan au kg ; concentrations de la veille pour l air."""
    __slots__ = ("air_jour", "air_conc", "eau", "sol", "c_rejete", "c_degrade", "c_evacue", "c_ventile", "m0")

    def __init__(self, n_lieux, n_bassins):
        self.air_jour = np.zeros((n_lieux, len(AIR))); self.air_conc = np.zeros((n_lieux, len(AIR)))
        self.eau = np.zeros((n_bassins, len(EAU))); self.sol = np.zeros((n_lieux, len(SOL)))
        self.c_rejete = {x.nom: 0.0 for x in POLLUANTS}; self.c_degrade = dict.fromkeys(self.c_rejete, 0.0)
        self.c_evacue = dict.fromkeys(self.c_rejete, 0.0); self.c_ventile = dict.fromkeys(self.c_rejete, 0.0)
        self.m0 = dict.fromkeys(self.c_rejete, 0.0)


class Catastrophe:
    """Une catastrophe en cours. gravite : classe de secheresse ( 2-3 ), degre de crue ( 1-3 ), MMI arrondi, categorie
    de cyclone, classe d incendie ( 3-5 ). valeur : indice, mm, magnitude. intensites : { lieu : MMI } ( seisme )."""
    __slots__ = ("type", "ile", "lieu", "gravite", "debut_j", "fin_j", "valeur", "intensites")

    def __init__(self, type_, ile, lieu, gravite, debut_j, fin_j, valeur, intensites=None):
        self.type, self.ile, self.lieu, self.gravite = type_, ile, lieu, int(gravite)
        self.debut_j, self.fin_j, self.valeur, self.intensites = debut_j, fin_j, float(valeur), intensites

    def __repr__(self): return f"{self.type}({self.ile}, {self.lieu}, gravite {self.gravite}, j{self.debut_j}-{self.fin_j})"


class Territoire:
    __slots__ = ("iles", "profils", "tab", "etat", "meteo", "normales", "forcages", "sequences", "centres", "lieux",
                 "index_lieu", "lieu_ile", "lieu_bassin", "lieu_pos", "lieu_largeur", "lieu_surface", "capitale_ile",
                 "bassins", "parcelles", "pollution", "catastrophes", "classe_secheresse", "en_secheresse",
                 "usages_repris", "pont_e1", "decideur", "jour_fait", "pluie30", "sites", "c_neige", "neige0",
                 "n_seismes", "n_crues", "n_alertes", "doy")


# ================================================================== la decision : gerer l eau d un bassin
class ContexteEau:
    """Ce que voit le gestionnaire d un bassin : ses jauges, ses volumes distribues, le pluviometre, le bulletin de
    secheresse et la climatologie publiee. Rien d autre : pas la pluie de demain, pas les reserves des voisins."""
    __slots__ = ("traits", "bassin")

    def __init__(self, traits, bassin): self.traits, self.bassin = traits, bassin


def _observer_eau(ctx): return ctx.traits


def _regle_eau(x, ctx):
    """Une regie raisonne en mois d eau devant elle, pas en taux de remplissage : une nappe cotiere est normalement
    basse a l automne ( ~10 % de l exploitable a Altis en annee normale, NormalesPays.rempl_n ). Severe sous un mois
    d autonomie ou en penurie ; legere sous trois mois, en secheresse severe, ou sous 5 % de l exploitable."""
    remplissage, autonomie, _, _, _, _, penurie, secheresse = x
    if autonomie < 30 / 120 or penurie > 0.10: return 2
    if autonomie < 90 / 120 or secheresse >= 2 / 3 or remplissage < 0.05: return 1
    return 0


def _temoin_eau(x, ctx, rng): return 0


POINT_EAU = D.PointDeDecision(
    "gerer_eau", "territoire",
    traits=(("remplissage", "jauge de la retenue et piezometres du bassin : volume exploitable sur capacite exploitable"),
            ("autonomie", "volume exploitable sur la demande moyenne des 7 derniers jours ( ses compteurs ), sur 120 jours"),
            ("pluie_30j", "pluviometre de l ile : pluie des 30 derniers jours sur deux fois la normale publiee"),
            ("pluie_a_venir", "climatologie publiee : pluie normale des 90 prochains jours sur son maximum de l annee"),
            ("tendance", "variation du volume exploitable sur 7 jours, 0,5 = stable, sur 20 % de la capacite"),
            ("restriction", "le palier en vigueur dans le bassin, sur 2"),
            ("penurie_7j", "ses compteurs : demande non servie des 7 derniers jours sur la demande"),
            ("secheresse", "bulletin de secheresse de l ile : classe de McKee, sur 3")),
    actions=ACTIONS_EAU,
    observer=_observer_eau, regle=_regle_eau, temoin=_temoin_eau,
    note=("sur les 21 jours qui suivent, la moyenne de : 1 si CE bassin a servi au moins 95 % de sa demande ce jour-la, "
          "moins la part de sa demande coupee par la restriction"),
    horizon_j=HORIZON_EAU)


# ================================================================== outils
def _doy(p):
    return min(JOURS_AN - 1, p.socle.calendrier.date(p.pas).timetuple().tm_yday - 1)


def _id(lieu): return lieu if isinstance(lieu, str) else lieu.id


def _ile_index(T, ou):
    """Un nom d ile, un Lieu ou l identifiant d un lieu -> rang de l ile."""
    if isinstance(ou, str) and ou in T.iles: return T.iles.index(ou)
    k = T.index_lieu.get(_id(ou))
    if k is None: raise KeyError(f"territoire : lieu ou ile inconnu {ou!r}")
    return int(T.lieu_ile[k])


def bassin_de(p, lieu):
    T = p.domaine("territoire")
    k = T.index_lieu.get(_id(lieu))
    if k is None: raise KeyError(f"territoire : lieu inconnu {lieu!r}")
    return int(T.lieu_bassin[k])


def _stocks_pollution(T, milieu):
    P = T.pollution
    tab, noms = {"eau": (P.eau, EAU), "sol": (P.sol, SOL), "air": (P.air_jour, AIR)}[milieu]
    return tab, noms


# ================================================================== la journee du territoire ( 00 h 00 )
def _minuit(p):
    T = p.domaine("territoire")
    j = p.jour
    if T.jour_fait == j: return
    T.jour_fait = j
    T.doy = doy = _doy(p)
    if j % 7 == 0: _recenser(p, T)
    if j % JOURS_ENTRE_DECISIONS == 0: _decider(p, T, doy)
    _climat_du_jour(p, T, doy)
    _sols_et_eau(p, T, doy)
    _facteurs_fermes(p, T, doy)
    _catastrophes(p, T, doy)
    _degradation(T)


def _forcage(T, j):
    n = len(T.iles)
    mult, chal, actif = np.ones(n), np.zeros(n), False
    for f in T.forcages:
        i, debut, jours, pm, dc = f
        if debut <= j < debut + jours:
            mult[i] *= pm; chal[i] += dc; actif = True
    T.forcages = [f for f in T.forcages if j < f[1] + f[2]]
    return (mult, chal) if actif else (None, None)


def _climat_du_jour(p, T, doy):
    mult, chal = _forcage(T, p.jour)
    m = tirer_meteo(T.tab, T.etat, doy, p.du_jour("territoire_meteo"), mult, chal)
    T.meteo = m
    T.c_neige[0] += m.neige_tombee; T.c_neige[1] += m.fonte
    T.pluie30 = np.roll(T.pluie30, -1, axis=1); T.pluie30[:, -1] = m.pluie
    for i in np.nonzero(m.cyclone_nouveau)[0].tolist():
        cat = int(m.cyclone[i]); lieu = T.capitale_ile[i]
        T.catastrophes.append(Catastrophe("cyclone", T.iles[i], lieu, cat, p.jour, p.jour + 1, float(m.pluie[i])))
        p.noter("cyclone", ile=T.iles[i], lieu=lieu, gravite=cat, pluie_mm=round(float(m.pluie[i]), 1),
                vent_ms=round(float(m.vent[i]), 1))


def _sols_et_eau(p, T, doy):
    m, P, B = T.meteo, T.parcelles, T.bassins
    # les parcelles : sec et irrigue
    eau, et0 = m.eau[P.ile], m.et0[P.ile]
    P.c_eau += eau
    P.w_sec, q, dr, eta, etm = pas_sol(P.w_sec, P.ru, P.cn, KC["sec"], eau, et0)
    P.c_q_sec += q; P.c_dr_sec += dr; P.c_eta_sec += eta
    P.eta_sec += A_EMA * (eta - P.eta_sec); P.etm_sec += A_EMA * (etm - P.etm_sec)
    P.w_irr, q, dr, eta, etm = pas_sol(P.w_irr, P.ru, P.cn, KC["irr"], eau, et0)
    P.c_q_irr += q; P.c_dr_irr += dr; P.c_eta_irr += eta
    P.eta_irr += A_EMA * (eta - P.eta_irr); P.etm_irr += A_EMA * (etm - P.etm_irr)
    # le maquis de chaque bassin, puis ses reserves
    eau_b, et0_b = m.eau[B.ile], m.et0[B.ile]
    ru_b, cn_b = SOL_RU[B.sol], SOL_CN[B.sol]
    B.s_eau += eau_b
    B.w_bv, q, dr, eta, _ = pas_sol(B.w_bv, ru_b, cn_b, KC["bv"], eau_b, et0_b)
    B.s_q += q; B.s_dr += dr; B.s_eta += eta
    B.ruis_jour = q
    in_n = B.surface_m2 * dr / 1000.0; in_r = B.surface_m2 * CAPTAGE * q / 1000.0
    avant = B.nappe + B.retenue + in_n + in_r
    B.nappe, B.retenue, ev, ex, deb = pas_ressource(B.nappe, B.retenue, B.cap_n, B.cap_r, B.surf_max, in_n, in_r, et0_b)
    B.c_in_n += in_n; B.c_in_r += in_r; B.c_evap += ev; B.c_exut += ex; B.c_debord += deb
    _emporter(T, np.divide(ex + deb, avant, out=np.zeros_like(avant), where=avant > 0))
    # les prelevements de fond : l eau potable d abord, l irrigation ensuite
    if "domestique" not in T.usages_repris:
        dem = B.pop * DOTATION_M3
        for b in np.nonzero(dem > 0)[0].tolist(): _servir(p, T, b, "domestique", float(dem[b]))
    if "irrigation" not in T.usages_repris:
        a_irr = P.surface_ha * P.irrigue
        brut = besoin_irrigation(P.w_irr, P.ru) * 10.0 * a_irr / EFFICIENCE        # m3 ( 1 mm sur 1 ha = 10 m3 )
        par_b = np.bincount(P.bassin, weights=brut, minlength=len(B.nom))
        part = np.zeros(len(B.nom))
        for b in np.nonzero(par_b > 0)[0].tolist():
            part[b] = _servir(p, T, b, "irrigation", float(par_b[b])) / par_b[b]
        recu = brut * part[P.bassin]                                                 # m3 bruts livres a chaque parcelle
        mm = np.divide(recu, 10.0 * a_irr, out=np.zeros_like(recu), where=a_irr > 0)
        P.w_irr = P.w_irr + EFFICIENCE * mm
        P.c_irr_brut += mm; P.c_irr_pertes += (1 - EFFICIENCE) * mm


def _servir(p, T, b, usage, m3):
    """Un prelevement dans le bassin b : la restriction coupe sa part, la reserve exploitable borne le reste ; l eau
    emporte ses polluants. Tout est compte : cumul du bilan, usage, et les compteurs du jour qui font la note."""
    B = T.bassins
    k = USAGES.index(usage)
    coupe = m3 * COUPURES[B.restriction[b], k]
    stock = B.nappe[b] + B.retenue[b]
    n, r, livre = retirer(B.nappe[b], B.retenue[b], B.min_n[b], B.min_r[b], m3 - coupe)
    B.nappe[b], B.retenue[b] = n, r
    livre = float(livre)
    B.c_prel[b] += livre; B.par_usage[b, k] += livre
    B.c_dem[b] += m3; B.c_cut[b] += coupe; B.c_liv[b] += livre
    if stock > 0 and livre > 0:
        f = livre / stock
        for x, nom in enumerate(EAU):
            dm = T.pollution.eau[b, x] * f
            T.pollution.eau[b, x] -= dm; T.pollution.c_evacue[nom] += dm
    if livre > 0: p.compter("prelevement_eau", livre)
    return livre


def _emporter(T, frac):
    """L eau qui sort d un bassin ( exutoire, debordement ) emporte sa part des polluants dissous."""
    P = T.pollution
    for x, nom in enumerate(EAU):
        dm = P.eau[:, x] * frac
        P.eau[:, x] -= dm; P.c_evacue[nom] += float(dm.sum())


def _facteurs_fermes(p, T, doy):
    """Le rendement climatique de chaque village : l evapotranspiration reelle des 30 derniers jours rapportee a la
    potentielle, comparee a ce qu elle est en annee normale a cette date ( part seche et part irriguee, ponderees par
    ce qu elles produisent normalement ), passee par la reponse de la FAO ( 1 - Ky ( 1 - ETR/ETR normale ) ), puis la
    chaleur et les crues. Une annee normale donne 1 en moyenne ; une annee humide un peu plus ; une secheresse moins."""
    P, N = T.parcelles, T.normales
    i, s = P.ile, P.sol
    ne_s, nm_s = N.eta_sec[i, s, doy], N.etm_sec[i, s, doy]
    ne_i, nm_i = N.eta_irr[i, s, doy], N.etm_irr[i, s, doy]
    def rel(eta, etm, ne, nm):
        r = np.divide(eta, etm, out=np.ones_like(eta), where=etm > 1e-9)
        rn = np.divide(ne, nm, out=np.ones_like(ne), where=nm > 1e-9)
        return np.clip(r / np.maximum(rn, 1e-3), 0.0, Q_MAX)
    ws, wi = (1 - P.irrigue) * ne_s, P.irrigue * ne_i
    tot = ws + wi
    rel_ = np.divide(ws * rel(P.eta_sec, P.etm_sec, ne_s, nm_s) + wi * rel(P.eta_irr, P.etm_irr, ne_i, nm_i), tot,
                     out=np.ones_like(tot), where=tot > 1e-6)
    f = np.clip(1.0 - KY * (1.0 - rel_), 0.0, F_MAX)
    f = f * np.clip(1.0 - K_CHALEUR * T.etat.chaleur[i], 0.0, 1.0)
    f = f * np.where(P.inond_fin >= p.jour, P.inond_facteur, 1.0)
    P.facteur = f
    _pousser_chocs(p, T)


def _pousser_chocs(p, T):
    """Le pont avec le moteur E1 : chaque village recoit une entree de `w.chocs` pour aujourd hui, qui compose son
    rendement climatique avec le choc pose par un autre ( Monde.facteur_choc ne lit que le premier qui s applique ).
    Une donnee, pas une methode : rien du moteur n est remplace. Coupe si l agriculture est installee."""
    w, j = p.w, p.jour
    autres = [c for c in w.chocs if not c.get("territoire")]
    if not T.pont_e1 or p.a("agriculture"):
        w.chocs[:] = autres; return
    miens = []
    for lid, f in zip(T.parcelles.lieu_id, T.parcelles.facteur.tolist()):
        if lid not in w.entreprises: continue
        for c in autres:
            if c["debut"] <= j < c["debut"] + c["jours"] and lid in c["lieux"]:
                f *= c["facteur"]; break
        miens.append({"debut": j, "jours": 1, "lieux": (lid,), "facteur": f, "territoire": True})
    w.chocs[:] = miens + autres


def _catastrophes(p, T, doy):
    j, m, B = p.jour, T.meteo, T.bassins
    T.catastrophes = [c for c in T.catastrophes if c.fin_j >= j]
    # secheresse : le deficit de pluie cumule, classe aux quantiles de la climatologie de l ile
    ind = T.etat.deficit / T.tab.p_an
    for i, ile in enumerate(T.iles):
        c = int(np.searchsorted(T.normales.seuils[i], ind[i], side="right"))
        if c >= 2 and not T.en_secheresse[i]:
            T.en_secheresse[i] = True
            p.noter("secheresse", ile=ile, lieu=T.capitale_ile[i], gravite=c, indice=round(float(ind[i]), 3))
        elif c == 0 and T.en_secheresse[i]:
            T.en_secheresse[i] = False
            p.noter("fin_secheresse", ile=ile, lieu=T.capitale_ile[i])
        if T.en_secheresse[i]:
            T.catastrophes.append(Catastrophe("secheresse", ile, T.capitale_ile[i], max(2, c), j, j, float(ind[i])))
        T.classe_secheresse[i] = c
        # incendie : le risque du jour ( l incendie lui-meme est au domaine 18 )
        if m.ffdi[i] >= FFDI_ALERTE:
            cl = int(np.searchsorted(FFDI_SEUILS, m.ffdi[i], side="right"))
            T.catastrophes.append(Catastrophe("risque_incendie", ile, T.capitale_ile[i], cl, j, j, float(m.ffdi[i])))
            p.noter("alerte_incendie", ile=ile, lieu=T.capitale_ile[i], gravite=cl, indice=round(float(m.ffdi[i]), 1))
            T.n_alertes += 1
    # crues : le ruissellement du bassin en un jour
    for b in np.nonzero(B.ruis_jour >= SEUILS_CRUE[0])[0].tolist():
        g = int(np.searchsorted(SEUILS_CRUE, B.ruis_jour[b], side="right"))
        i = int(B.ile[b])
        T.catastrophes.append(Catastrophe("inondation", T.iles[i], B.nom[b], g, j, j + 2, float(B.ruis_jour[b])))
        p.noter("inondation", ile=T.iles[i], lieu=B.nom[b], gravite=g, ruissellement_mm=round(float(B.ruis_jour[b]), 1),
                pluie_mm=round(float(m.pluie[i]), 1))
        P = T.parcelles
        touche = P.bassin == b
        P.inond_facteur = np.where(touche, np.minimum(np.where(P.inond_fin >= j, P.inond_facteur, 1.0),
                                                      1.0 - DEGAT_CRUE * g), P.inond_facteur)
        P.inond_fin = np.where(touche, j + DUREE_DEGAT_J, P.inond_fin)
        T.n_crues += 1
    # seismes
    rng = p.du_jour("territoire_seismes")
    for i, ile in enumerate(T.iles):
        sel = np.nonzero(T.lieu_ile == i)[0]
        for mag, x, y, h, rep in seismes_du_jour(SISMICITE[ile], T.sequences[i], j, rng):
            T.n_seismes += 1
            d = np.hypot(T.lieu_pos[sel, 0] - (T.centres[i][0] + 1000 * x), T.lieu_pos[sel, 1] - (T.centres[i][1] + 1000 * y)) / 1000
            mmi = intensite(mag, np.hypot(d, h))
            k = int(np.argmax(mmi))
            if mmi[k] < MMI_RESSENTI:
                p.compter("seisme_non_ressenti"); continue
            lieu = T.lieux[int(sel[k])]
            inten = {T.lieux[int(sel[a])]: round(float(mmi[a]), 1) for a in np.nonzero(mmi >= 4.0)[0].tolist()}
            T.catastrophes.append(Catastrophe("seisme", ile, lieu, round(float(mmi[k])), j, j, mag, inten))
            p.noter("seisme", ile=ile, lieu=lieu, gravite=int(round(float(mmi[k]))), magnitude=round(mag, 1),
                    profondeur_km=round(h, 1), distance_km=round(float(d[k]), 1), replique=rep)


def _degradation(T):
    """Un jour de degradation des polluants de l eau et du sol ( demi-vie )."""
    P = T.pollution
    for tab, noms in ((P.eau, EAU), (P.sol, SOL)):
        for x, nom in enumerate(noms):
            hl = POLLUANT[nom].demi_vie_j
            if math.isinf(hl): continue
            dm = tab[:, x] * (1.0 - 0.5 ** (1.0 / hl))
            tab[:, x] -= dm; P.c_degrade[nom] += float(dm.sum())


# ================================================================== le soir ( cloture du jour )
def _cloture(p, comptes):
    T = p.domaine("territoire")
    if T.meteo is None: return
    _sites_e1(p, T)
    _air_du_jour(T)
    _noter_eau(p, T)


def _sites_e1(p, T):
    """Ce que les sites du moteur E1 ont produit aujourd hui ( produit_du_jour est un cumul ) : leur eau et leurs
    rejets de fond, tant que leur domaine n est pas installe."""
    for e in p.w.entreprises.values():
        if e.type == "ferme": continue
        tot = sum(e.produit_du_jour.values())
        delta = tot - T.sites.get(e.id, tot)
        T.sites[e.id] = tot
        if delta <= 0: continue
        usage = USAGE_SITE.get(e.type)
        k = T.index_lieu.get(e.lieu.id)
        if k is None or usage is None: continue
        if usage not in T.usages_repris and not p.a(PROPRIETAIRE_USAGE[usage]):
            _servir(p, T, int(T.lieu_bassin[k]), usage, delta * EAU_PAR_UNITE[e.type])
        if not p.a(PROPRIETAIRE_USAGE[usage]):
            for nom, f in EMISSIONS_E1.get(e.type, ()): rejeter(p, e.lieu, nom, delta * f)


def concentration_air(kg, vent_ms, largeur_m, hauteur_m=HAUTEUR_MELANGE):
    """Une boite d air ventilee : ce qui est emis dans la journee, dilue dans le debit d air qui traverse le lieu.
    ug/m3 = kg * 1e9 / ( vent * 86 400 s * hauteur de melange * largeur )."""
    return kg * 1e9 / (np.maximum(vent_ms, 0.5) * 86400.0 * hauteur_m * largeur_m)


def _air_du_jour(T):
    P = T.pollution
    vent = T.meteo.vent[T.lieu_ile]
    for x, nom in enumerate(AIR):
        P.air_conc[:, x] = POLLUANT[nom].fond + concentration_air(P.air_jour[:, x], vent, T.lieu_largeur)
        P.c_ventile[nom] += float(P.air_jour[:, x].sum())
    P.air_jour[:] = 0.0


def _noter_eau(p, T):
    B = T.bassins
    voulu = B.c_dem - B.c_cut
    manque = np.maximum(0.0, voulu - B.c_liv)
    pen = (voulu > 0) & (manque > SEUIL_PENURIE * voulu)
    r = np.where(pen, 0.0, 1.0) - KAPPA * np.divide(B.c_cut, B.c_dem, out=np.zeros_like(B.c_dem), where=B.c_dem > 0)
    dec = T.decideur
    for b in range(len(B.nom)): dec.noter(b, float(r[b]), p.jour)
    B.jours_penurie += pen
    if manque.sum() > 0: p.compter("penurie_eau", float(manque.sum()))
    for h, v in ((B.h_dem, B.c_dem), (B.h_manque, manque), (B.h_dispo, B.dispo())):
        h[:, :-1] = h[:, 1:]; h[:, -1] = v
    B.c_dem[:] = 0.0; B.c_cut[:] = 0.0; B.c_liv[:] = 0.0


def _traits(T, b, doy):
    B = T.bassins
    i = int(B.ile[b])
    expl = max(1e-9, float(B.exploitable()[b]))
    dispo = float(B.dispo()[b])
    dem7 = float(B.h_dem[b].mean())
    normal30 = float(T.tab.r[i, [(doy - k) % JOURS_AN for k in range(1, 31)]].sum())
    return (min(1.0, dispo / expl),
            min(1.0, dispo / max(1e-9, dem7) / 120.0) if dem7 > 0 else 1.0,
            min(1.0, float(T.pluie30[i].sum()) / max(1e-9, 2 * normal30)),
            float(T.tab.r90[i, doy] / T.tab.r90[i].max()),
            min(1.0, max(0.0, 0.5 + (dispo - float(B.h_dispo[b, 0])) / (0.2 * expl))),
            B.restriction[b] / 2.0,
            min(1.0, float(B.h_manque[b].sum()) / max(1e-9, float(B.h_dem[b].sum()))) if B.h_dem[b].sum() > 0 else 0.0,
            T.classe_secheresse[i] / 3.0)


def _decider(p, T, doy):
    """Chaque bassin qui a des usagers decide ( un bassin sans demande depuis 7 jours n a pas de gestionnaire )."""
    B = T.bassins
    for b in np.nonzero(B.h_dem.sum(1) > 0)[0].tolist():
        a = T.decideur.decider(b, ContexteEau(_traits(T, b, doy), b))
        if a != B.restriction[b]:
            p.noter("restriction_eau", lieu=B.nom[b], niveau=ACTIONS_EAU[a])
        B.restriction[b] = a


def _recenser(p, T):
    """Les habitants de chaque bassin, une fois par semaine ( la population bouge lentement )."""
    pop = np.zeros(len(T.bassins.nom))
    for mg in p.w.menages:
        k = T.index_lieu.get(mg.domicile.id) if mg.domicile is not None else None
        if k is None: continue
        pop[T.lieu_bassin[k]] += sum(1 for x in mg.membres if x.vivant)
    T.bassins.pop = pop


# ================================================================== l API des autres domaines
class MeteoLocale:
    """La meteo du jour d une ile, telle qu un autre domaine la lit."""
    __slots__ = ("ile", "jour", "pluie_mm", "neige_tombee_mm", "neige_sol_mm", "tmin", "tmax", "tmoy", "vent_ms",
                 "hr", "et0_mm", "ffdi", "cyclone")

    def __init__(self, **v):
        for k in self.__slots__: setattr(self, k, v[k])


def meteo(p, ou):
    """La meteo du jour de l ile de `ou` ( un nom d ile, un Lieu, l identifiant d un lieu )."""
    T = p.domaine("territoire"); i = _ile_index(T, ou); m = T.meteo
    return MeteoLocale(ile=T.iles[i], jour=T.jour_fait, pluie_mm=float(m.pluie[i]), neige_tombee_mm=float(m.neige_tombee[i]),
                       neige_sol_mm=float(m.neige_sol[i]), tmin=float(m.tmin[i]), tmax=float(m.tmax[i]),
                       tmoy=float(m.tmoy[i]), vent_ms=float(m.vent[i]), hr=float(m.hr[i]), et0_mm=float(m.et0[i]),
                       ffdi=float(m.ffdi[i]), cyclone=int(m.cyclone[i]))


def saison(p, ou):
    """hiver, printemps, ete, automne ( saisons meteorologiques, selon l hemisphere de la station modele ) ; sous les
    tropiques : humide ou seche."""
    T = p.domaine("territoire"); i = _ile_index(T, ou); pr = T.profils[i]
    d = p.socle.calendrier.date(p.pas)
    if pr.tropical(): return "humide" if d.month in pr.mois_humides else "seche"
    return p.socle.calendrier.saison(d, pr.latitude)


def rendement_climatique(p, lieu):
    """Le rendement climatique du jour de la parcelle d un village ( 1 = annee normale )."""
    T = p.domaine("territoire")
    k = T.parcelles.lieu_id.index(_id(lieu))
    return float(T.parcelles.facteur[k])


def eau_disponible(p, lieu=None, ile=None):
    """Le volume exploitable ( m3, au-dessus des planchers ) du bassin d un lieu, ou de toute une ile."""
    T = p.domaine("territoire"); B = T.bassins
    if lieu is not None: return float(B.dispo()[bassin_de(p, lieu)])
    i = T.iles.index(ile)
    return float(B.dispo()[B.ile == i].sum())


def prelever(p, lieu, m3, usage):
    """Prelever `m3` d eau brute dans le bassin d un lieu, pour un usage ( domestique, irrigation, industrie,
    energie ). La restriction du bassin coupe sa part ; on ne preleve pas ce qui n est pas la. Rend les m3 livres.
    Un domaine qui preleve un usage appelle d abord `reprendre_usage`, sinon il sera compte deux fois."""
    if usage not in USAGES: raise ValueError(f"usage inconnu {usage!r} : {USAGES}")
    if not 0.0 <= m3 < math.inf: raise ValueError(f"volume invalide {m3!r}")
    T = p.domaine("territoire")
    return _servir(p, T, bassin_de(p, lieu), usage, float(m3))


def reprendre_usage(p, usage):
    """Un domaine prend un usage en charge : le territoire cesse ses prelevements de fond pour cet usage."""
    if usage not in USAGES: raise ValueError(f"usage inconnu {usage!r} : {USAGES}")
    p.domaine("territoire").usages_repris.add(usage)


def rejeter(p, lieu, polluant, kg):
    """Rejeter `kg` kilogrammes d un polluant a un lieu : dans l air du lieu, dans l eau brute de son bassin ou dans son
    sol, selon le polluant. Le territoire est le puits : il degrade, dilue, emporte."""
    x = POLLUANT.get(polluant)
    if x is None: raise ValueError(f"polluant inconnu {polluant!r} : {tuple(POLLUANT)}")
    if not 0.0 <= kg < math.inf: raise ValueError(f"masse invalide {kg!r}")
    T = p.domaine("territoire")
    k = T.index_lieu.get(_id(lieu))
    if k is None: raise KeyError(f"territoire : lieu inconnu {lieu!r}")
    tab, noms = _stocks_pollution(T, x.milieu)
    tab[int(T.lieu_bassin[k]) if x.milieu == "eau" else k, noms.index(polluant)] += kg
    T.pollution.c_rejete[polluant] += kg
    p.compter("rejet_polluant", kg)


def concentration(p, lieu, polluant):
    """La concentration d un polluant a un lieu, dans l unite du polluant ( air : celle de la veille )."""
    T = p.domaine("territoire"); x = POLLUANT[polluant]; P = T.pollution
    k = T.index_lieu[_id(lieu)]
    if x.milieu == "air": return float(P.air_conc[k, AIR.index(polluant)])
    if x.milieu == "eau":
        b = int(T.lieu_bassin[k]); B = T.bassins
        v = B.nappe[b] + B.retenue[b]
        return x.fond + (float(P.eau[b, EAU.index(polluant)]) * 1000.0 / v if v > 0 else 0.0)
    return x.fond + float(P.sol[k, SOL.index(polluant)]) * 1e6 / (T.lieu_surface[k] * PROF_SOL * DENSITE_SOL)


def pollution(p, lieu):
    """( air, eau, sol ) : pour chaque milieu, le pire polluant rapporte a sa limite ( 1 = a la limite ). Ce que la
    medecine lit."""
    return tuple(max(concentration(p, lieu, n) / POLLUANT[n].limite for n in noms) for noms in (AIR, EAU, SOL))


def risque_incendie(p, ou):
    """( indice FFDI du jour, classe ) pour l ile de `ou`."""
    T = p.domaine("territoire"); i = _ile_index(T, ou)
    v = float(T.meteo.ffdi[i])
    return v, FFDI_CLASSES[int(np.searchsorted(FFDI_SEUILS, v, side="right"))]


def catastrophes_en_cours(p, ile=None, type_=None):
    T = p.domaine("territoire")
    return [c for c in T.catastrophes if c.fin_j >= p.jour and (ile is None or c.ile == ile)
            and (type_ is None or c.type == type_)]


def vers_arma(p, ile):
    """La meteo du jour en valeurs des commandes d Arma 3 ( setOvercast, setRain, setFog dans [0 ; 1], setWind en m/s ) ;
    l intensite de BIS_fnc_earthquake ( 1 a 4 ) du seisme le plus fort du jour. arma_preuve = None."""
    T = p.domaine("territoire"); i = _ile_index(T, ile); m = T.meteo
    sis = [c.gravite for c in catastrophes_en_cours(p, T.iles[i], "seisme") if c.debut_j == p.jour]
    return {"overcast": float(min(1.0, 0.25 + m.pluie[i] / 20.0)), "rain": float(min(1.0, m.pluie[i] / 30.0)),
            "fog": float(min(0.5, max(0.0, (m.hr[i] - 85.0) / 30.0))),
            "wind": (float(m.vent_x[i]), float(m.vent_y[i])),
            "earthquake": int(min(4, max(0, max(sis) - 3))) if sis else 0, "arma_preuve": None}


# ------------------------------------------------------------------ scenarios ( portes, etudes )
def forcer_meteo(p, ile, jours, pluie=1.0, chaleur_c=0.0, debut=None):
    """Un forcage du temps d une ile : la pluie multipliee par `pluie`, la temperature augmentee de `chaleur_c`, pendant
    `jours` jours depuis `debut` ( aujourd hui par defaut ). Le hasard des jours suivants n est pas decale."""
    if not 0.0 <= pluie <= 10.0 or not -20.0 <= chaleur_c <= 20.0 or not 1 <= jours <= 3650: raise ValueError("forcage hors bornes")
    T = p.domaine("territoire")
    T.forcages.append((T.iles.index(ile), p.jour if debut is None else int(debut), int(jours), float(pluie), float(chaleur_c)))


def forcer_reserves(p, part, ile=None):
    """Porte les reserves des bassins ( d une ile, ou toutes ) a `part` de leur volume exploitable, au-dessus des
    planchers. Le changement est un terme compte du bilan ( forcage ) : le bilan continue de fermer."""
    if not 0.0 <= part <= 1.0: raise ValueError("part hors [0 ; 1]")
    T = p.domaine("territoire"); B = T.bassins
    sel = np.ones(len(B.nom), bool) if ile is None else B.ile == T.iles.index(ile)
    for b in np.nonzero(sel)[0].tolist():
        n = B.min_n[b] + part * (B.cap_n[b] - B.min_n[b]); r = B.min_r[b] + part * (B.cap_r[b] - B.min_r[b])
        B.c_forc[b] += (n - B.nappe[b]) + (r - B.retenue[b])
        B.nappe[b], B.retenue[b] = n, r


def imposer_secheresse(p, ile, jours, reserves=0.10, chaleur_c=3.0):
    """Une secheresse sur une ile : un hiver sec derriere elle ( reserves a `reserves` de l exploitable, sols au point
    de fletrissement, deficit de pluie au niveau d une secheresse extreme ) et `jours` jours sans pluie, plus chauds
    de `chaleur_c`. Chaque changement d etat passe par un terme compte des bilans."""
    T = p.domaine("territoire"); i = T.iles.index(ile)
    forcer_meteo(p, ile, jours, pluie=0.0, chaleur_c=chaleur_c)
    forcer_reserves(p, reserves, ile)
    P, B = T.parcelles, T.bassins
    sel = P.ile == i
    P.w0_sec[sel] -= P.w_sec[sel]; P.w_sec[sel] = 0.0         # le point de depart du bilan suit le forcage
    P.w0_irr[sel] -= P.w_irr[sel]; P.w_irr[sel] = 0.0
    sb = B.ile == i
    B.s_w0[sb] -= B.w_bv[sb]; B.w_bv[sb] = 0.0
    T.etat.deficit[i] = max(T.etat.deficit[i], 1.2 * T.normales.seuils[i, 2] * T.tab.p_an[i])


# ------------------------------------------------------------------ bilans ( portes )
def bilan_eau(p):
    """Par bassin : ( stock - stock de depart ) - ( entrees - sorties + forcages ), en m3. Zero, sinon de l eau est
    nee ou morte hors des flux comptes."""
    B = p.domaine("territoire").bassins
    flux = B.c_in_n + B.c_in_r - B.c_evap - B.c_exut - B.c_debord - B.c_prel + B.c_forc
    return (B.nappe + B.retenue) - B.stock0 - flux


def bilan_sols(p):
    """Le pire ecart ( mm ) des bilans des sols ( parcelles seches, irriguees, maquis des bassins ) et de la neige."""
    T = p.domaine("territoire"); P, B = T.parcelles, T.bassins
    e_sec = P.c_eau - P.c_q_sec - P.c_dr_sec - P.c_eta_sec - (P.w_sec - P.w0_sec)
    e_irr = P.c_eau + P.c_irr_brut - P.c_irr_pertes - P.c_q_irr - P.c_dr_irr - P.c_eta_irr - (P.w_irr - P.w0_irr)
    e_bv = B.s_eau - B.s_q - B.s_dr - B.s_eta - (B.w_bv - B.s_w0)
    e_ng = T.c_neige[0] - T.c_neige[1] - (T.etat.neige - T.neige0)
    return float(max(np.abs(e).max() if len(e) else 0.0 for e in (e_sec, e_irr, e_bv, e_ng)))


def bilan_pollution(p):
    """{ polluant : masse presente - ( depart + rejete - degrade - evacue - ventile ) } en kg."""
    T = p.domaine("territoire"); P = T.pollution
    out = {}
    for nom in POLLUANT:
        tab, noms = _stocks_pollution(T, POLLUANT[nom].milieu)
        m = float(tab[:, noms.index(nom)].sum())
        out[nom] = m - (P.m0[nom] + P.c_rejete[nom] - P.c_degrade[nom] - P.c_evacue[nom] - P.c_ventile[nom])
    return out


# ================================================================== installation
def _chefs_lieux(lieux):
    chefs = sorted((l for l in lieux if l.type in ("capitale", "ville")), key=lambda l: l.id)
    return chefs or sorted((l for l in lieux if l.type == "village"), key=lambda l: l.id)


def _tirer_sol(rng, ile):
    noms = sorted(SOLS_ILE[ile]); poids = np.array([SOLS_ILE[ile][n] for n in noms])
    return SOL_INDEX[noms[int(np.searchsorted(np.cumsum(poids / poids.sum()), rng.random(), side="right"))]]


def installer(p):
    w = p.w
    T = Territoire()
    T.iles = list(w.carte.iles)
    for ile in T.iles:
        if ile not in PROFILS: raise KeyError(f"territoire : pas de climat pour l ile {ile!r}")
    T.profils = [PROFILS[i] for i in T.iles]
    n_iles = len(T.iles)
    rng = p.hasard("territoire_installation")
    # ---- les lieux et les bassins
    lieux = sorted(w.carte.lieux.values(), key=lambda l: (T.iles.index(l.ile), l.id))
    T.lieux = [l.id for l in lieux]
    T.index_lieu = {lid: k for k, lid in enumerate(T.lieux)}
    T.lieu_ile = np.array([T.iles.index(l.ile) for l in lieux], np.int64)
    T.lieu_pos = np.array([l.pos[:2] for l in lieux], float)
    T.lieu_largeur = np.array([max(500.0, 2.0 * max(l.rayon) if l.rayon else 500.0) for l in lieux])
    T.lieu_surface = np.array([max(1e5, math.pi * max(100.0, l.rayon[0]) * max(100.0, l.rayon[1])) if l.rayon else 1e5
                               for l in lieux])
    T.centres = [tuple(T.lieu_pos[T.lieu_ile == i].mean(axis=0)) if (T.lieu_ile == i).any() else (0.0, 0.0)
                 for i in range(n_iles)]
    noms_b, iles_b, T.capitale_ile = [], [], []
    T.lieu_bassin = np.zeros(len(lieux), np.int64)
    for i, ile in enumerate(T.iles):
        du = [l for l in lieux if l.ile == ile]
        chefs = _chefs_lieux(du)
        caps = sorted(l.id for l in du if l.type == "capitale")
        T.capitale_ile.append(caps[0] if caps else (chefs[0].id if chefs else ile))
        base = len(noms_b)
        for c in chefs: noms_b.append(c.id); iles_b.append(i)
        for l in du:
            c = min(range(len(chefs)), key=lambda k: (l.distance(chefs[k]), chefs[k].id))
            T.lieu_bassin[T.index_lieu[l.id]] = base + c
    B = T.bassins = Bassins(noms_b, iles_b, [_tirer_sol(rng, T.iles[i]) for i in iles_b])
    # ---- les parcelles : une par village, sa surface suit ses paysans
    paysans = {}
    for h in w.habitants:
        if h.role == "paysan" and h.travail is not None: paysans[h.travail.id] = paysans.get(h.travail.id, 0) + 1
    villages = [l for l in lieux if l.type == "village"]
    T.parcelles = P = Parcelles([l.id for l in villages], [T.lieu_bassin[T.index_lieu[l.id]] for l in villages],
                                [T.iles.index(l.ile) for l in villages], [_tirer_sol(rng, l.ile) for l in villages],
                                [HA_PAR_PAYSAN * max(1, paysans.get(l.id, 0)) for l in villages],
                                [IRRIGUE[l.ile] for l in villages])
    # ---- les normales : 32 annees de climat par ile
    N = T.normales = NormalesPays(n_iles)
    ser, et0s = mesurer_normales(T.profils, [p.socle.hasard.sous_flux("territoire_normales", ILES_CONNUES.index(ile))
                                             for ile in T.iles], N)
    # ---- la demande normale de chaque bassin, puis sa ressource
    _recenser(p, T)
    T.sites = {}
    ind_an = np.zeros(len(noms_b))
    ouvriers = {}
    for h in w.habitants:
        if h.travail is not None: ouvriers[(h.travail.id, h.role)] = ouvriers.get((h.travail.id, h.role), 0) + 1
    for e in w.entreprises.values():
        if e.type == "ferme" or e.type not in EAU_PAR_UNITE: continue
        T.sites[e.id] = sum(e.produit_du_jour.values())
        k = T.index_lieu.get(e.lieu.id)
        if k is None: continue
        unites = sum(e.produits.values()) * ouvriers.get((e.lieu.id, e.role), 0) * 8.0 * ACTIVITE_NOMINALE
        ind_an[T.lieu_bassin[k]] += unites * EAU_PAR_UNITE[e.type] * JOURS_AN
    dom_an = np.maximum(B.pop, 0) * DOTATION_M3 * JOURS_AN
    irr_p = P.surface_ha * P.irrigue * N.irr_an[P.ile, P.sol] * 10.0 / EFFICIENCE
    irr_an = np.bincount(P.bassin, weights=irr_p, minlength=len(noms_b))
    B.demande_an = np.maximum(dom_an + irr_an + ind_an, HAB_MIN * DOTATION_M3 * JOURS_AN)
    wei = np.array([WEI[T.iles[i]] for i in B.ile])
    d_an, q_an = N.drain_an[B.ile, B.sol], N.ruis_an[B.ile, B.sol]
    B.surface_m2 = B.demande_an / wei / np.maximum(1e-9, (d_an + CAPTAGE * q_an) / 1000.0)
    B.cap_n = CAP_NAPPE * B.surface_m2 * d_an / 1000.0; B.min_n = MIN_NAPPE * B.cap_n
    B.cap_r = CAP_RETENUE * B.surface_m2 * CAPTAGE * q_an / 1000.0; B.min_r = MIN_RETENUE * B.cap_r
    B.surf_max = B.cap_r / PROF_RETENUE
    doy = T.doy = _doy(p)
    parts, poids = np.zeros((n_iles, 3)), np.zeros((n_iles, len(SOLS)))
    for i, ile in enumerate(T.iles):
        sb = B.ile == i
        v = np.array([dom_an[sb].sum(), irr_an[sb].sum(), ind_an[sb].sum()])
        parts[i] = v / v.sum() if v.sum() > 0 else (1.0, 0.0, 0.0)
        poids[i] = [SOLS_ILE[ile].get(x.nom, 0.0) for x in SOLS]; poids[i] /= poids[i].sum()
    remplissage_normal(N, ser, et0s, poids, parts, [WEI[i] for i in T.iles])
    ser = et0s = None
    B.nappe = N.rempl_n[B.ile, doy] * B.cap_n; B.retenue = N.rempl_r[B.ile, doy] * B.cap_r
    B.stock0 = B.nappe + B.retenue
    # ---- l etat de depart : normal pour la date
    B.w_bv = N.w_bv[B.ile, B.sol, doy].copy(); B.s_w0 = B.w_bv.copy()
    P.w_sec = N.w_sec[P.ile, P.sol, doy].copy(); P.w_irr = N.w_irr[P.ile, P.sol, doy].copy()
    P.w0_sec, P.w0_irr = P.w_sec.copy(), P.w_irr.copy()
    P.eta_sec, P.etm_sec = N.eta_sec[P.ile, P.sol, doy].copy(), N.etm_sec[P.ile, P.sol, doy].copy()
    P.eta_irr, P.etm_irr = N.eta_irr[P.ile, P.sol, doy].copy(), N.etm_irr[P.ile, P.sol, doy].copy()
    T.tab = TableClimat(T.profils); T.etat = EtatMeteo(n_iles)
    T.etat.kbdi = N.kbdi[:, doy].copy(); T.etat.neige = N.neige[:, doy].copy()
    T.neige0 = T.etat.neige.copy(); T.c_neige = np.zeros((2, n_iles))
    T.pluie30 = np.tile(T.tab.r[:, [(doy - k) % JOURS_AN for k in range(30, 0, -1)]], 1)
    T.meteo = None; T.forcages = []; T.sequences = [[] for _ in range(n_iles)]
    T.pollution = Pollution(len(T.lieux), len(noms_b))
    T.catastrophes = []; T.classe_secheresse = np.zeros(n_iles, np.int64); T.en_secheresse = [False] * n_iles
    T.usages_repris = set(); T.pont_e1 = True; T.jour_fait = None
    T.n_seismes = T.n_crues = T.n_alertes = 0
    for b in range(len(noms_b)): B.h_dem[b] = B.demande_an[b] / JOURS_AN; B.h_dispo[b] = B.dispo()[b]
    # ---- le journal, la decision, l horloge
    J = p.socle.journal
    for t, champs in (("secheresse", ("ile", "lieu", "gravite", "indice")), ("fin_secheresse", ("ile", "lieu")),
                      ("inondation", ("ile", "lieu", "gravite", "ruissellement_mm", "pluie_mm")),
                      ("seisme", ("ile", "lieu", "gravite", "magnitude", "profondeur_km", "distance_km", "replique")),
                      ("cyclone", ("ile", "lieu", "gravite", "pluie_mm", "vent_ms")),
                      ("alerte_incendie", ("ile", "lieu", "gravite", "indice")), ("restriction_eau", ("lieu", "niveau"))):
        J.declarer(t, "territoire", "individuel", champs)
    for t in ("seisme_non_ressenti", "penurie_eau", "prelevement_eau", "rejet_polluant"):
        J.declarer(t, "territoire", "compte")
    T.decideur = p.decideur(POINT_EAU)
    p.domaines["territoire"] = T
    p.routine(0.0, 10, "territoire", _minuit)
    p.cloture("territoire", _cloture)
    _minuit(p)                                  # le jour en cours ( l installation tombe a 6 h le jour 0 )
    return T
