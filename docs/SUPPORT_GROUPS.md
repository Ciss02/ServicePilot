# Gruppi di supporto

ServicePilot conserva i gruppi tecnici in un catalogo amministrabile. Lo stesso elenco
dei gruppi attivi alimenta sia il modulo di assegnazione sia la classificazione AI.

## Quale problema risolve

I gruppi non sono più una lista fissa nel codice. Un amministratore può aggiungerli,
rinominarli, descriverli e disattivarli, oltre a collegare ogni tecnico o amministratore
a uno o più gruppi.

## Quali dati riceve

- nome univoco da 2 a 100 caratteri;
- descrizione da 2 a 500 caratteri;
- stato attivo o non attivo;
- identificativi degli account tecnici attivi selezionati come membri.

## Dove vengono controllati

Il backend normalizza spazi e maiuscole per impedire nomi duplicati. Le appartenenze
accettano soltanto account attivi con ruolo `technician` o `admin`: un dipendente non
può diventare membro neppure inviando manualmente il modulo.

Una nuova assegnazione viene accettata soltanto se il nome coincide con un gruppo attivo
nel database. La classificazione AI riceve la stessa lista e una proposta fuori elenco
viene scartata integralmente.

## Dove vengono salvati

- `support_groups` contiene nome, chiave normalizzata, descrizione, stato e date;
- `support_group_memberships` contiene il collegamento molti-a-molti tra gruppi e utenti;
- `tickets.assigned_group` resta un testo storico, così rinomina e disattivazione non
  riscrivono i ticket già registrati.

La migrazione `0003_support_groups` crea le nuove tabelle. Il seed demo inserisce sette
gruppi fittizi e appartenenze ripetibili.

## Cosa può andare storto

- un nome può essere duplicato o fuori limite;
- un membro può non esistere, essere inattivo o avere ruolo dipendente;
- un gruppo può essere disattivato mentre un ticket lo conserva nello storico;
- il database può rifiutare il salvataggio.

In questi casi l'operazione viene annullata e l'interfaccia mostra un messaggio
controllato. La disattivazione non elimina gruppo, appartenenze o testo storico.

## Chi può usare la funzionalità

Solo l'amministratore può aprire `/app/admin/groups` e modificare catalogo o membri.
La pagina mantiene compatto il catalogo: il modulo di creazione si apre dal pulsante
**Nuovo gruppo**, mentre le appartenenze correnti sono mostrate come etichette rimovibili
e i nuovi membri si aggiungono da un selettore che propone soltanto gli account idonei
non ancora presenti nel gruppo.
Tecnici e amministratori possono scegliere un gruppo attivo durante la gestione ticket;
il dipendente vede soltanto l'eventuale assegnazione del proprio ticket.

## Quale test dimostra che funziona

I test verificano unicità, appartenenze multiple, rifiuto dei dipendenti, seed
ripetibile, permessi web, classificazione limitata all'elenco attivo e conservazione del
testo storico dopo rinomina o disattivazione.
