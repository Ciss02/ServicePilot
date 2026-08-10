# ServicePilot AI - Registro delle decisioni

Questo documento conserva le decisioni che influenzano il progetto e il motivo per cui
sono state prese. Serve a evitare che una nuova sessione cambi direzione senza accorgersene.

## D-001 - Sistema di gestione del lavoro

**Data:** 10 agosto 2026
**Stato:** confermata

**Decisione proposta:**

- GitHub Issues e milestone diventeranno la vista principale del lavoro quando verrà
  creato il repository remoto.
- `docs/PROJECT_PLAN.md` conserverà la tasklist completa accanto al codice.
- `docs/PROJECT_STATUS.md` indicherà sempre la prossima attività.
- Notion sarà facoltativo e potrà essere usato per diario di apprendimento, materiali
  del portfolio e bozze più narrative.
- Slack non verrà usato nella fase iniziale perché il progetto è individuale.

**Motivazione:**

Codice, attività e storia delle modifiche restano vicini. Codex può leggere questi file
in ogni sessione senza dipendere dalla memoria della chat o da un servizio esterno.

## D-002 - Una attività principale per sessione

**Data:** 10 agosto 2026
**Stato:** confermata

**Decisione proposta:**

Ogni sessione Codex parte da un codice attività, per esempio `SP-011`, e cerca di
produrre un solo risultato verificabile. Attività indipendenti potranno essere eseguite
in parallelo soltanto quando il progetto sarà più maturo.

**Motivazione:**

Sessioni più piccole sono più facili da comprendere, verificare e correggere. Riducono
anche il rischio che il contesto della conversazione sostituisca i requisiti scritti.

## D-003 - Flusso completo prima dell'intelligenza artificiale

**Data:** 10 agosto 2026
**Stato:** già previsto dalla roadmap

**Decisione:**

Il flusso base dei ticket verrà completato senza AI. Classificazione, RAG e azioni
dell'agente saranno aggiunti dopo database, permessi e interfaccia essenziale.

**Motivazione:**

In questo modo gli errori dell'applicazione possono essere separati dagli errori o dalle
risposte imprevedibili del modello AI.

## D-004 - Licenza iniziale del repository

**Data:** 10 agosto 2026
**Stato:** confermata

**Decisione proposta:**

Usare la licenza MIT per il repository pubblico.

**Motivazione:**

È una licenza breve e permissiva, adatta a mostrare e condividere un progetto portfolio.
Consente anche il riuso del codice, purché venga mantenuto l'avviso di copyright.

## D-005 - Repository GitHub pubblico

**Data:** 10 agosto 2026
**Stato:** confermata

**Decisione:**

Pubblicare il progetto nella repository `https://github.com/Ciss02/ServicePilot` con
ramo principale `main`.

**Motivazione:**

Il repository pubblico rende visibili sia il risultato sia il processo di sviluppo e
permetterà di usare issue e milestone come tasklist operativa del portfolio.

## D-006 - Versione Python e dipendenze iniziali

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-002

**Decisione:**

- usare Python 3.13 per lo sviluppo dell'MVP;
- separare le dipendenze dell'applicazione in `requirements.txt` dagli strumenti di
  sviluppo in `requirements-dev.txt`;
- usare versioni esplicite delle dipendenze dirette;
- usare `httpx2` soltanto nello sviluppo per eseguire i test HTTP compatibili con la
  versione corrente di Starlette inclusa da FastAPI.

**Motivazione:**

Python 3.13 offre una base recente e stabile, con maggiore probabilità di compatibilità
con le future librerie AI rispetto all'adozione immediata della serie più nuova. La
separazione dei requisiti rende inoltre chiaro cosa serve al server e cosa serve soltanto
per sviluppare e verificare il progetto.

## D-007 - Vocabolario iniziale dei ticket

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-010

**Decisione:**

- usare codici interni in inglese, minuscoli e stabili, separati dalle etichette italiane;
- adottare gli stati `new`, `in_progress`, `waiting_for_requester`,
  `waiting_for_vendor`, `resolved` e `closed`;
- usare tre livelli sia per l'impatto sia per l'urgenza: `low`, `medium` e `high`;
- mantenere le quattro priorità `p1`, `p2`, `p3` e `p4` previste dalla specifica;
- definire in attività successive le transizioni tra stati e la matrice della priorità.

**Motivazione:**

La specifica stabilisce ruoli, categorie e priorità, ma non elenca tutti gli stati o i
livelli di impatto e urgenza. Un insieme piccolo copre il flusso MVP senza introdurre
complessità non ancora necessaria. I codici stabili potranno essere riutilizzati da API
e database, mentre l'interfaccia continuerà a mostrare termini italiani comprensibili.

## D-008 - Matrice deterministica della priorità

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-011

**Decisione:**

Usare la seguente matrice per calcolare la priorità:

| Impatto / Urgenza | Bassa | Media | Alta |
| --- | --- | --- | --- |
| Basso | P4 | P4 | P3 |
| Medio | P4 | P3 | P2 |
| Alto | P3 | P2 | P1 |

La funzione di calcolo accetta soltanto i valori `Impact` e `Urgency` già validati. Non
consulta il modello AI e non usa dati esterni.

**Motivazione:**

La matrice rende il risultato ripetibile e verificabile. P1 richiede contemporaneamente
impatto e urgenza alti; P2 rappresenta combinazioni alte e medie; P3 copre i casi
intermedi; P4 resta per richieste limitate o pianificabili. Questa scelta rispetta il
vincolo della specifica secondo cui l'AI può suggerire impatto e urgenza, ma non decide
liberamente la priorità.

## D-009 - Contratti dati del ticket

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-012

**Decisione:**

