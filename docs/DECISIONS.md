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

## D-014 - Credenziali demo e hashing delle password

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-030

**Decisione:**

- usare `pwdlib` 0.3.0 con l'algoritmo raccomandato Argon2;
- isolare creazione e verifica degli hash in `app/security/passwords.py`;
- richiedere una password di almeno 12 caratteri per ciascun ruolo demo tramite le
  variabili `SERVICEPILOT_DEMO_EMPLOYEE_PASSWORD`,
  `SERVICEPILOT_DEMO_TECHNICIAN_PASSWORD` e `SERVICEPILOT_DEMO_ADMIN_PASSWORD`;
- lasciare vuoti i valori in `.env.example` e non inserire password predefinite nel
  repository;
- condividere la credenziale `employee` tra i tre dipendenti sintetici e usare valori
  separati per tecnico e amministratore;
- conservare nel database soltanto `password_hash`, rigenerandolo solo quando la
  credenziale configurata non corrisponde più;
- mantenere temporaneamente facoltativa la colonna per i record locali precedenti e
  aggiungerla in modo compatibile ai database SQLite già creati;
- rinviare autenticazione e sessioni a SP-031.

**Motivazione:**

Argon2 è progettato per rendere costosi i tentativi ripetuti di indovinare una password,
mentre `pwdlib` offre un'interfaccia moderna compatibile con Python 3.13. Le variabili
d'ambiente separano i segreti dal codice pubblico. Il controllo prima della transazione
evita dataset parziali e l'aggiornamento mirato della tabella preserva il lavoro locale
senza introdurre in questa fase un intero sistema di migrazioni.

## D-015 - Sessioni autenticate revocabili

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-031

**Decisione:**

- esporre `POST /auth/login`, `GET /auth/session` e `POST /auth/logout`;
- accettare soltanto account esistenti e attivi con password Argon2 valida;
- restituire lo stesso errore per email sconosciuta, password errata e account inattivo;
- generare per ogni login un codice casuale valido otto ore;
- inviare il codice in un cookie `HttpOnly` e `SameSite=Lax`, attivando `Secure` tramite
  `SERVICEPILOT_SECURE_COOKIES=true` negli ambienti HTTPS;
- conservare in `auth_sessions` soltanto l'impronta SHA-256 del codice, l'utente e la
  scadenza;
- rimuovere dal database sessioni scadute, riferite ad account inattivi o chiuse con il
  logout;
- mantenere il logout ripetibile anche quando la sessione manca;
- rinviare l'uso dell'identità per proteggere le API a SP-032 e la pagina login a SP-040.

**Motivazione:**

Una sessione conservata lato server può essere revocata immediatamente al logout e non
richiede una chiave di firma aggiuntiva. Il browser possiede il solo codice utilizzabile,
mentre una copia del database contiene un'impronta che non può essere usata direttamente
come cookie. Otto ore coprono una giornata dimostrativa senza creare sessioni permanenti.
La separazione dall'autorizzazione mantiene SP-031 concentrata sul riconoscimento
dell'utente e lascia a SP-032 regole di accesso verificabili in modo autonomo.

## D-016 - Autorizzazione backend e proprietà dei ticket

**Data:** 10 agosto 2026
**Stato:** confermata durante SP-032

**Decisione:**

- richiedere una sessione valida per tutte le API dei ticket;
- ricavare sempre il richiedente dalla sessione e rifiutare `requester_id` nel corpo;
- permettere a ogni account attivo di creare soltanto ticket propri;
- filtrare elenco e dettaglio di `employee` in base alla proprietà;
- restituire `404` quando un dipendente richiede il dettaglio di un ticket altrui;
- permettere a `technician` e `admin` di leggere l'intera coda;
- riservare `PATCH /tickets/{ticket_id}` a `technician` e `admin`;
- distinguere sessione non valida (`401`) da ruolo insufficiente (`403`);
- preparare controlli riutilizzabili per utente autenticato, ruolo tecnico e solo admin;
- non creare endpoint amministrativi fittizi prima delle attività che li richiedono.

**Motivazione:**

I permessi nel backend restano efficaci anche se una persona chiama direttamente l'API.
Derivare il richiedente dalla sessione elimina la possibilità di dichiarare un'altra
identità nel corpo della richiesta. Il `404` sui ticket altrui non rivela informazioni
sulla loro esistenza. Controlli condivisi evitano di riscrivere regole diverse in ogni
endpoint e preparano le future funzioni amministrative mantenendo SP-032 nel suo
perimetro.

## D-017 - Interfaccia server-rendered e accesso web

**Data:** 11 agosto 2026
**Stato:** confermata durante SP-040

**Decisione:**

- usare `Jinja2 3.1.6` per produrre HTML dal backend e `python-multipart 0.0.32` per
  leggere i moduli;
- creare un layout comune con HTML semantico e un foglio di stile locale responsive;
- esporre `/login`, `/app` e `/logout`, mantenendo separate e disponibili le API JSON;
- riutilizzare lo stesso servizio per verifica delle credenziali, creazione della
  sessione e gestione del cookie nei flussi API e web;
