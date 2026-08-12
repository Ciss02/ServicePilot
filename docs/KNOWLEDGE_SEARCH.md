# Indicizzazione e ricerca della knowledge base

SP-062 trasforma i segmenti di SP-061 in vettori confrontabili e recupera i passaggi
più pertinenti rispetto a una domanda tecnica. SP-063 riutilizza questi risultati per
generare un suggerimento tecnico con fonti verificabili; SP-064 impedisce la generazione
quando nessun risultato raggiunge la soglia prudenziale `0,55`.

## Quale problema risolve

Una ricerca per parola trova soltanto termini uguali. Gli embedding rappresentano
invece il significato generale di un testo con una lista di numeri. In questo modo una
domanda come `la connessione remota cade` può recuperare una procedura che parla di
`VPN intermittente`, anche se le frasi non sono identiche.

## Dati ricevuti

L'indicizzazione riceve:

- il testo dei segmenti già estratti;
- il modello e la dimensione configurati;
- il documento, la posizione e la sezione già presenti nel database.

La ricerca riceve una domanda da 3 a 500 caratteri e restituisce al massimo i tre
segmenti più simili per impostazione predefinita.

## Dove vengono controllati

L'adapter verifica che Gemini restituisca:

- un vettore per ciascun segmento;
- esattamente il numero di dimensioni configurato;
- soltanto numeri finiti;
- un vettore non vuoto e normalizzabile.

I vettori vengono normalizzati prima del salvataggio. La ricerca usa la similarità del
coseno: due vettori che puntano nella stessa direzione ricevono un punteggio più alto.
Il punteggio ordina i risultati, ma non è una certezza o una decisione tecnica.
Per la generazione RAG, i risultati sotto `0,55` vengono esclusi prima della chiamata al
modello. Il laboratorio amministrativo continua invece a mostrarli per rendere possibile
la valutazione e la futura calibrazione della soglia.

## Dove vengono salvati

Ogni riga di `knowledge_segments` conserva il proprio vettore come JSON. Il documento
registra inoltre:

- stato `pending`, `ready` o `failed`;
- modello e dimensione usati;
- data dell'indicizzazione;
- errore controllato, quando presente.

Modello e dimensione impediscono di confrontare per errore vettori incompatibili. Una
nuova indicizzazione sostituisce l'intero indice del documento senza lasciare risultati
parziali o mescolare versioni diverse.

## Configurazione e costo

L'indicizzazione è disattivata per impostazione predefinita. Per provarla con dati
esclusivamente fittizi, aggiungere al file `.env` locale:

```text
SERVICEPILOT_EMBEDDING_PROVIDER=gemini
SERVICEPILOT_EMBEDDING_MODEL=gemini-embedding-001
SERVICEPILOT_EMBEDDING_DIMENSIONS=768
GEMINI_API_KEY=la-chiave-locale
```

Il file `.env` è escluso da Git. Il modello testuale stabile
[`gemini-embedding-001`](https://ai.google.dev/gemini-api/docs/models/gemini-embedding-001)
supporta dimensioni da 128 a 3.072; ServicePilot usa 768 come equilibrio tra qualità e
spazio occupato. Secondo il
[listino ufficiale Gemini](https://ai.google.dev/gemini-api/docs/pricing), il free tier
è gratuito e il piano a pagamento indica 0,15 USD per milione di token di input. Prezzi
e limiti possono cambiare: verificare sempre il listino prima di un uso non dimostrativo.

## Cosa può andare storto

- provider disattivato: il testo resta `Da indicizzare` e l'upload non viene perso;
- timeout o errore Gemini: il documento resta conservato senza indice parziale;
- vettori errati: l'indice viene rifiutato;
- modello cambiato: i vecchi vettori non vengono confrontati con quelli nuovi;
- domanda vuota o troppo lunga: la ricerca viene fermata prima della chiamata.

La futura reindicizzazione amministrativa permetterà di riallineare documenti creati
con un modello precedente. La soglia iniziale di SP-064 dovrà essere rivalutata quando
sarà disponibile un insieme più ampio di domande e procedure dimostrative.

## Chi può usare la funzionalità

Il laboratorio visibile è riservato all'amministratore, come l'upload. Il servizio di
ricerca è separato dalla pagina ed è riutilizzato nel dettaglio tecnico da SP-063.
Dipendenti e tecnici non possono modificare l'indice tramite questa attività.

## Quale test dimostra che funziona

- l'adapter Gemini simulato usa i compiti `RETRIEVAL_DOCUMENT` e `RETRIEVAL_QUERY`;
- vettori errati, vuoti o incompatibili vengono rifiutati;
- un provider disattivato lascia il documento pronto da indicizzare;
- una domanda sulla connessione remota recupera per prima la procedura VPN nota;
- ogni risultato conserva documento, sezione, testo e punteggio;
- risultati assenti o tutti sotto soglia non avviano la generazione AI;
- il percorso web mostra risultati ordinati senza chiamate Gemini reali;
- un database precedente riceve i campi dell'indice senza perdere dati.

