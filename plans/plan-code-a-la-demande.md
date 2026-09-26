# Qwen dans le moteur : du code à la demande ( plan du 26/09/2026 )

Décision de Younes : Qwen ( Qwen3.8-27B, local ) répond à toutes les demandes du moteur et code n'importe quelle
situation à la demande ; Younes et Claude restent au-dessus pour lui donner de nouvelles capacités.

## Le principe

Une partie du monde qui rencontre une situation sans règle ( ou qui veut mieux que sa règle ) **demande une
fonction** au service de code : elle décrit la situation, donne un exemple d'entrée et dit ce qu'il faut rendre.
Qwen écrit la fonction ; le service la vérifie ; si elle est bonne, elle entre dans la **bibliothèque** et sert
sans rappeler Qwen. Tant qu'elle n'est pas prête, le monde continue avec sa règle : **jamais bloqué sur le LLM**.

## Les pièces

1. **Le contrat** ( ce que la demande dit ) : une clé ( `decision/importer`, `gouvernement/Malden`, ... ), une
   description, un exemple d'entrée, la forme de la sortie, un **valideur** ( la sortie est-elle permise ? ),
   et la **note** qui dira si la fonction est meilleure que la règle.
2. **Le service** ( un processus à part, une file ) : prend les demandes, appelle Qwen, extrait le code, le passe au
   bac à sable ( celui de l'agent codeur : pas d'import, pas de fichier, pas de dunder, une seconde par appel ),
   l'essaie sur des entrées réelles ( sorties valides ? ), et le range en **candidat**.
3. **L'épreuve dans le monde** : un candidat n'est jamais adopté sur parole.
   - Pour un point de décision du socle : il reçoit **une part des agents** ( 10 % ), les autres gardent la règle ;
     le socle note déjà chaque choix à son horizon. Adopté si sa note moyenne bat celle de la règle, testée par
     permutation ( la machinerie existe : `part_du_choix`, `p_permutation` ). Sinon, retiré, et la raison chiffrée
     retourne à Qwen pour la version suivante.
   - Pour un gouvernement : examen hors ligne sur des mondes neufs ( `examen_agent`, déjà prouvé ), puis adoption.
4. **La bibliothèque** : sur disque, versionnée ( code, contrat, mesures, qui l'a remplacée et pourquoi ). La
   matrice enregistre quelle version décidait à chaque pas : une nuit se relit et se rejoue.
5. **Au-dessus** ( Younes et Claude ) : nouveaux contrats ( nouvelles capacités ), nouveaux leviers ( actions du
   catalogue ), nouvelles portes ; lecture de ce que Qwen a écrit et de ce qui a marché.

## Les garde-fous

- Le code ne touche que sa sortie : aucune écriture dans le monde hors des actions validées ( comme `appliquer` ).
- Conservation de l'argent et des biens vérifiée chaque jour ( elle l'est déjà ) ; une version qui la romprait est
  retirée et signalée.
- Déterminisme : l'arrivée d'une réponse de Qwen change le monde à un pas qui dépend du temps de calcul ; la matrice
  garde le pas et la version, et un **mode rejeu** charge la bibliothèque telle qu'elle était pour refaire la nuit.

## Les étapes

1. Le service et la bibliothèque, le contrat d'un point de décision ( `importer` d'abord : 7 biens, 3 décisions par
   jour et par négociant, une note à 5 jours ) ; porte : un candidat faux est refusé, un candidat bon est adopté,
   la règle continue tant que Qwen n'a pas répondu ( contrôle : Ollama coupé ).
2. Tous les points de décision du socle ( 14 ), puis le parlement des gouvernements ( une loi par mois du monde ).
3. Les situations sans règle : un domaine qui rencontre un cas inconnu ( événement, bien nouveau ) écrit une demande
   au lieu de lever une erreur.
