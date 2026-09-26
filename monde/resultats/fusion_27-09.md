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

## Les échecs nouveaux de la liste ( tous antérieurs ou expliqués )

| Test | Cause |
|---|---|
| transport `test_decision` | identique, au chiffre près, sur `socle-du-pays` seule ( p 0,134 ; « marginal » au commit ffb600c, mesuré avant que la branche reçoive pays-sur-colonnes ) |
| logistique `test_faim_ile_sans_production`, hôpitaux `test_decision`, sécurité civile `test_decision`, médias `test_deformation_relais`, culture `test_rumeur_fausse` | annoncés par leurs commits ( c4693ae, f9946e3, b478e1c, 3bcb0c4, c1eaa79 ) |
| armée tactique `test_resolveur` | conséquence de la détection d'Arma : l'EMBUSCADE ne se déclenche plus de jour. Le modèle n'a pas de posture « couché » : les tireurs couchés comptent comme accroupis, et la patrouille les voit à 550 × 0,42 = 231 m, avant la zone de destruction. Arma n'a mesuré l'accroupi que de nuit. **À trancher** : une posture couchée mesurée dans Arma, ou le couvert de l'embuscade |

## Pour le long run

- Le coût d'une journée à 1 000 habitants monte jusqu'au jour ~ 120 ( les faits des médias s'accumulent ) puis
  plafonne ( `AGE_MAX_J` 120, `CAP_MAX` 4 096 ) : 25 jours en ~ 74 s au-delà du jour 200.
- d22 fait des produits de matrices ( faits × lieux × lieux ) : numpy y prenait tous les cœurs ( 650 % pour une île de
  1 000 habitants ), six îles en parallèle se seraient marché dessus ( 120 fils pour 20 cœurs ). `archipel.py` borne
  maintenant les fils de chaque île à sa part des cœurs ( 20 ÷ 6 = 3 ; `HMT_FILS_PAR_ILE` pour forcer ) ; le nombre de
  fils ne change pas les résultats ( porte des 27 domaines identique à 3 fils ).
- Ouvert, pour Younes : l'embuscade ( ci-dessus ) ; la décision d'achat de véhicule ( d14 ) trop faible pour sa porte ;
  8,5 % de militaires dans le moteur E1 contre 1,37 % en Grèce ( d25 ) ; la faim de 37-39 % de la guerre des îles
  n'est pas dans le moteur fusionné sans guerre ( 2,3 jours de faim ) : elle vient de la guerre ou de l'échelle 200.
