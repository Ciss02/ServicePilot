# Istruzioni di lavoro per Codex

## Obiettivo del progetto

ServicePilot AI è un'applicazione portfolio per la gestione intelligente dei ticket IT.
La specifica approvata è `docs/ServicePilot_AI_MVP_Specification.md`.

## Documenti da leggere prima di lavorare

Prima di modificare il progetto:

1. leggere `docs/ServicePilot_AI_MVP_Specification.md`;
2. leggere `docs/PROJECT_STATUS.md`;
3. individuare in `docs/PROJECT_PLAN.md` l'attività concordata con l'utente;
4. controllare lo stato di Git e le modifiche già presenti.

## Regole di collaborazione

- Comunicare in italiano, salvo richiesta diversa.
- Spiegare prima di ogni passaggio cosa verrà fatto e perché, usando parole semplici.
- Lavorare normalmente su una sola attività della tasklist per sessione.
- Non ampliare il perimetro dell'attività senza segnalarlo all'utente.
- Non sostituire una scelta della specifica senza registrare e spiegare la decisione.
- Conservare solo dati fittizi; non usare dati del datore di lavoro o di persone reali.
- Non inserire password, token o chiavi API nel repository.
- Spiegare lo scopo di una nuova dipendenza prima di aggiungerla.
- Preferire modifiche piccole, comprensibili e facili da verificare.

## Verifica del lavoro

- Non dichiarare completata un'attività solo perché il codice è stato scritto.
- Eseguire i controlli e i test pertinenti.
- Spiegare cosa è stato verificato e segnalare ciò che non è stato possibile verificare.
- Aggiornare `docs/PROJECT_STATUS.md` al termine di ogni attività completata.
- Aggiornare la casella corrispondente in `docs/PROJECT_PLAN.md` solo dopo la verifica.
- Prima di un commit, riepilogare modifiche e controlli eseguiti.
- Non pubblicare su GitHub o effettuare deploy senza richiesta esplicita dell'utente.

## Criterio di apprendimento

Per ogni funzionalità aiutare l'utente a rispondere a queste domande:

1. Quale problema risolve?
2. Quali dati riceve?
3. Dove vengono controllati?
4. Dove vengono salvati?
5. Cosa può andare storto?
6. Chi può usare la funzionalità?
7. Quale test dimostra che funziona?
