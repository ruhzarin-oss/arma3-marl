# BRANCHER L'ARC — amendement déposé avant l'entraînement

*11 août 2026. On ajoute **deux entrées** à la politique. C'est un amendement, il s'écrit.*

## POURQUOI, ET CE QUE ÇA N'EST PAS

La politique a perdu **12,3 points** contre une doctrine de flanc écrite à la main. Le flanc ne
paie que pour une raison mesurée : le défenseur a un **arc de tir**, et le contourner achète un
**sursis de 4 secondes** — le cône ne pivote pas, il s'ouvre. Certifié : **18 repérages sur 18
dans le cône contre 0 sur 26 hors.**

Or **aucune des onze entrées ne porte cette information**. L'agent ne peut donc pas *représenter*
la raison pour laquelle le flanc marche ; il ne peut que la retrouver par hasard, et la
récompense ne l'y guide pas.

> **Ce n'est pas un réglage de récompense.** C'est une **perception certifiée** qu'on lui rend :
> `agent-percoit-pas-manoeuvre`, mesurée en juillet — donner l'arc fait chuter son exposition de
> **28 %**, et il contourne à 132 m quand le bon crochet se fait à 184.

## ⚠️ CE QUE JE DOIS RECONNAÎTRE

**Je l'ajoute après avoir vu la porte tomber.** L'honnêteté exige de le dire : si l'agent passe
maintenant, on ne saura pas distinguer « l'arc était la pièce manquante » de « j'ai cherché
jusqu'à ce que ça marche ». **Une seule tentative de plus est donc autorisée sur cet axe.** Si
elle échoue, on ne rajoute pas une douzième idée : c'est l'algorithme ou le banc qui se redépose.

## CE QUI NE BOUGE PAS

- **La récompense** : `1,0 × prise + 0,001 × mètre gagné`, signée, sans terme d'exposition.
- **La porte** : battre les DEUX doctrines sur graines jamais vues, lecture **sur la borne**,
  contrôle nul, garde-fou anti-planque. **Aucun seuil assoupli.**
- **Les deux doctrines de référence** gardent leurs chiffres : frontal 20,4 %, flanc 42,3 %.

## CE QUI CHANGE

Deux entrées, en position 9 et 10 : **sinus et cosinus de l'angle entre la face du défenseur le
plus proche et la direction sous laquelle il me voit.** 0 = il me regarde en face ; ±π = je suis
dans son dos. L'observation passe de 11 à 13.

Et **la couture Arma les produit aussi** — `getDir` sur l'ennemi le plus proche, une ligne de
SQF — pour que la politique reste transportable. Elles sont ajoutées **en fin** des 18 colonnes,
donc aucun indice existant ne bouge.

## CE QUI FERAIT ÉCHOUER — écrit avant

- **La porte ne passe toujours pas** → l'arc n'était pas la pièce manquante, et on arrête de
  meubler la perception. On redépose l'algorithme ou le banc.
- **Elle passe mais l'agent gagne moins de mètres que la meilleure doctrine** → il a appris à se
  planquer derrière l'angle mort au lieu d'entrer. Le garde-fou tombe, et le verdict avec.
