# PROTOCOLE DE L'AIGUILLE — geste n°1, avant d'ouvrir le journal

*8 août 2026, 22 h 15. **Écrit avant la première lecture des bras.** C'est la condition qui
rend le regard innocent.*

⟨Fable, 08/08⟩ *« Vérifier l'instrument n'est pas lire le verdict, à condition que la lecture
ne puisse déclencher QUE des gestes pré-écrits. »*

## Pourquoi on regarde maintenant

La panne silencieuse du 235ᵉ accrochage — la fuite de groupes — a couru une nuit entière avant
d'être vue. **On ne l'attend plus poliment.** L'aiguille se vérifie tôt, mais sous contrainte.

## Ce qu'on lit, et rien d'autre

**Le taux d'arrivée par bras** : part des accrochages où au moins un axe franchit le rayon de
tenue (`HMT|G|ARR`), calculée séparément sur le bras professeur (`LIEU|*|*|1`) et le bras
témoin (`LIEU|*|*|0`).

On ne lit **ni l'écart entre les bras, ni sa significativité, ni le classement des couloirs**.
Ce sont deux nombres, et ils ne servent qu'à répondre à une question : *l'instrument
peut-il bouger ?*

## Les deux seules réactions permises — déposées maintenant

| ce que dit l'aiguille | ce qu'on fait, et rien d'autre |
|---|---|
| **les deux bras dans la bande 20-80 %** | **on ne touche à rien.** Le run continue tel quel jusqu'à son effectif. Aucun paramètre n'est modifié, aucun couloir écarté. |
| **un bras ou les deux au butoir** (< 20 % ou > 80 %) | **on répare les paramètres du monde et on recommence à zéro.** Les accrochages déjà tombés sont archivés comme partiels et ne comptent pas. |

Il n'existe pas de troisième réaction. En particulier : on ne réglera pas la difficulté « un
peu » pour rapprocher l'aiguille du milieu, et on ne gardera pas les accrochages d'avant une
réparation.

## Ce qui est corrigé par la même occasion, et qui ne dépend pas de cette lecture

- **La porte passe de 5 à 10 points.** Le dépôt distinguait dès l'origine : **10 points pour
  certifier un LIEU**, 5 pour juger un AGENT. Le serveur 1 est la PORTE 0 des lieux — elle se
  lit à 10. Un couloir qui ne sépare qu'à 5 ferait un tribunal mou. La taille était écrite ;
  je l'avais mal appliquée, et je la remets sans attendre aucun résultat.
- **La grandeur jugée est l'ARRIVÉE**, pas la tenue. Vérifié sur pièces : `HMT|G|ARR` porte le
  premier franchissement du rayon de tenue par groupe — la grandeur du dépôt est bien dans les
  journaux. La tenue reste relevée, en second, et ne décide pas.

## Empreinte du monde

Absente des 89 premiers accrochages. Elle est calculée et journalisée à partir de maintenant,
à chaque démarrage de serveur, sans exception.

**Ce que ça coûte, dit franchement** : les accrochages antérieurs n'ont pas d'empreinte. Ils
restent utilisables parce que les deux bras vivent dans **la même session**, tirés à pile ou
face accrochage par accrochage — la contemporanéité est structurellement sauve, ce n'est pas
une supposition. Mais ils ne pourront jamais être comparés à un run d'une autre session.
