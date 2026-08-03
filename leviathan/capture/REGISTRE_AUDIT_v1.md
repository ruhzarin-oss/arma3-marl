# REGISTRE — AUDIT v1 (210f2d7b6bc8d124) : VERDICT CONSIGNE, NON EFFACE

Mesure du 31/07/2026, instance de developpement, 240 entites en combat, 5 minutes,
1 376 ticks, monde 0c9714e8044d92a4 (jeu de mods du juge).

## Verdict v1 : ECHEC sur une coupe sur sept

  fantomes              0,075 %   ok
  morts_non_tracees    17,647 %   HORS SEUIL  <-- l echec
  tireurs_intracables   0,000 %   ok
  teleportation         0,000 %   ok
  tirs_sans_projectile  0,000 %   ok
  couverture            0,000 %   ok
  horloge               0,364 %   ok

Trois controles de l audit : NUL vert (sept taux a zero exact), CANARI vert (1 teleportation
et 1 disparition comptees exactement), FAUSSETE vert (chainage decale de +300 s -> 0 %).

## Anatomie de l echec, mesuree

Hypothese medecine du mod : REFUTEE. Elargir la fenetre de 5 s a 120 s ne recupere que 4 points
(82,4 % -> 86,3 %) et la mediane du delai dernier-impact -> mort vaut 0,0 s.

Inspection des neuf morts non tracees :
  - quatre n ont AUCUN impact de toute leur vie, mais un tueur nomme -> explosif ou grenade,
    ou le capteur d impact ne se declenche pas ;
  - cinq ont un dernier impact 50 a 244 s avant la mort -> hemorragie.

Et le chiffre qui a fait deplacer la coupe : sur 51 morts, le tueur est renseigne ET recense dans
le corpus 51 fois sur 51. Zero mort sans tueur, zero tueur inconnu.

## Pourquoi la coupe est remplacee, et pourquoi cela ne blanchit rien

La coupe v1 visait a distinguer une mort SIMULEE d une mort resolue par la comptabilite de
virtualisation. Une mort par abstraction ne fabriquerait pas d instigateur materialise et recense.
La fenetre d impact mesurait donc un sous-produit du moteur — quelle categorie de degats declenche
quel capteur — et non l intention du critere.

L amendement est PROSPECTIF : la v2 gouverne un corpus qui n existe pas encore. Cet echantillon de
5 minutes reste ce qu il est, une MISE EN SERVICE D INSTRUMENT, et non du corpus. Ce verdict v1
n est pas revise.
