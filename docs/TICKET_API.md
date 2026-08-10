# API essenziali dei ticket

SP-022 e SP-023 introducono le operazioni REST che salvano, leggono e gestiscono ticket
reali dal database. La documentazione interattiva è disponibile all'indirizzo `/docs`
mentre il server è in esecuzione.

## Creazione

`POST /tickets` accetta i dati di `TicketCreate`:

```json
{
  "title": "Accesso VPN non disponibile",
  "description": "La VPN demo mostra un errore prima del collegamento.",
  "site_id": 1,
  "service": "Accesso remoto",
  "affected_users": 1,
  "confirmed": true
}
```

Il backend verifica forma e limiti dei dati, richiede la conferma esplicita e controlla
che la sede esista. Il richiedente è sempre l'utente autenticato: inviare manualmente
`requester_id` produce `422`. Se il salvataggio riesce restituisce `201 Created` con ID,
stato `new`, date e classificazione inizialmente vuota. `confirmed` non viene conservato:
è una condizione necessaria per eseguire l'operazione, non una proprietà del ticket.

## Lettura

- per `employee`, `GET /tickets` restituisce soltanto i ticket propri;
- per `technician` e `admin`, `GET /tickets` restituisce l'intera coda;
- `GET /tickets/{ticket_id}` applica la stessa regola al dettaglio.

La risposta segue `TicketRead` e comprende dati iniziali, classificazione, assegnazione,
stato, note, soluzione e date. I campi non ancora valorizzati sono `null`.

## Gestione tecnica

`PATCH /tickets/{ticket_id}` accetta uno o più campi di `TicketUpdate`. Il tecnico può:

- correggere titolo, descrizione, sede, servizio e numero di utenti coinvolti;
- applicare una classificazione completa, con priorità ricalcolata dal backend;
- assegnare gruppo e tecnico;
- aggiungere una nota o una soluzione;
- cambiare lo stato seguendo il flusso consentito.

Il tecnico assegnato deve esistere, essere attivo e avere ruolo `technician` o `admin`.
Il richiedente non è modificabile. Tutti i controlli avvengono prima del salvataggio,
quindi un errore non lascia modifiche parziali. L'endpoint accetta soltanto utenti con
ruolo `technician` o `admin`.

## Ciclo di vita

| Stato attuale | Passaggi consentiti |
| --- | --- |
| `new` | `in_progress` |
| `in_progress` | `waiting_for_requester`, `waiting_for_vendor`, `resolved` |
| `waiting_for_requester` | `in_progress`, `resolved` |
| `waiting_for_vendor` | `in_progress`, `resolved` |
| `resolved` | `in_progress`, `closed` |
| `closed` | Nessuno: è lo stato finale. |

Ripetere lo stesso stato è accettato quando la richiesta modifica anche altri dati. Per
passare a `resolved` o `closed` deve essere disponibile una soluzione testuale.

## Errori principali

| Codice | Significato |
| --- | --- |
| `401` | Sessione non valida o assente. |
| `403` | Ruolo autenticato ma non autorizzato. |
| `404` | Sede o ticket non esistente; per un dipendente include i ticket altrui. |
| `409` | Transizione non consentita o riferimenti rifiutati dal database. |
| `422` | Corpo non valido, tecnico non idoneo o soluzione obbligatoria assente. |

Un errore annulla la transazione e non lascia ticket parziali.

La matrice completa è documentata in [`AUTHORIZATION.md`](AUTHORIZATION.md). Filtri di
ricerca e paginazione appartengono ad attività successive.

