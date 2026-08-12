# Adapter del modello AI

Questo documento descrive la base introdotta con SP-050. Da SP-051 l'adapter è usato
dalla raccolta guidata per estrarre i dati presenti nella descrizione; da SP-052 usa lo
stesso contratto per classificare il ticket confermato.

## Quale problema risolve

ServicePilot non dipende direttamente da Gemini. Il resto dell'applicazione conosce
soltanto il contratto `AIModel`, che riceve un testo e lo schema Pydantic della risposta
attesa. In questo modo Gemini può essere sostituito nei test o in futuro senza cambiare
il flusso dei ticket.

```text
ServicePilot -> AIModel -> GeminiAIModel -> Gemini API
                    `----> modello finto nei test
```

## Quali dati riceve

L'operazione `generate_structured` riceve:

- il testo da analizzare;
- eventuali istruzioni di sistema;
- lo schema esatto che la risposta deve rispettare.

Gli schemi specifici sono spiegati in `docs/AI_TICKET_EXTRACTION.md` e
`docs/AI_TICKET_CLASSIFICATION.md`.

## Dove vengono controllati

Gemini viene invitato a produrre JSON secondo lo schema richiesto. La risposta viene poi
controllata nuovamente da Pydantic nel backend. Una risposta vuota, incompleta o di forma
errata produce `AIInvalidResponseError` e non viene passata al resto dell'applicazione.

## Dove vengono salvati

L'adapter non salva prompt o risposte nel database. SP-050 non crea né modifica ticket.
La chiave API viene letta dall'ambiente e non viene stampata, salvata o inclusa nel
repository.

## Configurazione

L'AI è disattivata per impostazione predefinita, quindi applicazione e test funzionano
senza chiave e senza rete.

| Variabile | Valore predefinito | Scopo |
|---|---|---|
| `SERVICEPILOT_AI_PROVIDER` | `disabled` | Attiva `gemini` soltanto quando richiesto |
| `SERVICEPILOT_AI_MODEL` | `gemini-3.5-flash-lite` | Sceglie il modello senza cambiare codice |
| `GEMINI_API_KEY` | vuoto | Chiave locale necessaria soltanto per Gemini |
| `SERVICEPILOT_AI_TIMEOUT_SECONDS` | `15` | Interrompe richieste troppo lente |
| `SERVICEPILOT_AI_MAX_ATTEMPTS` | `2` | Limita il tentativo iniziale e l'eventuale retry |
| `SERVICEPILOT_AI_MAX_OUTPUT_TOKENS` | `1024` | Limita lunghezza e costo della risposta |
| `SERVICEPILOT_AI_REQUESTS_PER_MINUTE` | `10` | Ferma picchi di richieste prima della rete |
| `SERVICEPILOT_AI_REQUESTS_PER_DAY` | `100` | Impone un tetto giornaliero locale alla demo |

Per una prova manuale, copiare `.env.example` in `.env`, impostare soltanto dati
fittizi e avviare Uvicorn caricando quel file:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file .env
```

Il file `.env` è escluso da Git. Non inserire mai la chiave in `.env.example`, nei test,
nei comandi salvati o nella documentazione.

## Cosa può andare storto

- provider o limiti possono essere configurati con valori non ammessi;
- la chiave può mancare quando Gemini è attivo;
- la richiesta può superare il timeout;
- Gemini può restituire un errore o dati non conformi allo schema.
- il limite locale per minuto o giorno può essere raggiunto.

L'adapter trasforma questi casi in errori comuni di ServicePilot senza mostrare la
chiave o i dettagli interni del provider. La gestione visibile e il percorso di
ripiego verranno collegati all'interfaccia in SP-053.

## Chi può usarlo

L'adapter è un componente interno del backend. Non espone nuovi endpoint e non cambia i
permessi dei ruoli. Le funzionalità future continueranno ad applicare autorizzazione e
conferma nel backend.

## Quale test dimostra che funziona

I test in `tests/ai/` usano un client Gemini simulato e verificano:

- configurazione disattivata senza chiave;
- chiave assente dalle rappresentazioni e dagli errori;
- scelta del provider tramite factory;
- schema JSON, timeout, retry e limite di output inviati all'SDK;
- chiusura del client dopo ogni uso;
- rifiuto di risposte vuote o non valide;
- sostituzione di Gemini con un modello finto senza chiamate esterne.
- blocco di generazione ed embedding prima di costruire il client quando la quota è finita.

I limiti locali sono condivisi tra generazione ed embedding nel singolo processo. Limiti
residui e protezioni da applicare nel deploy sono documentati in
[`SECURITY_AND_DEMO_LIMITS.md`](SECURITY_AND_DEMO_LIMITS.md).
