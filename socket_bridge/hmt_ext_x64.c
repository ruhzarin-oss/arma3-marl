/* hmt_ext_x64.c — extension Arma 3 (Windows x64, tourne sous Proton/Wine sur le client SOLO).
 *
 * BUT : contourner le "gel d'index des fichiers" d'Arma en mode solo/host.
 * En solo, preprocessFileLineNumbers ne voit jamais les cmd_N.sqf ajoutés après le lancement.
 * Cette DLL, appelée par `"hmt_ext" callExtension (str N)`, lit le fichier au niveau OS (fopen)
 * -> elle court-circuite le cache de fichiers d'Arma et renvoie le contenu de cmd_N.sqf.
 *
 * Protocole (identique à la voie dédié) :
 *   SQF : _code = "hmt_ext" callExtension (str _next);   // _next = numéro de commande
 *   - fichier présent  -> renvoie le SQF (que l'actuateur fait `call compile`)
 *   - fichier absent   -> renvoie "" (l'actuateur ré-essaie au tick suivant)
 *
 * Chemin lu : <HMT_BRIDGE_WIN>\cmd_<N>.sqf  (défaut C:\hmt_bridge, surchargeable par var d'env).
 * REVUE 17/08 : ce commentaire annonçait Z:\tmp\hmt_bridge alors que DEFAULT_BRIDGE vaut
 * C:\hmt_bridge depuis un changement plus récent (C: = drive_c du préfixe Proton, partagé
 * HOST<->conteneur). build_ext.sh préparait le mauvais dossier. Le fichier absent et le
 * mauvais chemin rendent tous deux "" : la panne est indiscernable de l'attente.
 *
 * Limite : callExtension plafonne la sortie à ~10240 octets. Les cmd_N.sqf du projet sont petits
 * (obs/actions) -> OK. Garde-fou : si le fichier dépasse, on tronque ET on signale "__TOOBIG__".
 *
 * Compilation : voir build_ext.sh (x86_64-w64-mingw32-gcc -shared).
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* C: = drive_c du prefixe Proton = partage HOST<->conteneur (contrairement a Z:\tmp, isole). */
#define DEFAULT_BRIDGE "C:\\hmt_bridge"

static const char *bridge_dir(void) {
    const char *e = getenv("HMT_BRIDGE_WIN");
    return (e && e[0]) ? e : DEFAULT_BRIDGE;
}

/* Arma appelle ceci au chargement de l'extension. */
__declspec(dllexport) void RVExtensionVersion(char *output, int outputSize) {
    strncpy(output, "hmt_ext 1.0 (socket-bridge Harmattan)", outputSize - 1);
    output[outputSize - 1] = '\0';
}

/* Forme simple : "hmt_ext" callExtension "<N>".  function = le numéro de commande. */
__declspec(dllexport) void RVExtension(char *output, int outputSize, const char *function) {
    output[0] = '\0';
    if (function == NULL) return;

    char path[1024];
    snprintf(path, sizeof(path), "%s\\cmd_%s.sqf", bridge_dir(), function);

    FILE *f = fopen(path, "rb");
    if (!f) return;                 /* absent -> "" (pas encore écrit) */

    int cap = outputSize - 1;       /* place pour le '\0' */
    size_t n = fread(output, 1, (size_t)cap, f);
    output[n] = '\0';

    /* Détecte un fichier plus gros que la capacité (lecture suivante non vide). */
    int extra = fgetc(f);
    fclose(f);
    if (extra != EOF) {
        strncpy(output, "diag_log \"HARMATTAN_ERR cmd __TOOBIG__\";", outputSize - 1);
        output[outputSize - 1] = '\0';
    }
}
