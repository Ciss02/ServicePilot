# ServicePilot AI

## Roadmap integrata di formazione e sviluppo - 4 settimane

Impegno previsto: 2 ore al giorno, 7 giorni a settimana
Totale disponibile: 56 ore
Obiettivo: una credenziale Microsoft, basi Python riattivate e un MVP pubblico presentabile

---

## 1. Strategia

Il percorso alterna studio e applicazione pratica. Ogni concetto appreso deve essere utilizzato nel progetto entro pochi giorni.

Ripartizione indicativa:

- 20 ore di formazione guidata;
- 31 ore di sviluppo e documentazione;
- 5 ore di revisione, recupero e preparazione della candidatura.

Non è realistico completare in quattro settimane un intero percorso avanzato di programmazione e contemporaneamente costruire un'applicazione completa. La priorità è:

1. completare la Microsoft Applied Skill su Power Automate;
2. seguire i moduli Python necessari al progetto;
3. pubblicare un MVP di ServicePilot funzionante e spiegabile;
4. proseguire la certificazione Python dopo la candidatura, se non ancora conclusa.

## 2. Formazione selezionata

### Percorso A - Python

Piattaforma: freeCodeCamp
Percorso: Python Certification
URL: https://www.freecodecamp.org/learn/python-v9

Argomenti prioritari:

- variabili e tipi;
- condizioni e cicli;
- funzioni;
- liste e dizionari;
- gestione degli errori;
- moduli e ambienti virtuali;
- file e JSON;
- programmazione a oggetti essenziale;
- test di base.

Obiettivo delle quattro settimane: acquisire le parti necessarie a comprendere e modificare ServicePilot. La certificazione completa è un obiettivo successivo se il percorso richiede più tempo.

### Percorso B - Power Automate

Piattaforma: Microsoft Learn
Learning path: Automate a business process using Power Automate
URL: https://learn.microsoft.com/en-us/training/paths/automate-process-power-automate/

Credenziale obiettivo:

Microsoft Applied Skills - Create and manage automated processes by using Power Automate
URL: https://learn.microsoft.com/en-us/credentials/applied-skills/create-and-manage-automated-processes-with-power-automate/

Argomenti:

- trigger e azioni;
- cloud flow;
- condizioni;
- approvazioni;
- gestione degli errori;
- monitoraggio;
- amministrazione dei flow.

### Percorso C - API e Microsoft Graph

Risorsa: tutorial ufficiale Microsoft
URL: https://learn.microsoft.com/en-us/graph/tutorials/python

Nelle quattro settimane questo tutorial è facoltativo. Deve essere affrontato solo se l'MVP è in linea con il piano. In caso contrario viene spostato alla quinta settimana.

### Percorso successivo - Copilot Studio

Credenziale futura:

Microsoft Applied Skills - Enhance agents with autonomous capabilities
URL: https://learn.microsoft.com/en-us/credentials/applied-skills/enhance-agents-with-autonomous-capabilities/

Non è la priorità iniziale. Richiede già dimestichezza con Copilot Studio, Power Automate e Dataverse.

---

## 3. Piano giornaliero

## Settimana 1 - Ripartenza con Python e fondazioni

Obiettivo: comprendere nuovamente il codice Python e avviare un progetto eseguibile.

### Giorno 1

Formazione - 60 minuti:

- configurare l'account freeCodeCamp;
- iniziare Python: variabili, tipi e operazioni;
- scrivere gli esercizi senza AI al primo tentativo.

Progetto - 60 minuti:

- creare il repository GitHub pubblico;
- aggiungere README provvisorio;
- inserire licenza, `.gitignore` e struttura iniziale;
- aggiungere la specifica MVP nella cartella `docs`.

Output: repository pubblico inizializzato.

### Giorno 2

Formazione - 75 minuti:

- condizioni;
- operatori logici;
- cicli.

Progetto - 45 minuti:

- installare Python;
- creare ambiente virtuale;
- installare FastAPI e Uvicorn;
- creare endpoint `/health`.

Output: server locale funzionante.

### Giorno 3

Formazione - 75 minuti:

- funzioni;
- parametri;
- valori restituiti;
- scope.

Progetto - 45 minuti:

- separare configurazione e applicazione;
- creare struttura `app/`;
- documentare i comandi di avvio.

Output: struttura backend comprensibile.

### Giorno 4

Formazione - 60 minuti:

- liste;
- tuple;
- set;
- dizionari.

Progetto - 60 minuti:

- definire categorie, stati e priorità;
- implementare la matrice impatto × urgenza come funzione Python;
- scrivere esempi di input e output.

Output: logica priorità deterministica.

### Giorno 5

Formazione - 60 minuti:

- file;
- JSON;
- gestione delle eccezioni.

Progetto - 60 minuti:

- creare i primi modelli Pydantic;
- validare creazione e aggiornamento dei ticket;
- verificare gli errori della richiesta.

