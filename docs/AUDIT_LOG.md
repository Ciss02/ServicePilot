# Audit log

SP-073 aggiunge una cronologia persistente e consultabile delle operazioni rilevanti
eseguite sui ticket.

## 1. Quale problema risolve

Lo stato corrente di un ticket non spiega come ci si è arrivati. Il registro conserva
una sequenza leggibile di eventi umani, AI e automatici, così un tecnico può ricostruire
il percorso del singolo ticket e un amministratore può controllare l'intera demo.

Non è un semplice file di log del server: ogni evento è un dato applicativo collegato
al ticket e conservato nel database.

## 2. Quali dati riceve

Le funzioni del dominio costruiscono internamente eventi appartenenti a un vocabolario
chiuso:

- creazione e aggiornamenti del ticket;
- cambio di stato e assegnazione;
- proposta e revisione della classificazione AI;
- generazione o fallimento della soluzione con fonti;
- proposta, approvazione o rifiuto di un'azione;
- avvio ed esito del servizio REST simulato.

Ogni evento contiene ticket, origine (`human`, `ai` o `system`), tipo, riepilogo, data,
eventuale utente e dettagli brevi. Le azioni possono conservare anche il proprio
identificativo collegato.

## 3. Dove vengono controllati

I chiamanti non inviano JSON libero. Le funzioni di `app/audit/events.py` costruiscono
i dettagli consentiti e li limitano a 4.000 caratteri prima del salvataggio. Tipo di
evento e origine provengono dagli enum condivisi del dominio.

Il registro non copia password, chiavi API, prompt, payload completi, note tecniche o
soluzioni. Per questi ultimi indica soltanto quali campi sono cambiati.

## 4. Dove vengono salvati

La tabella `audit_events` conserva una riga per evento. Il salvataggio avviene nella
stessa transazione dell'operazione principale: ticket ed evento riescono insieme oppure
la transazione viene annullata.

Gli eventi sono append-only nell'applicazione. SQLAlchemy blocca modifiche e
cancellazioni delle righe già caricate e non esistono endpoint per riscriverle. Un
amministratore con accesso diretto al database rimane tecnicamente in grado di
intervenire: la demo locale non pretende di sostituire un archivio esterno
antimanomissione.

L'unica eliminazione prevista dall'app è il ripristino amministrativo dell'intero
dataset dimostrativo introdotto in SP-074. Richiede la frase `RIPRISTINA DEMO`, cancella
insieme ticket e relativa cronologia e crea i 9 eventi iniziali. Non permette di
modificare o rimuovere singoli eventi e non è una funzione adatta a un ambiente reale.

## 5. Cosa può andare storto

- un errore del database annulla anche l'operazione collegata quando fanno parte della
  stessa transazione;
- un'azione rifiutata registra la decisione ma non crea eventi di esecuzione;
- un servizio simulato non disponibile registra l'approvazione, l'avvio e l'esito
  fallito senza inventare un successo;
- un doppio invio già bloccato da SP-072 non aggiunge una seconda esecuzione;
- un dettaglio JSON illeggibile non viene mostrato liberamente nella pagina.
- il reset della demo elimina intenzionalmente l'intera cronologia operativa precedente.

## 6. Chi può usare la funzionalità

- tecnico e amministratore vedono la cronologia completa nel dettaglio del ticket;
- soltanto l'amministratore può aprire `/app/audit`, filtrare per origine e ticket e
  consultare gli ultimi 100 eventi;
- il dipendente non vede eventi operativi interni o la pagina amministrativa;
- nessun ruolo può modificare o cancellare eventi dall'interfaccia.

## 7. Quale test dimostra che funziona

I test verificano:

- creazione atomica degli eventi insieme al ticket o alla modifica;
- assenza di eventi per operazioni rifiutate;
- sequenza proposta → approvazione → avvio → esito;
- esiti AI validi, non disponibili e non utilizzabili;
- blocco di modifica e cancellazione tramite ORM;
- caricamento demo ripetibile senza duplicati;
- pagina amministrativa riservata e filtri;
- timeline visibile nel dettaglio tecnico.

Il collaudo nel browser usa soltanto dati fittizi e un servizio REST locale simulato.

## Presentazione

La timeline del ticket è ordinata dal primo all'ultimo evento. La pagina amministrativa
mostra invece i più recenti per primi e distingue visivamente:

- verde: persone;
- viola: assistente AI;
- ambra: sistema e servizi simulati.
