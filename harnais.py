#!/usr/bin/env python3
"""harnais — LE RUNNER. C'est ici que le premier gradient tombe.

Il ne tourne QU'APRES le contrôle 4 (temoins_traversants), qui est VERT :
    DOCTRINE  51/51 = 100,0 %  dans [93,0 ; 100]
    ALEATOIRE  7/51 =  13,7 %  dans [5,5 ; 23,4]   —  0 rejet sur 102 episodes
La couture ne mange rien : un verdict d'entrainement est donc lisible.

CE QUI EST PRE-INSCRIT, ET NE SE CHANGE PAS EN COURS DE ROUTE
  · recompense TERMINALE PURE : prise = 1, tout le reste = 0. Aucun faconnage.
  · decodeur = ECHANTILLONNAGE, jamais argmax. Le mode s'imprime a chaque lot.
  · bonus d'entropie beta = 0,01 — declare. Avec 13 actions et des lots de 24 episodes,
    l'effondrement d'entropie EST la condensation qui a coute le 3,3 %. L'entropie se
    journalise a chaque mise a jour : c'est le sismographe.
  · STOP-LOSS : si a 5000 episodes la prise n'a pas quitte la bande de l'aleatoire
    (< 25 %), on ARRETE et on diagnostique. On ne brule pas une seconde nuit sur une
    boucle muette.
  · PORTE B0@30 : >= 93,0 % — bornes basses de l'IC Wilson de la doctrine, mesurees.

CE QUI PROTEGE DES FAUTES DEJA PAYEES
  · un episode sans geste est VOID : jamais compte. Un pont mort ne fabrique pas d'echec.
  · le point de sauvegarde porte le SHA du initServer.sqf deploye. Un lot qui reprend sur
    une mission differente REFUSE de courir — le piege du « temoin d'hier » est verrouille.
  · plus de 10 % de voids sur un lot = lot suspect, on n'additionne pas.
  · l'alea du monde est tire ICI et voyage dans le ticket : le `random` de SQF ne se graine
    pas, donc « graines neuves » ne serait ni vrai ni rejouable autrement.
"""
import os, sys, time, json, math, random, hashlib, argparse
sys.path.insert(0, "/home/younes/arma3-marl")
import torch, torch.nn as nn
from pont import Pont
from para import instance

PROFIL  = "/mnt/c/Users/Younes/hmtech0"
MISSION = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Arma 3/mpmissions/EchellePol.Altis/initServer.sqf"
NOBS, NA = 9, 13
DEV = "cuda:0" if torch.cuda.is_available() else "cpu"

# meme architecture que la Politique de boucle.py : 9 -> 128 -> 128 -> (13 logits, valeur)
class Politique(nn.Module):
    def __init__(self, nobs=NOBS, nh=128, na=NA):
        super().__init__()
        self.f = nn.Sequential(nn.Linear(nobs, nh), nn.Tanh(), nn.Linear(nh, nh), nn.Tanh())
        self.pi = nn.Linear(nh, na)
        self.v  = nn.Linear(nh, 1)
    def forward(self, o):
        h = self.f(o)
        return self.pi(h), self.v(h).squeeze(-1)

def sha_mission():
    with open(MISSION, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]

