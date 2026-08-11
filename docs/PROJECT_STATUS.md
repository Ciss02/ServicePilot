# ServicePilot AI - Stato del progetto

Aggiornato: 11 agosto 2026

Questo è il punto di ingresso rapido per ogni nuova sessione Codex.

## Stato attuale

- Git inizializzato localmente sul ramo `main`.
- Repository GitHub pubblica: `https://github.com/Ciss02/ServicePilot`.
- Primo commit della struttura iniziale pubblicato sul ramo `main`.
- Specifica MVP presente e approvata.
- Roadmap di apprendimento presente.
- Piano di progetto e regole di continuità creati.
- Struttura iniziale del repository completata con README, `.gitignore` e licenza MIT.
- Documentazione raccolta nella cartella `docs/`.
- Python 3.13.15 installato e ambiente locale `.venv` creato.
- Dipendenze iniziali definite e verificate.
- Prima applicazione FastAPI disponibile in `app/`.
- Endpoint `GET /health` implementato e verificato.
- Primo test automatico disponibile in `tests/`.
- Vocabolario del dominio centralizzato in `app/domain/vocabulary.py`.
- Ruoli, categorie, stati, impatto, urgenza e priorità documentati.
- Matrice deterministica della priorità implementata in `app/domain/priority.py`.
- Contratti Pydantic per creazione, classificazione e aggiornamento dei ticket.
- Database SQLite configurato tramite SQLAlchemy.
- Tabelle iniziali per utenti, sedi e ticket con vincoli e collegamenti essenziali.
- Dataset sintetico con 6 sedi, 5 profili e 6 ticket dimostrativi.
- Comando ripetibile per creare o riallineare i dati demo senza duplicarli.
- API `POST /tickets`, `GET /tickets`, `GET /tickets/{ticket_id}` e
  `PATCH /tickets/{ticket_id}` disponibili.
- Contratto di risposta completo e gestione esplicita delle risorse inesistenti.
- Modifica, classificazione, assegnazione e ciclo di vita tecnico dei ticket verificati.
- Account demo configurabili tramite variabili d'ambiente e hash Argon2 nel database.
- Modulo riutilizzabile per creare e verificare password senza conservarle in chiaro.
- Login degli account demo con errore uniforme per credenziali non valide.
- Sessioni autenticate revocabili, conservate nel database soltanto come impronte.
- Endpoint per leggere l'identità corrente e chiudere la sessione.
- API ticket protette da sessione autenticata e permessi applicati nel backend.
- Dipendenti limitati ai propri ticket; tecnico e admin abilitati alla gestione completa.
- Controlli riutilizzabili per funzioni tecniche e amministrative.
- Interfaccia web responsive con layout condiviso e pagina di accesso accessibile.
- Area di base protetta e uscita dal browser collegate alle sessioni esistenti.
- Area dipendente con riepilogo filtrabile, elenco e dettaglio dei ticket personali.
- Query di visibilità condivise tra API e pagine web, con proprietà filtrata nel backend.

## Milestone attiva

**Milestone 4 - Interfaccia completa senza AI**

## Ultima attività completata

**SP-041 - Area del dipendente**

Il dipendente vede in `/app` conteggi ed elenco delle sole richieste associate alla
propria sessione e può aprirne il dettaglio. Il filtro di proprietà avviene nella query
del backend ed è condiviso con le API. Ticket inesistenti e ticket altrui restituiscono
la stessa pagina `404` senza rivelare dati. Tecnico e amministratore restano sulla base
protetta in attesa della coda prevista da SP-044. I tre conteggi permettono di filtrare
l'elenco per richieste attive, in attesa del dipendente o completate.

## Prossima attività

**SP-042 - Raccolta guidata dei dati**

Risultato atteso:

- creare una conversazione inizialmente deterministica per descrivere il problema;
- chiedere in modo sintetico i dati essenziali ancora mancanti;
- non creare ancora il ticket prima del riepilogo e della conferma di SP-043.

## Blocchi o decisioni aperte

- Provider di deploy da decidere in una fase successiva.

## Come iniziare una nuova sessione

Prompt consigliato:

> Leggi `AGENTS.md` e `docs/PROJECT_STATUS.md`. Occupati della task SP-042.
> Prima spiegami in modo semplice cosa farai e perché. Alla fine esegui i controlli,
> aggiorna lo stato del progetto e mostrami le modifiche prima del commit.

Sostituire `SP-042` con il codice dell'attività successiva.

## Come chiudere una sessione

Prima di terminare verificare che:

1. l'attività concordata sia stata controllata;
2. la relativa casella in `PROJECT_PLAN.md` sia aggiornata;
3. questo documento indichi la prossima attività;
4. test eseguiti e problemi aperti siano annotati;
5. le modifiche Git siano state riepilogate.

## Ultima verifica eseguita

- Verificata la struttura dei file e la raggiungibilità dei documenti dal README.
- Verificato che `.gitignore` escluda `.env`, ambiente Python, database e file temporanei.
- Verificata l'assenza di chiavi, token e password nei file pubblicati.
- Verificata la pubblicazione del ramo `main` su GitHub.
- Verificati Python 3.13.15, pip 26.2.1 e il percorso utente di Python.
- Ricreato `.venv` da zero e installate le dipendenze da `requirements-dev.txt`.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificate FastAPI 0.141.1, Uvicorn 0.52.1, HTTPX2 2.7.0 e pytest 9.1.1.
- Verificata la sintassi dei file in `app/` e `tests/`.
- `pytest`: 41 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Avviato Uvicorn su `127.0.0.1:8000` e verificato `GET /health`: risposta `200 OK`
  con `{"status":"ok"}`.
