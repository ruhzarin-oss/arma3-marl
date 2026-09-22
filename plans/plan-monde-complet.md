# Plan — un monde complet dans Arma, où l'on apprend et l'on forme (22/09/2026)

*Vision de Younes, dictée le 22/09 entre 16 h 30 et 17 h ; plan rédigé à sa demande (« rédige le plan complet »).
Rien n'est construit ni lancé avant sa validation. Les choix de conception qui lui reviennent sont en section 9.*

## 1. La vision, dans ses mots

- « Construire un monde complet dans Arma : une vraie vie civile, une économie, avec une armée. »
- « Une économie, des rôles et des classes, des règles. »
- « Des échéances, un cycle de jour et de nuit, des maladies et des remèdes. »
- « De la production : les minerais, fer, zinc, or, et le pétrole pour le déplacement des véhicules. »
- « Un gouvernement pour diriger et coordonner le tout. »
- « Sur un seul serveur ultra complet, où l'on branche un réseau de neurones, puis un LLM, où Claude se branche en MCP,
  plus des agents qui apprennent. »
- « On ne va plus entraîner : on va apprendre et former. »

## 2. Pourquoi ce monde

Aujourd'hui, dans CHACAL, le temps ne coûte rien. L'avis de Fable du 22/09 le chiffre : attendre est gratuit, donc la
meilleure règle est une constante (« toujours attendre »), et aucune règle intelligente ne peut gagner plus de 1 à
3 points. Le 17/09, les six choix de la mission étaient tous indifférents ou dominés.

Un monde vivant donne au temps un prix naturel. Attendre, c'est laisser passer un convoi, laisser le jour se lever,
laisser une épidémie s'étendre, laisser le carburant manquer. Les choix redeviennent des choix, et la mission CHACAL se
jouera à l'intérieur de ce monde.

## 3. L'architecture, en cinq couches

**Couche 0 — Arma, le terrain et les corps.** Le serveur Arma porte l'île, le jour et la nuit, la météo, la physique,
les véhicules et leur carburant (déjà natif), et les unités incarnées. Tout ce qui se voit et se combat vit ici.

**Couche 1 — Le cœur du monde, l'état du pays.** Chaque habitant, chaque stock, chaque prix, chaque malade, chaque loi est
une donnée. Le cœur fait avancer le pays pas à pas sur l'horloge du monde : production, transport, marché, contagion,
décisions du gouvernement. Ce n'est pas un moteur de jeu : c'est une simulation de données, comme l'économie d'Antistasi,
mais tenue hors de l'ordonnanceur d'Arma (voir la section 7).

**Couche 2 — La bulle.** Seuls les habitants proches de l'action deviennent de vraies unités Arma : autour du
détachement, d'un convoi, d'un événement. Quand l'action s'éloigne, ils redeviennent des données. Un habitant garde
toujours son identité, son rôle, son inventaire, sa santé, qu'il soit incarné ou non.

**Couche 3 — Les cerveaux.**
- **Le réseau de neurones** : les réflexes et la perception, à chaque instant, pour les unités incarnées.
- **Le LLM** : le raisonnement lent. Le gouvernement, les chefs, les décisions qui se prennent en heures du monde, par
  des actions typées et bornées (jamais du code libre injecté dans le monde).
- **Claude en MCP** : observer le monde, interroger, instruire, conduire des expériences. C'est le labo MCP Arma, déjà
  construit (projet Plane `MCP`, étapes MCP-3 à MCP-8), qui reste à brancher.
- **Les agents qui apprennent** : ils vivent dans le monde, dans leur rôle.

**Couche 4 — La formation.** On n'entraîne plus : on apprend et on forme. Le cycle est celui d'une formation militaire :
1. **Instruction** : la doctrine du rôle, donnée par un formateur (le LLM, ou Claude en MCP).
2. **Exercice** : une vraie situation, dans le monde qui continue.
3. **Débrief (RETEX)** : ce qui s'est passé, pourquoi, ce qu'il fallait faire.
4. **Correction** : la mémoire de l'agent change ; ce qui vaut pour tous devient doctrine commune.
5. **Qualification** : une épreuve du rôle, sur des situations jamais vues, qui dit si l'agent sait.

Le monde ne se remet jamais à zéro. Chaque agent garde sa mémoire. Une expérience compte, même vécue une seule fois.

## 4. Le contenu du monde

