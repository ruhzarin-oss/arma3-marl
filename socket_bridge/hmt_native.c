/* hmt_native.c — extension NATIVE Linux pour le serveur dédié Arma 3 (harnais de mesure Harmattan).
 *
 * BUT : remplacer le pont fichier+RPT (cmd_N.sqf + diag_log/parsing de log) par un canal TCP en mémoire.
 *   IN  : Python envoie  "c|<n>|<sqf, \n encodés en \x01>\n"  -> stocké en RAM.
 *         L'actuateur SQF poll : "hmt_native" callExtension "p|<n>" -> chunks "M|..."/"D|..." ("" si absent).
 *   OUT : le SQF émet      : "hmt_native" callExtension "o|<ligne>" -> ENFILÉ, envoyé par un thread dédié.
 *   SYNC: à la connexion, l'extension envoie "HMT_SYNC <dernier n délivré>" (reprise propre par op).
 *
 * ROBUSTESSE ANTI-CRASH (fix pipes.cpp) : RVExtension "o|" n'écrit PLUS sur le socket (ça bloquait le thread
 *   d'Arma quand Python prenait du retard -> stalled cross-thread pipe -> crash). Il ne fait qu'EMPILER dans une
 *   file bornée ; un thread EXPÉDITEUR dédié fait les send() bloquants HORS du thread d'Arma. File pleine -> on
 *   jette les plus vieux messages (le serveur survit toujours). MSG_NOSIGNAL partout, un seul client, loopback.
 * Compilation : gcc -shared -fPIC -O2 -pthread -o hmt_native_x64.so hmt_native.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

#define NCMD 128            /* ring des dernières commandes */
#define MAXCMD (1<<20)      /* 1 Mo max par commande */
#define NOUT 16384          /* file d'envoi : ring des lignes à émettre */

/* REVUE 17/08 : le pont perdait des lignes en SILENCE (file pleine, send() ignore,
 * ligne geante jetee) et son listener mourait sans un mot quand le port etait pris.
 * Ces compteurs et cet etat sont rendus par callExtension "version". */
static volatile long DROP_RING = 0;   /* lignes jetees : file d envoi pleine */
static volatile long DROP_SEND = 0;   /* lignes perdues : send() a echoue */
static volatile long DROP_LINE = 0;   /* commandes jetees : ligne > tampon rx */
static char STATUS[160] = "listener pas encore demarre";
static pthread_mutex_t MU = PTHREAD_MUTEX_INITIALIZER;
static pthread_once_t ONCE = PTHREAD_ONCE_INIT;
static int CLIENT = -1;
static long LAST_DELIVERED = 0;   /* dernier n entièrement remis au SQF (D|) */
static long CUR_N = -1; static size_t CUR_OFF = 0;   /* état de chunking */

typedef struct { long n; char *buf; size_t len; } cmd_t;
static cmd_t CMDS[NCMD];

/* --- file d'envoi (sortir l'I/O socket du thread d'Arma) --- */
typedef struct { char *buf; size_t len; } omsg_t;
static omsg_t OUT[NOUT];
static size_t OHEAD = 0, OTAIL = 0;                  /* head = prochaine écriture, tail = prochain envoi */
static pthread_mutex_t OMU = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t OCOND = PTHREAD_COND_INITIALIZER;

static void store_cmd(long n, const char *payload, size_t len) {
    if (len > MAXCMD) return;
    pthread_mutex_lock(&MU);
    cmd_t *c = &CMDS[n % NCMD];
    free(c->buf);
    c->buf = malloc(len + 1);
    if (!c->buf) { c->n = -1; c->len = 0; pthread_mutex_unlock(&MU); return; }  /* REVUE 17/08 */
    memcpy(c->buf, payload, len); c->buf[len] = 0;
    /* dé-encapsule \x01 -> \n */
    for (size_t i = 0; i < len; i++) if (c->buf[i] == '\x01') c->buf[i] = '\n';
    c->n = n; c->len = len;
    pthread_mutex_unlock(&MU);
}

