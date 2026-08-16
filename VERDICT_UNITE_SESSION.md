# VERDICT — L'UNITÉ DU PHÉNOMÈNE EST LA SESSION

17/08/2026, ~03 h 45. Sonde d'unité, socle **gelé** `1.13.0` (`db446bf`), régime de la nuit
(serveur neuf, réveil natif), **12 sessions × 6 tirages = 72**. Seuils écrits dans l'en-tête
du script **avant** qu'il tourne.

## Le résultat

| session | rouges T5 / 6 |
|---|---|
| 1, 2, 5, 8, 9, 12 | **6 / 6** |
| 4 | 5 / 6 |
| 6 | 4 / 6 |
| 3, 11 | 2 / 6 |
| **7, 10** | **0 / 6** |

- taux de base **p̂ = 0,681**
- variance observée des taux de session : **0,1503** — attendue sous binomiale : **0,0362**
- **surdispersion ×4,15**
- **X² = 49,77** à 11 ddl, seuil pré-écrit **19,68**

> ## ➤ L'UNITÉ EST LA SESSION. Franchi par plus du double du seuil.

La distribution est **bimodale** : six sessions à 100 %, deux à 0 %, quatre entre les deux.
Ce n'est pas un bruit qui module, c'est un état que le serveur prend **à sa naissance**.

## Ce que ça annule, rétroactivement

**Toutes mes sondes de la nuit tenaient dans une ou deux sessions.** Contre un phénomène
dont l'unité est la session, un bras à n=3 ou n=4 tirages, c'est **n=1**. ⟨Fable : *« leurs
réfutations sont des lancers de pièce »*⟩

Retournent au registre des hypothèses, **non réfutées** : le réveil (qui n'avait de toute
façon jamais été envoyé, voir `CORRECTIF_REVEIL_JAMAIS_TESTE.md`), l'échauffement, et la
lecture du 17/20 → 2/16 comme un effet de version.

**Survit** : la cadence — `nt`≈40 et `fps`≈48 **pendant les échecs**, sur des sessions
différentes. Ni le nombre d'impulsions ni le FPS ne séparent. La charge non plus : la
session à 0 rouge tournait à `load=1,88`, celle à 6 rouges à `load=2,09`, co-locataire
présent partout.

## Ce que la structure dit de la cause, sans parier

Le prévol **crée et détruit ses hommes à chaque tirage**. Si l'état est uniforme sur les six
tirages d'une session, alors **la cause vit au-dessus de l'homme** — dans ce qu'une session
n'initialise qu'**une seule fois** : init de mission, compilation, ordre de chargement des
mods, état de la machine à la naissance du serveur.

Ça ne nomme pas la cause. **Ça ampute la moitié de l'espace de recherche** ⟨Fable⟩.

## La clause de réalité est ATTEINTE — et la sortie n'est pas celle qu'on croyait

68 % de rouges : Fable avait écrit qu'à ce niveau, *« aucune option ne sauve une campagne —
134 épisodes coûteraient des centaines de serveurs »*. **C'est vrai du harnais actuel**, qui
démarre **un serveur par épisode** : ×3 en démarrages, soit ~400 lancements.

Mais la mesure dit aussi que **l'état est stable À L'INTÉRIEUR d'une session**. Donc le
harnais « un serveur par épisode » est **le pire choix possible** : il retire un tirage
neuf à chaque fois, au taux le plus défavorable.

**Conséquence de conception** : un serveur passe son contrôle, puis **porte plusieurs
épisodes**. Plafond imposé par un fait déjà déposé — le pont meurt après 20-40 min
(`pont-arma-meurt-en-service`), soit **6 épisodes de 2,5 min**. Coût : 134 ÷ 6 ≈ 23 serveurs
utiles, ×3 pour les rebuts ≈ **70 démarrages** au lieu de 400.

## RÉSERVE, et elle est éliminatoire

**Le filtre « un tirage de contrôle en tête de session » n'est PAS validé.** Les sessions à
2/6 prouvent qu'une session peut être mixte : un premier tirage vert n'y garantit pas les
suivants.

> **Avant toute campagne : mesurer P(session exploitable | 1er tirage vert).** Le calcul se
> fait sur les données existantes en relisant le rang de chaque tirage — **aucun serveur à
> démarrer**. Si cette probabilité est basse, le filtre en tête ne tient pas et il faut un
> contrôle **par épisode**, pas par session.

## Ce qui n'a pas bougé

Aucun `.npz` ouvert. Les 10 relevés de la nuit dorment et ne sont pas lisibles à 10 sur 67.
