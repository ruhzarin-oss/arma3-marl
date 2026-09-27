# Fusion du 27/09 : socle-du-pays + guerre-des-iles dans pays-sur-colonnes

Branche `fusion-27-09`, partie de `pays-sur-colonnes` ( 0d579fd ) : `socle-du-pays` ( domaines 14 à 27, 759936c ) puis
`guerre-des-iles` ( af99c4e ). Aucun conflit : la fusion ne modifie que deux fichiers existants ( `monde/archipel.py`,
commandes `guerre_*` ; `monde/pays/d06_etat.py`, passage d'année ), tout le reste est du code neuf.

## Ce qui est prouvé

| Porte | Résultat |
|---|---|
| Domaines d'origine ( 14, référence v8 ) | IDENTIQUE au bit sur les 5 mondes ; contrôle positif ( un milliardième de drachme ) : ÉCHOUE au jour 4 |
| Les 27 domaines ensemble | ne s'installaient PAS : `evacuation` déclaré par d18 ( crues ) et d26 ( évacuation sanitaire ) ; d26 écrit maintenant `evacuation_sanitaire` |
| Référence des 27 domaines | écrite deux fois : identique au bit ( déterministe ) ; contrôle positif : voir le commit |
| Passage d'année | 27 domaines, 1 000 habitants, 400 jours ( 15/06/2035 → juillet 2036 ) : VIVANT, conservation tenue à chaque relevé ; témoin sans le correctif de d06 ( `>=` ) : MORT au jour 200, `ValueError: jour 0 hors de l exercice de 366 jours` |
| Faim ( `sonde_faim.py 20 30`, 6 îles × 10 000, 30 jours ) | avant la fusion 3,4 jours de faim ( Malden 1,1, Stratis 0,8 ) ; après 2,3 ( 0,4 partout ) ; creux du jour 17 : 28 % → 20 %, fini le jour 18 |
| Tests du pays | 264 / 288 ; hors portes de coût, 16 échecs de comportement, tous connus ( liste `references/echecs_attendus_pays.txt` ) |

La référence d'avant la fusion reproduit exactement la nuit du 26/09 ( b259c4e ), île par île. Le total se lit ici en
somme des parts de ménages sans nourriture, jour par jour ( 3,4 ) ; le rapport du 26/09 disait 4,7 avec un autre
compte : seule la comparaison à méthode égale a un sens.

## Ce qui a été corrigé

1. **d26** : l'événement `evacuation` devient `evacuation_sanitaire` ( les 27 domaines ne s'installaient pas ensemble ).
2. **monde.py** : `ids_au_travail` / `nombre_au_travail` d'un métier inconnu rendent personne, comme l'ancien moteur
   ( `_par_travail.get(( lieu, role ), [])` ) ; le moteur en colonnes levait `KeyError: ''` quand d14 cherchait les
   employés d'une flotte dont le propriétaire n'a pas de métier ( l'État, un ménage ). `transport test_accidents` passe.
3. **Détection, copiée sur Arma** ( règle « dans le doute, copier le réel » ) :
   - d25 : portée d'un homme DEBOUT REGARDÉ 550 m de jour, 300 m de nuit ( nuit du 19/09 : de nuit ~ 85 % vus à
     250 m, médiane 300 à 450 m ; de jour ≥ 67 % à 550 m ), au lieu de 300 et 36 m. Les 36 m du 13/09 étaient la
     médiane des rencontres naturelles ( cibles accroupies, guetteurs qui balaient ) : les prendre comme portée de base
     comptait deux fois la posture ( × 0,42 ) et le regard ( × 0,5 ) que d26 applique déjà. Le 0,42 de d26 avait
     lui-même été tiré de ~ 300 m debout de nuit.
   - d26 : `PORTEE_ENTITE_M` ( 550, 300 ) ; `F_PERIPHERIE` 0,1 → 0,04, pour garder la mesure du 02/08 ( rien à 50 m
     sur le flanc ) : 44 m au plus pour le meilleur guetteur possible ( 1 100 m ).
   - tests : `test_connaissance_de_camp` ( de nuit, debout à 150 m : vu ; accroupi à 200 m : pas vu ),
     `test_regles_engagement` ( le contact connu par la seule rumeur passe de 150 à 300 m, hors de vue de nuit :
     252 m au plus accroupi ).
4. **Porte des domaines** : une référence dit ses domaines ( clé `_domaines` ) ; une référence qui ne les dit pas ( v1
   à v8 ) est jouée avec les 14 d'origine. `portes.sh` a une porte de plus, `domaines (27)`, contre
   `$HMT_REF/ref_domaines_tous.json` ; `refaire_references.sh` la reconstruit depuis une extraction propre du commit.

## Deuxième passe : une fuite entre îles ( d14 ), d13 en colonnes, règles remesurées