| domaine | ce qu'il contient | ce qui le relie au reste |
|---|---|---|
| **Population** | des habitants avec domicile, travail, horaires, besoins (nourriture, santé, revenu) | l'économie les emploie, la maladie les frappe, la loi les contraint |
| **Rôles et classes** | civils (paysan, mineur, ouvrier de raffinerie, convoyeur, marchand, médecin, policier), militaires (soldat, sous-officier, officier), gouvernement | chaque rôle a ses droits, ses devoirs, sa formation, sa qualification |
| **Production** | mines (fer, zinc, or), pétrole et raffinerie, agriculture, pharmacie | chaque production consomme du travail, de l'énergie, des intrants |
| **Carburant** | le pétrole raffiné devient du carburant ; sans lui aucun véhicule ne roule, civil ou militaire | la logistique de l'armée dépend de l'économie |
| **Échanges** | transport par convoi sur les routes, marchés, prix, monnaie, salaires, impôts | une route coupée devient une pénurie qui se propage |
| **Maladies et remèdes** | contagion par contact, gravité, guérison ou mort ; remèdes rares, produits, transportés, distribués | une échéance médicale manquée coûte des vies |
| **Échéances** | récoltes, livraisons, paie, relèves de garde, couvre-feu, fenêtre d'exfiltration | le temps a un prix pour chacun |
| **Jour et nuit** | cycle natif d'Arma, horloge du monde accélérable | routines, visibilité, sécurité changent avec l'heure |
| **Armée** | garnisons, patrouilles, réserve (les briques de CHACAL), logistique, commandement | vit du carburant et des vivres de l'économie |
| **Gouvernement** | budget, impôts, allocations (où vont les remèdes, où vont les troupes), lois | dirige et coordonne tout, joué par le LLM |
| **Règles** | qui va où, quand, avec quoi ; ce qui arrive quand une règle est enfreinte | la police et l'armée les font appliquer |

## 5. Les étapes, chacune avec sa porte écrite d'avance

