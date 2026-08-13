# Allegati privati e sicuri

SP-092 introduce l'archivio comune per gli allegati di ticket, bozze e messaggi. Il
primo collegamento grafico è disponibile sul dettaglio di un ticket: i contesti bozza e
messaggio sono già valori controllati del modello e saranno usati dalle relative issue,
senza anticiparne l'interfaccia.

## Problema risolto

Un file inviato dal browser non è affidabile solo perché ha una certa estensione o un
Content-Type plausibile. L'archivio evita file camuffati, metadati immagine superflui,
percorsi pubblici indovinabili e file orfani dopo un errore.

## Dati e controlli

La tabella `attachments` conserva proprietario, tipo e id del contesto, nome originale,
tipo validato, dimensione, SHA-256, nome interno casuale e data. Non conserva né mostra
mai il percorso assoluto. Il browser non invia il contesto come campo libero: la rotta
risolve prima il ticket visibile all'utente e lo passa al servizio.

- per invio: da 1 a 5 file;
- per file: massimo 10 MB ricevuti e dopo normalizzazione;
- per ticket: massimo 100 MB persistiti;
- formati: PNG, JPEG, PDF, TXT e LOG;
- PNG/JPEG: Pillow li apre, rifiuta immagini animate, corrotte o troppo grandi, applica
  l'orientamento EXIF e ricodifica senza metadati;
- PDF: `pypdf` deve poterlo aprire e il file non può essere cifrato;
- TXT/LOG: deve essere UTF-8, senza byte binari, HTML o SVG. Alcuni browser dichiarano
  un log come `application/octet-stream`: il contenuto viene comunque verificato come
  testo prima di accettarlo.

Il flusso è compensativo: file temporaneo, validazione/normalizzazione, nome finale
casuale e commit dei metadati. Un errore di disco o database rimuove temporanei e file
finali già creati e non lascia righe valide.

## Accesso, download e pulizia

Dipendenti, tecnici e amministratori passano dalla stessa verifica di visibilità del
ticket. Un dipendente può quindi accedere soltanto agli allegati dei propri ticket;
tecnico e amministratore usano la visibilità tecnica esistente. Un allegato inesistente,
di un altro dipendente o di un contesto non ancora collegato restituisce lo stesso 404.

Download e anteprima passano sempre dal backend. Il download usa `Content-Disposition`
come allegato, mentre l'anteprima inline è consentita solo per PNG, JPEG e PDF già
validati, con `nosniff`, CSP isolata e `no-store`.

Il reset della demo elimina metadati e file degli allegati prima di ricreare i ticket.
Il servizio `delete_context_attachments` è riutilizzabile per i futuri annullamenti di
bozze e cancellazioni di contesto; segnala un errore di disco senza dichiarare una pulizia
inesistente.

## Limiti intenzionali

Non sono inclusi scansione antivirus, OCR, miniature avanzate, condivisione pubblica,
storage cloud, archivi compressi, SVG, HTML, Office, audio o video. Nessun URL statico
espone la directory `storage/attachments`.

## Verifiche

I test automatici coprono file validi e camuffati, limiti, normalizzazione JPEG,
fallimento disco, autorizzazione, pulizia del contesto, upgrade dal database v0.1 e
download HTTP con intestazioni sicure. La prova visiva locale conferma il riquadro del
ticket, il caricamento di un log sintetico e il link di download.
