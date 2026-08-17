#!/usr/bin/env python3
"""smoke_placeur.py — RÈGLE 18 SUR LE PLACEUR v2.

Deux contrôles, tous deux exigibles avant de certifier quoi que ce soit :

  A · IL SAIT REFUSER — `HMT_SABOTER = "traverse"` retire les jambes du testeur.
      ATTENDU : AUCUN lieu reçu sur 24 candidats, et le prévol rouge en T0.
      Si le sabotage ne fait rien refuser, le placeur ne juge pas : ARRÊT TOTAL.

  B · IL RETROUVE LES CINQ LIEUX CONNUS — appel direct de `HMT_G_PRATICABLE`.
      ATTENDU : les trois lieux morts REJETÉS, les deux vivants REÇUS.
      ⚠️ C'est un SMOKE, pas une certification : ces lieux ont été choisis par le
      diagnostic, donc les tester ici c'est tester sur l'échantillon de découverte ⟨Fable⟩.
      Et « vivant » signifie seulement « pas 100 % mort » — un lieu à 33 % d'échec est
      MARGINAL, son rejet par le v2 ne serait pas une faute.
"""
import sys, os, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
from banc_live import SCENE, sans_commentaires
import arma_couture as C

SB = "/mnt/data/harmattan-sandbox"; EXT, PORT = 5830, 6062
LOG = SB + "/logs/serverSMOKE.out"
LIEUX = [("mort_4989_5877", 4989, 5877), ("mort_4716_5207", 4716, 5207),
         ("mort_4210_5369", 4210, 5369), ("vif_4776_5196", 4776, 5196),
         ("vif_4445_6138", 4445, 6138)]

def sh(c): subprocess.run(c, shell=True, executable="/bin/bash")

if __name__ == "__main__":
    C.CX, C.CY = 4644.0, 5652.0; C.SCALE = 200.0
    open(LOG, "w").close()
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done"); time.sleep(4)
    print("  serveur...", flush=True)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(45)
    b = SocketBridge(EXT); time.sleep(3)
    b.send(sans_commentaires(SCENE), wait=False); time.sleep(6)
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(3)
    v = None
    for _ in range(6):
        b.send('diag_log format ["HMT|V|%1", HMT_SOCLE_VERSION];', wait=False); time.sleep(1)
        L = [l for l in b._log_lines(80) if "HMT|V|" in l]
        if L: v = L[-1].split("HMT|V|")[1][:22]; break
    print("  socle : %s" % v, flush=True)

    print("\n  ══ B · LES CINQ LIEUX CONNUS ══", flush=True)
    res = {}
    for nom, x, y in LIEUX:
        b.send('HMT_R = nil; [] spawn { HMT_R = [[%d,%d]] call HMT_G_PRATICABLE; };' % (x, y), wait=False)
        r = None
        for _ in range(14):
            time.sleep(1.5)
            b.send('diag_log format ["HMT|R|%1", (if (isNil "HMT_R") then {"attente"} else {HMT_R})];', wait=False)
            time.sleep(0.5)
            L = [l for l in b._log_lines(80) if "HMT|R|" in l]
            if L and "attente" not in L[-1]:
                r = L[-1].split("HMT|R|")[1].strip().strip('"'); break
        res[nom] = r or "AUCUNE REPONSE"
        print("    %-18s → %s" % (nom, res[nom]), flush=True)

    print("\n  ══ A · SAIT-IL REFUSER ? (sabotage des jambes du testeur) ══", flush=True)
    b.send('HMT_SABOTER = "traverse";', wait=False); time.sleep(1)
    sab = {}
    for nom, x, y in LIEUX[:3]:
        b.send('HMT_R2 = nil; [] spawn { HMT_R2 = [[%d,%d]] call HMT_G_PRATICABLE; };' % (x, y), wait=False)
        r = None
        for _ in range(14):
            time.sleep(1.5)
            b.send('diag_log format ["HMT|R2|%1", (if (isNil "HMT_R2") then {"attente"} else {HMT_R2})];', wait=False)
            time.sleep(0.5)
            L = [l for l in b._log_lines(80) if "HMT|R2|" in l]
            if L and "attente" not in L[-1]:
                r = L[-1].split("HMT|R2|")[1].strip().strip('"'); break
        sab[nom] = r or "AUCUNE REPONSE"
        print("    %-18s → %s" % (nom, sab[nom]), flush=True)
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done")

    print("\n  ══ VERDICT ══", flush=True)
    recu = lambda s: "recu" in (s or "")
    if any(recu(x) for x in sab.values()):
        print("  ⛔ LE SABOTAGE N'A RIEN FAIT REFUSER — le placeur ne juge pas. ARRÊT TOTAL."); sys.exit(2)
    print("  ✓ A · sabotage : aucun lieu reçu — le placeur SAIT refuser")
    mor = [k for k in res if k.startswith("mort")]; vif = [k for k in res if k.startswith("vif")]
    nm = sum(1 for k in mor if not recu(res[k])); nv = sum(1 for k in vif if recu(res[k]))
    print("  %s B · lieux morts rejetés : %d/3   lieux vivants reçus : %d/2"
          % ("✓" if (nm == 3 and nv >= 1) else "⚠️", nm, nv))
    if nm < 3: print("     ⛔ un lieu MORT est reçu — le placeur laisse passer ce qui tue le banc."); sys.exit(3)
    if nv == 0: print("     ⚠️ aucun lieu vivant reçu — trop strict, ou ces lieux étaient marginaux.")
    print("\n  ⚠️ SMOKE, PAS CERTIFICATION : ces lieux ont été choisis par le diagnostic.")
    print("     La certification demande ~50 lieux FRAIS, zéro faux-reçu (plafond 6 %).")