def episode(pont, pol, uid, rng, D, barreau, patience=90.0, sites=None):
    """Un episode conduit par la mission, choisi par le reseau. Rend (traj, prise) ou (None, cause)."""
    dx, dy = rng.uniform(-D/25, D/25), rng.uniform(-D/25, D/25)
    daz = rng.uniform(-6, 6)
    if sites is None:
        pont.envoyer(f'HMT_TICKET = [{uid}, "{barreau}", {D}, {dx:.3f}, {dy:.3f}, {daz:.3f}];')
    else:
        # le site est tire par le MEME rng que le jitter : il fait partie de l'alea du
        # monde, il voyage dans le ticket, et il est donc rejouable a la graine pres.
        st = rng.choice(sites)
        pont.envoyer(f'HMT_TICKET = [{uid}, "{barreau}", {D}, {dx:.3f}, {dy:.3f}, {daz:.3f}, '
                     f'{st["x"]:.2f}, {st["y"]:.2f}, {st["az"]}];')
    traj = []
    t0 = time.time()
    while time.time() - t0 < patience:
        l = pont.attendre("[ECHP] ", patience - (time.time() - t0))
        if l is None:
            return None, "silence"
        if "] OBS " in l:
            p = l.split("] OBS ")[1].replace('"', "").split()
            if int(p[0]) != uid: continue
            cycle = int(p[1])
            o = torch.tensor([float(x) for x in p[2:11]], dtype=torch.float32, device=DEV)
            logits, v = pol(o)
            d = torch.distributions.Categorical(logits=logits)
            a = d.sample()                                    # ECHANTILLONNAGE, toujours
            traj.append((d.log_prob(a), v, d.entropy()))
            pont.envoyer(f"HMT_ACT = [{uid}, {cycle}, {int(a.item())}];")
        elif "] RESULT " in l:
            p = l.split("] RESULT ")[1].replace('"', "").split()
            if int(p[0]) != uid: continue
            prise, voids = int(p[1]), int(p[6])
            if voids or not traj:
                return None, "void"
            return traj, prise
    return None, "timeout"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--barreau", default="B0")
    ap.add_argument("--D", type=float, default=30.0)
    ap.add_argument("--episodes", type=int, default=48)
    ap.add_argument("--maj", type=int, default=24)         # episodes par mise a jour
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--beta", type=float, default=0.01)    # bonus d'entropie, DECLARE
    ap.add_argument("--graine", type=int, default=0)       # graine torch
    ap.add_argument("--ckpt", default="/home/younes/arma3-marl/ckpt_b0")
    ap.add_argument("--reprise", default="")
    ap.add_argument("--instance", type=int, default=0)   # une instance = un proprietaire
    # ⚠️ SANS CECI, DEUX GRAINES QUI REPRENNENT LE MEME POINT SONT LA MEME COURSE.
    # La reprise restaure torch_rng ET py_rng : les deux runs tireraient les memes
    # gestes et les memes mondes. La regle des deux graines ne verifierait plus rien,
    # et deux courbes jumelles ressembleraient a une reproductibilite parfaite.
    ap.add_argument("--resemer", action="store_true")
    ap.add_argument("--sites", default="")
    # ⚠️ REGLE D'ARRET A ISSUE UNIFORME. A plafond (ou a plancher), tous les retours sont
    # egaux, l'avantage degenere, et le seul gradient encore vivant est le bonus
    # d'entropie — qui pousse la politique vers l'uniforme. Laisser tourner EROODE alors
    # une politique acquise. La regle est SYMETRIQUE par construction : elle coupe aussi
    # bien un agent bloque a 100 % de reussite qu'un agent bloque a 100 % d'echec, donc
    # elle ne peut jamais etre accusee de couper « parce que ca plait ».
    ap.add_argument("--arret-uniforme", type=int, default=5)
    # ⚠️ MEME LOGIQUE QUE POUR LA PORTE : reprendre un point dans un monde CHANGE ne se
    # refuse pas en silence, mais ne se permet pas en silence non plus. Le drapeau exige
    # un aveu qui nomme les deux SHA dans le journal du run.
    ap.add_argument("--transfert", action="store_true")
    a = ap.parse_args()

    torch.manual_seed(a.graine)
    sha = sha_mission()
    pol = Politique().to(DEV)
    opt = torch.optim.Adam(pol.parameters(), lr=a.lr)
    fait, rng_state = 0, None
    rng = random.Random(90210 + a.graine)

    if a.reprise and os.path.exists(a.reprise):
        c = torch.load(a.reprise, map_location=DEV, weights_only=False)
        if c["sha_mission"] != sha:
            if not a.transfert:
                print(f"REFUS DE REPRENDRE : le point porte le SHA {c['sha_mission']}, "
                      f"la mission deployee vaut {sha}. Ce ne serait pas le meme monde.")
                return 2
            print(f"⚠️ REPRISE EN TRANSFERT, MONDE DIFFERENT ASSUME.")
            print(f"   point entraine dans le monde {c['sha_mission']}")
            print(f"   poursuivi     dans le monde {sha}")
            print(f"   Toute citation de ce run doit porter cette phrase.", flush=True)
        pol.load_state_dict(c["pol"]); opt.load_state_dict(c["opt"])
        torch.set_rng_state(c["torch_rng"].cpu()); rng.setstate(c["py_rng"])
        fait = c["fait"]
        print(f"reprise : {fait} episodes deja faits, SHA {sha} concordant")
        if a.resemer:
            torch.manual_seed(a.graine)
            rng = random.Random(90210 + a.graine)
            print(f"RESEMEE a la graine {a.graine} : les tirages du point sont jetes, "
                  f"cette course diverge de toute autre repartie du meme point.", flush=True)

    os.makedirs(a.ckpt, exist_ok=True)
    lots_sites = None
    if a.sites:
        from sites import charger
        lots_sites = charger(a.sites)
        print(f"sites   : lot '{a.sites}', {len(lots_sites)} sites tires a chaque episode", flush=True)
    uniformes = 0
    inst = instance(a.instance)
    print(f"instance {a.instance} : profil {inst['profil']}  pont {inst['pont']}  port {inst['port']}", flush=True)
    pont = Pont(inst['profil'], pont_dir=inst['pont'])
    print(f"PARAMETRES barreau={a.barreau} D={a.D} maj={a.maj} lr={a.lr} beta={a.beta} "
          f"graine_torch={a.graine} decodeur=ECHANTILLONNAGE dev={DEV} sha_mission={sha}", flush=True)
    if pont.attendre("ETAT PRET", 60) is None:
        print("la mission ne dit jamais PRET"); return 2

    tampon, rejets, hist = [], {}, []
    uid = 500000 + fait
    t_lot = time.time()
    while fait < a.episodes:
        uid += 1
        traj, r = episode(pont, pol, uid, rng, a.D, a.barreau, sites=lots_sites)
        if traj is None:
            rejets[r] = rejets.get(r, 0) + 1
            n_rej = sum(rejets.values())
            if n_rej > max(4, 0.10 * max(1, fait)):
                print(f"LOT SUSPECT : {n_rej} rejets {rejets} — on n'additionne pas, on regarde.")
                break
            continue
        fait += 1; tampon.append((traj, float(r))); hist.append(r)

        if len(tampon) >= a.maj:
            lp = torch.stack([t[0] for tr, _ in tampon for t in tr])
            vv = torch.stack([t[1] for tr, _ in tampon for t in tr])
            en = torch.stack([t[2] for tr, _ in tampon for t in tr])
            R  = torch.tensor([rr for tr, rr in tampon for _ in tr], device=DEV)   # terminale, propagee
            adv = (R - vv).detach()
            if adv.std() > 1e-6: adv = (adv - adv.mean()) / (adv.std() + 1e-8)
            perte = -(lp * adv).mean() + 0.5 * ((vv - R) ** 2).mean() - a.beta * en.mean()
            opt.zero_grad(); perte.backward()
            nn.utils.clip_grad_norm_(pol.parameters(), 1.0)
            opt.step()

            recent = hist[-a.maj:]
            taux = 100.0 * sum(recent) / len(recent)
            print(f"maj @ {fait:5d} ep  prise_lot={taux:5.1f} %  entropie={en.mean().item():.3f} "
                  f"(max {math.log(NA):.3f})  perte={perte.item():+.4f}  rejets={rejets} "
                  f"  {time.time()-t_lot:.0f} s", flush=True)
            t_lot = time.time()

            p = os.path.join(a.ckpt, f"pt_{fait:06d}.pt")
            torch.save(dict(pol=pol.state_dict(), opt=opt.state_dict(), fait=fait,
                            torch_rng=torch.get_rng_state(), py_rng=rng.getstate(),
                            sha_mission=sha, graine=a.graine,
                            hist=hist, beta=a.beta, lr=a.lr, D=a.D, barreau=a.barreau),
                       p + ".tmp")
            os.replace(p + ".tmp", p)          # atomique : jamais de point a moitie ecrit
            tampon = []

            # STOP-LOSS pre-inscrit
            if taux >= 100.0 or taux <= 0.0:
                uniformes += 1
                if uniformes >= a.arret_uniforme:
                    print(f"\nARRET A ISSUE UNIFORME : {uniformes} lots consecutifs a "
                          f"{taux:.1f} %. L'avantage est degenere, le seul gradient restant "
                          f"est l'entropie. On s'arrete, la porte se joue.", flush=True)
                    break
            else:
                uniformes = 0
            if fait >= 5000 and taux < 25.0:
                print("STOP-LOSS : 5000 episodes sans quitter la bande de l'aleatoire. On arrete.")
                break

    n = min(len(hist), 100)
    print(f"\nFIN : {fait} episodes, prise sur les {n} derniers = "
          f"{100.0*sum(hist[-n:])/max(1,n):.1f} %  rejets={rejets}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