Output: contratti dati iniziali.

### Giorno 6

Formazione - 45 minuti:

- ripasso degli argomenti;
- riscrivere una funzione senza consultare la soluzione.

Progetto - 75 minuti:

- configurare SQLAlchemy e SQLite;
- creare tabelle utenti, sedi e ticket;
- preparare dati seed sintetici.

Output: database locale iniziale.

### Giorno 7

Revisione - 60 minuti:

- spiegare a voce struttura, endpoint e funzione della priorità;
- annotare ciò che non è chiaro;
- correggere README e commenti.

Recupero - 60 minuti:

- completare le attività rimaste indietro;
- nessuna nuova funzionalità.

Checkpoint settimana 1:

- repository pubblico;
- applicazione avviabile;
- endpoint health;
- modelli dati;
- database;
- calcolo della priorità;
- almeno un commit significativo per giornata di sviluppo.

---

## Settimana 2 - API, database e autenticazione

Obiettivo: realizzare il flusso principale senza AI.

### Giorno 8

Formazione - 60 minuti:

- classi e oggetti in Python;
- differenza tra oggetto, modello e record.

Progetto - 60 minuti:

- implementare creazione e lettura dei ticket;
- verificare la documentazione OpenAPI automatica.

### Giorno 9

Formazione - 45 minuti:

- concetti REST;
- metodi HTTP;
- status code;
- payload JSON.

Progetto - 75 minuti:

- endpoint di modifica, assegnazione e cambio stato;
- gestione coerente degli errori.

### Giorno 10

Formazione - 60 minuti:

- password hashing;
- sessioni;
- autorizzazione per ruoli.

Progetto - 60 minuti:

- account demo;
- hashing delle password;
- login e logout.

### Giorno 11

Formazione - 45 minuti:

- principi minimi di sicurezza web;
- differenza tra autenticazione e autorizzazione.

Progetto - 75 minuti:

- permessi `employee`, `technician`, `admin`;
- impedire l'accesso ai ticket altrui;
- proteggere le funzioni amministrative.

### Giorno 12

Formazione - 45 minuti:

- template server-side;
- richieste HTMX.

Progetto - 75 minuti:

- layout Jinja;
- pagina login;
- dashboard dipendente.

### Giorno 13

Formazione - 30 minuti:

- ripasso HTML semantico e form.

Progetto - 90 minuti:

- form conversazionale iniziale;
- riepilogo dei dati;
- conferma prima della creazione.

La conversazione può essere inizialmente simulata con domande deterministiche. L'integrazione LLM arriverà dopo.

### Giorno 14

Revisione e test - 120 minuti:

- testare l'intero flusso senza AI;
- scrivere test per permessi e priorità;
- correggere errori;
- aggiornare README.

Checkpoint settimana 2:

- autenticazione funzionante;
- ruoli separati;
- CRUD essenziale dei ticket;
- dashboard dipendente;
- conferma prima della creazione;
- test iniziali.

---

## Settimana 3 - Power Automate, Gemini e RAG

Obiettivo: aggiungere le funzionalità che rendono il progetto realmente AI.

### Giorno 15

Formazione Microsoft Learn - 60 minuti:

- introduzione a Power Automate;
- trigger e azioni;
- primo cloud flow.

Progetto - 60 minuti:

- creare adapter LLM;
- configurare Gemini tramite variabile d'ambiente;
- creare un client di test isolato.

### Giorno 16

Formazione Microsoft Learn - 60 minuti:

- condizioni;
- espressioni;
- controlli del flusso.

Progetto - 60 minuti:

- estrazione strutturata dei dati dalla descrizione del ticket;
- validazione dell'output tramite Pydantic.

### Giorno 17

Formazione Microsoft Learn - 60 minuti:

- approval flow;
- gestione dell'approvazione e del rifiuto.

Progetto - 60 minuti:

- classificazione AI;
- verifica umana;
- salvataggio di proposta e correzione.

### Giorno 18

Formazione Microsoft Learn - 45 minuti:

- monitoraggio;
- gestione errori;
- retry.

Progetto - 75 minuti:

- upload sicuro di PDF e Markdown;
- estrazione e memorizzazione dei metadati.

### Giorno 19

Formazione - 30 minuti:

- concetti RAG: chunk, embedding, retrieval e grounding.

Progetto - 90 minuti:

- indicizzazione dei documenti;
- recupero dei passaggi pertinenti;
- gestione di una ricerca senza risultati.

### Giorno 20

Progetto - 120 minuti:

- generazione della soluzione;
- citazione di documento e sezione;
- avviso esplicito quando le fonti non sono sufficienti.

### Giorno 21

Revisione - 60 minuti:

- completare il learning path Power Automate;
- ripassare gli argomenti dell'assessment.

Test - 60 minuti:

- verificare classificazione, RAG e fallback;
- aggiungere casi di test con output AI simulati.

