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
