# Database

ServicePilot usa SQLAlchemy per salvare i dati. L'MVP usa SQLite sia in locale sia nella
demo gratuita; l'astrazione mantiene l'accesso al database separato dal resto
dell'applicazione, ma PostgreSQL resta un'evoluzione successiva.

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
  assegnazione, stato, soluzione finale e suggerimento AI separato;
- `ticket_solution_sources`: passaggi realmente citati da un suggerimento AI, con
  ordine e punteggio della ricerca.
- `proposed_actions`: intenzioni dell'agente collegate al ticket, con tipo, motivazione,
  payload JSON, effetto previsto, stato, decisore ed esito del servizio simulato.
- `audit_events`: eventi append-only collegati al ticket, con origine, tipo, riepilogo,
  dettagli controllati, autore umano facoltativo e azione collegata facoltativa.

La classificazione può essere vuota quando il ticket nasce perché viene proposta dopo
la conferma. La priorità è sempre calcolata dal backend prima di essere salvata. Gli
allegati non fanno parte del perimetro dell'MVP.

## Configurazione

Senza configurazione aggiuntiva viene usato `sqlite:///./servicepilot.db`. È possibile
scegliere un altro database impostando la variabile d'ambiente
`SERVICEPILOT_DATABASE_URL`.

Per creare le tabelle mancanti:

```powershell
.\.venv\Scripts\python.exe -m app.db
```

Il comando può essere eseguito più volte e non cancella i dati esistenti. L'avvio
include piccoli aggiornamenti compatibili per database creati da versioni precedenti.
Un sistema generale di migrazioni resta necessario se il progetto evolverà oltre
l'MVP con modifiche strutturali più ampie.

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
- fonti dei suggerimenti collegate a ticket e segmenti esistenti, senza duplicare rango
  o passaggio nello stesso risultato;
- suggerimenti invalidati quando una procedura citata viene rielaborata.
- azioni proposte collegate a ticket esistenti e limitate a tipi e stati controllati;
- creazione della proposta separata da assegnazione, comunicazione ed escalation reali.
- decisore e data salvati prima dell'esecuzione; riferimento, messaggio o errore salvati
  dopo la risposta del simulatore.
- eventi di audit collegati a ticket esistenti, con origine e tipo limitati al
  vocabolario del dominio;
- riepilogo tra 5 e 300 caratteri e dettagli JSON fino a 4.000 caratteri;
- modifica e cancellazione degli eventi già caricati bloccate dall'applicazione.

I test usano file SQLite temporanei e non modificano `servicepilot.db`.

## Dati dimostrativi

Il comando seguente crea le tabelle mancanti e carica il dataset sintetico:

```powershell
.\.venv\Scripts\python.exe -m app.db seed
```

Contenuto e comportamento sono descritti in
[`DEMO_DATA.md`](DEMO_DATA.md).

