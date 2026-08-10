# API essenziali dei ticket

SP-022 introduce le prime operazioni REST che salvano e leggono ticket reali dal
database. La documentazione interattiva è disponibile all'indirizzo `/docs` mentre il
server è in esecuzione.

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

## Errori principali

| Codice | Significato |
| --- | --- |
| `404` | Richiedente, sede o ticket non esistente. |
| `409` | Il database rifiuta i riferimenti durante il salvataggio. |
| `422` | Il corpo o l'identificativo non rispettano il contratto. |

Un errore annulla la transazione e non lascia ticket parziali.

## Limiti attuali

Le API non sono ancora protette da login e permessi. In particolare, l'elenco non è
filtrato per richiedente: serve alla costruzione del backend e non deve essere esposto
come funzione pubblica. SP-030, SP-031 e SP-032 aggiungeranno account sicuri, sessioni e
autorizzazione. Filtri, paginazione e modifiche tecniche appartengono a SP-023 e alle
attività successive.

