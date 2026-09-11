# LABO Arma : module typé et serveur MCP

Verdict de Fable du 11/09/2026 : **GO SOUS CONDITION**.
**MCP = labo, job = mesure. Rien ne traverse.** Le labo sert à régler une scène et à trouver une
panne. Il ne produit aucun chiffre publiable.

```
Claude → MCP (mcp_arma.py) → module (arma_labo.py) → pont fichier → Arma (Labo.Altis, instance 9)
```

## Ce qu'il y a ici

| Fichier | Rôle |
|---|---|
| `arma_labo.py` | Le module : liaison au pont, reçus, verrous, 7 outils typés. 80 % du travail. |
| `mcp_arma.py` | Le transport MCP : JSON-RPC sur stdio, zéro dépendance. |
| `mcp_arma.sh` | Le lanceur que Claude appelle par ssh, comme `outils/mcp_plane.sh`. |
| `mission.Altis/` | Labo.Altis : actuateur, battement, `fonctions.sqf`. |
| `lancer_labo.sh` + `.ps1` | Démarre le serveur du labo (instance 9) par WMI. |
| `arreter_labo.sh` | L'arrête par PID vérifié. À la main de Younes. |
| `server.cfg.modele` | Profil `hmtech9`, créé s'il manque. |
| `banc_pontmcp.py` + `../bancs/pontmcp/lancer.sh` | Le premier banc, critères écrits avant. |
| `faux_arma.py` + `test_labo.py` | Le jouet et 33 tests, sans Arma : `python3 labo/test_labo.py`. |

Les 7 outils : `canari`, `etat`, `poser_groupe`, `poser_scene`, `ordonner`, `nettoyer`, `sqf`.

## Les règles

- **Instance 9, mission Labo.Altis.** Aucun banc ne les emploie. Le module refuse toute autre instance.
- **Un seul écrivain par pont** (`etat/labo_i9.ecrivain`). Le MCP prend aussi `queue/verrous/j9` :
  la file le voit et le compte dans son plafond.
- **Chaque commande rend un reçu.** Pas de reçu = une exception (`PontMort`, `SansRecu`, `Incomplet`),
  jamais une liste vide.
- **Que des nombres en retour.** Aucun texte du monde ne remonte vers le LLM.
- **SQF brut** : une ligne, sans `//`, borné en taille, sur demande de Younes seulement.

## Ce qui est prouvé, et ce qui ne l'est pas

**Prouvé sur le jouet** (33 tests ; 7 casses volontaires du module, toutes détectées) :
le compteur, les reçus, les pannes (pont mort, sans reçu, ligne perdue, serveur relancé, mission
relancée, autre écrivain), les verrous, les refus, le transport MCP. Le banc de Fable **passe** sur
un pont sain et **échoue** dès qu'un seul reçu manque.

**Pas prouvé** — seul Arma peut le prouver :
- le SQF de `fonctions.sqf` (le jouet ne lit pas le SQF ; un test vérifie seulement la cohérence
  des listes, des clés et des parenthèses) ;
- le lancement par WMI et `lancer_labo.ps1` ;
- le chargement de la mission, la latence réelle.

C'est le rôle du banc `pontmcp`.

## Brancher : dans l'ordre, sur ordre de Younes

0. Commiter sur une branche. Rien dans `outils/` : `controle_avant_run.sh` refuse **tous** les jobs
   dès qu'un fichier de `outils/` n'est pas commité.
1. Poser le garde dans `controle_avant_run.sh` (bloc ci-dessous).
2. File vide. `bash labo/lancer_labo.sh`, attendre « LABO PRÊT ».
3. Canari à la main :
   `python3 -c 'import sys; sys.path.insert(0,"labo"); import arma_labo as a; l=a.Labo().ouvrir(); print(l.canari()); l.fermer()'`
4. `bash labo/arreter_labo.sh`. Puis le job
   `{"banc":"pontmcp","graines":[1,2],"instance":9,"plafond_s":1800}` : c'est lui qui dit PASSE ou ÉCHOUE.
5. Contrôle de contamination (Fable) : un vrai job sur une autre instance pendant le banc, avec
   `"tolere":["labo"]`. Attendu : `FIN.json` COMPLET, et `charge_au_lancement` cite le serveur du labo.
6. **Seulement si PASSE** : inscrire le MCP sur le Mac, dans `~/.claude.json` :
   `"arma": {"command": "ssh", "args": ["-o", "BatchMode=yes", "-T", "ws", "wsl -u younes -- bash /mnt/data/hmt/depot/labo/mcp_arma.sh"]}`

**Sortie de Fable** : un reçu manquant sur 100, un p99 au-dessus de 3 s, ou le serveur du labo dans
le `charge_au_lancement` d'un job sans y être déclaré → le MCP est retiré, et le diagnostic revient
à un CLI sur `arma_labo.py`.

## Le garde à poser dans `outils/controle_avant_run.sh`

À placer après la ligne `TOL=...`. Un job refuse de partir si le labo tourne et qu'il ne le tolère pas.

```bash
# --- le LABO (instance 9) : un serveur de plus change la charge du run. Refus, sauf "labo" toléré.
PL=$H/etat/labo_arma.pid
INSTJ=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('instance'))" "$JOB")
if [ -s "$PL" ] && [ "$INSTJ" != "9" ]; then
  PLABO=$(tr -dc 0-9 < "$PL")
  if "$TL" /FI "PID eq $PLABO" 2>/dev/null | grep -qi arma3server; then
    echo " $TOL " | grep -qi " labo " || { echo "REFUS: le serveur du labo tourne (PID $PLABO) et le job ne tolère pas \"labo\""; ERR=1; }
  fi
fi
```

## Ce qui manque

- **Une place joueur dans `mission.sqm`.** Sans elle, Younes ne peut pas rejoindre le labo. Non fait
  exprès : un morceau non prouvé de plus. À ajouter après le premier PASSE.
- **`catalogue.py`** lit les runs après chaque job : vérifier qu'il ignore un `resultat.json` de pontmcp.
