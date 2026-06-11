# Gate 0 CMO — pont via VM Windows (plan + etat)

## Pourquoi une VM
CMO est une appli .NET/WPF Windows. Sous Wine/Proton : bug `FDICopy` (extraction cabinet `netfx_core.mzz`)
sur TOUTES les versions testees (Proton 8/9/10, GE 10-27/10-34) -> .NET ne s installe pas. Cause : MSI 32 bits
qui ne se charge pas (erreur 193, WoW64). Une VM Windows fait tourner CMO NATIVEMENT -> zero bug.

## Architecture du pont (la 3090 reste cote Linux)
VM Windows : CMO + script Lua `cmo_bridge.lua` (evenement recurrent ~1/s).
Linux hote (3090) : Python `cmo_bridge.py` (officier + executeurs RL).
Echange : DOSSIER PARTAGE host<->VM. CMO ecrit state.json, Python ecrit cmd_<N>.lua. Ecritures ATOMIQUES.
La 3090 fait l inference en local sur l hote ; elle ne voit jamais la VM.

## Etat
- [x] `cmo_bridge.py` (hote) : read_state / send(lua) / last_executed / units. Ecriture atomique.
- [x] `cmo_bridge.lua` (CMO) : dump etat + poll cmd. Enumeration unites VP_GetSide/ScenEdit_GetUnit A VALIDER contre CMO reel.
- [x] `test_bridge.py` : TEST A BLANC complet PASSE (lecture/envoi/accuse/effet) sans CMO ni VM.
- [ ] BIOS : activer VT-x (actuellement OFF -> pas de /dev/kvm). REBOOT requis (acces physique).
- [ ] KVM/QEMU/virt-manager + VM Windows + Steam + CMO.
- [ ] Dossier partage host<->VM (virtio-9p ou Samba) ; HMT_DIR cote Windows.
- [ ] Lua security DESACTIVEE dans CMO (sinon io.open bloque).
- [ ] Valider l enumeration d unites Lua + premier round-trip CMO reel = Gate 0 franchi.

## Prerequis VM (quand VT-x sera ON)
ISO Windows 10/11 (gratuit MS) ; VM 8 Go RAM / 6 coeurs / disque 80 Go sur /mnt/data ; GPU virtuel (CMO=2D).
