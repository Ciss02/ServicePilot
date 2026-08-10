# ServicePilot AI - Piano di progetto

Questo documento è la lista ufficiale del lavoro da svolgere.

Ogni attività ha un codice, ad esempio `SP-001`. In una nuova sessione è sufficiente
indicare quel codice per definire con precisione il risultato da ottenere.

## Regole della tasklist

- `[ ]` da iniziare
- `[~]` in corso
- `[x]` completata e verificata
- Una attività viene chiusa solo quando i suoi controlli finali sono superati.
- Se emerge nuovo lavoro, viene aggiunto qui prima di essere implementato.
- Le attività vengono svolte nell'ordine indicato, salvo una decisione registrata.

## Milestone 0 - Fondamenta del progetto

**Risultato:** repository ordinato e applicazione minima avviabile.

- [x] **SP-001 - Struttura iniziale del repository**
  Creare README provvisorio, `.gitignore`, licenza e organizzare la documentazione.
  Verifica: la struttura è comprensibile e Git non include file locali o segreti.
- [x] **SP-002 - Ambiente Python locale**
  Verificare Python, creare l'ambiente isolato e definire le dipendenze iniziali.
  Verifica: l'ambiente può essere ricreato seguendo istruzioni scritte.
- [x] **SP-003 - Prima applicazione FastAPI**
  Creare la struttura `app/`, l'endpoint `/health` e il primo test automatico.
  Verifica: il server parte e il test di salute passa.

## Milestone 1 - Regole e dati del ticket

**Risultato:** il progetto conosce struttura, categorie e priorità dei ticket.

- [x] **SP-010 - Vocabolario del dominio**
  Definire categorie, stati, ruoli, impatto, urgenza e livelli di priorità.
  Verifica: i valori ammessi sono centralizzati e documentati.
- [x] **SP-011 - Matrice della priorità**
  Implementare il calcolo deterministico da impatto e urgenza.
  Verifica: test per casi P1, P2, P3 e P4.
- [x] **SP-012 - Contratti dati del ticket**
  Definire e validare i dati necessari per creare e aggiornare un ticket.
  Verifica: input validi accettati e input errati rifiutati chiaramente.

## Milestone 2 - Database e API essenziali

**Risultato:** i ticket possono essere salvati e gestiti senza AI.

- [ ] **SP-020 - Database iniziale**
  Configurare SQLite e le tabelle per utenti, sedi e ticket.
  Verifica: il database viene creato in modo ripetibile.
- [ ] **SP-021 - Dataset dimostrativo**
  Aggiungere sedi, account e ticket completamente fittizi.
  Verifica: il caricamento produce sempre dati demo coerenti.
- [ ] **SP-022 - Creazione e lettura dei ticket**
  Implementare le API per creare un ticket e consultarne i dati.
  Verifica: test di creazione, lettura e ticket inesistente.
- [ ] **SP-023 - Gestione tecnica del ticket**
  Implementare modifica, assegnazione e cambio di stato.
  Verifica: modifiche valide salvate ed errori gestiti.

## Milestone 3 - Accesso e permessi

**Risultato:** ogni ruolo può vedere ed eseguire soltanto le operazioni consentite.

- [ ] **SP-030 - Account demo e password sicure**
  Preparare gli account dei tre ruoli e memorizzare password protette.
  Verifica: nessuna password in chiaro nel database o nel codice.
- [ ] **SP-031 - Login, sessione e logout**
  Permettere l'accesso degli account demo e la chiusura della sessione.
  Verifica: accesso valido, accesso negato e logout testati.
- [ ] **SP-032 - Autorizzazione per ruolo**
  Proteggere ticket personali, funzioni tecniche e funzioni amministrative.
  Verifica: test dei principali tentativi di accesso non autorizzato.

## Milestone 4 - Interfaccia completa senza AI

**Risultato:** dipendente e tecnico completano il flusso principale dal browser.

- [ ] **SP-040 - Layout e pagina di accesso**
  Creare la base grafica responsive e la pagina login.
  Verifica: pagine utilizzabili da computer e schermo piccolo.
- [ ] **SP-041 - Area del dipendente**
  Mostrare i ticket personali e il relativo dettaglio.
  Verifica: un dipendente non vede ticket di altri utenti.
- [ ] **SP-042 - Raccolta guidata dei dati**
  Creare una conversazione inizialmente deterministica per descrivere il problema.
  Verifica: vengono richiesti i dati mancanti essenziali.
- [ ] **SP-043 - Riepilogo e conferma**
  Mostrare i dati raccolti e creare il ticket solo dopo conferma.
  Verifica: annullare non crea nulla; confermare crea un solo ticket.
