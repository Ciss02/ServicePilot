# Classificazione AI suggerita

SP-052 classifica un ticket subito dopo la sua creazione confermata. SP-053 rende
esplicita la successiva verifica umana e gli errori controllati. L'AI propone
categoria, sottocategoria, impatto, urgenza e gruppo di supporto; ServicePilot controlla
la proposta e calcola autonomamente la priorità.

## Quale problema risolve

Il tecnico riceve un ticket già organizzato e può concentrarsi sulla verifica anziché
partire da campi vuoti. La pagina distingue la proposta AI dai valori verificati e
richiede una conferma esplicita del tecnico.

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
nuove tabelle o dipendenze. Il campo `classification_review_status` conserva soltanto
lo stato sicuro del processo, non la risposta grezza o il messaggio del provider.

Un ticket già classificato non viene inviato nuovamente al modello, evitando chiamate
doppie durante un reinvio della conferma.

## Cosa può andare storto

- l'AI può essere disattivata o non disponibile;
- la risposta può contenere valori fuori vocabolario;
- il salvataggio della classificazione può fallire;
- la proposta può essere valida ma non corretta dal punto di vista operativo.

In caso di provider non disponibile o risposta non valida il ticket resta creato e
utilizzabile. Il dettaglio tecnico mostra un messaggio distinto e invita a completare i
campi manualmente. Nessun valore non valido viene applicato e lo stesso fallimento non
produce chiamate ripetute durante un reinvio della conferma.

## Chi può usare la funzionalità

La classificazione è un'operazione interna del backend. Il dipendente deve confermare il
ticket prima che venga eseguita; soltanto tecnico e amministratore possono correggere e
registrare la verifica tramite pagina operativa o API tecnica.

## Quale test dimostra che funziona

I test usano modelli simulati e verificano:

- proposta valida tramite API e pagina web;
- rifiuto di categorie, livelli e gruppi sconosciuti;
- rifiuto della priorità proposta dal modello;
- calcolo backend dei casi P1, P2, P3 e P4 tramite la matrice già testata;
- salvataggio della proposta sul ticket confermato;
- assenza di una seconda chiamata per un ticket già classificato;
- creazione ancora funzionante quando l'AI è disattivata;
- stati distinti per proposta, timeout/provider non disponibile e risposta non valida;
- conferma umana esplicita soltanto con classificazione e gruppo completi;
- correzione del tecnico con priorità nuovamente calcolata dal backend.
