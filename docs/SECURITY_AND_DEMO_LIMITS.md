# Sicurezza e limiti della demo

Questo documento descrive le protezioni effettive dell'MVP al 13 agosto 2026.
ServicePilot resta una demo portfolio con dati fittizi: non va usato per
password, documenti aziendali o informazioni personali reali.

## Obiettivo della revisione

La demo pubblica espone account condivisi e funzioni che consumano risorse. La revisione
controlla quattro aree: segreti, upload, sessioni/browser e chiamate AI. L'obiettivo non
è dichiarare il sistema privo di rischi, ma rimuovere i problemi critici prima del deploy
e rendere visibili i limiti ancora accettati.

## Risultato sintetico

| Area | Protezione verificata | Limite residuo |
|---|---|---|
| Segreti | Chiave Gemini solo lato server, ambiente locale escluso da Git, nessun valore sensibile nei file tracciati | Il deploy deve usare il secret store del provider e una chiave limitata alla sola Gemini API |
| Upload | Solo admin, PDF/Markdown, massimo 5 MB, contenuto controllato, nome interno casuale, massimo 500.000 caratteri estratti e 500 segmenti | Non è presente un antivirus; usare esclusivamente documenti sintetici della demo |
| Sessioni | Token casuale, sola impronta nel database, durata 8 ore, cookie `HttpOnly` e `SameSite=Lax`, massimo 20 sessioni per account | Gli account sono condivisi e non hanno MFA, registrazione o recupero password |
| Browser | Host ammessi, origine controllata sugli invii, CSP e intestazioni anti-clickjacking/MIME sniffing, cookie HTTPS obbligatori in modalità pubblica | I client REST senza `Origin` o `Referer` restano ammessi; un prodotto reale userebbe anche token CSRF dedicati |
| Accesso | Errori uniformi e massimo 10 tentativi di login al minuto per client | Il contatore vive nel processo; una distribuzione con più istanze richiede un contatore condiviso |
| AI | Disattivata per default, timeout, retry e output limitati; massimo 10 richieste/minuto e 100/giorno tra generazione ed embedding | Il contatore vive nel processo e riparte al riavvio; il deploy deve usare una sola istanza o un limite condiviso, oltre alle quote del provider |

## 1. Segreti

- `.env` e le sue varianti sono escluse da Git; `.env.example` contiene soltanto nomi e
  valori non sensibili.
- `GEMINI_API_KEY` viene letta nel backend, esclusa dalle rappresentazioni degli oggetti
  di configurazione e mai inviata al browser.
- AI ed embedding restano disattivati finché il provider non viene scelto esplicitamente.
- La ricerca sui file tracciati non ha trovato chiavi Gemini, token GitHub o chiavi
  private riconoscibili.

