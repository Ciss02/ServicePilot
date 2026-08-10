# Database iniziale

SP-020 introduce la persistenza minima di ServicePilot con SQLAlchemy e SQLite.

## Perché esiste

I contratti Pydantic controllano i dati ricevuti dall'applicazione. Il database ha un
compito diverso: conservarli tra un avvio e l'altro e mantenere validi i collegamenti
tra ticket, utenti e sedi.

## Tabelle iniziali

- `users`: identità fittizia, nome visibile, ruolo e stato attivo;
- `sites`: codice, nome e stato attivo di una sede fittizia;
- `tickets`: dati confermati della richiesta, classificazione facoltativa,
  assegnazione, stato e date.

La classificazione può essere vuota quando il ticket nasce perché, nel flusso MVP,
viene proposta dopo la conferma. La priorità sarà sempre calcolata dal backend prima
di essere salvata. Password, allegati, cronologia e audit richiederanno attività
dedicate.

## Configurazione

Senza configurazione aggiuntiva viene usato `sqlite:///./servicepilot.db`. È possibile
scegliere un altro database impostando la variabile d'ambiente
`SERVICEPILOT_DATABASE_URL`.

Per creare le tabelle mancanti:

```powershell
.\.venv\Scripts\python.exe -m app.db
```

Il comando può essere eseguito più volte: SQLAlchemy crea soltanto ciò che manca e non
cancella i dati esistenti. Le modifiche future alla struttura richiederanno invece un
sistema di migrazioni, che non fa parte di SP-020.

## Controlli applicati

- email utente e codice sede unici;
- ruoli, categorie, stati, impatto, urgenza e priorità limitati al vocabolario;
- numero di utenti coinvolti compreso tra 1 e 10.000;
- richiedente, sede e tecnico assegnato collegati a record esistenti;
- stato iniziale del ticket uguale a `new`;
- data di creazione e di ultimo aggiornamento.

I test usano file SQLite temporanei e non modificano `servicepilot.db`.

## Dati dimostrativi

Il comando seguente crea le tabelle mancanti e carica il dataset sintetico:

```powershell
.\.venv\Scripts\python.exe -m app.db seed
```

Contenuto e comportamento sono descritti in
[`DEMO_DATA.md`](DEMO_DATA.md).

