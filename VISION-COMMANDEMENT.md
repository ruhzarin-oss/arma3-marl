# HARMATTAN — Vision du Commandement Terrestre
## Questionnaire de cadrage du livrable principal

> **But** : capter ta vision *précise* d'un **commandement de l'armée de terre** où un **officier commande des escouades tactiquement opérables** dans Arma 3.
> **Mode d'emploi** : pour chaque section → le *pourquoi*, des questions numérotées, et *ma supposition par défaut* en italique. Tu réponds dans le fil (ou tu annotes). Réponds vite : « A1 oui / A2 plutôt X / défaut OK »… ça suffit.

---

### A. L'objectif & le critère de réussite
*Pourquoi : définir « le commandement marche » AVANT de le bâtir, sinon on optimise un fantôme (leçon payée).*
- **A1.** Qu'est-ce qui prouve concrètement la réussite ? (taux de succès de mission · pertes contenues · un observateur voit un comportement militaire cohérent · toi qui joues et constates)
- **A2.** « Opérable tactiquement » = quel niveau exigé ? (tenir une opération de bout en bout sans micro-gestion · réagir au contact · exécuter une manœuvre complexe coordonnée)
- **A3.** Livrable = une **vitrine** (vidéo/scénario jouable) ou un **système réutilisable** (n'importe quelle mission) ?
- *Défaut : réussite = opération menée de bout en bout dans le VRAI Arma, comportement militaire lisible, toi dans la boucle comme témoin/acteur.*

### B. La structure de commandement
*Pourquoi : le nombre d'échelons change tout (1 officier + 4 escouades ≠ une compagnie).*
- **B1.** Combien d'échelons ? (officier unique → escouades → soldats · OU chef de section + chefs de groupe + soldats)
- **B2.** Quelle taille de force ? (nb d'escouades, nb de soldats/escouade — section ~30 ? compagnie ~120 ?)
- **B3.** Un seul officier-cerveau, ou une **hiérarchie** de décideurs (sous-chefs) ?
- *Défaut : 1 officier (échelon lent) → 4 escouades de ~7 → ~28 hommes (section renforcée), ce qu'on a déjà.*

### C. L'officier (le cerveau de commandement — la pièce à construire)
- **C1.** Quelles décisions prend-il ? (posture de faction · choix de la manœuvre dans le répertoire M1-M12 · allocation des escouades aux objectifs · déclenchement des contingences/réserve)
- **C2.** À quel tempo ? (ordres toutes les N secondes — échelon lent)
- **C3.** Son cerveau : LLM qui raisonne (qwen) · règles doctrinales · appris par RL (GRPO) · un mélange ?
- **C4.** Raisonne-t-il en **langage clair** (ordres explicites) ou en **vocabulaire d'options** codé ?
- *Défaut : officier lent qui LIT la situation, CHOISIT la manœuvre et ALLOUE les escouades ; LLM qwen raisonnant, affiné GRPO ensuite ; vocabulaire doctrinal.*

### D. Les escouades / agents (les exécutants)
*Pourquoi : « tactiquement opérables » = leur compétence réelle au feu.*
- **D1.** Que doivent-ils savoir faire seuls ? (avancer · supprimer · assauter · se couvrir · déborder · exploiter le terrain · réagir au contact · soigner)
- **D2.** Rôles **fixes** (mitrailleur, voltigeur, antichar, médecin) ou interchangeables ?
- **D3.** Autonomie : exécutent une **intention** (« prends cette position ») ou des ordres fins ?
- *Défaut : agents koth_finetuned (déjà compétents en combat dans Arma) exécutant des macro-ordres ; rôles à préciser avec toi.*

### E. La mission & le théâtre
- **E1.** Types d'opérations visés ? (assaut d'une position · défense · King of the Hill · patrouille/embuscade · raid · MEDEVAC)
- **E2.** Objectif unique ou **enchaînement** (infiltration → assaut → consolidation → exfil) ?
- **E3.** Terrain/carte ? (Altis, un secteur type, des théâtres variés)
- *Défaut : opération à phases sur Altis (ce qu'on a), objectif type « prendre et tenir une position ».*

### F. L'ennemi
- **F1.** Scripté · adaptatif (réagit au contact) · ou **APPRIS** (RL) ?
- **F2.** Niveau et taille face à la force amie ? (parité 1:1 ? supériorité ? infériorité ?)
- **F3.** Veut-on un ennemi qui **évolue contre nous** (co-évolution) — c'est lui qui crée le vrai dilemme de commandement ?
- *Défaut : démarrer scripté/adaptatif (skilled_react…), viser le défenseur APPRIS pour faire émerger le vrai besoin de choisir.*

### G. Réalisme & contraintes
- **G1.** Vanilla ou **moddé** (ACE : médical réaliste, balistique) ?
- **G2.** Contraintes à modéliser : ROE/civils · logistique (munitions) · blessés/MEDEVAC ?
- **G3.** Brouillard de guerre · nuit · météo ?
- *Défaut : vanilla d'abord (monde de contrôle stable), Monde 2 (ACE) en version majeure ultérieure.*

### H. L'apprentissage
- **H1.** Officier : LLM **gelé prompté** d'abord puis **GRPO** ? ou RL direct ?
- **H2.** Agents : garder koth_finetuned · ré-entraîner · co-évolution avec l'ennemi ?
- **H3.** Échelle : sandbox GPU (rapide, millions de parties) PUIS validation Arma ?
- *Défaut : officier gelé → GRPO ; agents existants ; sandbox GPU + validation Arma (court-circuite le mur sim-to-real, leçon du manager appris 0/32).*

### I. L'humain dans la boucle (toi)
- **I1.** Tu te connectes avec la 1060 — comme **quoi** ? (soldat · chef d'escouade · l'officier toi-même · observateur · adversaire)
- **I2.** **Allié** des agents ou **contre** eux ?
- **I3.** Le commandement IA doit-il t'intégrer comme une unité commandable, ou tu restes hors hiérarchie ?
- *Défaut : toi connecté en privé (Tailscale, jamais d'autres humains), allié OU adversaire selon la session, l'IA s'adapte à ta présence.*

### J. Vitrine & jalons
- **J1.** Le **livrable démontrable final** ? (vidéo d'une opération commandée par l'IA · scénario jouable · rapport)
- **J2.** Le **premier jalon minimal** qui te ferait dire « ça marche » ?
- **J3.** Ambition : démo soignée vs système complet ? échéance ?
- *Défaut : J1 = une opération complète menée par l'officier, visible et jouable ; jalon 1 = l'officier commande 4 escouades sur une prise de position, de bout en bout, sans toi aux manettes.*

### K. CMO (théâtre 2 — confirmé : pas un remplacement)
- **K1.** CMO = la **même architecture** (officier → exécuteurs) transposée à l'aéronaval, en parallèle ?
- **K2.** Priorité claire : **Arma d'abord** (commandement terrestre complet), CMO en parallèle léger ?
- *Défaut : Arma = livrable principal MAINTENANT ; CMO = 2e théâtre, Gate 0 en parallèle léger, montée en puissance après le commandement Arma.*

---

### Bonus — questions ouvertes (réponds si tu as un avis tranché)
- **L1.** Y a-t-il un **modèle militaire réel** qui t'inspire la doctrine de commandement visée ? (Auftragstaktik allemande / commandement par intention, doctrine OTAN, autre)
- **L2.** L'officier doit-il **expliquer ses décisions** (ordres en clair traçables, valeur démonstration/pédagogie) ?
- **L3.** Qu'est-ce qui, dans une opération, te ferait dire « là, c'est un VRAI commandement militaire » et pas juste des bots qui bougent ?