Google raccomanda di trattare la chiave come una password, conservarla lato server,
limitarla alla sola API necessaria e configurare avvisi di spesa. Queste ultime due
operazioni dipendono dall'account cloud e vanno controllate nel progetto che ospita la
demo:
[gestione sicura delle chiavi Gemini](https://ai.google.dev/gemini-api/docs/api-key).

Se una chiave compare per errore in Git, rimuovere il testo dal commit non basta:
occorre sostituire la chiave, disabilitare quella precedente e controllarne l'utilizzo.

## 2. Upload e documenti

Il backend non si fida del nome scelto nel browser. Controlla estensione, tipo dichiarato,
contenuto riconoscibile e dimensione; salva con un UUID in una cartella non pubblica e
ignorata da Git. Un errore rimuove file temporanei e salvataggi parziali.

Un secondo tetto si applica dopo l'estrazione: un PDF compresso di pochi megabyte
può infatti produrre molto testo. Oltre 500.000 caratteri o 500 segmenti, il documento
viene marcato come non elaborabile e nessun embedding viene richiesto.

Non è presente scansione antivirus. Questo è accettato soltanto perché l'upload è
riservato all'admin e la demo deve usare documenti sintetici preparati per il progetto.

## 3. Login e sessioni

La password viene verificata contro Argon2. Il token di sessione contiene casualità
crittografica e soltanto la sua impronta SHA-256 entra nel database. Ogni nuova sessione:

1. elimina le sessioni già scadute;
2. conserva al massimo 20 sessioni attive dello stesso account;
3. scade dopo otto ore;
4. viene revocata al logout.

Il login accetta al massimo 10 tentativi al minuto per client, prima di eseguire il
controllo Argon2. Questo riduce sia i tentativi automatici sia il consumo di CPU.

Nella demo pubblica `SERVICEPILOT_PUBLIC_DEMO=true` richiede obbligatoriamente
`SERVICEPILOT_SECURE_COOKIES=true`; una configurazione incoerente ferma l'avvio. Gli host
pubblici ammessi devono essere elencati in `SERVICEPILOT_ALLOWED_HOSTS`.

## 4. Browser e richieste che modificano dati

Le richieste `POST`, `PATCH`, `PUT` e `DELETE` che arrivano da un browser con `Origin` o
`Referer` vengono accettate soltanto se provengono dallo stesso portale. Le risposte
aggiungono inoltre:

- Content Security Policy limitata alle risorse locali;
- blocco dell'inclusione in frame;
- blocco del riconoscimento automatico del tipo MIME;
- politica prudente del referrer e disattivazione di fotocamera, microfono e posizione;
- `Cache-Control: no-store` per pagine autenticate, login e API;
- HSTS quando sono attivi i cookie HTTPS.

`SameSite` è una protezione aggiuntiva, non l'unica difesa. La scelta segue le indicazioni
OWASP su [CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
e [intestazioni HTTP](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html).

## 5. Chiamate AI

Un unico contatore è condiviso da generazione strutturata ed embedding nel processo web.
Prima di costruire il client Google, il backend prenota una quota:

- `SERVICEPILOT_AI_REQUESTS_PER_MINUTE=10`;
- `SERVICEPILOT_AI_REQUESTS_PER_DAY=100`.

Quando una soglia è raggiunta, la rete non viene contattata e il flusso usa gli errori
controllati già previsti. Il limite giornaliero locale usa il giorno UTC. È indipendente
dalle quote Gemini, che possono variare per modello e progetto; Google applica limiti
per minuto, token e giorno e mostra quelli effettivi in AI Studio:
[quote Gemini](https://ai.google.dev/gemini-api/docs/rate-limits).

Il contatore è volutamente semplice e vive in memoria. La demo pubblica parte quindi
con una sola istanza. Prima di aumentare il numero di processi servirà spostare
il conteggio in un archivio condiviso. Anche il riavvio azzera il contatore locale: quote
del provider e avvisi di spesa restano il secondo livello obbligatorio.

## Configurazione minima del deploy

```text
SERVICEPILOT_PUBLIC_DEMO=true
SERVICEPILOT_SECURE_COOKIES=true
SERVICEPILOT_ALLOWED_HOSTS=nome-pubblico.example
SERVICEPILOT_LOGIN_ATTEMPTS_PER_MINUTE=10
SERVICEPILOT_AI_REQUESTS_PER_MINUTE=10
SERVICEPILOT_AI_REQUESTS_PER_DAY=100
```

La chiave Gemini e le password demo devono entrare nel secret store del provider, mai
nel repository o nell'immagine pubblica. Il deploy deve inoltre usare HTTPS, una sola
istanza applicativa e dati esclusivamente sintetici.

## Cosa dimostra che funziona

- test dei limiti al minuto e al giorno con orologio controllato;
- test che esaurisce la quota e dimostra che il client Gemini non viene costruito;
- test di rifiuto `403` per un invio proveniente da un'origine diversa;
- test di host non ammesso, intestazioni di sicurezza e HSTS;
- test del limite login e del recupero dopo un minuto;
- test di pulizia delle sessioni scadute e massimo per account;
- test di un documento che supera il limite di testo senza creare segmenti;
- suite completa, lint e formattazione eseguiti senza chiavi né chiamate esterne.

## Le sette domande di apprendimento

1. **Quale problema risolve?** Riduce abusi, costi inattesi e configurazioni pubbliche
   pericolose.
2. **Quali dati riceve?** Host e origine HTTP, tentativi di login, token di sessione,
   documenti demo e conteggi delle richieste AI; non conserva prompt nel limitatore.
3. **Dove vengono controllati?** Nel middleware web, nei servizi di sessione, nella
   pipeline documentale e negli adapter AI del backend.
4. **Dove vengono salvati?** Sessioni e documenti seguono il database e l'archivio già
   documentati; i contatori login e AI restano soltanto nella memoria del processo.
5. **Cosa può andare storto?** Una chiave può essere configurata male, più istanze
   possono moltiplicare i limiti locali o un documento può essere malevolo.
6. **Chi può usare la funzionalità?** Tutti attraversano le protezioni browser e login;
   AI e upload restano vincolati ai ruoli già previsti.
7. **Quale test dimostra che funziona?** I test elencati sopra provano sia i casi ammessi
   sia il blocco prima della rete o del salvataggio derivato.
