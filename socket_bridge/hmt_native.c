/* hmt_native.c — extension NATIVE Linux pour le serveur dédié Arma 3 (harnais de mesure Harmattan).
 *
 * BUT : remplacer le pont fichier+RPT (cmd_N.sqf + diag_log/parsing de log) par un canal TCP en mémoire.
 *   IN  : Python envoie  "c|<n>|<sqf, \n encodés en \x01>\n"  -> stocké en RAM.
 *         L'actuateur SQF poll : "hmt_native" callExtension "p|<n>" -> chunks "M|..."/"D|..." ("" si absent).
 *   OUT : le SQF émet      : "hmt_native" callExtension "o|<ligne>" -> forward TCP immédiat vers Python.
 *   SYNC: à la connexion, l'extension envoie "HMT_SYNC <dernier n délivré>" (reprise propre par op).
 *
 * Sécurité de process : MSG_NOSIGNAL partout (un client mort ne doit JAMAIS tuer le serveur Arma),
 * un seul client à la fois (le harnais), listener lazy au premier appel, port = env HMT_EXT_PORT (déf. 5801).
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

static pthread_mutex_t MU = PTHREAD_MUTEX_INITIALIZER;
static pthread_once_t ONCE = PTHREAD_ONCE_INIT;
static int CLIENT = -1;
static long LAST_DELIVERED = 0;   /* dernier n entièrement remis au SQF (D|) */
static long CUR_N = -1; static size_t CUR_OFF = 0;   /* état de chunking */

typedef struct { long n; char *buf; size_t len; } cmd_t;
static cmd_t CMDS[NCMD];

static void store_cmd(long n, const char *payload, size_t len) {
    if (len > MAXCMD) return;
    pthread_mutex_lock(&MU);
    cmd_t *c = &CMDS[n % NCMD];
    free(c->buf);
    c->buf = malloc(len + 1);
    memcpy(c->buf, payload, len); c->buf[len] = 0;
    /* dé-encapsule \x01 -> \n */
    for (size_t i = 0; i < len; i++) if (c->buf[i] == '\x01') c->buf[i] = '\n';
    c->n = n; c->len = len;
    pthread_mutex_unlock(&MU);
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
    if (bind(srv, (struct sockaddr*)&a, sizeof a) || listen(srv, 1)) return NULL;
    char rx[65536]; size_t fill = 0;
    for (;;) {
        int c = accept(srv, NULL, NULL);
        if (c < 0) continue;
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
            if (fill > sizeof rx - 1024) fill = 0;   /* ligne géante -> on jette (garde-fou) */
        }
        pthread_mutex_lock(&MU);
        if (CLIENT == c) CLIENT = -1;
        pthread_mutex_unlock(&MU);
        close(c);
    }
    return NULL;
}

static void start_once(void) {
    pthread_t t;
    pthread_create(&t, NULL, listener, NULL);
    pthread_detach(t);
}

__attribute__((visibility("default"))) void RVExtensionVersion(char *output, int outputSize) {
    pthread_once(&ONCE, start_once);
    snprintf(output, (size_t)outputSize, "hmt_native 1.0 (pont TCP Harmattan)");
}

__attribute__((visibility("default"))) void RVExtension(char *output, int outputSize, const char *function) {
    pthread_once(&ONCE, start_once);
    output[0] = 0;
    if (!function) return;
    if (!strncmp(function, "version", 7)) {
        snprintf(output, (size_t)outputSize, "hmt_native 1.0");
        return;
    }
    if (function[0] == 'o' && function[1] == '|') {        /* OUT : forward au client */
        pthread_mutex_lock(&MU);
        if (CLIENT >= 0) {
            send(CLIENT, function + 2, strlen(function + 2), MSG_NOSIGNAL);
            send(CLIENT, "\n", 1, MSG_NOSIGNAL);
        }
        pthread_mutex_unlock(&MU);
        return;
    }
    if (function[0] == 'p' && function[1] == '|') {        /* POLL : chunks M|/D| */
        long n = atol(function + 2);
        pthread_mutex_lock(&MU);
        cmd_t *c = &CMDS[n % NCMD];
        if (c->buf && c->n == n) {
            if (CUR_N != n) { CUR_N = n; CUR_OFF = 0; }
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
