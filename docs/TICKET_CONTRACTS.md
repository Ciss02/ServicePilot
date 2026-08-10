# ServicePilot AI - Contratti dati del ticket

I contratti descrivono la forma dei dati accettati e restituiti dal backend. Sono
implementati in `app/domain/ticket_contracts.py` usando Pydantic e vengono utilizzati
dalle API dei ticket.

Questi controlli verificano la forma dei dati. I permessi, per esempio se un dipendente
può modificare uno specifico ticket, verranno aggiunti nel backend nelle attività
dedicate all'autenticazione e all'autorizzazione.

## Creazione del ticket

`TicketCreate` rappresenta la richiesta confermata dal dipendente.

| Campo | Tipo e regola | Motivo |
| --- | --- | --- |
| `title` | Testo, 5-120 caratteri | Riassume il problema. |
| `description` | Testo, 10-4000 caratteri | Contiene le informazioni utili alla diagnosi. |
| `requester_id` | Intero positivo | Collega il ticket al richiedente. |
| `site_id` | Intero positivo | Identifica la sede coinvolta. |
| `service` | Testo, 2-100 caratteri | Indica il servizio interessato. |
| `affected_users` | Intero da 1 a 10.000 | Misura quante persone sono coinvolte. |
| `confirmed` | Deve essere `true` | Impedisce la creazione prima della conferma. |

Il contratto non accetta campi aggiuntivi. Identificativo del ticket, stato iniziale,
date e audit saranno assegnati dal backend. La classificazione avviene dopo la creazione,
come previsto dal flusso della specifica.

## Classificazione

`TicketClassification` richiede:

- una categoria del vocabolario;
- una sottocategoria facoltativa;
- impatto e urgenza;
- nessuna priorità fornita dall'esterno.

La proprietà `priority` viene calcolata automaticamente dalla matrice deterministica.
Impatto e urgenza devono essere presenti insieme, così il risultato è sempre completo.

## Aggiornamento

`TicketUpdate` accetta uno o più di questi campi:

- titolo, descrizione, sede, servizio e numero di utenti coinvolti;
- stato;
- classificazione completa;
- gruppo o tecnico assegnato;
- nota tecnica o soluzione.

Una richiesta vuota o composta soltanto da valori nulli viene rifiutata perché non
produrrebbe alcun cambiamento. Il richiedente non è modificabile tramite questo contratto:
un eventuale trasferimento di proprietà richiederebbe una funzione amministrativa
esplicita, fuori dal perimetro attuale.

## Lettura

`TicketRead` rappresenta un ticket salvato. Oltre ai dati iniziali include ID, stato,
classificazione facoltativa, assegnazione, note, soluzione e date. Può leggere
direttamente un modello SQLAlchemy, mantenendo separata la struttura della risposta
dalla tabella del database.

## Cosa non viene ancora gestito

- controllo dei permessi per ruolo e proprietà del ticket;
- allegati;
- transizioni consentite tra stati;
- date, cronologia e audit trail;
- azioni dell'agente e fonti della knowledge base.

Queste responsabilità appartengono alle successive attività del piano e non vengono
simulate nei contratti.
