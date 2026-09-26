# PLAN DE L'ARCHIPEL — six pays autonomes, un monde branché en temps réel

*Écrit le 24/09 à partir des décisions de Younes et de mesures faites le même jour. Aucune ligne de code n'est écrite
avant que ce plan soit validé. Toutes les portes sont fixées ici, AVANT toute mesure.*

---

## 0. Ce qu'on veut, dans les mots de Younes

- « Une île représente un pays avec des ressources différentes. »
- « Chaque île a son armée, ses hôpitaux, ses propres systèmes. »
- « Le but, c'est que chaque île vive de manière autonome et soit responsable de sa propre survie et de sa sécurité. »
- « Je veux une liaison directe entre toutes les îles, je veux qu'elles soient connectées. »
- « Si je me connecte à un serveur Tanoa, je veux pouvoir voir débarquer des gars d'Altis ou de Malden en temps réel. »
- « Exactement comme dans le réel. »
- « On passe en temps réel seulement si je suis sur le serveur ; sinon, ça va beaucoup plus vite. »
- « Tu crées une carte d'identité et un passeport pour chaque individu. »
- Une monnaie par île ; une population proportionnelle à la taille de l'île.

**En une phrase** : six pays qui vivent en même temps, chacun seul responsable de sa survie, reliés par la mer ; les
gens, les marchandises et l'argent passent d'un pays à l'autre comme dans le réel, et le monde ralentit à l'heure
réelle dès qu'un humain y entre.

---

## 1. Où on en est vraiment (mesures du 24/09)

### 1.1 Le moteur et le pays
- Le moteur en colonnes et les 14 domaines livrés tournent ensemble à **un million d'habitants** : 57 à 79 s par
  journée, 41 à 60 millions de décisions par heure, argent conservé. Mais **tout sur Altis seule**.
- Un monde peut déjà contenir plusieurs îles, mais avec **un seul État**, une seule monnaie, un seul gouvernement.
- Le 22/09, Younes avait proposé un cerveau par île ; la position tenue était « un seul cerveau », avec cette phrase :
  *« Une île deviendra un cerveau le jour où elle sera un pays à part. »* **Ce jour est arrivé** : le plan ci-dessous
  est le passage à six cerveaux.

### 1.2 Aucune île sauf Altis ne peut exister seule
Créer un monde sur n'importe quelle autre île plante immédiatement : la capitale du gouvernement est écrite en dur
(`carte.py : CAPITALE_GOUVERNEMENT = "Kavala"`). Autres noms d'Altis codés en dur : l'épidémie part de Pyrgos
(`monde.py`), l'élève vit à Kavala (`population.py`), le port d'Altis est nommé, le climat et le calendrier du soleil
ne connaissent qu'Altis et Stratis, l'agriculture ne suit le calendrier de l'Égée que sur trois îles.

### 1.3 Les îles n'ont pas de quoi être des pays

| île | lieux | étendue | capitales | villages / villes | usines, énergie, mines | bases militaires | port |
|---|---|---|---|---|---|---|---|
| Altis | 68 | 24 × 16 km | Kavala, Athira, Pyrgos | 27 / 18 | 3 centrales, 3 carrières, 2 fonderies, 1 raffinerie, 1 puits, 1 pharmacie, 1 mine | 6 | 1 (+ 1 dépôt) |
| Tanoa | 60 | 14 × 12 km | Georgetown | 45 / 14 | **aucune** | **aucune** | trouvé seul |
| Sahrani (Sara) | 41 | 16 × 13 km | Paraiso, Bagango | 29 / 10 | **aucune** | **aucune** | trouvé seul |
| Livonia (Enoch) | 28 | 11 × 11 km | **aucune** | 23 / 5 | **aucune** | **aucune** | trouvé seul |
| Malden | 17 | 7 × 9 km | La Trinité | 13 / 3 | **aucune** | **aucune** | trouvé seul |
| Stratis | 8 | 4 × 3 km | Agia Marina | 5 / 2 | **aucune** | **aucune** | trouvé seul |

