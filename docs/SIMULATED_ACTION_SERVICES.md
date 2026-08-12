# Servizi REST simulati per le azioni

SP-071 aggiunge una piccola applicazione FastAPI separata dal portale principale. I
suoi tre endpoint imitano integrazioni operative senza assegnare ticket reali, inviare
messaggi o contattare fornitori.

## Quale problema risolve

La demo deve mostrare cosa accade dopo l'approvazione di un'azione anche se non dispone
di sistemi aziendali esterni. I simulatori forniscono risposte HTTP realistiche e
permettono di provare sia il percorso positivo sia la gestione di un guasto.

## Quali dati riceve

Ogni richiesta contiene:

- `request_id`: codice UUID che identifica il tentativo;
- `ticket_id`: identificativo positivo del ticket nel portale;
- `simulation_scenario`: `success` oppure `service_unavailable`;
- `payload`: gli stessi dati specifici già controllati dalla proposta.

Gli endpoint sono:

| Metodo e percorso | Dati specifici | Effetto esclusivamente fittizio |
| --- | --- | --- |
| `POST /assignments` | gruppo e/o tecnico | registra un'assegnazione demo |
| `POST /requester-communications` | messaggio | registra una comunicazione demo |
| `POST /vendor-escalations` | fornitore e riepilogo | apre un'escalation demo |

## Dove vengono controllati

Pydantic controlla UUID, identificativi positivi, lunghezze, vocabolari e campi
aggiuntivi. I payload riusano i contratti di SP-070, quindi un'assegnazione continua a
richiedere almeno un gruppo o un tecnico e nessun endpoint accetta comandi generici.

## Dove vengono salvati

SP-071 non salva dati. Con `success` restituisce `200`, stato `succeeded`, messaggio e
un riferimento stabile derivato dal `request_id`. Ripetere la stessa richiesta produce
lo stesso risultato, senza duplicare effetti perché non esistono effetti reali.

La futura SP-072 collegherà questi servizi alle proposte approvate; SP-073 conserverà
l'approvazione e l'esito nell'audit log.

## Cosa può andare storto

- dati non validi: risposta `422`, senza eseguire la simulazione;
- scenario `service_unavailable`: risposta controllata `503`, stato `failed`, codice
  `simulated_service_unavailable` e indicazione che il tentativo è ripetibile;
- richiesta duplicata: stesso riferimento e stessa risposta;
- simulatore non avviato: il futuro chiamante dovrà gestire l'indisponibilità come un
  errore esterno, senza fingere un successo.

Gli errori sono scelti esplicitamente e non casuali, così i test sono riproducibili.

## Chi può usare la funzionalità

I simulatori sono destinati soltanto al backend locale. Non sono inclusi
nell'applicazione `app.main`, quindi non diventano endpoint del portale e oggi non sono
raggiungibili dalle sue pagine o dalle sue sessioni utente.

Per una prova manuale locale possono essere avviati soltanto sull'indirizzo di loopback:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.simulated_services.main:app `
  --host 127.0.0.1 --port 8011
```

La documentazione interattiva sarà disponibile in `http://127.0.0.1:8011/docs` e lo
stato minimo in `http://127.0.0.1:8011/health`. Non sono necessarie chiavi API.

## Quale test dimostra che funziona

- tutti e tre gli endpoint restituiscono un successo coerente;
- ripetere la richiesta restituisce lo stesso riferimento;
- tutti e tre producono un `503` ripetibile nello scenario di errore;
- UUID, ticket, payload e campi inattesi vengono controllati;
- gli endpoint simulati risultano assenti dalle rotte del portale principale.

I test usano richieste HTTP locali in memoria e dati completamente fittizi. Non
chiamano Gemini, la rete, servizi di messaggistica o sistemi di fornitori.
