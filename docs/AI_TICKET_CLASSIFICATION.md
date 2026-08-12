# Classificazione AI suggerita

SP-052 classifica un ticket subito dopo la sua creazione confermata. L'AI propone
categoria, sottocategoria, impatto, urgenza e gruppo di supporto; ServicePilot controlla
la proposta e calcola autonomamente la priorità.

## Quale problema risolve

Il tecnico riceve un ticket già organizzato e può concentrarsi sulla verifica anziché
partire da campi vuoti. La proposta non sostituisce la decisione umana: SP-053 renderà
più esplicite revisione, correzione e gestione degli errori.

## Quali dati riceve

Il modello riceve soltanto dati già confermati e fittizi:

- titolo e descrizione;
- servizio coinvolto;
- numero di persone interessate;
- codice e nome della sede;
- categorie, livelli e gruppi ammessi dal backend.

Non riceve password, chiavi API o dati di altri ticket.

## Dove vengono controllati

La risposta deve rispettare `AIProposedTicketClassification`. Categoria, impatto,
urgenza e gruppo sono valori chiusi: un codice o un gruppo inventato viene rifiutato.
La sottocategoria è un testo breve oppure `null`. Anche campi aggiuntivi vengono
rifiutati, compreso un eventuale campo `priority` inviato dal modello.

ServicePilot trasforma poi la proposta in `TicketClassificationSuggestion` e usa la
matrice deterministica `impatto × urgenza` per aggiungere la priorità.

## Dove vengono salvati

Solo dopo la conferma del dipendente il backend crea il ticket. La classificazione viene
quindi salvata nei campi già esistenti della tabella `tickets`: categoria,
sottocategoria, impatto, urgenza, priorità e gruppo assegnato. Non sono state aggiunte
nuove tabelle o dipendenze.

Un ticket già classificato non viene inviato nuovamente al modello, evitando chiamate
doppie durante un reinvio della conferma.

## Cosa può andare storto

- l'AI può essere disattivata o non disponibile;
- la risposta può contenere valori fuori vocabolario;
- il salvataggio della classificazione può fallire;
- la proposta può essere valida ma non corretta dal punto di vista operativo.

Nei primi tre casi il ticket confermato resta creato e utilizzabile, ma senza proposta.
La segnalazione visibile dell'errore e gli strumenti di revisione appartengono a SP-053.

## Chi può usare la funzionalità

La classificazione è un'operazione interna del backend. Il dipendente deve confermare il
ticket prima che venga eseguita; tecnico e amministratore vedono poi i valori nel
dettaglio operativo esistente.

## Quale test dimostra che funziona

I test usano modelli simulati e verificano:

- proposta valida tramite API e pagina web;
- rifiuto di categorie, livelli e gruppi sconosciuti;
- rifiuto della priorità proposta dal modello;
- calcolo backend dei casi P1, P2, P3 e P4 tramite la matrice già testata;
- salvataggio della proposta sul ticket confermato;
- assenza di una seconda chiamata per un ticket già classificato;
- creazione ancora funzionante quando l'AI è disattivata.
