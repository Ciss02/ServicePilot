# Area del dipendente

Un dipendente autenticato può consultare dal browser soltanto le proprie richieste,
aprirne il dettaglio e avviare una nuova segnalazione guidata.

## Quale problema risolve

Le API proteggevano già i ticket personali, ma mancava una schermata utilizzabile senza
strumenti tecnici. L'area dipendente riunisce stato, priorità, servizio, sede,
aggiornamenti del supporto e soluzione finale in una vista leggibile e responsive.

## Pagine disponibili

- `GET /app` mostra riepilogo ed elenco personale quando il ruolo è `employee`;
- `GET /app?filter=active`, `waiting` o `completed` filtra l'elenco tramite i tre
  riepiloghi cliccabili;
- `GET /app/tickets/{ticket_id}` mostra il dettaglio di una richiesta personale;
- tecnico e amministratore vengono indirizzati alla coda completa dei ticket.

La voce “Nuova richiesta” apre il percorso descritto in
[`GUIDED_TICKET_INTAKE.md`](GUIDED_TICKET_INTAKE.md), che comprende descrizione libera,
eventuali domande integrative, riepilogo e conferma.

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

I filtri lavorano soltanto sull'insieme personale già autorizzato: `active` include gli
stati non conclusi, `waiting` le richieste in attesa del dipendente e `completed` gli
stati risolto o chiuso. I conteggi nei tre box restano complessivi e “Mostra tutti”
rimuove il filtro.

## Dove vengono salvati i dati

Elenco e dettaglio sono funzioni di sola lettura. Il percorso guidato salva invece una
bozza temporanea nella sessione e crea il ticket nel database soltanto dopo la conferma.
Ticket, sedi, utenti e sessioni risiedono nel database configurato. L'indice esistente su `requester_id` supporta
il filtro personale.

## Cosa può andare storto

- senza sessione valida il browser torna alla pagina di accesso;
- un ID non valido viene rifiutato dal percorso;
- un ticket assente o di un altro dipendente restituisce la stessa pagina privata `404`;
- sedi o tecnici non più disponibili ricevono un testo neutro, senza bloccare la pagina;
- un account senza richieste vede uno stato vuoto esplicativo.

## Chi può usare la funzionalità

L'elenco personale, il dettaglio e la creazione guidata sono destinati al ruolo
`employee`. Tecnico e amministratore consultano invece la coda completa attraverso la
loro interfaccia dedicata.

## Quali test dimostrano che funziona

I test HTTP creano dati fittizi per due dipendenti differenti e verificano che:

- l'elenco mostri soltanto i ticket dell'account corrente;
- il dettaglio personale mostri sede, categoria, tecnico e nota disponibili;
- il collegamento diretto a un ticket altrui restituisca `404` senza mostrare dati;
- un ID inesistente usi la stessa risposta privata;
- un dipendente senza ticket veda lo stato vuoto;
- i tre riepiloghi mostrino soltanto ticket attivi, in attesa o completati e permettano
  di tornare all'elenco completo;
- una persona anonima venga rimandata al login;
- tecnico e amministratore vengano indirizzati alla propria coda.
