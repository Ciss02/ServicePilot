# ServicePilot AI v0.2.0 - Piano di prodotto

Stato: approvato il 13 agosto 2026

Questo documento conserva le regole comuni della prossima versione. La suddivisione
operativa ufficiale è in [`PROJECT_PLAN.md`](PROJECT_PLAN.md); ogni attività rimanda a
una issue GitHub dettagliata.

## Obiettivo

La `v0.2.0` trasforma l'MVP in un service desk più completo:

- apertura tramite agente AI conversazionale;
- diagnosi preventiva fondata su procedure sicure;
- allegati e comunicazioni cronologiche;
- conferma del dipendente dopo la risoluzione;
- gruppi, sotto-attività, worklog e notifiche;
- procedure modificabili e versionate;
- report amministrativi ed esportazione CSV.

Tutte queste capacità appartengono alla stessa release. Verranno però implementate una
issue e una pull request alla volta, completando le milestone nell'ordine indicato.

## Ciclo di vita del ticket

- Il tecnico può impostare `resolved` soltanto insieme a una soluzione.
- Il dipendente può confermare la soluzione e passare a `closed`, oppure riaprire il
  ticket con una nota se il problema persiste.
- Un ticket risolto senza risposta viene chiuso dopo 5 giorni. La scadenza viene salvata
  nel database e applicata in modo idempotente al successivo avvio o accesso, perché la
  demo Render Free non mantiene un processo sempre attivo.
- Un ticket chiuso può essere riaperto dal dipendente entro 14 giorni, con nota
  obbligatoria; i ticket rifiutati non possono essere riaperti.
- Il dipendente può chiudere direttamente un ticket attivo quando il problema è stato
  risolto autonomamente o è scomparso, scegliendo un motivo controllato.
- Il rifiuto non cancella il ticket: usa lo stato terminale `rejected` e richiede una
  motivazione visibile al richiedente.
- Risoluzione, conferma, riapertura, rifiuto e chiusura autonoma sono comandi distinti,
  con permessi e audit separati.

## Comunicazioni e allegati

- La nota singola viene sostituita da un thread pubblico append-only tra dipendente e
  supporto. Il lavoro interno resta nelle sotto-attività e nel worklog.
- Il tecnico aggiunge messaggi tramite un popup; ogni messaggio può contenere testo e
  allegati e non modifica i messaggi precedenti.
- Ogni invio accetta al massimo 5 file da 10 MB; una bozza o un ticket può conservarne
  complessivamente al massimo 100 MB.
- Formati ammessi: PNG, JPEG, PDF, TXT e LOG. Archivi, eseguibili, SVG e HTML sono
  rifiutati.
- Il backend controlla il contenuto reale, assegna nomi interni casuali e verifica i
  permessi anche in download. Le immagini vengono normalizzate e private dei metadati.
- Le regole backend possono richiedere uno screenshot, una foto o un log in base al
  problema. Se l'utente non può fornirlo, deve registrare una motivazione e può
  proseguire.

## Agente conversazionale

- La conversazione è una bozza privata persistente, riprendibile dopo logout o chiusura
  del browser e rimossa dopo 30 giorni di abbandono.
- Gemini può richiedere soltanto strumenti controllati dal backend: fare una domanda,
  cercare procedure, richiedere un allegato, proporre un passaggio sicuro, preparare il
  riepilogo o concludere l'assistenza.
- Ogni output è strutturato e ricontrollato. Sono consentite al massimo 12 risposte
  dell'utente e 4 azioni dell'agente per turno; raggiunto il limite viene preparato il
  miglior riepilogo possibile.
- I passaggi proposti provengono da procedure pubblicate per dipendenti oppure da una
  piccola lista deterministica di azioni sicure. Non sono ammessi privilegi elevati,
  credenziali, azioni distruttive o modifiche rischiose del sistema.
- Il riepilogo conserva separatamente racconto originale, tentativi eseguiti, allegati e
  descrizione tecnica riscritta. Nessun ticket viene creato senza conferma esplicita.
- Se il problema viene risolto prima del ticket, si conserva un'assistenza conclusa e
  Gemini può preparare una conoscenza candidata anonimizzata. Soltanto un admin può
  correggerla e pubblicarla come procedura.
- Tecnico e admin possono usare lo stesso agente per conto di un dipendente attivo. Il
  ticket distingue richiedente e autore dell'apertura.

## Workspace tecnico

- I gruppi di supporto sono dati amministrabili. Un tecnico può appartenere a più
  gruppi; quelli disattivati restano leggibili nello storico ma non sono assegnabili.
- Il dettaglio tecnico mostra dati fissi. Un pulsante separato apre la modifica; lo stato
  resta l'unico comando immediato.
- Le sotto-attività sono interne al team IT, non annidate, assegnabili a un tecnico e
  dotate di stato e scadenza facoltativa.
- Il worklog registra data, minuti, descrizione e sotto-attività facoltativa. È possibile
  inserire il tempo manualmente o usare un solo timer persistente per tecnico.
- Fermare il timer genera una riga da confermare. Un timer oltre 12 ore produce un
  avviso; la chiusura del ticket ferma eventuali timer e blocca nuovo lavoro.
- Il centro notifiche è soltanto interno al portale: campanella, conteggio non letti,
  filtri e segna come letto. Non sono previste email reali.

## Procedure e report

- Una procedura logica possiede versioni immutabili. Le modifiche restano in bozza fino
  alla pubblicazione riuscita della nuova versione.
- I PDF originali restano intatti; il sistema produce una copia Markdown modificabile,
  distinta e riconoscibile.
- Estrazione e indicizzazione devono terminare con successo prima di attivare la nuova
  versione. In caso di errore resta attiva quella precedente.
- Le conoscenze candidate provenienti dalle assistenze non entrano nella ricerca prima
  della revisione e pubblicazione amministrativa.
- I report admin comprendono volumi, stati, tempi di prima risposta/risoluzione/chiusura,
  attività, worklog e assistenze concluse, con filtri condivisi tra dashboard e CSV.
- Il CSV deve neutralizzare valori interpretabili come formule da un foglio di calcolo.

## Vincoli della demo

- SQLite e lo storage temporaneo Render restano accettabili per il portfolio.
- Tutte le date sono salvate in UTC e mostrate nel fuso `Europe/Rome`.
- Non sono previste email reali, antivirus, directory aziendali o integrazioni esterne.
- Tutti i dati, i file e le procedure usati nello sviluppo e nel collaudo sono fittizi.
- I test automatici usano modelli AI finti; le chiamate Gemini reali sono prove manuali
  limitate e dichiarate.

## Verifica della release

La `v0.2.0` richiede test delle migrazioni da `v0.1.0`, autorizzazioni dei tre ruoli,
scadenze con orologio finto, upload sicuri, timer, report e pubblicazione atomica delle
procedure. Ogni modifica visiva viene provata nel browser integrato prima del merge. La
release finale viene pubblicata soltanto dopo suite completa e CI GitHub verde.
