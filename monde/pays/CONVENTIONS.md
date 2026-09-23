# Conventions des domaines du pays

Ce fichier est la loi commune des 27 domaines. Le domaine 1 (`d01_population.py`, `tests_d01_population.py`) en est
l'exemple complet : le lire avant d'écrire.

## 1. Le projet en une page

- Un moteur de monde en Python (`monde/`, dit « moteur E1 ») fait vivre un pays : habitants (`population.Habitant`),
  ménages (`population.Menage`), entreprises, marchés, convois, gouvernement (`economie.py`, `monde.py`,
  `gouvernement.py`). Un pas = 10 minutes ; une journée du monde = 144 pas ; les routines tombent à heure fixe
  (`Monde.pas_suivant`). Le moteur est tenu par Younes, EN PARALLÈLE : **on ne modifie jamais `monde/*.py`**.
- Le **socle** (`monde/socle/`) : grand livre (`comptes.GrandLivre` : `transferer`, `recevoir_de_l_exterieur`,
  `payer_l_exterieur`, `emettre`, `detruire_monnaie`, et pour les biens `deplacer`, `produire`, `importer`,
  `consommer`, `bruler`, `perimer`, `perdre`, `detruire`, `exporter`), créances (`Creances`), registre des détenteurs
  et conservation (`registre.py`), biens fongibles (`biens.Catalogue`, `biens.Stock` creux), objets durables
  (`objets.Parc` : `Modele`, individus, cohortes), échéancier, hasard par domaine, calendrier (fériés grecs, soleil),
  journal borné, protocole de décision (`decision.PointDeDecision`, `Decideur`). Lire chaque module du socle.
- Le **pays** (`monde/pays/pays.py`) pose les domaines sur un Monde E1 : routines à heure fixe, échéances, colonnes
  par habitant et par ménage, décideurs, clôture du jour. Lire sa docstring : c'est l'API d'un domaine.

## 2. Ce qu'un domaine livre

Deux fichiers, et **seulement** ces deux-là :

