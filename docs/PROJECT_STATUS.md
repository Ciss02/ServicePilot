# ServicePilot AI - Stato del progetto

Aggiornato: 13 agosto 2026

Questo è il punto di ingresso rapido per ogni nuova sessione Codex.

## Stato attuale

### Evoluzione v0.2.0 pianificata

- La release stabile pubblicata resta `v0.1.0`; la prima base tecnica della v0.2 è
  implementata localmente ma non ancora pubblicata.
- Approvata la roadmap completa descritta in
  [`V020_PRODUCT_PLAN.md`](V020_PRODUCT_PLAN.md).
- Le milestone GitHub 0-8 sono state chiuse perché già completate nella release MVP.
- Create le milestone GitHub 9-13 e le 22 issue da `SP-090` a `SP-133`.
- Ogni issue contiene obiettivo, modifiche, dipendenze, rischi, criteri di accettazione e
  verifiche.
- **SP-090 - Migrazioni versionate per la v0.2** è completata e pubblicata su `main`.
- **SP-091 - Gruppi di supporto e appartenenze** è completata e pubblicata su `main`.
- **SP-092 - Allegati sicuri** è completata e verificata localmente sulla base di SP-091,
  senza anticipare le funzioni di SP-093.
- La roadmap verrà implementata una issue e una pull request alla volta; il codice della
  `v0.2.0` non è stato anticipato durante la pianificazione.

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
- Raccolta guidata deterministica con descrizione libera e richiesta dei dati mancanti.
- Bozza temporanea validata senza creazione del ticket prima della conferma.
- Riepilogo completo con correzione, annullamento e conferma esplicita.
- Creazione web condivisa con l'API e protetta dai doppi invii accidentali.
- Coda tecnica completa con filtri per stato, assegnazione e priorità.
- Dettaglio operativo per tecnico e amministratore con assegnazione, classificazione,
  note, soluzione e avanzamento controllato.
- Aggiornamento condiviso tra pagine web e API con ricalcolo deterministico della priorità.
- Adapter AI sostituibile con Gemini 3.5 Flash-Lite come modello configurabile.
- Configurazione AI esterna, disattivata per impostazione predefinita e protetta da
  timeout, tentativi e limite di output.
- Risposte strutturate ricontrollate da Pydantic e testabili senza chiamate AI reali.
- Estrazione AI di titolo, sede, servizio e persone coinvolte dalla descrizione libera.
- Campi mancanti calcolati dal backend e richiesti singolarmente nel percorso web.
- Passaggio diretto al riepilogo quando l'estrazione è completa, senza creare il ticket.
- Raccolta manuale ancora disponibile quando il provider AI è disattivato.
- Classificazione AI controllata di categoria, sottocategoria, impatto, urgenza e gruppo.
- Gruppi di supporto fittizi limitati a un vocabolario esplicito.
- Priorità della proposta calcolata esclusivamente dalla matrice del backend.
- Classificazione salvata dopo la conferma, senza duplicare chiamate su ticket completi.
- Stato persistente che distingue proposta AI, verifica umana e fallimenti controllati.
- Conferma tecnica esplicita con correzione e nuovo calcolo deterministico della priorità.
- Messaggi visibili per provider non disponibile e risposta AI non valida.
- Area amministrativa per caricare e consultare i documenti della knowledge base.
- Upload limitato a PDF e Markdown, con massimo 5 MB e controllo del contenuto reale.
- File conservati con nome interno casuale in una cartella esclusa da Git.
- Metadati persistenti con nome originale, formato, dimensione, impronta e autore.
- Pulizia automatica dei file temporanei o definitivi quando il salvataggio fallisce.
- Estrazione locale del testo dai documenti Markdown e dai PDF con testo selezionabile.
- Titoli Markdown conservati come percorso di sezione e pagine PDF come fonte stabile.
- Segmenti fino a 1.200 caratteri con sovrapposizione, ordine e documento di origine.
- Stato persistente dell'estrazione con conteggio visibile nella knowledge base.
- Sostituzione atomica dei segmenti che evita duplicati e risultati parziali.
- Adapter embedding separato e sostituibile con Gemini disattivato per impostazione
  predefinita.
