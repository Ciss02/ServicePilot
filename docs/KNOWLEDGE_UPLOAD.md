# Upload sicuro dei documenti

SP-060 introduce il primo passaggio della knowledge base: l'amministratore può
caricare una procedura PDF o Markdown e il server la conserva soltanto dopo averla
controllata. In questa attività non vengono ancora estratti testo e sezioni e non
viene creata alcuna indicizzazione.

## Quale problema risolve

Una knowledge base non può fidarsi del solo nome scelto nel browser. Un file potrebbe
essere troppo grande, avere un'estensione ingannevole oppure contenere dati diversi dal
formato dichiarato. Il controllo avviene quindi interamente nel backend prima del
salvataggio definitivo.

## Dati ricevuti

Il modulo `POST /app/knowledge` riceve un solo documento e conserva:

- nome originale ripulito dalle eventuali parti di percorso;
- nome interno casuale;
- formato normalizzato;
- dimensione in byte;
- impronta SHA-256 del contenuto;
- amministratore che ha effettuato l'upload;
- data del caricamento.

## Controlli applicati

- estensioni ammesse: `.pdf`, `.md` e `.markdown`;
- dimensione compresa tra 1 byte e 5 MB;
- tipo dichiarato compatibile con l'estensione;
- intestazione `%PDF-` presente per i PDF;
- testo UTF-8 e assenza di byte nulli per Markdown;
- nome originale non vuoto, non eccessivamente lungo e privo di caratteri di controllo.

Il tipo generico `application/octet-stream` viene accettato perché alcuni browser lo
usano per file Markdown o PDF; in quel caso il contenuto reale continua comunque a
essere verificato.

Dopo l'estrazione, SP-081 accetta al massimo 500.000 caratteri e 500 segmenti per
documento. Questo secondo tetto protegge da PDF piccoli ma molto compressi e impedisce
che un singolo upload produca migliaia di righe o una richiesta embedding eccessiva.

## Dove vengono salvati i dati

La tabella `knowledge_documents` contiene soltanto i metadati. I file vengono salvati
per impostazione predefinita in `storage/knowledge/`, cartella esclusa da Git. Il
percorso può essere sostituito con la variabile:

```text
SERVICEPILOT_KNOWLEDGE_STORAGE_DIR
```

Il nome interno è casuale e non deriva dal percorso inviato dal browser. Un file viene
prima scritto con un nome temporaneo, poi spostato nella posizione definitiva. Se il
database non riesce a registrare i metadati, il file viene rimosso.

## Errori gestiti

Un formato non ammesso, un file vuoto, troppo grande o con contenuto incoerente produce
una spiegazione semplice nella pagina e non modifica database o archivio. Anche un
errore durante il salvataggio annulla i dati e ripulisce i file temporanei.

## Chi può usare la funzione

Soltanto il ruolo `admin`. Dipendente e tecnico vengono rimandati alla propria area e
non possono salvare documenti neppure inviando direttamente la richiesta HTTP.

## Test che dimostrano il funzionamento

- PDF e Markdown validi vengono conservati con nome interno sicuro e metadati coerenti;
- parti di percorso presenti nel nome originale vengono ignorate;
- estensioni errate, PDF finti, tipi incoerenti, testo binario, file vuoti e oltre 5 MB
  vengono rifiutati senza modifiche parziali;
- un errore del database rimuove il file già scritto;
- i test web verificano accesso amministrativo, diniego agli altri ruoli, messaggio di
  successo e messaggio di errore.
- un documento che supera il limite del testo estratto viene marcato come fallito senza
  creare segmenti né chiamare il provider embedding.

SP-061 usa ora i documenti conservati per estrarre il testo e dividerlo in segmenti
con riferimenti alla fonte. Il comportamento è descritto in
[`KNOWLEDGE_EXTRACTION.md`](KNOWLEDGE_EXTRACTION.md).
