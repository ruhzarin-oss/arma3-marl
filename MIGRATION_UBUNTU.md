# Passer le moteur de WSL ( Windows ) à Ubuntu natif

Préparé le 26/09/2026, sur la branche `pays-sur-colonnes`. Tout ce qu'il faut est dans le dépôt, sauf les données
( le disque `/mnt/data`, qu'on garde tel quel ) et les modèles d'Ollama ( qu'on retélécharge ).

## 1. Le disque de données

Monter le disque de données au **même endroit** : `/mnt/data`. Les chemins du moteur y pointent
( `/mnt/data/hmt/...` : nuits, matrice, références, agent codeur ). Sous Windows, c'est `/dev/sdd1` ( 3,6 To, ext4 ).
Dans `/etc/fstab`, par son UUID ( `sudo blkid` ) :

    UUID=<uuid>  /mnt/data  ext4  defaults,nofail  0  2

## 2. Python et le cœur Rust

    sudo apt install -y build-essential python3.12 python3.12-venv python3.12-dev git curl
    curl https://sh.rustup.rs -sSf | sh                       # cargo 1.98 ou plus
    python3.12 -m venv /mnt/data/hmt/evogp/env                # ( ou garder l'environnement existant du disque )
    /mnt/data/hmt/evogp/env/bin/pip install -r requirements-monde.txt --extra-index-url https://download.pytorch.org/whl/cu126
    cd coeur_rust && /mnt/data/hmt/evogp/env/bin/maturin develop --release && cd ..

Le cœur Rust ( `coeur_monde` ) se construit depuis `coeur_rust/` : il n'est pas dans `requirements-monde.txt`.
Si l'environnement du disque est gardé, il suffit de reconstruire le cœur ( l'ancien a été compilé sous WSL ).

## 3. Ollama et l'agent codeur

    curl -fsSL https://ollama.com/install.sh | sh             # version 0.32.12 ou plus ( Qwen3.8 )
    ollama pull qwen3.8:27b                                    # 17 Go ; l'agent codeur écrit les gouvernements

## 4. Les références des portes

Elles vivent hors du dépôt, dans `/mnt/data/hmt` ( donc sur le disque, elles suivent ). Pour les refaire ou les
vérifier depuis le dépôt seul :

    PY=/mnt/data/hmt/evogp/env/bin/python bash references/refaire_references.sh /mnt/data/hmt

Attendu : `REFERENCE DES DOMAINES REPRODUITE AU BIT` et `ANCIEN MOTEUR TEMOIN IDENTIQUE` ( vérifié le 26/09 sous WSL ).

## 5. Toutes les portes

    PY=/mnt/data/hmt/evogp/env/bin/python bash portes.sh

Attendu : `PORTES REFUSEES : 0`. La dernière porte compare les échecs de comportement des portes du pays à
`references/echecs_attendus_pays.txt` ( les portes de coût dépendent de la charge de la machine et ne comptent pas ).

## 6. La nuit sous systemd ( remplace la tâche planifiée Windows `HMT_Archipel` )

    mkdir -p /mnt/data/hmt/archipel/{code,nuit,matrice}
    git archive HEAD monde | tar -x -C /mnt/data/hmt/archipel/code     # le code gelé de la nuit
    sudo cp deploy/hmt-nuit.service /etc/systemd/system/ && sudo systemctl daemon-reload
    sudo systemctl start hmt-nuit                                       # arrêt propre : touch /mnt/data/hmt/archipel/nuit/STOP

Les gardes mémoire de `monde/nuit.py` sont en **part de la mémoire de la machine** : sous WSL ( 49,3 Go déclarés ),
38 et 42 Go ; sur 64 Gio sans WSL, ~53 et ~58 Go. Les nuits à six fois un million iront donc plus loin. On peut les
forcer avec `HMT_SANS_INSTANTANE_GO` et `HMT_ARRET_GO`.

## Ce qui ne passe PAS sous Ubuntu

- Arma 3 et ses serveurs ( Windows ) : le moteur n'en a pas besoin ( décision du 23/09 : moteur seul ).
- Les tâches planifiées Windows ( `HMT_RUN`, `HMT_MONTER_DATA`, ... ) : remplacées par systemd et fstab.