- Configurazione di `gemini-embedding-001` con 768 dimensioni e chiave soltanto locale.
- Vettori normalizzati e persistenti con modello, dimensione, stato e data dell'indice.
- Ricerca semantica ordinata per similarità con documento, sezione e testo originali.
- Laboratorio amministrativo per provare domande tecniche senza generare risposte AI.
- Generazione tecnica RAG avviata soltanto su richiesta di tecnico o amministratore.
- Suggerimento AI separato dalla soluzione finale e salvato insieme alle fonti citate.
- Documento, sezione, passaggio e punteggio visibili nel dettaglio del ticket.
- Citazioni inventate rifiutate e suggerimenti invalidati se una procedura viene
  rielaborata.
- Stop prudenziale prima di Gemini quando non esistono fonti o nessuna raggiunge la
  soglia iniziale di similarità `0,55`.
- Risultati deboli esclusi dal contesto del modello e messaggio operativo mostrato al
  tecnico senza modificare la soluzione finale.
- Tre tipi controllati di azione proposta: assegnazione, comunicazione al richiedente ed
  escalation verso un fornitore fittizio.
- Motivazione, payload specifico, effetto previsto e stato `pending_approval` salvati in
  una tabella separata senza applicare modifiche al ticket.
- Applicazione FastAPI separata con servizi REST fittizi per assegnazione, comunicazione
  al richiedente ed escalation al fornitore.
- Successi `200` ed errori demo `503` deterministici, con riferimenti stabili e senza
  effetti reali, persistenza o esposizione nelle rotte del portale.
- Tre proposte completamente fittizie disponibili nel dataset demo, una per tipo di
  azione, ripristinate in attesa senza duplicati.
- Sezione tecnica con motivazione, payload, effetto previsto e stato di ogni proposta.
- Approvazione o rifiuto espliciti riservati a tecnico e amministratore nel backend.
- Decisione salvata prima dell'esecuzione e chiamata REST singola soltanto dopo
  l'approvazione, con doppio invio bloccato.
- Decisore, data, riferimento, messaggio o errore del simulatore conservati e visibili.
- Registro append-only con eventi umani, AI e automatici collegati ai ticket.
- Salvataggio dell'evento nella stessa transazione dell'operazione principale.
- Dettagli minimizzati senza password, chiavi, prompt, note o soluzioni complete.
- Timeline cronologica disponibile nel dettaglio tecnico di ogni ticket.
- Vista complessiva degli ultimi 100 eventi, con filtri, riservata all'amministratore.
- Nove eventi iniziali fittizi caricati in modo ripetibile senza duplicati.
- Rielaborazione amministrativa dei documenti con sostituzione di segmenti e indice.
- Eliminazione controllata delle fonti e invalidazione dei suggerimenti che le citano.
- Ripristino completo dei dati operativi tramite la frase `RIPRISTINA DEMO`.
- Reset atomico di ticket, azioni, audit e knowledge base con account e sessione
  amministrativa conservati.
- Formattazione Python uniforme e controllo degli import tramite Ruff 0.16.2.
- Workflow GitHub Actions su pull request e ramo `main` con installazione pulita,
  controllo delle dipendenze, lint, formattazione e test senza chiamate AI reali.
- Revisione della sicurezza pubblica documentata per segreti, upload, sessioni, browser
  e consumo AI, con limiti residui dichiarati.
- Modalità demo pubblica che richiede cookie HTTPS e host esplicitamente ammessi.
- Controllo dell'origine sugli invii browser e intestazioni CSP, anti-frame, `nosniff`,
  referrer, permessi, cache e HSTS.
- Login limitato a 10 tentativi al minuto per client e massimo 20 sessioni attive per
  account, con pulizia automatica di quelle scadute.
- Chiamate AI ed embedding condivise sotto un tetto locale di 10 al minuto e 100 al
  giorno, applicato prima di costruire il client esterno.
- Testo documentale limitato a 500.000 caratteri estratti e 500 segmenti prima degli
  embedding.
- Demo pubblica su Render Free nella regione di Francoforte, disponibile tramite HTTPS
  su `https://servicepilot-ai-demo-ciss02.onrender.com`.
- Avvio coordinato in una sola istanza del portale pubblico e del simulatore azioni,
  raggiungibile soltanto su `127.0.0.1`.
- Dataset SQLite temporaneo ricreato automaticamente prima dell'avvio, con ripristino
  amministrativo verificato a 6 ticket, 3 azioni e 9 eventi iniziali.
- Compatibilità Gemini 3.5 Flash-Lite verificata tramite JSON Schema standard e chiamata
  reale con dati esclusivamente fittizi.
