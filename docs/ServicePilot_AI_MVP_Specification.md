# ServicePilot AI

## Specifica MVP / MVP Specification

Versione: 0.1
Stato: requisiti iniziali approvati
Lingua dell'interfaccia: italiano
Documentazione: italiano e inglese

---

## 1. Obiettivo

ServicePilot AI è un'applicazione dimostrativa per la gestione intelligente delle richieste IT in una PMI multisede con uffici, stabilimento produttivo, magazzino e punti vendita.

L'applicazione permette ai dipendenti di aprire ticket tramite una conversazione guidata e ai tecnici IT di gestire la coda, consultare suggerimenti basati sulle procedure aziendali e approvare azioni proposte dall'agente.

Il progetto deve dimostrare:

- analisi e digitalizzazione di un processo aziendale;
- sviluppo di un'applicazione web interna;
- progettazione e utilizzo di API REST;
- persistenza dei dati;
- integrazione con un modello LLM;
- Retrieval-Augmented Generation (RAG);
- tool calling con approvazione umana;
- autenticazione e autorizzazione per ruoli;
- tracciabilità delle operazioni;
- utilizzo professionale di GitHub e documentazione tecnica.

## 2. Contesto aziendale fittizio

La demo rappresenta un'azienda sintetica composta da:

- una sede centrale;
- uno stabilimento produttivo;
- un magazzino;
- tre punti vendita;
- utenti in presenza e da remoto;
- fornitori IT esterni.

Tutti i nomi, gli utenti, le sedi, i ticket e le procedure utilizzati nella demo devono essere fittizi.

## 3. Ruoli

### 3.1 Dipendente

Può:

- autenticarsi con un account dimostrativo;
- aprire una richiesta tramite chat guidata;
- aggiungere informazioni e allegati;
- confermare i dati prima della creazione del ticket;
- consultare esclusivamente i propri ticket;
- leggere stato, aggiornamenti e soluzione finale;
- rispondere alle richieste di ulteriori informazioni.

### 3.2 Tecnico IT

Può:

- visualizzare la coda dei ticket;
- filtrare e ordinare i ticket;
- consultare categoria, impatto, urgenza e priorità suggeriti;
- correggere la classificazione proposta;
- assegnare un ticket;
- consultare la soluzione suggerita dall'AI;
- controllare le fonti recuperate dalla knowledge base;
- approvare o rifiutare le azioni proposte;
- aggiornare stato e note;
- risolvere e chiudere il ticket.

### 3.3 Amministratore

Possiede i permessi del tecnico e può inoltre:

- caricare procedure PDF e Markdown;
- visualizzare, eliminare e reindicizzare i documenti;
- ripristinare il dataset dimostrativo;
- consultare l'audit log completo.

## 4. Flusso di apertura del ticket

1. Il dipendente descrive liberamente il problema.
2. L'agente estrae le informazioni disponibili.
3. L'agente pone domande sintetiche per acquisire i dati mancanti.
4. Il sistema mostra un riepilogo strutturato.
5. Il dipendente conferma o corregge la richiesta.
6. Il backend crea il ticket.
7. L'AI propone categoria, sottocategoria, impatto, urgenza e gruppo di assegnazione.
8. La priorità viene calcolata da regole deterministiche.
9. Il tecnico verifica e, se necessario, modifica la classificazione.

Il modello non può creare un ticket senza la conferma del dipendente.

## 5. Dati principali del ticket

- identificativo;
- titolo;
- descrizione;
- richiedente;
- sede;
- categoria;
- sottocategoria;
- servizio coinvolto;
- numero di utenti coinvolti;
- impatto operativo;
- urgenza dichiarata;
- priorità calcolata;
- gruppo e tecnico assegnati;
- stato;
- allegati;
- soluzione proposta;
- azioni proposte;
- fonti della knowledge base;
- date di creazione e aggiornamento;
- cronologia e audit trail.

## 6. Categorie iniziali

- Account e accessi
- Dispositivi e hardware
- Software e applicazioni
- Rete e connettività
- Stampanti ed etichettatura
- Telefonia
- Sistemi di negozio
- Sistemi produttivi
- Sicurezza informatica
- Altre richieste

