# Le porteur n'arrive pas, et personne ne le remplace

*14 septembre 2026. Mesuré sur 159 épisodes de référence déjà au disque. Aucun épisode dépensé.*

## Le goulot, puis le goulot du goulot

La mission gagne 84 fois sur 159. Des 75 échecs, **61 sont des `CHARGES_INCOMPLETES` contre 10
`EXFIL_MANQUEE`** : l'assaut échoue six fois plus souvent que le décrochage.

Et ces 61 échecs ne sont pas répartis. Ils se concentrent sur la dernière marche :

| charges posées | épisodes | vivants médians |
|---|---|---|
| 0 sur 3 | 2 (3 %) | 5 |
| 1 sur 3 | 14 (23 %) | 6 |
| **2 sur 3** | **45 (74 %)** | **8** |

**Trois quarts des échecs d'assaut s'arrêtent à deux charges sur trois, avec huit hommes debout.**
Le délai entre l'arrivée à l'ouverture et la première charge est le même en réussite et en échec —
52 secondes dans les deux cas. L'entrée dans l'enceinte n'est pas le problème.

## Le script écrit lui-même la cause

```
PORTEUR_N_ARRIVE_PAS   x54   distance médiane 22 m  (le seuil est 12 m)
ELEMENT_N_ARRIVE_PAS   x12
AUCUN_PORTEUR_VIVANT   x 6
PLAFOND_PHASE          x 0
```

72 charges manquées, dont **54 parce qu'un seul homme n'est pas arrivé**. Seulement 6 fois parce
qu'il ne restait personne pour porter. Et `PLAFOND_PHASE` **ne se déclenche jamais** : la phase
d'assaut n'a pas une seule fois épuisé son budget. Le rang de l'objectif abandonné est le troisième
dans 45 cas sur 72 — exactement la marche entre l'échec et la réussite.

Les objectifs abandonnés sont les gros : `Land_Cargo_HQ_V1_F` 30 fois, `Land_TTowerBig_1_F` 30 fois
(emprises 9 et 8), contre `Land_Communication_F` 12 fois (emprise 2). Plus le bâtiment est large,
plus le point de pose est loin d'un endroit où un homme peut se tenir.

## Le mécanisme, lu dans le code

```sqf
private _h = if (count _demo > 0) then { _demo select 0 } else { _porteurs select 0 };
_h doMove _pt;
private _t = time;
waitUntil { sleep 1; ((_h distance2D _pt) < 5) || !(alive _h)
            || (time - _t > CHACAL_DELAI_PORTEUR * CHACAL_ECHELLE) || CHACAL_FIN };
private _dH = round (_h distance2D _pt);
if (!alive _h || { _dH > 12 }) then {
    ... cause|PORTEUR_N_ARRIVE_PAS ...
    continue                      // -> objectif suivant. UN SEUL essai, jamais de second.
};
```

**Un porteur, un essai.** S'il meurt en route ou s'il reste à plus de 12 m, l'objectif est abandonné
définitivement. Le code porte pourtant, quelques lignes plus haut, l'intention contraire :

> `// ! S1 ( 11/09 ) : la releve est ecrite d avance - DEMO_1, DEMO_2, ADJOINT, CHEF, MEDECIN - et`
> `// chaque homme de l assaut porte une charge, donc un porteur mort a toujours un suivant.`

La relève existe — mais elle ne joue qu'au prochain objectif, jamais sur celui qu'on vient de perdre.

## La preuve par le chronomètre

```
en RÉUSSITE  : 3e porteur -> 3e charge posée    = 4,0 s   (n=98 ; min 4,0 ; max 4,0)
en ÉCHEC     : 3e porteur -> ordre de dégagement = 4,0 s   (n=37 ; max 4,1 ; tous < 45 s)
```

Le `sleep (4 * CHACAL_ECHELLE)` du geste explique le 4,0 s exact des réussites. Et dans les échecs,
**l'ordre de repli tombe dans la même fenêtre de quatre secondes** où la charge aurait été posée.
La décision de partir ne vient pas d'un manque de temps : elle suit immédiatement le renoncement.

## Deux fautes, pas une

La partition des 54 cas est nette, et elle sépare deux remèdes différents :

| | n | distance médiane | temps consommé |
|---|---|---|---|
| porteur **mort** dans la fenêtre | 16 (30 %) | 16 m | 12 s — **aucun** n'épuise son délai |
| porteur **vivant mais trop loin** | 38 (70 %) | 26 m | 45 s — **38 sur 38** à bout de délai |

- Les **16 morts** demandent une **relève** : envoyer le suivant de la liste. C'est ce que le code
  dit vouloir faire, et il reste presque toujours un homme (seulement 6 `AUCUN_PORTEUR_VIVANT` sur
  tout le corpus).
