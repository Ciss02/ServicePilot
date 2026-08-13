# Estrazione e segmentazione della knowledge base

Il processo trasforma i documenti già controllati in passaggi piccoli e rintracciabili.
Questi passaggi alimentano l'indicizzazione e la ricerca descritte in
[`KNOWLEDGE_SEARCH.md`](KNOWLEDGE_SEARCH.md). L'estrazione del testo è deterministica;
gli embedding vengono creati nel passaggio successivo della stessa pipeline.

## Quale problema risolve

Un file intero è troppo grande e poco preciso per rispondere a una domanda. Dividerlo
in segmenti permette alla ricerca di scegliere soltanto i passaggi pertinenti.
Ogni segmento conserva il documento e la sezione di origine, così una risposta può
mostrare una fonte verificabile.

## Dati ricevuti

L'elaborazione usa il file già controllato e conservato e i suoi metadati:

- formato normalizzato (`application/pdf` oppure `text/markdown`);
- nome interno sicuro;
- identificativo del documento.

## Dove vengono controllati e trasformati

- Markdown: il testo viene letto come UTF-8 e i titoli `#` - `######` formano il
  percorso della sezione, per esempio `Wi-Fi > Verifica finale`;
- PDF: viene estratto soltanto il testo selezionabile e ogni passaggio conserva il
  riferimento `Pagina N`;
- ogni sezione viene divisa in blocchi di massimo 1.200 caratteri;
- due blocchi consecutivi condividono fino a 150 caratteri, per non spezzare il senso
  di una frase proprio sul confine;
- posizione, contenuto e numero di caratteri vengono calcolati dal backend.

La libreria locale `pypdf==6.14.2` legge i PDF senza inviare file a servizi esterni e
senza utilizzare chiavi API.

## Dove vengono salvati

La tabella `knowledge_segments` conserva:

- documento di origine;
- posizione del segmento nel documento;
- sezione Markdown o pagina PDF;
- testo leggibile;
- numero di caratteri.

Il documento conserva anche lo stato `pending`, `ready` o `failed`. Una nuova
elaborazione sostituisce tutti i segmenti precedenti in un'unica operazione: non
vengono accumulati duplicati e un errore di database non lascia una serie parziale.

## Cosa può andare storto

Un PDF scansionato come immagine, protetto da password o privo di testo selezionabile
non produce segmenti. Il file originale resta conservato e la pagina mostra
`Testo non estratto`. L'OCR delle scansioni non fa parte dell'MVP corrente.

Se il salvataggio dei segmenti fallisce, il documento resta nello stato da elaborare e
l'amministratore può riprovare dalla funzione di rielaborazione della knowledge base.

## Chi può usare la funzionalità

L'elaborazione parte dall'upload della knowledge base, già riservato al ruolo `admin`.
Dipendenti e tecnici non possono avviare direttamente il processo.

## Test che dimostrano il funzionamento

- titoli Markdown semplici e annidati diventano riferimenti di sezione;
- due pagine PDF reali producono segmenti con `Pagina 1` e `Pagina 2`;
- un testo lungo produce più segmenti entro il limite, tutti con la stessa fonte;
- un documento senza contenuto leggibile viene marcato senza righe parziali;
- elaborare due volte lo stesso file sostituisce i segmenti anziché duplicarli;
- il flusso web mostra l'esito e il numero reale di segmenti;
- un database creato nelle sessioni precedenti riceve i nuovi campi senza perdere il
  documento locale già presente.