## 7. Priorità

La priorità non deve essere decisa liberamente dal modello. L'AI estrae impatto e urgenza dal testo; il backend applica una matrice deterministica.

Livelli:

- P1 - Critica
- P2 - Alta
- P3 - Media
- P4 - Bassa

Esempi:

- fermo di un sistema produttivo o indisponibilità di rete in un'intera sede: P1;
- servizio essenziale bloccato per più utenti senza alternativa: P2;
- problema individuale con impatto lavorativo e soluzione temporanea: P3;
- richiesta informativa o attività pianificabile: P4.

Il tecnico deve poter correggere impatto, urgenza e priorità, indicando facoltativamente una motivazione.

## 8. Knowledge base e RAG

L'amministratore può caricare file PDF e Markdown.

Pipeline:

1. validazione del file;
2. estrazione del testo;
3. suddivisione in segmenti;
4. generazione degli embedding;
5. indicizzazione;
6. recupero dei passaggi pertinenti;
7. generazione della risposta con riferimenti alle fonti.

Procedure dimostrative iniziali:

- problemi Wi-Fi;
- reset e sblocco account;
- installazione software;
- configurazione stampanti;
- problemi con stampanti Zebra;
- accesso VPN;
- onboarding di un dispositivo;
- escalation di un sistema produttivo;
- supporto a un punto vendita;
- possibile incidente di sicurezza.

Requisiti:

- la risposta deve indicare documento e sezione utilizzati;
- l'agente deve dichiarare quando non dispone di informazioni sufficienti;
- il sistema non deve presentare come certe informazioni non presenti nelle fonti;
- eliminazione e reindicizzazione sono riservate all'amministratore.

## 9. Azioni dell'agente

L'agente può proporre:

1. assegnazione del ticket a un tecnico o gruppo;
2. invio di una comunicazione al dipendente;
3. creazione di un'escalation verso un fornitore esterno.

Le azioni sono implementate come chiamate REST verso servizi simulati.

Vincoli:

- nessuna azione viene eseguita senza approvazione esplicita del tecnico;
- il tecnico vede payload, motivazione ed effetto previsto;
- approvazione, rifiuto, esecuzione ed esito vengono registrati;
- i servizi devono simulare anche errori per dimostrare la gestione delle eccezioni.

## 10. Autenticazione e autorizzazione

- account dimostrativi preconfigurati;
- ruoli `employee`, `technician`, `admin`;
- password memorizzate mediante hashing robusto;
- sessioni autenticate;
- verifica dei permessi nel backend;
- nessuna registrazione pubblica;
- nessun recupero password nell'MVP;
- il dipendente non può accedere ai ticket altrui;
- le operazioni amministrative sono protette.

## 11. Architettura proposta

### Backend

- Python;
- FastAPI;
- API REST documentate tramite OpenAPI;
- SQLAlchemy;
- SQLite in sviluppo;
- possibilità di PostgreSQL in produzione.

### Frontend

- Jinja2;
- HTMX;
- CSS leggero o Tailwind CSS;
- layout responsive.

### AI

- Gemini come provider iniziale;
- adapter indipendente dal provider;
- chiave API tramite variabili d'ambiente;
- output strutturati e validati;
- timeout, retry controllati e gestione degli errori.

### RAG

- estrazione PDF e Markdown;
- indicizzazione locale o database vettoriale leggero;
- metadati di documento e sezione;
- citazioni visibili nell'interfaccia.

### Qualità

- pytest;
- dati seed;
- logging strutturato;
- audit log;
- file `.env.example`;
- linting e formattazione;
- GitHub Actions per test automatici.

## 12. Demo pubblica

- account demo per i tre ruoli;
- dati sintetici precompilati;
- nessuna registrazione libera;
- banner che identifica il progetto come demo;
- limitazione delle chiamate AI;
- protezione dei segreti lato server;
- funzione di ripristino del dataset;
- gestione sicura degli upload;
- nessun riferimento a dati o sistemi dell'attuale datore di lavoro.

## 13. Fuori perimetro MVP