Les lieux des cinq autres îles ont été récoltés le 22/09 à partir des NOMS de la carte (villes et villages) : on n'a
jamais cherché leurs usines, leurs centrales, leurs zones militaires, leurs aéroports. **Sans cet inventaire, ces
îles n'ont ni armée, ni industrie, ni énergie, ni pharmacie** : elles ne peuvent être ni autonomes ni responsables de
leur sécurité.

Distances en mer entre capitales : 130 à 146 km (un archipel virtuel ; Livonia n'a pas de position en mer faute de
capitale). À 25 km/h, une traversée dure **5 h 15 à 6 h**.

---

## 2. Les principes, qui ne se discuteront plus ensuite

1. **Une île = un pays = un cerveau.** Chaque île est un monde complet, dans son propre processus : sa population, ses
   ressources, ses 14 domaines (et les suivants), son État, sa banque centrale et sa monnaie, son armée, ses hôpitaux.
2. **Une seule vérité par personne.** À tout instant, chaque personne est dans exactement un endroit : une île, ou la
   mer. Jamais deux, jamais zéro. C'est la leçon des doublons du 22/09.
3. **Rien ne se téléporte.** Une personne, une cargaison ou une nouvelle qui passe d'une île à l'autre prend le temps
   que ça prend dans le réel. L'information (radio, téléphone, prix affichés) passe dans la minute ; les corps et les
   marchandises prennent le temps de la mer.
4. **L'argent ne traverse jamais la mer.** Chaque monnaie n'existe que dans son île. Entre îles, on échange des
   créances entre banques centrales (des réserves), comme dans le réel.
5. **Chaque île décide seule** de ce qui la concerne : qui entre, à quel taux elle change sa monnaie, ce qu'elle vend,
   ce qu'elle achète, comment elle se défend. Ces choix sont des points de décision de son État, donc des agents.
6. **Le monde ne s'arrête jamais.** Qu'un humain regarde ou non, le temps passe, les bateaux naviguent, les gens
   vivent. Un humain connecté ne change que la VITESSE, jamais les règles.
7. **Le même monde, quelle que soit la machine.** Le résultat ne dépend ni du nombre de cœurs, ni de l'ordre
   d'arrivée des messages, ni d'une panne suivie d'une reprise.

---

## 3. L'architecture

### 3.1 Sept processus
- **Six îles.** Chacune est un monde en colonnes (le moteur actuel) avec ses domaines, qui avance pas à pas.
- **Le pont.** Un septième processus, léger, qui tient :
  - l'**horloge maîtresse** de l'archipel ;
  - la **mer** : tout ce qui est en traversée (personnes, cargaisons, courrier), avec son heure d'arrivée ;
  - le **registre d'identité de l'archipel** : quel numéro existe, où est chaque corps ;
  - la **chambre de compensation** entre banques centrales : qui doit quoi à qui, dans quelle monnaie ;
  - le **journal du pont** : tout ce qui a traversé, rejouable.

Le pont ne décide rien à la place d'une île. Il transporte, il date, il compte.

### 3.2 L'horloge : deux vitesses, une seule règle
- Toutes les îles avancent **au même pas de 10 minutes**, ensemble. À la fin de chaque pas, chaque île remet au pont
  son courrier sortant (départs, commandes, paiements, messages), et reçoit ce qui arrive chez elle pendant le pas
  suivant.