| étape | ce qu'on fait | porte (ce qui prouve que ça marche) | falsificateur (ce qui prouve que c'est cassé) |
|---|---|---|---|
| **E0 — Décisions** | les réponses de Younes à la section 9 ; avis de Fable s'il le demande | le périmètre de la v1 est écrit et signé | — |
| **E1 — Le cœur, sans Arma** | données, horloge, une ressource, une production, un transport, un marché, 200 habitants avec rôles et horaires | conservation exacte des stocks ; couper la seule route crée une pénurie mesurée (contrôle positif) ; sans perturbation, les prix restent stables (contrôle négatif) | un stock qui apparaît ou disparaît sans cause |
| **E2 — Le pont et la bulle** | le cœur relié à Arma ; un village incarné puis désincarné autour d'un détachement | un habitant incarné puis rendu retrouve exactement son état ; pouls de l'ordonnanceur ≥ 95 % dans la bande | une identité perdue, un doublon, un pouls qui décroche |
| **E3 — Le temps** | horloge du monde accélérée ; le cœur bat sur la date du monde, le combat en temps réel | une journée du monde en temps prévu (×120 : 12 min) ; routines jour/nuit visibles dans Arma | le cœur qui suit le temps de mission (le piège d'Antistasi) |
| **E4 — L'armée et le carburant** | garnisons ravitaillées par convoi ; véhicules qui consomment | un convoi coupé vide les réservoirs de la garnison dans le délai calculé | des véhicules qui roulent sans carburant |
| **E5 — Maladies, remèdes, échéances** | contagion, pharmacie, distribution, échéances | une épidémie sans remède suit la courbe attendue ; un remède livré à temps la plie | une contagion sans contact |
| **E6 — Le gouvernement (LLM)** | décisions toutes les heures du monde, par actions typées, journalisées (consigne figée, empreinte) | un choix absurde est refusé par les règles ; un budget n'est jamais dépassé | une action hors du catalogue qui passe |
| **E7 — Le réseau de neurones** | réflexes et perception des unités incarnées | ses décisions restent dans les bornes du rôle, ses sorties sont journalisées | un réflexe qui lit la vérité du monde (comme l'Architecte : perception seule) |
| **E8 — Claude en MCP** | brancher le labo MCP Arma sur le serveur du monde | observer, interroger, instruire, sans jamais toucher à une mesure en cours (MCP = labo, job = mesure) | une commande MCP qui modifie une expérience |
| **E9 — La première formation** | un rôle, un cycle complet : instruction, exercice, débrief, correction, qualification | l'agent formé réussit sa qualification sur des situations jamais vues mieux que l'agent non formé, écart écrit d'avance | une qualification réussie par un agent au hasard |
| **E10 — CHACAL dans le monde** | la mission jouée dans le monde vivant, avec une vraie échéance | les choix de la mission cessent d'être indifférents : au moins un choix dépend de la situation | les six choix restent indifférents ou dominés |

## 6. La rigueur dans un monde qui ne se remet jamais à zéro

- **Des instantanés.** L'état complet du monde est sauvegardé à intervalles réguliers. Un plantage de la station ne perd
  pas le pays.
- **Des jumeaux.** Pour comparer deux choix, on copie le monde depuis un instantané et on joue les deux branches. Le monde
  principal continue ; les jumeaux servent à mesurer.
- **Des épreuves gelées.** Les qualifications portent sur des situations mises de côté, jamais vues en formation.
- **Pré-enregistrement et regard unique**, comme partout dans le projet.
- **Tout est journalisé** : chaque décision du LLM (consigne, empreinte), chaque sortie du réseau, chaque intervention de
  Claude.

## 7. Les contraintes déjà mesurées

- **L'ordonnanceur SQF d'Arma a un budget fixe de 3 ms par image** (mesuré le 22/09 sur le banc multiple). Une population
  entière en SQF le saturerait. D'où le cœur hors d'Arma et la bulle.
- **Quelques centaines d'unités actives par serveur** au plus (314 unités mesurées à 29 images/s, 22/09).
- **Le temps de mission ne s'accélère pas sur serveur dédié**, seule l'horloge du monde s'accélère (Antistasi, 10/08).
- **Le pont vers Arma sous Windows passe par fichier** : 0,5 s par échange. C'est assez pour le cœur (un battement par
  minute du monde) et pour le LLM ; c'est trop pour des réflexes image par image, qui restent donc dans Arma. Le pont TCP
  rapide n'existe que sous Linux.
- **Un seul serveur, un seul fil de temps.** C'est voulu : on apprend dans la continuité ; les jumeaux servent à mesurer.
- **Les tirages du moteur ne sont pas semés** : deux jumeaux divergent. Les comparaisons se font donc sur plusieurs paires
  de jumeaux, jamais sur une seule.
- **Le 07/07, Younes a arrêté les moteurs maison.** Ce plan reste dans Arma : le cœur est une simulation de données, pas un
  moteur. À confirmer par Younes.

## 8. Ce qui existe déjà et sert

- La mission CHACAL (garnison, patrouilles, réserve, détachement, perception mesurée), son enregistreur et son lecteur.
- La boucle de l'Oracle (imagination, pièges, motifs) et l'Architecte (règles lisibles, perception seule).
- Le banc multiple : plusieurs rencontres indépendantes par serveur, pouls, journal croisé, témoins.
- Le labo MCP Arma (construit, non branché) et le pont Windows.
- Les expériences ALiVE (BORÉE sur Stratis, MELTEMI sur Altis) et les leçons d'Antistasi (horloge, débit).
- LAMBS pour les réactions au contact.

## 9. Les décisions qui reviennent à Younes

1. **L'île** : Altis (tous nos mondes y sont) ou une autre ?
2. **La taille** : combien d'habitants simulés, combien incarnés au plus à la fois ?
3. **La v1** : quels domaines d'abord ? Proposition à trancher : population, une ressource, carburant, jour et nuit,
   armée, gouvernement ; maladies et minerais ensuite.
4. **L'économie** : monnaie ou troc, prix fixés ou de marché, impôts ?
5. **Le gouvernement** : ses objectifs, ce qu'il a le droit de décider, et face à quoi (paix, insurrection, guerre) ?
6. **L'armée** : de quel camp, contre qui, et quel est le rôle du détachement CHACAL dans ce monde ?
7. **Qui apprend d'abord** : quel rôle suit la première formation ?
8. **La qualification** : qu'est-ce qu'un agent « formé » dans ce rôle ?
9. **L'horloge** : quelle accélération du monde (×12, ×60, ×120) ?
10. **Fable** : faut-il lui soumettre ce plan avant la construction ?

## 10. Décisions de Younes (22/09, 17 h 15) et interprétation retenue

- Île : **Altis**. Taille : **500 habitants** pour commencer.
- **Tout dans la première version** : économie réelle, **vrai gouvernement**, armée, maladies et remèdes, minerais, pétrole,
  échéances, jour et nuit.
- **Aucun ennemi pour l'instant** : l'armée vit en temps de paix (garde, patrouilles, logistique).
- **Un agent qui va à l'école et apprend son monde** : l'élève (enfant de Kavala), formé par le cycle instruction →
  exercice → débrief → observation → qualification.
- **Cycle complet de 6 heures** : interprété comme une journée entière du monde en 6 heures réelles (accélération ×4).
  À confirmer par Younes.

## 11. État au 22/09 soir — étape E1 (le cœur, hors Arma) construite

Paquet `monde/` du dépôt : `config`, `carte` (127 lieux d'Altis extraits de la configuration du jeu), `population`
(500 habitants, 366 ménages, rôles, classes, horaires), `economie` (entreprises, 3 marchés régionaux, convois, réseau
électrique), `gouvernement` (catalogue d'actions bornées ; cerveau par règles ou Qwen 14B par Ollama), `ecole`
(enseignant tiré du monde réel, élèves témoin / mémoire / Qwen avec mémoire bge-m3), `monde` (le pas de 10 minutes),
`tests`, `lancer`. **Portes E1 : 7/7** — conservation exacte de l'argent et des biens (et le contrôle la voit échouer),
contrôle négatif (30 jours sans famine, carburant dans la bande), contrôle positif (Pyrgos coupée : nourriture ×23,
100 % des ménages à court), reproductibilité, gouvernement borné (6/6), école (mémoire 0,62 contre témoin 0,00).
Tenue sur 120 jours : 499 vivants, carburant 5-8, caisse de l'État stable. Défauts connus : la mine n'est pas rentable
(salaires), la nourriture reste au prix plancher (surproduction agricole), l'élève à mémoire simple régresse à 0,25 quand
ses notes s'accumulent (plancher que l'élève Qwen doit battre).

## 12. État au 22/09, 20 h — étape E2 (le pont et la bulle) en service

**Le pont est en Rust** (`depot/pont_rust`, extension `monde_x64.dll`, arma-rs) : le cerveau Python est le serveur TCP,
l'extension est le client et se reconnecte seule. Les ordres sont **poussés** dans la mission par `ExtensionCallback`,
sans attente et sans fichier — le pont par fichier de Windows coûtait 0,5 s par échange.

**Mesures du premier vol** (bulle Kavala, serveur instance 9, mission `MONDE.Altis`) :

| ce qui est mesuré | résultat |
|---|---|
| horloge | 901 s réelles = 60,1 min du monde, soit **×4,00** : une journée du monde en 6 h réelles |
| corps | 49 puis 68 corps dans Arma = habitants incarnés par le cerveau, **0 doublon**, 0 écart |
| pont | 0 message perdu, 0 erreur SQF, ~1 s pour incarner 49 habitants |
| serveur | ~28 images/s avec 49 à 68 corps |
| reconnexion | cerveau relancé : le pont se reconnecte seul, 19 corps orphelins purgés par réconciliation |

**Deux défauts trouvés et corrigés** :

1. **La bulle comparait des villes.** Les 49 habitants de Kavala y vivent *et* y travaillent : aucun changement de lieu,
   donc aucun déplacement. Chaque habitant porte désormais un **poste** explicite (maison, travail, hôpital), posé par
   le cœur ; un changement de poste devient un ordre `aller`. Les 7 portes d'E1 restent vertes.
2. **`moveTo` seul ne déplace pas un agent d'Arma.** Contrôle positif à quatre méthodes (`monde/essai_aller.py`,
   3 corps chacune, 90 s) : agent + `moveTo` = **0,0 m** ; agent + `setDestination` puis `moveTo` = 226-265 m ;
   unité en groupe + `doMove` = 97-120 m ; groupe + `move` = 83-130 m. La mission pose maintenant une destination avant
   `moveTo`. Les civils restent des agents : un groupe par habitant heurterait la limite de 288 groupes par camp.
   Après correction : 8 ordres `aller` à 7 h 10, **4 corps en marche** mesurés.

**Porte E2** — identité conservée, aucun doublon, pouls tenu : franchie sur la bulle de Kavala. Reste à tenir un cycle
complet de 24 h du monde (6 h réelles) avec Qwen au gouvernement et à l'école, cycle lancé le 22/09 à 20 h 10.
