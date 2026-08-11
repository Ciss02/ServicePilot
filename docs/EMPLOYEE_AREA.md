# Area del dipendente

SP-041 permette a un dipendente autenticato di consultare dal browser soltanto le
proprie richieste e di aprirne il dettaglio.

## Quale problema risolve

Le API proteggevano già i ticket personali, ma mancava una schermata utilizzabile senza
strumenti tecnici. L'area dipendente riunisce stato, priorità, servizio, sede,
aggiornamenti del supporto e soluzione finale in una vista leggibile e responsive.

## Pagine disponibili

- `GET /app` mostra riepilogo ed elenco personale quando il ruolo è `employee`;
- `GET /app/tickets/{ticket_id}` mostra il dettaglio di una richiesta personale;
- tecnico e amministratore conservano la pagina provvisoria fino alla coda di SP-044.

La voce “Nuova richiesta” è visibile ma non attiva: la raccolta guidata dei dati
appartiene a SP-042 e la conferma a SP-043.

## Dati ricevuti e controlli

L'elenco non riceve un identificativo utente dal browser. Il backend ricava l'identità
dal cookie di sessione e aggiunge alla query il vincolo
`tickets.requester_id == current_user.id` per il ruolo dipendente.

Il dettaglio riceve soltanto un identificativo positivo del ticket. Anche in questo
caso il database cerca contemporaneamente ID e proprietario. Un ticket inesistente e
un ticket appartenente a un collega producono la stessa pagina `404`, che non rivela
titolo, descrizione o altri dati riservati.

Le stesse query di visibilità sono condivise dalle API e dalle pagine HTML, così i due
ingressi non possono applicare regole differenti.

## Dove vengono salvati i dati

SP-041 è una funzionalità di sola lettura e non salva nuovi dati. Ticket, sedi, utenti e
sessioni continuano a risiedere nel database SQLite già configurato. Non sono state
aggiunte tabelle, migrazioni o dipendenze. L'indice esistente su `requester_id` supporta
il filtro personale.

## Cosa può andare storto

- senza sessione valida il browser torna alla pagina di accesso;
- un ID non valido viene rifiutato dal percorso;
- un ticket assente o di un altro dipendente restituisce la stessa pagina privata `404`;
- sedi o tecnici non più disponibili ricevono un testo neutro, senza bloccare la pagina;
- un account senza richieste vede uno stato vuoto esplicativo.

## Chi può usare la funzionalità

L'elenco e il dettaglio implementati in SP-041 sono destinati al ruolo `employee`.
Tecnico e amministratore potranno consultare la coda completa attraverso l'interfaccia
prevista da SP-044; le loro API autorizzate restano invariate.

## Quali test dimostrano che funziona

I test HTTP creano dati fittizi per due dipendenti differenti e verificano che:

- l'elenco mostri soltanto i ticket dell'account corrente;
- il dettaglio personale mostri sede, categoria, tecnico e nota disponibili;
- il collegamento diretto a un ticket altrui restituisca `404` senza mostrare dati;
- un ID inesistente usi la stessa risposta privata;
- un dipendente senza ticket veda lo stato vuoto;
- una persona anonima venga rimandata al login;
- il tecnico non riceva in anticipo la schermata della futura coda.
