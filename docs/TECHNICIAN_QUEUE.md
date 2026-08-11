# Coda tecnica

Questo documento riassume in modo semplice la funzionalità SP-044.

## Quale problema risolve

Il tecnico ha un unico punto in cui vedere tutte le richieste, capire quali sono più
urgenti e accompagnare ogni ticket dall'apertura alla chiusura.

## Quali dati riceve

La coda riceve filtri facoltativi per stato, assegnazione e priorità, oltre alla scelta
dell'ordinamento. Il dettaglio riceve tecnico, gruppo, categoria, sottocategoria,
impatto, urgenza, stato, nota e soluzione.

## Dove vengono controllati

I valori del modulo vengono controllati dal backend. L'assegnatario deve essere un
tecnico o amministratore attivo. Categoria, impatto, urgenza e stato devono appartenere
al vocabolario approvato. Ogni cambio di stato deve seguire il percorso consentito.

## Dove vengono salvati

Gli aggiornamenti validi vengono salvati nella tabella `tickets` di SQLite. Tutte le
modifiche di un invio vengono confermate insieme: se un controllo fallisce, il ticket
rimane invariato.

## Cosa può andare storto

- un tecnico selezionato può non esistere o essere inattivo;
- un passaggio di stato può non essere consentito;
- categoria, impatto o urgenza possono essere incompleti;
- la soluzione può mancare quando si prova a risolvere o chiudere;
- il database può rifiutare il salvataggio.

In questi casi la pagina mostra un messaggio vicino al campo interessato e non salva
un aggiornamento parziale.

## Chi può usarla

Soltanto i ruoli `technician` e `admin` possono usare il pannello operativo. Un
`employee` continua a vedere esclusivamente i propri ticket e non può inviare
aggiornamenti tecnici.

## Quale test dimostra che funziona

I test web verificano la visibilità della coda, i filtri, l'accesso dei ruoli, il
ricalcolo della priorità e l'intero percorso `new → in_progress → resolved → closed`.
La prova nel browser verifica inoltre che elenco, filtri e pannello siano realmente
utilizzabili dalla pagina.
