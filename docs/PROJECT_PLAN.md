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

- [x] **SP-020 - Database iniziale**
  Configurare SQLite e le tabelle per utenti, sedi e ticket.
  Verifica: il database viene creato in modo ripetibile.
- [x] **SP-021 - Dataset dimostrativo**
  Aggiungere sedi, account e ticket completamente fittizi.
  Verifica: il caricamento produce sempre dati demo coerenti.
- [x] **SP-022 - Creazione e lettura dei ticket**
  Implementare le API per creare un ticket e consultarne i dati.
  Verifica: test di creazione, lettura e ticket inesistente.
- [x] **SP-023 - Gestione tecnica del ticket**
  Implementare modifica, assegnazione e cambio di stato.
  Verifica: modifiche valide salvate ed errori gestiti.

## Milestone 3 - Accesso e permessi

**Risultato:** ogni ruolo può vedere ed eseguire soltanto le operazioni consentite.

- [x] **SP-030 - Account demo e password sicure**
  Preparare gli account dei tre ruoli e memorizzare password protette.
  Verifica: nessuna password in chiaro nel database o nel codice.
- [x] **SP-031 - Login, sessione e logout**
  Permettere l'accesso degli account demo e la chiusura della sessione.
  Verifica: accesso valido, accesso negato e logout testati.
- [x] **SP-032 - Autorizzazione per ruolo**
  Proteggere ticket personali, funzioni tecniche e funzioni amministrative.
  Verifica: test dei principali tentativi di accesso non autorizzato.

## Milestone 4 - Interfaccia completa senza AI

**Risultato:** dipendente e tecnico completano il flusso principale dal browser.

- [x] **SP-040 - Layout e pagina di accesso**
  Creare la base grafica responsive e la pagina login.
  Verifica: pagine utilizzabili da computer e schermo piccolo.
- [x] **SP-041 - Area del dipendente**
  Mostrare i ticket personali e il relativo dettaglio.
  Verifica: un dipendente non vede ticket di altri utenti.
- [x] **SP-042 - Raccolta guidata dei dati**
  Creare una conversazione inizialmente deterministica per descrivere il problema.
  Verifica: vengono richiesti i dati mancanti essenziali.
- [x] **SP-043 - Riepilogo e conferma**
  Mostrare i dati raccolti e creare il ticket solo dopo conferma.
  Verifica: annullare non crea nulla; confermare crea un solo ticket.
- [x] **SP-044 - Coda del tecnico**
  Creare elenco, filtri, dettaglio, assegnazione e aggiornamento.
  Verifica: il tecnico completa manualmente un ticket demo.

## Milestone 5 - Classificazione AI

**Risultato:** l'AI assiste la raccolta e la classificazione senza decidere la priorità.

- [x] **SP-050 - Adapter del modello AI**
  Isolare Gemini dietro un'interfaccia sostituibile e configurazione sicura.
  Verifica: il progetto funziona nei test senza chiamate AI reali.
- [x] **SP-051 - Estrazione strutturata**
  Estrarre i dati presenti nella descrizione e individuare quelli mancanti.
  Verifica: output controllato e casi incompleti gestiti.
- [x] **SP-052 - Classificazione suggerita**
  Proporre categoria, sottocategoria, impatto, urgenza e gruppo.
  Verifica: la priorità continua a essere calcolata dal backend.
- [x] **SP-053 - Revisione umana e gestione errori**
  Permettere correzioni e gestire timeout o risposte AI non valide.
  Verifica: il flusso rimane utilizzabile anche se il provider non risponde.

## Milestone 6 - Knowledge base e RAG

**Risultato:** il tecnico riceve suggerimenti fondati su procedure consultabili.

- [x] **SP-060 - Upload sicuro dei documenti**
  Accettare PDF e Markdown con controlli di tipo e dimensione.
  Verifica: file non ammessi vengono rifiutati.
- [x] **SP-061 - Estrazione e segmentazione**
  Estrarre il testo e conservarne documento, sezione e segmenti.
  Verifica: i segmenti mantengono il riferimento alla fonte.
- [x] **SP-062 - Indicizzazione e ricerca**
  Generare rappresentazioni ricercabili e recuperare passaggi pertinenti.
  Verifica: una procedura nota viene ritrovata da una domanda collegata.
- [x] **SP-063 - Soluzione con fonti**
  Generare un suggerimento mostrando documento e sezione utilizzati.
  Verifica: fonti visibili e collegate ai passaggi recuperati.
- [x] **SP-064 - Risposta prudente**
  Dichiarare quando le fonti non sono sufficienti.
  Verifica: test con ricerca senza risultati e fonti deboli.

## Milestone 7 - Azioni, audit e amministrazione

**Risultato:** le azioni dell'agente richiedono approvazione e sono tracciate.

- [x] **SP-070 - Modello delle azioni proposte**
  Salvare tipo, motivazione, dati, stato ed effetto previsto.
  Verifica: proposta separata dall'esecuzione.