- **Vitesse rapide** (personne n'est connecté) : le pas suivant démarre dès que les six îles ont fini. L'île la plus
  lente fixe le rythme.
- **Temps réel** (au moins un humain sur un serveur Arma, quelle que soit l'île) : un pas de 10 minutes dure 10 minutes
  d'horloge murale, **pour tout l'archipel**. Les îles sont au même instant ; elles ralentissent donc toutes ensemble.
- Le passage d'une vitesse à l'autre se fait **à la frontière d'un pas**, jamais au milieu. Le pont apprend la
  présence d'un humain par les serveurs Arma (liste des joueurs).
- **À l'intérieur d'un pas**, les événements ont une minute précise : un bateau qui accoste à 14 h 37 accoste à 14 h 37,
  pas à 14 h 40. Le moteur calcule par pas de 10 minutes ; les échéances, elles, sont datées à la minute, et Arma les
  joue à la minute.
- Marge mesurée : un pas d'une île d'un million d'habitants coûte ~0,4 s de calcul pour 600 s de temps réel.

### 3.3 Déterminisme et reprise
- Chaque île a son propre hasard (graine de l'archipel + nom de l'île).
- Le courrier est toujours traité dans le même ordre : (pas, île d'origine, numéro d'ordre du message).
- **Instantané de l'archipel** : les six îles et le pont, sauvés au même pas. Une panne (processus mort, station
  tombée — piège payé le 20/09) : l'archipel s'arrête (tout le monde attend le même pas) et reprend du dernier instantané.
- Le journal du pont permet de **rejouer** une île seule avec exactement le courrier qu'elle a reçu : c'est l'outil de
  débogage principal.

### 3.4 Arma : on n'incarne que ce qu'on regarde
- Chaque île a son serveur Arma possible (les six cartes sont installées ; Sahrani demande CUP Terrains, déjà présent).
- **Un serveur Arma ne tourne que pour l'île où un humain veut aller.** Les autres îles vivent dans le moteur seul.
  Six serveurs Arma en permanence coûteraient la station ; six cerveaux, non.
- Quand un bateau approche d'une île incarnée, le pont prévient son serveur : le bateau apparaît au large, fait son
  approche, accoste, et ses passagers descendent sur le quai comme des corps. C'est ce que Younes veut voir à Tanoa.
- Déjà mesuré : 765 corps par serveur à 29 images/s ; le coût est le mouvement simultané (d'où le décalage personnel).

---

## 4. Les personnes

### 4.1 Le numéro de l'archipel
- Chaque personne reçoit à la naissance un **numéro unique dans tout l'archipel** : l'île qui l'a vu naître et un
  compteur local, dans un seul entier. Il n'est **jamais réutilisé**, même après la mort.
- Dans chaque île, les colonnes restent indexées par un numéro local (c'est ce qui rend le moteur rapide) ; une table
  de correspondance relie numéro local et numéro de l'archipel.

### 4.2 État civil et corps
Chaque personne a deux réalités :
- **son état civil** : nationalité, famille, compte en banque, impôts, droits, casier. Il est tenu par son île de
  nationalité ;
- **son corps** : là où elle est physiquement. C'est lui qui mange, travaille, tombe malade, peut être arrêté, meurt.
  Il est simulé par l'île où il se trouve.

### 4.3 Les situations d'une personne

| situation | corps | état civil | exemple |
|---|---|---|---|
| résident | son île | son île | la plupart des gens |
| en mer | le pont | son île | un passager entre Altis et Tanoa |
| visiteur | île d'accueil | son île | un marchand d'Altis trois jours à Tanoa |
| résident étranger | île d'accueil | son île, avec un titre de séjour | un ouvrier de Malden qui travaille à Altis |
| naturalisé | île d'accueil | île d'accueil | après des années, il change de nationalité |
| militaire déployé *(plus tard)* | île d'accueil ou mer | son île | une unité en mission |
| détenu *(plus tard)* | prison de l'île d'accueil | son île | un contrebandier arrêté |

### 4.4 Traverser : le protocole
1. **Décision.** La personne (ou son ménage, son employeur, son État) décide de partir : un point de décision, avec
   un motif (commerce, travail, famille, fuite de la faim, tourisme).
2. **Papiers.** Il faut un passeport valide ; pour certaines îles, un visa demandé à l'avance.
3. **Billet.** Une place sur un bateau qui part de son port, payée dans sa monnaie.
4. **Embarquement.** Son corps quitte la table de son île au pas du départ. L'île garde une trace (« absent, en mer
   vers Tanoa »). Le pont prend **toute sa ligne** : les colonnes du moteur et les colonnes que chaque domaine déclare
   *voyageuses* (santé, âge, qualifications, bagage), mais pas celles qui restent à la maison (compte, bail, emploi).
5. **Traversée.** 5 à 6 h. Le corps est dans le pont, en mer. Une maladie peut évoluer ; un naufrage, plus tard.
6. **Douane.** À l'arrivée, l'île d'accueil contrôle les papiers, la santé (quarantaine possible) et les bagages.
   Refus possible : le bateau repart avec lui.
7. **Débarquement.** Son corps entre dans la table de l'île d'accueil, avec un numéro local neuf, relié à son numéro
   d'archipel. Il change sa monnaie au port.
8. **Retour ou installation.** Un visiteur repart à la date prévue ; un résident étranger renouvelle son titre ;
   un immigré déplace son ménage.

### 4.5 La famille qui reste
- Un membre absent reste membre de son ménage, mais **ne mange pas à la maison** et ne compte pas dans sa faim.
- Un ménage qui émigre ensemble traverse ensemble (un « groupe »).
- Un mineur ne traverse jamais seul sans adulte (règle déjà tenue par le domaine population).

### 4.6 Les papiers
- **Carte d'identité** : numéro d'archipel, nationalité, date de naissance, sexe, domicile, photo (le visage du corps
  Arma). Délivrée à la naissance ou à la naturalisation.
- **Passeport** : numéro, île émettrice, date de délivrance, date d'expiration. Demandé à son État, avec un coût et un
  délai.
- **Visa, titre de séjour** : délivrés par l'île d'accueil, selon SA politique.
- **Faux papiers** *(plus tard)* : un marché noir, lié à la contrebande du domaine 7.
- Tout cela en **colonnes** (numéros, dates, codes), jamais en objets.

### 4.7 Le contrat que chaque domaine devra signer
Un domaine qui tient quelque chose sur une personne doit dire ce qui se passe quand elle part :
- **ce qui voyage avec elle** (ses colonnes voyageuses) ;
- **ce qui l'attend chez elle** (son compte, son bail, son emploi, sa pension) ;
- **ce qui casse** (un locataire qui émigre rompt son bail ; un emprunteur qui fuit fait défaut ; un fonctionnaire
  absent n'est pas payé).

C'est le point le plus dur du plan : aujourd'hui, les 14 domaines supposent qu'une personne ne quitte jamais son pays.

---

## 5. L'argent

- **Une monnaie par île**, créée uniquement par sa banque centrale (le domaine banques en tient déjà une).
- **L'argent ne traverse pas.** Quand Tanoa achète du carburant à Altis :
  1. l'importateur de Tanoa paie en monnaie de Tanoa à sa banque centrale ;
  2. la banque centrale de Tanoa doit la somme à celle d'Altis (écrit au pont, dans la chambre de compensation) ;
  3. la banque centrale d'Altis paie l'exportateur en monnaie d'Altis.
  Les réserves de change des deux banques bougent ; aucune drachme ne quitte son île.
- **Le taux de change** vient de la balance des paiements (le domaine 7 la tient déjà, au centime) : il flotte, ou
  l'État le fixe. C'est une décision d'État.
- **Un voyageur** change son argent au port : bureau de change, taux du jour, commission.
- **Conservation, monnaie par monnaie** : dans chaque île, l'argent ne se crée que par sa banque centrale ; au pont,
  la somme des créances entre banques centrales se compense exactement.
- Le « taux de conversion commun » actuel (`EUROS_PAR_DRACHME = 1,15`, une seule monnaie) devient un taux PAR ÎLE.

---

## 6. Les marchandises et la mer

- **Des bateaux** : capacité, vitesse, coût, équipage (des habitants avec un métier : marins), port d'attache.
- **Des ports** : un par île au départ (trouvé seul le 22/09) ; capacité de quai, entrepôts, douane.
- **Un manifeste** pour chaque traversée : les passagers et la cargaison, déclarés à la douane de départ et d'arrivée.
- La **contrebande** existe déjà (domaine 7, un réseau par île) ; entre îles, elle devient une traversée non déclarée.
- Les **maladies** voyagent avec les voyageurs : la médecine compte déjà les infections importées.
- Le **reste du monde** (prix mondiaux en euros) : à décider — voir § 11.
- Les domaines transport (14) et logistique (15) ne sont pas livrés : le pont aura un transport **minimal** (un
  armateur par île, des lignes régulières), que ces domaines remplaceront.

---

## 7. La sécurité et la souveraineté

- **Chaque armée défend son île**, et seulement son île, pour commencer.
- **La frontière, c'est la douane** : chaque île choisit sa politique d'entrée (ouverte, sélective, fermée) ; fermer
  en cas d'épidémie est un vrai choix, avec un vrai coût (plus de commerce).
- **Le blocus** : refuser tous les bateaux d'une île.
- **L'invasion** *(protocole à part, plus tard)* : un groupe armé qui traverse, refusé par la douane, combattu par
  l'armée locale. C'est le même pont : des corps qui traversent. Le protocole de traversée doit donc accepter des
  **groupes** dès le début, même s'ils ne sont pas armés.
- **L'espionnage** *(plus tard)* : un visiteur qui observe et rapporte.
- **Question ouverte** : Sahrani a deux capitales. Dans son histoire (Arma), c'est une île coupée en deux pays rivaux,
  le Nord et le Sud. Un seul pays, ou deux ?

---

## 8. Donner à chaque île de quoi être un pays

C'est le **premier vrai chantier**, avant tout pont : aujourd'hui, cinq îles n'ont ni armée, ni industrie, ni énergie.

1. **Inventaire réel des cartes.** Pour chaque île, demander au serveur Arma ce que sa carte contient vraiment : zones
   militaires, aéroports, usines, centrales, lignes électriques, carrières, champs, ports, hôpitaux, par les classes
   de bâtiments et les noms de la carte (la méthode « la carte se raconte elle-même » du 22/09). **Il faut allumer les
   serveurs Arma pour ça : c'est à Younes de donner le feu vert** (décision du 23/09 : Arma éteint).
2. **Une identité économique par île**, tirée de sa carte, pas inventée : ce qu'elle produit bien, ce qui lui manque.
   Les îles n'auront pas les mêmes forces, et c'est ce qui les obligera à échanger.
3. **Un siège de gouvernement par île** (Livonia n'a pas de capitale : il faut en désigner une, sur sa carte).
4. **Retirer d'abord tout ce qui est propre à Altis** du moteur et des domaines (§ 1.2), puis faire passer à CHAQUE île
   seule toutes les portes du pays.
5. **La population, proportionnelle** : sur le nombre de lieux habitables au départ (tableau § 1.3 : Tanoa 60, Altis
   48, Sahrani 41, Livonia 28, Malden 16, Stratis 7), avec un contrôle : la capacité nourricière de l'île. Une île qui
   démarre au-dessus de ce qu'elle peut nourrir doit importer ou souffrir, et c'est voulu.

---

## 9. Les portes, fixées maintenant

Chaque porte a un contrôle positif : on vérifie qu'elle sait échouer avant de la croire (règle 16).

| porte | ce qu'elle exige | contrôle positif |
|---|---|---|
| **G1 île seule** | chacune des six îles tourne seule 30 jours avec tous les domaines ; toutes les portes du pays passent sur chaque île ; argent et biens conservés | une île privée de sa capitale doit échouer à l'installation |
| **G2 isolement** | l'archipel, pont FERMÉ, donne six îles identiques au bit aux six îles simulées seules | un seul message injecté doit faire échouer la porte |
| **G3 déterminisme** | parallèle = séquentiel au bit ; deux passages identiques ; panne + reprise = sans panne | inverser l'ordre de deux messages d'un même pas doit changer le résultat |
| **G4 conservation** | par monnaie : argent créé seulement par sa banque centrale ; créances du pont compensées au centime ; biens conservés, mer comprise ; personnes : vivants = somme des îles + en mer ; aucun numéro en double ni disparu | un corps dupliqué ; un milliardième de monnaie créé sans cause |
| **G5 traversée** | une personne partie d'A à t arrive à B à t + distance/vitesse (à la minute) ; sa ligne arrive intacte (hors lieu et situation) ; refusée, elle revient | une ligne altérée en mer doit être vue |
| **G6 temps réel** | un humain connecté → un pas dure 600 s ± 1 s pour tout l'archipel ; déconnecté → retour à la vitesse rapide au pas suivant ; un bateau accosté dans le moteur apparaît sur le quai d'Arma dans la minute | horloge faussée de 10 % : doit être vue |
| **G7 autonomie** | chaque île sous blocus 30 jours : on mesure sa faim, sa mortalité, son énergie ; les attentes par île sont écrites AVANT, à partir de ses ressources | — (porte de mesure, pas de réussite) |
| **G8 coût** | un pas de l'archipel ≤ temps de l'île la plus lente + 10 % ; mémoire totale sous 40 Go | — |

---

## 10. L'ordre de marche

Chaque phase finit par ses portes et par un point d'arrêt où Younes décide de la suite.

| phase | contenu | dépend de | fini quand |
|---|---|---|---|
| **A. Carte des pays** | inventaire réel des six cartes par Arma ; identité économique ; sièges de gouvernement ; population de départ | **feu vert Arma** | chaque île a de quoi avoir une armée, une énergie, une économie |
| **B. Une île = un pays** | retirer Altis du code ; chaque île tourne seule avec les 14 domaines ; monnaie propre | A | **G1** sur les six îles |
| **C. Identité** | numéro d'archipel, carte d'identité, passeport, en colonnes ; délivrance par l'État | B | portes d'identité (unicité, pas de réutilisation) |
| **D. Le pont fermé** | sept processus, horloge maîtresse, instantané et reprise, pont sans échanges | B | **G2**, **G3** |
| **E. Traverser** | contrat « voyageur » des domaines ; embarquement, mer, douane, débarquement ; ménages absents | C, D | **G5**, **G4** (personnes) |
| **F. Commercer** | chambre de compensation, change, négociants entre îles, bateaux de marchandises | E | **G4** (monnaies, biens) |
| **G. Temps réel et Arma** | deux vitesses ; présence humaine ; bateaux et débarquements dans Arma | E | **G6** |
| **H. Vivre** | archipel complet, proportionnel, 30 jours ; blocus île par île | F, G | **G7**, **G8** |
| *plus tard* | visas, naturalisation, faux papiers, invasion, espionnage, Sahrani en deux pays | H | protocoles à part |

**L'autre conversation** (les domaines) doit suivre deux règles de plus dès maintenant : rien de propre à Altis ; tout
prix dans la monnaie de son île. Et chaque nouveau domaine déclare ses colonnes voyageuses (§ 4.7).

---

## 11. Les décisions qui restent à Younes

1. **Feu vert Arma** pour la phase A (inventaire des cartes) : les serveurs sont éteints depuis le 23/09.
2. **Le reste du monde** : l'archipel reste-t-il ouvert sur le monde (euros, prix mondiaux, aide de l'Union), ou
   fermé sur lui-même ? Fermé = chaque île ne peut compter que sur les cinq autres.
3. **Le change** : taux flottant (marché) ou fixé par chaque État (décision d'agent) ?
4. **Visiteurs et immigrés** : chaque île décide-t-elle seule qui entre, dès le début ?
5. **Sahrani** : un pays ou deux (Nord et Sud, comme dans son histoire) ?
6. **La population** : sur les lieux habitables (proposé), ou autre base ? Et quelle taille totale (Altis à un million
   et les autres en proportion ≈ 4 millions au total ; ou un total fixé) ?

---

## 12. Les risques, dits franchement

- **Le contrat voyageur** (§ 4.7) touche les 14 domaines : chacun suppose aujourd'hui qu'une personne ne part jamais.
  C'est le plus gros chantier caché du plan.
- **Les cartes pauvres** : si une carte n'a vraiment ni usine ni base, il faudra en décider (poser des sites plausibles
  sur des bâtiments réels, ou accepter une île dépendante). À décider île par île, jamais inventé en silence.
- **Le temps réel avec Arma** : le moteur avance par pas de 10 minutes ; Arma vit à la seconde. L'accostage « à la
  minute » demande que les échéances de la mer soient datées à la minute et jouées par Arma ; à vérifier tôt (G6).
- **La mémoire** : quatre millions d'habitants ≈ 16 Go aujourd'hui, et le journal du moteur grandit sans limite
  (3,9 Go en 3 jours pour un million) : à borner avant la phase H.
- **La station** : six cerveaux + un ou deux serveurs Arma tiennent sur 12 cœurs ; six serveurs Arma en permanence, non.
- **La reprise** : une station tombée arrête tout l'archipel (leçon du 20/09) ; la reprise automatique fait partie de D.
