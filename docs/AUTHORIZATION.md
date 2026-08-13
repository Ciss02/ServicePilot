# Autorizzazione per ruolo

ServicePilot applica l'identità della sessione alle API e alle pagine protette. I
controlli sono eseguiti dal backend: nascondere un pulsante nell'interfaccia non sarebbe
sufficiente, perché una persona potrebbe comunque chiamare direttamente l'API.

## Matrice dei permessi

| Operazione | `employee` | `technician` | `admin` |
| --- | --- | --- | --- |
| Creare un ticket | Sì, per sé | Sì, per sé | Sì, per sé |
| Elencare i ticket | Solo i propri | Tutti | Tutti |
| Leggere un dettaglio | Solo se proprio | Tutti | Tutti |
| Modificare tecnicamente | No | Sì | Sì |
| Funzioni amministrative | No | No | Sì |

Ogni account attivo può segnalare un proprio problema. Il campo `requester_id` non viene
più accettato da `POST /tickets`: il backend usa sempre l'identificativo della sessione,
quindi un browser non può creare un ticket a nome di un altro utente.

## Controlli condivisi

`app/api/dependencies.py` contiene tre livelli riutilizzabili:

- `CurrentUser` richiede una sessione valida e restituisce l'utente attivo;
- `TechnicalUser` accetta `technician` e `admin`;
- `AdminUser` accetta soltanto `admin`.

`AdminUser` protegge le operazioni riservate, tra cui gestione della knowledge base,
consultazione dell'audit e ripristino dei dati demo. Nascondere i relativi pulsanti agli
altri ruoli migliora l'esperienza, ma il controllo decisivo resta sempre nel backend.

## Risposte di sicurezza

- `401 Unauthorized`: sessione assente, sconosciuta, scaduta o non più valida;
- `403 Forbidden`: utente autenticato, ma ruolo non autorizzato all'operazione;
- `404 Not Found`: ticket inesistente oppure ticket altrui richiesto da un dipendente.

Per il dettaglio altrui viene usato `404` anziché `403`: in questo modo la risposta non
rivela al dipendente se quell'identificativo appartiene davvero a un altro ticket.

## Verifiche

I test coprono richieste anonime, proprietà del ticket, filtro dell'elenco, dettaglio
altrui nascosto, modifica negata al dipendente, gestione consentita a tecnico e admin e
controllo amministrativo consentito soltanto ad admin.
