# Accès distant à la workstation Linux — mémo d'installation

Objectif : piloter la machine Linux (Xeon 12c / RTX 3090 / 64 Go) depuis le Mac, **en terminal
(SSH) et en visuel au besoin (NoMachine)**, accessible **de partout** grâce à Tailscale.

Montage retenu :
- **Tailscale** — VPN privé gratuit : relie Mac et Linux dans un réseau sécurisé, de partout, sans
  ouvrir de port sur la box.
- **SSH** (avec clé) — le terminal : Claude Code, lancement des entraînements, lecture des journaux.
- **NoMachine** — le visuel à la demande (bureau distant fluide, gère la 3D → utile pour regarder
  Arma). La machine Linux a un bureau + un écran branché : cas le plus simple.

> Hypothèse : machine Linux sous **Ubuntu/Debian** (commandes `apt`). Si c'est Arch/Fedora/autre,
> me le dire pour adapter.

---

## Côté Mac — déjà fait ✅

- Clé SSH **ed25519** générée : `~/.ssh/id_ed25519` (privée, ne se partage jamais) +
  `~/.ssh/id_ed25519.pub` (publique).
- Clé **publique** à déposer sur la machine Linux :

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKFrO+Do8HB7nKZjnU4S3rmc+8DyVkPHEEeeUjJzn0Ir mac-vers-workstation-arma
```

## Côté Mac — à installer (Homebrew présent)

```bash
brew install --cask tailscale      # le VPN privé
brew install --cask nomachine      # le client visuel
```
Puis lancer Tailscale (appli) et se connecter avec ton compte (Google/GitHub/email).

---

## Côté Linux — à faire une fois sur place

### 1) Tailscale (VPN)
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Se connecter avec **le même compte** que sur le Mac. Noter le nom/!'IP Tailscale de la machine :
```bash
tailscale ip -4        # affiche l'adresse 100.x.y.z
tailscale status       # affiche le nom de la machine (MagicDNS)
```

### 2) Serveur SSH
```bash
sudo apt update && sudo apt install -y openssh-server
sudo systemctl enable --now ssh
```
Déposer la clé publique du Mac (coller la ligne ci-dessus) :
```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKFrO+Do8HB7nKZjnU4S3rmc+8DyVkPHEEeeUjJzn0Ir mac-vers-workstation-arma" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```
*(Plus tard, durcissement possible : désactiver l'authentification par mot de passe dans
`/etc/ssh/sshd_config` → `PasswordAuthentication no`, puis `sudo systemctl restart ssh`.)*

### 3) NoMachine (visuel)
```bash
# Télécharger le .deb depuis nomachine.com (section Download > Linux > DEB amd64), puis :
sudo dpkg -i nomachine_*.deb
```
Le service NoMachine démarre tout seul. Comme un bureau + écran sont présents, le client pourra se
connecter au **« Physical display »** (le bureau réel de la machine).

---

## Ordre d'exécution (résumé)

1. **Linux** : Tailscale → `openssh-server` → déposer la clé publique → NoMachine.
2. **Mac** : Tailscale (appli + connexion) → client NoMachine.
3. **Tester** SSH, puis NoMachine.

---

## Usage quotidien

### Se connecter en terminal
```bash
ssh ybouhassoun@<nom-ou-IP-tailscale>
```
Astuce confort : créer `~/.ssh/config` sur le Mac (à compléter une fois le nom Tailscale connu) :
```
Host arma
    HostName <nom-ou-IP-tailscale>
    User ybouhassoun
    IdentityFile ~/.ssh/id_ed25519
```
→ ensuite il suffit de taper : `ssh arma`

### Voir les courbes d'apprentissage dans le navigateur du Mac
Sur Linux, lancer le suivi :
```bash
tensorboard --logdir runs --port 6006
```
Depuis le Mac, ouvrir un tunnel puis le navigateur :
```bash
ssh -L 6006:localhost:6006 arma
# puis ouvrir http://localhost:6006 dans le navigateur du Mac
```
*(Avec Tailscale, on peut aussi viser directement `http://<IP-tailscale>:6006` ; le tunnel reste
l'option la plus propre.)*

### Voir le bureau / Arma en visuel
Ouvrir l'appli **NoMachine** sur le Mac → ajouter la machine par son **nom/IP Tailscale** →
se connecter avec le compte Linux. Fonctionne de partout via Tailscale.

---

## Sécurité (en clair)

- Avec **Tailscale**, **rien n'est exposé à l'Internet public** : seules tes propres machines
  (ton « tailnet ») peuvent atteindre la workstation. C'est ça qui rend l'accès « de partout » sûr.
- La clé **privée** (`~/.ssh/id_ed25519`) ne quitte jamais le Mac.
- NoMachine utilise le **login système** de la machine Linux → garde un mot de passe utilisateur solide.
