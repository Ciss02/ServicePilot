# Dataset dimostrativo

SP-021 fornisce dati sintetici coerenti per sviluppare e mostrare ServicePilot senza
usare informazioni di persone o aziende reali.

## Contenuto

Il dataset comprende:

- 6 sedi: una sede centrale, uno stabilimento, un magazzino e tre punti vendita;
- 5 profili: tre dipendenti, un tecnico IT e un amministratore;
- 6 ticket che rappresentano produzione, rete, VPN, software, stampa e sicurezza;
- 3 azioni proposte sul ticket produttivo, una per ciascun tipo simulato.
- 9 eventi iniziali: creazione dei 6 ticket e proposta delle 3 azioni.

I profili ricevono credenziali configurate esternamente e nel database conservano
soltanto hash Argon2. Le istruzioni sono in [`DEMO_ACCOUNTS.md`](DEMO_ACCOUNTS.md).

## Come riconoscere i dati fittizi

- i codici delle sedi terminano con `-DEMO`;
- le email usano `@servicepilot.example`, un dominio riservato agli esempi;
- i titoli dei ticket iniziano con `[DEMO]`;
- nomi e descrizioni dichiarano esplicitamente il carattere dimostrativo.

## Caricamento

Dopo aver preparato l'ambiente locale e impostato le tre variabili descritte in
[`DEMO_ACCOUNTS.md`](DEMO_ACCOUNTS.md), eseguire:

```powershell
.\.venv\Scripts\python.exe -m app.db seed
```

Il comando crea anche le tabelle mancanti. Può essere ripetuto: sedi e utenti vengono
riconosciuti rispettivamente tramite codice ed email, mentre i ticket demo vengono
riconosciuti dal loro titolo esplicito. Le azioni demo vengono riconosciute tramite
ticket, tipo e motivazione. I record già presenti vengono riallineati ai valori
approvati e non vengono creati duplicati. Gli eventi iniziali hanno chiavi demo stabili:
un nuovo caricamento non riscrive né duplica la cronologia già presente.

Il caricamento non elimina righe estranee al dataset. Tutte le modifiche demo vengono
salvate insieme; in caso di errore la transazione viene annullata per non lasciare dati
parziali.

Le password non fanno parte del dataset versionato. Se una variabile manca o è troppo
corta, il caricamento viene rifiutato prima di aprire la transazione. Ripetere il comando
mantiene gli hash validi; cambiare una credenziale esterna aggiorna soltanto il relativo
hash.

## Coerenza dei ticket

Ogni ticket punta a una sede e a un richiedente esistenti. Quando è assegnato, anche il
tecnico è un profilo demo valido. Impatto e urgenza provengono dal vocabolario del
progetto e la priorità viene calcolata dalla matrice deterministica del backend.

I test verificano caricamento ripetuto, conteggi, ripristino dei valori approvati,
conservazione di record estranei, coerenza delle priorità e ritorno delle tre azioni
demo allo stato `pending_approval`, oltre alle 9 righe iniziali di audit senza duplicati.

