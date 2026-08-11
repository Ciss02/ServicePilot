# Raccolta guidata dei dati

SP-042 e SP-043 permettono a un dipendente autenticato di descrivere un problema,
completare i dati essenziali e controllare tutto prima dell'invio. Il flusso non usa
ancora l'AI: la raccolta manuale è la base temporanea che verrà sostituita dalla
conversazione intelligente nelle attività SP-050 e SP-051.

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
`POST /app/new-ticket/problem`, `POST /app/new-ticket/details`,
`POST /app/new-ticket/edit` e `POST /app/new-ticket/confirm`.

## Dove vengono controllati

Il browser fornisce indicazioni immediate, ma il controllo decisivo avviene sempre nel
backend tramite i contratti Pydantic in `app/domain/ticket_intake.py`. Anche i valori
trasportati da un passaggio al successivo vengono controllati di nuovo, perché un campo
nascosto può essere modificato. La sede viene inoltre cercata nel database e deve essere
ancora attiva.

Quando un dato non è valido, la stessa pagina evidenzia il campo e spiega come
correggerlo. Il testo inserito viene protetto automaticamente dal template prima di
essere mostrato nella conversazione.

## Riepilogo, correzione e conferma

Il riepilogo mostra titolo, descrizione, sede, servizio e persone coinvolte. Il pulsante
`Correggi i dati` riapre il modulo già compilato; `Annulla` torna all'area personale e
non salva nulla. Soltanto `Conferma e crea ticket` invia una conferma esplicita al
backend.

## Dove vengono salvati

Fino alla conferma la bozza resta soltanto nei moduli e viene persa abbandonando il
percorso. Dopo la conferma il ticket viene salvato nella tabella `tickets`, collegato
all'utente autenticato e alla sede scelta, con stato iniziale `new`.

Il riepilogo riceve anche un codice casuale di creazione. Il database lo accetta una
sola volta: un doppio clic o un reinvio della stessa conferma riporta allo stesso ticket
senza crearne un secondo. L'aggiornamento della tabella è applicato anche ai database
SQLite locali già esistenti. Non sono state aggiunte dipendenze o codice JavaScript.

## Cosa può andare storto

- senza una sessione valida il browser torna al login;
- tecnico e amministratore vengono rimandati alla propria area;
- testi troppo brevi o lunghi, numeri fuori limite e campi mancanti vengono rifiutati;
- una sede inesistente, disattivata o manomessa viene rifiutata dal backend;
- una conferma mancante o manomessa viene rifiutata senza creare dati;
- un doppio invio riconosce il ticket già creato e non lo duplica;
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
- il riepilogo non aumenti il numero dei ticket;
- correggere o annullare non crei nulla;
- una conferma esplicita crei un ticket collegato al dipendente;
- ripetere la stessa conferma restituisca lo stesso ticket senza duplicarlo;
- una conferma mancante venga rifiutata;
- visitatori anonimi e tecnici non possano usare il percorso del dipendente.