- Les **38 vivants** ont consommé **exactement** les 45 secondes et se sont arrêtés à 26 m. Pour
  eux, la relève ne servirait à rien : un second homme se heurterait au même obstacle. Ce qu'il
  leur manque est du temps — ou une autre façon d'approcher. En COMBAT, l'homme avance par bonds ;
  le code le sait déjà, il l'a écrit à propos de l'exploitation.

## Ce qui est mis à l'épreuve cette nuit

`DELAI-PORTEUR-14-09` : six mondes, même protocole et même azimut imposé que le bras témoin qui
tourne en parallèle, **une seule chose change** — `delai_porteur` passe de 45 à 180 s. Plan apparié,
bras entrelacés dans le temps, 12 épisodes par monde et par bras.

*180 et non 150* : `description.ext` déclare `values[] = {45,60,90,120,180}`, et 180 en est le
maximum — donc le choix le plus puissant, quoi qu'il en soit de la suite.

> ⚠️ **Affirmation retirée, 15/09.** J'avais écrit ici qu'une valeur hors liste retombe
> *silencieusement au défaut*, et j'en avais fait la raison du choix de 180. **Je n'en ai aucune
> preuve.** L'audit du 15/09 soutient l'inverse : aucun étage ne validerait la valeur — ni le
> moteur, ni `controle_avant_run.sh` qui ne lit jamais `description.ext`, ni `lancer.sh`. Balayage
> du disque : **aucun job n'a jamais demandé de valeur hors liste**, donc la mesure ne peut pas
> trancher sur l'existant. Un job de quatre minutes (`GARDE-VALUES-15-09`, `delai_porteur = 150`,
> `geometrie=1`, cinq graines vierges) est en file pour lire ce que la mission joue réellement.
> **TRANCHÉ le 15/09 à 05h46.** Le job a tourné. Le lanceur a écrit
> `CHACAL_DELAI_PORTEUR = 150` dans `server.cfg`, et la ligne `FINI` des épisodes porte
> `|delai_porteur|150` — lecteur `ACCEPTE`. **`values[]` n'est PAS une garde : la valeur hors
> liste est jouée telle quelle.** Mon affirmation était fausse, l'audit avait raison.
>
> La conséquence dépasse mon erreur : **rien dans la chaîne n'arrête une faute de frappe dans un
> job.** Ni le moteur, qui rend la valeur de `server.cfg` verbatim ; ni `controle_avant_run.sh`,
> qui ne lit jamais `description.ext` ; ni `lancer.sh`. Un `delai_porteur: 1500` au lieu de 150
> serait joué sans un mot. Le remède — comparer les valeurs d'un job aux listes déclarées, en
> AVERTISSEMENT et non en refus — est préparé et sera posé avec les autres correctifs, machine
> au repos.
>
> Le choix de 180 pour la campagne reste bon : c'est le maximum déclaré, donc le plus puissant.
> 150 aurait marché aussi. Seule la raison que j'en avais donnée était fausse. Le choix de 180 reste bon dans les deux
> cas ; seule la raison que j'en avais donnée était sans fondement.
>
> Voir `audit-banc-neuf-fautes-sur-vingt-quatre`.

**Prédiction enregistrée d'avance.** Si le temps est la contrainte, les 38 cas à bout de délai se
convertissent en grande partie, et le taux de charges complètes — 98 sur 159, soit 62 % — monte
nettement. **Falsificateur** : si l'écart apparié reste sous 8 points, le porteur est *cloué* et non
*lent*, et le remède doit viser son comportement d'approche, pas la durée.

**Limite assumée.** À `arret=5` la phase 6 n'est pas jouée : on mesure le bénéfice d'un homme exposé
plus longtemps sans en mesurer le coût au décrochage. Si le levier gagne, il faudra le remesurer à
`arret=6` avant de l'écrire dans le socle.

## Ce que cela dit de la suite

Le verdict `le-script-ne-choisit-pas-son-ouverture` établissait que rien de connu avant l'assaut ne
prédit son issue à l'intérieur d'un monde. Celui-ci dit pourquoi ce n'était pas une impasse mais un
indice : **la variance ne venait pas de la décision, elle venait d'un renoncement**. Un homme sur
trois n'arrive pas, et le script tourne les talons plutôt que d'en envoyer un autre.

C'est le plus gros levier mesuré du projet — et ce n'est pas un problème d'apprentissage, c'est une
réparation de script. Il faut la faire *avant* de mesurer quoi que ce soit d'autre sur l'assaut :
tant qu'elle tient, toute couture de décision est mesurée à travers un plancher qui s'effondre.

*Voir aussi : `le-script-ne-choisit-pas-son-ouverture`, `un-levier-ecrit-nest-pas-un-levier-lu`,
`phase3-porte-hors-datteinte`, `cinq-arrets-derivation-placeur`.*