- integrazione reale con Active Directory o Microsoft Entra ID;
- integrazione reale con ServiceDesk Plus;
- invio di email reali;
- Microsoft Graph;
- single sign-on;
- applicazione mobile;
- SLA complessi;
- sincronizzazione con inventari aziendali reali;
- azioni remote sui dispositivi;
- multi-tenancy.

Questi elementi potranno essere descritti come possibili evoluzioni, non come funzionalità già implementate.

## 14. Criteri di completamento

L'MVP è pronto per il portfolio quando:

- un dipendente apre e conferma un ticket tramite chat;
- il sistema classifica il ticket e calcola la priorità;
- un tecnico può correggere e assegnare il ticket;
- l'AI propone una soluzione con fonti verificabili;
- il tecnico può approvare almeno una delle tre azioni simulate;
- ogni passaggio rilevante compare nell'audit log;
- l'amministratore può caricare e indicizzare una procedura;
- i ruoli impediscono accessi non autorizzati;
- i test principali vengono eseguiti automaticamente;
- la demo pubblica è ripristinabile;
- il repository contiene README bilingue, screenshot, architettura, istruzioni di avvio, limiti e roadmap.

## 15. Presentazione nel portfolio

Il progetto deve essere accompagnato da:

- descrizione del problema aziendale;
- utenti e bisogni;
- diagramma dell'architettura;
- demo pubblica utilizzabile;
- video dimostrativo facoltativo;
- schermate dei flussi principali;
- decisioni tecniche e alternative considerate;
- sezione sicurezza e privacy;
- test e controlli implementati;
- limiti noti;
- sviluppi futuri;
- dichiarazione trasparente sull'utilizzo di strumenti AI durante lo sviluppo.

Per la versione `v0.1.0` il video è stato reso facoltativo: demo online, schermate reali,
README bilingue e documento di architettura costituiscono il materiale di presentazione
principale. La scelta e la motivazione sono registrate in `DECISIONS.md`.

## 16. Evoluzione approvata v0.2.0

L'MVP descritto nelle sezioni precedenti resta la baseline pubblicata come `v0.1.0`.
La prossima versione estende il prodotto senza riscrivere retroattivamente i criteri con
cui l'MVP è stato completato.

La `v0.2.0` comprende:

- agente conversazionale persistente con diagnosi preventiva prudente;
- allegati sicuri e richieste condizionali di screenshot, foto o log;
- thread pubblico cronologico tra richiedente e supporto;
- conferma del dipendente, riapertura e chiusura automatica del ticket;
- gruppi amministrabili, sotto-attività, worklog, timer e notifiche interne;
- apertura per conto del dipendente;
- procedure versionate, editor Markdown e conversione controllata dei PDF;
- apprendimento mediato da revisione amministrativa;
- dashboard amministrativa ed esportazioni CSV.

Le decisioni trasversali, i limiti e il comportamento atteso sono descritti in
[`V020_PRODUCT_PLAN.md`](V020_PRODUCT_PLAN.md). La sequenza implementativa ufficiale è
in [`PROJECT_PLAN.md`](PROJECT_PLAN.md) e nelle issue GitHub `SP-090`-`SP-133`.

---

# English Summary

ServicePilot AI is a portfolio application for intelligent IT service-request management in a fictional multi-site company with offices, manufacturing, warehousing, and retail locations.

Employees submit requests through a guided conversational interface. The system extracts missing information, requires confirmation, creates the ticket, proposes classification and impact, and calculates priority using deterministic business rules.

Technicians review the ticket, correct AI suggestions, retrieve grounded troubleshooting guidance from an uploaded knowledge base, and approve simulated actions. Supported actions include assignment, user notification, and vendor escalation. No action is executed without explicit human approval, and all decisions are recorded in an audit log.

The proposed stack is Python, FastAPI, Jinja2, HTMX, SQLAlchemy, SQLite/PostgreSQL, Gemini through a provider-independent adapter, document ingestion for PDF and Markdown files, and automated testing with pytest and GitHub Actions.

The public demo uses synthetic data, preconfigured accounts, protected secrets, AI rate limits, role-based authorization, and a resettable dataset.
