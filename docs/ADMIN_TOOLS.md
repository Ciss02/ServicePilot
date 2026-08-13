# Strumenti amministrativi

L'area riservata all'amministratore comprende gestione delle fonti e ripristino
controllato della demo.

## Quale problema risolve

Durante una dimostrazione i documenti possono cambiare, accumularsi oppure lasciare
indici non più aggiornati. Anche ticket e azioni vengono modificati mentre si prova il
portale. Gli strumenti amministrativi riportano queste parti in uno stato noto senza
intervenire manualmente sul database o sulla cartella dei file.

## Quali dati riceve

- rielaborazione: l'identificativo numerico del documento;
- eliminazione: l'identificativo e una conferma selezionata nel modulo;
- ripristino: la frase esatta `RIPRISTINA DEMO`.

Il browser non invia percorsi locali, nomi interni, password o chiavi API.

## Dove vengono controllati

Ogni richiesta richiede prima una sessione valida e poi il ruolo `admin`. Il backend
ricontrolla l'esistenza del documento, limita il file alla cartella configurata e non si
affida alla sola conferma visiva della pagina. Le tre password demo vengono lette dalle
variabili d'ambiente prima di iniziare un reset.

## Dove vengono salvati

La rielaborazione sostituisce i segmenti e gli embedding nel database. L'eliminazione
rimuove metadati e segmenti, poi cancella il file locale. Il reset sostituisce in una
sola transazione ticket, azioni, audit e knowledge base con i dati iniziali; account,
sedi e sessioni restano disponibili.

## Cosa può andare storto

- un documento potrebbe essere già stato eliminato;
- il file conservato potrebbe non essere più leggibile;
- il provider degli embedding potrebbe essere disattivato o non disponibile;
- il database potrebbe rifiutare un aggiornamento;
- Windows potrebbe impedire la rimozione di un file ancora aperto;
- le password demo potrebbero non essere configurate.

In caso di errore del database l'operazione viene annullata. Se soltanto la pulizia del
file fallisce, il documento non viene più utilizzato e la pagina mostra un avviso. Una
rielaborazione invalida i suggerimenti AI basati sui vecchi segmenti.

## Chi può usare la funzionalità

Soltanto l'amministratore autenticato. Dipendenti e tecnici vengono rimandati alla loro
area prima dell'esecuzione, anche se costruiscono manualmente l'indirizzo della richiesta.

## Quale test dimostra che funziona

I test verificano rielaborazione senza duplicati, invalidazione delle fonti citate,
eliminazione di database e file, frase obbligatoria, ripristino esatto di 6 ticket,
3 azioni e 9 eventi, conservazione della sessione e rifiuto degli altri ruoli.

## Limiti dichiarati

Il reset è intenzionalmente distruttivo per i soli dati operativi della demo: elimina
anche ticket e documenti creati durante le prove. Non è un sistema di backup e non deve
essere usato con dati reali. Se un file non può essere cancellato resta come file orfano
nella cartella locale, ma non compare più nell'applicazione.
