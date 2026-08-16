# Dépôt — LA NUIT ARMÉE : l'ordre du gymnase tient-il sur Arma ? Critères AVANT

Déposé le 16/08/2026, geste 2 du plan de Fable, **avant que le moindre épisode NATIF ou
FLANC armé ne soit joué**.

> ⟨Fable⟩ *« La question n'est plus "pourquoi 15 points ?" mais **"l'ORDRE tient-il ?"** Si
> la nuit armée reproduit ce classement sur Arma, le tarif absolu est un détail. Si l'ordre
> casse, aucune chirurgie de couvert ne t'aurait sauvé. »*

## QUELLE DÉCISION CETTE MESURE FAIT BASCULER

**Si l'ordre tient** → le gymnase classe comme Arma classe, il **regagne le droit
d'entraîner**, et le chantier devient la qualité de ce qu'il enseigne (le couvert mal typé),
pas sa validité.

**Si l'ordre casse** → le gymnase ne peut plus servir de gymnase en l'état, et aucune
chirurgie de couvert n'aurait suffi. C'est alors l'architecture entière qui se rejuge.

Aucune autre mesure ne fait basculer cette décision.

## Le classement de référence — le gymnase, 6 graines held-out × 256 environnements

| bras | gymnase |
|---|---|
| FRONTAL | **12,8 %** |
| FLANC | **34,3 %** |
| SCRIPT (feu-et-mouvement alterné) | **46,1 %** |
| POLITIQUE apprise | **51,1 %** |

## Les bras d'Arma, tous ARMÉS et sous PRÉVOL

- **POLITIQUE** — en cours, 67 épisodes sous socle 1.3.0 ;
- **FLANC** — 67 épisodes, doctrine portée telle quelle de `boucle.py`, **même corps** ;
- **NATIF** — 67 épisodes, l'IA d'Arma seule, aucun `disableAI`, waypoint SAD.
  **Hors concordance** : il n'a pas d'équivalent au gymnase et sert d'étalon absolu.
- **SCRIPT** — 67 épisodes si la nuit le permet ; sinon reporté et **déclaré manquant**.

Tous partagent : site (4644, 5652), 4 contre 4, 170 m, `combatMode RED`, arme en main
vérifiée par le prévol, mêmes graines d'azimut.

## LA PORTE — l'ordre, pas les niveaux

**ZÉRO inversion de signe** entre les paires ordonnées du gymnase et celles d'Arma, sur les
trois bras communs (FLANC, SCRIPT, POLITIQUE). Tolérance d'amplitude **×3**, tolérance de
signe **NULLE** ⟨Fable, 15/08⟩.

| inversions | lecture |
|---|---|
| **0** | le gymnase CLASSE comme Arma. Il regagne le droit d'entraîner. |
| **≥ 1** | classement inversé **au niveau politique**. Le gymnase ne peut pas entraîner en l'état. |

Si SCRIPT manque, la lecture se fait sur la **seule paire** FLANC/POLITIQUE et **le dit** —
une paire n'est pas un classement, et le verdict sera nommé « partiel ».

## CONTRÔLES POSITIFS ⟨règle 16⟩

1. **le prévol vert** avant chaque épisode — c'est désormais mécanique ;
2. **scène confirmée par le jeu** : `def=4 att=4 enmain=4` ;
3. **azimuts distincts** : écart-type > 60° ;
4. **le bras NATIF doit BOUGER** — plus d'un mètre par pas. Un natif immobile mesurerait un
   point de passage, pas l'IA d'Arma. *Cette porte a déjà sauvé un verdict le 15/08.*
5. **le bras FLANC doit émettre au moins 3 actions distinctes** — sinon la doctrine n'est
   pas exécutée.

## Ce qui ferait échouer

- moins de 50 épisodes valides sur 67 dans un bras → ce bras ne se lit pas ;
- un contrôle positif en défaut → ce bras ne se lit pas ;
- **un prévol rouge sur plus de 20 % des épisodes** → l'instrument est instable et **rien**
  ne se lit. *T4 s'est déjà montré intermittent : la fenêtre de 6 s est marginale.*

## Ce qui n'est PAS promis

Que l'ordre tienne. Et une réserve qui pèse : **`ANOMALIE_AUTOCOMBAT.md`** — si l'IA d'Arma
choisit ses cibles en parallèle de la politique, les trois bras pilotés mesurent un
**attelage**, et l'ordre qu'on lira sera celui des attelages, pas des cerveaux. Le verdict
le dira.
