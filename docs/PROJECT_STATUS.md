# ServicePilot AI - Stato del progetto

Aggiornato: 10 agosto 2026

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
- API `POST /tickets`, `GET /tickets` e `GET /tickets/{ticket_id}` disponibili.
- Contratto di risposta completo e gestione esplicita delle risorse inesistenti.

## Milestone attiva

**Milestone 2 - Database e API essenziali**

## Ultima attività completata

**SP-022 - Creazione e lettura dei ticket**

È possibile creare un ticket confermato e leggere elenco o dettaglio tramite API REST.
Il backend controlla richiedente e sede, assegna stato e date, chiude correttamente le
sessioni del database e restituisce errori chiari per dati o risorse non validi.

## Prossima attività

**SP-023 - Gestione tecnica del ticket**

Risultato atteso:

- API per modificare i campi consentiti di un ticket;
- assegnazione a gruppo o tecnico e cambio di stato;
- gestione di modifiche, riferimenti e transizioni non valide.

## Blocchi o decisioni aperte

- Provider di deploy da decidere in una fase successiva.

## Come iniziare una nuova sessione

Prompt consigliato:

> Leggi `AGENTS.md` e `docs/PROJECT_STATUS.md`. Occupati della task SP-023.
> Prima spiegami in modo semplice cosa farai e perché. Alla fine esegui i controlli,
> aggiorna lo stato del progetto e mostrami le modifiche prima del commit.

Sostituire `SP-022` con il codice dell'attività successiva.

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