- Arrestato il server locale dopo il controllo.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-010.
- Verificati 3 ruoli, 10 categorie, 6 stati, 3 livelli di impatto, 3 livelli di
  urgenza e 4 priorità.
- Verificate tutte le 9 combinazioni della matrice impatto × urgenza.
- Verificato che input non convertiti nel vocabolario vengano rifiutati chiaramente.
- Verificati contratti validi per creazione, classificazione e aggiornamento.
- Verificato il rifiuto di conferma falsa o ambigua, identificativi errati, campi
  sconosciuti, categorie non ammesse, priorità fornite dall'esterno e aggiornamenti vuoti.
- Verificata SQLAlchemy 2.0.51 nell'ambiente Python 3.13.
- Verificata la creazione ripetuta delle tabelle `users`, `sites` e `tickets`.
- Verificato il salvataggio di dati fittizi con stato iniziale `new` e codici stabili.
- Verificato il rifiuto di un ticket collegato a un richiedente inesistente.
- Eseguito due volte il comando `python -m app.db` su SQLite in memoria.
- `pytest`: 44 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificato il caricamento di 6 sedi, 5 profili e 6 ticket sintetici.
- Verificato che due caricamenti consecutivi non creino duplicati.
- Verificato che un nuovo caricamento ripristini i valori demo modificati.
- Verificato che record estranei al dataset non vengano cancellati.
- Verificata la corrispondenza tra impatto, urgenza e priorità di ogni ticket demo.
- Eseguito il comando `python -m app.db seed` su SQLite in memoria.
- `pytest`: 48 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata la creazione di un ticket confermato con risposta `201` e persistenza.
- Verificato che una conferma falsa non produca alcun ticket.
- Verificati errori `404` per richiedente, sede e ticket inesistenti.
- Verificato l'elenco dei ticket dal più recente e il dettaglio coerente con la creazione.
- Verificata la creazione automatica delle tabelle all'avvio dell'applicazione.
- `pytest`: 55 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata la modifica parziale dei campi consentiti senza cambiare il richiedente.
- Verificati classificazione e ricalcolo deterministico della priorità.
- Verificate assegnazioni soltanto a tecnici o amministratori attivi.
- Verificati avanzamento, attese, risoluzione, riapertura e chiusura finale del ticket.
- Verificato che soluzione assente, riferimenti errati e transizioni vietate non lascino
  aggiornamenti parziali.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-023.
- `pytest`: 84 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificati `pwdlib` 0.3.0 e Argon2 nell'ambiente Python 3.13.
- Verificato che la stessa password produca hash diversi e resti comunque verificabile.
- Verificato il rifiuto di credenziali demo mancanti o più corte di 12 caratteri senza
  mostrarne i valori negli errori.
- Verificato che tutti i 5 account demo conservino soltanto hash Argon2 e che un nuovo
  seed non rigeneri hash ancora validi.
- Verificata l'aggiunta ripetibile di `password_hash` a un vecchio database SQLite senza
  perdere il profilo già presente.
- Eseguito `python -m app.db seed` con credenziali casuali su SQLite in memoria.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-030.
- `pytest`: 96 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificato il login valido con un account demo attivo e hash Argon2.
- Verificato lo stesso errore per password errata, email inesistente e account inattivo.
- Verificato che il cookie sia `HttpOnly` e `SameSite=Lax` e che il database conservi
  soltanto l'impronta del codice casuale.
- Verificato il mantenimento dell'identità tra richieste successive.
- Verificati rifiuto e rimozione di sessioni scadute o collegate ad account disattivati.
- Verificato che il logout revochi la sessione, cancelli il cookie e sia ripetibile.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-031.
- `pytest`: 111 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificato che tutte le API ticket rifiutino sessioni assenti con `401`.
- Verificato che il richiedente venga ricavato dalla sessione e non sia accettato come
  dato libero nel corpo della creazione.
- Verificati elenco personale e dettaglio altrui nascosto per `employee`.
- Verificato il rifiuto con `403` della gestione tecnica da parte di `employee`.
- Verificate lettura e modifica dell'intera coda per `technician` e `admin`.
- Verificato il controllo amministrativo: `admin` accettato e `technician` rifiutato.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-032.
- `pytest`: 123 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificate Jinja2 3.1.6 e python-multipart 0.0.32 nell'ambiente Python 3.13.
- Verificati modulo di accesso, errore uniforme, cookie di sessione, pagina protetta e
  logout tramite test HTTP automatici.
- Verificato che la password errata non venga ripresentata nel documento HTML.
- Verificati layout e interazioni reali nel browser a 1440 × 900 e 390 × 844 pixel,
  senza scorrimento orizzontale o errori nella console.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-040.
- `pytest`: 130 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificato che l'elenco web del dipendente mostri soltanto i propri ticket, ordinati
  dal più recente.
- Verificati dettaglio personale, sede, categoria, priorità, tecnico, aggiornamento e
  soluzione quando disponibili.
- Verificato che ticket altrui e ticket inesistenti restituiscano la stessa pagina `404`
  senza titolo o descrizione riservati.
- Verificati stato vuoto, rinvio anonimo al login e separazione dalla futura coda tecnica.
- Verificati i filtri `active`, `waiting` e `completed`, il conteggio rispetto al totale
  e il ripristino dell'elenco completo.
- Provati nel browser i tre box cliccabili e “Mostra tutti”, senza errori nella pagina.
- Verificato che le API conservino lettura e gestione completa per tecnico e admin dopo
  l'estrazione delle query condivise.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-041.
- `pytest`: 140 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
