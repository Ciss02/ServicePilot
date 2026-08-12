# ServicePilot AI - Stato del progetto

Aggiornato: 12 agosto 2026

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

## Milestone attiva

**Milestone 6 - Knowledge base e RAG**

## Ultima attività completata

**SP-062 - Indicizzazione e ricerca**

I segmenti estratti vengono trasformati in vettori tramite un adapter sostituibile e
salvati soltanto dopo controlli di numero, dimensione e validità. Il laboratorio della
knowledge base confronta una domanda con i segmenti indicizzati e mostra i passaggi più
simili conservando documento, sezione e testo. Test e sviluppo non chiamano Gemini.

## Prossima attività

**SP-063 - Soluzione con fonti**

Risultato atteso:

- usare i passaggi recuperati per generare un suggerimento tecnico;
- mostrare documento e sezione accanto alla soluzione proposta;
- mantenere il suggerimento separato dalla decisione finale del tecnico.

## Blocchi o decisioni aperte

- Provider di deploy da decidere in una fase successiva.

## Come iniziare una nuova sessione

Prompt consigliato:

> Leggi `AGENTS.md` e `docs/PROJECT_STATUS.md`. Occupati della task SP-063.
> Prima spiegami in modo semplice cosa farai e perché. Alla fine esegui i controlli,
> aggiorna lo stato del progetto e mostrami le modifiche prima del commit.

Sostituire `SP-063` con il codice dell'attività successiva.

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