/* RVExtension "o|" appelle ça : rapide, JAMAIS bloquant (pas d'I/O socket ici) */
static void out_enqueue(const char *data, size_t len) {
    char *b = malloc(len + 1);
    if (!b) return;
    memcpy(b, data, len); b[len] = '\n';             /* on ajoute le \n de fin de ligne ici */
    pthread_mutex_lock(&OMU);
    size_t nh = (OHEAD + 1) % NOUT;
    if (nh == OTAIL) {                               /* file pleine -> jette le plus vieux (le serveur survit) */
        free(OUT[OTAIL].buf); OUT[OTAIL].buf = NULL;
        OTAIL = (OTAIL + 1) % NOUT;
        DROP_RING++;                                 /* REVUE 17/08 : la perte est COMPTEE */
    }
    OUT[OHEAD].buf = b; OUT[OHEAD].len = len + 1;
    OHEAD = nh;
    pthread_cond_signal(&OCOND);
    pthread_mutex_unlock(&OMU);
}

/* thread EXPÉDITEUR : draine la file, fait les send() bloquants HORS du thread d'Arma */
static void *sender(void *arg) {
    (void)arg;
    for (;;) {
        pthread_mutex_lock(&OMU);
        while (OHEAD == OTAIL) pthread_cond_wait(&OCOND, &OMU);
        char *b = OUT[OTAIL].buf; size_t len = OUT[OTAIL].len;
        OUT[OTAIL].buf = NULL; OTAIL = (OTAIL + 1) % NOUT;
        pthread_mutex_unlock(&OMU);
        pthread_mutex_lock(&MU); int cl = CLIENT; pthread_mutex_unlock(&MU);  /* on ne tient PAS MU pendant le send */
        /* REVUE 17/08 : le code de retour etait jete — un EPIPE ou un tampon plein
         * perdait la ligne de mesure sans aucune trace. */
        if (cl >= 0 && b) { ssize_t w = send(cl, b, len, MSG_NOSIGNAL); if (w < 0) DROP_SEND++; }
        else if (b) { DROP_SEND++; }
        free(b);
    }
    return NULL;
}

static void *listener(void *arg) {
    (void)arg;
    const char *pe = getenv("HMT_EXT_PORT");
    int port = (pe && pe[0]) ? atoi(pe) : 5801;
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    struct sockaddr_in a = {0};
    a.sin_family = AF_INET; a.sin_port = htons(port);
    a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);           /* loopback only : privé */
    if (bind(srv, (struct sockaddr*)&a, sizeof a) || listen(srv, 1)) {
        /* REVUE 17/08 : on rendait NULL sans un mot. L extension repondait quand meme a
         * "version" depuis la memoire, donc la porte d init.sqf etait VERTE alors que le
         * port etait pris par un serveur zombie : « muet sans erreur ». */
        snprintf(STATUS, sizeof STATUS, "ECHEC bind/listen port %d (deja pris ?)", port);
        fprintf(stderr, "hmt_native: %s\n", STATUS);
        return NULL;
    }
    snprintf(STATUS, sizeof STATUS, "ecoute sur %d", port);
    char rx[65536]; size_t fill = 0;
    for (;;) {
        int c = accept(srv, NULL, NULL);
        if (c < 0) { usleep(1000); continue; }   /* REVUE 17/08 : plus de boucle serree */
        setsockopt(c, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
        pthread_mutex_lock(&MU);
        if (CLIENT >= 0) close(CLIENT);
        CLIENT = c;
        char hello[64];
        int hl = snprintf(hello, sizeof hello, "HMT_SYNC %ld\n", LAST_DELIVERED);
        send(c, hello, hl, MSG_NOSIGNAL);
        pthread_mutex_unlock(&MU);
        fill = 0;
        for (;;) {
            ssize_t r = recv(c, rx + fill, sizeof rx - fill - 1, 0);
            if (r <= 0) break;
            fill += (size_t)r; rx[fill] = 0;
            char *nl;
            while ((nl = memchr(rx, '\n', fill))) {
                *nl = 0;
                if (rx[0] == 'c' && rx[1] == '|') {                    /* c|<n>|<payload> */
                    char *p2 = strchr(rx + 2, '|');
                    if (p2) store_cmd(atol(rx + 2), p2 + 1, (size_t)(nl - p2 - 1));
                }
                size_t rest = fill - (size_t)(nl - rx) - 1;
                memmove(rx, nl + 1, rest); fill = rest;
            }
            /* REVUE 17/08 : MAXCMD annonce 1 Mo mais rx ne fait que 64 Ko : au-dela on
             * jetait le DEBUT de la commande en cours, et la queue etait ensuite relue
             * comme de nouvelles lignes -> ecrasement d emplacements d anneau au hasard.
             * On compte la perte pour qu elle cesse d etre invisible. */
            if (fill > sizeof rx - 1024) { DROP_LINE++; fill = 0; }
        }
        pthread_mutex_lock(&MU);
        if (CLIENT == c) CLIENT = -1;
        pthread_mutex_unlock(&MU);
        close(c);
    }
    return NULL;
}

