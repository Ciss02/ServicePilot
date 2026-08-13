# API essenziali dei ticket

Le API REST salvano, leggono e gestiscono ticket reali nel database. La documentazione
interattiva è disponibile all'indirizzo `/docs`
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
stato `new`, date e risultato del tentativo di classificazione AI. Se il provider non è
disponibile, il ticket resta creato con classificazione vuota e stato di revisione
`ai_unavailable`. `confirmed` non viene conservato: è una condizione necessaria per
eseguire l'operazione, non una proprietà del ticket.

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
- confermare esplicitamente la revisione con `"classification_reviewed": true`;
- assegnare gruppo e tecnico;
- aggiungere una nota o una soluzione;
- cambiare lo stato seguendo il flusso consentito.

Il tecnico assegnato deve esistere, essere attivo e avere ruolo `technician` o `admin`.
La conferma della revisione richiede una classificazione completa; nella pagina web
richiede anche il gruppo. Il valore `false` non è accettato come conferma.
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

La matrice completa è documentata in [`AUTHORIZATION.md`](AUTHORIZATION.md). L'MVP non
espone ricerca testuale e paginazione nelle API; l'interfaccia tecnica offre invece i
filtri operativi necessari alla demo.