- README portfolio completo in italiano e inglese con demo, funzioni, avvio locale,
  sicurezza, limiti e roadmap.
- Architettura documentata con componenti, flussi, confini di sicurezza e scelte di
  deploy.
- Cinque schermate reali prodotte da un dataset temporaneo esclusivamente sintetico.
- Indice completo della documentazione con separazione tra guide tecniche attuali e
  registri storici.
- Revisionati 26 documenti tecnici per eliminare riferimenti operativi alle vecchie
  issue e descrivere le funzionalità nello stato realmente disponibile.
- Release stabile [`v0.1.0`](https://github.com/Ciss02/ServicePilot/releases/tag/v0.1.0)
  pubblicata da `main` con funzioni, controlli e limiti documentati.
- Video dimostrativo reso facoltativo: demo online, screenshot, README e architettura
  costituiscono il materiale principale del portfolio.

## Milestone completata

**Milestone 8 - Qualità, pubblicazione e portfolio**

## Milestone pianificata corrente

**Milestone 9 - Modello operativo e collaborazione**

## Ultima attività completata

**SP-092 - Allegati sicuri**

Archivio privato riutilizzabile per ticket, bozze e messaggi, con contesto controllato,
nomi casuali, controlli reali dei contenuti e download autorizzato. Il primo collegamento
web è il dettaglio ticket; le future issue useranno gli stessi servizi per bozze e messaggi.

## Prossima attività

**SP-093 - Comunicazioni cronologiche sul ticket.** Introdurre il thread pubblico
append-only per richiedente e supporto, riusando gli allegati autorizzati di SP-092.

## Blocchi o decisioni aperte

- Il piano Render Free spegne il servizio dopo inattività e non conserva SQLite o file
  caricati; questa perdita controllata è accettata soltanto per la demo portfolio.

## Come iniziare una nuova sessione

Prompt consigliato:

> Leggi `AGENTS.md`, `docs/PROJECT_STATUS.md` e `docs/PROJECT_PLAN.md`. L'MVP è completo:
> procedi con SP-093 seguendo la relativa issue GitHub. Spiegami in modo semplice cosa
> farai e perché, senza anticipare le issue successive.

## Come chiudere una sessione

Prima di terminare verificare che:

1. l'attività concordata sia stata controllata;
2. la relativa casella in `PROJECT_PLAN.md` sia aggiornata;
3. questo documento indichi la prossima attività oppure che l'MVP è completo;
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
- Verificato che la raccolta chieda prima la descrizione e poi soltanto titolo, sede,
  servizio e numero di persone coinvolte.
- Verificati limiti dei campi, messaggi di errore e nuovo controllo dei dati trasportati
  tra i passaggi.
- Verificato che sedi disattivate non compaiano nell'elenco e siano rifiutate anche se
  inviate manualmente.
- Verificato che visitatori anonimi e tecnici non accedano al percorso dipendente.
- Verificato che una raccolta valida non crei alcun ticket prima di SP-043.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-042.
- `pytest`: 149 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificato che il riepilogo mostri tutti i dati raccolti senza creare ticket.
- Verificato che correzione e annullamento non modifichino il database.
- Verificata la creazione di un ticket soltanto con conferma esplicita positiva.
- Verificato che due invii con lo stesso codice riportino allo stesso ticket senza
  duplicarlo.
- Verificato che una sede disattivata dopo il riepilogo venga rifiutata alla conferma.
- Verificato che tutti i passaggi di raccolta, correzione e conferma restino riservati
  al dipendente.
- Verificati il messaggio di successo, il collegamento al dipendente e lo stato iniziale
  `new`.
- Verificato l'aggiornamento ripetibile dei database SQLite esistenti con il codice di
  creazione univoco, senza perdere ticket locali.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-043.
- `pytest`: 161 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificato che tecnico e amministratore vedano l'intera coda e il dettaglio completo.
- Verificati filtri per stato, assegnazione e priorità, insieme ai quattro ordinamenti.
- Verificati assegnazione a un account tecnico attivo e rifiuto del ruolo dipendente.
- Verificata la correzione manuale di categoria, impatto e urgenza con priorità ricalcolata.
- Verificato dal browser il percorso `new → in_progress → resolved → closed` con
  soluzione obbligatoria e senza aggiornamenti parziali in caso di errore.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-044.
- Verificata l'evidenziazione visiva del riepilogo tecnico realmente selezionato.
- Verificata la vista predefinita “Aperti” e la selezione dei riepiloghi senza salti
  nella pagina, conservando priorità e ordinamento scelti.
- `pytest`: 172 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata la configurazione AI disattivata senza chiave e l'attivazione esplicita di
  Gemini soltanto con `GEMINI_API_KEY` presente.
- Verificato che la chiave non compaia nelle rappresentazioni o nei messaggi di errore.
- Verificati modello configurabile, timeout di 15 secondi, massimo 2 tentativi e limite
  di 1024 token di output.
- Verificato l'uso di uno schema Pydantic e il rifiuto di risposte vuote o non valide.
- Verificata la sostituzione completa di Gemini con client simulati senza accesso alla rete.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-050.
- `pytest`: 186 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata l'estrazione strutturata di titolo, sede, servizio e persone coinvolte.
- Verificato che il backend calcoli esattamente i campi ancora mancanti.
- Verificato il passaggio diretto al riepilogo con un risultato completo.
- Verificata la richiesta dei soli dati mancanti con un risultato incompleto.
- Verificati il rifiuto di sedi non disponibili e di risposte fuori contratto.
- Verificato che il percorso manuale resti disponibile con provider disattivato.
- Verificata l'assenza di creazioni ticket prima della conferma esplicita.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-051.
- `pytest`: 192 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata la proposta controllata di categoria, sottocategoria, impatto, urgenza e
  gruppo di assegnazione.
- Verificato il rifiuto di valori sconosciuti e di una priorità inviata dal modello.
- Verificato il calcolo deterministico della priorità a partire da impatto e urgenza.
- Verificato il salvataggio della classificazione dopo la conferma web e tramite API.
- Verificato che un ticket già classificato non produca una seconda chiamata AI.
- Verificato che un provider disattivato lasci il ticket creato e utilizzabile.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-052.
- `pytest`: 201 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificati gli stati persistenti `pending`, proposta AI, verifica umana, provider non
  disponibile e risposta non valida.
- Verificato che timeout e risposte non valide conservino il ticket senza applicare
  campi non controllati e senza ripetere automaticamente la chiamata.
- Verificate correzione e conferma esplicita da pagina web e API tecnica.
- Verificato che una classificazione incompleta non possa essere confermata.
- Verificato il nuovo calcolo della priorità dopo la correzione del tecnico.
- Verificato l'aggiornamento ripetibile del database SQLite locale senza perdita di dati.
- Verificati nel browser proposta, conferma e messaggio di revisione senza errori nella
  console; server locale aggiornato su `127.0.0.1:8010`.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-053.
- `pytest`: 213 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificati upload validi di PDF e Markdown con nome interno casuale, impronta SHA-256
  e metadati collegati all'amministratore.
- Verificato il rifiuto senza modifiche parziali di estensioni non ammesse, PDF finti,
  tipi incoerenti, Markdown binari, file vuoti e documenti oltre 5 MB.
- Verificato che un errore del database rimuova anche il file già scritto.
- Verificato che dipendenti e tecnici non possano aprire la pagina né caricare file.
- Verificata nel browser integrato l'area amministrativa responsive con navigazione,
  regole di sicurezza, modulo di upload e archivio vuoto; server aggiornato su
  `127.0.0.1:8010`.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-060.
- `pytest`: 228 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata l'estrazione locale di testo selezionabile da PDF reali e Markdown UTF-8.
- Verificati riferimenti `Pagina N`, titoli Markdown annidati e collegamento al documento.
- Verificata la suddivisione dei testi lunghi entro 1.200 caratteri con sovrapposizione.
- Verificati stato `ready` o `failed`, assenza di righe parziali e rielaborazione senza
  duplicati.
- Verificato l'aggiornamento ripetibile di un database precedente senza perdere i
  metadati del documento già presente.
- Verificato il flusso web con elaborazione immediata e conteggio reale dei segmenti.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-061.
- `pytest`: 235 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata la configurazione embedding disattivata senza chiave e attivabile
  separatamente con Gemini.
- Verificati modello `gemini-embedding-001`, 768 dimensioni predefinite, timeout e
  tentativi controllati.
- Verificati i compiti distinti `RETRIEVAL_DOCUMENT` e `RETRIEVAL_QUERY` senza chiamate
  esterne nei test.
- Verificati rifiuto di vettori mancanti, non numerici, non finiti, vuoti o di dimensione
  errata.
- Verificata l'indicizzazione completa senza risultati parziali e lo stato `pending`
  quando il provider è disattivato.
- Verificato che una domanda sulla connessione remota recuperi per prima la procedura
  VPN mantenendo documento, sezione e testo.
- Verificata la compatibilità ripetibile con database creati nelle sessioni precedenti.
- Verificato il laboratorio web con risultati ordinati e messaggio controllato quando
  gli embedding sono disattivati.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-062.
- `pytest`: 259 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata la generazione strutturata da ticket e massimo tre passaggi recuperati.
- Verificato che il backend accetti soltanto identificativi di fonti realmente fornite.
- Verificato il salvataggio atomico di suggerimento, ordine delle fonti e punteggi.
- Verificato che il suggerimento non modifichi stato né soluzione finale del tecnico.
- Verificati accesso di tecnico e amministratore e rifiuto del ruolo dipendente.
- Verificata l'invalidazione dei suggerimenti quando una procedura citata viene
  rielaborata.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-063.
- `pytest`: 267 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificato che una ricerca senza risultati non chiami il modello e non salvi fonti.
- Verificato che risultati tutti sotto la soglia `0,55` fermino la generazione prima di
  Gemini e rimuovano eventuali suggerimenti non più sostenuti.
- Verificato che soltanto i risultati sopra soglia vengano inclusi nel contesto AI.
- Verificato il messaggio web che invita il tecnico a controllare il ticket o aggiungere
  una procedura più specifica.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-064.
- `pytest`: 270 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificati i tre tipi controllati di azione e i relativi payload specifici.
- Verificato il rifiuto di motivazioni, effetti, destinazioni e tipi non validi.
- Verificato che ogni nuova proposta nasca in stato `pending_approval`.
- Verificato che lo stato iniziale non possa essere fornito o alterato dall'esterno.
- Verificato che salvare assegnazione, comunicazione o escalation non modifichi alcun
  campo operativo del ticket e non esegua servizi esterni.
- Verificati collegamento obbligatorio a un ticket, rollback e lettura controllata del
  payload JSON, inclusa la gestione di dati corrotti.
- Verificata la creazione ripetibile di `proposed_actions` anche su un database locale
  precedente senza perdita dei ticket esistenti.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-070.
- `pytest`: 291 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificati i successi ripetibili dei tre servizi REST simulati con riferimenti stabili.
- Verificati errori `503` intenzionali e identici su assegnazione, comunicazione ed
  escalation, senza dipendere dal caso o da servizi esterni.
- Verificati il rifiuto `422` di UUID, identificativi, payload e campi inattesi non
  validi.
- Verificato che gli endpoint simulati non siano inclusi nell'applicazione del portale.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-071.
- `pytest`: 305 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificati rifiuto, ruolo dipendente e riferimento ticket errato senza alcuna chiamata
  al servizio simulato.
- Verificato che `approved` ed `executing` siano persistenti prima della singola chiamata
  REST e che un secondo invio non la ripeta.
- Verificati successo, errore `503`, simulatore irraggiungibile e risposta controllata
  senza modificare stato, assegnazione o soluzione del ticket.
- Verificati decisore, data, riferimento, messaggio e codice di errore persistenti.
- Verificate tre proposte demo ripetibili senza duplicati e migrazione dei database
  locali precedenti senza perdita delle righe esistenti.
- Verificata nel browser la chiamata reale portale `8010` → simulatore `8011`, con
  riferimento di esecuzione visibile e dati demo poi ripristinati.
- Verificato il layout a 390 × 844 senza scorrimento orizzontale e senza errori nella
  console; pagina lasciata aperta nel browser integrato sul ticket `SP-0001`.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-072.
- `pytest`: 324 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata la creazione atomica degli eventi insieme a ticket, modifiche,
  classificazioni, suggerimenti e azioni.
- Verificato che operazioni rifiutate o non autorizzate non aggiungano eventi falsi.
- Verificata la sequenza proposta, approvazione, avvio ed esito, incluso il riferimento
  restituito dal simulatore locale.
- Verificati dettagli minimizzati e blocco di modifica o cancellazione tramite ORM.
- Verificati i 9 eventi demo iniziali e il caricamento ripetuto senza duplicati.
- Verificate timeline tecnica, pagina amministrativa, filtri e permessi nel browser.
- Verificato il layout a 390 × 844 senza scorrimento orizzontale della pagina.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-073.
- `pytest`: 330 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificate rielaborazione e sostituzione dei segmenti senza duplicati.
- Verificata l'eliminazione di fonte, file e riferimenti AI derivati.
- Verificati conferma obbligatoria e rifiuto di dipendente e tecnico.
- Verificato il reset atomico a 6 ticket, 3 azioni e 9 eventi iniziali.
- Verificate conservazione della sessione amministrativa e pulizia dei file caricati.
- Verificata la sintassi di tutti i file in `app/` e `tests/` dopo SP-074.
- `pytest`: 335 test superati senza avvisi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Verificata la configurazione Ruff su 139 file Python con controllo degli errori e
  ordinamento degli import.
- Verificata la formattazione uniforme di tutti i file Python del repository.
- Verificato il workflow GitHub Actions con Python 3.13, permessi di sola lettura,
  limite di tempo e annullamento delle esecuzioni superate sullo stesso ramo.
- Ricreato un secondo ambiente virtuale vuoto e installato soltanto
  `requirements-dev.txt`.
- Nell'ambiente pulito, `pip check`, Ruff e formattazione sono passati.
- Nell'ambiente pulito, `pytest -W error`: 335 test superati senza avvisi.
- Verificato che `.env`, database e archivio documentale restino esclusi da Git.
- Verificata l'assenza di pattern noti di chiavi Gemini, token GitHub e chiavi private nei
  file pubblicabili.
- Verificati limiti AI condivisi al minuto e al giorno, incluso il blocco prima della
  costruzione del client esterno.
- Verificati limite login, pulizia e massimo delle sessioni, host e origine ammessi,
  intestazioni di sicurezza e obbligo dei cookie HTTPS nella modalità pubblica.
- Verificato il rifiuto dell'elaborazione oltre 500.000 caratteri estratti senza creare
  segmenti o chiamare gli embedding.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Ruff: controllo superato e 145 file Python conformi alla formattazione.
- `pytest -W error`: 348 test superati senza avvisi.
- Verificato l'avvio locale coordinato di portale e simulatore con entrambi gli endpoint
  `/health` disponibili e le porte temporanee chiuse al termine.
- Ruff: controllo superato e 148 file Python conformi alla formattazione.
- `pytest`: 354 test superati; stessa suite superata dalla CI GitHub sulla PR #71.
- Verificata una chiamata reale Gemini con testo fittizio: titolo, sede, servizio e
  persone coinvolte estratti senza campi mancanti.
- Verificato il deploy automatico Render del commit `4242878` soltanto dopo la CI verde.
- Verificato da sessione anonima il percorso dipendente → tecnico → amministratore:
  creazione di `SP-0007`, revisione umana, azione simulata `ASG-62D227858B3B` e audit.
- Verificato il reset pubblico: `SP-0007` restituisce 404, la coda torna a 6 ticket, le
  tre azioni tornano in attesa e `SP-0001` conserva soltanto i 4 eventi iniziali.
- Verificati tutti i collegamenti e le immagini locali del README e del documento di
  architettura.
- Verificato due volte l'avvio da database vuoto con `python -m app.deployment`: 6 sedi,
  5 utenti, 6 ticket, portale `8010` e simulatore `8011` disponibili.
- Verificate nel browser le schermate dipendente, raccolta guidata, coda tecnica,
  dettaglio operativo e knowledge base con soli dati temporanei fittizi.
- `pip check`: nessuna dipendenza mancante o incompatibile.
- Ruff: controllo superato e 150 file conformi alla formattazione.
- `pytest -W error`: 354 test superati senza avvisi dopo SP-083.
- Verificati tutti i collegamenti Markdown locali dell'intero repository: nessun file o
  immagine mancante.
- Verificato che i codici attività restino soltanto nei registri storici; `SP-0007` in
  `DEPLOYMENT.md` è esplicitamente identificato come ticket demo.
- `git diff --check`: nessun errore di spaziatura nella revisione generale dei documenti.
- Verificata la pubblicazione GitHub della release stabile `v0.1.0` da `main`, non bozza
  e non prerelease.
- Verificati nuovamente tutti i collegamenti Markdown locali: nessun file mancante.
- `pip check`: nessuna dipendenza mancante o incompatibile dopo SP-084.
- Ruff: controllo superato e 150 file conformi alla formattazione.
- `pytest -W error`: 354 test superati senza avvisi dopo SP-084.
- Aggiunta Alembic `1.19.1` come dipendenza di runtime, necessaria anche durante
  l'avvio e il deploy.
- Verificate `0001_v010_baseline` e `0002_normalize_v010` su database SQLite vuoto, su
  schema v0.1.0 canonico e sulla variante prodotta dai vecchi `ALTER TABLE`, usando dati
  fittizi di utenti, ticket, knowledge base e audit.
- Verificata la conservazione delle righe e l'idempotenza di due avvii consecutivi.
- Aggiornata con successo una copia temporanea del database locale storico: conteggi
  invariati su 9 tabelle, nessuna violazione delle chiavi esterne e file originale non
  modificato.
- Confrontati colonne, tipi, nullabilità, chiavi, riferimenti, indici, unicità e vincoli:
  fresh install e upgrade v0.1.0 producono lo stesso schema applicativo.
- Verificato il rifiuto di un database non versionato incompleto senza creare
  `alembic_version`.
- `alembic current`: revisione `0002_normalize_v010 (head)`; `alembic check`: nessuna
  nuova operazione rilevata rispetto ai modelli SQLAlchemy.
- Rimossi dal bootstrap tutti gli `ALTER TABLE` manuali e verificata l'applicazione
  automatica delle migrazioni da portale, comando locale e deploy.
- `pytest -W error`: 350 test superati senza avvisi dopo SP-090.
- Ruff: controllo superato e 155 file Python conformi alla formattazione.
- `pip check`: nessuna dipendenza mancante o incompatibile dopo SP-090.
- Aggiunta la migrazione `0003_support_groups` con catalogo univoco e appartenenze
  molti-a-molti; fresh install e upgrade v0.1.0 convergono ancora allo stesso schema.
- Convertiti i sette gruppi fissi in seed demo ripetibile con 11 appartenenze fittizie.
- Verificati tecnico in più gruppi, rifiuto dei dipendenti, unicità normalizzata e
  permessi di modifica riservati all'amministratore.
- Verificato che un gruppo disattivato resti leggibile nei ticket storici ma venga
  escluso dalle nuove assegnazioni e dalla lista fornita alla classificazione AI.
- Rimosso l'ultimo enum di gruppi dal contratto delle azioni proposte: anche una nuova
  proposta di assegnazione viene controllata sul catalogo attivo del database.
- Verificate nel browser integrato pagina amministrativa, editor dei membri e dettaglio
  ticket; layout mobile a 390 × 844 senza scorrimento orizzontale o errori console.
- `alembic current`: revisione `0003_support_groups (head)`; `alembic check`: nessuna
  nuova operazione rilevata rispetto ai modelli SQLAlchemy.
- `pytest -W error`: 358 test superati senza avvisi dopo SP-091.
- Ruff: controllo superato e 161 file Python conformi alla formattazione.
- `pip check`: nessuna dipendenza mancante o incompatibile dopo SP-091.
- Aggiunta Pillow `12.3.0` per decodificare e ricodificare PNG/JPEG senza metadati;
  PDF, TXT e LOG sono validati con parser o testo UTF-8 reale.
- Aggiunta migrazione `0004_secure_attachments`, successiva a `0003_support_groups`;
  fresh install e upgrade v0.1.0 producono anche la tabella privata `attachments` senza
  perdere righe esistenti.
- Verificati file validi e camuffati, limiti per invio/file/ticket, errori disco,
  integrità SHA-256, autorizzazione dipendente/tecnico/admin e pulizia ripetibile di
  metadati e file del contesto.
- Verificati nel browser integrato riquadro Allegati privati, caricamento di un LOG
  sintetico, download autorizzato, vista tecnica e layout mobile senza overflow o errori
  console; il file di collaudo è stato poi rimosso.
- `alembic current`: revisione `0004_secure_attachments (head)`; `alembic check`: nessuna
  nuova operazione rilevata rispetto ai modelli SQLAlchemy.
- `pytest -W error`: 386 test superati senza avvisi dopo la revisione completa di SP-092.
- Ruff: controllo superato e 168 file Python conformi alla formattazione.
- `pip check`: nessuna dipendenza mancante o incompatibile dopo SP-092.