static void start_once(void) {
    pthread_t t, s;
    pthread_create(&t, NULL, listener, NULL);
    pthread_detach(t);
    pthread_create(&s, NULL, sender, NULL);          /* thread expéditeur */
    pthread_detach(s);
}

__attribute__((visibility("default"))) void RVExtensionVersion(char *output, int outputSize) {
    pthread_once(&ONCE, start_once);
    snprintf(output, (size_t)outputSize, "hmt_native 1.1 (pont TCP Harmattan, envoi non bloquant)");
}

__attribute__((visibility("default"))) void RVExtension(char *output, int outputSize, const char *function) {
    pthread_once(&ONCE, start_once);
    output[0] = 0;
    if (!function) return;
    if (!strncmp(function, "version", 7)) {
        /* REVUE 17/08 : « version » repondait depuis la memoire et ne disait RIEN de
         * l etat du socket. Elle porte desormais l etat du listener et les pertes. */
        snprintf(output, (size_t)outputSize,
                 "hmt_native 1.2 | %s | jetes ring=%ld send=%ld ligne=%ld",
                 STATUS, DROP_RING, DROP_SEND, DROP_LINE);
        return;
    }
    if (function[0] == 'o' && function[1] == '|') {        /* OUT : ENFILE (ne bloque JAMAIS le thread d'Arma) */
        out_enqueue(function + 2, strlen(function + 2));
        return;
    }
    if (function[0] == 'p' && function[1] == '|') {        /* POLL : chunks M|/D| */
        long n = atol(function + 2);
        pthread_mutex_lock(&MU);
        cmd_t *c = &CMDS[n % NCMD];
        if (c->buf && c->n == n) {
            /* REVUE 17/08 : `left = c->len - CUR_OFF` debordait quand la case avait ete
             * remplacee par une charge PLUS COURTE en cours de decoupage (reconnexion,
             * renvoi du meme n) -> memcpy hors bornes de ~10 Ko. */
            if (CUR_N != n || CUR_OFF > c->len) { CUR_N = n; CUR_OFF = 0; }
            size_t cap = (size_t)outputSize - 4;
            size_t left = c->len - CUR_OFF;
            size_t take = left < cap ? left : cap;
            int done = (take == left);
            output[0] = done ? 'D' : 'M'; output[1] = '|';
            memcpy(output + 2, c->buf + CUR_OFF, take); output[2 + take] = 0;
            CUR_OFF += take;
            if (done) { CUR_N = -1; CUR_OFF = 0; LAST_DELIVERED = n; }
        }
        pthread_mutex_unlock(&MU);
        return;
    }
}