- [x] **SP-071 - Servizi REST simulati**
  Simulare assegnazione, comunicazione ed escalation, inclusi errori.
  Verifica: successi e fallimenti riproducibili nei test.
- [x] **SP-072 - Approvazione del tecnico**
  Mostrare i dettagli e permettere approvazione o rifiuto espliciti.
  Verifica: nessuna azione parte prima dell'approvazione.
- [x] **SP-073 - Audit log**
  Registrare operazioni umane, AI, approvazioni ed esiti.
  Verifica: il percorso di un ticket è ricostruibile.
- [x] **SP-074 - Strumenti amministrativi**
  Gestire documenti, reindicizzazione e ripristino dei dati demo.
  Verifica: funzioni disponibili soltanto all'amministratore.

## Milestone 8 - Qualità, pubblicazione e portfolio

**Risultato:** demo stabile, documentata e presentabile.

- [x] **SP-080 - Controlli automatici**
  Completare test, formattazione e controllo automatico su GitHub.
  Verifica: tutti i controlli passano da un ambiente pulito.
- [x] **SP-081 - Sicurezza e limiti della demo**
  Controllare segreti, upload, sessioni e limiti delle chiamate AI.
  Verifica: revisione documentata e problemi critici risolti.
- [x] **SP-082 - Deploy e ripristino**
  Pubblicare la demo e verificare il ripristino del dataset.
  Verifica: collaudo completo da una sessione anonima.
- [x] **SP-083 - Documentazione portfolio**
  Completare README bilingue, architettura, screenshot, limiti e roadmap.
  Verifica: una persona esterna comprende e avvia il progetto.
- [x] **SP-084 - Release MVP v0.1.0**
  Pubblicare la versione stabile e collegarla nel README; il video resta facoltativo.
  Verifica: release accessibile con note finali e documentazione aggiornata.

## Ordine di partenza

L'MVP `v0.1.0` e le milestone 0-8 sono completati. La roadmap approvata della `v0.2.0`
è descritta in [`V020_PRODUCT_PLAN.md`](V020_PRODUCT_PLAN.md). Le attività successive
vengono svolte nell'ordine seguente, una issue e una pull request alla volta.

## Milestone 9 - Modello operativo e collaborazione

**Risultato:** ticket, gruppi, allegati e comunicazioni hanno una base dati sicura e
versionata.

