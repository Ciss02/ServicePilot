# Interfaccia web

ServicePilot AI offre un portale responsive collegato alle sessioni e ai permessi già
applicati dal backend.

## Quale problema risolve

Una persona può accedere dal browser con un modulo comprensibile, raggiungere le pagine
consentite dal proprio ruolo e chiudere la sessione.

## Pagine disponibili

- `GET /` indirizza verso l'area dell'applicazione;
- `GET /login` mostra il modulo di accesso;
- `POST /login` controlla email e password e avvia la sessione;
- `GET /app` mostra la dashboard personale oppure la coda tecnica in base al ruolo;
- `/app/new-ticket` gestisce descrizione, integrazione dei dati e conferma del ticket;
- `GET /app/tickets/{ticket_id}` mostra il dettaglio autorizzato e, per tecnico e admin,
  i comandi operativi;
- `GET /app/knowledge` permette all'amministratore di gestire e provare le fonti;
- `GET /app/audit` permette all'amministratore di consultare gli eventi;
- `POST /logout` revoca la sessione e torna alla pagina di accesso.

Una persona non autenticata che visita `/app` viene accompagnata a `/login`. Chi ha già
una sessione valida non deve invece ripetere l'accesso.

## Dati e controlli

Il modulo riceve email e password. Pydantic controlla la forma dei dati, poi il servizio
di autenticazione condiviso verifica account attivo e hash Argon2. Per qualsiasi
credenziale non valida viene mostrato lo stesso messaggio: in questo modo la pagina non
rivela se una particolare email esiste.

La password non viene reinserita nel documento HTML dopo un errore. La sessione continua
a usare il cookie `HttpOnly` e il database conserva soltanto l'impronta del codice
casuale, come descritto in [`AUTHENTICATION.md`](AUTHENTICATION.md).

## Struttura grafica e accessibilità

I template Jinja2 condividono intestazione, contenuto principale e piè di pagina. Lo
stile è contenuto in un solo file CSS e non scarica immagini, font o script esterni.
Sono presenti:

- etichette visibili per i campi;
- collegamento per saltare direttamente al contenuto;
- indicatore del punto attivo quando si usa la tastiera;
- messaggio di errore annunciabile dalle tecnologie assistive;
- colori con contrasto leggibile e pulsanti abbastanza grandi;
- adattamento a desktop, tablet e telefono;
- rispetto della preferenza di riduzione delle animazioni.

## Dipendenze

- `Jinja2 3.1.6` trasforma i template HTML nei documenti inviati al browser;
- `python-multipart 0.0.32` permette a FastAPI di leggere i campi inviati dai moduli.

Il portale usa pagine HTML generate dal server e normali moduli o collegamenti. Per
l'MVP non è stato necessario introdurre HTMX o un framework JavaScript: questo mantiene
il flusso semplice e riduce le parti che possono rompersi.

## Funzioni collegate

- il dipendente consulta le proprie richieste e usa la
  [`raccolta guidata`](GUIDED_TICKET_INTAKE.md);
- tecnico e amministratore lavorano dalla [`coda tecnica`](TECHNICIAN_QUEUE.md);
- l'amministratore gestisce knowledge base, audit e ripristino dei dati demo;
- limiti ai tentativi ripetuti, cookie sicuri e controlli dell'origine sono descritti in
  [`SECURITY_AND_DEMO_LIMITS.md`](SECURITY_AND_DEMO_LIMITS.md).