- mostrare un errore generico per qualsiasi accesso non valido e non ripresentare la
  password nel documento HTML;
- non aggiungere JavaScript o HTMX finché una funzionalità interattiva non lo richiede;
- mantenere `/app` come sola base protetta e rinviare elenco e dettaglio ticket a
  SP-041;
- rinviare pubblicazione e configurazione dell'ambiente ospitato a SP-082.

**Motivazione:**

Il rendering sul server produce una prima interfaccia semplice da capire e verificare,
senza duplicare nel browser le regole di autenticazione. I servizi condivisi impediscono
che API e pagine applichino controlli differenti. HTML semantico, uso da tastiera e
adattamento allo schermo piccolo rendono la base riutilizzabile per le prossime pagine,
mentre l'assenza di JavaScript evita complessità che il modulo di accesso non richiede.

## D-018 - Visibilità condivisa e area personale dei ticket

**Data:** 11 agosto 2026
**Stato:** confermata durante SP-041

**Decisione:**

- estrarre le query di elenco e dettaglio in un modulo condiviso da API e pagine web;
- aggiungere sempre il richiedente alla query quando il ruolo è `employee`;
- restituire la stessa pagina `404` per ticket inesistente e ticket di un altro
  dipendente;
- mostrare in `/app` conteggi ed elenco personale ordinato dal più recente;
- esporre `/app/tickets/{ticket_id}` come dettaglio di sola lettura;
- rendere i tre conteggi filtri server-side tramite il parametro `filter`, mantenendo
  invariati i conteggi complessivi e senza aggiungere stato nel browser;
- caricare in gruppo i nomi di sedi e tecnici necessari alla presentazione;
- convertire codici di stato, categoria e priorità in etichette italiane fuori dai
  modelli persistenti;
- mantenere tecnico e amministratore sulla base provvisoria fino a SP-044;
- non aggiungere tabelle, dipendenze, JavaScript o funzioni di creazione ticket.

**Motivazione:**

Filtrare direttamente nel database evita che dati non autorizzati raggiungano il
template. La query condivisa mantiene identica la regola tra API e interfaccia. La
risposta `404` non conferma l'esistenza di ticket altrui, mentre la separazione dei testi
grafici dai codici persistenti conserva stabile il vocabolario del dominio. La pagina
resta concentrata sulla consultazione richiesta da SP-041 senza anticipare raccolta,
conferma o coda tecnica.

## D-019 - Bozza temporanea e raccolta guidata deterministica

**Data:** 11 agosto 2026
**Stato:** confermata durante SP-042

**Decisione:**

- esporre il percorso dipendente in `/app/new-ticket` con due invii successivi;
- chiedere prima una descrizione libera e poi titolo, sede, servizio e persone coinvolte;
- applicare nel backend gli stessi limiti dei contratti del ticket;
- accettare soltanto sedi attive lette dal database;
- ricontrollare anche i valori trasportati in campi nascosti;
- mantenere la bozza soltanto nei moduli tra un passaggio e il successivo;
- non creare né salvare ticket durante SP-042;
- riservare il percorso al ruolo `employee`;
- non introdurre JavaScript, HTMX, nuove dipendenze o nuove tabelle;
- rinviare riepilogo, correzione, conferma e persistenza a SP-043.

**Motivazione:**

La sequenza rende il modulo più facile da completare e dimostra già il comportamento
conversazionale senza simulare capacità AI non ancora presenti. Una bozza temporanea è
sufficiente per due richieste consecutive e impedisce di confonderla con un ticket
ufficiale. La validazione ripetuta evita di fidarsi dei dati modificabili nel browser;
la persistenza verrà introdotta soltanto insieme alla conferma esplicita prevista dalla
specifica.

## D-020 - Conferma esplicita e creazione ripetibile

**Data:** 11 agosto 2026
**Stato:** confermata durante SP-043

**Decisione:**

- mostrare tutti i dati raccolti prima della creazione;
- permettere correzione e annullamento senza conservare una bozza nel database;
- creare il ticket soltanto con una conferma positiva inviata dal pulsante dedicato;
- ricontrollare dati, sede attiva e conferma nel backend;
- usare la stessa funzione di creazione per API e interfaccia web;
- associare al riepilogo un codice casuale univoco, conservato nel ticket;
- in caso di doppio invio, restituire il ticket già collegato a quel codice;
- aggiornare in modo ripetibile anche i database SQLite creati prima di SP-043;
- non aggiungere dipendenze o JavaScript.

**Motivazione:**

Il riepilogo rende consapevole la decisione del dipendente e rispetta il vincolo che
impedisce al sistema di creare richieste autonomamente. La funzione condivisa evita
regole diverse tra pagina e API. Il codice univoco protegge dai duplicati causati da un
doppio clic o dal reinvio del modulo, senza salvare bozze non confermate.

## D-021 - Coda tecnica e gestione web condivisa

**Data:** 11 agosto 2026
**Stato:** confermata durante SP-044

**Decisione:**

