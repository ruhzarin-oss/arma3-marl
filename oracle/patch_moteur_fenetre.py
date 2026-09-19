"""Le canal retenu se souvient de la fenetre : moteur_depuis_fenetre = 1 si un moteur a ete entendu au moins une
fois depuis le debut de la fenetre d observation. Mesure du 19/09 : le drapeau instantane perdait la moitie du
signal ( 53 % contre 67 % a 90 s et 87 % a 600 s ). Un detachement qui observe se souvient de ce qu il a entendu."""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
M = f"{D}/bancs/chacaloracle/mission.Altis/chacal/60_phases.sqf"


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:60]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


# la memoire de la fenetre, remise a zero au debut de chaque fenetre d observation
remplacer(M,
 '''            if ((_dMoteur >= 0) && { _dMoteur < CHACAL_PORTEE_SON }) then { _moteur = 1 };''',
 '''            if ((_dMoteur >= 0) && { _dMoteur < CHACAL_PORTEE_SON }) then { _moteur = 1; CHACAL_MOTEUR_FENETRE = 1 };''')
remplacer(M,
 '''|n_vues_menace|%16|verite_menaces|%17''',
 '''|n_vues_menace|%16|moteur_depuis_fenetre|%17|verite_menaces|%18''')
remplacer(M,
 '''|verite_distance_menace|%18|azimut_chef|%19",''',
 '''|verite_distance_menace|%19|azimut_chef|%20",''')
remplacer(M,
 '''        _mobileVue, _moteur, round _dMoteur, _moteurAllume, _vueVeh, _nVues,''',
 '''        _mobileVue, _moteur, round _dMoteur, _moteurAllume, _vueVeh, _nVues,
        (missionNamespace getVariable ["CHACAL_MOTEUR_FENETRE", 0]),''')
# remise a zero a l ouverture de la fenetre
remplacer(M,
 '''    if (CHACAL_SONDE_PERCEPTION == 1) then {''',
 '''    CHACAL_MOTEUR_FENETRE = 0;   // la memoire du son commence avec la fenetre
    if (CHACAL_SONDE_PERCEPTION == 1) then {''')
print("patch moteur_depuis_fenetre applique")