Checkpoint settimana 3:

- percorso Power Automate completato;
- Gemini integrato;
- classificazione strutturata;
- upload documenti;
- RAG con fonti;
- fallback sicuro.

---

## Settimana 4 - Azioni, credenziale, deploy e portfolio

Obiettivo: trasformare il prototipo in un progetto pubblico presentabile.

### Giorno 22

Formazione/valutazione - 120 minuti:

- sostenere la valutazione Microsoft Applied Skills su Power Automate;
- se non superata, annotare le aree deboli e programmare il nuovo tentativo.

### Giorno 23

Progetto - 120 minuti:

- API simulata per assegnazione;
- API simulata per comunicazione al dipendente;
- API simulata per escalation al fornitore.

### Giorno 24

Progetto - 120 minuti:

- schermata di approvazione;
- visualizzazione del payload;
- approvazione e rifiuto;
- gestione degli errori simulati.

### Giorno 25

Progetto - 120 minuti:

- audit log;
- filtri e pagina amministrativa;
- registrazione delle azioni AI e umane.

### Giorno 26

Qualità - 120 minuti:

- completare i test principali;
- configurare GitHub Actions;
- controllare segreti e `.env.example`;
- eseguire una revisione di sicurezza essenziale.

### Giorno 27

Deploy - 120 minuti:

- configurare database e applicazione sul provider scelto;
- creare account demo;
- impostare limiti alle chiamate AI;
- verificare ripristino del dataset;
- collaudare la demo da una sessione anonima.

### Giorno 28

Portfolio - 120 minuti:

- completare README bilingue;
- aggiungere diagramma architetturale e screenshot;
- registrare video demo di 2-3 minuti;
- descrivere limiti, sicurezza e sviluppi futuri;
- pubblicare release `v0.1.0`;
- aggiungere progetto e credenziale a LinkedIn.

Checkpoint finale:

- Applied Skill Power Automate ottenuta o nuovo tentativo già pianificato;
- MVP online;
- repository pubblico ordinato;
- test automatici;
- README bilingue;
- video demo;
- release GitHub.

---

## 4. Regole di utilizzo dell'AI durante lo sviluppo

Claude Code o Codex possono:

- proporre architettura;
- generare una prima implementazione;
- spiegare codice e messaggi di errore;
- suggerire test;
- eseguire revisioni.

Lorenzo deve:

- leggere ogni file prima del merge;
- chiedere la spiegazione delle parti non comprese;
- eseguire manualmente l'applicazione;
- modificare almeno una parte di ogni funzionalità;
- saper descrivere richiesta, elaborazione, database e risposta;
- evitare commit che non sa spiegare;
- tenere issue e pull request piccole;
- non pubblicare chiavi, dati o materiali aziendali.

Domande di controllo per ogni funzionalità:

1. Quale problema risolve?
2. Quali dati riceve?
3. Dove vengono validati?
4. Dove vengono salvati?
5. Cosa può fallire?
6. Chi è autorizzato a eseguirla?
7. Quale test dimostra che funziona?

## 5. Strategia GitHub

Branch:

- `main`: sempre funzionante;
- branch brevi `feature/...`, `fix/...`, `docs/...`.

Per ogni funzione:

1. aprire una issue;
2. creare un branch;
3. sviluppare e testare;
4. aprire una pull request;
5. descrivere cosa è cambiato e come è stato verificato;
6. eseguire merge.

Il repository deve mostrare un processo ordinato, non una sequenza di commit generati automaticamente.

## 6. Cosa inserire nel curriculum

Solo dopo il completamento:

### Progetto

**ServicePilot AI - Applicazione portfolio per la gestione intelligente dei ticket**

Progettazione e sviluppo assistito da AI di un'applicazione web con FastAPI, Jinja2 e database relazionale. Integrazione Gemini per classificazione strutturata e suggerimenti grounded su knowledge base PDF/Markdown; implementazione di API REST, autenticazione per ruoli, approvazione umana delle azioni e audit log. Pubblicazione di demo e repository documentato.

### Formazione

- Microsoft Applied Skills: Create and manage automated processes by using Power Automate - solo se ottenuta;
- Python Certification, freeCodeCamp - solo se completata;
- corsi Anthropic già completati.

Un corso iniziato ma non terminato non va presentato come certificazione. Può comparire su LinkedIn come formazione in corso, ma non è prioritario nel CV.

## 7. Piano di emergenza

Se il progetto accumula più di due giorni di ritardo:

1. mantenere autenticazione, ticket, classificazione, RAG e una sola azione approvabile;
2. rinviare due delle tre azioni simulate;
3. rinviare la funzione di reindicizzazione;
4. mantenere test, sicurezza, README e deploy;
5. non sacrificare la capacità di spiegare il codice per aggiungere funzioni.

Un MVP più piccolo, stabile e comprensibile vale più di una demo ampia ma fragile.