**Fuite entre îles.** Le premier `portes.sh` complet du moteur fusionné ( f82eb1d ) a refusé 3 portes, les trois qui
comparent l'archipel séquentiel aux six processus ( G3, traversée, enregistreur E1 ). Dichotomie sur les domaines :
13 domaines passent, 14 échouent → d14. Seule Malden différait, dès le jour 1 ( marchés, caisses, équipement ).
Cause : d14 mettait à 0 la part « transport » de `EC.PART_BIEN` — un tableau du MODULE d03 — de 18 h 50 à 19 h, puis
reposait la valeur sauvée. Le moteur achète AVANT les routines du pas ; dans l'archipel séquentiel, les six îles
alternent pas à pas dans un même processus : Altis reposait la part avant que Malden achète, puis Malden reposait le 0
sauvé. Correctif : la fenêtre est dans l'état de d03 de CE pays ( `Economie.part_bien`, None hors fenêtre ; d03 la lit
si elle existe ). Une île seule est identique au bit ( portes v8 et 27 domaines ) ; séquentiel = parallèle pour les six
îles, à 14 et à 27 domaines. Reste un piège sans effet : `_declarer` écrit `c.modele` dans les `CARAC` du module, jamais
relu.

**Les détenus comptés absents.** La porte G4 ( un corps par personne, chaque soir ) échouait aussi — cachée par
l'affichage de `portes.sh`, qui ne montre que les 8 dernières lignes : une personne par île, « absente » sans corps
ailleurs. d21 marque ses DÉTENUS `statut = ABSENT` pour que le moteur les sorte du travail et du ménage ; or ABSENT veut
dire « son corps est dans une autre île ou en mer ». Correctif du recensement de l'île ( `corps` ) : un détenu a son
corps ICI. ( Leur santé en prison : réglée dans la troisième passe, plus bas. )

**d13 `_apparier` en colonnes.** Les candidats d'un chercheur se calculent sur les offres de ses lieux voisins mises
bout à bout, un logement pris est marqué dans un masque : mêmes flottants dans le même ordre, mêmes départages.
Identique au bit : portes v8 et 27 domaines, 8/8 tests de d13, et 15 empreintes journalières identiques à 20 000
habitants. Le gain n'est PAS mesuré ici : à 20 000 et 100 000 habitants sur 8 jours, `_apparier` ne coûte presque rien
( 0,1 s en 15 jours ) ; les 75 % de la guerre des îles venaient d'un monde où beaucoup de ménages cherchent un logement.

**Où va le temps à 100 000 habitants, 27 domaines** ( cProfile, jours 6 à 8 ; hors profil 15 à 18 s par jour sur la
machine chargée ) : d15 logistique `conducteur` ~ 25 %, d14 transport ~ 19 % ( `_habitants`, `_reconcilier`,
`_km_agenda` ), puis d03 achats, d16 médecine ( `r_reseau` ), d12 recensement, d17 hôpitaux, d04 paie. d14, d15 et d17
travaillent encore par objets `Habitant` ( 5,7 millions créés en 3 jours ) : c'est le prochain chantier de vitesse.

**Les deux règles réglées après la mesure, sur 10 graines neuves** ( 101-110, critère écrit avant,
`regles_neuves.py` ) :
- campagne ( d24, C_CAMP 0,10 → 0,25 ) : porte tenue 10/10 ( e2 0,29 à 0,39, p 0,005 ) → TIENT. Mais la règle de
  campagne fait PIRE que le témoin ( rien ) sur les 10 graines : −0,196 IC95 [−0,197 ; −0,196]. À trancher.
- ravitaillement ( d26, règle revue ) : bat le témoin 10/10, +0,008 IC95 [+0,005 ; +0,011] → TIENT.

## Troisième passe ( 27/09, « fait au plus réaliste », « il faut tout enregistrer » )

**La règle de campagne n'est PAS pire que rien — ma lecture était fausse.** `regles_neuves.py` comparait un monde où
TOUTES les listes suivent la règle à un monde où AUCUNE ne fait campagne ; les parts d'intention se partagent : si tout
le monde fait campagne les gains s'annulent et les coûts restent ( d24 le disait : « les moyennes de mondes différents
ne se comparent pas » ). La bonne question est celle d'une liste seule ( `campagne_seul.py`, critère écrit avant ) :
les autres suivant la règle, la liste qui suit la règle finit 12 jours plus tard à **+3,07 points d'intention** de la
même liste forcée à « rien » ( IC95 [+2,65 ; +3,49], 60 couples graine × liste sur 60 ). Rien à corriger dans d24.
Réserve de réalisme, non corrigée faute de chiffre : les méta-analyses d'expériences de terrain ( Kalla et Broockman
2018 ) trouvent un effet de persuasion des contacts de campagne proche de zéro dans les élections générales ; `C_CAMP`
( 0,25, porté de 0,10 après la mesure ) est peut-être fort.