- [x] **[SP-090 - Migrazioni versionate per la v0.2](https://github.com/Ciss02/ServicePilot/issues/74)**
  Introdurre Alembic e garantire upgrade da `v0.1.0` e creazione da database vuoto.
  Verifica: i due percorsi producono lo stesso schema senza perdere dati.
- [x] **[SP-091 - Gruppi di supporto e appartenenze](https://github.com/Ciss02/ServicePilot/issues/75)**
  Rendere i gruppi amministrabili e collegare ogni tecnico a uno o più gruppi.
  Verifica: gruppi disattivati restano nello storico ma non sono assegnabili.
- [x] **[SP-092 - Allegati sicuri](https://github.com/Ciss02/ServicePilot/issues/76)**
  Conservare file controllati per bozze, ticket e messaggi con download autorizzato.
  Verifica: tipi camuffati, limiti e accessi estranei vengono rifiutati.
- [ ] **[SP-093 - Comunicazioni cronologiche sul ticket](https://github.com/Ciss02/ServicePilot/issues/77)**
  Sostituire la nota singola con un thread pubblico append-only e allegati.
  Verifica: più messaggi restano distinti e visibili soltanto ai partecipanti autorizzati.
- [ ] **[SP-094 - Nuovo ciclo di vita del ticket](https://github.com/Ciss02/ServicePilot/issues/78)**
  Separare risoluzione, conferma, riapertura, rifiuto e chiusure autonoma/automatica.
  Verifica: finestre di 5 e 14 giorni, ruoli e audit sono testati con orologio finto.

## Milestone 10 - Agente conversazionale e apertura guidata

**Risultato:** l'agente raccoglie informazioni, prova soluzioni sicure e prepara un
ticket utile al tecnico.

- [ ] **[SP-100 - Bozze conversazionali persistenti](https://github.com/Ciss02/ServicePilot/issues/79)**
  Salvare sessioni, messaggi, fatti e allegati privati riprendibili.
  Verifica: logout, annullamento e scadenza non producono ticket o file orfani.
- [ ] **[SP-101 - Orchestratore AI con strumenti controllati](https://github.com/Ciss02/ServicePilot/issues/80)**
  Costruire un ciclo Gemini limitato a strumenti e output validati dal backend.
  Verifica: limiti, timeout e fallback manuale impediscono blocchi o costi incontrollati.
- [ ] **[SP-102 - Diagnosi preventiva basata sulle procedure](https://github.com/Ciss02/ServicePilot/issues/81)**
  Proporre passaggi sicuri soltanto da fonti pubblicate o regole approvate.
  Verifica: contenuti rischiosi e fonti non destinate ai dipendenti sono esclusi.
- [ ] **[SP-103 - Allegati condizionali e ticket tecnico completo](https://github.com/Ciss02/ServicePilot/issues/82)**
  Richiedere evidenze per regola e produrre un riepilogo tecnico confermabile.
  Verifica: obblighi, eccezioni motivate e descrizioni originale/AI restano distinti.
- [ ] **[SP-104 - Assistenze concluse e apprendimento controllato](https://github.com/Ciss02/ServicePilot/issues/83)**
  Registrare problemi risolti senza ticket e generare conoscenze candidate anonimizzate.
  Verifica: nessun candidato viene usato dalla ricerca prima della pubblicazione admin.
- [ ] **[SP-105 - Apertura ticket per conto del dipendente](https://github.com/Ciss02/ServicePilot/issues/84)**
  Consentire al team IT di usare l'agente scegliendo un dipendente attivo.
  Verifica: richiedente, autore, notifica e audit restano corretti e separati.

## Milestone 11 - Workspace tecnico e notifiche

**Risultato:** i tecnici hanno uno spazio operativo ordinato senza modifiche accidentali.

- [ ] **[SP-110 - Dettaglio ticket in sola lettura e modifica esplicita](https://github.com/Ciss02/ServicePilot/issues/85)**
  Separare consultazione, modifica dati e comandi di stato.
  Verifica: soluzione e motivazione vengono richieste soltanto dall'azione pertinente.
- [ ] **[SP-111 - Sotto-attività tecniche](https://github.com/Ciss02/ServicePilot/issues/86)**
  Aggiungere attività interne assegnabili e l'area `Le mie attività`.
  Verifica: il dipendente non può leggerne neppure titoli, conteggi o URL.
- [ ] **[SP-112 - Worklog manuale e timer](https://github.com/Ciss02/ServicePilot/issues/87)**
  Registrare durata e attività manualmente o con un solo timer persistente.
  Verifica: stop idempotente, riavvio, avviso 12 ore e chiusura ticket sono testati.
- [ ] **[SP-113 - Centro notifiche](https://github.com/Ciss02/ServicePilot/issues/88)**
  Aggiungere campanella, non letti, filtri e collegamenti autorizzati.
  Verifica: destinatari, deduplicazione e permessi sono coerenti con l'evento sorgente.

## Milestone 12 - Knowledge management evoluto

**Risultato:** le procedure sono modificabili, versionate e pubblicate senza alterare
lo storico.

- [ ] **[SP-120 - Procedure versionate e conversione PDF](https://github.com/Ciss02/ServicePilot/issues/89)**
  Separare procedura, versioni e originale; convertire i PDF in bozze Markdown.
  Verifica: citazioni esistenti restano legate alla versione corretta.
- [ ] **[SP-121 - Editor Markdown con bozza e pubblicazione](https://github.com/Ciss02/ServicePilot/issues/90)**
  Creare editor e anteprima sicura con pubblicazione atomica.
  Verifica: un errore mantiene attiva e ricercabile la versione precedente.
- [ ] **[SP-122 - Revisione delle conoscenze candidate](https://github.com/Ciss02/ServicePilot/issues/91)**
  Correggere, rifiutare o trasformare una soluzione riuscita in bozza.
  Verifica: soltanto la successiva pubblicazione rende il contenuto ricercabile.

## Milestone 13 - Report, qualità e release

**Risultato:** amministratore e portfolio mostrano dati affidabili e una versione stabile.

- [ ] **[SP-130 - Metriche e servizi di reporting](https://github.com/Ciss02/ServicePilot/issues/92)**
  Calcolare volumi, tempi, lavoro e assistenze concluse con filtri condivisi.
  Verifica: formule, casi vuoti, intervalli e fusi orari hanno test deterministici.
- [ ] **[SP-131 - Dashboard report ed esportazione CSV](https://github.com/Ciss02/ServicePilot/issues/93)**
  Mostrare report admin accessibili ed esportare gli stessi dati in CSV sicuri.
  Verifica: pagina e CSV concordano e neutralizzano le formule.
- [ ] **[SP-132 - Audit, sicurezza e dati demo v0.2](https://github.com/Ciss02/ServicePilot/issues/94)**
  Completare eventi, seed, reset e revisione di sicurezza delle nuove funzioni.
  Verifica: reset ripetibile, audit minimizzato e nessun dato reale o segreto.
- [ ] **[SP-133 - Collaudo, documentazione e release v0.2.0](https://github.com/Ciss02/ServicePilot/issues/95)**
  Collaudare i tre ruoli, aggiornare il portfolio, distribuire e pubblicare la release.
  Verifica: CI verde, demo ripristinata, tag e release `v0.2.0` accessibili.

## Prossima attività

**SP-092 - Allegati sicuri.** Conservare file controllati per bozze, ticket e messaggi
con download autorizzato, senza anticipare il thread cronologico previsto in SP-093.
