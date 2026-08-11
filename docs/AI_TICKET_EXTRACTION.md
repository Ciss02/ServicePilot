# Estrazione AI dei dati del ticket

SP-051 collega l'adapter AI alla prima domanda della raccolta guidata. Il dipendente può
descrivere liberamente il problema; ServicePilot prepara i dati riconoscibili e chiede
soltanto le informazioni che non può ricavare con sicurezza.

## Quale problema risolve

Il dipendente non deve trasformare da solo il proprio racconto in un modulo completo.
Se descrive, per esempio, servizio, sede e numero di persone coinvolte, questi dati non
vengono richiesti una seconda volta. Il riepilogo e la conferma esplicita restano
obbligatori: l'AI prepara una bozza, ma non crea autonomamente il ticket.

## Quali dati riceve

Il componente riceve:

- la descrizione libera, già controllata dal backend;
- codice e nome delle sole sedi attive presenti nel database.

L'AI può restituire titolo, codice della sede, servizio coinvolto e numero di persone.
Ogni campo non ricavabile senza supposizioni deve essere `null`.

## Dove vengono controllati

La risposta deve rispettare `AIExtractedTicketDetails`, uno schema Pydantic che vieta
campi inattesi e applica gli stessi limiti del ticket. Il backend verifica inoltre che
il codice della sede appartenga davvero all'elenco inviato. La lista dei dati mancanti
viene calcolata da ServicePilot e non viene accettata come decisione libera del modello.

Le istruzioni dicono al modello di ignorare eventuali comandi scritti nella descrizione,
di non classificare ancora il ticket e di non inventare informazioni. Categoria,
impatto e urgenza appartengono alla successiva attività SP-052.

## Dove vengono salvati

L'estrazione non salva prompt, risposte o bozze nel database. I valori passano tra le
pagine del modulo e vengono controllati di nuovo prima della creazione. Soltanto il
pulsante `Conferma e crea ticket` salva il ticket, come nel flusso precedente.

## Cosa può andare storto

- il provider AI può essere disattivato o non disponibile;
- alcuni dati possono non comparire nella descrizione;
- la risposta può avere una forma non valida;
- il modello può indicare una sede che non appartiene all'elenco consentito.

Se l'AI è disattivata o restituisce un errore controllato, il percorso manuale resta
disponibile e chiede i quattro dati essenziali. La gestione visibile più completa di
timeout e altri errori del provider verrà affrontata in SP-053.

## Chi può usare la funzionalità

Il percorso resta riservato al ruolo `employee`. Tecnici e amministratori continuano a
essere rimandati alla propria area. La chiave Gemini rimane soltanto sul server.

## Quale test dimostra che funziona

I test usano modelli simulati, senza rete e senza consumo di chiamate Gemini, e verificano:

- estrazione completa e passaggio diretto al riepilogo;
- richiesta dei soli campi mancanti;
- corrispondenza tra sede estratta e sedi attive;
- rifiuto di campi inattesi, valori fuori limite e sedi non consentite;
- mancata creazione del ticket prima della conferma;
- disponibilità del percorso manuale quando l'AI è disattivata.
