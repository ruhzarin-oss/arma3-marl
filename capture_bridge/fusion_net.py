#!/usr/bin/env python3
"""fusion_net.py — extension pixel+etat de Net (train_koth_gpu.py).

Contexte : verdict Fable du 25/08 (NO-GO argumente sur les pixels dans Arma,
voir memoire pixels-arma-verdict-fable-nogo), passe outre par decision de
Younes le 31/08/2026. Un seul client rendu = une seule camera = UN agent :
l'image ne peut donc augmenter QU'UNE ligne du vecteur d'etat par pas, jamais
les N lignes de HMT_FR. Design retenu : chaque agent porte un bit `has_pixel`
(1 si c'est lui qui est filme ce pas, 0 sinon) ; l'embedding image est nul
pour les agents non filmes plutot que de dupliquer l'image sur tous.

NetFusion garde l'interface de Net (a_logits/value) pour rester substituable
dans le harnais PPO existant (ppo_mb dans train_koth_gpu.py).
"""
import torch
import torch.nn as nn

OBS_DIM_STATE = 20          # inchange, cf. arma_couture.py (base9+suffer2+team4+posture3+arc2)
IMG_SIZE = 96                # cote de l'image apres redimensionnement cote capture (carre)
IMG_EMBED_DIM = 32           # embedding image, volontairement petit : MVP, pas ViT
OBS_DIM_FUSION = OBS_DIM_STATE + 1 + IMG_EMBED_DIM   # +1 = flag has_pixel


class ImageEncoder(nn.Module):
    """CNN leger. Budget vise < 5 ms sur 3090 pour un lot de quelques agents/pas —
    le pont (238 ms median mesure) reste le goulot, pas ce reseau."""
    def __init__(self, embed_dim=IMG_EMBED_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 16, 5, stride=2, padding=2), nn.ReLU(),   # 96 -> 48
            nn.Conv2d(16, 32, 5, stride=2, padding=2), nn.ReLU(),  # 48 -> 24
            nn.Conv2d(32, 32, 3, stride=2, padding=1), nn.ReLU(),  # 24 -> 12
            nn.Conv2d(32, 32, 3, stride=2, padding=1), nn.ReLU(),  # 12 -> 6
            nn.Flatten(),
            nn.Linear(32 * 6 * 6, embed_dim), nn.ReLU(),
        )

    def forward(self, img):
        # img : (N, 1, IMG_SIZE, IMG_SIZE), niveaux de gris normalises [0,1]
        return self.net(img)


class NetFusion(nn.Module):
    """Fusion tardive : encodeur image -> embedding, concatene au vecteur d'etat,
    tronc + tetes pi/v identiques a Net. Asymetrique PAS implemente ici (le critique
    voit la meme entree fusionnee que l'acteur) : c'est la variante MVP, la variante
    Dactyl (critique sur etat privilegie seul) est un axe documente, pas construit.
    """
    def __init__(self, nact, hidden=512, layers=3, embed_dim=IMG_EMBED_DIM):
        super().__init__()
        self.img_enc = ImageEncoder(embed_dim)
        din = OBS_DIM_STATE + 1 + embed_dim
        body = []
        for _ in range(layers):
            body += [nn.Linear(din, hidden), nn.ReLU()]
            din = hidden
        self.body = nn.Sequential(*body)
        self.pi = nn.Linear(hidden, nact)
        self.v = nn.Linear(hidden, 1)

    def fuse(self, state, img, has_pixel):
        """state: (N, OBS_DIM_STATE) ; img: (N, 1, IMG_SIZE, IMG_SIZE) ; has_pixel: (N,)
        Les agents avec has_pixel=0 doivent recevoir une image nulle (zeros) en entree :
        l'encodeur tourne quand meme dessus (simplicite), son embedding est ensuite
        multiplie par le flag, donc annule proprement plutot que masque en aval."""
        emb = self.img_enc(img) * has_pixel.unsqueeze(-1)
        return torch.cat([state, has_pixel.unsqueeze(-1), emb], dim=-1)

    def a_logits(self, fused_obs):
        return self.pi(self.body(fused_obs))

    def value(self, fused_obs):
        return self.v(self.body(fused_obs)).squeeze(-1).mean(-1)


def _selftest():
    """Verifie la forme des tenseurs et l'annulation de l'embedding quand has_pixel=0,
    hors-ligne, sans Arma ni image reelle. Ne remplace pas une mesure sur le vrai flux."""
    net = NetFusion(nact=13)
    N = 9
    state = torch.randn(N, OBS_DIM_STATE)
    img = torch.rand(N, 1, IMG_SIZE, IMG_SIZE)
    has_pixel = torch.zeros(N)
    has_pixel[0] = 1.0   # seul l'agent 0 est filme ce pas (cas standard : un client rendu)

    fused = net.fuse(state, img, has_pixel)
    assert fused.shape == (N, OBS_DIM_FUSION), f"forme fusion inattendue: {fused.shape}"

    logits = net.a_logits(fused)
    val = net.value(fused)
    assert logits.shape == (N, 13), f"logits: {logits.shape}"
    assert val.shape == (), f"value devrait etre scalaire (moyenne equipe): {val.shape}"

    # controle : deux images DIFFERENTES sur un agent has_pixel=0 doivent produire
    # la MEME fusion (l'embedding est annule par le flag) -> sinon le flag ne protege rien
    img_b = torch.rand(N, 1, IMG_SIZE, IMG_SIZE)
    fused_b = net.fuse(state, img_b, has_pixel)
    assert torch.allclose(fused[1:], fused_b[1:]), "has_pixel=0 ne neutralise pas l'image : FUITE"
    print("[selftest] NetFusion : formes OK (%d agents, obs_dim=%d), has_pixel=0 neutralise bien l'image" %
          (N, OBS_DIM_FUSION))

    n_params = sum(p.numel() for p in net.parameters())
    print(f"[selftest] {n_params:,} parametres (dont encodeur image : "
          f"{sum(p.numel() for p in net.img_enc.parameters()):,})")


if __name__ == "__main__":
    _selftest()