- mostrare a `technician` e `admin` l'intera coda in `/app`;
- offrire filtri server-side per stato, assegnazione e priorità e ordinamenti per
  priorità, data di apertura o ultimo aggiornamento;
- riutilizzare `/app/tickets/{ticket_id}` con una vista diversa in base al ruolo;
- mantenere nel dettaglio tecnico assegnazione, classificazione, stato, nota e soluzione;
- mostrare soltanto i passaggi di stato consentiti dal punto corrente;
- calcolare sempre la priorità a partire da impatto e urgenza;
- usare una singola funzione di aggiornamento per API e pagine web;
- non aggiungere JavaScript, nuove dipendenze o nuove tabelle.

**Motivazione:**

Una coda ordinata per priorità porta subito l'attenzione sui ticket più importanti,
mentre i filtri permettono di isolare il proprio lavoro o le richieste ancora senza
responsabile. La pagina del ticket concentra tutte le operazioni manuali necessarie al
ciclo di vita MVP. La funzione condivisa impedisce che browser e API applichino regole
diverse; i controlli nel backend restano efficaci anche se il modulo viene alterato.

## D-022 - Adapter AI sostituibile e disattivato per impostazione predefinita

**Data:** 11 agosto 2026
**Stato:** confermata durante SP-050

**Decisione:**

- usare `google-genai` 2.13.0, SDK ufficiale compatibile con Python 3.13;
- usare `gemini-3.5-flash-lite` come modello predefinito configurabile;
- esporre al progetto un solo contratto per generare risposte strutturate;
- richiedere sempre uno schema Pydantic e ricontrollare la risposta nel backend;
- leggere provider, modello, chiave e limiti soltanto dalle variabili d'ambiente;
- mantenere l'AI disattivata quando il provider non viene scelto esplicitamente;
- limitare timeout, tentativi e lunghezza massima della risposta;
- usare client simulati nei test senza chiamate Gemini reali;
- non collegare ancora l'adapter alla raccolta guidata o alla persistenza.

**Motivazione:**

Il contratto comune separa le regole del portale dal servizio esterno e permette test
veloci, gratuiti e ripetibili. La risposta strutturata riduce l'ambiguità, ma il controllo
Pydantic resta necessario perché il modello può comunque produrre valori non validi.
La configurazione disattivata mantiene il portale avviabile senza segreti o rete, mentre
i limiti impediscono attese e tentativi eccessivi. Il collegamento al flusso utente viene
rinviato alle issue che definiscono dati estratti, classificazione e gestione visibile
degli errori.

## D-023 - Estrazione prudente e campi mancanti calcolati dal backend

**Data:** 11 agosto 2026
**Stato:** confermata durante SP-051

**Decisione:**

- inviare al modello la descrizione e soltanto codice e nome delle sedi attive;
- richiedere titolo, codice sede, servizio e persone coinvolte in uno schema rigido;
- usare `null` quando un dato non è ricavabile senza supposizioni;
- generare un titolo breve fedele alla descrizione, senza classificare il ticket;
- accettare una sede soltanto se corrisponde a una delle opzioni fornite dal backend;
- calcolare nel backend, e non nel modello, l'elenco esatto dei campi mancanti;
- mostrare soltanto i campi mancanti e passare direttamente al riepilogo se il risultato
  è completo;
- conservare il percorso manuale quando l'AI è disattivata o produce un errore controllato;
- non salvare descrizione, prompt o bozza prima della conferma esplicita;
- usare modelli simulati nei test senza chiamate esterne.

**Motivazione:**

Il modello riduce il lavoro del dipendente, ma ogni dato continua a passare attraverso
regole deterministiche del backend. Limitare la scelta delle sedi evita che una risposta
plausibile ma inventata diventi un identificativo valido. Calcolare localmente i campi
mancanti impedisce contraddizioni tra dati e domande successive. Il percorso manuale
mantiene l'applicazione utilizzabile anche senza configurare Gemini.

## D-024 - Classificazione AI controllata e priorità deterministica

**Data:** 12 agosto 2026
**Stato:** confermata durante SP-052

**Decisione:**

- classificare soltanto ticket già creati dopo la conferma del dipendente;
- inviare titolo, descrizione, servizio, persone coinvolte e sede confermati;
- limitare categoria, impatto e urgenza al vocabolario del dominio;
- limitare il gruppo a sette opzioni fittizie definite nel backend;
- accettare una sottocategoria breve oppure `null`;
- vietare campi aggiuntivi nella risposta, inclusa la priorità;
- calcolare sempre la priorità tramite la matrice deterministica esistente;
- salvare la proposta nei campi già presenti del ticket;
- non richiamare il modello quando la classificazione è già completa;
- conservare il ticket non classificato se il provider non è disponibile;
- rinviare messaggi di errore e revisione esplicita del tecnico a SP-053.

**Motivazione:**

L'AI riduce il lavoro iniziale del tecnico, ma non deve introdurre codici o gruppi
arbitrari né decidere la priorità. Separare prima la creazione e poi la classificazione
garantisce che un problema esterno non faccia perdere una richiesta già confermata. Il
riuso dei campi esistenti mantiene la modifica piccola e compatibile con il database.