- usare Pydantic 2.13.4 come dipendenza diretta per i contratti applicativi;
- separare creazione, classificazione e aggiornamento in tre modelli;
- richiedere `confirmed=true` come valore booleano esplicito per la creazione;
- usare identificativi interi positivi per i riferimenti iniziali a richiedente, sede e
  tecnico;
- calcolare la priorità dalla classificazione senza accettarla come input;
- rifiutare campi sconosciuti e aggiornamenti senza valori;
- non permettere la modifica del richiedente tramite l'aggiornamento ordinario.

**Motivazione:**

La separazione segue il flusso della specifica: il dipendente conferma i dati essenziali,
la classificazione viene completata successivamente e il tecnico può modificare soltanto
campi esplicitamente previsti. Limiti e tipi rendono gli errori comprensibili prima del
salvataggio. La priorità resta sotto il controllo della matrice del backend e il
richiedente non può essere trasferito accidentalmente con una normale modifica.

## D-010 - Persistenza iniziale

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-020

**Decisione:**

- usare SQLAlchemy 2.0.51 come dipendenza diretta;
- usare SQLite locale tramite `sqlite:///./servicepilot.db` come configurazione
  predefinita;
- permettere la sostituzione dell'indirizzo con `SERVICEPILOT_DATABASE_URL`;
- creare le tabelle iniziali `users`, `sites` e `tickets`;
- conservare nel database i codici testuali del vocabolario, per esempio `employee` e
  `new`, con vincoli sui valori ammessi;
- mantenere facoltativa la classificazione al momento della nascita del ticket;
- rinviare migrazioni, password, dati demo, allegati e audit alle attività dedicate.

**Motivazione:**

SQLAlchemy separa il codice applicativo dal database specifico, mentre SQLite consente
di sviluppare la demo senza installare un server. La creazione basata sui metadati è
ripetibile e sufficiente per la struttura iniziale; un sistema di migrazioni sarà utile
quando dovremo modificare database già popolati, ma non è necessario per SP-020.

## D-011 - Dataset dimostrativo ripetibile

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-021

**Decisione:**

- creare 6 sedi sintetiche coerenti con sede centrale, stabilimento, magazzino e tre
  punti vendita della specifica;
- creare 5 profili che coprono i ruoli `employee`, `technician` e `admin`, senza
  password fino a SP-030;
- creare 6 ticket dimostrativi con scenari, stati e priorità differenti;
- identificare chiaramente i dati con codici `-DEMO`, email nel dominio riservato
  `.example` e titoli `[DEMO]`;
- riconoscere sedi, utenti e ticket tramite chiavi stabili e aggiornare i record demo
  esistenti senza duplicarli;
- non cancellare record estranei al dataset;
- calcolare le priorità con la matrice deterministica già approvata.

**Motivazione:**

Un dataset stabile rende schermate e test riproducibili tra sessioni. L'aggiornamento
mirato è più sicuro di una cancellazione completa e permette di ricaricare gli esempi
senza perdere eventuali dati locali non dimostrativi. I marcatori visibili e il dominio
`.example` evitano di confondere gli esempi con persone o sistemi reali.

## D-012 - API essenziali dei ticket

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-022

**Decisione:**

- esporre `POST /tickets`, `GET /tickets` e `GET /tickets/{ticket_id}`;
- usare `TicketCreate` per l'ingresso e un contratto separato `TicketRead` per la
  risposta completa;
- creare un ticket soltanto con `confirmed=true` e con richiedente e sede esistenti;
- assegnare al backend ID, stato iniziale `new` e date;
- lasciare vuota la classificazione iniziale, coerentemente con il flusso approvato;
- restituire `404` per risorse non esistenti, `422` per dati non validi e `409` quando
  il database rifiuta i riferimenti durante il salvataggio;
- ordinare l'elenco dal ticket più recente;
- creare le tabelle mancanti all'avvio dell'applicazione;
- rinviare autenticazione, autorizzazione, paginazione e modifica alle attività dedicate.

**Motivazione:**

Contratti distinti impediscono al client di scegliere campi gestiti dal backend. Le
verifiche dei riferimenti producono errori comprensibili prima del vincolo del database,
mentre la transazione evita salvataggi parziali. L'applicazione è ora utilizzabile per
il flusso base senza anticipare regole di sicurezza non ancora implementate.

## D-013 - Gestione tecnica e ciclo di vita del ticket

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-023

**Decisione:**

- esporre `PATCH /tickets/{ticket_id}` per aggiornamenti parziali validati;
- permettere la correzione dei dati tecnici previsti da `TicketUpdate`, mantenendo il
  richiedente non modificabile;
- ricalcolare sempre la priorità da impatto e urgenza quando cambia la classificazione;
- accettare come assegnatari soltanto utenti attivi con ruolo `technician` o `admin`;
- usare il percorso `new → in_progress → attesa o resolved → closed`, permettendo il
  ritorno a `in_progress` dagli stati di attesa e da `resolved`;
- considerare `closed` uno stato finale e richiedere una soluzione prima di risolvere o
  chiudere un ticket;
- restituire `404` per riferimenti assenti, `409` per transizioni in conflitto e `422`
  per dati validi nella forma ma non utilizzabili nella gestione tecnica;
- rinviare il controllo di chi può chiamare l'endpoint a SP-032.

**Motivazione:**

Un ciclo di vita esplicito impedisce salti accidentali e rende ogni comportamento
testabile. La soluzione obbligatoria conserva l'esito prima della chiusura. I controlli
eseguiti prima di modificare il modello e il commit unico evitano dati salvati a metà.
La separazione dall'autorizzazione mantiene SP-023 concentrata sulle regole del ticket,
mentre la milestone successiva proteggerà le operazioni in base all'utente autenticato.
