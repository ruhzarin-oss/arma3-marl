"""obs_contract — LE CONTRAT D'OBSERVATION (FIGÉ 13/06/2026, validé Younes : "Standard").

Source de vérité UNIQUE de la perception spatiale. Le sandbox GPU (`koth_gpu`/`op_gpu`, vectorisé torch)
ET l'exporteur Arma (SQF + pont natif) produisent EXACTEMENT ce format, à l'octet près.
=> adresse le SCAR sim-to-real (manager 83% sim -> 0% Arma) : une seule définition, deux implémentations.

Repère : ÉGOCENTRIQUE orienté cap. Origine = position de l'agent. "Devant" = +y (haut). "Droite" = +x.
(Pilier 1 du doc perception : une leçon ne dépend pas du Nord -> 1 entrée apprise 1 fois au lieu de 4.)
"""
import numpy as np

# ============================ PARAMÈTRES FIGÉS ============================
W_METERS = 128.0                       # côté de la fenêtre égocentrique (m)
CELL_METERS = 2.0                      # résolution (m / cellule)
GRID = int(round(W_METERS / CELL_METERS))   # = 64  -> grille 64x64

# --- Calques STATIQUES (décor connu, pré-calculé 1x, jamais en mémoire récurrente) ---
# image (N_STATIC, GRID, GRID), chaque canal normalisé dans [0,1].
STATIC_LAYERS = ["elevation", "slope", "road", "building", "cover"]
N_STATIC = len(STATIC_LAYERS)          # 5

# --- Tokens DYNAMIQUES (acteurs, nb variable -> tokens pour le Perceiver) ---
# 1 token par entité perçue. Le dynamique est la SEULE chose lue en direct + mise en mémoire.
ENTITY_TYPES = ["ally", "enemy", "threat", "smoke"]   # one-hot (4)
# token = [one-hot type (4), ex_norm, ey_norm, bearing_sin, bearing_cos, dist_norm, state]
ENTITY_TOKEN_DIM = len(ENTITY_TYPES) + 6               # = 10

# --- Variables VECTORIELLES de l'agent (proprioception + but) ---
AGENT_VEC = ["speed_norm", "hp", "ammo", "obj_bearing_sin", "obj_bearing_cos", "obj_dist_norm"]
N_AGENT_VEC = len(AGENT_VEC)           # 6  (le rôle est ajouté par un embedding séparé côté réseau)

# --- Normalisation (IDENTIQUE des deux côtés) ---
ELEV_SCALE = 50.0      # élévation : (h - moyenne locale de la fenêtre) / ELEV_SCALE, puis clip [-1,1]->[0,1]
DIST_SCALE = W_METERS  # distances normalisées par la demi-fenêtre


# ============================ TRANSFORM ÉGOCENTRIQUE (le coeur partagé) ============================
def to_egocentric(world_xy, agent_xy, heading_rad):
    """Monde -> repère agent (forward=+y, right=+x). heading_rad = cap depuis le Nord (+y), horaire (Arma getDir).
    world_xy: (...,2) ; renvoie (...,2) en mètres, origine agent. IDENTIQUE sandbox/Arma."""
    rel = np.asarray(world_xy, dtype=np.float32) - np.asarray(agent_xy, dtype=np.float32)
    c, s = np.cos(heading_rad), np.sin(heading_rad)
    ego_x = rel[..., 0] * c - rel[..., 1] * s      # droite
    ego_y = rel[..., 0] * s + rel[..., 1] * c      # devant
    return np.stack([ego_x, ego_y], axis=-1)


def entity_token(etype, ego_xy, state=0.0):
    """Construit un token d'entité normalisé (egocentrique)."""
    oh = [1.0 if etype == t else 0.0 for t in ENTITY_TYPES]
    ex, ey = float(ego_xy[0]), float(ego_xy[1])
    dist = float(np.hypot(ex, ey)); bearing = float(np.arctan2(ex, ey))   # 0 = droit devant
    return np.array(oh + [ex / DIST_SCALE, ey / DIST_SCALE,
                          np.sin(bearing), np.cos(bearing),
                          min(dist / DIST_SCALE, 2.0), float(state)], dtype=np.float32)


# ============================ VALIDATEUR (garde-fou sim<->Arma) ============================
def validate(static_grid, entity_tokens, agent_vec):
    """Vérifie qu'une observation produite (sandbox OU Arma) respecte le contrat. Lève si non conforme."""
    sg = np.asarray(static_grid)
    assert sg.shape == (N_STATIC, GRID, GRID), "static_grid doit être (%d,%d,%d), reçu %s" % (N_STATIC, GRID, GRID, sg.shape)
    assert sg.min() >= -1e-3 and sg.max() <= 1.0 + 1e-3, "calques statiques hors [0,1]"
    et = np.asarray(entity_tokens)
    assert et.ndim == 2 and et.shape[1] == ENTITY_TOKEN_DIM, "tokens entités doivent être (n, %d)" % ENTITY_TOKEN_DIM
    av = np.asarray(agent_vec)
    assert av.shape == (N_AGENT_VEC,), "agent_vec doit être (%d,)" % N_AGENT_VEC
    return True


CONTRACT = dict(W_METERS=W_METERS, CELL_METERS=CELL_METERS, GRID=GRID,
                STATIC_LAYERS=STATIC_LAYERS, ENTITY_TYPES=ENTITY_TYPES,
                ENTITY_TOKEN_DIM=ENTITY_TOKEN_DIM, AGENT_VEC=AGENT_VEC,
                FROZEN="2026-06-13", PROFILE="Standard")

if __name__ == "__main__":
    print("CONTRAT D'OBSERVATION (figé) :")
    for k, v in CONTRACT.items():
        print("  %-16s %s" % (k, v))
    # auto-test du transform + validateur
    ego = to_egocentric([15050, 16000], [15000, 16000], 0.0)   # ennemi 50m à l'est, agent face nord
    print("\ntest egocentrique (ennemi 50m est, cap nord): ego=", ego, "(attendu ~[50, 0] = à droite)")
    sg = np.zeros((N_STATIC, GRID, GRID), dtype=np.float32)
    tok = np.stack([entity_token("enemy", ego)])
    av = np.zeros(N_AGENT_VEC, dtype=np.float32)
    print("validate:", validate(sg, tok, av), "| token dim:", tok.shape)
