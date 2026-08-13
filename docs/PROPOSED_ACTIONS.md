# Modello delle azioni proposte

Una proposta descrive un possibile passo successivo suggerito dall'agente, ma non lo
applica al ticket senza una decisione umana. Dopo l'approvazione, ServicePilot chiama un
servizio REST simulato e registra decisione, tentativo e risultato nell'audit.

## Quale problema risolve

Un testo generato dall'AI non deve trasformarsi direttamente in un effetto operativo.
La proposta crea un confine controllabile tra ciò che l'agente consiglia e ciò che un
tecnico decide di autorizzare.

## Quali dati riceve

Ogni proposta contiene:

- il ticket al quale appartiene;
- uno dei tre tipi ammessi;
- una motivazione tra 20 e 1.000 caratteri;
- dati specifici per il tipo di azione;
- l'effetto previsto, tra 10 e 1.000 caratteri.

I dati specifici sono:

- assegnazione: gruppo controllato e/o identificativo del tecnico;
- comunicazione: messaggio destinato al richiedente;
- escalation: nome fittizio del fornitore e riepilogo del problema.

## Dove vengono controllati

I contratti Pydantic rifiutano tipi sconosciuti, campi aggiuntivi, testi troppo brevi o
lunghi e dati che non corrispondono al tipo dichiarato. Un'assegnazione deve indicare
almeno un gruppo o un tecnico. Il database limita inoltre tipo e stato ai valori del
vocabolario condiviso.

## Dove vengono salvati

La tabella `proposed_actions` conserva tipo, motivazione, payload JSON normalizzato,
effetto previsto, stato, decisione, risultato e date. La proposta è collegata al ticket
e viene eliminata insieme a esso. Lo stato iniziale viene deciso dal backend ed è sempre
`pending_approval`; i campi operativi vengono completati dal servizio di approvazione.

La funzione che crea la proposta non compila decisione o risultato e non riceve alcun
client REST. Questi campi vengono aggiornati soltanto dal flusso di approvazione: il
semplice salvataggio della proposta non può quindi eseguire accidentalmente un'azione.

## Cosa può andare storto

- tipo e payload non corrispondono: la proposta viene rifiutata prima del database;
- ticket inesistente: il collegamento viene rifiutato e non resta una riga parziale;
- JSON salvato non leggibile: la proposta non viene restituita come affidabile;
- errore del database: la transazione viene annullata;
- proposta non approvata: resta in attesa e non produce effetti.

## Chi può usare la funzionalità

Tecnico e amministratore possono approvare o rifiutare le proposte dal dettaglio del
ticket. Il dipendente non può autorizzare azioni operative e il backend verifica il
ruolo anche se qualcuno prova a inviare direttamente una richiesta.

## Quale test dimostra che funziona

- tutti e tre i tipi vengono salvati con stato `pending_approval`;
- assegnazione, nota, stato e soluzione del ticket rimangono invariati;
- i payload errati o incoerenti vengono rifiutati;
- un ticket inesistente impedisce il salvataggio;
- il JSON viene ricaricato nel contratto specifico corretto;
- dati memorizzati corrotti producono un errore controllato;
- la creazione del database rimane ripetibile.

I test usano soltanto dati fittizi e non chiamano Gemini o servizi esterni.
