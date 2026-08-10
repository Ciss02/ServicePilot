# Dataset dimostrativo

SP-021 fornisce dati sintetici coerenti per sviluppare e mostrare ServicePilot senza
usare informazioni di persone o aziende reali.

## Contenuto

Il dataset comprende:

- 6 sedi: una sede centrale, uno stabilimento, un magazzino e tre punti vendita;
- 5 profili: tre dipendenti, un tecnico IT e un amministratore;
- 6 ticket che rappresentano produzione, rete, VPN, software, stampa e sicurezza.

I profili non hanno ancora password. SP-030 aggiungerà credenziali demo memorizzate in
modo sicuro.

## Come riconoscere i dati fittizi

- i codici delle sedi terminano con `-DEMO`;
- le email usano `@servicepilot.example`, un dominio riservato agli esempi;
- i titoli dei ticket iniziano con `[DEMO]`;
- nomi e descrizioni dichiarano esplicitamente il carattere dimostrativo.

## Caricamento

Dopo aver preparato l'ambiente locale, eseguire:

```powershell
.\.venv\Scripts\python.exe -m app.db seed
```

Il comando crea anche le tabelle mancanti. Può essere ripetuto: sedi e utenti vengono
riconosciuti rispettivamente tramite codice ed email, mentre i ticket demo vengono
riconosciuti dal loro titolo esplicito. I record già presenti vengono riallineati ai
valori approvati e non vengono creati duplicati.

Il caricamento non elimina righe estranee al dataset. Tutte le modifiche demo vengono
salvate insieme; in caso di errore la transazione viene annullata per non lasciare dati
parziali.

## Coerenza dei ticket

Ogni ticket punta a una sede e a un richiedente esistenti. Quando è assegnato, anche il
tecnico è un profilo demo valido. Impatto e urgenza provengono dal vocabolario del
progetto e la priorità viene calcolata dalla matrice deterministica del backend.

I test verificano caricamento ripetuto, conteggi, ripristino dei valori approvati,
conservazione di record estranei e coerenza delle priorità.

