# OU LIRE L ETAT DU PROJET — a faire AVANT toute autre chose

Trois lieux, une seule verite, dans cet ordre :

1. **Le wiki de Plane** — `http://localhost:8080` (tunnel `ssh -f -N ws`), espace `travaux`, projet HMT, onglet Pages.
   - **ETAT — lire ceci en premier** : la machine, la file, le debit, les portes ouvertes, les verdicts vivants.
   - **Verdicts — le detail** : le texte entier de chaque verdict.
   - **Journal des runs** : une entree datee par run termine, en AJOUT seulement, l'historique ne se reecrit pas.
   Ces trois pages sont **generees** par `outils/wiki.sh` a la fin de chaque run et toutes les 10 minutes.
   **Ne jamais les editer a la main** : la generation suivante ecrase.

2. **Le registre**, source de verite machine : `verdicts/*.md` (en-tete `porte/date/graines/chiffre/verdict/depend_de/remplace_par`)
   et `ETAT.md`, genere par `outils/etat.py`. C'est ici qu'on ECRIT un verdict, jamais dans le wiki.

3. **La file** : `hmt/queue/` dit ce qui va tourner, `hmt/runs/<date>_<banc>/FIN.json` dit ce qui a tourne.

Regles qui ne se discutent pas : deux graines par job, un run finit par `FIN.json`, aucun run lance depuis ssh,
arret par PID jamais par nom, un verdict cite doit avoir son fichier.

---

# arma3-marl — spécifique projet

Le protocole général (style, économie de jetons, standard scientifique, file du
labo, machine 24/24, espace réservé) est dans `~/.claude/CLAUDE.md`. Il
s'applique ici. Ce fichier n'ajoute que ce qui est propre au projet.

## CE QUI COMPTE COMME PROGRÈS
Un verdict certifié sur le vrai Arma. Rien d'autre.
Pas un script écrit, pas un refactor, pas une courbe qui monte en sandbox, pas un
rapport. Si une journée n'a produit aucun verdict, elle n'a rien produit — dis-le
franchement au lieu de lister l'activité.

## LES DEUX INSTRUMENTS
Sandbox = banc d'essai, on y met la machinerie au point. Arma = certificateur,
c'est lui qui tranche. Une brique non passée sur le vrai Arma n'est pas acquise.
Sandbox sur la 3090 et certification Arma peuvent tourner ensemble : ce sont deux
instruments, pas un. Arma rend sur la 1060.

## PONT ARMA
Un seul client. `close()` obligatoire. Zombies tués avant tout lancement — deux
Python sur le pont et il devient muet sans erreur.
Le pont meurt en service après 20-40 min même à vide : prévoir la sentinelle.
Un pont qui accepte la connexion ne prouve pas que le script de mission est
chargé. Vérifier le second, pas le premier.

## CROYANCES DU PROJET DÉJÀ RÉFUTÉES
Trois croyances tenues pour acquises se sont révélées fausses après mesure.
Toute affirmation HÉRITÉ de ce projet est suspecte tant qu'un log ne la
confirme pas.
NE PAS refaire « RL découvre la tactique en sim » (scar manager 83 %→0 %).

## JOURNAL
Tout verdict daté dans `MEMOIRE-COMMUNE.md`, en append. L'historique ne se
réécrit pas. L'architecte (Claude-Mac) y écrit aussi : relis avant d'éditer.
En début de session : `MEMOIRE-COMMUNE.md`, puis `/mnt/data2/lab/QUEUE.tsv`,
puis `NEXT-TASKS.md`.
Références : `PROTOCOL.md`, `FICHE-ROUTE.md`, `arma3-marl-TOUT-EN-UN.pdf`.
`MEMOIRE-COMMUNE.md` fait foi sur l'état du projet, pas ce fichier.

## FLOTTE
Flotte dégradée (>15 % erreurs/timeouts) : reboot. Mot de passe sudo à me demander.