- `monde/pays/dNN_<nom>.py` : une docstring FICHE en 8 points (classes ; invariants et ce que le domaine détient ;
  points de décision ; événements ; liens avec les autres domaines ; portes ; correspondance Arma ; coût à
  l'échelle), puis les classes, les fonctions de routine, et `installer(p)` qui rend l'état du domaine.
- `monde/pays/tests_dNN_<nom>.py` : `TESTS = [...]`, des fonctions sans argument qui rendent `(ok, message)`.

## 3. Les règles du moteur (non négociables)

1. **Conservation exacte.** Tout argent passe par `p.socle.livre` avec un **motif déclaré** (`declarer_motif(nom,
   nature, domaine)`, natures SCN de `comptes.NATURES`). Tout bien d'un `Stock` du socle passe par le grand livre.
   Les stocks du moteur E1 (dictionnaires `stocks`, `garde_manger`, `publics`) peuvent être modifiés directement
   SEULEMENT pour un déplacement entre deux détenteurs inscrits ; une création ou une destruction met à jour
   `p.socle.livre.flux[nature][bien]` (natures : produit, importe, consomme, brule, perime, perdu, detruit,
   exporte). Toute nouvelle classe qui détient de l'argent ou des biens est **inscrite** au registre
   (`p.socle.registre.inscrire(...)`, fonctions de module, jamais de lambda, classe Python unique par famille
   d'argent). La porte commune (`essais.porte_commune`) doit passer.
2. **Échelle.** `__slots__` partout. Jamais de boucle sur la population dans une boucle sur la population. Un champ
   que TOUS les habitants (ou ménages) portent va dans `p.colonnes["habitant"|"menage"]` (numpy, indexé par
   identifiant). Un champ que peu portent va dans une table éparse (dict par identifiant). Tirer le hasard **par
   vecteur** (`p.du_jour(dom).random(n)` : 6 ns par tirage) plutôt qu'à l'unité (2,4 µs). Cohortes et stocks quand
   l'individu n'est pas nécessaire. Pas d'héritage profond : des données simples, portables en Rust.
3. **L'état n'est pas la décision.** Au moins un point de décision par domaine (`D.PointDeDecision`) : règle de base
   déterministe ; `observer()` ne rend que des traits bornés dans [0 ; 1], chacun avec sa source, jamais la vérité
   cachée ni l'avenir ; actions discrètes ; note et horizon (3 jours par défaut, autre valeur justifiée) ; témoin
   bête. Le décideur s'obtient par `p.decideur(POINT)` ; son mode vient de `p.modes` (regle par défaut).
4. **Déterminisme.** Tout le hasard par `p.hasard(dom)` ou `p.du_jour(dom)` (noms de flux propres au domaine :
   `"<nom>_<usage>"`). Attention : `p.du_jour(x)` rend le MÊME flux à chaque appel du même jour ; prendre un nom
   distinct par usage. Jamais `random`, jamais `np.random` global, jamais `hash()`.
5. **Incarnation.** Tout ce qui peut avoir un corps (personne, véhicule, arme, bâtiment) porte un classname Arma 3
   (`Modele.arma` ; jeu de base, Apex, Contact, Malden, CUP Terrains/Units/Vehicles/Weapons). `arma_preuve = None`
   tant que personne ne l'a vu vivre en jeu : ne jamais inventer une preuve. Leçons payées : un agent ne bouge
   qu'avec une destination posée AVANT l'ordre de marche ; deux véhicules créés au même point se détruisent ; le van
   `C_Van_01_box_F` (Apex) naissait mort.
6. **Mesurabilité.** Chaque domaine arrive avec ses portes : un test chiffré qui peut échouer, son **contrôle
   positif** (l'instrument voit un effet qu'on a mis exprès), son **falsificateur** (une erreur posée à la main est
   vue). Les seuils s'écrivent AVANT la première mesure. Si une porte échoue : corriger un BOGUE, jamais desserrer un
   seuil ; si l'échec vient du modèle ou du moteur E1, le laisser échouer et l'expliquer (voir `test_recensement`).
   Un test qui passe pour une mauvaise raison est pire qu'un échec : vérifier que chaque contrôle voit bien ce
   qu'il prétend voir (leçon du socle : un falsificateur passait sur un instantané intact).
7. **Style.** Python 3.12, identifiants en français sans accents, docstrings en français **sans accents ni
   apostrophes** dans le code (comme le moteur), qui disent le POURQUOI ; unités explicites (drachmes, unités,
   heures, km, jours) ; bornes vérifiées dans les constructeurs (`ValueError`).
8. **Réalisme.** Ordres de grandeur réels (Grèce prise pour modèle : drachme, Égée ; médecine, prix, consommations,
   balistique), avec leur source, ou « a calibrer » quand c'est une hypothèse. Aucune simplification de confort ;
   aucun attribut qui ne serve pas une décision, une mesure ou la conservation.

## 4. Les leçons déjà payées, à respecter dans chaque point de décision

- Une note doit dépendre du choix de l'agent : noter l'effet de CE choix sur ceux qu'il touche (ni la moyenne
  nationale, ni le seul profit). Porte obligatoire : dans un scénario où la décision compte, en mode `hasard`,
  `decideur.part_du_choix() >= 0.01`.
- La conséquence se lit sur plusieurs jours (horizon), jamais le soir même.
- Le prix dit la faim trop tard, et pas du tout pour les pauvres : jamais un prix comme seul signal d'un besoin.
- Un témoin bête peut battre une règle savante : chaque point en déclare un.
- Le coût d'un monde incarné est le mouvement simultané : étaler les départs (`Habitant.decalage`).

## 5. Le pays et le moteur E1

- Installer : `essais.monde([nom], graine, echelle, modes)` rend `(w, p)`. `essais.jours(w, n)` fait vivre n jours.
- Un domaine qui reprend une part du moteur la **neutralise par une donnée** (ex. `Entreprise.activite = 0` pour les
  fermes après la règle de l'aube) plutôt qu'en remplaçant une méthode que d'autres utilisent. Remplacer une
  méthode du moteur (`w.<methode> = ObjetAppelable(p)`, un objet picklable à `__slots__`, comme
  `d01.RemplaceDemographie`) n'est permis qu'au domaine propriétaire de cette méthode :

  | méthode du moteur | propriétaire |
  |---|---|
  | demographie | population |
  | deplacer | agenda |
  | paie, embaucher | travail |
  | achats, repas, regler_activite, ajuster_prix (marchés) | economie |
  | contagion, progression_maladie, soigner | medecine (soigner : hopitaux s'il est là) |
  | gouverner, sitrep | etat |
  | importer, exporter_or, commerce_exterieur | exterieur |
  | produire (fermes) | agriculture ; (mines, carrières, fonderies) industrie ; (puits, raffinerie, centrale) energie |
  | expedier, lancer_convoi, arrivees | logistique |
  | patrouilles, ravitailler_bases | armee |

  Un domaine qui a besoin d'une autre méthode le dit dans son rapport au lieu de la remplacer.
- **Reprendre des entreprises du moteur** (fermes, mines, centrales...) : `p.reprendre(e, "<nom>")`. Le moteur n'y
  produit plus (activité remise à 0 à 6 h 10, après la règle de l'aube) ; le domaine produit lui-même, met à jour
  `livre.flux` pour ce qu'il crée ou consomme, et crédite `Habitant.heures_jour` des heures réellement travaillées
  pour que la paie du moteur (ou du domaine travail) les paie. `p.repris` dit qui fait vivre quoi.
- Morts : TOUTE mort passe par `d01_population.deceder(p, h, cause)` (causes : `d01.CAUSES`, en ajouter se discute).
  Nouveaux ménages : `d01.nouveau_menage`. Changer un habitant de ménage : `d01.deplacer_membre`.

## 6. Qui déclare quoi

Un bien, un modèle, un motif, un type d'événement, une colonne, un type d'échéance n'est déclaré que par UN domaine :
celui qui le produit ou le possède. Les autres le lisent par son nom et ont ce domaine en dépendance.

- Biens déjà au catalogue (moteur E1) : nourriture, fer, zinc, or, petrole, carburant (gazole), electricite, outils,
  remedes.
- agriculture : céréales, légumes, fruits, olives, huile, lait, viande, poisson, fourrage, semences, bois.
- industrie : cuivre, charbon, calcaire, acier, ciment, chimie, engrais, plastique, pieces (mécaniques), verre ;
  modèles de machines.
- energie : gaz, essence, kerosene, fioul (le pétrole brut, le gazole et l'électricité existent déjà).
- services_publics : eau_potable, dechets.
- medecine : les molécules et produits de santé (antibiotique, antalgique, insuline, antiviral, vaccin,
  anesthesique, sang, oxygene...), rattachés ou non à `remedes`.
- immobilier : modèles de bâtiments. transport : modèles de véhicules civils, pneus, pièces auto.
  logistique : navires, avions. securite_civile : engins de secours. hopitaux : équipements médicaux, ambulances.
- armee : munitions par calibre, explosifs, rations de combat ; modèles d'armes, d'optiques, de véhicules militaires,
  de radios, de protections.

## 7. Comment travailler (station de travail)

- Le code vit sur la station (`ssh ws`), dans la copie de travail **`/mnt/data/hmt/depot-socle`** (branche
  `socle-du-pays`). Écrire ses deux fichiers dans son dossier de brouillon, puis :
  `COPYFILE_DISABLE=1 tar czf <nom>.tgz -C <brouillon> <deux fichiers>` ; `scp -q <nom>.tgz ws:C:/hmt/tmp/<nom>.tgz` ;
  extraire dans `/mnt/data/hmt/depot-socle/monde/pays/`.
- `ssh ws` atterrit dans PowerShell, qui interprète `$`, les guillemets et les parenthèses : **toujours** écrire un
  script bash local et le passer par l'entrée standard : `ssh ws 'wsl -e bash -s' < script.sh`.
- Python : `/mnt/data/hmt/depot/.venv/bin/python` (3.12, numpy). Portes :
  `cd /mnt/data/hmt/depot-socle && timeout 1800 /mnt/data/hmt/depot/.venv/bin/python -m monde.pays.tests <nom>`.
- **Ne jamais** : committer (Claude principal committe après relecture), toucher un autre fichier que ses deux
  fichiers, lancer Arma, modifier `monde/*.py`, `monde/socle/*`, `pays.py`, `essais.py`, `tests.py`. Un besoin
  dans ces fichiers se décrit dans le rapport final.
- D'autres agents travaillent en même temps sur d'autres domaines, dans le même dossier : n'extraire que ses
  propres fichiers.

## 8. Le rapport final (pour Claude principal)

Les deux fichiers ; les lignes exactes de la sortie des portes ; ce que le domaine EXPOSE aux domaines suivants
(fonctions, colonnes, biens, motifs, états) ; ce qu'il remplace ou neutralise du moteur ; les hypothèses « a
calibrer » ; les portes qui échouent et pourquoi ; ce qu'il faudrait changer ailleurs.
