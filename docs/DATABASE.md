# Database iniziale

SP-020 introduce la persistenza minima di ServicePilot con SQLAlchemy e SQLite.

## Perché esiste

I contratti Pydantic controllano i dati ricevuti dall'applicazione. Il database ha un
compito diverso: conservarli tra un avvio e l'altro e mantenere validi i collegamenti
tra ticket, utenti e sedi.

## Tabelle iniziali

- `users`: identità fittizia, nome visibile, ruolo, hash della password e stato attivo;
- `auth_sessions`: impronta del codice casuale, utente collegato, creazione e scadenza;
- `sites`: codice, nome e stato attivo di una sede fittizia;
- `knowledge_documents`: file della knowledge base, metadati, stato di estrazione e
  stato dell'indice con modello, dimensione e data;
- `knowledge_segments`: testo estratto, posizione, sezione o pagina di origine e
  vettore JSON facoltativo;
- `tickets`: dati confermati della richiesta, classificazione facoltativa,
  assegnazione, stato e date.

La classificazione può essere vuota quando il ticket nasce perché, nel flusso MVP,
viene proposta dopo la conferma. La priorità sarà sempre calcolata dal backend prima
di essere salvata. Allegati, cronologia e audit richiederanno attività dedicate.

## Configurazione

Senza configurazione aggiuntiva viene usato `sqlite:///./servicepilot.db`. È possibile
scegliere un altro database impostando la variabile d'ambiente
`SERVICEPILOT_DATABASE_URL`.

Per creare le tabelle mancanti:

```powershell
.\.venv\Scripts\python.exe -m app.db
```

Il comando può essere eseguito più volte e non cancella i dati esistenti. SP-030 include
un aggiornamento compatibile che aggiunge `password_hash` alle tabelle `users` create
nelle sessioni precedenti. Un sistema generale di migrazioni resta necessario per
modifiche strutturali future.

## Controlli applicati

- email utente e codice sede unici;
- password degli account demo conservata soltanto come hash Argon2;
- codici di sessione conservati nel database soltanto come impronte SHA-256;
- sessioni collegate a utenti esistenti e rimosse con l'utente;
- ruoli, categorie, stati, impatto, urgenza e priorità limitati al vocabolario;
- numero di utenti coinvolti compreso tra 1 e 10.000;
- richiedente, sede e tecnico assegnato collegati a record esistenti;
- stato iniziale del ticket uguale a `new`;
- data di creazione e di ultimo aggiornamento.
- posizione del segmento unica all'interno del documento e collegamento eliminato
  automaticamente insieme al documento.
- vettori confrontati soltanto quando modello e dimensione del documento corrispondono
  alla configurazione attiva.

I test usano file SQLite temporanei e non modificano `servicepilot.db`.

## Dati dimostrativi

Il comando seguente crea le tabelle mancanti e carica il dataset sintetico:

```powershell
.\.venv\Scripts\python.exe -m app.db seed
```

Contenuto e comportamento sono descritti in
[`DEMO_DATA.md`](DEMO_DATA.md).

