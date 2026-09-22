//! Le pont du monde : une extension Arma 3 ( `monde_x64.dll` ) qui relie un serveur Arma au cerveau du monde ( Python,
//! paquet `monde/` du depot ) par une connexion TCP locale.
//!
//! Sens cerveau -> Arma : le cerveau ecrit une ligne par lot d ordres ; l extension la POUSSE dans la mission par
//! `ExtensionCallback` ( nom "monde", fonction "ordres" ) - aucune attente, aucun fichier, aucune scrutation.
//! Sens Arma -> cerveau : la mission appelle `"monde" callExtension ["envoyer", [texte]]` ; l extension ecrit la ligne.
//!
//! Le cerveau est le SERVEUR ( il vit longtemps ) ; l extension est le CLIENT et se reconnecte seule si le cerveau
//! redemarre. Une ligne = un tableau au format « tableau simple » d Arma ( lisible par parseSimpleArray ).
//! Remplace, pour le monde, le pont par fichier sous Windows ( 0,5 s par echange, mesure du 11/09 ).

use arma_rs::{arma, Context, Extension};
use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::mpsc::{channel, Receiver, Sender};
use std::sync::{Mutex, OnceLock};
use std::time::Duration;

static ENVOI: OnceLock<Mutex<Option<Sender<String>>>> = OnceLock::new();
static CONNECTE: AtomicBool = AtomicBool::new(false);
static LANCE: AtomicBool = AtomicBool::new(false);
static ENVOYES: AtomicU64 = AtomicU64::new(0);
static RECUS: AtomicU64 = AtomicU64::new(0);
static POUSSES: AtomicU64 = AtomicU64::new(0);
static REPRISES: AtomicU64 = AtomicU64::new(0);
static PERDUS: AtomicU64 = AtomicU64::new(0);

#[arma]
fn init() -> Extension {
    Extension::build()
        .command("connecter", connecter)
        .command("envoyer", envoyer)
        .command("etat", etat)
        .finish()
}

/// `"monde" callExtension ["connecter", ["127.0.0.1", 2350]]` : lance ( une seule fois ) le fil de connexion.
fn connecter(ctx: Context, hote: String, port: u16) -> String {
    if LANCE.swap(true, Ordering::SeqCst) {
        return "deja".to_string();
    }
    let (tx, rx) = channel::<String>();
    *ENVOI.get_or_init(|| Mutex::new(None)).lock().unwrap() = Some(tx);
    std::thread::spawn(move || boucle(ctx, hote, port, rx));
    "ok".to_string()
}

/// La boucle de connexion : se connecte, lance le lecteur, ecrit ce que la mission envoie ; recommence si la
/// connexion tombe ( le cerveau a redemarre ).
fn boucle(ctx: Context, hote: String, port: u16, rx: Receiver<String>) {
    loop {
        match TcpStream::connect((hote.as_str(), port)) {
            Ok(flux) => {
                let _ = flux.set_nodelay(true);
                CONNECTE.store(true, Ordering::SeqCst);
                let lecture = match flux.try_clone() {
                    Ok(l) => l,
                    Err(_) => {
                        CONNECTE.store(false, Ordering::SeqCst);
                        continue;
                    }
                };
                let ctx_lecteur = ctx.clone();
                std::thread::spawn(move || lire(ctx_lecteur, lecture));
                let mut ecrivain = flux;
                // tant que la connexion vit : chaque texte recu de la mission devient une ligne
                loop {
                    match rx.recv_timeout(Duration::from_millis(500)) {
                        Ok(mut texte) => {
                            texte.push('\n');
                            if ecrivain.write_all(texte.as_bytes()).is_err() {
                                PERDUS.fetch_add(1, Ordering::SeqCst);
                                break;
                            }
                            ENVOYES.fetch_add(1, Ordering::SeqCst);
                        }
                        Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {
                            if !CONNECTE.load(Ordering::SeqCst) {
                                break; // le lecteur a vu la fin de la connexion
                            }
                        }
                        Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => return,
                    }
                }
                CONNECTE.store(false, Ordering::SeqCst);
                REPRISES.fetch_add(1, Ordering::SeqCst);
            }
            Err(_) => std::thread::sleep(Duration::from_secs(1)),
        }
    }
}

/// Le lecteur : chaque ligne du cerveau est poussee dans la mission. Si la file des rappels d Arma est pleine, on
/// attend et on reessaie - un ordre n est jamais jete en silence.
fn lire(ctx: Context, flux: TcpStream) {
    let lecteur = BufReader::new(flux);
    for ligne in lecteur.lines() {
        let ligne = match ligne {
            Ok(l) => l,
            Err(_) => break,
        };
        if ligne.is_empty() {
            continue;
        }
        RECUS.fetch_add(1, Ordering::SeqCst);
        let mut essais = 0;
        while ctx.callback_data("monde", "ordres", Some(ligne.clone())).is_err() {
            essais += 1;
            if essais > 200 {
                PERDUS.fetch_add(1, Ordering::SeqCst);
                break;
            }
            std::thread::sleep(Duration::from_millis(5));
        }
        if essais <= 200 {
            POUSSES.fetch_add(1, Ordering::SeqCst);
        }
    }
    CONNECTE.store(false, Ordering::SeqCst);
}

/// `"monde" callExtension ["envoyer", [texte]]` : une ligne vers le cerveau. Rend "ok", ou "deconnecte".
fn envoyer(texte: String) -> String {
    if !CONNECTE.load(Ordering::SeqCst) {
        PERDUS.fetch_add(1, Ordering::SeqCst);
        return "deconnecte".to_string();
    }
    let garde = ENVOI.get_or_init(|| Mutex::new(None)).lock().unwrap();
    match garde.as_ref() {
        Some(tx) if tx.send(texte).is_ok() => "ok".to_string(),
        _ => {
            PERDUS.fetch_add(1, Ordering::SeqCst);
            "deconnecte".to_string()
        }
    }
}

/// `"monde" callExtension ["etat", []]` : de quoi verifier le pont depuis la mission ou le journal.
fn etat() -> String {
    format!(
        "connecte={} envoyes={} recus={} pousses={} reprises={} perdus={}",
        CONNECTE.load(Ordering::SeqCst) as u8,
        ENVOYES.load(Ordering::SeqCst),
        RECUS.load(Ordering::SeqCst),
        POUSSES.load(Ordering::SeqCst),
        REPRISES.load(Ordering::SeqCst),
        PERDUS.load(Ordering::SeqCst)
    )
}
