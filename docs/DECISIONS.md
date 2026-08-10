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