**L'embuscade.** Deux causes, toutes deux corrigées.
- La posture couchée n'existait pas pour la détection. Le moteur d'Arma donne à l'animation couchée une taille visible
  de 0,15 contre 0,6 accroupi et 0,9 debout ( `visibleSize`, CfgMovesMaleSdr ) ; d26 garde le 0,42 MESURÉ de l'accroupi
  et le rapport d'Arma : couché 0,105 ( ~ 58 m de jour pour un guetteur moyen, ~ 32 m de nuit ). d27 : nos éléments à
  l'arrêt se montrent dans la posture de leur conduite ( ils gardaient celle de leur dernière marche : DEBOUT après une
  occupation, accroupis après une infiltration ) ; les postes adverses gardent la posture où ils sont posés.
- La cause qui empêchait le déclenchement : l'exercice ne donnait pas l'axe de la menace, les guetteurs regardaient dans
  le sens de leur marche et TOURNAIENT LE DOS à la route de la patrouille ( 96° à 150° au plus près, 54 m ) ; seule la
  vision périphérique, trop généreuse avant la mesure d'Arma, les faisait voir passer la patrouille. La patrouille est
  « repérée » ( le code le dit ) : l'embuscade connaît son axe d'arrivée et le regarde. `test_resolveur` passe
  ( exposition exécutée = déclarée ), 32/32 tests de l'armée.

**Les détenus.** d21 les garde ABSENTS pour le moteur ( ni repas ni travail chez eux ) ; d16 les compte maintenant
PRÉSENTS en prison : ils tombent malades, la nuit dans leur cellule ( 4 détenus, surpopulation grecque de 3 à 6, à
calibrer ), le jour dans toute la prison avec les gardiens de service ( 8 h - 16 h, à calibrer ), jamais avec leur
ménage, et ne comptent plus dans la nourriture de leur ménage. Expérience dirigée ( `prison_contagion.py`, 50 000
habitants, UN détenu infecté du covid, 14 jours, même graine ) : avant, codétenus 0/48, gardiens 0/20, mais **6
personnes de la ville** contaminées directement par le prisonnier ; après, codétenus 2/48, gardiens 1/20, ville 0 —
l'épidémie circule dans la prison et en sort par un gardien. École : d21 n'incarcère que des majeurs ( 18 ans et plus ),
aucun détenu n'est d'âge scolaire ; la formation en prison n'est pas modélisée ( pas de chiffre sourcé ).

**Tout enregistrer.** La photo du soir ne prenait que les colonnes du MOTEUR ; l'état des domaines manquait ( 89
colonnes par habitant, 68 par ménage, les tables des bâtiments, de l'armée, les maladies, les intentions de vote, les
baux, les détentions, le parc… ). `photo_pays` écrit maintenant chaque soir : `pays_habitants`, `pays_menages`, chaque
table en colonnes d'un domaine, chaque dictionnaire ou liste d'objets semblables en table ( une colonne par attribut ),
`tableaux` ( chaque tableau numpy ) et `objets` ( le reste, en json ) ; le socle aussi ( créances, parc, stocks ). Porte
E6 : chaque colonne du pays et CHAQUE attribut de chaque domaine se retrouve dans l'enregistrement ; contrôle positif :
la justice oubliée à la lecture → refusée. Enregistrer ne change toujours pas le monde ( E1, séquentiel et parallèle ).

## Les échecs nouveaux de la liste ( tous antérieurs ou expliqués )

| Test | Cause |
|---|---|
| transport `test_decision` | identique, au chiffre près, sur `socle-du-pays` seule ( p 0,134 ; « marginal » au commit ffb600c, mesuré avant que la branche reçoive pays-sur-colonnes ) |
| logistique `test_faim_ile_sans_production`, hôpitaux `test_decision`, sécurité civile `test_decision`, médias `test_deformation_relais`, culture `test_rumeur_fausse` | annoncés par leurs commits ( c4693ae, f9946e3, b478e1c, 3bcb0c4, c1eaa79 ) |
| armée tactique `test_resolveur` | RÉGLÉ dans la troisième passe ( posture couchée, axe de la menace ) : retiré de la liste |

## Pour le long run

- Le coût d'une journée à 1 000 habitants monte jusqu'au jour ~ 120 ( les faits des médias s'accumulent ) puis
  plafonne ( `AGE_MAX_J` 120, `CAP_MAX` 4 096 ) : 25 jours en ~ 74 s au-delà du jour 200.
- d22 fait des produits de matrices ( faits × lieux × lieux ) : numpy y prenait tous les cœurs ( 650 % pour une île de
  1 000 habitants ), six îles en parallèle se seraient marché dessus ( 120 fils pour 20 cœurs ). `archipel.py` borne
  maintenant les fils de chaque île à sa part des cœurs ( 20 ÷ 6 = 3 ; `HMT_FILS_PAR_ILE` pour forcer ) ; le nombre de
  fils ne change pas les résultats ( porte des 27 domaines identique à 3 fils ).
- Ouvert, pour Younes : la décision d'achat de véhicule ( d14 ) trop faible pour sa porte ;
  8,5 % de militaires dans le moteur E1 contre 1,37 % en Grèce ( d25 ) ; la faim de 37-39 % de la guerre des îles
  n'est pas dans le moteur fusionné sans guerre ( 2,3 jours de faim ) : elle vient de la guerre ou de l'échelle 200.