- [ ] **SP-044 - Coda del tecnico**
  Creare elenco, filtri, dettaglio, assegnazione e aggiornamento.
  Verifica: il tecnico completa manualmente un ticket demo.

## Milestone 5 - Classificazione AI

**Risultato:** l'AI assiste la raccolta e la classificazione senza decidere la priorità.

- [ ] **SP-050 - Adapter del modello AI**
  Isolare Gemini dietro un'interfaccia sostituibile e configurazione sicura.
  Verifica: il progetto funziona nei test senza chiamate AI reali.
- [ ] **SP-051 - Estrazione strutturata**
  Estrarre i dati presenti nella descrizione e individuare quelli mancanti.
  Verifica: output controllato e casi incompleti gestiti.
- [ ] **SP-052 - Classificazione suggerita**
  Proporre categoria, sottocategoria, impatto, urgenza e gruppo.
  Verifica: la priorità continua a essere calcolata dal backend.
- [ ] **SP-053 - Revisione umana e gestione errori**
  Permettere correzioni e gestire timeout o risposte AI non valide.
  Verifica: il flusso rimane utilizzabile anche se il provider non risponde.

## Milestone 6 - Knowledge base e RAG

**Risultato:** il tecnico riceve suggerimenti fondati su procedure consultabili.

- [ ] **SP-060 - Upload sicuro dei documenti**
  Accettare PDF e Markdown con controlli di tipo e dimensione.
  Verifica: file non ammessi vengono rifiutati.
- [ ] **SP-061 - Estrazione e segmentazione**
  Estrarre il testo e conservarne documento, sezione e segmenti.
  Verifica: i segmenti mantengono il riferimento alla fonte.
- [ ] **SP-062 - Indicizzazione e ricerca**
  Generare rappresentazioni ricercabili e recuperare passaggi pertinenti.
  Verifica: una procedura nota viene ritrovata da una domanda collegata.
- [ ] **SP-063 - Soluzione con fonti**
  Generare un suggerimento mostrando documento e sezione utilizzati.
  Verifica: fonti visibili e collegate ai passaggi recuperati.
- [ ] **SP-064 - Risposta prudente**
  Dichiarare quando le fonti non sono sufficienti.
  Verifica: test con ricerca senza risultati e fonti deboli.

## Milestone 7 - Azioni, audit e amministrazione

**Risultato:** le azioni dell'agente richiedono approvazione e sono tracciate.

- [ ] **SP-070 - Modello delle azioni proposte**
  Salvare tipo, motivazione, dati, stato ed effetto previsto.
  Verifica: proposta separata dall'esecuzione.
- [ ] **SP-071 - Servizi REST simulati**
  Simulare assegnazione, comunicazione ed escalation, inclusi errori.
  Verifica: successi e fallimenti riproducibili nei test.
- [ ] **SP-072 - Approvazione del tecnico**
  Mostrare i dettagli e permettere approvazione o rifiuto espliciti.
  Verifica: nessuna azione parte prima dell'approvazione.
- [ ] **SP-073 - Audit log**
  Registrare operazioni umane, AI, approvazioni ed esiti.
  Verifica: il percorso di un ticket è ricostruibile.
- [ ] **SP-074 - Strumenti amministrativi**
  Gestire documenti, reindicizzazione e ripristino dei dati demo.
  Verifica: funzioni disponibili soltanto all'amministratore.

## Milestone 8 - Qualità, pubblicazione e portfolio

**Risultato:** demo stabile, documentata e presentabile.

- [ ] **SP-080 - Controlli automatici**
  Completare test, formattazione e controllo automatico su GitHub.
  Verifica: tutti i controlli passano da un ambiente pulito.
- [ ] **SP-081 - Sicurezza e limiti della demo**
  Controllare segreti, upload, sessioni e limiti delle chiamate AI.
  Verifica: revisione documentata e problemi critici risolti.
- [ ] **SP-082 - Deploy e ripristino**
  Pubblicare la demo e verificare il ripristino del dataset.
  Verifica: collaudo completo da una sessione anonima.
- [ ] **SP-083 - Documentazione portfolio**
  Completare README bilingue, architettura, screenshot, limiti e roadmap.
  Verifica: una persona esterna comprende e avvia il progetto.
- [ ] **SP-084 - Video e release MVP**
  Registrare la demo e pubblicare la versione `v0.1.0`.
  Verifica: video di 2-3 minuti e release collegati nel README.

## Ordine di partenza

La prossima attività è **SP-020**. La milestone attiva è **Milestone 2**.
