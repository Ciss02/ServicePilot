# Raccolta guidata dei dati

SP-042 permette a un dipendente autenticato di descrivere un problema e completare i
dati essenziali con una breve conversazione deterministica. Il flusso non usa ancora
l'AI e non crea un ticket: riepilogo e conferma appartengono a SP-043.

## Quale problema risolve

Un modulo unico e lungo può lasciare campi importanti vuoti. Il percorso divide invece
la raccolta in due domande semplici: prima il racconto libero del problema, poi soltanto
le informazioni che mancano per preparare un ticket completo.

## Dati ricevuti

Il primo passaggio riceve una descrizione da 10 a 4.000 caratteri. Il secondo riceve:

- titolo breve, da 5 a 120 caratteri;
- sede attiva scelta dall'elenco del database;
- servizio o strumento coinvolto, da 2 a 100 caratteri;
- numero di persone coinvolte, da 1 a 10.000.

Le pagine sono disponibili in `GET /app/new-ticket`,
`POST /app/new-ticket/problem` e `POST /app/new-ticket/details`.

## Dove vengono controllati

Il browser fornisce indicazioni immediate, ma il controllo decisivo avviene sempre nel
backend tramite i contratti Pydantic in `app/domain/ticket_intake.py`. Anche i valori
trasportati da un passaggio al successivo vengono controllati di nuovo, perché un campo
nascosto può essere modificato. La sede viene inoltre cercata nel database e deve essere
ancora attiva.

Quando un dato non è valido, la stessa pagina evidenzia il campo e spiega come
correggerlo. Il testo inserito viene protetto automaticamente dal template prima di
essere mostrato nella conversazione.

## Dove vengono salvati

SP-042 non salva dati nel database. La descrizione viene trasportata temporaneamente nel
modulo del passaggio successivo e viene persa se il percorso viene abbandonato o
ricaricato. Questa scelta mantiene netto il vincolo della specifica: nessun ticket nasce
prima che il dipendente veda il riepilogo e confermi in SP-043.

Non sono state aggiunte tabelle, migrazioni, dipendenze o codice JavaScript.

## Cosa può andare storto

- senza una sessione valida il browser torna al login;
- tecnico e amministratore vengono rimandati alla propria area;
- testi troppo brevi o lunghi, numeri fuori limite e campi mancanti vengono rifiutati;
- una sede inesistente, disattivata o manomessa viene rifiutata dal backend;
- abbandonare il percorso elimina la bozza temporanea, perché non è ancora un ticket.

## Chi può usare la funzionalità

La raccolta è riservata al ruolo `employee`. La protezione è applicata dal backend sia
alle pagine sia agli invii dei moduli.

## Quali test dimostrano che funziona

I test HTTP verificano che:

- il primo passaggio chieda soltanto la descrizione;
- una descrizione non valida venga richiesta di nuovo;
- il secondo passaggio chieda titolo, sede, servizio e persone coinvolte;
- le sedi disattivate non compaiano e non possano essere inviate manualmente;
- valori errati producano messaggi comprensibili;
- il completamento della raccolta non aumenti il numero dei ticket;
- visitatori anonimi e tecnici non possano usare il percorso del dipendente.
