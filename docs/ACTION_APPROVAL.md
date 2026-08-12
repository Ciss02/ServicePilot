# Approvazione umana delle azioni

SP-072 collega le proposte di SP-070 ai servizi REST simulati di SP-071. Tecnico e
amministratore vedono i dettagli nel ticket e devono scegliere esplicitamente se
approvare oppure rifiutare ogni proposta.

## Quale problema risolve

Un suggerimento dell'agente non deve diventare automaticamente un effetto operativo.
L'approvazione umana crea un confine verificabile: finché lo stato è
`pending_approval`, il portale non chiama alcun servizio.

## Quali dati riceve

La decisione usa soltanto:

- ticket e proposta indicati nell'indirizzo della pagina;
- identità ricavata dalla sessione autenticata;
- decisione controllata `approve` oppure `reject`;
- payload, motivazione ed effetto già salvati nella proposta.

Il browser non può dichiarare liberamente chi ha deciso, cambiare lo stato finale o
fornire un payload alternativo durante l'approvazione.

## Dove vengono controllati

Il backend verifica che:

- il profilo sia `technician` oppure `admin`;
- proposta e ticket esistano e siano collegati;
- la proposta sia ancora `pending_approval`;
- il payload salvato superi nuovamente i contratti di SP-070;
- la decisione sia uno dei due valori ammessi.

Un aggiornamento condizionale nel database prenota la decisione una sola volta. Due
invii contemporanei non possono quindi avviare due chiamate.

## Dove vengono salvati

`proposed_actions` conserva inoltre:

- identificativo del tecnico o amministratore che ha deciso;
- data della decisione;
- riferimento e messaggio restituiti dal simulatore;
- codice dell'eventuale errore controllato.

Le transizioni sono:

```text
pending_approval -> rejected
pending_approval -> approved -> executing -> succeeded
pending_approval -> approved -> executing -> failed
```

Prima della chiamata REST vengono salvati sia `approved` sia `executing`. Se il processo
si interrompe, la proposta non torna falsamente in attesa e non viene ripetuta da un
doppio clic. SP-073 aggiungerà il registro audit generale e immutabile degli eventi.

## Cosa può andare storto

- rifiuto: viene registrato senza chiamare il simulatore;
- doppio invio: la seconda decisione viene ignorata senza una nuova chiamata;
- simulatore spento o timeout: la proposta termina `failed`, non in falso successo;
- errore demo `503`: codice e messaggio controllati vengono mostrati al tecnico;
- payload salvato corrotto: la chiamata viene fermata;
- errore nel salvataggio prima dell'esecuzione: il simulatore non viene chiamato;
- errore nel salvataggio finale: la proposta resta prudenzialmente `executing`.

Il client non esegue tentativi automatici, perché ripetere una richiesta operativa
senza una scelta del tecnico potrebbe duplicare un effetto.

## Chi può usare la funzionalità

Soltanto `technician` e `admin` vedono e decidono le azioni nella pagina tecnica del
ticket. Il ruolo `employee` viene rinviato alla propria area e non può modificare la
proposta nemmeno chiamando direttamente l'indirizzo del modulo.

## Quale test dimostra che funziona

- il rifiuto produce zero chiamate;
- un dipendente e una proposta appartenente a un altro ticket producono zero chiamate;
- lo stato `executing` è già persistente quando parte la chiamata;
- un'approvazione produce esattamente una chiamata e salva il riferimento;
- un secondo invio non ripete la chiamata;
- errori REST e di rete terminano `failed` con messaggi controllati;
- la pagina mostra motivazione, payload, effetto, pulsanti e risultato;
- il dataset demo crea tre proposte fittizie, una per tipo.

I test sostituiscono il client HTTP con un oggetto locale e non chiamano rete, Gemini,
persone o sistemi reali.

## Configurazione locale

Il portale usa per impostazione predefinita `http://127.0.0.1:8011` con timeout di tre
secondi. I valori possono essere cambiati soltanto tramite ambiente:

```text
SERVICEPILOT_ACTION_SERVICE_BASE_URL=http://127.0.0.1:8011
SERVICEPILOT_ACTION_SERVICE_TIMEOUT_SECONDS=3
```

L'indirizzo non può contenere credenziali. Non sono necessarie chiavi API.
