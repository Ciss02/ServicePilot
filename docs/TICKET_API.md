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
  "requester_id": 1,
  "site_id": 1,
  "service": "Accesso remoto",
  "affected_users": 1,
  "confirmed": true
}
```

Il backend verifica forma e limiti dei dati, richiede la conferma esplicita e controlla
che richiedente e sede esistano. Se il salvataggio riesce restituisce `201 Created` con
ID, stato `new`, date e classificazione inizialmente vuota. `confirmed` non viene
conservato: è una condizione necessaria per eseguire l'operazione, non una proprietà del
ticket.

## Lettura

- `GET /tickets` restituisce tutti i ticket dal più recente;
- `GET /tickets/{ticket_id}` restituisce il dettaglio di un ticket.

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
quindi un errore non lascia modifiche parziali.

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
| `404` | Richiedente, sede o ticket non esistente. |
| `409` | Transizione non consentita o riferimenti rifiutati dal database. |
| `422` | Corpo non valido, tecnico non idoneo o soluzione obbligatoria assente. |

Un errore annulla la transazione e non lascia ticket parziali.

## Limiti attuali

Le API non sono ancora protette da login e permessi. In particolare, l'elenco non è
filtrato per richiedente e `PATCH` non identifica ancora chi invia la modifica: servono
alla costruzione del backend e non devono essere esposti come funzioni pubbliche.
SP-030, SP-031 e SP-032 aggiungeranno account sicuri, sessioni e autorizzazione. Filtri
e paginazione appartengono ad attività successive.

